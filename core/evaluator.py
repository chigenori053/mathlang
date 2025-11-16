"""Evaluator and engine implementations for MathLang Core."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from . import ast_nodes as ast
from .errors import InconsistentEndError, InvalidStepError, MissingProblemError
from .learning_logger import LearningLogger
from .symbolic_engine import SymbolicEngine
from .knowledge_registry import KnowledgeRegistry
from .fuzzy.judge import FuzzyJudge
from .fuzzy.types import NormalizedExpr


class Engine:
    """Abstract engine interface."""

    def set(self, expr: str) -> None:  # pragma: no cover - documentation guard
        raise NotImplementedError

    def check_step(self, expr: str) -> dict:  # pragma: no cover - documentation guard
        raise NotImplementedError

    def finalize(self, expr: str | None) -> dict:  # pragma: no cover - documentation guard
        raise NotImplementedError


@dataclass
class SymbolicEvaluationEngine(Engine):
    """Concrete engine that relies on SymbolicEngine and KnowledgeRegistry."""

    symbolic_engine: SymbolicEngine
    knowledge_registry: KnowledgeRegistry | None = None

    def __post_init__(self) -> None:
        self._current_expr: str | None = None

    def set(self, expr: str) -> None:
        self._current_expr = expr

    def check_step(self, expr: str) -> dict:
        if self._current_expr is None:
            raise MissingProblemError("Problem expression must be set before steps.")
        before = self._current_expr
        valid = self.symbolic_engine.is_equiv(before, expr)
        rule_id: str | None = None
        if valid and self.knowledge_registry is not None:
            matched = self.knowledge_registry.match(before, expr)
            rule_id = matched.id if matched else None
        details = {"explanation": self.symbolic_engine.explain(before, expr)}
        result = {
            "before": before,
            "after": expr,
            "valid": valid,
            "rule_id": rule_id,
            "details": details,
        }
        if valid:
            self._current_expr = expr
        return result

    def finalize(self, expr: str | None) -> dict:
        if self._current_expr is None:
            raise MissingProblemError("Cannot finalize before a problem is declared.")
        target = expr if expr is not None else self._current_expr
        valid = self.symbolic_engine.is_equiv(self._current_expr, target)
        details = {"explanation": self.symbolic_engine.explain(self._current_expr, target)}
        return {
            "before": self._current_expr,
            "after": target,
            "valid": valid,
            "rule_id": None,
            "details": details,
        }


class Evaluator:
    """Process a ProgramNode using the specified engine."""

    def __init__(
        self,
        program: ast.ProgramNode,
        engine: Engine,
        learning_logger: LearningLogger | None = None,
        fuzzy_judge: FuzzyJudge | None = None,
    ) -> None:
        self.program = program
        self.engine = engine
        self.learning_logger = learning_logger or LearningLogger()
        self._fuzzy_judge = fuzzy_judge
        self._state = "INIT"
        self._completed = False
        self._current_problem_expr: str | None = None
        self._last_expr_raw: str | None = None

    def run(self) -> List[dict]:
        for node in self.program.body:
            if isinstance(node, ast.ProblemNode):
                self._handle_problem(node)
            elif isinstance(node, ast.StepNode):
                self._handle_step(node)
            elif isinstance(node, ast.EndNode):
                self._handle_end(node)
            elif isinstance(node, ast.ExplainNode):
                self._handle_explain(node)
            else:  # pragma: no cover - defensive block.
                raise SyntaxError(f"Unsupported node type: {type(node)}")
        if self._state != "END":
            raise MissingProblemError("Program did not reach an end statement.")
        self._completed = True
        return self.learning_logger.to_list()

    def _handle_problem(self, node: ast.ProblemNode) -> None:
        if self._state != "INIT":
            raise MissingProblemError("Problem already defined.")
        self.engine.set(node.expr)
        self._current_problem_expr = node.expr
        self._last_expr_raw = node.expr
        self.learning_logger.record(
            phase="problem",
            expression=node.expr,
            rendered=f"Problem: {node.expr}",
            status="ok",
        )
        self._state = "PROBLEM_SET"

    def _handle_step(self, node: ast.StepNode) -> None:
        if self._state not in {"PROBLEM_SET", "STEP_RUN"}:
            raise MissingProblemError("step declared before problem.")
        result = self.engine.check_step(node.expr)
        status = "ok" if result["valid"] else "invalid_step"
        self.learning_logger.record(
            phase="step",
            expression=node.expr,
            rendered=f"Step ({node.step_id or 'unnamed'}): {node.expr}",
            status=status,
            rule_id=result.get("rule_id"),
            meta=result.get("details", {}),
        )
        if result["valid"]:
            self._last_expr_raw = node.expr
            self._state = "STEP_RUN"
            return

        self._run_fuzzy_judge(
            previous_expr=self._last_expr_raw or "",
            candidate_expr=node.expr,
            applied_rule_id=result.get("rule_id"),
        )
        self._log_error(
            rendered="InvalidStepError",
            status="invalid_step",
            expression=node.expr,
            meta={
                "details": result.get("details", {}),
                "step_id": node.step_id,
            },
        )
        raise InvalidStepError(f"Step is not equivalent: {node.expr}")

    def _handle_end(self, node: ast.EndNode) -> None:
        if self._state not in {"PROBLEM_SET", "STEP_RUN"}:
            raise MissingProblemError("end declared before problem.")
        result = self.engine.finalize(node.expr)
        if not result["valid"]:
            self._log_error(
                rendered="InconsistentEndError",
                status="inconsistent_end",
                expression=node.expr,
                meta=result.get("details", {}),
            )
            raise InconsistentEndError("Final expression does not match expected result.")
        rendered = "End: done" if node.is_done else f"End: {node.expr}"
        self.learning_logger.record(
            phase="end",
            expression=node.expr if not node.is_done else None,
            rendered=rendered,
            status="ok",
            meta=result.get("details", {}),
        )
        self._state = "END"
        self._last_expr_raw = node.expr if not node.is_done else self._last_expr_raw

    def _handle_explain(self, node: ast.ExplainNode) -> None:
        if self._state == "INIT":
            raise MissingProblemError("Explain cannot appear before problem.")
        self.learning_logger.record(
            phase="explain",
            expression=None,
            rendered=node.text,
            status="ok",
        )

    def _run_fuzzy_judge(
        self,
        *,
        previous_expr: str,
        candidate_expr: str,
        applied_rule_id: str | None,
    ) -> None:
        if self._fuzzy_judge is None or self._current_problem_expr is None:
            return
        normalized_problem = self._normalized_expr(self._current_problem_expr)
        normalized_prev = self._normalized_expr(previous_expr)
        normalized_candidate = self._normalized_expr(candidate_expr)
        fuzzy_result = self._fuzzy_judge.judge_step(
            problem_expr=normalized_problem,
            previous_expr=normalized_prev,
            candidate_expr=normalized_candidate,
            applied_rule_id=applied_rule_id,
            candidate_rule_id=None,
            explain_text=None,
        )
        self.learning_logger.record(
            phase="fuzzy",
            expression=candidate_expr,
            rendered=f"Fuzzy: {fuzzy_result['label'].value} ({fuzzy_result['score']['combined_score']:.2f})",
            status="info",
            meta=fuzzy_result,
        )

    def _normalized_expr(self, expr: str) -> NormalizedExpr:
        tokens = expr.split()
        return {"raw": expr, "sympy": expr, "tokens": tokens}

    def _log_error(
        self,
        *,
        rendered: str,
        status: str,
        expression: str | None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.learning_logger.record(
            phase="error",
            expression=expression,
            rendered=rendered,
            status=status,
            meta=meta or {},
        )
