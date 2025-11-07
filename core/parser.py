"""Recursive-descent parser for the MathLang DSL as defined in the specification."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Sequence

from . import ast_nodes as ast


class ParserError(ValueError):
    """Raised when invalid syntax is encountered."""


class LexerError(ValueError):
    """Raised when the source contains invalid characters."""


class TokenType(Enum):
    IDENT = auto()
    NUMBER = auto()
    SHOW = auto()
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    CARET = auto()
    EQUAL = auto()
    LPAREN = auto()
    RPAREN = auto()
    NEWLINE = auto()
    EOF = auto()


@dataclass(frozen=True)
class Token:
    type: TokenType
    lexeme: str
    line: int
    column: int


class Lexer:
    """Turns the MathLang source code into a token stream."""

    def __init__(self, source: str) -> None:
        self.source = source
        self.length = len(source)
        self.index = 0
        self.line = 1
        self.column = 1

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []
        while not self._is_at_end():
            ch = self._peek()

            if ch in " \t":
                self._advance()
                continue

            if ch == "#":
                self._skip_comment()
                continue

            if ch in "\r\n":
                tokens.append(self._make_token(TokenType.NEWLINE, "\n"))
                self._consume_newline()
                continue

            if ch.isdigit():
                tokens.append(self._number())
                continue

            if ch.isalpha() or ch == "_":
                tokens.append(self._identifier())
                continue

            single_char_tokens = {
                "+": TokenType.PLUS,
                "-": TokenType.MINUS,
                "*": TokenType.STAR,
                "/": TokenType.SLASH,
                "^": TokenType.CARET,
                "=": TokenType.EQUAL,
                "(": TokenType.LPAREN,
                ")": TokenType.RPAREN,
            }
            if ch in single_char_tokens:
                tokens.append(self._make_token(single_char_tokens[ch], ch))
                self._advance()
                continue

            raise LexerError(f"Unexpected character '{ch}' at line {self.line}, column {self.column}")

        tokens.append(self._make_token(TokenType.EOF, ""))
        return tokens

    def _advance(self) -> str:
        ch = self.source[self.index]
        self.index += 1
        if ch == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def _peek(self) -> str:
        return self.source[self.index]

    def _peek_next(self) -> str:
        if self.index + 1 >= self.length:
            return "\0"
        return self.source[self.index + 1]

    def _is_at_end(self) -> bool:
        return self.index >= self.length

    def _make_token(self, token_type: TokenType, lexeme: str) -> Token:
        return Token(token_type, lexeme, self.line, self.column)

    def _consume_newline(self) -> None:
        if self._peek() == "\r" and self._peek_next() == "\n":
            self._advance()
            self._advance()
            return
        self._advance()

    def _skip_comment(self) -> None:
        while not self._is_at_end() and self._peek() not in "\r\n":
            self._advance()

    def _number(self) -> Token:
        start_line, start_column = self.line, self.column
        lexeme_chars = []
        has_decimal_point = False

        while not self._is_at_end():
            ch = self._peek()
            if ch == ".":
                if has_decimal_point:
                    break
                has_decimal_point = True
            elif not ch.isdigit():
                break
            lexeme_chars.append(self._advance())

        lexeme = "".join(lexeme_chars)
        return Token(TokenType.NUMBER, lexeme, start_line, start_column)

    def _identifier(self) -> Token:
        start_line, start_column = self.line, self.column
        lexeme_chars = []

        while not self._is_at_end() and (self._peek().isalnum() or self._peek() == "_"):
            lexeme_chars.append(self._advance())

        lexeme = "".join(lexeme_chars)
        token_type = TokenType.SHOW if lexeme == "show" else TokenType.IDENT
        return Token(token_type, lexeme, start_line, start_column)


class Parser:
    """Turns MathLang source text into an AST program object."""

    def __init__(self, source: str):
        try:
            self.tokens: Sequence[Token] = Lexer(source).tokenize()
        except LexerError as exc:
            raise ParserError(str(exc)) from exc
        self.position = 0

    def parse(self) -> ast.Program:
        statements: List[ast.Statement] = []

        self._consume_newlines()
        while not self._is_at_end():
            statements.append(self._parse_statement())
            self._consume_newlines()

        return ast.Program(statements=statements)

    def _parse_statement(self) -> ast.Statement:
        if self._match(TokenType.SHOW):
            identifier = self._consume(TokenType.IDENT, "'show' の後には識別子が必要です")
            return ast.Show(identifier=identifier.lexeme)

        if self._check(TokenType.IDENT) and self._check_next(TokenType.EQUAL):
            target = self._consume(TokenType.IDENT, "代入の先頭には識別子が必要です")
            self._consume(TokenType.EQUAL, "代入には '=' が必要です")
            expression = self._parse_expression()
            return ast.Assignment(target=target.lexeme, expression=expression)

        expression = self._parse_expression()
        return ast.ExpressionStatement(expression=expression)

    def _parse_expression(self) -> ast.Expression:
        return self._parse_additive()

    def _parse_additive(self) -> ast.Expression:
        expr = self._parse_multiplicative()
        while self._match(TokenType.PLUS, TokenType.MINUS):
            operator = self._previous().lexeme
            right = self._parse_multiplicative()
            expr = ast.BinaryOp(left=expr, operator=operator, right=right)
        return expr

    def _parse_multiplicative(self) -> ast.Expression:
        expr = self._parse_exponent()
        while self._match(TokenType.STAR, TokenType.SLASH):
            operator = self._previous().lexeme
            right = self._parse_exponent()
            expr = ast.BinaryOp(left=expr, operator=operator, right=right)
        return expr

    def _parse_exponent(self) -> ast.Expression:
        expr = self._parse_unary()
        if self._match(TokenType.CARET):
            operator = self._previous().lexeme
            right = self._parse_exponent()
            expr = ast.BinaryOp(left=expr, operator=operator, right=right)
        return expr

    def _parse_unary(self) -> ast.Expression:
        if self._match(TokenType.PLUS):
            return self._parse_unary()
        if self._match(TokenType.MINUS):
            right = self._parse_unary()
            zero = ast.NumberLiteral(value=0.0)
            return ast.BinaryOp(left=zero, operator="-", right=right)
        return self._parse_primary()

    def _parse_primary(self) -> ast.Expression:
        if self._match(TokenType.NUMBER):
            value = float(self._previous().lexeme)
            return ast.NumberLiteral(value=value)
        if self._match(TokenType.IDENT):
            return ast.Identifier(name=self._previous().lexeme)
        if self._match(TokenType.LPAREN):
            expr = self._parse_expression()
            self._consume(TokenType.RPAREN, "括弧を閉じる ')' が必要です")
            return expr
        token = self._peek()
        raise ParserError(
            f"Unexpected token '{token.lexeme}' at line {token.line}, column {token.column}"
        )

    def _consume_newlines(self) -> None:
        while self._match(TokenType.NEWLINE):
            continue

    def _match(self, *types: TokenType) -> bool:
        for token_type in types:
            if self._check(token_type):
                self._advance()
                return True
        return False

    def _consume(self, token_type: TokenType, message: str) -> Token:
        if self._check(token_type):
            return self._advance()
        token = self._peek()
        raise ParserError(f"{message} (line {token.line}, column {token.column})")

    def _check(self, token_type: TokenType) -> bool:
        if self._is_at_end():
            return False
        return self._peek().type == token_type

    def _check_next(self, token_type: TokenType) -> bool:
        if self.position + 1 >= len(self.tokens):
            return False
        return self.tokens[self.position + 1].type == token_type

    def _advance(self) -> Token:
        if not self._is_at_end():
            self.position += 1
        return self._previous()

    def _previous(self) -> Token:
        return self.tokens[self.position - 1]

    def _peek(self) -> Token:
        return self.tokens[self.position]

    def _is_at_end(self) -> bool:
        return self._peek().type == TokenType.EOF
