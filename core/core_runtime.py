"""Core Runtime for MathLang."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .evaluator import Engine
from .computation_engine import ComputationEngine
from .validation_engine import ValidationEngine
from .hint_engine import HintEngine
from .exercise_spec import ExerciseSpec
from .learning_logger import LearningLogger
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
        
        self._current_expr: str | None = None
        self._context: Dict[str, Any] = {}

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
        
        # Apply context if variables are bound
        if self._context:
            # Use computation engine to substitute variables
            # We catch errors in case substitution fails (e.g. partial)
            try:
                before_eval = self.computation_engine.substitute(before, self._context)
                after_eval = self.computation_engine.substitute(after, self._context)
            except Exception:
                # Fallback to original if substitution fails
                before_eval = before
                after_eval = after
        else:
            before_eval = before
            after_eval = after
        
        # check equivalence using computation engine
        # We use simplify/is_equiv from symbolic engine via computation engine
        # But ComputationEngine doesn't expose is_equiv directly, let's use symbolic_engine
        is_valid = self.computation_engine.symbolic_engine.is_equiv(before_eval, after_eval)
        
        result = {
            "before": before,
            "after": after,
            "valid": is_valid,
            "rule_id": None, # Could be enhanced with rule detection later
            "details": {},
        }
        
        if is_valid:
            self._current_expr = after
        else:
            # Generate hint if invalid
            if self.exercise_spec:
                # For intermediate steps, we might want to hint based on the *previous* expression
                # or just generic "not equivalent"
                # The HintEngine is designed for final answers vs target, but can be adapted
                # For now, we'll leave step-level hinting simple or future work
                pass
                
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
                hint = self.hint_engine.generate_hint(final_expr, self.exercise_spec)
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
