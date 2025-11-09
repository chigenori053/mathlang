"""AST node definitions for the MathLang DSL."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Union


# Expressions -----------------------------------------------------------------


@dataclass
class NumberLiteral:
    value: float


@dataclass
class Identifier:
    name: str


@dataclass
class BinaryOp:
    left: "Expression"
    operator: str
    right: "Expression"


Expression = Union["NumberLiteral", "Identifier", "BinaryOp"]


# Statements ------------------------------------------------------------------


@dataclass
class Assignment:
    target: str
    expression: Expression


@dataclass
class Show:
    identifier: str


@dataclass
class ExpressionStatement:
    expression: Expression


@dataclass
class Problem:
    expression: Expression


@dataclass
class Step:
    expression: Expression
    label: str | None = None


@dataclass
class End:
    expression: Expression | None
    done: bool = False


@dataclass
class Explain:
    message: str


Statement = Union[Assignment, Show, ExpressionStatement, Problem, Step, End, Explain]


@dataclass
class Program:
    statements: List[Statement]
