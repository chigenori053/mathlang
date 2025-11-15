"""Polynomial evaluator implementation."""

from __future__ import annotations

from typing import Callable, List, Optional

from . import ast_nodes as ast
from .errors import InvalidStepError, MissingProblemError
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

    def run(self) -> List[dict]:
        for node in self.program.body:
            if isinstance(node, ast.ProblemNode):
                self._handle_problem(node)
            elif isinstance(node, ast.StepNode):
                self._handle_step(node)
            elif isinstance(node, ast.EndNode):
                self._handle_end(node)
            elif isinstance(node, ast.ExplainNode):
                self.learning_logger.record(
                    phase="explain",
                    expression=None,
                    rendered=node.text,
                    status="ok",
                )
        if self._state != "END":
            raise MissingProblemError("Program did not reach an end statement.")
        return self.learning_logger.to_list()

    def _handle_problem(self, node: ast.ProblemNode) -> None:
        if self._state != "INIT":
            raise MissingProblemError("Problem already defined.")
        normalized = self.normalizer(node.expr)
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
            raise MissingProblemError("step declared before problem.")
        normalized = self.normalizer(node.expr)
        if normalized != self._current_normalized:
            raise InvalidStepError("Polynomial step is not equivalent.")
        self.learning_logger.record(
            phase="step",
            expression=node.expr,
            rendered=f"Step ({node.step_id or 'unnamed'}): {node.expr}",
            status="ok",
        )
        self._state = "STEP_RUN"

    def _handle_end(self, node: ast.EndNode) -> None:
        if self._state not in {"PROBLEM_SET", "STEP_RUN"}:
            raise MissingProblemError("end declared before problem.")
        if self._current_normalized is None:
            raise MissingProblemError("Problem must be declared before end.")
        if node.is_done:
            target_expr = self._current_normalized
        else:
            target_expr = self.normalizer(node.expr or "")
        if target_expr is None:
            raise MissingProblemError("No expression to compare for end statement.")
        if target_expr != self._current_normalized:
            raise InvalidStepError("End expression is not equivalent.")
        rendered = "End: done" if node.is_done else f"End: {node.expr}"
        self.learning_logger.record(
            phase="end",
            expression=node.expr if not node.is_done else None,
            rendered=rendered,
            status="ok",
        )
        self._state = "END"
