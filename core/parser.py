"""Line-oriented parser for the MathLang Core DSL."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from . import ast_nodes as ast
from .errors import SyntaxError


@dataclass
class ParsedLine:
    number: int
    content: str


class Parser:
    """Parse MathLang DSL source text into a ProgramNode."""

    def __init__(self, source: str) -> None:
        self._lines = [
            ParsedLine(idx, line.rstrip("\n"))
            for idx, line in enumerate(source.splitlines(), start=1)
        ]

    def parse(self) -> ast.ProgramNode:
        nodes: list[ast.Node] = []
        for parsed in self._normalized_lines():
            content = parsed.content
            if content.startswith("problem:"):
                nodes.append(self._parse_problem(content, parsed.number))
            elif content.startswith("step"):
                nodes.append(self._parse_step(content, parsed.number))
            elif content.startswith("end:"):
                nodes.append(self._parse_end(content, parsed.number))
            elif content.startswith("explain:"):
                nodes.append(self._parse_explain(content, parsed.number))
            else:
                raise SyntaxError(f"Unsupported statement on line {parsed.number}: {content}")

        program = ast.ProgramNode(line=None, body=nodes)
        if not any(isinstance(node, ast.ProblemNode) for node in nodes):
            raise SyntaxError("Program must contain at least one problem statement.")
        if not any(isinstance(node, ast.EndNode) for node in nodes):
            raise SyntaxError("Program must contain at least one end statement.")
        return program

    def _normalized_lines(self) -> Iterable[ParsedLine]:
        for parsed in self._lines:
            stripped = parsed.content.strip()
            if not stripped or stripped.startswith("#"):
                continue
            yield ParsedLine(parsed.number, stripped)

    def _parse_problem(self, content: str, number: int) -> ast.ProblemNode:
        expr = content[len("problem:") :].strip()
        if not expr:
            raise SyntaxError(f"Problem expression required on line {number}.")
        return ast.ProblemNode(expr=expr, line=number)

    def _parse_step(self, content: str, number: int) -> ast.StepNode:
        prefix, sep, rest = content.partition(":")
        if not sep:
            raise SyntaxError(f"Missing ':' for step on line {number}.")
        tail = prefix[len("step") :].strip()
        step_id = tail if tail else None
        expr = rest.strip()
        if not expr:
            raise SyntaxError(f"Step expression required on line {number}.")
        return ast.StepNode(step_id=step_id, expr=expr, line=number)

    def _parse_end(self, content: str, number: int) -> ast.EndNode:
        expr_text = content[len("end:") :].strip()
        if not expr_text:
            raise SyntaxError(f"End expression required on line {number}.")
        if expr_text.lower() == "done":
            return ast.EndNode(expr=None, is_done=True, line=number)
        return ast.EndNode(expr=expr_text, is_done=False, line=number)

    def _parse_explain(self, content: str, number: int) -> ast.ExplainNode:
        raw_text = content[len("explain:") :].strip()
        if not raw_text:
            raise SyntaxError(f"Explain statement requires a string literal on line {number}.")
        text = self._strip_string_literal(raw_text, number)
        return ast.ExplainNode(text=text, line=number)

    def _strip_string_literal(self, literal: str, number: int) -> str:
        if len(literal) < 2 or literal[0] not in {'"', "'"} or literal[-1] != literal[0]:
            raise SyntaxError(f"Explain statement requires a quoted string on line {number}.")
        return literal[1:-1]
