import pytest

from core.parser import Parser
from core.polynomial_evaluator import PolynomialEvaluator
from core.learning_logger import LearningLogger
from core.symbolic_engine import SymbolicEngine
from core.errors import InvalidStepError


def _normalizer():
    engine = SymbolicEngine()

    if engine.has_sympy():

        def normalize(expr: str) -> str:
            internal = engine.to_internal(expr)
            return str(internal.expand())  # type: ignore[attr-defined]

        return normalize

    assignments = [
        {"x": 1, "y": 2, "z": 3},
        {"x": 2, "y": 1, "z": 0},
    ]

    def normalize(expr: str) -> str:
        values = [str(engine.evaluate_numeric(expr, assignment)) for assignment in assignments]
        return "|".join(values)

    return normalize


def test_polynomial_evaluator_accepts_equivalent_steps():
    source = """
problem: (x + 1) * (x + 2)
step: x^2 + 3*x + 2
end: x^2 + 3*x + 2
"""
    program = Parser(source).parse()
    evaluator = PolynomialEvaluator(program, normalizer=_normalizer(), learning_logger=LearningLogger())
    records = evaluator.run()
    assert [r["phase"] for r in records] == ["problem", "step", "end"]


def test_polynomial_evaluator_detects_invalid_step():
    source = """
problem: (x + 1) * (x + 2)
step: x^2 + 2*x + 1
end: done
"""
    program = Parser(source).parse()
    evaluator = PolynomialEvaluator(program, normalizer=_normalizer())
    with pytest.raises(InvalidStepError):
        evaluator.run()
