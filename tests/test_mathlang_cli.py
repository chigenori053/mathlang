"""Tests for the unified `mathlang` command and its REPL."""

from __future__ import annotations

import io
import json

import pytest

from mathlang import api
from mathlang.cli import main
from mathlang.repl import Repl

VERIFIED_PROGRAM = "problem: (3 + 5) * 4\nstep: 8 * 4\nend: 32\n"
MISTAKEN_PROGRAM = "problem: (3 + 5) * 4\nstep: 8 * 5\nend: 40\n"


def run(*argv: str, stdin: str = "") -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    code = main(list(argv), out=out, err=err, stdin=io.StringIO(stdin))
    return code, out.getvalue(), err.getvalue()


def run_json(*argv: str) -> tuple[int, dict]:
    code, out, _ = run(*argv, "--json")
    return code, json.loads(out)


# -- expression subcommands -------------------------------------------------


def test_eval_exact_and_numeric():
    code, out, _ = run("eval", "sqrt(2)/2 + x", "-v", "x=1/3")
    assert code == 0
    assert out.strip() == "1/3 + sqrt(2)/2  ≈ 1.04044011451988"


def test_eval_integer_prints_once():
    assert run("eval", "2^10") == (0, "1024\n", "")


def test_eval_json():
    code, payload = run_json("eval", "1/4", "--precision", "3")
    assert code == 0
    assert payload == {
        "ok": True,
        "command": "eval",
        "input": {"expr": "1/4"},
        "result": {"exact": "1/4", "numeric": "0.250"},
    }


def test_eval_undefined_symbol_is_an_error():
    code, payload = run_json("eval", "x + 1")
    assert code == 1
    assert payload["ok"] is False
    assert payload["error"] == {"type": "EvaluationError", "message": "Undefined symbols: x"}


def test_eval_rejects_code_injection():
    code, out, err = run("eval", "__import__('os').getcwd()")
    assert code == 1
    assert out == ""
    assert "calls to named math functions" in err


@pytest.mark.parametrize(
    "argv, expected",
    [
        (("simplify", "sin(x)^2 + cos(x)^2"), "1"),
        (("simplify", "x + y", "-v", "y=x"), "2*x"),
        (("expand", "(x + 1)^2"), "x**2 + 2*x + 1"),
        (("factor", "x^2 - 1"), "(x - 1)*(x + 1)"),
        (("subs", "a*x + b", "-v", "x=5"), "5*a + b"),
        (("convert", "90*minute", "hour"), "3*hour/2"),
    ],
)
def test_transformations(argv, expected):
    assert run(*argv) == (0, expected + "\n", "")


def test_subs_requires_a_binding():
    code, _, err = run("subs", "x + 1")
    assert code == 2
    assert "-v NAME=VALUE" in err


def test_invalid_binding():
    code, _, err = run("eval", "x", "-v", "x")
    assert code == 1
    assert "expected NAME=VALUE" in err


def test_equiv_exit_status_reflects_result():
    assert run("equiv", "(x + 1)^2", "x^2 + 2*x + 1") == (0, "equivalent\n", "")
    assert run("equiv", "x + 1", "x") == (1, "not equivalent\n", "")


def test_timeout_aborts_long_computation():
    code, _, err = run("eval", "factorial(10**7)", "--timeout", "0.5")
    assert code == 1
    assert "timed out" in err


# -- run --------------------------------------------------------------------


def test_run_verified_program(tmp_path):
    path = tmp_path / "ok.mlang"
    path.write_text(VERIFIED_PROGRAM, encoding="utf-8")
    code, out, _ = run("run", str(path))
    assert code == 0
    assert out.splitlines()[-1] == "Result: verified"


def test_run_reports_mistakes_with_nonzero_exit():
    code, out, _ = run("run", "-", stdin=MISTAKEN_PROGRAM)
    assert code == 1
    assert "== Causal Analysis ==" in out
    assert out.splitlines()[-1] == "Result: 2 mistake(s) (step1, end)"


def test_run_inline_code_json():
    code, payload = run_json("run", "-c", VERIFIED_PROGRAM.replace("\n", "\\n"))
    assert code == 0
    assert payload["command"] == "run"
    assert payload["verified"] is True
    assert payload["mistake_count"] == 0
    assert payload["error"] is None


def test_run_parse_error():
    code, _, err = run("run", "-c", "problem: 1 + 1")
    assert code == 1
    assert err.startswith("Error:")


def test_run_missing_file():
    code, _, err = run("run", "does-not-exist.mlang")
    assert code == 1
    assert "not found" in err


def test_usage_error_exit_code():
    assert run("run")[0] == 2


# -- api --------------------------------------------------------------------


def test_program_result_verdict():
    assert api.run_program(VERIFIED_PROGRAM).verified
    mistaken = api.run_program(MISTAKEN_PROGRAM)
    assert mistaken.ok and not mistaken.verified
    assert [record["phase"] for record in mistaken.mistakes] == ["step", "end"]


# -- repl -------------------------------------------------------------------


def repl_session(*lines: str, json_output: bool = False) -> list[str]:
    out = io.StringIO()
    Repl(out=out, json_output=json_output).loop(io.StringIO("\n".join(lines) + "\n"))
    return out.getvalue().splitlines()


def test_repl_variables_and_ans():
    assert repl_session("x = 3", "y = x^2 + 1/2", "y", "ans * 2", "a + x") == [
        "x = 3",
        "y = 19/2",
        "19/2  ≈ 9.50000000000000",
        "19",
        "a + 3",
    ]


def test_repl_commands():
    output = repl_session(
        ":equiv (a+b)^2 ; a^2 + 2*a*b + b^2",
        ":convert 3*kilometer -> meter",
        ":factor x^2 - 4",
        "z = 1",
        ":vars",
        ":clear",
        ":vars",
    )
    assert output == [
        "equivalent",
        "3000*meter",
        "(x - 2)*(x + 2)",
        "z = 1",
        "z = 1",
        "variables cleared",
        "(no variables)",
    ]


def test_repl_errors_do_not_end_session():
    assert repl_session(":nope", "open('x')", "1 + 1") == [
        "Error: Unknown command ':nope'. Type :help.",
        "Error: Function 'open' is not allowed.",
        "2",
    ]


def test_repl_inline_dsl_block():
    output = repl_session(":dsl", *VERIFIED_PROGRAM.splitlines(), "", "1 + 1")
    assert output[-2:] == ["Result: verified", "2"]


def test_repl_quit_stops_reading():
    assert repl_session("1 + 1", ":quit", "2 + 2") == ["2"]


def test_repl_json_mode():
    output = repl_session(":json on", "sqrt(8)")
    assert json.loads(output[-1]) == {
        "ok": True,
        "command": "eval",
        "result": {"exact": "2*sqrt(2)", "numeric": "2.82842712474619"},
    }
