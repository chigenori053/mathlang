"""Pro CLI entry point."""

from __future__ import annotations

from typing import List, Optional

from cli.base_runner import run_cli
from cli.modes import run_symbolic_mode, run_polynomial_mode
from cli.output import (
    print_records,
    print_causal_summary,
    print_counterfactual_summary,
    should_run_causal_analysis,
    rule_metadata_from_registry,
)
from pro.dsl import ProParser


def _postprocess(records, knowledge_registry, counterfactual_arg: Optional[str]) -> None:
    print_records(records)
    if should_run_causal_analysis(records):
        print_causal_summary(records, rule_info=rule_metadata_from_registry(knowledge_registry))
    if counterfactual_arg:
        print_counterfactual_summary(records, counterfactual_arg)


def main(argv: Optional[List[str]] = None) -> int:
    return run_cli(
        argv,
        ProParser,
        symbolic_runner=run_symbolic_mode,
        polynomial_runner=run_polynomial_mode,
        postprocess=_postprocess,
    )


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
