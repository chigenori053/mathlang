import pytest
from core.parser import Parser, ParserError
from core.ast_nodes import (
    Program,
    Problem,
    PrepareNode,
    Step,
    Assignment,
    Int,
    Sym,
    Add,
    Mul,
    Div,
)
from core.i18n import get_language_pack

def test_parse_simple_problem():
    source = """
    problem MyProblem
        step:
            1 + 1 = 2
    end
    """
    parser = Parser(source)
    program = parser.parse()
    assert len(program.statements) == 1
    problem = program.statements[0]
    assert isinstance(problem, Problem)
    assert problem.name == "MyProblem"
    assert problem.prepare is None
    assert len(problem.steps) == 1
    step = problem.steps[0]
    assert isinstance(step, Step)
    assert step.before == Add(terms=[Int(1), Int(1)])
    assert step.after == Int(2)

def test_parse_problem_with_prepare():
    source = """
    problem WithPrepare
        prepare:
            x = 1
            y = 2
        step:
            x + y = 3
    end
    """
    parser = Parser(source)
    program = parser.parse()
    problem = program.statements[0]
    assert isinstance(problem, Problem)
    assert problem.name == "WithPrepare"
    assert isinstance(problem.prepare, PrepareNode)
    assert len(problem.prepare.assignments) == 2
    assert problem.prepare.assignments[0] == Assignment(target="x", expression=Int(1))
    assert len(problem.steps) == 1
    step = problem.steps[0]
    assert step.before == Add(terms=[Sym("x"), Sym("y")])
    assert step.after == Int(3)

def test_parse_multiple_steps():
    source = """
    problem MultiStep
        step:
            2 * 3 = 6
        step:
            6 / 2 = 3
    end
    """
    parser = Parser(source)
    program = parser.parse()
    problem = program.statements[0]
    assert len(problem.steps) == 2
    assert problem.steps[0].before == Mul(factors=[Int(2), Int(3)])
    assert problem.steps[1].before == Div(left=Int(6), right=Int(2))

def test_parser_error_on_missing_end():
    source = """
    problem MissingEnd
        step: 1 = 1
    """
    parser = Parser(source)
    with pytest.raises(ParserError, match="Expected 'end' to close problem block"):
        parser.parse()

def test_parser_error_on_bad_step():
    source = """
    problem BadStep
        step: 1 +
    end
    """
    parser = Parser(source)
    with pytest.raises(ParserError, match="Unexpected token"):
        parser.parse()
