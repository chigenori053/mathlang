import pytest

from core.evaluator import Evaluator, SymbolicEvaluationEngine, Engine
from core.knowledge_registry import KnowledgeRegistry
from core.learning_logger import LearningLogger
from core.parser import Parser
from core.symbolic_engine import SymbolicEngine
from core.errors import (
    InvalidStepError,
    InconsistentEndError,
    MissingProblemError,
    SyntaxError as DslSyntaxError,
)
from core.fuzzy.types import FuzzyLabel, FuzzyResult, FuzzyScore
from pathlib import Path


def _program_from_source(source: str):
    return Parser(source).parse()


def _engine():
    sym = SymbolicEngine()
    registry = KnowledgeRegistry(Path("core/knowledge"), sym)
    return SymbolicEvaluationEngine(sym, registry)


def test_evaluator_runs_problem_step_end():
    program = _program_from_source(
        """
problem: (x + 1) * (x + 2)
step: x^2 + 3*x + 2
end: x^2 + 3*x + 2
"""
    )
    logger = LearningLogger()
    evaluator = Evaluator(program, _engine(), learning_logger=logger)
    records = evaluator.run()
    assert len(records) == 3
    assert records[0]["phase"] == "problem"
    assert records[1]["phase"] == "step"
    assert records[2]["phase"] == "end"


def test_evaluator_invalid_step_raises():
    program = _program_from_source(
        """
problem: 1 + 1
step: 3
end: done
"""
    )
    evaluator = Evaluator(program, _engine())
    with pytest.raises(InvalidStepError):
        evaluator.run()


def test_evaluator_end_mismatch_raises():
    program = _program_from_source(
        """
problem: 1 + 1
end: 3
"""
    )
    evaluator = Evaluator(program, _engine())
    with pytest.raises(InconsistentEndError):
        evaluator.run()


def test_evaluator_requires_problem():
    with pytest.raises(DslSyntaxError):
        _program_from_source(
            """
step: 1 + 1
end: done
"""
        )


class AlwaysInvalidEngine(Engine):
    def __init__(self) -> None:
        self._current = None

    def set(self, expr: str) -> None:
        self._current = expr

    def check_step(self, expr: str) -> dict:
        return {
            "before": self._current or "",
            "after": expr,
            "valid": False,
            "rule_id": "RULE-1",
            "details": {},
        }

    def finalize(self, expr: str | None) -> dict:
        return {"before": self._current, "after": expr, "valid": False, "rule_id": None, "details": {}}


class StubFuzzyJudge:
    def __init__(self) -> None:
        self.calls = 0

    def judge_step(self, **kwargs) -> FuzzyResult:
        self.calls += 1
        return {
            "label": FuzzyLabel.UNKNOWN,
            "score": FuzzyScore(
                expr_similarity=0.5,
                rule_similarity=0.0,
                text_similarity=0.0,
                combined_score=0.5,
            ),
            "reason": "stub",
            "debug": {},
        }


def test_evaluator_logs_fuzzy_when_invalid_step():
    source = """
problem: 1 + 1
step: 3
end: done
"""
    program = Parser(source).parse()
    fuzzy = StubFuzzyJudge()
    logger = LearningLogger()
    evaluator = Evaluator(program, AlwaysInvalidEngine(), learning_logger=logger, fuzzy_judge=fuzzy)
    with pytest.raises(InvalidStepError):
        evaluator.run()
    assert fuzzy.calls == 1
    assert any(record["phase"] == "fuzzy" for record in logger.to_list())


class RecordingFuzzyJudge:
    def __init__(self, label: FuzzyLabel) -> None:
        self.label = label
        self.calls = 0

    def judge_step(self, **kwargs) -> FuzzyResult:
        self.calls += 1
        return {
            "label": self.label,
            "score": FuzzyScore(
                expr_similarity=0.6,
                rule_similarity=0.0,
                text_similarity=0.0,
                combined_score=0.6,
            ),
            "reason": "recorded",
            "debug": {"candidate_raw": kwargs["candidate_expr"]["raw"]},
        }


def _assert_fuzzy_label(logger: LearningLogger, expected: FuzzyLabel) -> None:
    entries = [r for r in logger.to_list() if r["phase"] == "fuzzy"]
    assert entries, "expected fuzzy log entry"
    assert entries[-1]["meta"]["label"] == expected


def test_arithmetic_equivalent_step():
    source = """
problem: (3 + 5) * 2
step: 16
end: 16
"""
    program = Parser(source).parse()
    evaluator = Evaluator(program, _engine())
    records = evaluator.run()
    assert records[-1]["phase"] == "end"


def test_arithmetic_non_equivalent_triggers_fuzzy():
    source = """
problem: (3 + 5) * 2
step: 15
end: done
"""
    program = Parser(source).parse()
    fuzzy = RecordingFuzzyJudge(FuzzyLabel.ANALOGOUS)
    logger = LearningLogger()
    evaluator = Evaluator(program, _engine(), learning_logger=logger, fuzzy_judge=fuzzy)
    with pytest.raises(InvalidStepError):
        evaluator.run()
    assert fuzzy.calls == 1
    _assert_fuzzy_label(logger, FuzzyLabel.ANALOGOUS)


def test_polynomial_non_equivalent_triggers_fuzzy():
    source = """
problem: (x + 1) * (x + 2)
step: x^2 + 2*x + 1
end: done
"""
    program = Parser(source).parse()
    fuzzy = RecordingFuzzyJudge(FuzzyLabel.APPROX_EQ)
    logger = LearningLogger()
    evaluator = Evaluator(program, _engine(), learning_logger=logger, fuzzy_judge=fuzzy)
    with pytest.raises(InvalidStepError):
        evaluator.run()
    _assert_fuzzy_label(logger, FuzzyLabel.APPROX_EQ)


def test_fraction_non_equivalent_triggers_fuzzy():
    source = """
problem: 1/2 + 1/3
step: 2/3
end: done
"""
    program = Parser(source).parse()
    fuzzy = RecordingFuzzyJudge(FuzzyLabel.CONTRADICT)
    logger = LearningLogger()
    evaluator = Evaluator(program, _engine(), learning_logger=logger, fuzzy_judge=fuzzy)
    with pytest.raises(InvalidStepError):
        evaluator.run()
    _assert_fuzzy_label(logger, FuzzyLabel.CONTRADICT)
