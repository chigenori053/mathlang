import pytest
from core.parser import Parser
from core.evaluator import Evaluator, EvaluationError

def test_evaluator_verifies_correct_step():
    source = """
    problem CorrectStep
        step:
            1 + 2 = 3
    end
    """
    program = Parser(source).parse()
    evaluator = Evaluator(program)
    results = evaluator.run()
    
    assert len(results) == 2
    assert "Problem: CorrectStep" in results[0].message
    assert "Step 1: 1 + 2 = 3 (Verified)" in results[1].message

def test_evaluator_fails_incorrect_step():
    source = """
    problem IncorrectStep
        step:
            1 + 2 = 4
    end
    """
    program = Parser(source).parse()
    evaluator = Evaluator(program)
    results = evaluator.run()
    
    assert len(results) == 2
    assert "Failed: Expected 3, got 4" in results[1].message

def test_evaluator_handles_prepare_and_substitution():
    source = """
    problem WithPrepare
        prepare:
            x = 2
            y = 3
        step:
            x * y = 6
    end
    """
    program = Parser(source).parse()
    evaluator = Evaluator(program)
    results = evaluator.run()
    
    messages = [r.message for r in results]
    assert "Problem: WithPrepare" in messages[0]
    assert "Prepare: x = 2" in messages[1]
    assert "Prepare: y = 3" in messages[2]
    assert "Step 1: x * y = 6 (Verified)" in messages[3]

def test_evaluator_handles_fraction_step():
    source = """
    problem FractionStep
        step:
            1/2 + 1/3 = 5/6
    end
    """
    program = Parser(source).parse()
    evaluator = Evaluator(program)
    results = evaluator.run()
    
    assert "Step 1: (1) / (2) + (1) / (3) = (5) / (6) (Verified)" in results[1].message
