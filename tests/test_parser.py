import pytest

from core import ast_nodes as ast
from core.parser import Parser, ParserError


def test_parse_sequential_statements():
    source = """
    a = 2
    b = a + 3
    show b
    """
    program = Parser(source).parse()
    assert isinstance(program, ast.Program)
    assert len(program.statements) == 3

    assign_a = program.statements[0]
    assert isinstance(assign_a, ast.Assignment)
    assert assign_a.target == "a"
    assert isinstance(assign_a.expression, ast.Int)
    assert assign_a.expression.value == 2

    assign_b = program.statements[1]
    assert isinstance(assign_b, ast.Assignment)
    expr = assign_b.expression
    assert isinstance(expr, ast.Add)
    assert isinstance(expr.terms[0], ast.Sym)
    assert expr.terms[0].name == "a"
    assert isinstance(expr.terms[1], ast.Int)
    assert expr.terms[1].value == 3

    assert isinstance(program.statements[2], ast.Show)


def test_operator_precedence_and_associativity():
    source = "result = 2 + 3 * 4 ^ 2"
    program = Parser(source).parse()
    assignment = program.statements[0]
    assert isinstance(assignment, ast.Assignment)
    expr = assignment.expression

    # Top level should be addition
    assert isinstance(expr, ast.Add)
    assert isinstance(expr.terms[0], ast.Int)
    assert expr.terms[0].value == 2

    # Right branch should be multiplication
    right = expr.terms[1]
    assert isinstance(right, ast.Mul)
    assert isinstance(right.factors[0], ast.Int)
    assert right.factors[0].value == 3

    # Exponent should be nested on the right branch
    exponent = right.factors[1]
    assert isinstance(exponent, ast.Pow)
    assert isinstance(exponent.base, ast.Int)
    assert exponent.base.value == 4
    assert isinstance(exponent.exp, ast.Int)
    assert exponent.exp.value == 2


def test_invalid_character_raises_error():
    with pytest.raises(ParserError):
        Parser("a = 2 $ 3").parse()


def test_comments_and_blank_lines_are_ignored():
    source = """
    # setup values
    a = 1

    # compute
    result = (a + 2) * 3
    show result
    """
    program = Parser(source).parse()
    assert len(program.statements) == 3


def test_show_requires_identifier():
    with pytest.raises(ParserError):
        Parser("show\n").parse()


def test_core_dsl_statements_are_parsed():
    source = """
    problem: (2 + 3)
    step1: 5
    step[hint]: 5
    explain: "addition"
    end: done
    """
    program = Parser(source).parse()
    assert len(program.statements) == 5

    assert isinstance(program.statements[0], ast.Problem)

    step1 = program.statements[1]
    assert isinstance(step1, ast.Step)
    assert step1.label == "step1"

    step_hint = program.statements[2]
    assert isinstance(step_hint, ast.Step)
    assert step_hint.label == "step[hint]"

    explain = program.statements[3]
    assert isinstance(explain, ast.Explain)
    assert explain.message == "addition"

    end = program.statements[4]
    assert isinstance(end, ast.End)
    assert end.done is True
