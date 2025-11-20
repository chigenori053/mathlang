import pytest
from core.core_runtime import CoreRuntime
from core.computation_engine import ComputationEngine
from core.validation_engine import ValidationEngine
from core.hint_engine import HintEngine
from core.symbolic_engine import SymbolicEngine
from core.exercise_spec import ExerciseSpec
from core.errors import MissingProblemError

@pytest.fixture
def runtime():
    symbolic = SymbolicEngine()
    computation = ComputationEngine(symbolic)
    validation = ValidationEngine(computation)
    hint = HintEngine(computation)
    
    return CoreRuntime(computation, validation, hint)

def test_set_problem(runtime):
    runtime.set("x + 1")
    assert runtime._current_expr == "x + 1"

def test_check_step_valid(runtime):
    runtime.set("x + x")
    result = runtime.check_step("2*x")
    assert result["valid"] is True
    assert runtime._current_expr == "2*x"

def test_check_step_invalid(runtime):
    runtime.set("x + x")
    result = runtime.check_step("3*x")
    assert result["valid"] is False
    assert runtime._current_expr == "x + x"  # Should not update

def test_check_step_missing_problem(runtime):
    with pytest.raises(MissingProblemError):
        runtime.check_step("x")

def test_finalize_without_spec(runtime):
    runtime.set("x + 1")
    # Check against equivalent expression
    result = runtime.finalize("1 + x")
    assert result["valid"] is True
    
    # Check against non-equivalent
    result = runtime.finalize("x + 2")
    assert result["valid"] is False

def test_finalize_with_spec_correct(runtime):
    spec = ExerciseSpec(
        id="test1",
        target_expression="2*x",
        validation_mode="symbolic_equiv"
    )
    runtime.exercise_spec = spec
    runtime.set("x + x")
    
    result = runtime.finalize("2*x")
    assert result["valid"] is True
    assert "Correct!" in result["details"]["message"]

def test_finalize_with_spec_incorrect_with_hint(runtime):
    spec = ExerciseSpec(
        id="test2",
        target_expression="x**2",
        hint_rules={"2*x": "You differentiated instead of squaring."}
    )
    runtime.exercise_spec = spec
    runtime.set("x**2") # Initial state doesn't matter much for finalize check against spec
    
    # User answers 2*x
    result = runtime.finalize("2*x")
    assert result["valid"] is False
    assert "hint" in result["details"]
    assert result["details"]["hint"]["message"] == "You differentiated instead of squaring."

def test_variable_binding(runtime):
    runtime.set_variable("a", 10)
    assert runtime.evaluate("a + 5") == 15
    
    # Check if binding affects step checking (it should if variables are used)
    runtime.set("a + x")
    result = runtime.check_step("10 + x")
    assert result["valid"] is True
