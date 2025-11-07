import pytest

from core.evaluator import EvaluationError, Evaluator
from core.parser import Parser


def test_stepwise_evaluation_produces_expected_trace():
    source = """
    a = 2
    b = 3
    c = a^2 + b^2
    show c
    """
    program = Parser(source).parse()
    evaluator = Evaluator(program)
    results = evaluator.run()

    # Four steps plus final output
    assert len(results) == 5
    assert evaluator.context["c"] == 13
    assert results[-1].message == "Output: 13"


def test_showing_unknown_identifier_raises():
    source = """
    a = 1
    show b
    """
    program = Parser(source).parse()
    evaluator = Evaluator(program)
    with pytest.raises(EvaluationError):
        list(evaluator.step_eval())
