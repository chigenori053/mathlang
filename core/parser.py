"""Recursive-descent parser for the MathLang DSL as defined in the specification."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Sequence

from . import ast_nodes as ast
from .i18n import LanguagePack, get_language_pack


class ParserError(ValueError):
    """Raised when invalid syntax is encountered."""


class LexerError(ValueError):
    """Raised when the source contains invalid characters."""


class TokenType(Enum):
    IDENT = auto()
    NUMBER = auto()
    STRING = auto()
    SHOW = auto()
    PROBLEM = auto()
    STEP = auto()
    END = auto()
    PREPARE = auto()
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    CARET = auto()
    EQUAL = auto()
    COLON = auto()
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

    def __init__(self, source: str, language: LanguagePack) -> None:
        self.source = source
        self.length = len(source)
        self.index = 0
        self.line = 1
        self.column = 1
        self.language = language
        self.keywords = {
            "problem": TokenType.PROBLEM,
            "prepare": TokenType.PREPARE,
            "step": TokenType.STEP,
            "end": TokenType.END,
            "show": TokenType.SHOW,
        }

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []
        while not self._is_at_end():
            ch = self._peek()

            if ch in " 	":
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

            if ch == '"':
                tokens.append(self._string())
                continue

            single_char_tokens = {
                "+": TokenType.PLUS,
                "-": TokenType.MINUS,
                "*": TokenType.STAR,
                "/": TokenType.SLASH,
                "^": TokenType.CARET,
                "=": TokenType.EQUAL,
                ":": TokenType.COLON,
                "(": TokenType.LPAREN,
                ")": TokenType.RPAREN,
            }
            if ch in single_char_tokens:
                tokens.append(self._make_token(single_char_tokens[ch], ch))
                self._advance()
                continue

            raise LexerError(
                self.language.text(
                    "lexer.unexpected_character", char=ch, line=self.line, column=self.column
                )
            )

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
        if self._is_at_end(): return "\0"
        return self.source[self.index]

    def _is_at_end(self) -> bool:
        return self.index >= self.length

    def _make_token(self, token_type: TokenType, lexeme: str) -> Token:
        return Token(token_type, lexeme, self.line, self.column)

    def _consume_newline(self) -> None:
        while self._peek() in "\r\n":
            self._advance()

    def _skip_comment(self) -> None:
        while self._peek() not in "\r\n" and not self._is_at_end():
            self._advance()

    def _number(self) -> Token:
        start_pos = self.index
        while self._peek().isdigit():
            self._advance()
        return self._make_token(TokenType.NUMBER, self.source[start_pos:self.index])

    def _identifier(self) -> Token:
        start_pos = self.index
        while self._peek().isalnum() or self._peek() == "_":
            self._advance()
        lexeme = self.source[start_pos:self.index]
        token_type = self.keywords.get(lexeme, TokenType.IDENT)
        return self._make_token(token_type, lexeme)

    def _string(self) -> Token:
        start_pos = self.index
        self._advance() # Consume the opening quote

        while self._peek() != '"' and not self._is_at_end():
            self._advance()

        if self._is_at_end():
            raise LexerError(self.language.text("lexer.unterminated_string", line=self.line, column=self.column))

        self._advance() # Consume the closing quote
        lexeme = self.source[start_pos:self.index]
        return self._make_token(TokenType.STRING, lexeme)


class Parser:
    """Turns MathLang source text into an AST program object."""

    def __init__(self, source: str, language: LanguagePack | None = None):
        self._language = language or get_language_pack("en")
        try:
            self.tokens: Sequence[Token] = Lexer(source, self._language).tokenize()
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
        if self._match(TokenType.PROBLEM):
            return self._parse_problem_block()
        if self._check(TokenType.IDENT) and self._check_next(TokenType.EQUAL):
            return self._parse_assignment()
        if self._match(TokenType.SHOW):
            return self._parse_show()
        
        token = self._peek()
        raise ParserError(f"Unexpected token '{token.lexeme}' at line {token.line}, column {token.column}")

    def _parse_assignment(self) -> ast.Assignment:
        target = self._consume(TokenType.IDENT, "Expected identifier for assignment.")
        self._consume(TokenType.EQUAL, "Expected '=' after identifier.")
        expression = self._parse_expression()
        return ast.Assignment(target=target.lexeme, expression=expression)

    def _parse_show(self) -> ast.Show:
        identifier = self._consume(TokenType.IDENT, "Expected identifier after 'show'.")
        return ast.Show(identifier=identifier.lexeme)

    def _parse_problem_block(self) -> ast.Problem:
        name_token = self._advance()
        if name_token.type == TokenType.IDENT:
            name = name_token.lexeme
        elif name_token.type == TokenType.STRING:
            # Remove quotes from the string literal
            name = name_token.lexeme[1:-1]
        else:
            raise ParserError(f"Expected problem name (identifier or string), but got '{name_token.lexeme}' at line {name_token.line}, column {name_token.column}")
        self._consume_newlines()

        prepare_node: ast.PrepareNode | None = None
        if self._match(TokenType.PREPARE):
            self._consume(TokenType.COLON, "Expected ':' after 'prepare'.")
            self._consume_newlines()
            assignments: List[ast.Assignment] = []
            while not self._check(TokenType.STEP) and not self._check(TokenType.END):
                assignments.append(self._parse_assignment())
                self._consume_newlines()
            prepare_node = ast.PrepareNode(assignments=assignments)

        steps: List[ast.Step] = []
        while True:
            if self._check(TokenType.END):
                break
            if self._is_at_end():
                raise ParserError("Expected 'end' to close problem block.")
            # Allow expressions as steps without 'step' keyword
            # If 'step' keyword is present, consume it and the colon
            if self._match(TokenType.STEP):
                self._consume(TokenType.COLON, "Expected ':' after 'step'.")
            self._consume_newlines()
            before = self._parse_expression()
            self._consume(TokenType.EQUAL, "Expected '=' in step definition.")
            after = self._parse_expression()
            steps.append(ast.Step(before=before, after=after))
            self._consume_newlines()

        self._consume(TokenType.END, "Expected 'end' to close problem block.")
        return ast.Problem(name=name, prepare=prepare_node, steps=steps)

    def _parse_expression(self) -> ast.Expr:
        return self._parse_additive()

    def _parse_additive(self) -> ast.Expr:
        expr = self._parse_multiplicative()
        while self._match(TokenType.PLUS, TokenType.MINUS):
            op = self._previous()
            right = self._parse_multiplicative()
            if op.type == TokenType.MINUS:
                right = ast.Neg(expr=right)
            
            if isinstance(expr, ast.Add):
                expr.terms.append(right)
            else:
                expr = ast.Add(terms=[expr, right])
        return expr

    def _parse_multiplicative(self) -> ast.Expr:
        expr = self._parse_exponent()
        while self._match(TokenType.STAR, TokenType.SLASH):
            op = self._previous()
            right = self._parse_exponent()
            if op.type == TokenType.STAR:
                if isinstance(expr, ast.Mul):
                    expr.factors.append(right)
                else:
                    expr = ast.Mul(factors=[expr, right])
            else:
                expr = ast.Div(left=expr, right=right)
        return expr

    def _parse_exponent(self) -> ast.Expr:
        expr = self._parse_unary()
        if self._match(TokenType.CARET):
            right = self._parse_exponent()
            expr = ast.Pow(base=expr, exp=right)
        return expr

    def _parse_unary(self) -> ast.Expr:
        if self._match(TokenType.MINUS):
            return ast.Neg(expr=self._parse_unary())
        return self._parse_primary()

    def _parse_primary(self) -> ast.Expr:
        if self._match(TokenType.NUMBER):
            return ast.Int(value=int(self._previous().lexeme))
        if self._match(TokenType.IDENT):
            return ast.Sym(name=self._previous().lexeme)
        if self._match(TokenType.LPAREN):
            expr = self._parse_expression()
            self._consume(TokenType.RPAREN, "Expected ')' after expression.")
            return expr
        
        token = self._peek()
        raise ParserError(f"Unexpected token '{token.lexeme}' at line {token.line}, column {token.column}")

    def _consume(self, token_type: TokenType, message: str) -> Token:
        if self._check(token_type):
            return self._advance()
        raise ParserError(message)

    def _match(self, *types: TokenType) -> bool:
        for t in types:
            if self._check(t):
                self._advance()
                return True
        return False

    def _check(self, token_type: TokenType) -> bool:
        if self._is_at_end(): return False
        return self._peek().type == token_type

    def _check_next(self, token_type: TokenType) -> bool:
        if self.position + 1 >= len(self.tokens):
            return False
        return self.tokens[self.position + 1].type == token_type

    def _consume_newlines(self) -> None:
        while self._match(TokenType.NEWLINE):
            pass

    def _is_at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _peek(self) -> Token:
        return self.tokens[self.position]

    def _previous(self) -> Token:
        return self.tokens[self.position - 1]

    def _advance(self) -> Token:
        if not self._is_at_end():
            self.position += 1
        return self._previous()
