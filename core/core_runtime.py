"""Core Runtime for MathLang."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .evaluator import Engine
from .computation_engine import ComputationEngine
from .validation_engine import ValidationEngine
from .hint_engine import HintEngine
from .exercise_spec import ExerciseSpec
from .learning_logger import LearningLogger
from .knowledge_registry import KnowledgeRegistry
from .errors import MissingProblemError, MathLangError


class CoreRuntime(Engine):
    """
    Orchestrates the execution of MathLang programs using specialized engines.
    
    Integrates:
    - ComputationEngine: For symbolic/numeric evaluation
    - ValidationEngine: For answer checking
    - HintEngine: For generating feedback
    """

    def __init__(
        self,
        computation_engine: ComputationEngine,
        validation_engine: ValidationEngine,
        hint_engine: HintEngine,
        exercise_spec: Optional[ExerciseSpec] = None,
        learning_logger: Optional[LearningLogger] = None,
        knowledge_registry: Optional[KnowledgeRegistry] = None,
    ):
        """
        Initialize the CoreRuntime.
        
        Args:
            computation_engine: Engine for computation
            validation_engine: Engine for validation
            hint_engine: Engine for hints
            exercise_spec: Optional specification for the current exercise
            learning_logger: Optional logger for learning analytics
        """
        self.computation_engine = computation_engine
        self.validation_engine = validation_engine
        self.hint_engine = hint_engine
        self.exercise_spec = exercise_spec
        self.learning_logger = learning_logger or LearningLogger()
        self.knowledge_registry = knowledge_registry
        
        self._current_expr: str | None = None
        self._context: Dict[str, Any] = {}
        self._scenarios: Dict[str, Dict[str, Any]] = {}

    def set(self, expr: str) -> None:
        """
        Set the initial problem expression.
        
        Args:
            expr: The problem expression string
        """
        self._current_expr = expr
        # Also set in computation engine if needed, though it's stateless regarding current expr
        
    def set_variable(self, name: str, value: Any) -> None:
        """
        Set a variable in the execution context.
        
        Args:
            name: Variable name
            value: Variable value
        """
        self._context[name] = value
        self.computation_engine.bind(name, value)

    def add_scenario(self, name: str, context: Dict[str, Any]) -> None:
        """
        Add a scenario with a specific context.
        
        Args:
            name: Scenario name
            context: Variable assignments for this scenario
        """
        self._scenarios[name] = context

    def evaluate(self, expr: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Evaluate an expression.
        
        Args:
            expr: Expression to evaluate
            context: Optional temporary context
            
        Returns:
            Evaluation result
        """
        return self.computation_engine.numeric_eval(expr, context)

    def check_step(self, expr: str) -> dict:
        """
        Check if a step is valid (equivalent to the previous expression).
        
        Args:
            expr: The new expression for this step
            
        Returns:
            Dictionary containing validation results and metadata
        """
        if self._current_expr is None:
            raise MissingProblemError("Problem expression must be set before steps.")
            
        before = self._current_expr
        after = expr
        
        # Default validation (symbolic)
        # Apply context if variables are bound
        if self._context:
            try:
                before_eval = self.computation_engine.substitute(before, self._context)
                after_eval = self.computation_engine.substitute(after, self._context)
            except Exception:
                before_eval = before
                after_eval = after
        else:
            before_eval = before
            after_eval = after
        
        is_valid_symbolic = self.computation_engine.symbolic_engine.is_equiv(before_eval, after_eval)
        
        # Scenario validation
        scenario_results = {}
        is_valid_scenarios = True
        if self._scenarios:
            scenario_results = self.computation_engine.check_equivalence_in_scenarios(
                before, after, self._scenarios
            )
            is_valid_scenarios = all(scenario_results.values())
        
        # Combine results
        # If scenarios are present, they override symbolic check if symbolic check is ambiguous?
        # Or should we require BOTH?
        # Usually symbolic implies numeric, but numeric doesn't imply symbolic.
        # However, if scenarios are explicitly defined, the user likely wants to verify against them.
        # Let's say: valid if symbolic is valid OR (scenarios exist AND all scenarios are valid)
        # Actually, if symbolic is valid, it should be valid everywhere.
        # If symbolic fails (e.g. too complex), scenarios might pass.
        # If scenarios fail, symbolic should definitely fail (unless scenarios are wrong).
        
        is_valid = is_valid_symbolic
        if not is_valid and self._scenarios:
            is_valid = is_valid_scenarios
        
        # If scenarios exist but some fail, it's definitely invalid even if symbolic says yes?
        # No, symbolic is ground truth. If symbolic says yes, it's yes.
        # But if symbolic says "I don't know" (which is_equiv might not do, it returns bool),
        # we rely on scenarios.
        # For now, let's trust symbolic if True. If False, check scenarios.
        
        result = {
            "before": before,
            "after": after,
            "valid": is_valid,
            "rule_id": None,
            "details": {},
        }

        if is_valid and self.knowledge_registry:
            rule_node = self.knowledge_registry.match(before, after)
            if rule_node:
                result["rule_id"] = rule_node.id
                result["details"]["rule"] = rule_node.to_metadata()
        
        if self._scenarios:
            result["details"]["scenarios"] = scenario_results
        
        if is_valid:
            self._current_expr = after
        else:
            # Generate hint if invalid
            # Use the previous expression as the target for the hint
            hint = self.hint_engine.generate_hint(after, before)
            result["details"]["hint"] = {
                "message": hint.message,
                "type": hint.hint_type
            }
                
        return result

    def finalize(self, expr: str | None) -> dict:
        """
        Finalize the problem and validate the answer.
        
        Args:
            expr: The final answer expression (or None to use current)
            
        Returns:
            Dictionary containing validation results
        """
        if self._current_expr is None:
            raise MissingProblemError("Cannot finalize before a problem is declared.")
            
        final_expr = expr if expr is not None else self._current_expr
        
        # If we have an exercise spec, use ValidationEngine
        if self.exercise_spec:
            validation_result = self.validation_engine.check_answer(
                final_expr, self.exercise_spec
            )
            
            result = {
                "before": self._current_expr,
                "after": final_expr,
                "valid": validation_result.is_correct,
                "rule_id": None,
                "details": {
                    "message": validation_result.message,
                    "validation_details": validation_result.details
                }
            }
            
            # If incorrect, generate hint
            if not validation_result.is_correct:
                hint = self.hint_engine.generate_hint_for_spec(final_expr, self.exercise_spec)
                result["details"]["hint"] = {
                    "message": hint.message,
                    "type": hint.hint_type
                }
                
            return result
            
        else:
            # Fallback to simple equivalence check if no spec
            # This behaves like the old SymbolicEvaluationEngine
            # But wait, what is the target? 
            # In finalize(expr), 'expr' is the user's final answer.
            # But usually finalize checks against a target.
            # In the old engine, finalize(expr) checked if current_expr == expr (if expr provided)
            # OR it just returned the current state.
            
            # Let's look at Evaluator logic.
            # Evaluator calls finalize(node.expr).
            # If node.expr is provided (e.g. "End: x = 5"), it checks if current state matches it.
            # If node.expr is NOT provided (e.g. "End: done"), it assumes current state is final.
            
            # Without ExerciseSpec, we can only check if the provided expr is equivalent to current state
            if expr is not None:
                is_valid = self.computation_engine.symbolic_engine.is_equiv(self._current_expr, expr)
                return {
                    "before": self._current_expr,
                    "after": expr,
                    "valid": is_valid,
                    "rule_id": None,
                    "details": {}
                }
            else:
                return {
                    "before": self._current_expr,
                    "after": self._current_expr,
                    "valid": True,
                    "rule_id": None,
                    "details": {}
                }
