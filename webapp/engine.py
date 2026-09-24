"""Pure execution logic for the MathLang notebook web UI.

No Streamlit import here on purpose: the program runner lives in
`mathlang.api` (shared with the `mathlang` CLI) so it can be exercised
directly by pytest, independent of the UI layer.
"""

from __future__ import annotations

from mathlang.api import MODES, ProgramResult as CellResult, run_program as run_cell

__all__ = ["MODES", "CellResult", "run_cell"]
