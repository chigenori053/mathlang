"""MathLang AST を多項式として評価する Evaluator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from . import ast_nodes as ast
from .i18n import LanguagePack, get_language_pack
from .knowledge import KnowledgeRegistry, KnowledgeNode
from .logging import LearningLogger
from .polynomial import Polynomial


class PolynomialEvaluationError(RuntimeError):
    """多項式評価に失敗した場合の例外."""


@dataclass
class PolynomialEvaluationResult:
    step_number: int
    message: str


class PolynomialEvaluator:
    """MathLang の AST を多項式として解釈し、四則演算を行う."""

    def __init__(
        self,
        program: ast.Program,
        language: LanguagePack | None = None,
        learning_logger: LearningLogger | None = None,
    ):
        self.program = program
        self.context: Dict[str, Polynomial] = {}
        self._language = language or get_language_pack()
        self._step = 0
        self._core_problem_active = False
        self._core_last_polynomial: Optional[Polynomial] = None
        self._core_auto_step_index = 0
        self._knowledge_registry = KnowledgeRegistry()
        self._core_last_rule: Optional[KnowledgeNode] = None
        self._core_last_expression_str: Optional[str] = None
        self._learning_logger = learning_logger

    def run(self) -> List[PolynomialEvaluationResult]:
        return list(self.step_eval())

    def step_eval(self) -> Iterable[PolynomialEvaluationResult]:
        for statement in self.program.statements:
            yield from self._execute_statement(statement)

    # 内部処理 -------------------------------------------------------------

    def _execute_statement(self, statement: ast.Statement) -> Iterable[PolynomialEvaluationResult]:
        if isinstance(statement, ast.Problem):
            polynomial = self._evaluate_expression(statement.expression)
            expr_str = self._format_expression(statement.expression)
            self._core_problem_active = True
            self._core_last_polynomial = polynomial
            self._core_last_expression_str = expr_str
            self._core_auto_step_index = 0
            formatted = self._core_message_payload(statement.expression, polynomial)
            message = self._language.text("evaluator.core.problem", expression=formatted)
            result = self._next_step(message)
            self._log_learning_event(
                phase="problem",
                expression=expr_str,
                rendered=formatted,
                status="presented",
            )
            yield result
            return

        if isinstance(statement, ast.Step):
            self._ensure_problem_declared()
            polynomial = self._evaluate_expression(statement.expression)
            expr_str = self._format_expression(statement.expression)
            self._verify_polynomial(polynomial, expr_str)
            self._core_last_polynomial = polynomial
            self._core_last_expression_str = expr_str
            label = self._resolve_step_label(statement.label)
            formatted = self._core_message_payload(statement.expression, polynomial)
            status = self._status_with_rule()
            message = self._language.text("evaluator.core.step", label=label, expression=formatted, status=status)
            result = self._next_step(message)
            self._log_learning_event(
                phase="step",
                label=label,
                expression=expr_str,
                rendered=formatted,
                status=status,
                rule_id=self._current_rule_id(),
            )
            yield result
            self._core_last_rule = None
            return

        if isinstance(statement, ast.End):
            self._ensure_problem_declared()
            if statement.done:
                result = self._next_step(self._language.text("evaluator.core.end_done"))
                self._log_learning_event(
                    phase="end",
                    expression="done",
                    rendered="done",
                    status="done",
                )
                yield result
                self._finalize_core_sequence()
                return
            polynomial = self._evaluate_expression(statement.expression)
            expr_str = self._format_expression(statement.expression)
            self._verify_polynomial(polynomial, expr_str)
            self._core_last_polynomial = polynomial
            self._core_last_expression_str = expr_str
            formatted = self._core_message_payload(statement.expression, polynomial)
            status = self._status_with_rule()
            message = self._language.text("evaluator.core.end", expression=formatted, status=status)
            result = self._next_step(message)
            self._log_learning_event(
                phase="end",
                expression=expr_str,
                rendered=formatted,
                status=status,
                rule_id=self._current_rule_id(),
            )
            yield result
            self._finalize_core_sequence()
            return

        if isinstance(statement, ast.Explain):
            result = self._next_step(self._language.text("evaluator.core.explain", message=statement.message))
            self._log_learning_event(
                phase="explain",
                expression=statement.message,
                rendered=statement.message,
                status="info",
            )
            yield result
            return

        if isinstance(statement, ast.Assignment):
            polynomial = self._evaluate_expression(statement.expression)
            self.context[statement.target] = polynomial
            message = (
                f"{statement.target} = {self._format_expression(statement.expression)}"
                f" → {self._format_polynomial(polynomial)}"
            )
            result = self._next_step(message)
            self._log_learning_event(
                phase="assignment",
                label=statement.target,
                expression=self._format_expression(statement.expression),
                rendered=self._format_polynomial(polynomial),
                status="info",
            )
            yield result
            return

        if isinstance(statement, ast.Show):
            if statement.identifier not in self.context:
                raise PolynomialEvaluationError(
                    self._language.text("evaluator.undefined_identifier", name=statement.identifier)
                )
            polynomial = self.context[statement.identifier]
            value_str = self._format_polynomial(polynomial)
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
            yield PolynomialEvaluationResult(step_number=0, message=self._language.text("evaluator.output", value=value_str))
            return

        if isinstance(statement, ast.ExpressionStatement):
            polynomial = self._evaluate_expression(statement.expression)
            message = f"{self._format_expression(statement.expression)} → {self._format_polynomial(polynomial)}"
            yield self._next_step(message)
            return

        raise PolynomialEvaluationError(self._language.text("evaluator.unsupported_statement", statement=statement))

    def _evaluate_expression(self, expression: ast.Expr) -> Polynomial:
        if isinstance(expression, ast.Int):
            return Polynomial.constant(expression.value)
        if isinstance(expression, ast.Rat):
            return Polynomial.constant(expression.p / expression.q)
        if isinstance(expression, ast.Sym):
            if expression.name not in self.context:
                return Polynomial.variable(expression.name)
            return self.context[expression.name]
        if isinstance(expression, ast.Neg):
            return -self._evaluate_expression(expression.expr)
        if isinstance(expression, ast.Add):
            result = Polynomial.zero()
            for term in expression.terms:
                result += self._evaluate_expression(term)
            return result
        if isinstance(expression, ast.Mul):
            result = Polynomial.constant(1)
            for factor in expression.factors:
                result *= self._evaluate_expression(factor)
            return result
        if isinstance(expression, ast.Pow):
            base = self._evaluate_expression(expression.base)
            exp_expr = expression.exp
            if isinstance(exp_expr, ast.Int):
                exponent_value = exp_expr.value
                if exponent_value < 0:
                    if exponent_value == -1:
                        if not base.is_constant():
                            raise PolynomialEvaluationError("Polynomial division by non-scalar is not supported")
                        if base.is_zero():
                            raise PolynomialEvaluationError(self._language.text("evaluator.division_by_zero"))
                        scalar = next(iter(base.terms.values()))
                        return Polynomial.constant(1).divide_by_scalar(scalar)
                    else:
                        raise PolynomialEvaluationError("Negative exponent other than -1 is not supported for polynomials")
                return base.pow(exponent_value)

            raise PolynomialEvaluationError("Exponent must be an integer")

        raise PolynomialEvaluationError(self._language.text("evaluator.unsupported_expression", expression=expression))

    def _format_expression(self, expression: ast.Expr) -> str:
        if isinstance(expression, ast.Int):
            return str(expression.value)
        if isinstance(expression, ast.Rat):
            return f"({expression.p}/{expression.q})"
        if isinstance(expression, ast.Sym):
            return expression.name
        if isinstance(expression, ast.Neg):
            return f"-{self._format_expression(expression.expr)}"
        if isinstance(expression, ast.Add):
            return " + ".join(self._format_expression(term) for term in expression.terms)
        if isinstance(expression, ast.Mul):
            return " * ".join(self._format_expression(factor) for factor in expression.factors)
        if isinstance(expression, ast.Pow):
            base = self._format_expression(expression.base)
            exp = self._format_expression(expression.exp)
            return f"({base})^({exp})"
        if isinstance(expression, ast.Call):
            args = ", ".join(self._format_expression(arg) for arg in expression.args)
            return f"{expression.name}({args})"
        return repr(expression)

    def _format_polynomial(self, polynomial: Polynomial) -> str:
        return str(polynomial)

    def _core_message_payload(self, expression: ast.Expr, polynomial: Polynomial) -> str:
        return f"{self._format_expression(expression)} → {self._format_polynomial(polynomial)}"

    def _next_step(self, message: str) -> PolynomialEvaluationResult:
        self._step += 1
        return PolynomialEvaluationResult(step_number=self._step, message=message)

    def _ensure_problem_declared(self) -> None:
        if not self._core_problem_active or self._core_last_polynomial is None:
            raise PolynomialEvaluationError(self._language.text("evaluator.core.missing_problem"))

    def _verify_polynomial(self, polynomial: Polynomial, expression_str: str) -> None:
        self._core_last_rule = None
        if self._core_last_polynomial is None:
            return
        if polynomial == self._core_last_polynomial:
            self._core_last_rule = self._lookup_knowledge(self._core_last_expression_str, expression_str)
            return
        raise PolynomialEvaluationError(
            self._language.text(
                "evaluator.core.invalid_step",
                expected=self._format_polynomial(self._core_last_polynomial),
                actual=self._format_polynomial(polynomial),
            )
        )

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
        self._core_last_polynomial = None
        self._core_auto_step_index = 0
        self._core_last_rule = None
        self._core_last_expression_str = None

    def _status_with_rule(self) -> str:
        status = self._language.text("evaluator.core.status.verified")
        if self._core_last_rule is not None:
            rule_label = self._language.text("evaluator.core.rule", rule=self._core_last_rule.id)
            status = f"{status} ({rule_label})"
        return status

    def _lookup_knowledge(self, before_expr: Optional[str], after_expr: str) -> Optional[KnowledgeNode]:
        if before_expr is None:
            return None
        return self._knowledge_registry.match(before_expr, after_expr)

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