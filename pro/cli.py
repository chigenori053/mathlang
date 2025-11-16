"""CLI entry point for MathLang Pro edition."""

from __future__ import annotations

from typing import List, Optional

from edu.cli import _run_cli
from pro.dsl import ProParser


def main(argv: Optional[List[str]] = None) -> int:
    """Run the Pro CLI using the shared runner with the Pro parser."""
    return _run_cli(argv, ProParser)
