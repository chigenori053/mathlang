"""Knowledge node registry and helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .. import ast_nodes as ast
from ..parser import Parser
from ..arithmetic_engine import ArithmeticEngine
from ..fraction_engine import FractionEngine

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None  # type: ignore

def _normalize_for_pattern(expression: ast.Expr) -> ast.Expr:
    """
    Normalizes an expression for pattern matching by selecting the correct engine.
    """
    def _contains_division(expr: ast.Expr) -> bool:
        if isinstance(expr, ast.Div):
            return True
        if isinstance(expr, ast.Neg):
            return _contains_division(expr.expr)
        if isinstance(expr, (ast.Add, ast.Mul)):
            children = expr.terms if isinstance(expr, ast.Add) else expr.factors
            return any(_contains_division(child) for child in children)
        if isinstance(expr, ast.Pow):
            return _contains_division(expr.base) or _contains_division(expr.exp)
        return False

    if _contains_division(expression):
        return FractionEngine().normalize(expression)
    return ArithmeticEngine().normalize(expression)

@dataclass(frozen=True)
class KnowledgeNode:
    id: str
    category: str
    title: str
    explanation: str | None
    before_src: str
    after_src: str
    before_expr: ast.Expr
    after_expr: ast.Expr


class KnowledgeRegistry:
    """Loads YAML/JSON rule files and performs structural pattern matching."""

    def __init__(self, base_path: Path | None = None):
        self.base_path = base_path or Path(__file__).resolve().parent
        self.nodes: List[KnowledgeNode] = []
        self._load_all()

    def match(self, before_expr: ast.Expr, after_expr: ast.Expr) -> Optional[KnowledgeNode]:
        # This match logic is simplistic and may need to be improved.
        # It currently relies on the normalized string representation.
        # A more robust solution would be structural matching on the AST.
        normalized_before = _normalize_for_pattern(before_expr)
        normalized_after = _normalize_for_pattern(after_expr)

        for node in self.nodes:
            # This is a placeholder for a real matching implementation
            if str(node.before_expr) == str(normalized_before) and str(node.after_expr) == str(normalized_after):
                return node
        return None

    def _load_all(self) -> None:
        for path in self._iter_rule_files():
            data = self._load_file(path)
            if not isinstance(data, list):
                continue
            for entry in data:
                node = self._register_rule(entry, path)
                if node:
                    self.nodes.append(node)

    def _load_file(self, path: Path):
        text = path.read_text(encoding="utf-8")
        suffix = path.suffix.lower()
        if suffix == ".json":
            return json.loads(text)
        if suffix in {".yml", ".yaml"}:
            if yaml is None:
                raise RuntimeError("PyYAML is required to load YAML knowledge files.")
            return yaml.safe_load(text)
        return []

    def _iter_rule_files(self) -> Iterable[Path]:
        for yml in self.base_path.rglob("*.yml"):
            yield yml
        for yaml_path in self.base_path.rglob("*.yaml"):
            yield yaml_path
        for json_path in self.base_path.rglob("*.json"):
            yield json_path

    def _register_rule(self, entry: dict, path: Path) -> KnowledgeNode | None:
        node_id = entry.get("id")
        before_src = entry.get("pattern", {}).get("before")
        after_src = entry.get("pattern", {}).get("after")
        if not node_id or not before_src or not after_src:
            return None

        before_expr = self._parse_pattern_expression(before_src)
        after_expr = self._parse_pattern_expression(after_src)

        return KnowledgeNode(
            id=node_id,
            category=entry.get("category", path.parent.name),
            title=entry.get("title", ""),
            explanation=entry.get("explanation"),
            before_src=before_src,
            after_src=after_src,
            before_expr=before_expr,
            after_expr=after_expr,
        )

    def _parse_pattern_expression(self, expr_src: str) -> ast.Expr:
        # The parser expects a full statement, so we wrap the expression
        program = Parser(expr_src).parse()
        if not program.statements or not isinstance(program.statements[0], ast.ExpressionStatement):
            raise ValueError(f"Pattern '{expr_src}' is not a valid expression.")
        
        pattern_expr = program.statements[0].expression
        return _normalize_for_pattern(pattern_expr)
