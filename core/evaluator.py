"""Stepwise evaluator for the MathLang AST."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Generator, Iterable, List, Optional

from . import ast_nodes as ast
from .optimizer import clone_expression, optimize_expression
from .symbolic_engine import SymbolicEngine, SymbolicEngineError
from .i18n import LanguagePack, get_language_pack



class EvaluationError(RuntimeError):
    """Raised when evaluation cannot proceed due to invalid state."""


@dataclass
class EvaluationResult:
    step_number: int
    message: str


class Evaluator:
    """Evaluates a MathLang program while emitting human-friendly steps."""

    def __init__(
        self,
        program: ast.Program,
        symbolic_engine_factory: Optional[Callable[[], SymbolicEngine]] = None,
        language: LanguagePack | None = None,
    ):
        self.program = program
        self.context: Dict[str, float] = {}
        self.expressions: Dict[str, ast.Expression] = {}
        self._step = 0
        self._language = language or get_language_pack()
        self._symbolic_engine_factory = symbolic_engine_factory
        self._symbolic_engine: Optional[SymbolicEngine] = None
        self._symbolic_error: Optional[str] = None

        if symbolic_engine_factory is not None:
            try:
                self._symbolic_engine = symbolic_engine_factory()
            except SymbolicEngineError as exc:
                self._symbolic_error = str(exc)

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
            self.expressions[statement.target] = clone_expression(statement.expression)
            message = f"{statement.target} = {self._format_expression(statement.expression)} → {self._format_value(value)}"
            yield self._next_step(message)
            return

        if isinstance(statement, ast.Show):
            if statement.identifier not in self.context:
                raise EvaluationError(
                    self._language.text("evaluator.undefined_identifier", name=statement.identifier)
                )
            value = self.context[statement.identifier]
            value_str = self._format_value(value)
            message = self._language.text("evaluator.show_step", identifier=statement.identifier, value=value_str)
            yield self._next_step(message)
            yield from self._symbolic_trace(statement.identifier)
            yield EvaluationResult(step_number=0, message=self._language.text("evaluator.output", value=value_str))
            return

        if isinstance(statement, ast.ExpressionStatement):
            value = self._evaluate_expression(statement.expression)
            message = f"{self._format_expression(statement.expression)} → {self._format_value(value)}"
            yield self._next_step(message)
            return

        raise EvaluationError(self._language.text("evaluator.unsupported_statement", statement=statement))

    def _evaluate_expression(self, expression: ast.Expression) -> float:
        if isinstance(expression, ast.NumberLiteral):
            return expression.value
        if isinstance(expression, ast.Identifier):
            if expression.name not in self.context:
                raise EvaluationError(
                    self._language.text("evaluator.undefined_identifier", name=expression.name)
                )
            return self.context[expression.name]
        if isinstance(expression, ast.BinaryOp):
            left = self._evaluate_expression(expression.left)
            right = self._evaluate_expression(expression.right)
            return self._apply_operator(expression.operator, left, right)
        raise EvaluationError(self._language.text("evaluator.unsupported_expression", expression=expression))

    def _apply_operator(self, operator: str, left: float, right: float) -> float:
        if operator == "+":
            return left + right
        if operator == "-":
            return left - right
        if operator == "*":
            return left * right
        if operator == "/":
            if right == 0:
                raise EvaluationError(self._language.text("evaluator.division_by_zero"))
            return left / right
        if operator == "^":
            return left**right
        raise EvaluationError(self._language.text("evaluator.unsupported_operator", operator=operator))

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

    # Symbolic helpers ----------------------------------------------------------

    def _symbolic_trace(self, identifier: str) -> Iterable[EvaluationResult]:
        if self._symbolic_engine_factory is None:
            return []

        if self._symbolic_engine is None:
            if self._symbolic_error is None:
                return []
            # 既にエラーが発生している場合は一度だけ通知
            error_message = self._symbolic_error
            # エラーメッセージが複数回出力されるのを防ぐ
            self._symbolic_error = None
            return [EvaluationResult(step_number=0, message=self._language.text("symbolic.disabled", error=error_message))]

        expression = self.expressions.get(identifier)
        if expression is None:
            expression = ast.NumberLiteral(value=self.context[identifier])

        optimized = optimize_expression(expression, self.expressions)
        expression_str = self._format_expression(optimized)

        try:
            result = self._symbolic_engine.simplify(expression_str)
            structure = self._symbolic_engine.explain(expression_str)
        except SymbolicEngineError as exc:
            return [EvaluationResult(step_number=0, message=f"[Symbolic Error] {exc}")]

        return [
            EvaluationResult(step_number=0, message=self._language.text("symbolic.result", result=result.simplified)),
            EvaluationResult(step_number=0, message=self._language.text("symbolic.explanation", explanation=result.explanation)),
            EvaluationResult(step_number=0, message=self._language.text("symbolic.structure", structure=structure)),
        ]
