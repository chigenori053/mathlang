import math

from core import ast_nodes as ast
from core.optimizer import constant_fold, optimize_expression, substitute_identifiers


def make_binary(left, operator, right):
    return ast.BinaryOp(left=left, operator=operator, right=right)


def test_substitute_identifiers_expands_assignments():
    expr = make_binary(ast.Identifier("x"), "+", ast.NumberLiteral(1))
    mapping = {
        "x": make_binary(ast.NumberLiteral(2), "*", ast.Identifier("y")),
        "y": ast.NumberLiteral(3),
    }

    substituted = substitute_identifiers(expr, mapping)

    assert isinstance(substituted.left, ast.BinaryOp)
    assert isinstance(substituted.left.left, ast.NumberLiteral)
    assert substituted.left.left.value == 2
    assert isinstance(substituted.left.right, ast.NumberLiteral)
    assert substituted.left.right.value == 3


def test_constant_fold_handles_arithmetic_operations():
    expr = make_binary(
        make_binary(ast.NumberLiteral(2), "+", ast.NumberLiteral(3)),
        "*",
        make_binary(ast.NumberLiteral(5), "-", ast.NumberLiteral(1)),
    )

    folded = constant_fold(expr)

    assert isinstance(folded, ast.NumberLiteral)
    assert folded.value == 20


def test_optimize_expression_combines_substitution_and_folding():
    expr = make_binary(ast.Identifier("x"), "^", ast.NumberLiteral(2))
    mapping = {"x": make_binary(ast.NumberLiteral(3), "+", ast.NumberLiteral(4))}

    optimized = optimize_expression(expr, mapping)

    assert isinstance(optimized, ast.NumberLiteral)
    assert optimized.value == math.pow(7, 2)

