"""Symbolic manipulation helpers built on top of SymPy (with a fallback)."""

from __future__ import annotations

import ast as py_ast
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Dict, Sequence, Set

from .errors import InvalidExprError

try:  # pragma: no cover - SymPy is an optional dependency at import time.
    import sympy as _sympy
except Exception:  # pragma: no cover
    _sympy = None


_SAMPLE_ASSIGNMENTS: Sequence[Dict[str, int]] = (
    {"x": -2, "y": 1, "z": 3, "a": 1},
    {"x": 0, "y": 0, "z": 0, "a": 2, "b": -1},
    {"x": 1, "y": 2, "z": -1, "b": 3, "c": 4},
    {"a": 2, "b": 5, "c": -3},
    {},
)


class _FallbackEvaluator:
    """Very small arithmetic evaluator used when SymPy is unavailable."""

    def parse(self, expr: str) -> py_ast.AST:
        expr = expr.replace("^", "**")
        try:
            tree = py_ast.parse(expr, mode="eval")
        except SyntaxError as exc:  # pragma: no cover - Python syntax errors.
            raise InvalidExprError(str(exc)) from exc
        return tree

    def evaluate(self, expr: str, values: Dict[str, int]) -> Fraction:
        tree = self.parse(expr)
        return self._eval_node(tree.body, values)

    def _eval_node(self, node: py_ast.AST, values: Dict[str, int]) -> Fraction:
        if isinstance(node, py_ast.Constant):
            return Fraction(node.value)
        if isinstance(node, py_ast.Name):
            return Fraction(values.get(node.id, 1))
        if isinstance(node, py_ast.BinOp):
            left = self._eval_node(node.left, values)
            right = self._eval_node(node.right, values)
            if isinstance(node.op, py_ast.Add):
                return left + right
            if isinstance(node.op, py_ast.Sub):
                return left - right
            if isinstance(node.op, py_ast.Mult):
                return left * right
            if isinstance(node.op, py_ast.Div):
                if right == 0:
                    raise InvalidExprError("Division by zero")
                return left / right
            if isinstance(node.op, py_ast.Pow):
                if right.denominator != 1:
                    raise InvalidExprError("Exponent must be an integer.")
                exponent = right.numerator
                return Fraction(left ** exponent)
        if isinstance(node, py_ast.UnaryOp):
            operand = self._eval_node(node.operand, values)
            if isinstance(node.op, py_ast.UAdd):
                return operand
            if isinstance(node.op, py_ast.USub):
                return -operand
        raise InvalidExprError(f"Unsupported expression: {py_ast.dump(node)}")

    def symbols(self, expr: str) -> Set[str]:
        tree = self.parse(expr)
        return {node.id for node in py_ast.walk(tree) if isinstance(node, py_ast.Name)}


@dataclass
class SymbolicEngine:
    """Thin wrapper providing equivalence and simplification utilities."""

    def __post_init__(self) -> None:
        self._fallback = _FallbackEvaluator() if _sympy is None else None

    def has_sympy(self) -> bool:
        return self._fallback is None

    def to_internal(self, expr: str) -> Any:
        if self._fallback is not None:
            return self._fallback.parse(expr)
        try:
            return _sympy.sympify(expr)
        except Exception as exc:  # pragma: no cover - SymPy provides details.
            raise InvalidExprError(str(exc)) from exc

    def is_equiv(self, expr1: str, expr2: str) -> bool:
        if self._fallback is not None:
            return self._fallback_is_equiv(expr1, expr2)
        internal1 = self.to_internal(expr1)
        internal2 = self.to_internal(expr2)
        return bool(_sympy.simplify(internal1 - internal2) == 0)

    def _fallback_is_equiv(self, expr1: str, expr2: str) -> bool:
        assert self._fallback is not None
        symbols = self._fallback.symbols(expr1) | self._fallback.symbols(expr2)
        success = False
        for assignment in _SAMPLE_ASSIGNMENTS:
            subset = {name: assignment.get(name, 1) for name in symbols}
            try:
                left = self._fallback.evaluate(expr1, subset)
                right = self._fallback.evaluate(expr2, subset)
            except InvalidExprError:
                continue
            if left != right:
                return False
            success = True
        if not success:
            raise InvalidExprError("Unable to evaluate expressions for comparison.")
        return True

    def simplify(self, expr: str) -> str:
        if self._fallback is not None:
            try:
                value = self._fallback.evaluate(expr, {})
                if value.denominator == 1:
                    return str(value.numerator)
                return f"{value.numerator}/{value.denominator}"
            except InvalidExprError:
                return expr
        internal = self.to_internal(expr)
        return str(_sympy.simplify(internal))

    def evaluate_numeric(self, expr: str, assignment: Dict[str, int]) -> Any:
        if self._fallback is not None:
            return self._fallback.evaluate(expr, assignment)
        internal = self.to_internal(expr)
        subs = {symbol: assignment.get(str(symbol), 0) for symbol in internal.free_symbols}
        return internal.subs(subs)

    def explain(self, before: str, after: str) -> str:
        if self.is_equiv(before, after):
            return "Expressions are equivalent."
        simplified_before = self.simplify(before)
        simplified_after = self.simplify(after)
        hint = "sympy" if self._fallback is None else "numeric sampling"
        return f"Compared via {hint}: {simplified_before} → {simplified_after}."
