
"""Symbolic manipulation helpers bridging MathLang with SymPy (Phase 2 stub)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

try:  # SymPy is an optional import during early scaffolding.
    import sympy as _sympy
except ImportError:  # pragma: no cover - import guard exercised in CI environments.
    _sympy = None


class SymbolicEngineError(RuntimeError):
    """Raised when symbolic processing cannot be performed."""


@dataclass
class SymbolicResult:
    simplified: str
    explanation: str


class SymbolicEngine:
    """Thin wrapper around SymPy operations used by downstream components."""

    def __init__(self, sympy_module: Any | None = None) -> None:
        self._sympy = sympy_module or _sympy
        if self._sympy is None:
            raise SymbolicEngineError(
                "SymPy is not available. Install dependencies or pin the correct Python env "
                "before enabling symbolic features."
            )

    def simplify(self, expression: str) -> SymbolicResult:
        """Simplify a textual expression and describe the transformation."""

        try:
            sympy_expr = self._sympy.sympify(expression)
            simplified = self._sympy.simplify(sympy_expr)
        except Exception as exc:  # pragma: no cover - bubbled up for visibility.
            raise SymbolicEngineError(f"Failed to simplify expression '{expression}': {exc}") from exc

        if simplified == sympy_expr:
            explanation = "Expression already in simplest SymPy form."
        else:
            explanation = f"Simplified from {sympy_expr} to {simplified}."

        return SymbolicResult(simplified=str(simplified), explanation=explanation)

    def explain(self, expression: str) -> str:
        """Return a human-friendly breakdown of the parsed SymPy expression tree."""

        try:
            sympy_expr = self._sympy.sympify(expression)
        except Exception as exc:  # pragma: no cover - bubbled up for visibility.
            raise SymbolicEngineError(f"Failed to parse expression '{expression}': {exc}") from exc

        return self._sympy.srepr(sympy_expr)
