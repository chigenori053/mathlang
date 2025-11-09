"""Command-line entry point for running MathLang programs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from typing import Callable

from core.evaluator import EvaluationError, Evaluator
from core.i18n import LanguagePack, available_languages, get_language_pack
from core.parser import Parser, ParserError
from core.polynomial_evaluator import PolynomialEvaluationError, PolynomialEvaluator
from core.symbolic_engine import SymbolicEngine, SymbolicEngineError


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=get_language_pack().text("cli.description"))
    parser.add_argument(
        "script",
        nargs="?",
        help=get_language_pack().text("cli.script_help"),
    )
    parser.add_argument(
        "-c",
        "--code",
        help=get_language_pack().text("cli.code_help"),
    )
    parser.add_argument(
        "--symbolic",
        metavar="EXPR",
        help=get_language_pack().text("cli.symbolic_help"),
    )
    parser.add_argument(
        "--symbolic-trace",
        action="store_true",
        help=get_language_pack().text("cli.symbolic_trace_help"),
    )
    parser.add_argument(
        "--polynomial",
        action="store_true",
        help=get_language_pack().text("cli.polynomial_help"),
    )
    parser.add_argument(
        "--hello-world-test",
        action="store_true",
        help=get_language_pack().text("cli.hello_help"),
    )
    parser.add_argument(
        "--language",
        choices=available_languages(),
        default="ja",
        help=get_language_pack().text("cli.language_help"),
    )
    return parser


def _load_source(args: argparse.Namespace, language: LanguagePack) -> tuple[str, str]:
    if args.code:
        return args.code, language.text("cli.inline_label")
    if args.script:
        script_path = Path(args.script)
        if not script_path.exists():
            raise FileNotFoundError(language.text("cli.script_not_found", path=script_path))
        return script_path.read_text(encoding="utf-8"), str(script_path)
    raise ValueError(language.text("cli.missing_input"))


def _render_results(evaluator: Evaluator, language: LanguagePack) -> None:
    step_label = language.text("cli.step_label")
    for result in evaluator.run():
        if result.step_number:
            print(f"{step_label} {result.step_number}: {result.message}")
        else:
            print(result.message)


def _render_polynomial_results(evaluator: PolynomialEvaluator, language: LanguagePack) -> None:
    step_label = language.text("cli.step_label")
    for result in evaluator.run():
        if result.step_number:
            print(f"{step_label} {result.step_number}: {result.message}")
        else:
            print(result.message)


def _run_hello_world_test(language: LanguagePack) -> int:
    print(language.text("cli.heading_hello"))
    print(language.text("cli.hello_step"))
    print(language.text("cli.hello_output"))
    return 0


def _run_symbolic_mode(
    expression: str,
    language: LanguagePack,
    engine_factory: Callable[[], SymbolicEngine] = SymbolicEngine,
) -> int:
    try:
        engine = engine_factory()
    except SymbolicEngineError as exc:
        print(f"[Symbolic Error] {exc}", file=sys.stderr)
        return 1

    print(language.text("cli.heading_symbolic"))
    print(language.text("cli.symbolic_input", expression=expression))

    try:
        result = engine.simplify(expression)
        structure = engine.explain(expression)
    except SymbolicEngineError as exc:
        print(f"[Symbolic Error] {exc}", file=sys.stderr)
        return 1

    print(language.text("cli.symbolic_result", result=result.simplified))
    print(language.text("cli.symbolic_explanation", explanation=result.explanation))
    print(language.text("cli.symbolic_structure", structure=structure))
    return 0


def _run_polynomial_mode(expression: str, language: LanguagePack) -> int:
    synthetic_source = f"result = {expression}\nshow result\n"
    try:
        program = Parser(synthetic_source, language=language).parse()
    except ParserError as exc:
        print(language.text("cli.polynomial_parse_error", error=exc), file=sys.stderr)
        return 1

    evaluator = PolynomialEvaluator(program)
    print(language.text("cli.heading_polynomial"))
    print(language.text("cli.polynomial_input", expression=expression))

    try:
        _render_polynomial_results(evaluator, language)
    except PolynomialEvaluationError as exc:
        print(language.text("cli.polynomial_error", error=exc), file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = _build_arg_parser()
    args = parser.parse_args()
    language = get_language_pack(args.language)

    if args.symbolic:
        if args.script or args.code:
            parser.error(language.text("cli.symbolic_conflict_script"))
        if args.symbolic_trace:
            parser.error(language.text("cli.symbolic_conflict_trace"))
        return _run_symbolic_mode(args.symbolic, language)

    if args.polynomial:
        if args.symbolic_trace:
            parser.error(language.text("cli.polynomial_conflict_trace"))
        
        try:
            source, label = _load_source(args, language)
        except ValueError as exc:
            parser.error(str(exc))
        except FileNotFoundError as exc:
            print(str(exc), file=sys.stderr)
            return 1

        try:
            program = Parser(source, language=language).parse()
        except ParserError as exc:
            print(f"[Parse Error] {exc}", file=sys.stderr)
            return 1

        evaluator = PolynomialEvaluator(program)
        print(language.text("cli.heading_execution", label=label))
        try:
            _render_polynomial_results(evaluator, language)
        except PolynomialEvaluationError as exc:
            print(f"[Polynomial Error] {exc}", file=sys.stderr)
            return 1
        return 0


    if args.hello_world_test:
        if args.script or args.code:
            parser.error(language.text("cli.hello_conflict_script"))
        if args.symbolic:
            parser.error(language.text("cli.hello_conflict_symbolic"))
        if args.polynomial:
            parser.error(language.text("cli.hello_conflict_polynomial"))
        return _run_hello_world_test(language)

    try:
        source, label = _load_source(args, language)
    except ValueError as exc:
        parser.error(str(exc))
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    try:
        program = Parser(source, language=language).parse()
    except ParserError as exc:
        print(f"[Parse Error] {exc}", file=sys.stderr)
        return 1

    symbolic_factory = SymbolicEngine if args.symbolic_trace else None
    evaluator = Evaluator(program, symbolic_engine_factory=symbolic_factory, language=language)
    print(language.text("cli.heading_execution", label=label))

    try:
        _render_results(evaluator, language)
    except EvaluationError as exc:
        print(f"[Evaluation Error] {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover - manual invocation entry.
    raise SystemExit(main())
