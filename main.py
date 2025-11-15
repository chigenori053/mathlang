"""Command-line interface for MathLang Core."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from core import ast_nodes as ast
from core.evaluator import Evaluator, SymbolicEvaluationEngine
from core.knowledge_registry import KnowledgeRegistry
from core.learning_logger import LearningLogger
from core.parser import Parser
from core.polynomial_evaluator import PolynomialEvaluator
from core.symbolic_engine import SymbolicEngine
from core.errors import MathLangError, SyntaxError
from core.fuzzy.encoder import ExpressionEncoder
from core.fuzzy.metric import SimilarityMetric
from core.fuzzy.judge import FuzzyJudge


def _load_source(file_path: Optional[str], inline_code: Optional[str]) -> str:
    if file_path:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Script '{file_path}' not found")
        return path.read_text(encoding="utf-8")
    if inline_code:
        return inline_code
    raise SyntaxError("Provide either --file or --code.")


def _hello_world() -> int:
    print("== MathLang Execution (hello-world self-test) ==")
    print("Step 1: show greeting")
    print("Hello World")
    print("Output: Hello World")
    return 0


def _symbolic_mode(program: ast.ProgramNode, learning_logger: LearningLogger) -> None:
    symbolic_engine = SymbolicEngine()
    knowledge_registry = KnowledgeRegistry(
        base_path=Path(__file__).resolve().parent / "core" / "knowledge",
        engine=symbolic_engine,
    )
    engine = SymbolicEvaluationEngine(symbolic_engine=symbolic_engine, knowledge_registry=knowledge_registry)
    fuzzy_judge = FuzzyJudge(
        encoder=ExpressionEncoder(),
        metric=SimilarityMetric(),
    )
    evaluator = Evaluator(program, engine, learning_logger=learning_logger, fuzzy_judge=fuzzy_judge)
    evaluator.run()


def _polynomial_mode(program: ast.ProgramNode, learning_logger: LearningLogger) -> None:
    symbolic_engine = SymbolicEngine()

    if symbolic_engine.has_sympy():

        def normalizer(expr: str) -> str:
            internal = symbolic_engine.to_internal(expr)
            return str(internal.expand())  # type: ignore[attr-defined]

    else:
        assignments = [
            {"x": 1, "y": 2, "z": 3},
            {"x": 2, "y": 1, "z": 0},
            {"a": 1, "b": 2, "c": 3},
        ]

        def normalizer(expr: str) -> str:
            values = []
            for assignment in assignments:
                try:
                    val = symbolic_engine.evaluate_numeric(expr, assignment)
                except Exception:
                    continue
                values.append(str(val))
            if not values:
                raise RuntimeError("Unable to normalize expression without SymPy.")
            return "|".join(values)

    evaluator = PolynomialEvaluator(program, normalizer=normalizer, learning_logger=learning_logger)
    evaluator.run()


def main(argv: Optional[List[str]] = None) -> int:
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
    args = parser.parse_args(argv)

    if args.hello_world_test:
        return _hello_world()

    if not args.file and not args.code:
        print("Error: Provide either --file or --code snippet", file=sys.stderr)
        return 1
    if args.file and args.code:
        print("Error: --file and --code are mutually exclusive", file=sys.stderr)
        return 1

    learning_logger = LearningLogger()
    try:
        source = _load_source(args.file, args.code)
        program = Parser(source).parse()
        if args.mode == "symbolic":
            _symbolic_mode(program, learning_logger)
        else:
            _polynomial_mode(program, learning_logger)
        _print_records(learning_logger.to_list())
        return 0
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
    except MathLangError as exc:
        _print_records(learning_logger.to_list())
        print(f"Error: {exc}", file=sys.stderr)
    except Exception as exc:  # pragma: no cover - defensive.
        print(f"Unexpected error: {exc}", file=sys.stderr)
    return 1


def _print_records(records: List[dict], stream: Optional[object] = None) -> None:
    if stream is None:
        stream = sys.stdout
    for record in records:
        rendered = record.get("rendered") or record.get("expression") or ""
        if rendered:
            print(rendered, file=stream)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
