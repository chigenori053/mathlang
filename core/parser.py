"""Simple recursive-descent parser for the MathLang DSL."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from . import ast_nodes as ast


class ParserError(ValueError):
    """Raised when the parser encounters invalid syntax."""


@dataclass
class Token:
    kind: str
    value: str


class Parser:
    """Converts MathLang source text into an AST Program."""

    def __init__(self, source: str):
        self.tokens = self._tokenize(source)
        self.position = 0

    # Public API -----------------------------------------------------------------

    def parse(self) -> ast.Program:
        statements: List[ast.Statement] = []
        while not self._is_at_end():
            if self._match("NEWLINE"):
                continue
            statements.append(self._parse_statement())
            self._consume_newlines()
        return ast.Program(statements=statements)

    # Statement parsing ----------------------------------------------------------

    def _parse_statement(self) -> ast.Statement:
        if self._match("SHOW"):
            identifier = self._consume("IDENT", "Expected identifier after 'show'")
            return ast.Show(identifier=identifier.value)

        if self._check("IDENT") and self._check_next("EQUAL"):
            target = self._consume("IDENT", "Expected identifier to start assignment")
            self._consume("EQUAL", "Expected '=' in assignment")
            expression = self._parse_expression()
            return ast.Assignment(target=target.value, expression=expression)

        expression = self._parse_expression()
        return ast.ExpressionStatement(expression=expression)

    # Expression parsing ---------------------------------------------------------

    def _parse_expression(self) -> ast.Expression:
        return self._parse_additive()

    def _parse_additive(self) -> ast.Expression:
        expr = self._parse_multiplicative()
        while self._match("PLUS", "MINUS"):
            operator = self._previous().value
            right = self._parse_multiplicative()
            expr = ast.BinaryOp(left=expr, operator=operator, right=right)
        return expr

    def _parse_multiplicative(self) -> ast.Expression:
        expr = self._parse_exponent()
        while self._match("STAR", "SLASH"):
            operator = self._previous().value
            right = self._parse_exponent()
            expr = ast.BinaryOp(left=expr, operator=operator, right=right)
        return expr

    def _parse_exponent(self) -> ast.Expression:
        expr = self._parse_unary()
        while self._match("CARET"):
            operator = self._previous().value
            right = self._parse_exponent()
            expr = ast.BinaryOp(left=expr, operator=operator, right=right)
        return expr

    def _parse_unary(self) -> ast.Expression:
        if self._match("PLUS"):
            return self._parse_unary()
        if self._match("MINUS"):
            right = self._parse_unary()
            zero = ast.NumberLiteral(value=0.0)
            return ast.BinaryOp(left=zero, operator="-", right=right)
        return self._parse_primary()

    def _parse_primary(self) -> ast.Expression:
        if self._match("NUMBER"):
            value = float(self._previous().value)
            return ast.NumberLiteral(value=value)
        if self._match("IDENT"):
            return ast.Identifier(name=self._previous().value)
        if self._match("LPAREN"):
            expr = self._parse_expression()
            self._consume("RPAREN", "Expected ')' after expression")
            return expr
        raise ParserError(f"Unexpected token: {self._peek().value!r}")

    # Token helpers --------------------------------------------------------------

    def _consume_newlines(self) -> None:
        while self._match("NEWLINE"):
            continue

    def _match(self, *kinds: str) -> bool:
        for kind in kinds:
            if self._check(kind):
                self._advance()
                return True
        return False

    def _consume(self, kind: str, message: str) -> Token:
        if self._check(kind):
            return self._advance()
        raise ParserError(message)

    def _check(self, kind: str) -> bool:
        if self._is_at_end():
            return False
        return self._peek().kind == kind

    def _check_next(self, kind: str) -> bool:
        if self.position + 1 >= len(self.tokens):
            return False
        return self.tokens[self.position + 1].kind == kind

    def _advance(self) -> Token:
        if not self._is_at_end():
            self.position += 1
        return self._previous()

    def _previous(self) -> Token:
        return self.tokens[self.position - 1]

    def _peek(self) -> Token:
        return self.tokens[self.position]

    def _is_at_end(self) -> bool:
        return self._peek().kind == "EOF"

    # Tokenization ---------------------------------------------------------------

    def _tokenize(self, source: str) -> List[Token]:
        tokens: List[Token] = []
        i = 0
        length = len(source)

        while i < length:
            ch = source[i]

            if ch in " \t":
                i += 1
                continue

            if ch == "#":
                while i < length and source[i] != "\n":
                    i += 1
                continue

            if ch in "\r\n":
                tokens.append(Token(kind="NEWLINE", value="\\n"))
                i += 1
                if ch == "\r" and i < length and source[i] == "\n":
                    i += 1
                continue

            if ch.isdigit():
                start = i
                while i < length and (source[i].isdigit() or source[i] == "."):
                    i += 1
                tokens.append(Token(kind="NUMBER", value=source[start:i]))
                continue

            if ch.isalpha() or ch == "_":
                start = i
                while i < length and (source[i].isalnum() or source[i] == "_"):
                    i += 1
                value = source[start:i]
                kind = "SHOW" if value == "show" else "IDENT"
                tokens.append(Token(kind=kind, value=value))
                continue

            single_char_tokens = {
                "+": "PLUS",
                "-": "MINUS",
                "*": "STAR",
                "/": "SLASH",
                "^": "CARET",
                "=": "EQUAL",
                "(": "LPAREN",
                ")": "RPAREN",
            }
            if ch in single_char_tokens:
                tokens.append(Token(kind=single_char_tokens[ch], value=ch))
                i += 1
                continue

            raise ParserError(f"Unexpected character: {ch}")

        tokens.append(Token(kind="EOF", value=""))
        return tokens
