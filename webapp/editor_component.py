"""Custom Streamlit component: a CodeMirror-based DSL editor wired to the
MathLang LSP server for real-time diagnostics and hover docs (no completion).

Static/no-build component (see webapp/frontend/index.html): the frontend is
plain HTML/JS loading CodeMirror 6 and its own LSP client from a CDN, so no
npm/webpack toolchain is required to develop or ship this project.
"""

from __future__ import annotations

from pathlib import Path

import streamlit.components.v1 as components

_FRONTEND_DIR = Path(__file__).parent / "frontend"

_component_func = components.declare_component("mathlang_editor", path=str(_FRONTEND_DIR))


def mathlang_editor(
    value: str,
    *,
    key: str,
    lsp_url: str = "ws://127.0.0.1:2087",
    height: int = 200,
) -> str:
    """Render the DSL cell editor and return its current source text."""

    result = _component_func(value=value, lsp_url=lsp_url, height=height, key=key, default=value)
    return result if isinstance(result, str) else value
