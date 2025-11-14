import pytest
from core.fraction_engine import FractionEngine
from core import ast_nodes as ast

@pytest.fixture
def engine() -> FractionEngine:
    return FractionEngine()

def test_normalize_reduces_simple_fraction(engine: FractionEngine):
    """Test normalizing 2/4 to 1/2."""
    expr = ast.Div(left=ast.Int(2), right=ast.Int(4))
    normalized = engine.normalize(expr)
    assert normalized == ast.Div(left=ast.Int(1), right=ast.Int(2))

def test_normalize_reduces_to_integer(engine: FractionEngine):
    """Test normalizing 4/2 to 2."""
    expr = ast.Div(left=ast.Int(4), right=ast.Int(2))
    normalized = engine.normalize(expr)
    assert normalized == ast.Int(2)

def test_normalize_handles_sign_in_denominator(engine: FractionEngine):
    """Test normalizing 1/-2 to -1/2."""
    expr = ast.Div(left=ast.Int(1), right=ast.Int(-2))
    normalized = engine.normalize(expr)
    assert normalized == ast.Div(left=ast.Int(-1), right=ast.Int(2))

def test_add_two_fractions(engine: FractionEngine):
    """Test 1/2 + 1/3 = 5/6"""
    left = ast.Div(left=ast.Int(1), right=ast.Int(2))
    right = ast.Div(left=ast.Int(1), right=ast.Int(3))
    result = engine.add(left, right)
    assert result == ast.Div(left=ast.Int(5), right=ast.Int(6))

def test_multiply_two_fractions(engine: FractionEngine):
    """Test (1/2) * (2/3) = 1/3"""
    left = ast.Div(left=ast.Int(1), right=ast.Int(2))
    right = ast.Div(left=ast.Int(2), right=ast.Int(3))
    result = engine.multiply(left, right)
    assert result == ast.Div(left=ast.Int(1), right=ast.Int(3))

def test_divide_two_fractions(engine: FractionEngine):
    """Test (1/2) / (3/4) = 2/3"""
    left = ast.Div(left=ast.Int(1), right=ast.Int(2))
    right = ast.Div(left=ast.Int(3), right=ast.Int(4))
    result = engine.divide(left, right)
    assert result == ast.Div(left=ast.Int(2), right=ast.Int(3))

def test_multiply_fraction_by_integer(engine: FractionEngine):
    """Test (3/4) * 2 = 3/2"""
    left = ast.Div(left=ast.Int(3), right=ast.Int(4))
    right = ast.Int(2)
    result = engine.multiply(left, right)
    assert result == ast.Div(left=ast.Int(3), right=ast.Int(2))

def test_divide_fraction_by_integer(engine: FractionEngine):
    """Test (1/2) / 3 = 1/6"""
    left = ast.Div(left=ast.Int(1), right=ast.Int(2))
    right = ast.Int(3)
    result = engine.divide(left, right)
    assert result == ast.Div(left=ast.Int(1), right=ast.Int(6))

def test_divide_integer_by_fraction(engine: FractionEngine):
    """Test 3 / (1/2) = 6"""
    left = ast.Int(3)
    right = ast.Div(left=ast.Int(1), right=ast.Int(2))
    result = engine.divide(left, right)
    assert result == ast.Int(6)
