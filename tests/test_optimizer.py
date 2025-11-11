import math

from core import ast_nodes as ast
from core.optimizer import constant_fold, optimize_expression, substitute_identifiers

def test_substitute_identifiers_expands_assignments():
    expr = ast.Add(terms=[ast.Sym("x"), ast.Int(1)])
    mapping = {
        "x": ast.Mul(factors=[ast.Int(2), ast.Sym("y")]),
        "y": ast.Int(3),
    }

    substituted = substitute_identifiers(expr, mapping)

    assert isinstance(substituted, ast.Add)
    assert isinstance(substituted.terms[0], ast.Mul)
    assert isinstance(substituted.terms[0].factors[0], ast.Int)
    assert substituted.terms[0].factors[0].value == 2
    assert isinstance(substituted.terms[0].factors[1], ast.Int)
    assert substituted.terms[0].factors[1].value == 3


def test_constant_fold_handles_arithmetic_operations():
    expr = ast.Mul(factors=[
        ast.Add(terms=[ast.Int(2), ast.Int(3)]),
        ast.Add(terms=[ast.Int(5), ast.Neg(ast.Int(1))])
    ])

    folded = constant_fold(expr)

    assert isinstance(folded, ast.Int)
    assert folded.value == 20


def test_optimize_expression_combines_substitution_and_folding():
    expr = ast.Pow(base=ast.Sym("x"), exp=ast.Int(2))
    mapping = {"x": ast.Add(terms=[ast.Int(3), ast.Int(4)])}

    optimized = optimize_expression(expr, mapping)

    assert isinstance(optimized, ast.Int)
    assert optimized.value == math.pow(7, 2)