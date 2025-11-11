"""AST node definitions for the MathLang DSL, based on Core Engine Architecture v1."""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Union

# Core Expression Types based on MathLang Core Engine Architecture v1

@dataclass
class Int:
    value: int

@dataclass
class Rat:
    p: int
    q: int

@dataclass
class Sym:
    name: str

@dataclass
class Add:
    terms: List['Expr']

@dataclass
class Mul:
    factors: List['Expr']

@dataclass
class Pow:
    base: 'Expr'
    exp: 'Expr'

@dataclass
class Neg:
    expr: 'Expr'

@dataclass
class Call:
    name: str
    args: List['Expr']

Expr = Union[Int, Rat, Sym, Add, Mul, Pow, Neg, Call]

# --- High-level DSL Statements ---
# These are kept for now to represent the overall structure of a .mlang file,
# but their `expression` fields will now use the new Expr model.

@dataclass
class Assignment:
    target: str
    expression: Expr

@dataclass
class Show:
    identifier: str

@dataclass
class ExpressionStatement:
    expression: Expr

@dataclass
class Problem:
    expression: Expr

@dataclass
class Step:
    expression: Expr
    label: str | None = None

@dataclass
class End:
    expression: Expr | None
    done: bool = False

@dataclass
class Explain:
    message: str

Statement = Union[Assignment, Show, ExpressionStatement, Problem, Step, End, Explain]

@dataclass
class Program:
    statements: List[Statement]