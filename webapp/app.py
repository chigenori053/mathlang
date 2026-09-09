"""Streamlit entrypoint: MathLang notebook-style web UI.

Run with `make web` (or `uv run streamlit run webapp/app.py`). The MathLang
LSP server (diagnostics + hover for the cell editor) is spawned automatically
if it isn't already running, so this single command is enough to get the
full experience.
"""

from __future__ import annotations

import socket
import subprocess
import sys
import uuid
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))  # `streamlit run webapp/app.py` sets sys.path[0] to webapp/, not the repo root.

import streamlit as st

from notebooks.sample_programs import SAMPLE_PROGRAMS
from webapp.editor_component import mathlang_editor
from webapp.engine import MODES, run_cell
from webapp.render import render_cell_result

LSP_HOST = "127.0.0.1"
LSP_PORT = 2087
LSP_URL = f"ws://{LSP_HOST}:{LSP_PORT}"

DEFAULT_SOURCE = "problem: \nstep: \nend: \n"


def _lsp_is_running() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex((LSP_HOST, LSP_PORT)) == 0


def _ensure_lsp_server() -> None:
    if st.session_state.get("lsp_spawned"):
        return
    st.session_state.lsp_spawned = True
    if _lsp_is_running():
        return
    subprocess.Popen(
        [sys.executable, "-m", "tools.lsp.server"],
        cwd=str(_REPO_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _new_cell(source: str = DEFAULT_SOURCE, mode: str = "symbolic") -> dict:
    return {"id": uuid.uuid4().hex, "source": source, "mode": mode, "exec_count": None}


def _init_state() -> None:
    if "cells" not in st.session_state:
        st.session_state.cells = [_new_cell()]
    if "results" not in st.session_state:
        st.session_state.results = {}
    if "exec_counter" not in st.session_state:
        st.session_state.exec_counter = 0


def _run(cell: dict) -> None:
    st.session_state.exec_counter += 1
    cell["exec_count"] = st.session_state.exec_counter
    st.session_state.results[cell["id"]] = run_cell(cell["source"], cell["mode"])


def _sidebar() -> None:
    st.sidebar.title("MathLang Notebook")

    labels = [program.title for program in SAMPLE_PROGRAMS]
    choice = st.sidebar.selectbox("Example", options=range(len(SAMPLE_PROGRAMS)), format_func=lambda i: labels[i])
    if st.sidebar.button("+ Insert as cell"):
        st.session_state.cells.append(_new_cell(SAMPLE_PROGRAMS[choice].source))
        st.rerun()

    if st.sidebar.button("+ Empty cell"):
        st.session_state.cells.append(_new_cell())
        st.rerun()

    if st.sidebar.button("▶ Run all", type="primary"):
        for cell in st.session_state.cells:
            _run(cell)
        st.rerun()


def _render_cell(cell: dict) -> None:
    prompt = f"In [{cell['exec_count']}]:" if cell["exec_count"] is not None else "In [ ]:"

    prompt_col, editor_col, controls_col = st.columns([1, 10, 1])
    prompt_col.caption(prompt)
    with editor_col:
        cell["source"] = mathlang_editor(cell["source"], key=f"editor_{cell['id']}", lsp_url=LSP_URL)
    with controls_col:
        run_clicked = st.button("▶", key=f"run_{cell['id']}", help="Run")
        delete_clicked = st.button("✕", key=f"del_{cell['id']}", help="Delete")
        cell["mode"] = st.selectbox(
            "mode",
            MODES,
            index=MODES.index(cell["mode"]),
            key=f"mode_{cell['id']}",
            label_visibility="collapsed",
        )

    if delete_clicked:
        st.session_state.cells = [c for c in st.session_state.cells if c["id"] != cell["id"]]
        st.session_state.results.pop(cell["id"], None)
        st.rerun()

    if run_clicked:
        _run(cell)
        st.rerun()

    result = st.session_state.results.get(cell["id"])
    if result is not None:
        out_prompt_col, out_col = st.columns([1, 11])
        out_prompt_col.caption(f"Out[{cell['exec_count']}]:")
        with out_col:
            render_cell_result(result)


def main() -> None:
    st.set_page_config(page_title="MathLang Notebook", layout="wide")
    _ensure_lsp_server()
    _init_state()
    _sidebar()

    for cell in st.session_state.cells:
        _render_cell(cell)


main()
