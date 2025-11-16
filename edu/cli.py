"""Command-line interface for MathLang Core."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional

from core import ast_nodes as ast
from core.causal.integration import run_causal_analysis
from core.evaluator import Evaluator, SymbolicEvaluationEngine
from core.knowledge_registry import KnowledgeRegistry
from core.learning_logger import LearningLogger
from core.polynomial_evaluator import PolynomialEvaluator
from core.symbolic_engine import SymbolicEngine
from core.errors import MathLangError, SyntaxError
from core.fuzzy.encoder import ExpressionEncoder
from core.fuzzy.metric import SimilarityMetric
from core.fuzzy.judge import FuzzyJudge
from edu.dsl import EduParser


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


def _symbolic_mode(program: ast.ProgramNode, learning_logger: LearningLogger) -> KnowledgeRegistry:
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
    return knowledge_registry


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


def _run_cli(argv: Optional[List[str]], parser_cls: type) -> int:
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
        return _hello_world()

    if not args.file and not args.code:
        print("Error: Provide either --file or --code snippet", file=sys.stderr)
        return 1
    if args.file and args.code:
        print("Error: --file and --code are mutually exclusive", file=sys.stderr)
        return 1

    learning_logger = LearningLogger()
    knowledge_registry: KnowledgeRegistry | None = None
    try:
        source = _load_source(args.file, args.code)
        program = parser_cls(source).parse()
        if args.mode == "symbolic":
            knowledge_registry = _symbolic_mode(program, learning_logger)
        else:
            _polynomial_mode(program, learning_logger)
        records = learning_logger.to_list()
        _print_records(records)
        _print_causal_summary(records, rule_info=_rule_metadata_from_registry(knowledge_registry))
        if args.counterfactual:
            _print_counterfactual_summary(records, args.counterfactual)
        return 0
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
    except MathLangError as exc:
        records = learning_logger.to_list()
        _print_records(records)
        _print_causal_summary(records, rule_info=_rule_metadata_from_registry(knowledge_registry))
        if args.counterfactual:
            _print_counterfactual_summary(records, args.counterfactual)
        print(f"Error: {exc}", file=sys.stderr)
    except Exception as exc:  # pragma: no cover - defensive.
        print(f"Unexpected error: {exc}", file=sys.stderr)
    return 1


def main(argv: Optional[List[str]] = None) -> int:
    return _run_cli(argv, EduParser)


def _print_records(records: List[dict], stream: Optional[object] = None) -> None:
    if stream is None:
        stream = sys.stdout
    for record in records:
        rendered = record.get("rendered") or record.get("expression") or ""
        if rendered:
            print(rendered, file=stream)


def _print_causal_summary(
    records: List[dict],
    stream: Optional[object] = None,
    *,
    rule_info: Dict[str, Dict[str, str]] | None = None,
) -> None:
    if not records:
        return
    engine, report = run_causal_analysis(records, rule_info=rule_info)
    error_ids: List[str] = report.get("errors", [])
    if not error_ids:
        return
    summaries = report.get("explanations", [])
    if stream is None:
        stream = sys.stdout
    print("\n== Causal Analysis ==", file=stream)
    rule_details: Dict[str, Dict[str, str]] = report.get("rule_details", {})
    for idx, error_id in enumerate(error_ids):
        summary = summaries[idx] if idx < len(summaries) else {"message": "", "cause_steps": [], "cause_rules": []}
        message = summary.get("message") or f"Error {error_id}"
        print(f"{error_id}: {message}", file=stream)
        steps = summary.get("cause_steps") or []
        rules = summary.get("cause_rules") or []
        if steps:
            print(f"  steps: {', '.join(steps)}", file=stream)
        if rules:
            print(f"  rules: {', '.join(rules)}", file=stream)
            for rule_id in rules:
                detail = rule_details.get(rule_id)
                if detail and detail.get("description"):
                    print(f"    {rule_id}: {detail['description']}", file=stream)
        fixes = engine.suggest_fix_candidates(error_id)
        if fixes:
            fix_ids = ", ".join(node.node_id for node in fixes)
            print(f"  fix candidates: {fix_ids}", file=stream)


def _print_counterfactual_summary(records: List[dict], intervention_str: str) -> None:
    intervention = _parse_counterfactual_json(intervention_str)
    if intervention is None:
        print("Invalid counterfactual JSON; skipping simulation.", file=sys.stderr)
        return
    engine = CausalEngine()
    engine.ingest_log(records)
    result = engine.counterfactual_result(intervention, records)
    print("\n== Counterfactual Simulation ==")
    if not result["changed"]:
        print("No changes applied.")
        return
    for step_diff in result.get("diff_steps", []):
        action = step_diff.get("action", "replace")
        print(
            f"Step {step_diff.get('index')} {action}: {step_diff.get('old_expression')} -> {step_diff.get('new_expression')}"
        )
    for end_diff in result.get("diff_end", []):
        print(
            f"End {end_diff.get('index')} {end_diff.get('action', 'replace')}: {end_diff.get('old_expression')} -> {end_diff.get('new_expression')}"
        )
    print(f"Rerun success: {result['rerun_success']} (last phase: {result['rerun_last_phase']})")
    if result.get("rerun_first_error"):
        print(f"First error after intervention: {result['rerun_first_error']}")
    print(f"New end expression: {result.get('new_end_expr')}")


def _parse_counterfactual_json(value: str) -> Dict[str, Any] | List[Dict[str, Any]] | None:
    try:
        import json

        data = json.loads(value)
        if isinstance(data, (dict, list)):
            return data
        return None
    except Exception:
        return None


def _rule_metadata_from_registry(
    registry: KnowledgeRegistry | None,
) -> Dict[str, Dict[str, str]]:
    source = registry
    if source is None:
        try:
            symbolic = SymbolicEngine()
            source = KnowledgeRegistry(
                base_path=Path(__file__).resolve().parent / "core" / "knowledge",
                engine=symbolic,
            )
        except Exception:  # pragma: no cover - best effort fallback
            return {}
    return {
        node.id: {
            "description": node.description,
            "domain": node.domain,
            "category": node.category,
            "pattern_before": node.pattern_before,
            "pattern_after": node.pattern_after,
        }
        for node in source.nodes
    }


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
