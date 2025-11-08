import pytest

from core.symbolic_engine import SymbolicEngine, SymbolicEngineError


class FakeExpr:
    def __init__(self, text: str):
        self.text = text.strip()

    def __str__(self) -> str:  # pragma: no cover - trivial string conversion.
        return self.text

    def __eq__(self, other: object) -> bool:  # pragma: no cover - structural equality.
        return isinstance(other, FakeExpr) and self.text == other.text


class FakeSymPy:
    def sympify(self, expression: str) -> FakeExpr:
        if expression.strip() == "??":
            raise ValueError("invalid expression")
        return FakeExpr(expression)

    def simplify(self, expr: FakeExpr) -> FakeExpr:
        if expr.text.endswith(" + 0"):
            return FakeExpr(expr.text[:-4])
        return expr

    def srepr(self, expr: FakeExpr) -> str:
        return f"FakeExpr({expr.text})"


def test_simplify_reports_transformation():
    engine = SymbolicEngine(sympy_module=FakeSymPy())
    result = engine.simplify("a + 0")

    assert result.simplified == "a"
    assert "Simplified" in result.explanation


def test_explain_returns_structured_representation():
    engine = SymbolicEngine(sympy_module=FakeSymPy())
    assert engine.explain("x + y") == "FakeExpr(x + y)"


def test_engine_raises_when_sympy_missing(monkeypatch):
    # Simulate that the initial import of sympy failed.
    monkeypatch.setattr("core.symbolic_engine._sympy", None)

    with pytest.raises(SymbolicEngineError, match="SymPy is not available"):
        SymbolicEngine()
