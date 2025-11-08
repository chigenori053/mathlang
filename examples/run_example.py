"""Utility script to run the bundled MathLang example program."""

from __future__ import annotations

from pathlib import Path

from core.evaluator import Evaluator
from core.parser import Parser


EXAMPLE_PATH = Path(__file__).with_name("pythagorean.mlang")


def main() -> None:
    source = EXAMPLE_PATH.read_text(encoding="utf-8")
    program = Parser(source).parse()
    evaluator = Evaluator(program)

    for result in evaluator.run():
        if result.step_number:
            print(f"Step {result.step_number}: {result.message}")
        else:
            print(result.message)


if __name__ == "__main__":
    main()
