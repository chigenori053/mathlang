"""Tests for the pure diagnostic/hover logic behind the MathLang LSP server.

These exercise `build_diagnostics`/`hover_text_for` directly; no websocket or
pygls server needs to be running.
"""

from __future__ import annotations

from tools.lsp.server import KEYWORD_DOCS, build_diagnostics, hover_text_for


def test_build_diagnostics_valid_source_is_empty() -> None:
    diagnostics = build_diagnostics("problem: 1 + 1\nstep: 2\nend: 2\n")

    assert diagnostics == []


def test_build_diagnostics_reports_syntax_error_with_line() -> None:
    source = "problem: 1 + 1\nend: 2\nnot a valid statement\n"

    diagnostics = build_diagnostics(source)

    assert len(diagnostics) == 1
    diagnostic = diagnostics[0]
    assert "line 3" in diagnostic.message
    assert diagnostic.range.start.line == 2


def test_build_diagnostics_missing_end_reports_line_zero() -> None:
    diagnostics = build_diagnostics("problem: 1 + 1\n")

    assert len(diagnostics) == 1
    assert diagnostics[0].range.start.line == 0


def test_hover_text_for_keyword_returns_doc() -> None:
    source = "problem: 1 + 1\nend: 2\n"

    text = hover_text_for(source, 0, 2)

    assert text == KEYWORD_DOCS["problem"]


def test_hover_text_for_non_keyword_returns_none() -> None:
    source = "problem: 1 + 1\nend: 2\n"

    assert hover_text_for(source, 0, 12) is None


def test_hover_text_for_out_of_range_line_returns_none() -> None:
    assert hover_text_for("problem: 1 + 1\n", 5, 0) is None
