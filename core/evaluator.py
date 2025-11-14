"""Stepwise evaluator for the MathLang AST."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Generator, Iterable, List, Optional, Set

from . import ast_nodes as ast
from .arithmetic_engine import ArithmeticEngine
from .fraction_engine import FractionEngine
from .i18n import LanguagePack, get_language_pack
from .logging import LearningLogger
from .knowledge import KnowledgeRegistry, KnowledgeNode


class EvaluationError(RuntimeError):
    """Raised when evaluation cannot proceed due to invalid state."""

@dataclass
class EvaluationResult:
    step_number: int
    message: str

class Evaluator:
    """Evaluates a MathLang program by normalizing expressions."""

    def __init__(
        self,
        program: ast.Program,
        language: LanguagePack | None = None,
        learning_logger: LearningLogger | None = None,
    ):
        self.program = program
        self.context: Dict[str, float] = {}
        self.expressions: Dict[str, ast.Expr] = {}
        self._step = 0
        self._language = language or get_language_pack()
        self._learning_logger = learning_logger
        self._arithmetic_engine = ArithmeticEngine()
        self._fraction_engine = FractionEngine()

    def run(self) -> List[EvaluationResult]:
        return list(self.step_eval())

    def step_eval(self) -> Generator[EvaluationResult, None, None]:
        for statement in self.program.statements:
            yield from self._execute_statement(statement)

    def _execute_statement(self, statement: ast.Statement) -> Iterable[EvaluationResult]:
        if isinstance(statement, ast.Assignment):
            substituted_expr = self._substitute_identifiers(statement.expression)
            normalized_expr = self._normalize_expression(substituted_expr)
            self.expressions[statement.target] = normalized_expr
            
            # This will raise an error on failure, which is caught by the main CLI loop
            value = self._evaluate_numeric(normalized_expr)
            self.context[statement.target] = value
            message = f"{statement.target} = {self._format_expression(statement.expression)} → {self._format_expression(normalized_expr)} (value: {self._format_value(value)})"
            yield self._next_step(message)
            return

        if isinstance(statement, ast.Show):
            if statement.identifier not in self.expressions:
                raise EvaluationError(f"Unknown identifier '{statement.identifier}'")
            
            expr = self.expressions[statement.identifier]
            normalized_expr = self._normalize_expression(expr)
            
            message = f"show {statement.identifier} → {self._format_expression(normalized_expr)}"
            yield self._next_step(message)
            
            value = self._evaluate_numeric(normalized_expr)
            yield EvaluationResult(step_number=0, message=f"Output: {self._format_value(value)}")
            return

        if isinstance(statement, ast.ExpressionStatement):
            normalized_expr = self._normalize_expression(statement.expression)
            message = f"{self._format_expression(statement.expression)} → {self._format_expression(normalized_expr)}"
            yield self._next_step(message)
            return

        raise EvaluationError(f"Unsupported statement type: {type(statement)}")

    def _normalize_expression(self, expression: ast.Expr) -> ast.Expr:
        if isinstance(expression, (ast.Int, ast.Rat)):
            return expression
        if isinstance(expression, ast.Sym):
            return self._substitute_identifiers(expression)

        if isinstance(expression, ast.Neg):
            return self._arithmetic_engine.normalize(ast.Neg(self._normalize_expression(expression.expr)))

        if isinstance(expression, ast.Add):
            normalized_terms = [self._normalize_expression(term) for term in expression.terms]
            if any(isinstance(t, ast.Div) for t in normalized_terms):
                result = normalized_terms[0]
                for i in range(1, len(normalized_terms)):
                    result = self._fraction_engine.add(result, normalized_terms[i])
                return result
            return self._arithmetic_engine.normalize(ast.Add(terms=normalized_terms))

        if isinstance(expression, ast.Mul):
            normalized_factors = [self._normalize_expression(factor) for factor in expression.factors]
            if any(isinstance(f, ast.Div) for f in normalized_factors):
                result = normalized_factors[0]
                for i in range(1, len(normalized_factors)):
                    result = self._fraction_engine.multiply(result, normalized_factors[i])
                return result
            return self._arithmetic_engine.normalize(ast.Mul(factors=normalized_factors))

        if isinstance(expression, ast.Pow):
            base = self._normalize_expression(expression.base)
            exp = self._normalize_expression(expression.exp)
            return self._arithmetic_engine.normalize(ast.Pow(base, exp))

        if isinstance(expression, ast.Div):
            left = self._normalize_expression(expression.left)
            right = self._normalize_expression(expression.right)
            return self._fraction_engine.normalize(ast.Div(left, right))

        return expression

    def _substitute_identifiers(self, expression: ast.Expr, _visited: Optional[Set[str]] = None) -> ast.Expr:
        visited = _visited or set()
        if isinstance(expression, ast.Sym):
            if expression.name in visited:
                raise EvaluationError(f"Circular dependency detected for variable '{expression.name}'")
            if expression.name in self.expressions:
                visited.add(expression.name)
                return self._substitute_identifiers(self.expressions[expression.name], visited)
        
        if isinstance(expression, ast.Neg):
            return ast.Neg(self._substitute_identifiers(expression.expr, visited))
        if isinstance(expression, ast.Add):
            return ast.Add([self._substitute_identifiers(t, visited) for t in expression.terms])
        if isinstance(expression, ast.Mul):
            return ast.Mul([self._substitute_identifiers(f, visited) for f in expression.factors])
        if isinstance(expression, ast.Pow):
            return ast.Pow(self._substitute_identifiers(expression.base, visited), self._substitute_identifiers(expression.exp, visited))
        if isinstance(expression, ast.Div):
            return ast.Div(self._substitute_identifiers(expression.left, visited), self._substitute_identifiers(expression.right, visited))
        
        return expression

    def _evaluate_numeric(self, expression: ast.Expr, env: Optional[Dict[str, float]] = None) -> float:
        local_env = env or {}
        if isinstance(expression, ast.Int):
            return float(expression.value)
        if isinstance(expression, ast.Sym):
            if expression.name in local_env:
                return local_env[expression.name]
            if expression.name in self.context:
                return self.context[expression.name]
            raise EvaluationError(f"Cannot evaluate symbol '{expression.name}' to a numeric value.")
        if isinstance(expression, ast.Neg):
            return -self._evaluate_numeric(expression.expr, local_env)
        if isinstance(expression, ast.Add):
            return sum(self._evaluate_numeric(term, local_env) for term in expression.terms)
        if isinstance(expression, ast.Mul):
            val = 1.0
            for factor in expression.factors:
                val *= self._evaluate_numeric(factor, local_env)
            return val
        if isinstance(expression, ast.Pow):
            base = self._evaluate_numeric(expression.base, local_env)
            exp = self._evaluate_numeric(expression.exp, local_env)
            return base ** exp
        if isinstance(expression, ast.Div):
            num = self._evaluate_numeric(expression.left, local_env)
            den = self._evaluate_numeric(expression.right, local_env)
            if den == 0:
                raise EvaluationError("Division by zero.")
            return num / den
        raise EvaluationError(f"Cannot evaluate expression type '{type(expression).__name__}' to a numeric value.")

    def _next_step(self, message: str) -> EvaluationResult:
        self._step += 1
        return EvaluationResult(step_number=self._step, message=message)

    @staticmethod
    def _format_expression(expression: ast.Expr) -> str:
        if isinstance(expression, ast.Int):
            return str(expression.value)
        if isinstance(expression, ast.Sym):
            return expression.name
        if isinstance(expression, ast.Neg):
            if isinstance(expression.expr, ast.Add):
                return f"-({Evaluator._format_expression(expression.expr)})"
            return f"-{Evaluator._format_expression(expression.expr)}"
        if isinstance(expression, ast.Add):
            return " + ".join(Evaluator._format_expression(term) for term in expression.terms).replace(" + -", " - ")
        if isinstance(expression, ast.Mul):
            return " * ".join(Evaluator._format_expression(factor) for factor in expression.factors)
        if isinstance(expression, ast.Pow):
            return f"({Evaluator._format_expression(expression.base)})^({Evaluator._format_expression(expression.exp)})"
        if isinstance(expression, ast.Div):
            return f"({Evaluator._format_expression(expression.left)}) / ({Evaluator._format_expression(expression.right)})"
        return repr(expression)

    @staticmethod
    def _format_value(value: float) -> str:
        if value.is_integer():
            return str(int(value))
        return f"{value:.6g}"