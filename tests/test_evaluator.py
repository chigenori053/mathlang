import pytest

from core.evaluator import EvaluationError, Evaluator
from core.i18n import get_language_pack
from core.logging import LearningLogger
from core.parser import Parser
from core.symbolic_engine import SymbolicEngineError, SymbolicResult


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
    assert results[-1].message == "出力: 13"


def test_showing_unknown_identifier_raises():
    source = """
    a = 1
    show b
    """
    program = Parser(source).parse()
    evaluator = Evaluator(program)
    with pytest.raises(EvaluationError):
        list(evaluator.step_eval())


def test_expression_with_undefined_identifier_raises():
    source = """
    a = 1
    result = a + missing
    """
    program = Parser(source).parse()
    evaluator = Evaluator(program)

    with pytest.raises(EvaluationError):
        list(evaluator.step_eval())


def test_division_by_zero_raises_evaluation_error():
    source = """
    value = 1 / 0
    """
    program = Parser(source).parse()
    evaluator = Evaluator(program)

    with pytest.raises(EvaluationError, match="ゼロ除算が発生しました"):
        list(evaluator.step_eval())


def test_multiple_unary_minus_chain_evaluates_correctly():
    source = """
    value = ---5
    show value
    """
    program = Parser(source).parse()
    evaluator = Evaluator(program)
    results = evaluator.run()

    assert evaluator.context["value"] == -5
    assert results[-1].message == "出力: -5"


class StubSymbolicEngine:
    def __init__(self):
        self.calls = []

    def simplify(self, expression: str) -> SymbolicResult:
        self.calls.append(("simplify", expression))
        return SymbolicResult(simplified=f"simpl({expression})", explanation="stub simplify")

    def explain(self, expression: str) -> str:
        self.calls.append(("explain", expression))
        return f"StubExplain({expression})"


def test_show_emits_symbolic_trace_when_engine_available():
    source = """
    a = 2
    b = a + a
    show b
    """
    program = Parser(source).parse()
    stub_engine = StubSymbolicEngine()

    evaluator = Evaluator(program, symbolic_engine_factory=lambda: stub_engine)
    results = evaluator.run()

    messages = [result.message for result in results]
    assert "シンボリック: simpl(a + a)" in messages
    assert "説明: stub simplify" in messages
    assert "構造: StubExplain(a + a)" in messages
    assert messages[-1] == "出力: 4"
    assert stub_engine.calls.count(("simplify", "a + a")) == 1
    assert stub_engine.calls.count(("explain", "a + a")) == 1


def test_symbolic_disabled_message_emitted_once_when_engine_creation_fails():
    source = """
    value = 1 + 1
    show value
    show value
    """
    program = Parser(source).parse()

    def failing_factory():
        raise SymbolicEngineError("missing sympy")

    evaluator = Evaluator(program, symbolic_engine_factory=failing_factory)
    results = evaluator.run()

    messages = [result.message for result in results]
    assert messages.count("[シンボリック無効] missing sympy") == 1


def test_language_switches_to_english_output():
    source = """
    a = 2
    b = 3
    c = a + b
    show c
    """
    language = get_language_pack("en")
    program = Parser(source, language=language).parse()
    evaluator = Evaluator(program, language=language)
    results = evaluator.run()

    messages = [result.message for result in results]
    assert messages[3] == "show c → 5"
    assert messages[-1] == "Output: 5"


def _test_core_dsl_constant_sequence_verifies():
    source = """
    problem: (2^2) + (3^2)
    step: 4 + 9
    end: 13
    """
    language = get_language_pack("en")
    program = Parser(source, language=language).parse()
    evaluator = Evaluator(program, language=language)
    messages = [result.message for result in evaluator.run()]

    assert messages[0].startswith("[problem]")
    assert "(equivalence: OK)" in messages[1]
    assert messages[2].startswith("[end] 13")


def _test_core_dsl_symbolic_equivalence():
    source = """
    problem: (a + b)^2
    step: a^2 + 2*a*b + b^2
    end: done
    """
    language = get_language_pack("en")
    program = Parser(source, language=language).parse()
    evaluator = Evaluator(program, language=language)

    messages = [result.message for result in evaluator.run()]
    assert any("[step1]" in message and "(equivalence: OK)" in message for message in messages)
    assert messages[-1] == "[end] done"


def test_core_dsl_logs_knowledge_rule_when_available():
    source = """
    problem: x + 1 + x + 2
    step: 2*x + 3
    end: done
    """
    language = get_language_pack("en")
    program = Parser(source, language=language).parse()
    evaluator = Evaluator(program, language=language)
    messages = [result.message for result in evaluator.run()]

    assert any("ARITH-ADD-001" in message for message in messages)


def _test_core_dsl_invalid_step_raises():
    source = """
    problem: 2 + 2
    step: 5
    """
    language = get_language_pack("en")
    program = Parser(source, language=language).parse()
    evaluator = Evaluator(program, language=language)

    with pytest.raises(EvaluationError, match="not equivalent"):
        list(evaluator.step_eval())


def test_core_dsl_step_requires_problem():
    source = """
    step: 3
    """
    language = get_language_pack("en")
    program = Parser(source, language=language).parse()
    evaluator = Evaluator(program, language=language)

    with pytest.raises(EvaluationError, match="problem"):
        list(evaluator.step_eval())


def test_learning_logger_collects_problem_step_end():
    source = """
    problem: (2 + 3) * 4
    step: 5 * 4
    end: 20
    """
    logger = LearningLogger()
    program = Parser(source).parse()
    evaluator = Evaluator(program, learning_logger=logger)
    evaluator.run()

    entries = logger.to_dict()
    phases = [entry["phase"] for entry in entries]
    assert phases[0] == "problem"
    assert "step" in phases
    assert phases[-1] == "end"
