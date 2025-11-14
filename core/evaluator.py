"""Stepwise evaluator for the MathLang AST."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
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
    """Evaluates a MathLang program by processing problem blocks."""

    def __init__(
        self,
        program: ast.Program,
        language: LanguagePack | None = None,
        learning_logger: LearningLogger | None = None,
    ):
        self.program = program
        self.global_expressions: Dict[str, ast.Expr] = {}
        self._step_count = 0
        self._language = language or get_language_pack("en")
        self._learning_logger = learning_logger
        self._arithmetic_engine = ArithmeticEngine()
        self._fraction_engine = FractionEngine()

    def run(self) -> List[EvaluationResult]:
        results = []
        for statement in self.program.statements:
            results.extend(list(self._execute_statement(statement)))
        return results

    def _execute_statement(self, statement: ast.Statement) -> Iterable[EvaluationResult]:
        if isinstance(statement, ast.Problem):
            yield from self._evaluate_problem(statement)
            return

        if isinstance(statement, ast.Assignment):
            # This logic is for global-level assignments
            normalized_expr = self._normalize_expression(statement.expression)
            self.global_expressions[statement.target] = normalized_expr
            self._step_count += 1
            try:
                value = self._evaluate_numeric(normalized_expr, self.global_expressions)
                message = f"Global assignment: {statement.target} = {self._format_expression(normalized_expr)} (value: {value})"
            except EvaluationError as e:
                message = f"Global assignment: {statement.target} = {self._format_expression(normalized_expr)} (Error: {e})"
                raise e # Re-raise the error to propagate it to the main function
            yield EvaluationResult(self._step_count, message)
            return

        if isinstance(statement, ast.Show):
            if statement.identifier not in self.global_expressions:
                raise EvaluationError(f"Unknown global identifier '{statement.identifier}'")
            expr = self.global_expressions[statement.identifier]
            self._step_count += 1
            message = f"Show: {statement.identifier} → {self._format_expression(expr)}"
            yield EvaluationResult(self._step_count, message)
            return
                
        raise EvaluationError(f"Unsupported statement type: {type(statement)}")

    def _evaluate_numeric(self, expression: ast.Expr, context: Dict[str, ast.Expr]) -> int | float | Fraction:
        # First, substitute any symbols in the expression
        substituted_expr = self._substitute_identifiers(expression, context)

        if isinstance(substituted_expr, ast.Int):
            return substituted_expr.value
        elif isinstance(substituted_expr, ast.Rat):
            return Fraction(substituted_expr.numerator, substituted_expr.denominator)
        elif isinstance(substituted_expr, ast.Neg):
            return -self._evaluate_numeric(substituted_expr.expr, context)
        elif isinstance(substituted_expr, ast.Add):
            return sum(self._evaluate_numeric(term, context) for term in substituted_expr.terms)
        elif isinstance(substituted_expr, ast.Mul):
            product = 1
            for factor in substituted_expr.factors:
                product *= self._evaluate_numeric(factor, context)
            return product
        elif isinstance(substituted_expr, ast.Div):
            numerator = self._evaluate_numeric(substituted_expr.left, context)
            denominator = self._evaluate_numeric(substituted_expr.right, context)
            if denominator == 0:
                raise EvaluationError("Division by zero")
            return Fraction(numerator, denominator)
        elif isinstance(substituted_expr, ast.Pow):
            base = self._evaluate_numeric(substituted_expr.base, context)
            exp = self._evaluate_numeric(substituted_expr.exp, context)
            return base ** exp
        else:
            raise EvaluationError(f"Cannot evaluate non-numeric expression: {type(substituted_expr)}")

    def _evaluate_problem(self, problem: ast.Problem) -> Iterable[EvaluationResult]:

        self._step_count += 1

        yield EvaluationResult(self._step_count, f"Problem: {problem.name}")



        local_expressions = self.global_expressions.copy()

        if problem.prepare:

            for assignment in problem.prepare.assignments:

                # Note: Normalization during prepare is not specified, but could be added.

                local_expressions[assignment.target] = assignment.expression

                self._step_count += 1

                yield EvaluationResult(self._step_count, f"  Prepare: {assignment.target} = {self._format_expression(assignment.expression)}")



        for i, step in enumerate(problem.steps):
            self._step_count += 1
            
            # Substitute variables from the local context
            before_sub = self._substitute_identifiers(step.before, local_expressions)
            after_sub = self._substitute_identifiers(step.after, local_expressions)

            # Normalize the 'before' side
            normalized_before = self._normalize_expression(before_sub)

            # Check for equivalence
            try:
                numeric_before = self._evaluate_numeric(normalized_before, local_expressions)
                numeric_after = self._evaluate_numeric(after_sub, local_expressions)
                if numeric_before == numeric_after:
                    status = "Verified"
                else:
                    status = f"Failed: Expected {numeric_before}, got {numeric_after}"
            except EvaluationError as e:
                status = f"Error during evaluation: {e}"

            message = f"  Step {i+1}: {self._format_expression(step.before)} = {self._format_expression(step.after)} ({status})"
            yield EvaluationResult(self._step_count, message)



    def _normalize_expression(self, expression: ast.Expr) -> ast.Expr:

        if isinstance(expression, (ast.Int, ast.Rat)):

            return expression

        if isinstance(expression, ast.Sym):

            # Substitution should be handled before normalization

            return expression



        if isinstance(expression, ast.Neg):

            return self._arithmetic_engine.normalize(ast.Neg(self._normalize_expression(expression.expr)))



        if isinstance(expression, ast.Add):

            normalized_terms = [self._normalize_expression(term) for term in expression.terms]

            if any(self._contains_division(t) for t in normalized_terms):

                result = normalized_terms[0]

                for i in range(1, len(normalized_terms)):

                    result = self._fraction_engine.add(result, normalized_terms[i])

                return result

            return self._arithmetic_engine.normalize(ast.Add(terms=normalized_terms))



        if isinstance(expression, ast.Mul):

            normalized_factors = [self._normalize_expression(factor) for factor in expression.factors]

            if any(self._contains_division(f) for f in normalized_factors):

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

    

    def _contains_division(self, expression: ast.Expr) -> bool:

        if isinstance(expression, ast.Div):

            return True

        if isinstance(expression, ast.Neg):

            return self._contains_division(expression.expr)

        if isinstance(expression, (ast.Add, ast.Mul)):

            children = expression.terms if isinstance(expression, ast.Add) else expression.factors

            return any(self._contains_division(child) for child in children)

        if isinstance(expression, ast.Pow):

            return self._contains_division(expression.base) or self._contains_division(expression.exp)

        return False



    def _substitute_identifiers(self, expression: ast.Expr, context: Dict[str, ast.Expr], _visited: Optional[Set[str]] = None) -> ast.Expr:

        visited = _visited or set()

        if isinstance(expression, ast.Sym):

            if expression.name in visited:

                raise EvaluationError(f"Circular dependency for '{expression.name}'")

            if expression.name in context:

                visited.add(expression.name)

                return self._substitute_identifiers(context[expression.name], context, visited)

        

        if isinstance(expression, ast.Neg):

            return ast.Neg(self._substitute_identifiers(expression.expr, context, visited))

        if isinstance(expression, ast.Add):

            return ast.Add([self._substitute_identifiers(t, context, visited) for t in expression.terms])

        if isinstance(expression, ast.Mul):

            return ast.Mul([self._substitute_identifiers(f, context, visited) for f in expression.factors])

        if isinstance(expression, ast.Pow):

            return ast.Pow(self._substitute_identifiers(expression.base, context, visited), self._substitute_identifiers(expression.exp, context, visited))

        if isinstance(expression, ast.Div):

            return ast.Div(self._substitute_identifiers(expression.left, context, visited), self._substitute_identifiers(expression.right, context, visited))

        

        return expression



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
