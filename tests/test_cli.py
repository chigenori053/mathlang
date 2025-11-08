import subprocess
import sys
from pathlib import Path

from core.i18n import get_language_pack
from core.symbolic_engine import SymbolicEngineError, SymbolicResult
from main import _run_symbolic_mode


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLI_ENTRY = PROJECT_ROOT / "main.py"


class DummyEngine:
    def __init__(self) -> None:
        self.simplify_calls = 0
        self.explain_calls = 0

    def simplify(self, expression: str) -> SymbolicResult:
        self.simplify_calls += 1
        return SymbolicResult(simplified=expression.replace(" ", ""), explanation="dummy explanation")

    def explain(self, expression: str) -> str:
        self.explain_calls += 1
        return f"Dummy({expression})"


def test_symbolic_mode_outputs_analysis(capsys):
    engine = DummyEngine()
    rc = _run_symbolic_mode("a + a", language=get_language_pack("ja"), engine_factory=lambda: engine)

    assert rc == 0
    captured = capsys.readouterr()
    assert "簡約結果: a+a" in captured.out
    assert "説明: dummy explanation" in captured.out
    assert "構造: Dummy(a + a)" in captured.out
    assert engine.simplify_calls == 1
    assert engine.explain_calls == 1


def test_symbolic_mode_handles_factory_error(capsys):
    rc = _run_symbolic_mode(
        "expr",
        language=get_language_pack("ja"),
        engine_factory=lambda: (_ for _ in ()).throw(SymbolicEngineError("boom")),
    )

    assert rc == 1
    captured = capsys.readouterr()
    assert "[Symbolic Error]" in captured.err


def test_cli_hello_world_self_test_runs_via_subprocess():
    result = subprocess.run(
        [sys.executable, str(CLI_ENTRY), "--hello-world-test"],
        capture_output=True,
        text=True,
        check=True,
    )

    assert "Hello World" in result.stdout
    assert "== MathLang 実行 (Hello World 自己診断) ==" in result.stdout


def test_symbolic_mode_outputs_analysis_in_english(capsys):
    engine = DummyEngine()
    rc = _run_symbolic_mode("a + a", language=get_language_pack("en"), engine_factory=lambda: engine)

    assert rc == 0
    captured = capsys.readouterr()
    assert "Simplified: a+a" in captured.out
    assert "Explanation: dummy explanation" in captured.out
    assert "Structure: Dummy(a + a)" in captured.out
    assert engine.simplify_calls == 1
    assert engine.explain_calls == 1
