"""Shared CLI runner utilities for edu/pro/demo entry points."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable, Optional, Sequence, Any

from core.errors import MathLangError
from core.learning_logger import LearningLogger


def _load_source(file_path: Optional[str], inline_code: Optional[str]) -> str:
    if file_path:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Script '{file_path}' not found")
        return path.read_text(encoding="utf-8")
    if inline_code:
        return inline_code
    raise MathLangError("Provide either --file or --code.")


def run_cli(
    argv: Optional[Sequence[str]],
    parser_cls: type,
    *,
    symbolic_runner: Callable[[Any, LearningLogger], Optional[Any]],
    polynomial_runner: Callable[[Any, LearningLogger], None],
    postprocess: Callable[[list[dict[str, Any]], Optional[Any], Optional[str]], None],
) -> int:
    parser = argparse.ArgumentParser(description="MathLang Program Runner")
    parser.add_argument("--file", help="Path to a .mlang file.")
    parser.add_argument("-c", "--code", help="Inline MathLang source.")
    parser.add_argument("--hello-world-test", action="store_true", help="Run built-in hello world test.")
    parser.add_argument(
        "--mode",
        choices=("symbolic", "polynomial"),
        default="symbolic",
        help="Evaluation mode (symbolic or polynomial).",
    )
    parser.add_argument(
        "--counterfactual",
        help="Apply a simple counterfactual intervention (JSON string). Example: "
        "'{\"phase\": \"step\", \"index\": 2, \"expression\": \"8 * 4\"}'",
    )
    args = parser.parse_args(argv)

    if args.hello_world_test:
        print("== MathLang Execution (hello-world self-test) ==")
        print("Hello World")
        return 0

    if not args.file and not args.code:
        print("Error: Provide either --file or --code snippet", file=sys.stderr)
        return 1
    if args.file and args.code:
        print("Error: --file and --code are mutually exclusive", file=sys.stderr)
        return 1

    learning_logger = LearningLogger()
    knowledge_registry: Any | None = None
    try:
        source = _load_source(args.file, args.code)
        program = parser_cls(source).parse()
        if args.mode == "symbolic":
            knowledge_registry = symbolic_runner(program, learning_logger)
        else:
            polynomial_runner(program, learning_logger)
        records = learning_logger.to_list()
        postprocess(records, knowledge_registry, args.counterfactual)
        return 0
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
    except MathLangError as exc:
        records = learning_logger.to_list()
        postprocess(records, knowledge_registry, args.counterfactual)
        print(f"Error: {exc}", file=sys.stderr)
    except Exception as exc:  # pragma: no cover
        print(f"Unexpected error: {exc}", file=sys.stderr)
    return 1
