"""
UnitEngine module for handling unit conversions and dimensional analysis.
"""

from typing import Any, Optional, Dict
import sympy.physics.units as units
from sympy.physics.units.systems.si import SI
from sympy import sympify, Expr

from core.symbolic_engine import SymbolicEngine


class UnitEngine:
    """
    Engine for performing unit conversions and dimensional analysis.
    Wraps sympy.physics.units.
    """

    def __init__(self, symbolic_engine: SymbolicEngine):
        self.symbolic_engine = symbolic_engine

    def _parse_expr(self, expr: str) -> Expr:
        """Parse string expression to SymPy expression with units."""
        # We use the symbolic engine's internal conversion, but we might need
        # to ensure units are recognized. For now, we rely on sympify with
        # units module available in the namespace if needed, or just standard parsing.
        # SymPy's parse_expr might not automatically pick up units without context.
        # A safer approach for units is to use sympify with a locals dict containing units.
        
        # Construct a locals dictionary with common units
        # This is a simplified approach; in a full system we might want a more robust parser
        unit_locals = {
            name: getattr(units, name) 
            for name in dir(units) 
            if not name.startswith("_")
        }
        
        return sympify(expr, locals=unit_locals)

    def convert(self, expr: str, target_unit: str) -> str:
        """
        Convert an expression to a target unit.

        Args:
            expr: The expression to convert (e.g., "10 * meter")
            target_unit: The target unit (e.g., "centimeter")

        Returns:
            The converted expression as a string.
        """
        sym_expr = self._parse_expr(expr)
        sym_target = self._parse_expr(target_unit)
        
        converted = units.convert_to(sym_expr, sym_target)
        return str(converted)

    def simplify(self, expr: str) -> str:
        """
        Simplify a unit expression.

        Args:
            expr: The expression to simplify.

        Returns:
            The simplified expression as a string.
        """
        from sympy import simplify
        sym_expr = self._parse_expr(expr)
        simplified = simplify(sym_expr)
        return str(simplified)

    def check_consistency(self, expr: str) -> bool:
        """
        Check if the dimensions in the expression are consistent.
        For example, '1*meter + 1*second' is inconsistent.

        Args:
            expr: The expression to check.

        Returns:
            True if consistent, False otherwise.
        """
        from sympy.physics.units.util import check_dimensions
        try:
            sym_expr = self._parse_expr(expr)
            # check_dimensions raises ValueError if inconsistent
            check_dimensions(sym_expr)
            return True
        except ValueError:
            return False

    def get_si_units(self, expr: str) -> str:
        """
        Convert the expression to SI base units.

        Args:
            expr: The expression to convert.

        Returns:
            The expression in SI units.
        """
        sym_expr = self._parse_expr(expr)
        # Convert to base SI units (meter, kilogram, second, ampere, kelvin, mole, candela)
        base_units = [
            units.meter, units.kilogram, units.second, 
            units.ampere, units.kelvin, units.mole, units.candela
        ]
        converted = units.convert_to(sym_expr, base_units)
        return str(converted)
