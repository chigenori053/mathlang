import pytest

from core.evaluator import EvaluationError, Evaluator
from core.i18n import get_language_pack
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
    assert "シンボリック: simpl(4)" in messages
    assert "説明: stub simplify" in messages
    assert "構造: StubExplain(4)" in messages
    assert messages[-1] == "出力: 4"
    assert stub_engine.calls.count(("simplify", "4")) == 1
    assert stub_engine.calls.count(("explain", "4")) == 1


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
