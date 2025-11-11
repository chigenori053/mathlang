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
    STEP_LABEL = auto()
    END = auto()
    EXPLAIN = auto()
    DONE = auto()
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    CARET = auto()
    EQUAL = auto()
    COLON = auto()
    LBRACKET = auto()
    RBRACKET = auto()
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

            if ch in "\"'":
                tokens.append(self._string(ch))
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
                ":": TokenType.COLON,
                "[": TokenType.LBRACKET,
                "]": TokenType.RBRACKET,
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

    def _string(self, quote: str) -> Token:
        start_line, start_column = self.line, self.column
        self._advance()  # consume opening quote
        lexeme_chars = []

        while not self._is_at_end():
            ch = self._peek()
            if ch == quote:
                self._advance()
                lexeme = "".join(lexeme_chars)
                return Token(TokenType.STRING, lexeme, start_line, start_column)
            if ch == "\n":
                break
            lexeme_chars.append(self._advance())

        raise LexerError(
            self.language.text(
                "lexer.unterminated_string",
                line=start_line,
                column=start_column,
            )
        )

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
        keyword_tokens = {
            "show": TokenType.SHOW,
            "problem": TokenType.PROBLEM,
            "step": TokenType.STEP,
            "end": TokenType.END,
            "explain": TokenType.EXPLAIN,
            "done": TokenType.DONE,
        }
        token_type = keyword_tokens.get(lexeme, TokenType.IDENT)
        if token_type is TokenType.IDENT and lexeme.startswith("step"):
            suffix = lexeme[4:]
            if suffix.isdigit():
                token_type = TokenType.STEP_LABEL
        return Token(token_type, lexeme, start_line, start_column)


class Parser:
    """Turns MathLang source text into an AST program object."""

    def __init__(self, source: str, language: LanguagePack | None = None):
        self._language = language or get_language_pack()
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
            return self._parse_problem()

        if self._match(TokenType.STEP):
            return self._parse_step()

        if self._check(TokenType.STEP_LABEL) and self._check_next(TokenType.COLON):
            label_token = self._advance()
            return self._parse_step(prefixed_label=label_token.lexeme)

        if self._match(TokenType.END):
            return self._parse_end()

        if self._match(TokenType.EXPLAIN):
            return self._parse_explain()

        if self._match(TokenType.SHOW):
            identifier = self._consume(
                TokenType.IDENT,
                self._language.text("parser.show_identifier_required"),
            )
            return ast.Show(identifier=identifier.lexeme)

        if self._check(TokenType.IDENT) and self._check_next(TokenType.EQUAL):
            target = self._consume(
                TokenType.IDENT,
                self._language.text("parser.assignment_identifier_required"),
            )
            self._consume(TokenType.EQUAL, self._language.text("parser.assignment_equal_missing"))
            expression = self._parse_expression()
            return ast.Assignment(target=target.lexeme, expression=expression)

        expression = self._parse_expression()
        return ast.ExpressionStatement(expression=expression)

    def _parse_problem(self) -> ast.Statement:
        self._consume(TokenType.COLON, self._language.text("parser.colon_missing", keyword="problem"))
        expression = self._parse_expression()
        return ast.Problem(expression=expression)

    def _parse_step(self, prefixed_label: str | None = None) -> ast.Statement:
        label = prefixed_label or self._parse_step_bracket_label()
        self._consume(TokenType.COLON, self._language.text("parser.colon_missing", keyword="step"))
        expression = self._parse_expression()
        return ast.Step(expression=expression, label=label)

    def _parse_step_bracket_label(self) -> str | None:
        if not self._match(TokenType.LBRACKET):
            return None
        if not (self._check(TokenType.IDENT) or self._check(TokenType.NUMBER)):
            raise ParserError(self._language.text("parser.step_id_required"))
        label_token = self._advance()
        self._consume(TokenType.RBRACKET, self._language.text("parser.step_bracket_close_missing"))
        return f"step[{label_token.lexeme}]"

    def _parse_end(self) -> ast.Statement:
        self._consume(TokenType.COLON, self._language.text("parser.colon_missing", keyword="end"))
        if self._match(TokenType.DONE):
            return ast.End(expression=None, done=True)
        expression = self._parse_expression()
        return ast.End(expression=expression, done=False)

    def _parse_explain(self) -> ast.Statement:
        self._consume(TokenType.COLON, self._language.text("parser.colon_missing", keyword="explain"))
        string_token = self._consume(TokenType.STRING, self._language.text("parser.explain_string_required"))
        return ast.Explain(message=string_token.lexeme)

    def _parse_expression(self) -> ast.Expr:
        return self._parse_additive()

    def _parse_additive(self) -> ast.Expr:
        terms = [self._parse_multiplicative()]
        while self._match(TokenType.PLUS, TokenType.MINUS):
            operator = self._previous().lexeme
            right = self._parse_multiplicative()
            if operator == "-":
                terms.append(ast.Neg(expr=right))
            else:
                terms.append(right)
        
        if len(terms) == 1:
            return terms[0]
        return ast.Add(terms=terms)

    def _parse_multiplicative(self) -> ast.Expr:
        factors = [self._parse_exponent()]
        while self._match(TokenType.STAR, TokenType.SLASH):
            operator = self._previous().lexeme
            right = self._parse_exponent()
            if operator == "/":
                # Represent division as multiplication by the reciprocal
                factors.append(ast.Pow(base=right, exp=ast.Int(value=-1)))
            else:
                factors.append(right)

        if len(factors) == 1:
            return factors[0]
        return ast.Mul(factors=factors)

    def _parse_exponent(self) -> ast.Expr:
        expr = self._parse_unary()
        if self._match(TokenType.CARET):
            right = self._parse_exponent()
            expr = ast.Pow(base=expr, exp=right)
        return expr

    def _parse_unary(self) -> ast.Expr:
        if self._match(TokenType.PLUS):
            return self._parse_unary()
        if self._match(TokenType.MINUS):
            right = self._parse_unary()
            return ast.Neg(expr=right)
        return self._parse_primary()

    def _parse_primary(self) -> ast.Expr:
        if self._match(TokenType.NUMBER):
            value_str = self._previous().lexeme
            if "." in value_str:
                # Not supporting floats in the new AST directly, parsing as int for now.
                # This should be handled as Rat or with a dedicated Float node if needed.
                value = int(float(value_str))
            else:
                value = int(value_str)
            return ast.Int(value=value)
        if self._match(TokenType.IDENT):
            return ast.Sym(name=self._previous().lexeme)
        if self._match(TokenType.LPAREN):
            expr = self._parse_expression()
            self._consume(TokenType.RPAREN, self._language.text("parser.closing_paren_missing"))
            return expr
        token = self._peek()
        raise ParserError(
            self._language.text("parser.unexpected_token", lexeme=token.lexeme, line=token.line, column=token.column)
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
