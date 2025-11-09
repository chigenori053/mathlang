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
    assert isinstance(assign_a.expression, ast.NumberLiteral)

    assign_b = program.statements[1]
    assert isinstance(assign_b, ast.Assignment)
    expr = assign_b.expression
    assert isinstance(expr, ast.BinaryOp)
    assert isinstance(expr.left, ast.Identifier)
    assert isinstance(expr.right, ast.NumberLiteral)

    assert isinstance(program.statements[2], ast.Show)


def test_operator_precedence_and_associativity():
    source = "result = 2 + 3 * 4 ^ 2"
    program = Parser(source).parse()
    assignment = program.statements[0]
    assert isinstance(assignment, ast.Assignment)
    expr = assignment.expression

    # Top level should be addition
    assert isinstance(expr, ast.BinaryOp)
    assert expr.operator == "+"

    # Right branch should be multiplication
    right = expr.right
    assert isinstance(right, ast.BinaryOp)
    assert right.operator == "*"

    # Exponent should be nested on the right branch
    exponent = right.right
    assert isinstance(exponent, ast.BinaryOp)
    assert exponent.operator == "^"


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
