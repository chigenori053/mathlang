"""AST最適化ユーティリティ（Phase 2）。"""

from __future__ import annotations

from typing import Dict, Iterable, Set

from . import ast_nodes as ast


def clone_expression(expression: ast.Expression) -> ast.Expression:
    """式ノードをディープコピーする。"""

    if isinstance(expression, ast.NumberLiteral):
        return ast.NumberLiteral(value=expression.value)
    if isinstance(expression, ast.Identifier):
        return ast.Identifier(name=expression.name)
    if isinstance(expression, ast.BinaryOp):
        return ast.BinaryOp(
            left=clone_expression(expression.left),
            operator=expression.operator,
            right=clone_expression(expression.right),
        )
    raise TypeError(f"Unsupported expression type: {type(expression)!r}")


def substitute_identifiers(
    expression: ast.Expression,
    mapping: Dict[str, ast.Expression],
    _visited: Iterable[str] | None = None,
) -> ast.Expression:
    """識別子を代入式で再帰的に展開する。

    `_visited` は循環参照を検出し、無限再帰を防ぐための内部利用。
    """

    visited: Set[str] = set(_visited or ())

    if isinstance(expression, ast.Identifier):
        if expression.name in visited:
            return ast.Identifier(name=expression.name)
        if expression.name not in mapping:
            return ast.Identifier(name=expression.name)
        visited.add(expression.name)
        substituted = substitute_identifiers(mapping[expression.name], mapping, visited)
        return clone_expression(substituted)

    if isinstance(expression, ast.BinaryOp):
        return ast.BinaryOp(
            left=substitute_identifiers(expression.left, mapping, visited),
            operator=expression.operator,
            right=substitute_identifiers(expression.right, mapping, visited),
        )

    return clone_expression(expression)


def constant_fold(expression: ast.Expression) -> ast.Expression:
    """数値リテラルのみで構成された演算を定数畳み込みする。"""

    if isinstance(expression, ast.BinaryOp):
        left = constant_fold(expression.left)
        right = constant_fold(expression.right)

        if isinstance(left, ast.NumberLiteral) and isinstance(right, ast.NumberLiteral):
            operator = expression.operator

            if operator == "+":
                return ast.NumberLiteral(value=left.value + right.value)
            if operator == "-":
                return ast.NumberLiteral(value=left.value - right.value)
            if operator == "*":
                return ast.NumberLiteral(value=left.value * right.value)
            if operator == "/":
                if right.value == 0:
                    # 0除算はそのまま戻し、Evaluator側でエラーにする
                    return ast.BinaryOp(left=left, operator=operator, right=right)
                return ast.NumberLiteral(value=left.value / right.value)
            if operator == "^":
                return ast.NumberLiteral(value=left.value**right.value)

        return ast.BinaryOp(left=left, operator=expression.operator, right=right)

    return clone_expression(expression)


def optimize_expression(expression: ast.Expression, environment: Dict[str, ast.Expression]) -> ast.Expression:
    """環境を考慮して式を最適化（代入展開＋定数畳み込み）する。"""

    substituted = substitute_identifiers(expression, environment)
    return constant_fold(substituted)

