import pytest
from core.parser import Parser
from core.evaluator import Evaluator, EvaluationError

def test_arithmetic_normalization():
    source = "x = 2 + 3 * 2"
    program = Parser(source).parse()
    evaluator = Evaluator(program)
    evaluator.run()
    # 2 + 6 -> 8
    assert evaluator.expressions["x"].value == 8

def test_fraction_normalization():
    source = "y = 1/2 + 1/3"
    program = Parser(source).parse()
    evaluator = Evaluator(program)
    evaluator.run()
    
    result = evaluator.expressions["y"]
    # 1/2 + 1/3 -> 5/6
    assert result.left.value == 5
    assert result.right.value == 6

def test_identifier_substitution():
    source = """
    a = 2
    b = 3
    c = a + b
    """
    program = Parser(source).parse()
    evaluator = Evaluator(program)
    evaluator.run()
    assert evaluator.expressions["c"].value == 5

def test_symbolic_fraction_reduction():
    source = "z = (2*a) / (4*a)"
    program = Parser(source).parse()
    evaluator = Evaluator(program)
    evaluator.run()
    
    result = evaluator.expressions["z"]
    # (2*a)/(4*a) -> 1/2
    assert result.left.value == 1
    assert result.right.value == 2

def test_show_statement():
    source = """
    x = 10 / 2
    show x
    """
    program = Parser(source).parse()
    evaluator = Evaluator(program)
    results = evaluator.run()
    
    messages = [r.message for r in results]
    
    assert "x = (10) / (2) → 5 (value: 5)" in messages
    assert "show x → 5" in messages
    assert "Output: 5" in messages

def test_division_by_zero_error():
    source = "x = 1 / 0"
    program = Parser(source).parse()
    evaluator = Evaluator(program)
    
    with pytest.raises(EvaluationError, match="Division by zero"):
        evaluator.run()
