"""Stepwise evaluator for the MathLang AST."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Generator, Iterable, List

from . import ast_nodes as ast


class EvaluationError(RuntimeError):
    """Raised when evaluation cannot proceed due to invalid state."""


@dataclass
class EvaluationResult:
    step_number: int
    message: str


class Evaluator:
    """Evaluates a MathLang program while emitting human-friendly steps."""

    def __init__(self, program: ast.Program):
        self.program = program
        self.context: Dict[str, float] = {}
        self._step = 0

    def run(self) -> List[EvaluationResult]:
        """Evaluate the full program and collect all steps."""
        return list(self.step_eval())

    def step_eval(self) -> Generator[EvaluationResult, None, None]:
        """Generator yielding EvaluationResult for each evaluation step."""
        for statement in self.program.statements:
            yield from self._execute_statement(statement)

    # Internal helpers ----------------------------------------------------------

    def _execute_statement(self, statement: ast.Statement) -> Iterable[EvaluationResult]:
        if isinstance(statement, ast.Assignment):
            value = self._evaluate_expression(statement.expression)
            self.context[statement.target] = value
            message = f"{statement.target} = {self._format_expression(statement.expression)} → {self._format_value(value)}"
            yield self._next_step(message)
            return

        if isinstance(statement, ast.Show):
            if statement.identifier not in self.context:
                raise EvaluationError(f"Identifier '{statement.identifier}' not defined")
            value = self.context[statement.identifier]
            message = f"show {statement.identifier} → {self._format_value(value)}"
            yield self._next_step(message)
            yield EvaluationResult(step_number=0, message=f"Output: {self._format_value(value)}")
            return

        if isinstance(statement, ast.ExpressionStatement):
            value = self._evaluate_expression(statement.expression)
            message = f"{self._format_expression(statement.expression)} → {self._format_value(value)}"
            yield self._next_step(message)
            return

        raise EvaluationError(f"Unsupported statement type: {statement}")

    def _evaluate_expression(self, expression: ast.Expression) -> float:
        if isinstance(expression, ast.NumberLiteral):
            return expression.value
        if isinstance(expression, ast.Identifier):
            if expression.name not in self.context:
                raise EvaluationError(f"Identifier '{expression.name}' not defined")
            return self.context[expression.name]
        if isinstance(expression, ast.BinaryOp):
            left = self._evaluate_expression(expression.left)
            right = self._evaluate_expression(expression.right)
            return self._apply_operator(expression.operator, left, right)
        raise EvaluationError(f"Unsupported expression type: {expression}")

    def _apply_operator(self, operator: str, left: float, right: float) -> float:
        if operator == "+":
            return left + right
        if operator == "-":
            return left - right
        if operator == "*":
            return left * right
        if operator == "/":
            return left / right
        if operator == "^":
            return left**right
        raise EvaluationError(f"Unsupported operator: {operator}")

    def _next_step(self, message: str) -> EvaluationResult:
        self._step += 1
        return EvaluationResult(step_number=self._step, message=message)

    @staticmethod
    def _format_expression(expression: ast.Expression) -> str:
        if isinstance(expression, ast.NumberLiteral):
            return Evaluator._format_value(expression.value)
        if isinstance(expression, ast.Identifier):
            return expression.name
        if isinstance(expression, ast.BinaryOp):
            left = Evaluator._format_expression(expression.left)
            right = Evaluator._format_expression(expression.right)
            return f"{left} {expression.operator} {right}"
        return repr(expression)

    @staticmethod
    def _format_value(value: float) -> str:
        if value.is_integer():
            return str(int(value))
        return f"{value:.6g}"
