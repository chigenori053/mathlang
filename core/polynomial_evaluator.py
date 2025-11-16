"""Polynomial evaluator implementation."""

from __future__ import annotations

from typing import Callable, Optional

from . import ast_nodes as ast
from .errors import MissingProblemError
from .learning_logger import LearningLogger


class PolynomialEvaluator:
    """Evaluate MathLang programs by comparing normalized polynomial strings."""

    def __init__(
        self,
        program: ast.ProgramNode,
        normalizer: Callable[[str], str],
        learning_logger: Optional[LearningLogger] = None,
    ) -> None:
        self.program = program
        self.normalizer = normalizer
        self.learning_logger = learning_logger or LearningLogger()
        self._state = "INIT"
        self._current_normalized: str | None = None

    def run(self) -> bool:
        for node in self.program.body:
            if isinstance(node, ast.ProblemNode):
                self._handle_problem(node)
            elif isinstance(node, ast.StepNode):
                self._handle_step(node)
            elif isinstance(node, ast.EndNode):
                self._handle_end(node)
            elif isinstance(node, ast.ExplainNode):
                self._handle_explain(node)
        if self._state != "END":
            exc = MissingProblemError("Program did not reach an end statement.")
            self._fatal(
                phase="end",
                expression=None,
                rendered="Fatal: missing end statement.",
                exc=exc,
            )
        return True

    def _handle_problem(self, node: ast.ProblemNode) -> None:
        if self._state != "INIT":
            exc = MissingProblemError("Problem already defined.")
            self._fatal(
                phase="problem",
                expression=node.expr,
                rendered=f"Duplicate problem: {node.expr}",
                exc=exc,
            )
        normalized = self._normalize_expr(node.expr, phase="problem")
        self._current_normalized = normalized
        self.learning_logger.record(
            phase="problem",
            expression=node.expr,
            rendered=f"Problem: {node.expr}",
            status="ok",
        )
        self._state = "PROBLEM_SET"

    def _handle_step(self, node: ast.StepNode) -> None:
        if self._state not in {"PROBLEM_SET", "STEP_RUN"}:
            exc = MissingProblemError("step declared before problem.")
            self._fatal(
                phase="step",
                expression=node.expr,
                rendered=f"Step ({node.step_id or 'unnamed'}): {node.expr}",
                exc=exc,
            )
        normalized = self._normalize_expr(node.expr, phase="step")
        is_valid = normalized == self._current_normalized
        status = "ok" if is_valid else "mistake"
        meta = {}
        if not is_valid:
            meta = {
                "reason": "invalid_step",
                "expected": self._current_normalized,
                "actual": normalized,
            }
        self.learning_logger.record(
            phase="step",
            expression=node.expr,
            rendered=f"Step ({node.step_id or 'unnamed'}): {node.expr}",
            status=status,
            meta=meta,
        )
        if is_valid:
            self._state = "STEP_RUN"

    def _handle_end(self, node: ast.EndNode) -> None:
        if self._state not in {"PROBLEM_SET", "STEP_RUN"}:
            exc = MissingProblemError("end declared before problem.")
            self._fatal(
                phase="end",
                expression=node.expr,
                rendered=f"End: {node.expr}",
                exc=exc,
            )
        if self._current_normalized is None:
            exc = MissingProblemError("Problem must be declared before end.")
            self._fatal(
                phase="end",
                expression=node.expr,
                rendered=f"End: {node.expr}",
                exc=exc,
            )
        if node.is_done:
            normalized_target = self._current_normalized
        else:
            normalized_target = self._normalize_expr(node.expr or "", phase="end")
        is_valid = normalized_target == self._current_normalized
        status = "ok" if is_valid else "mistake"
        meta = {}
        if not is_valid:
            meta = {
                "reason": "final_result_mismatch",
                "expected": self._current_normalized,
                "actual": normalized_target,
            }
        rendered = "End: done" if node.is_done else f"End: {node.expr}"
        self.learning_logger.record(
            phase="end",
            expression=node.expr if not node.is_done else None,
            rendered=rendered,
            status=status,
            meta=meta,
        )
        self._state = "END"

    def _handle_explain(self, node: ast.ExplainNode) -> None:
        if self._state == "INIT":
            exc = MissingProblemError("Explain cannot appear before problem.")
            self._fatal(
                phase="explain",
                expression=None,
                rendered="Explain before problem.",
                exc=exc,
            )
        self.learning_logger.record(
            phase="explain",
            expression=None,
            rendered=node.text,
            status="ok",
        )

    def _normalize_expr(self, expr: str, *, phase: str) -> str:
        try:
            return self.normalizer(expr)
        except Exception as exc:  # pragma: no cover - delegated to fatal log
            self._fatal(
                phase=phase,
                expression=expr,
                rendered=f"{phase.title()}: {expr}",
                exc=exc,
            )
        raise AssertionError("unreachable")  # pragma: no cover - satisfies type checkers

    def _fatal(
        self,
        *,
        phase: str,
        expression: str | None,
        rendered: str | None,
        exc: Exception,
    ) -> None:
        self.learning_logger.record(
            phase=phase,
            expression=expression,
            rendered=rendered,
            status="fatal",
            meta={"exception": exc.__class__.__name__, "message": str(exc)},
        )
        raise exc
