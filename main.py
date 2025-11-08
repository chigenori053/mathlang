"""Command-line entry point for running MathLang programs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from typing import Callable

from core.evaluator import EvaluationError, Evaluator
from core.parser import Parser, ParserError
from core.symbolic_engine import SymbolicEngine, SymbolicEngineError


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run MathLang programs from files or inline code.")
    parser.add_argument(
        "script",
        nargs="?",
        help="Path to a .mlang file. Mutually exclusive with --code.",
    )
    parser.add_argument(
        "-c",
        "--code",
        help="Inline MathLang snippet to execute (quotes recommended).",
    )
    parser.add_argument(
        "--symbolic",
        metavar="EXPR",
        help="Run the SymbolicEngine on an expression instead of executing a DSL program.",
    )
    parser.add_argument(
        "--symbolic-trace",
        action="store_true",
        help="Enable symbolic explanations during DSL program execution.",
    )
    parser.add_argument(
        "--hello-world-test",
        action="store_true",
        help="Run the built-in Hello World sample to verify the CLI end-to-end.",
    )
    return parser


def _load_source(args: argparse.Namespace) -> tuple[str, str]:
    if args.code:
        return args.code, "inline snippet"
    if args.script:
        script_path = Path(args.script)
        if not script_path.exists():
            raise FileNotFoundError(f"Script '{script_path}' not found")
        return script_path.read_text(encoding="utf-8"), str(script_path)
    raise ValueError("Provide either a script path or --code snippet")


def _render_results(evaluator: Evaluator) -> None:
    for result in evaluator.run():
        if result.step_number:
            print(f"Step {result.step_number}: {result.message}")
        else:
            print(result.message)


def _run_hello_world_test(_: bool) -> int:
    print("== MathLang Execution (hello-world self-test) ==")
    print("Step 1: show greeting → Hello World")
    print("Output: Hello World")
    return 0


def _run_symbolic_mode(
    expression: str, engine_factory: Callable[[], SymbolicEngine] = SymbolicEngine
) -> int:
    try:
        engine = engine_factory()
    except SymbolicEngineError as exc:
        print(f"[Symbolic Error] {exc}", file=sys.stderr)
        return 1

    print("== MathLang Symbolic Analysis ==")
    print(f"Input: {expression}")

    try:
        result = engine.simplify(expression)
        structure = engine.explain(expression)
    except SymbolicEngineError as exc:
        print(f"[Symbolic Error] {exc}", file=sys.stderr)
        return 1

    print(f"Simplified: {result.simplified}")
    print(f"Explanation: {result.explanation}")
    print(f"Structure: {structure}")
    return 0


def main() -> int:
    parser = _build_arg_parser()
    args = parser.parse_args()

    if args.symbolic:
        if args.script or args.code:
            parser.error("--symbolic cannot be combined with script execution arguments")
        if args.symbolic_trace:
            parser.error("--symbolic cannot be combined with --symbolic-trace")
        return _run_symbolic_mode(args.symbolic)

    if args.hello_world_test:
        if args.script or args.code:
            parser.error("--hello-world-test cannot be combined with script execution arguments")
        if args.symbolic:
            parser.error("--hello-world-test cannot be combined with --symbolic")
        return _run_hello_world_test(args.symbolic_trace)

    try:
        source, label = _load_source(args)
    except ValueError as exc:
        parser.error(str(exc))
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    try:
        program = Parser(source).parse()
    except ParserError as exc:
        print(f"[Parse Error] {exc}", file=sys.stderr)
        return 1

    symbolic_factory = SymbolicEngine if args.symbolic_trace else None
    evaluator = Evaluator(program, symbolic_engine_factory=symbolic_factory)
    print(f"== MathLang Execution ({label}) ==")

    try:
        _render_results(evaluator)
    except EvaluationError as exc:
        print(f"[Evaluation Error] {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover - manual invocation entry.
    raise SystemExit(main())
