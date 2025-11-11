"""AST最適化ユーティリティ（Phase 2）。"""

from __future__ import annotations

from typing import Dict, Iterable, Set

from . import ast_nodes as ast

def clone_expression(expression: ast.Expr) -> ast.Expr:
    """式ノードをディープコピーする。"""
    if isinstance(expression, (ast.Int, ast.Rat, ast.Sym)):
        return expression
    if isinstance(expression, ast.Neg):
        return ast.Neg(expr=clone_expression(expression.expr))
    if isinstance(expression, ast.Add):
        return ast.Add(terms=[clone_expression(term) for term in expression.terms])
    if isinstance(expression, ast.Mul):
        return ast.Mul(factors=[clone_expression(factor) for factor in expression.factors])
    if isinstance(expression, ast.Pow):
        return ast.Pow(
            base=clone_expression(expression.base),
            exp=clone_expression(expression.exp),
        )
    if isinstance(expression, ast.Call):
        return ast.Call(
            name=expression.name,
            args=[clone_expression(arg) for arg in expression.args],
        )
    raise TypeError(f"Unsupported expression type: {type(expression)!r}")


def substitute_identifiers(
    expression: ast.Expr,
    mapping: Dict[str, ast.Expr],
    _visited: Iterable[str] | None = None,
) -> ast.Expr:
    """識別子を代入式で再帰的に展開する。

    `_visited` は循環参照を検出し、無限再帰を防ぐための内部利用。
    """
    visited: Set[str] = set(_visited or ())

    if isinstance(expression, ast.Sym):
        if expression.name in visited:
            return ast.Sym(name=expression.name)
        if expression.name not in mapping:
            return ast.Sym(name=expression.name)
        visited.add(expression.name)
        substituted = substitute_identifiers(mapping[expression.name], mapping, visited)
        return clone_expression(substituted)

    if isinstance(expression, ast.Neg):
        return ast.Neg(expr=substitute_identifiers(expression.expr, mapping, visited))
    if isinstance(expression, ast.Add):
        return ast.Add(
            terms=[substitute_identifiers(term, mapping, visited) for term in expression.terms]
        )
    if isinstance(expression, ast.Mul):
        return ast.Mul(
            factors=[substitute_identifiers(factor, mapping, visited) for factor in expression.factors]
        )
    if isinstance(expression, ast.Pow):
        return ast.Pow(
            base=substitute_identifiers(expression.base, mapping, visited),
            exp=substitute_identifiers(expression.exp, mapping, visited),
        )
    if isinstance(expression, ast.Call):
        return ast.Call(
            name=expression.name,
            args=[substitute_identifiers(arg, mapping, visited) for arg in expression.args],
        )

    return clone_expression(expression)


def constant_fold(expression: ast.Expr) -> ast.Expr:
    """数値リテラルのみで構成された演算を定数畳み込みする。"""
    if isinstance(expression, ast.Neg):
        expr = constant_fold(expression.expr)
        if isinstance(expr, ast.Int):
            return ast.Int(value=-expr.value)
        return ast.Neg(expr=expr)

    if isinstance(expression, ast.Add):
        terms = [constant_fold(term) for term in expression.terms]
        if all(isinstance(term, ast.Int) for term in terms):
            return ast.Int(value=sum(term.value for term in terms))
        return ast.Add(terms=terms)

    if isinstance(expression, ast.Mul):
        factors = [constant_fold(factor) for factor in expression.factors]
        if all(isinstance(factor, ast.Int) for factor in factors):
            result = 1
            for factor in factors:
                result *= factor.value
            return ast.Int(value=result)
        return ast.Mul(factors=factors)

    if isinstance(expression, ast.Pow):
        base = constant_fold(expression.base)
        exp = constant_fold(expression.exp)
        if isinstance(base, ast.Int) and isinstance(exp, ast.Int):
            return ast.Int(value=base.value ** exp.value)
        return ast.Pow(base=base, exp=exp)

    return clone_expression(expression)


def optimize_expression(expression: ast.Expr, environment: Dict[str, ast.Expr]) -> ast.Expr:
    """環境を考慮して式を最適化（代入展開＋定数畳み込み）する。"""
    substituted = substitute_identifiers(expression, environment)
    return constant_fold(substituted)