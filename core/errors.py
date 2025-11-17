"""Error classes for the MathLang Core implementation."""

from __future__ import annotations


class MathLangError(Exception):
    """Base class for all MathLang-specific errors."""


class SyntaxError(MathLangError):
    """Raised when the DSL contains invalid syntax."""


class MissingProblemError(MathLangError):
    """Raised when a problem declaration is missing before other statements."""


class InvalidStepError(MathLangError):
    """Raised when a transformation step is not equivalent to the previous expression."""


class InconsistentEndError(MathLangError):
    """Raised when the final expression does not match the expected end expression."""


class InvalidExprError(MathLangError):
    """Raised when symbolic or polynomial engines cannot interpret an expression."""


class EvaluationError(MathLangError):
    """Raised during expression evaluation."""


class ExtraContentError(MathLangError):
    """Raised when additional statements appear after an end declaration."""
