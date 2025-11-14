import pytest
from core.parser import Parser, ParserError
from core.ast_nodes import (
    Program,
    Assignment,
    ExpressionStatement,
    Int,
    Sym,
    Add,
    Mul,
    Pow,
    Div,
    Neg,
)

def test_parse_assignment():
    source = "x = 10"
    parser = Parser(source)
    program = parser.parse()
    assert isinstance(program, Program)
    assert len(program.statements) == 1
    statement = program.statements[0]
    assert isinstance(statement, Assignment)
    assert statement.target == "x"
    assert statement.expression == Int(value=10)

def test_parse_expression_statement():
    source = "2 + 2"
    parser = Parser(source)
    program = parser.parse()
    assert isinstance(program, Program)
    assert len(program.statements) == 1
    statement = program.statements[0]
    assert isinstance(statement, ExpressionStatement)
    assert statement.expression == Add(terms=[Int(value=2), Int(value=2)])

def test_parse_division():
    source = "a / b"
    parser = Parser(source)
    program = parser.parse()
    statement = program.statements[0]
    assert isinstance(statement, ExpressionStatement)
    assert statement.expression == Div(left=Sym("a"), right=Sym("b"))

def test_parse_precedence():
    source = "1 + 2 * 3"
    parser = Parser(source)
    program = parser.parse()
    statement = program.statements[0]
    assert isinstance(statement, ExpressionStatement)
    assert statement.expression == Add(
        terms=[Int(value=1), Mul(factors=[Int(value=2), Int(value=3)])]
    )

def test_parse_parentheses():
    source = "(1 + 2) * 3"
    parser = Parser(source)
    program = parser.parse()
    statement = program.statements[0]
    assert isinstance(statement, ExpressionStatement)
    assert statement.expression == Mul(
        factors=[Add(terms=[Int(value=1), Int(value=2)]), Int(value=3)]
    )

from core.i18n import get_language_pack

def test_parser_error_handling():
    source = "show @"
    # Force english for consistent error message
    en_pack = get_language_pack("en")
    with pytest.raises(ParserError, match="Unexpected character"):
        Parser(source, language=en_pack).parse()
