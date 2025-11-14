import argparse
import sys
from pathlib import Path
from typing import List

from core.evaluator import Evaluator, EvaluationError
from core.i18n import get_language_pack
from core.logging import LearningLogger
from core.parser import Parser, ParserError

def main(argv: List[str] | None = None) -> int:
    """Main entry point for the MathLang CLI."""
    parser = argparse.ArgumentParser(description="MathLang Interpreter")
    parser.add_argument("file", help="The .mlang file to execute.")
    parser.add_argument(
        "--lang",
        default="ja",
        help="Language for output messages (e.g., 'en', 'ja').",
    )
    parser.add_argument(
        "--log",
        help="Path to a file to record learning log entries.",
    )
    args = parser.parse_args(argv)

    try:
        with open(args.file, "r", encoding="utf-8") as f:
            source = f.read()
    except FileNotFoundError:
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        return 1

    try:
        language_pack = get_language_pack(args.lang)
        learning_logger = LearningLogger() if args.log else None

        math_parser = Parser(source, language=language_pack)
        program = math_parser.parse()

        evaluator = Evaluator(
            program,
            language=language_pack,
            learning_logger=learning_logger,
        )

        for result in evaluator.step_eval():
            print(result.message)

        if learning_logger and args.log:
            learning_logger.write(Path(args.log))

    except (ParserError, EvaluationError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
