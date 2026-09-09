"""Tests for the pure execution logic behind the notebook-style web UI."""

from __future__ import annotations

from webapp.engine import run_cell

CONTRADICTORY_SOURCE = """
meta:
    id: web_ui_contradiction
    topic: counterfactual
config:
    causal: true

prepare:
    - base_sum = 3 + 5
    - scale_factor = 4

problem: base_sum * scale_factor

step:
    before: base_sum * scale_factor
    after: 8 * scale_factor

step:
    before: 8 * scale_factor
    after: 32 * scale_factor

end: 32
"""


def test_run_cell_valid_arithmetic() -> None:
    result = run_cell("problem: (3 + 5) * 4\nstep: 8 * 4\nend: 32\n")

    assert result.error is None
    assert result.records
    assert result.formatted_lines
    assert any("32" in line for line in result.formatted_lines)


def test_run_cell_polynomial_mode() -> None:
    result = run_cell(
        "problem: (x - y)^2\nstep: (x - y) (x - y)\nstep: x^2 - 2xy + y^2\nend: done\n",
        mode="polynomial",
    )

    assert result.error is None
    assert result.records


def test_run_cell_syntax_error_is_captured_not_raised() -> None:
    result = run_cell("this is not valid mathlang\n")

    assert result.error is not None
    assert result.records == []


def test_run_cell_rejects_unknown_mode() -> None:
    try:
        run_cell("problem: 1 + 1\nend: 2\n", mode="causal")
    except ValueError as exc:
        assert "Unsupported mode" in str(exc)
    else:
        raise AssertionError("Expected ValueError for an unsupported mode")


def test_run_cell_causal_analysis_flags_contradiction() -> None:
    result = run_cell(CONTRADICTORY_SOURCE)

    assert result.causal is not None
    assert result.causal["errors"]
    assert result.causal["fix_candidates"]
