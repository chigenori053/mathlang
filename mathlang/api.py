"""Stable, UI-independent entry points for evaluating MathLang.

Every front end (the `mathlang` CLI, the web UI and, later, the MCP server)
should call these functions instead of wiring the core engines itself. All
expression strings are parsed through `core.safe_parse`, and every function
returns plain data (str / bool / dict / dataclass) that serializes to JSON.
"""

from __future__ import annotations

import signal
import threading
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Iterator, Mapping, Optional

import sympy

from cli.modes import run_polynomial_mode, run_symbolic_mode
from cli.output import rule_metadata_from_registry, should_run_causal_analysis
from core.causal import run_causal_analysis
from core.computation_engine import ComputationEngine
from core.errors import EvaluationError, EvaluationTimeoutError, InvalidExprError, MathLangError
from core.knowledge_registry import KnowledgeRegistry
from core.learning_logger import LearningLogger
from core.log_formatter import format_records
from core.parser import Parser
from core.safe_parse import safe_sympify
from core.symbolic_engine import SymbolicEngine
from core.unit_engine import UnitEngine

MODES = ("symbolic", "polynomial")
DEFAULT_PRECISION = 15

Bindings = Mapping[str, Any]


# ---------------------------------------------------------------------------
# DSL programs
# ---------------------------------------------------------------------------


@dataclass
class ProgramResult:
    records: list[dict] = field(default_factory=list)
    formatted_lines: list[str] = field(default_factory=list)
    error: str | None = None
    causal: dict[str, Any] | None = None

    @property
    def ok(self) -> bool:
        """The program ran to completion (it may still contain mistakes)."""
        return self.error is None

    @property
    def mistakes(self) -> list[dict]:
        """Steps / end statements that failed verification."""
        return [record for record in self.records if record.get("status") == "mistake"]

    @property
    def verified(self) -> bool:
        """The program ran and every step and end statement checked out."""
        return self.ok and not self.mistakes

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "verified": self.verified,
            "mistake_count": len(self.mistakes),
            **asdict(self),
        }


def run_program(source: str, mode: str = "symbolic") -> ProgramResult:
    """Parse and evaluate one MathLang program.

    Mirrors the try/except flow in `cli/base_runner.py::run_cli`: a
    `MathLangError` still yields whatever records were captured before the
    failure (partial trace + error), rather than discarding them.
    """

    if mode not in MODES:
        raise ValueError(f"Unsupported mode '{mode}'. Supported: {', '.join(MODES)}")

    learning_logger = LearningLogger()
    knowledge_registry: Optional[KnowledgeRegistry] = None
    error: str | None = None

    try:
        program = Parser(source).parse()
        if mode == "polynomial":
            run_polynomial_mode(program, learning_logger)
        else:
            knowledge_registry = run_symbolic_mode(program, learning_logger)
    except MathLangError as exc:
        error = str(exc)
    except Exception as exc:  # pragma: no cover - defensive guard, mirrors base_runner.py
        error = f"Unexpected error: {exc}"

    records = learning_logger.to_list()
    causal = _causal_report(records, knowledge_registry)

    return ProgramResult(
        records=records,
        formatted_lines=format_records(records),
        error=error,
        causal=causal,
    )


def _causal_report(
    records: list[dict], knowledge_registry: Optional[KnowledgeRegistry]
) -> dict[str, Any] | None:
    if not records or not should_run_causal_analysis(records):
        return None
    rule_info = rule_metadata_from_registry(knowledge_registry)
    engine, report = run_causal_analysis(records, rule_info=rule_info)
    error_ids: list[str] = report.get("errors", [])
    if not error_ids:
        return None
    report["fix_candidates"] = {
        error_id: [node.node_id for node in engine.suggest_fix_candidates(error_id)]
        for error_id in error_ids
    }
    return report


# ---------------------------------------------------------------------------
# Expressions
# ---------------------------------------------------------------------------


def parse_bindings(pairs: Iterable[str]) -> dict[str, str]:
    """Parse ``NAME=VALUE`` strings (as given on the command line)."""

    bindings: dict[str, str] = {}
    for pair in pairs:
        name, sep, value = pair.partition("=")
        name, value = name.strip(), value.strip()
        if not sep or not name.isidentifier() or name.startswith("_") or not value:
            raise InvalidExprError(f"Invalid binding {pair!r}; expected NAME=VALUE.")
        bindings[name] = value
    return bindings


def evaluate(
    expr: str,
    variables: Bindings | None = None,
    precision: int = DEFAULT_PRECISION,
) -> dict[str, str]:
    """Evaluate *expr* to a number.

    Returns ``{"exact": ..., "numeric": ...}``: the exact SymPy value
    (e.g. ``"sqrt(2)/2"``) and its decimal approximation. Raises
    `EvaluationError` if symbols remain unbound.
    """

    value = sympy.simplify(_substituted(expr, variables))
    free = sorted(str(symbol) for symbol in value.free_symbols)
    if free:
        raise EvaluationError(f"Undefined symbols: {', '.join(free)}")
    return {"exact": str(value), "numeric": _numeric(value, precision)}


def simplify(expr: str, variables: Bindings | None = None) -> str:
    return str(sympy.simplify(_substituted(expr, variables)))


def expand(expr: str) -> str:
    return _computation_engine().expand(expr)


def factor(expr: str) -> str:
    return _computation_engine().factor(expr)


def substitute(expr: str, variables: Bindings) -> str:
    return str(sympy.simplify(_substituted(expr, variables)))


def check_equivalence(expr1: str, expr2: str) -> bool:
    return SymbolicEngine().is_equiv(expr1, expr2)


def convert_units(expr: str, target_unit: str) -> str:
    return UnitEngine(SymbolicEngine()).convert(expr, target_unit)


def _computation_engine() -> ComputationEngine:
    return ComputationEngine(SymbolicEngine())


def _substituted(expr: str, variables: Bindings | None) -> Any:
    value = safe_sympify(expr)
    if variables:
        value = value.subs(
            {sympy.Symbol(name): safe_sympify(raw) for name, raw in variables.items()}
        )
    return value


def _numeric(value: Any, precision: int) -> str:
    if getattr(value, "is_Integer", False):
        return str(value)
    try:
        return str(sympy.N(value, precision))
    except Exception:  # pragma: no cover - non-numeric SymPy objects (e.g. relations)
        return str(value)


# ---------------------------------------------------------------------------
# Resource limits
# ---------------------------------------------------------------------------


class _Deadline(BaseException):
    """Raised from the alarm handler.

    A `BaseException` so that the engines' broad ``except Exception`` blocks
    cannot swallow it; `time_limit` converts it to `EvaluationTimeoutError`.
    """


@contextmanager
def time_limit(seconds: float | None) -> Iterator[None]:
    """Abort the enclosed evaluation after *seconds* (wall clock).

    Uses ``SIGALRM``, so it only takes effect on POSIX in the main thread;
    elsewhere, or when *seconds* is falsy, it is a no-op.
    """

    usable = (
        seconds
        and seconds > 0
        and hasattr(signal, "setitimer")
        and threading.current_thread() is threading.main_thread()
    )
    if not usable:
        yield
        return

    def _on_alarm(signum: int, frame: Any) -> None:
        raise _Deadline()

    previous = signal.signal(signal.SIGALRM, _on_alarm)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    except _Deadline:
        raise EvaluationTimeoutError(f"Evaluation timed out after {seconds:g} seconds.") from None
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
