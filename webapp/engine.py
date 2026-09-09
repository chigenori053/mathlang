"""Pure execution logic for the MathLang notebook web UI.

No Streamlit import here on purpose: this module wraps the same building
blocks the CLI uses (`cli.modes`, `core.parser`, `core.causal`) so it can be
exercised directly by pytest, independent of the UI layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from cli.modes import run_polynomial_mode, run_symbolic_mode
from cli.output import rule_metadata_from_registry, should_run_causal_analysis
from core.causal import run_causal_analysis
from core.errors import MathLangError
from core.knowledge_registry import KnowledgeRegistry
from core.learning_logger import LearningLogger
from core.log_formatter import format_records
from core.parser import Parser

MODES = ("symbolic", "polynomial")


@dataclass
class CellResult:
    records: list[dict] = field(default_factory=list)
    formatted_lines: list[str] = field(default_factory=list)
    error: str | None = None
    causal: dict[str, Any] | None = None


def run_cell(source: str, mode: str = "symbolic") -> CellResult:
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

    return CellResult(
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
