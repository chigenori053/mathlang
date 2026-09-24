"""The `mathlang` command: evaluate expressions and MathLang programs from a terminal.

Subcommands::

    mathlang run FILE | -c CODE        run a .mlang program (FILE "-" reads stdin)
    mathlang eval EXPR [-v x=2 ...]     numeric value (exact + decimal)
    mathlang simplify|expand|factor EXPR
    mathlang subs EXPR -v x=2 ...       substitute variables
    mathlang equiv EXPR1 EXPR2          equivalence check (exit 0 = equivalent)
    mathlang convert EXPR UNIT          unit conversion
    mathlang repl                       interactive session

Every subcommand accepts ``--json`` (machine-readable output on stdout) and
``--timeout SECONDS``. Exit status: 0 success, 1 evaluation failure / not
equivalent / program error or unverified step, 2 usage error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable, Optional, Sequence, TextIO

from core.errors import MathLangError
from core.log_formatter import format_record_label
from mathlang import __version__, api

EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_USAGE = 2

DEFAULT_TIMEOUT = 10.0


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------


def _emit_json(payload: dict[str, Any], stream: TextIO) -> None:
    print(json.dumps(payload, ensure_ascii=False, default=str), file=stream)


def _error_payload(command: str, exc: BaseException) -> dict[str, Any]:
    return {
        "ok": False,
        "command": command,
        "error": {"type": type(exc).__name__, "message": str(exc)},
    }


def program_lines(result: api.ProgramResult) -> list[str]:
    """Human-readable trace of a program run, ending with a verdict line."""

    lines = result.formatted_lines + causal_lines(result.causal)
    if result.error:
        return lines
    if result.verified:
        lines.append("Result: verified")
    else:
        labels = ", ".join(format_record_label(record) for record in result.mistakes)
        lines.append(f"Result: {len(result.mistakes)} mistake(s) ({labels})")
    return lines


def causal_lines(causal: dict[str, Any] | None) -> list[str]:
    if not causal:
        return []
    lines = ["", "== Causal Analysis =="]
    explanations = causal.get("explanations", [])
    fix_candidates = causal.get("fix_candidates", {})
    for idx, error_id in enumerate(causal.get("errors", [])):
        summary = explanations[idx] if idx < len(explanations) else {}
        lines.append(f"{error_id}: {summary.get('message') or f'Error {error_id}'}")
        if summary.get("cause_steps"):
            lines.append(f"  steps: {', '.join(summary['cause_steps'])}")
        if summary.get("cause_rules"):
            lines.append(f"  rules: {', '.join(summary['cause_rules'])}")
        if fix_candidates.get(error_id):
            lines.append(f"  fix candidates: {', '.join(fix_candidates[error_id])}")
    return lines


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------


def _read_source(args: argparse.Namespace, stdin: TextIO) -> str:
    if args.code is not None:
        return args.code.replace("\\n", "\n")
    if args.file == "-":
        return stdin.read()
    path = Path(args.file)
    if not path.is_file():
        raise FileNotFoundError(f"Script '{args.file}' not found")
    return path.read_text(encoding="utf-8")


def _cmd_run(args: argparse.Namespace, out: TextIO, err: TextIO, stdin: TextIO) -> int:
    try:
        source = _read_source(args, stdin)
    except FileNotFoundError as exc:
        if args.json:
            _emit_json(_error_payload("run", exc), out)
        else:
            print(f"Error: {exc}", file=err)
        return EXIT_FAILURE
    with api.time_limit(args.timeout):
        result = api.run_program(source, mode=args.mode)
    if args.json:
        _emit_json({"command": "run", **result.to_dict()}, out)
    else:
        for line in program_lines(result):
            print(line, file=out)
        if result.error:
            print(f"Error: {result.error}", file=err)
    return EXIT_OK if result.verified else EXIT_FAILURE


def _expression_command(
    name: str, compute: Callable[[argparse.Namespace], Any], render: Callable[[Any], str] = str
) -> Callable[[argparse.Namespace, TextIO, TextIO, TextIO], int]:
    def handler(args: argparse.Namespace, out: TextIO, err: TextIO, stdin: TextIO) -> int:
        with api.time_limit(args.timeout):
            result = compute(args)
        if args.json:
            _emit_json({"ok": True, "command": name, "input": _inputs(args), "result": result}, out)
        else:
            print(render(result), file=out)
        return EXIT_OK

    return handler


def _inputs(args: argparse.Namespace) -> dict[str, Any]:
    fields = ("expr", "expr1", "expr2", "unit", "var")
    return {key: getattr(args, key) for key in fields if getattr(args, key, None) is not None}


def _bindings(args: argparse.Namespace) -> dict[str, str]:
    return api.parse_bindings(args.var or [])


def _render_eval(result: dict[str, str]) -> str:
    if result["exact"] == result["numeric"]:
        return result["exact"]
    return f"{result['exact']}  ≈ {result['numeric']}"


def _cmd_equiv(args: argparse.Namespace, out: TextIO, err: TextIO, stdin: TextIO) -> int:
    with api.time_limit(args.timeout):
        equivalent = api.check_equivalence(args.expr1, args.expr2)
    if args.json:
        _emit_json(
            {"ok": True, "command": "equiv", "input": _inputs(args), "result": equivalent}, out
        )
    else:
        print("equivalent" if equivalent else "not equivalent", file=out)
    return EXIT_OK if equivalent else EXIT_FAILURE


def _cmd_repl(args: argparse.Namespace, out: TextIO, err: TextIO, stdin: TextIO) -> int:
    from mathlang.repl import Repl

    return Repl(timeout=args.timeout, json_output=args.json, out=out).loop(stdin)


_HANDLERS: dict[str, Callable[[argparse.Namespace, TextIO, TextIO, TextIO], int]] = {
    "run": _cmd_run,
    "eval": _expression_command(
        "eval",
        lambda a: api.evaluate(a.expr, _bindings(a), precision=a.precision),
        _render_eval,
    ),
    "simplify": _expression_command("simplify", lambda a: api.simplify(a.expr, _bindings(a))),
    "expand": _expression_command("expand", lambda a: api.expand(a.expr)),
    "factor": _expression_command("factor", lambda a: api.factor(a.expr)),
    "subs": _expression_command("subs", lambda a: api.substitute(a.expr, _bindings(a))),
    "equiv": _cmd_equiv,
    "convert": _expression_command("convert", lambda a: api.convert_units(a.expr, a.unit)),
    "repl": _cmd_repl,
}


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", help="print machine-readable JSON")
    common.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        metavar="SECONDS",
        help=f"abort evaluation after SECONDS (default {DEFAULT_TIMEOUT:g}; 0 disables)",
    )

    var_option = argparse.ArgumentParser(add_help=False)
    var_option.add_argument(
        "-v",
        "--var",
        action="append",
        metavar="NAME=VALUE",
        help="bind a variable (repeatable), e.g. -v x=2 -v y=1/3",
    )

    parser = argparse.ArgumentParser(
        prog="mathlang",
        description="Evaluate mathematical expressions and verify MathLang programs.",
    )
    parser.add_argument("--version", action="version", version=f"mathlang {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="COMMAND", required=True)

    run = sub.add_parser("run", parents=[common], help="run a MathLang (.mlang) program")
    source = run.add_mutually_exclusive_group(required=True)
    source.add_argument("file", nargs="?", help='path to a .mlang file ("-" for stdin)')
    source.add_argument("-c", "--code", help="inline program source (\\n for newlines)")
    run.add_argument("--mode", choices=api.MODES, default="symbolic", help="evaluation mode")

    ev = sub.add_parser("eval", parents=[common, var_option], help="evaluate an expression numerically")
    ev.add_argument("expr")
    ev.add_argument(
        "--precision", type=int, default=api.DEFAULT_PRECISION, help="significant digits of the decimal value"
    )

    for name, help_text in (
        ("simplify", "simplify an expression"),
        ("expand", "expand products and powers"),
        ("factor", "factor a polynomial"),
    ):
        parents = [common, var_option] if name == "simplify" else [common]
        cmd = sub.add_parser(name, parents=parents, help=help_text)
        cmd.add_argument("expr")

    subs = sub.add_parser("subs", parents=[common, var_option], help="substitute variables into an expression")
    subs.add_argument("expr")

    equiv = sub.add_parser("equiv", parents=[common], help="check whether two expressions are equivalent")
    equiv.add_argument("expr1")
    equiv.add_argument("expr2")

    convert = sub.add_parser("convert", parents=[common], help="convert a quantity to another unit")
    convert.add_argument("expr", help='quantity, e.g. "3 * kilometer"')
    convert.add_argument("unit", help='target unit, e.g. "meter"')

    sub.add_parser("repl", parents=[common], help="start an interactive session")
    return parser


def main(
    argv: Optional[Sequence[str]] = None,
    *,
    out: TextIO | None = None,
    err: TextIO | None = None,
    stdin: TextIO | None = None,
) -> int:
    out = out or sys.stdout
    err = err or sys.stderr
    stdin = stdin or sys.stdin
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code or 0)

    if args.command == "subs" and not args.var:
        print("mathlang subs: error: at least one -v NAME=VALUE is required", file=err)
        return EXIT_USAGE

    try:
        return _HANDLERS[args.command](args, out, err, stdin)
    except MathLangError as exc:
        if args.json:
            _emit_json(_error_payload(args.command, exc), out)
        else:
            print(f"Error: {exc}", file=err)
        return EXIT_FAILURE
    except KeyboardInterrupt:
        print("Interrupted.", file=err)
        return 130
    except Exception as exc:  # SymPy can raise arbitrary errors on odd input.
        if args.json:
            _emit_json(_error_payload(args.command, exc), out)
        else:
            print(f"Unexpected error: {exc}", file=err)
        return EXIT_FAILURE


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
