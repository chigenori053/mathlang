"""Utility script to run the bundled MathLang example program."""

from __future__ import annotations

from pathlib import Path

from core.evaluator import Evaluator
from core.i18n import get_language_pack
from core.parser import Parser


EXAMPLE_PATH = Path(__file__).with_name("pythagorean.mlang")


def main() -> None:
    source = EXAMPLE_PATH.read_text(encoding="utf-8")
    language = get_language_pack()
    program = Parser(source, language=language).parse()
    evaluator = Evaluator(program, language=language)
    step_label = language.text("cli.step_label")

    for result in evaluator.run():
        if result.step_number:
            print(f"{step_label} {result.step_number}: {result.message}")
        else:
            print(result.message)


if __name__ == "__main__":
    main()
