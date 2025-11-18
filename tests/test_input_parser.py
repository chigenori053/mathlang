from core.input_parser import MathLangInputParser


def normalize(expr: str) -> str:
    return MathLangInputParser.normalize(expr)


def test_caret_power_and_parentheses():
    assert normalize("(x - y)^2") == "(x - y)**2"
    assert normalize("(x - y)(x + y)") == "(x - y)*(x + y)"


def test_implicit_multiplication_runs_and_numbers():
    assert normalize("2xy + 3x") == "2*x*y + 3*x"
    assert normalize("(x - y) (x - y)") == "(x - y)*(x - y)"


def test_unicode_sqrt_and_mixed_terms():
    assert normalize("√x + 2y") == "sqrt(x) + 2*y"
    assert normalize("3(x+1)^2") == "3*(x + 1)**2"
