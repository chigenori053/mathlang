"""Hint engine for MathLang Core."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .computation_engine import ComputationEngine
from .exercise_spec import ExerciseSpec
from .errors import InvalidExprError, EvaluationError


@dataclass
class HintResult:
    """
    Result of generating a hint for a user's answer.
    
    Attributes:
        message: The hint message to display to the user
        hint_type: Type of hint generated (e.g., "pattern_match", "heuristic", "none")
        details: Additional details about the hint generation
    """
    
    message: str
    hint_type: str
    details: Dict[str, Any] = field(default_factory=dict)


class HintEngine:
    """
    Generates hints based on incorrect answer patterns or symbolic differences.
    
    The HintEngine analyzes user answers against the target expression and
    defined hint rules to provide helpful feedback.
    """
    
    def __init__(self, computation_engine: ComputationEngine):
        """
        Initialize the hint engine.
        
        Args:
            computation_engine: ComputationEngine instance for symbolic operations
        """
        self.computation_engine = computation_engine
        self.symbolic_engine = computation_engine.symbolic_engine
    
    def generate_hint(self, user_expr: str, spec: ExerciseSpec) -> HintResult:
        """
        Generate a hint for a user's answer.
        
        Args:
            user_expr: The user's answer expression
            spec: Exercise specification defining target and hint rules
            
        Returns:
            HintResult containing the hint message and metadata
        """
        # 1. Validate expression first
        try:
            self.symbolic_engine.to_internal(user_expr)
        except InvalidExprError:
            return HintResult(
                message="Your expression contains syntax errors.",
                hint_type="syntax_error"
            )
            
        # 2. Check for Pattern Matching (hint_rules)
        if spec.hint_rules:
            for pattern, hint_msg in spec.hint_rules.items():
                try:
                    if self.symbolic_engine.is_equiv(user_expr, pattern):
                        return HintResult(
                            message=hint_msg,
                            hint_type="pattern_match",
                            details={"pattern": pattern}
                        )
                except (InvalidExprError, EvaluationError):
                    continue

        # 3. Heuristics
        
        # 3a. Sign Error (user == -target)
        try:
            neg_target = f"-({spec.target_expression})"
            if self.symbolic_engine.is_equiv(user_expr, neg_target):
                return HintResult(
                    message="It looks like you might have a sign error. Check your positives and negatives.",
                    hint_type="heuristic_sign_error"
                )
        except (InvalidExprError, EvaluationError):
            pass
            
        # 3b. Constant Offset (user - target == constant)
        # This requires subtracting and checking if the result is a number
        try:
            # We can check if simplify(user - target) is a number
            diff_expr = f"({user_expr}) - ({spec.target_expression})"
            simplified_diff = self.symbolic_engine.simplify(diff_expr)
            
            # Check if simplified_diff is a number (not containing variables)
            # A simple heuristic is checking if it converts to a float, 
            # but we need to be careful about symbols.
            # Let's try to evaluate it with empty context if possible, or check if it's numeric.
            
            # If we have SymPy, we can check is_number or similar, but here we rely on string output
            # or numeric_eval.
            
            # If it's a number, numeric_eval should succeed with empty context (if no vars left)
            # But if variables are left, it might fail or return symbolic.
            
            # Let's try numeric_eval. If it returns a number, then it's a constant offset.
            # Note: numeric_eval might fail if variables are present and not bound.
            # So if it succeeds, it's likely a constant.
            
            try:
                # We need to handle the case where variables are present in the original exprs
                # but cancel out in the difference.
                # numeric_eval with empty context might fail if variables are still there.
                # But if they cancelled out, it should work.
                
                # However, SymbolicEngine.evaluate might raise error if variables are missing.
                # Let's rely on the fact that simplify returns a string.
                # If the string looks like a number, it's a constant offset.
                
                # A robust way: try to convert simplified_diff to float
                float(simplified_diff)
                # If successful and not 0 (which would mean correct answer)
                if float(simplified_diff) != 0:
                     return HintResult(
                        message="You're close, but your answer differs by a constant amount.",
                        hint_type="heuristic_constant_offset",
                        details={"offset": simplified_diff}
                    )
            except ValueError:
                pass # Not a number
                
        except (InvalidExprError, EvaluationError):
            pass

        # 4. Fallback
        return HintResult(
            message="Try checking your steps carefully.",
            hint_type="none"
        )
