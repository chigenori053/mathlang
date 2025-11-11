import re
import subprocess
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_mathlang_cli(script_path: str, *args: str) -> str:
    """MathLangのCLIを実行し、標準出力を返すヘルパー関数"""
    command = [sys.executable, str(PROJECT_ROOT / "main.py"), script_path, *args]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    return result.stdout


@pytest.fixture
def example_file_path():
    return str(PROJECT_ROOT / "examples" / "polynomial_arithmetic.mlang")


def test_polynomial_scenario_symbolic_evaluation(example_file_path):
    """PolynomialEvaluatorが正しい多項式を生成することをテスト"""
    stdout = run_mathlang_cli(example_file_path, "--polynomial", "--language", "en")

    end_results = []
    for line in stdout.splitlines():
        if "[end]" in line and "→" in line:
            after_arrow = line.split("→", 1)[1]
            polynomial = after_arrow.split("(")[0].strip()
            end_results.append(polynomial)

    expected_polynomials = [
        "2*x + 3",
        "x^2 + 2*x",
        "x^2 - y^2",
        "x*y",
    ]

    assert len(end_results) == len(expected_polynomials)

    for actual, expected in zip(end_results, expected_polynomials):
        actual_norm = "".join(sorted(actual.replace(" ", "")))
        expected_norm = "".join(sorted(expected.replace(" ", "")))
        assert actual_norm == expected_norm, f"Expected '{expected}' but got '{actual}'"


def test_evaluator_symbolic_trace():
    """Evaluatorのシンボリックトレース機能をテスト"""
    source = """
result = 1 + 2
show result
    """
    temp_file = PROJECT_ROOT / "examples" / "temp_symbolic_test.mlang"
    temp_file.write_text(source, encoding="utf-8")

    stdout = run_mathlang_cli(str(temp_file), "--symbolic-trace")

    try:
        import sympy  # type: ignore
    except ImportError:
        assert "[シンボリック無効]" in stdout
    else:
        assert "シンボリック: 3" in stdout
