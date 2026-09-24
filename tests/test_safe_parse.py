"""Tests for the whitelist-based expression parser guarding SymPy."""

from __future__ import annotations

import pytest

from core.errors import InvalidExprError
from core.safe_parse import safe_sympify, validate_expression
from core.symbolic_engine import SymbolicEngine
from core.unit_engine import UnitEngine


@pytest.mark.parametrize(
    "expr, expected",
    [
        ("(x + 1)^2", "(x + 1)**2"),
        ("sqrt(8)", "2*sqrt(2)"),
        ("Rational(1, 3) + 1", "4/3"),
        ("integrate(x, (x, 0, 1))", "1/2"),
        ("-x + 2*pi", "-x + 2*pi"),
    ],
)
def test_safe_sympify_accepts_math(expr, expected):
    assert str(safe_sympify(expr)) == expected


@pytest.mark.parametrize(
    "expr",
    [
        "__import__('os').getcwd()",
        "open('/etc/passwd')",
        "x.__class__",
        "Symbol('x')",
        "(lambda: 1)()",
        "[1, 2]",
        "'text'",
        "sqrt(x=2)",
        "_x + 1",
        "x if y else z",
        "",
        "1 +",
    ],
)
def test_safe_sympify_rejects_unsafe_or_invalid(expr):
    with pytest.raises(InvalidExprError):
        safe_sympify(expr)


def test_validate_expression_rejects_overlong_input():
    with pytest.raises(InvalidExprError, match="too long"):
        validate_expression("1+" * 6000 + "1")


def test_symbolic_engine_blocks_code_execution():
    with pytest.raises(InvalidExprError):
        SymbolicEngine().to_internal("__import__('os').system('true')")


def test_unit_engine_blocks_code_execution():
    engine = UnitEngine(SymbolicEngine())
    assert engine.convert("3 * kilometer", "meter") == "3000*meter"
    with pytest.raises(InvalidExprError):
        engine.convert("__import__('os').getcwd()", "meter")
