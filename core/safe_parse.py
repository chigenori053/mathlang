"""Safe conversion of user-supplied expression strings into SymPy objects.

`sympy.sympify` evaluates its input with Python's `eval`, so passing it an
untrusted string such as ``"__import__('os').system(...)"`` executes code.
Every string that reaches SymPy must go through `safe_sympify`, which first
checks the expression's Python AST against a whitelist of arithmetic syntax
and known math functions.
"""

from __future__ import annotations

import ast as py_ast
from typing import Any, Mapping

from .errors import InvalidExprError

MAX_EXPRESSION_LENGTH = 10_000

# Functions callable from an expression. Anything else in call position
# (builtins, SymPy classes such as `Symbol`, attribute access) is rejected.
ALLOWED_FUNCTIONS = frozenset(
    {
        # roots, powers, logarithms
        "sqrt", "cbrt", "root", "exp", "log", "ln",
        # trigonometric / hyperbolic
        "sin", "cos", "tan", "cot", "sec", "csc",
        "asin", "acos", "atan", "atan2", "acot",
        "sinh", "cosh", "tanh", "asinh", "acosh", "atanh",
        # number theory / rounding
        "Abs", "abs", "sign", "floor", "ceiling", "factorial", "binomial",
        "gcd", "lcm", "Mod", "Min", "Max", "min", "max",
        # exact numbers
        "Rational", "Integer", "Float",
        # complex numbers
        "re", "im", "conjugate", "arg",
        # calculus
        "diff", "integrate", "limit", "Sum", "Product", "summation",
        "Derivative", "Integral",
        # relations
        "Eq", "Ne", "Lt", "Le", "Gt", "Ge",
    }
)

_ALLOWED_BINOPS = (
    py_ast.Add, py_ast.Sub, py_ast.Mult, py_ast.Div,
    py_ast.Pow, py_ast.Mod, py_ast.FloorDiv,
)
_ALLOWED_UNARYOPS = (py_ast.UAdd, py_ast.USub)
_ALLOWED_CMPOPS = (py_ast.Eq, py_ast.NotEq, py_ast.Lt, py_ast.LtE, py_ast.Gt, py_ast.GtE)


def normalize_expression(expr: str) -> str:
    """Return the Python-syntax form of *expr* (``^`` means power, as in SymPy)."""

    return expr.strip().replace("^", "**")


def validate_expression(expr: str) -> str:
    """Check that *expr* only uses whitelisted syntax.

    Returns the normalized expression string. Raises `InvalidExprError` when
    the expression is empty, too long, syntactically invalid, or uses
    constructs outside the whitelist.
    """

    if not isinstance(expr, str):
        raise InvalidExprError(f"Expression must be a string, got {type(expr).__name__}.")
    normalized = normalize_expression(expr)
    if not normalized:
        raise InvalidExprError("Expression is empty.")
    if len(normalized) > MAX_EXPRESSION_LENGTH:
        raise InvalidExprError(
            f"Expression is too long ({len(normalized)} > {MAX_EXPRESSION_LENGTH} characters)."
        )
    try:
        tree = py_ast.parse(normalized, mode="eval")
    except SyntaxError as exc:
        raise InvalidExprError(f"Invalid expression syntax: {expr!r}") from exc
    _check_node(tree.body)
    return normalized


def safe_sympify(expr: Any, locals: Mapping[str, Any] | None = None) -> Any:
    """Validate *expr* and convert it to a SymPy expression."""

    import sympy

    if isinstance(expr, (int, float)) and not isinstance(expr, bool):
        return sympy.sympify(expr)
    normalized = validate_expression(expr)
    try:
        return sympy.sympify(normalized, locals=dict(locals) if locals else None)
    except Exception as exc:
        raise InvalidExprError(f"Failed to parse expression {expr!r}: {exc}") from exc


def _check_node(node: py_ast.AST) -> None:
    if isinstance(node, py_ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float, complex)):
            raise InvalidExprError(f"Unsupported literal: {node.value!r}")
        return
    if isinstance(node, py_ast.Name):
        _check_identifier(node.id)
        return
    if isinstance(node, py_ast.BinOp):
        if not isinstance(node.op, _ALLOWED_BINOPS):
            raise InvalidExprError(f"Unsupported operator: {type(node.op).__name__}")
        _check_node(node.left)
        _check_node(node.right)
        return
    if isinstance(node, py_ast.UnaryOp):
        if not isinstance(node.op, _ALLOWED_UNARYOPS):
            raise InvalidExprError(f"Unsupported operator: {type(node.op).__name__}")
        _check_node(node.operand)
        return
    if isinstance(node, py_ast.Compare):
        for op in node.ops:
            if not isinstance(op, _ALLOWED_CMPOPS):
                raise InvalidExprError(f"Unsupported comparison: {type(op).__name__}")
        _check_node(node.left)
        for comparator in node.comparators:
            _check_node(comparator)
        return
    if isinstance(node, py_ast.Call):
        if not isinstance(node.func, py_ast.Name):
            raise InvalidExprError("Only calls to named math functions are allowed.")
        if node.func.id not in ALLOWED_FUNCTIONS:
            raise InvalidExprError(f"Function '{node.func.id}' is not allowed.")
        if node.keywords:
            raise InvalidExprError("Keyword arguments are not allowed.")
        for arg in node.args:
            _check_node(arg)
        return
    if isinstance(node, py_ast.Tuple):
        # Used for limits of integrals and sums: integrate(x, (x, 0, 1)).
        for element in node.elts:
            _check_node(element)
        return
    raise InvalidExprError(f"Unsupported syntax: {type(node).__name__}")


def _check_identifier(name: str) -> None:
    if name.startswith("_"):
        raise InvalidExprError(f"Identifier '{name}' is not allowed.")
