"""Computation Engine for MathLang Core."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .symbolic_engine import SymbolicEngine
from .errors import EvaluationError, InvalidExprError
from .ast_nodes import Node

try:
    import sympy
except ImportError:
    sympy = None


class ComputationEngine:
    """
    Provides symbolic and numeric evaluation using SymbolicEngine and SymPy.
    
    The ComputationEngine wraps the SymbolicEngine to provide a higher-level
    interface for mathematical computations, including simplification, expansion,
    factoring, and numeric evaluation.
    
    Attributes:
        symbolic_engine: The underlying SymbolicEngine instance
        variables: Dictionary of bound variables for evaluation context
    """

    def __init__(self, symbolic_engine: SymbolicEngine):
        """
        Initialize the computation engine.
        
        Args:
            symbolic_engine: SymbolicEngine instance for symbolic operations
        """
        self.symbolic_engine = symbolic_engine
        self.variables: Dict[str, Any] = {}

    def to_sympy(self, expr: str | Node) -> Any:
        """
        Converts an expression string or ASTNode to a SymPy expression.
        
        Args:
            expr: Expression string or ASTNode to convert
            
        Returns:
            SymPy expression object (or fallback AST if SymPy not available)
            
        Raises:
            NotImplementedError: If expr is an ASTNode (not yet implemented)
            InvalidExprError: If the expression is invalid
        """
        if isinstance(expr, str):
            return self.symbolic_engine.to_internal(expr)
        # If it's an ASTNode, we might need to convert it to string first or handle it
        # For now, assuming string input as primary interface
        raise NotImplementedError("ASTNode conversion not yet implemented")

    def simplify(self, expr: str) -> str:
        """
        Simplifies the given expression string.
        
        Uses SymPy's simplify function when available, otherwise attempts
        numeric evaluation for constant expressions.
        
        Args:
            expr: Expression string to simplify
            
        Returns:
            Simplified expression as a string
            
        Examples:
            >>> engine.simplify("2 + 2")
            "4"
            >>> engine.simplify("x + x")  # With SymPy
            "2*x"
        """
        return self.symbolic_engine.simplify(expr)

    def expand(self, expr: str) -> str:
        """
        Expands the given algebraic expression.
        
        Args:
            expr: Expression string to expand
            
        Returns:
            Expanded expression as a string
            
        Raises:
            InvalidExprError: If the expression is invalid
            
        Examples:
            >>> engine.expand("(x + y)**2")
            "x**2 + 2*x*y + y**2"
            >>> engine.expand("(a + b)*(c + d)")
            "a*c + a*d + b*c + b*d"
        """
        if not self.symbolic_engine.has_sympy():
            # Fallback: return expression as-is if SymPy not available
            return expr
        
        try:
            internal = self.symbolic_engine.to_internal(expr)
            if sympy is not None:
                expanded = sympy.expand(internal)
                return str(expanded)
            return expr
        except Exception as exc:
            raise InvalidExprError(f"Failed to expand expression: {exc}") from exc

    def factor(self, expr: str) -> str:
        """
        Factors the given algebraic expression.
        
        Args:
            expr: Expression string to factor
            
        Returns:
            Factored expression as a string
            
        Raises:
            InvalidExprError: If the expression is invalid
            
        Examples:
            >>> engine.factor("x**2 - y**2")
            "(x - y)*(x + y)"
            >>> engine.factor("x**2 + 2*x + 1")
            "(x + 1)**2"
        """
        if not self.symbolic_engine.has_sympy():
            # Fallback: return expression as-is if SymPy not available
            return expr
        
        try:
            internal = self.symbolic_engine.to_internal(expr)
            if sympy is not None:
                factored = sympy.factor(internal)
                return str(factored)
            return expr
        except Exception as exc:
            raise InvalidExprError(f"Failed to factor expression: {exc}") from exc

    def substitute(self, expr: str, substitutions: Dict[str, Any]) -> str:
        """
        Substitutes variables in an expression with given values.
        
        Args:
            expr: Expression string containing variables
            substitutions: Dictionary mapping variable names to values
            
        Returns:
            Expression with substitutions applied as a string
            
        Raises:
            InvalidExprError: If the expression is invalid
            
        Examples:
            >>> engine.substitute("x + y", {"x": 2, "y": 3})
            "5"
            >>> engine.substitute("a*x + b", {"x": 5})
            "5*a + b"
        """
        try:
            internal = self.symbolic_engine.to_internal(expr)
            
            if self.symbolic_engine.has_sympy() and sympy is not None:
                # Convert substitutions to SymPy symbols
                subs_dict = {}
                for name, value in substitutions.items():
                    sym = sympy.Symbol(name)
                    subs_dict[sym] = value
                
                result = internal.subs(subs_dict)
                # Simplify the result
                result = sympy.simplify(result)
                return str(result)
            else:
                # Use fallback evaluator
                try:
                    result = self.symbolic_engine.evaluate(expr, substitutions)
                    if isinstance(result, dict) and result.get("not_evaluatable"):
                        return expr
                    return str(result)
                except EvaluationError:
                    return expr
        except Exception as exc:
            raise InvalidExprError(f"Failed to substitute in expression: {exc}") from exc

    def numeric_eval(self, expr: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Evaluates the expression numerically.
        
        Combines the engine's bound variables with the provided context,
        then evaluates the expression to a numeric value.
        
        Args:
            expr: Expression string to evaluate
            context: Optional dictionary of variable values for this evaluation
            
        Returns:
            Numeric result of evaluation
            
        Raises:
            EvaluationError: If evaluation fails
            
        Examples:
            >>> engine.numeric_eval("3 * 4")
            12
            >>> engine.bind("x", 10)
            >>> engine.numeric_eval("x + 5")
            15
            >>> engine.numeric_eval("y * 2", context={"y": 3})
            6
        """
        eval_context = self.variables.copy()
        if context:
            eval_context.update(context)
        
        try:
            return self.symbolic_engine.evaluate(expr, eval_context)
        except EvaluationError:
            # If symbolic engine fails, we might want to try direct numeric evaluation if possible
            # But SymbolicEngine.evaluate already handles numeric evaluation if variables are present
            raise

    def bind(self, name: str, value: Any) -> None:
        """
        Binds a variable to a value in the engine's context.
        
        The bound variable will be available for all subsequent evaluations
        until explicitly unbound or overwritten.
        
        Args:
            name: Variable name to bind
            value: Value to bind to the variable
            
        Examples:
            >>> engine.bind("a", 100)
            >>> engine.numeric_eval("a + 10")
            110
        """
        self.variables[name] = value
