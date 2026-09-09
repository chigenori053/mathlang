"""Streamlit rendering helpers for `webapp.engine.CellResult`.

Kept deliberately plain (Jupyter's Out[] cells are just monospace text, no
icons or boxes per line) — one `st.code` block for the whole trace.
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from core.log_formatter import format_record_message
from webapp.engine import CellResult


def render_cell_result(result: CellResult) -> None:
    """Render one cell's execution result: steps, error, causal analysis."""

    if not result.records and not result.error:
        return

    lines: list[str] = []
    for record in result.records:
        lines.extend(format_record_message(record))
    if lines:
        st.code("\n".join(lines), language=None)

    if result.error:
        st.error(result.error)

    if result.causal:
        _render_causal(result.causal)


def _render_causal(causal: dict[str, Any]) -> None:
    error_ids: list[str] = causal.get("errors", [])
    if not error_ids:
        return
    explanations = causal.get("explanations", [])
    rule_details: dict[str, Any] = causal.get("rule_details", {})
    fix_candidates: dict[str, list[str]] = causal.get("fix_candidates", {})

    with st.expander(f"Causal analysis ({len(error_ids)})"):
        lines: list[str] = []
        for idx, error_id in enumerate(error_ids):
            summary = explanations[idx] if idx < len(explanations) else {}
            message = summary.get("message") or f"Error {error_id}"
            lines.append(f"{error_id}: {message}")

            steps = summary.get("cause_steps") or []
            if steps:
                lines.append(f"  steps: {', '.join(steps)}")

            rules = summary.get("cause_rules") or []
            if rules:
                lines.append(f"  rules: {', '.join(rules)}")
                for rule_id in rules:
                    detail = rule_details.get(rule_id)
                    if detail and detail.get("description"):
                        lines.append(f"    {rule_id}: {detail['description']}")

            fixes = fix_candidates.get(error_id) or []
            if fixes:
                lines.append(f"  fix candidates: {', '.join(fixes)}")

        st.code("\n".join(lines), language=None)
