"""Stepwise evaluator for the MathLang AST."""

from __future__ import annotations

import random
from dataclasses import dataclass
from math import isclose
from typing import Any, Callable, Dict, Generator, Iterable, List, Optional

from . import ast_nodes as ast
from .optimizer import clone_expression, optimize_expression
from .symbolic_engine import SymbolicEngine, SymbolicEngineError
from .i18n import LanguagePack, get_language_pack
from .logging import LearningLogger
from .knowledge import KnowledgeRegistry, KnowledgeNode



class EvaluationError(RuntimeError):
    """Raised when evaluation cannot proceed due to invalid state."""


@dataclass
class EvaluationResult:
    step_number: int
    message: str


@dataclass
class _CoreSnapshot:
    expression: ast.Expression
    formatted: str
    is_constant: bool
    value: float | None


class Evaluator:
    """Evaluates a MathLang program while emitting human-friendly steps."""

    def __init__(
        self,
        program: ast.Program,
        symbolic_engine_factory: Optional[Callable[[], SymbolicEngine]] = None,
        language: LanguagePack | None = None,
        learning_logger: LearningLogger | None = None,
    ):
        self.program = program
        self.context: Dict[str, float] = {}
        self.expressions: Dict[str, ast.Expression] = {}
        self._step = 0
        self._language = language or get_language_pack()
        self._symbolic_engine_factory = symbolic_engine_factory
        self._symbolic_engine: Optional[SymbolicEngine] = None
        self._symbolic_error: Optional[str] = None
        self._core_problem_active = False
        self._core_last_snapshot: Optional[_CoreSnapshot] = None
        self._core_auto_step_index = 0
        self._core_symbolic_engine: Optional[SymbolicEngine] = None
        self._core_symbolic_error: Optional[str] = None
        self._core_random = random.Random(0)
        self._knowledge_registry = KnowledgeRegistry()
        self._core_last_rule: Optional[KnowledgeNode] = None
        self._learning_logger = learning_logger

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
        if isinstance(statement, ast.Problem):
            snapshot = self._snapshot_expression(statement.expression)
            self._core_problem_active = True
            self._core_auto_step_index = 0
            self._core_last_snapshot = snapshot
            message = self._language.text("evaluator.core.problem", expression=snapshot.formatted)
            result = self._next_step(message)
            self._log_learning_event(
                phase="problem",
                expression=snapshot.formatted,
                rendered=snapshot.formatted,
                status="presented",
            )
            yield result
            return

        if isinstance(statement, ast.Step):
            self._ensure_problem_declared()
            snapshot = self._snapshot_expression(statement.expression)
            verified = self._verify_snapshot(snapshot)
            self._core_last_snapshot = snapshot
            label = self._resolve_step_label(statement.label)
            status = self._status_with_rule(
                verified
            )
            message = self._language.text("evaluator.core.step", label=label, expression=snapshot.formatted, status=status)
            result = self._next_step(message)
            self._log_learning_event(
                phase="step",
                label=label,
                expression=snapshot.formatted,
                rendered=snapshot.formatted,
                status=status,
                rule_id=self._current_rule_id(),
            )
            yield result
            self._core_last_rule = None
            return

        if isinstance(statement, ast.End):
            self._ensure_problem_declared()
            if statement.done:
                message = self._language.text("evaluator.core.end_done")
                result = self._next_step(message)
                self._log_learning_event(
                    phase="end",
                    expression="done",
                    rendered="done",
                    status="done",
                )
                yield result
                self._finalize_core_sequence()
                return

            snapshot = self._snapshot_expression(statement.expression)
            verified = self._verify_snapshot(snapshot)
            self._core_last_snapshot = snapshot
            status = self._status_with_rule(verified)
            message = self._language.text("evaluator.core.end", expression=snapshot.formatted, status=status)
            result = self._next_step(message)
            self._log_learning_event(
                phase="end",
                expression=snapshot.formatted,
                rendered=snapshot.formatted,
                status=status,
                rule_id=self._current_rule_id(),
            )
            yield result
            self._finalize_core_sequence()
            return

        if isinstance(statement, ast.Explain):
            message = self._language.text("evaluator.core.explain", message=statement.message)
            result = self._next_step(message)
            self._log_learning_event(
                phase="explain",
                expression=statement.message,
                rendered=statement.message,
                status="info",
            )
            yield result
            return

        if isinstance(statement, ast.Assignment):
            value = self._evaluate_expression(statement.expression)
            self.context[statement.target] = value
            self.expressions[statement.target] = clone_expression(statement.expression)
            message = f"{statement.target} = {self._format_expression(statement.expression)} → {self._format_value(value)}"
            result = self._next_step(message)
            self._log_learning_event(
                phase="assignment",
                label=statement.target,
                expression=self._format_expression(statement.expression),
                rendered=self._format_value(value),
                status="info",
            )
            yield result
            return

        if isinstance(statement, ast.Show):
            if statement.identifier not in self.context:
                raise EvaluationError(
                    self._language.text("evaluator.undefined_identifier", name=statement.identifier)
                )
            value = self.context[statement.identifier]
            value_str = self._format_value(value)
            message = self._language.text("evaluator.show_step", identifier=statement.identifier, value=value_str)
            result = self._next_step(message)
            self._log_learning_event(
                phase="show",
                label=statement.identifier,
                expression=statement.identifier,
                rendered=value_str,
                status="info",
                metadata={"value": value_str},
            )
            yield result
            yield from self._symbolic_trace(statement.identifier)
            yield EvaluationResult(step_number=0, message=self._language.text("evaluator.output", value=value_str))
            return

        if isinstance(statement, ast.ExpressionStatement):
            value = self._evaluate_expression(statement.expression)
            message = f"{self._format_expression(statement.expression)} → {self._format_value(value)}"
            result = self._next_step(message)
            self._log_learning_event(
                phase="expression",
                expression=self._format_expression(statement.expression),
                rendered=self._format_value(value),
                status="info",
            )
            yield result
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

    # Core DSL helpers ---------------------------------------------------------

    def _snapshot_expression(self, expression: ast.Expression) -> _CoreSnapshot:
        optimized = optimize_expression(expression, self.expressions)
        formatted = self._format_expression(optimized)
        if isinstance(optimized, ast.NumberLiteral):
            return _CoreSnapshot(expression=optimized, formatted=formatted, is_constant=True, value=optimized.value)
        return _CoreSnapshot(expression=optimized, formatted=formatted, is_constant=False, value=None)

    def _ensure_problem_declared(self) -> None:
        if not self._core_problem_active or self._core_last_snapshot is None:
            raise EvaluationError(self._language.text("evaluator.core.missing_problem"))

    def _verify_snapshot(self, snapshot: _CoreSnapshot) -> bool:
        self._core_last_rule = None
        if self._core_last_snapshot and self._core_last_snapshot.is_constant and snapshot.is_constant:
            expected_value = self._core_last_snapshot.value
            actual_value = snapshot.value
            if expected_value is None or actual_value is None:
                return False
            if isclose(expected_value, actual_value, rel_tol=1e-9, abs_tol=1e-9):
                self._core_last_rule = self._lookup_knowledge(self._core_last_snapshot, snapshot)
                return True
            raise EvaluationError(
                self._language.text(
                    "evaluator.core.invalid_step",
                    expected=self._format_value(expected_value),
                    actual=self._format_value(actual_value),
                )
            )

        if self._core_last_snapshot:
            engine = self._get_core_symbolic_engine()
            if engine is not None:
                previous_expr = self._format_expression(self._core_last_snapshot.expression)
                current_expr = self._format_expression(snapshot.expression)
                diff_expr = f"({previous_expr}) - ({current_expr})"
                try:
                    result = engine.simplify(diff_expr)
                except SymbolicEngineError:
                    pass
                else:
                    if result.simplified.strip() == "0":
                        self._core_last_rule = self._lookup_knowledge(self._core_last_snapshot, snapshot)
                        return True
                    raise EvaluationError(
                        self._language.text(
                            "evaluator.core.invalid_step",
                            expected=previous_expr,
                            actual=current_expr,
                        )
                    )

            if self._probabilistic_equivalence(self._core_last_snapshot.expression, snapshot.expression):
                self._core_last_rule = self._lookup_knowledge(self._core_last_snapshot, snapshot)
                return True

        return False

    def _resolve_step_label(self, explicit_label: str | None) -> str:
        if explicit_label:
            self._sync_auto_step_counter(explicit_label)
            return explicit_label
        self._core_auto_step_index += 1
        return f"step{self._core_auto_step_index}"

    def _sync_auto_step_counter(self, label: str) -> None:
        index = None
        if label.startswith("step[") and label.endswith("]"):
            inner = label[5:-1]
            if inner.isdigit():
                index = int(inner)
        elif label.startswith("step"):
            suffix = label[4:]
            if suffix.isdigit():
                index = int(suffix)
        if index is not None and index > self._core_auto_step_index:
            self._core_auto_step_index = index

    def _finalize_core_sequence(self) -> None:
        self._core_problem_active = False
        self._core_last_snapshot = None
        self._core_auto_step_index = 0
        self._core_last_rule = None

    def _get_core_symbolic_engine(self) -> Optional[SymbolicEngine]:
        if self._symbolic_engine is not None:
            return self._symbolic_engine
        if self._core_symbolic_engine is not None:
            return self._core_symbolic_engine
        if self._core_symbolic_error is not None:
            return None
        try:
            self._core_symbolic_engine = SymbolicEngine()
        except SymbolicEngineError as exc:
            self._core_symbolic_error = str(exc)
            return None
        return self._core_symbolic_engine

    def _probabilistic_equivalence(self, reference: ast.Expression, candidate: ast.Expression) -> bool:
        variables: set[str] = set()
        self._collect_identifiers(reference, variables)
        self._collect_identifiers(candidate, variables)
        if not variables:
            return False

        samples = 5
        attempts = 0
        successes = 0
        while attempts < samples and successes < samples:
            attempts += 1
            env = {var: self._core_random.uniform(2, 11) for var in variables}
            try:
                ref_val = self._evaluate_expression_numeric(reference, env)
                cand_val = self._evaluate_expression_numeric(candidate, env)
            except ZeroDivisionError:
                continue
            if not isclose(ref_val, cand_val, rel_tol=1e-6, abs_tol=1e-6):
                raise EvaluationError(
                    self._language.text(
                        "evaluator.core.invalid_step",
                        expected=self._format_expression(reference),
                        actual=self._format_expression(candidate),
                    )
                )
            successes += 1

        return successes > 0

    def _collect_identifiers(self, expression: ast.Expression, sink: set[str]) -> None:
        if isinstance(expression, ast.Identifier):
            sink.add(expression.name)
            return
        if isinstance(expression, ast.BinaryOp):
            self._collect_identifiers(expression.left, sink)
            self._collect_identifiers(expression.right, sink)

    def _evaluate_expression_numeric(self, expression: ast.Expression, env: Dict[str, float]) -> float:
        if isinstance(expression, ast.NumberLiteral):
            return expression.value
        if isinstance(expression, ast.Identifier):
            return env[expression.name]
        if isinstance(expression, ast.BinaryOp):
            left = self._evaluate_expression_numeric(expression.left, env)
            right = self._evaluate_expression_numeric(expression.right, env)
            if expression.operator == "+":
                return left + right
            if expression.operator == "-":
                return left - right
            if expression.operator == "*":
                return left * right
            if expression.operator == "/":
                if isclose(right, 0.0, abs_tol=1e-12):
                    raise ZeroDivisionError
                return left / right
            if expression.operator == "^":
                return left ** right
        raise EvaluationError(self._language.text("evaluator.unsupported_expression", expression=expression))

    def _log_learning_event(
        self,
        *,
        phase: str,
        expression: str,
        rendered: str,
        status: str,
        label: str | None = None,
        rule_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if self._learning_logger is None:
            return
        self._learning_logger.record(
            step_number=self._step,
            phase=phase,
            label=label,
            expression=expression,
            rendered=rendered,
            rule_id=rule_id,
            status=status,
            metadata=metadata or {},
        )

    def _current_rule_id(self) -> Optional[str]:
        if self._core_last_rule is None:
            return None
        return self._core_last_rule.id

    def _status_with_rule(self, verified: bool) -> str:
        status = self._language.text(
            "evaluator.core.status.verified" if verified else "evaluator.core.status.unverified"
        )
        if self._core_last_rule is not None:
            rule_label = self._language.text("evaluator.core.rule", rule=self._core_last_rule.id)
            status = f"{status} ({rule_label})"
        return status

    def _lookup_knowledge(self, before: _CoreSnapshot | None, after: _CoreSnapshot) -> Optional[KnowledgeNode]:
        if before is None:
            return None
        return self._knowledge_registry.match(before.formatted, after.formatted)
