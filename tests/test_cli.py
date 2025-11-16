import textwrap
from pathlib import Path

import pytest

from main import main


def test_cli_hello_world(capsys):
    assert main(["--hello-world-test"]) == 0
    captured = capsys.readouterr()
    assert "Hello World" in captured.out


def test_cli_runs_inline_code(capsys):
    capsys.readouterr()
    source = textwrap.dedent(
        """
        problem: 1 + 1
        end: 2
        """
    )
    result = main(["-c", source])
    captured = capsys.readouterr()
    assert result == 0
    assert "Problem" in captured.out


def test_cli_runs_file(tmp_path: Path, capsys):
    capsys.readouterr()
    script = tmp_path / "sample.mlang"
    script.write_text("problem: 1 + 1\nend: 2\n", encoding="utf-8")
    result = main(["--file", str(script)])
    captured = capsys.readouterr()
    assert result == 0
    assert "End" in captured.out


def test_cli_requires_input(capsys):
    assert main([]) == 1
    captured = capsys.readouterr()
    assert "Provide either --file or --code" in captured.err


def test_cli_prints_fuzzy_on_invalid_step(capsys):
    capsys.readouterr()
    source = textwrap.dedent(
        """
        problem: 1 + 1
        step: 3
        end: done
        """
    )
    result = main(["-c", source])
    captured = capsys.readouterr()
    assert result == 1
    assert "Fuzzy:" in captured.out
    assert "Causal Analysis" in captured.out
