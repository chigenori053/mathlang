import pytest

from core.logging import LearningLogger
from core.parser import Parser
from core.polynomial_evaluator import PolynomialEvaluationError, PolynomialEvaluator
from core.i18n import get_language_pack
from main import _run_polynomial_mode


def _run_program(source: str) -> tuple[PolynomialEvaluator, list]:
    program = Parser(source, language=get_language_pack("en")).parse()
    evaluator = PolynomialEvaluator(program, language=get_language_pack("en"))
    results = evaluator.run()
    return evaluator, results


def _collect_outputs(results):
    return [result.message for result in results if result.step_number == 0]


def test_addition_is_commutative():
    source = """
    a = x + y
    b = y + x
    show a
    show b
    """
    evaluator, results = _run_program(source)

    assert evaluator.context["a"] == evaluator.context["b"]
    outputs = _collect_outputs(results)
    assert outputs[-2] == "Output: x + y"
    assert outputs[-1] == "Output: x + y"


def test_multiplication_is_commutative():
    source = """
    result1 = x * y
    result2 = y * x
    show result1
    show result2
    """
    evaluator, results = _run_program(source)

    assert evaluator.context["result1"] == evaluator.context["result2"]
    outputs = _collect_outputs(results)
    assert outputs[-2] == "Output: x*y"
    assert outputs[-1] == "Output: x*y"


def test_associativity_and_distributivity():
    source = """
    left = (x + y) + z
    right = x + (y + z)
    distributed = x * (y + z)
    expanded = x * y + x * z
    show left
    show right
    show distributed
    show expanded
    """
    evaluator, results = _run_program(source)

    assert evaluator.context["left"] == evaluator.context["right"]
    assert evaluator.context["distributed"] == evaluator.context["expanded"]
    outputs = _collect_outputs(results)
    assert outputs[-4] == "Output: x + y + z"
    assert outputs[-3] == "Output: x + y + z"
    assert outputs[-2] == "Output: x*y + x*z"
    assert outputs[-1] == "Output: x*y + x*z"


def test_polynomial_power_and_scalar_division():
    source = """
    square = (x + y)^2
    normalized = (2 * x) / 2
    show square
    show normalized
    """
    evaluator, results = _run_program(source)

    assert evaluator.context["square"].__str__() == "x^2 + 2*x*y + y^2"
    assert evaluator.context["normalized"].__str__() == "x"
    outputs = _collect_outputs(results)
    assert "Output: x^2 + 2*x*y + y^2" in outputs
    assert "Output: x" in outputs


def test_polynomial_division_by_variable_raises():
    source = """
    result = x / y
    """
    program = Parser(source, language=get_language_pack("en")).parse()
    evaluator = PolynomialEvaluator(program, language=get_language_pack("en"))

    with pytest.raises(PolynomialEvaluationError):
        list(evaluator.step_eval())


def test_cli_polynomial_mode_outputs_distribution(capsys):
    language = get_language_pack("en")
    rc = _run_polynomial_mode("x * (y + z)", language)
    assert rc == 0

    captured = capsys.readouterr()
    assert "x*y + x*z" in captured.out


def test_core_polynomial_program_verifies_steps():
    source = """
    problem: (x + 1) + (x + 2)
    step1: x + 1 + x + 2
    step2: 2*x + 3
    end: 2*x + 3
    """
    evaluator, results = _run_program(source)
    messages = [res.message for res in results]

    assert any("[problem]" in msg and "2*x + 3" in msg for msg in messages)
    assert any("[step2]" in msg and "ARITH-ADD-001" in msg for msg in messages)
    assert any("[end]" in msg and "2*x + 3" in msg for msg in messages)


def test_core_polynomial_invalid_step_raises():
    source = """
    problem: x + 1
    step: x + 2
    """
    program = Parser(source, language=get_language_pack("en")).parse()
    evaluator = PolynomialEvaluator(program, language=get_language_pack("en"))

    with pytest.raises(PolynomialEvaluationError):
        list(evaluator.step_eval())


def test_polynomial_learning_logger_includes_rule_metadata():
    source = """
    problem: (x + 1) + (x + 2)
    step: 2*x + 3
    end: done
    """
    logger = LearningLogger()
    program = Parser(source, language=get_language_pack("en")).parse()
    evaluator = PolynomialEvaluator(program, language=get_language_pack("en"), learning_logger=logger)
    evaluator.run()

    assert any(entry["rule_id"] == "ARITH-ADD-001" for entry in logger.to_dict())

