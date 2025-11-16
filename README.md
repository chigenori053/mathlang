# MathLang

MathLang (Mathematical Thinking Language) is a DSL and tooling suite that captures stepwise mathematical reasoning so learners and AI systems can inspect, replay, and refine thought processes.

## Why MathLang?
- **Process-first**: emphasizes intermediate working steps over final answers.
- **AI-assisted**: pairs human reasoning with SymbolicAI for explanation and transformation of expressions.
- **Reproducible**: identical inputs always re-create the same execution trace.
- **Lightweight**: Python 3.12 stack with modular components for education and research.

## Architecture Snapshot
| Layer | Key Modules | Purpose |
|-------|-------------|---------|
| DSL Core | `core/parser.py`, `core/ast_nodes.py` | Parse MathLang syntax into AST structures. |
| Execution | `core/evaluator.py` | Replay reasoning steps and emit annotated outputs. |
| Polynomial | `core/polynomial.py`, `core/polynomial_evaluator.py` | Evaluate multivariate polynomials via algebraic laws. |
| Optimization | `core/optimizer.py` | Inline assignments and fold constants to streamline traces. |
| SymbolicAI | `core/symbolic_engine.py` | Simplify expressions and generate explanations via SymPy/custom logic. |
| Interfaces | JupyterLab / Streamlit | Provide interactive teaching and demo surfaces. |
| Testing | `pytest` suites under `tests/` | Guard parser/evaluator semantics. |

Reference structure and full requirements live in `MathLang_SPECIFICATION.md`.

## DSL Glimpse
```text
# Stepwise computation
a = 2
b = 3
c = a^2 + b^2
show c
```
Expected output:
```
ステップ 1: a = 2
ステップ 2: b = 3
ステップ 3: c = a^2 + b^2 → 13
出力: 13
```

## CLI Usage
- Run a `.mlang` file: `python main.py --file edu/examples/pythagorean.mlang`
- Run an inline snippet: `python main.py -c "problem: 1 + 1\nend: 2"`
- Switch to the polynomial evaluator: `python main.py --mode polynomial --file edu/examples/polynomial_arithmetic.mlang`
- Run the built-in Hello World self-test: `python main.py --hello-world-test`
- Simulate a counterfactual: `python main.py --file edu/examples/counterfactual_demo.mlang --counterfactual '{"phase": "step", "index": 2, "expression": "8 * 4"}'`
- Run the Edu demo runner: `python -m edu.demo.edu_demo_runner basic_arithmetic`
- Run the Pro CLI: `python -m pro.cli -c "problem: (x + 1) * (x + 2)\nend: (x + 1) * (x + 2)"`
- Run the Pro demo runner: `python -m pro.demo_runner counterfactual`

The CLI prints rendered text for every `problem`, `step`, `explain`, and `end` clause. Symbolic mode verifies steps with SymPy and the knowledge registry, while polynomial mode expands expressions before comparing them.  
エラーが発生した場合は、収集した LearningLogger レコードを元に因果推論エンジンが解析され、`== Causal Analysis ==` セクションとして推定原因と修正候補ステップが追加表示されます。

## Pro Edition
プロフェッショナル向け CLI / デモについては `README_PRO.md` を参照。`python -m pro.cli ...` で直接呼び出せます。

## Learning Logs & Notebook Demo
MathLang now ships with a lightweight `LearningLogger` that records `problem → step → end` events (including rule IDs supplied by the knowledge base) as JSON. You can pass the logger into an evaluator:

```python
from pathlib import Path

from core.learning_logger import LearningLogger
from core.parser import Parser
from core.evaluator import Evaluator, SymbolicEvaluationEngine
from core.symbolic_engine import SymbolicEngine
from core.knowledge_registry import KnowledgeRegistry

source = \"\"\"problem: (2 + 3) * 4
step: 5 * 4
end: 20\"\"\"

logger = LearningLogger()
program = Parser(source).parse()
symbolic_engine = SymbolicEngine()
registry = KnowledgeRegistry(Path("core/knowledge"), symbolic_engine)
engine = SymbolicEvaluationEngine(symbolic_engine, registry)
Evaluator(program, engine=engine, learning_logger=logger).run()
print(logger.to_list())
```

An executable walkthrough lives in `notebooks/Learning_Log_Demo.ipynb`, which illustrates how to import the repo modules inside Jupyter and display the collected JSON using `IPython.display.JSON`.

## Causal Analysis in Notebooks
Notebook から因果推論を呼び出す場合は、LearningLogger の記録を `core.causal.integration.run_causal_analysis` に渡すだけです。

```python
from core.causal.integration import run_causal_analysis
from core.causal.graph_utils import graph_to_text

records = logger.to_list()
engine, report = run_causal_analysis(records, include_graph=True)
report["explanations"]  # 各エラーの原因サマリ

# 修正候補（例: step ノードID）
for error_id in report["errors"]:
    fix_nodes = engine.suggest_fix_candidates(error_id)
    print(error_id, [node.node_id for node in fix_nodes])

# グラフの簡易表示
print(graph_to_text(report["graph"]))
```

`report["graph"]` にはノード・エッジ情報が入るため、テキスト可視化に加えて Graphviz/DOT ツールへもそのまま渡せます（`core.causal.graph_utils.graph_to_dot` 参照）。

## Roadmap (Draft)
1. **Phase 1** – Parser/Evaluator foundation (target: mid Nov 2025)
2. **Phase 2** – SymbolicAI integration & AST optimization (early Dec 2025)
3. **Phase 3** – Jupyter UI + learning logs (late Dec 2025)
4. **Phase 4** – Educational beta release v0.9 (Jan 2026)

## Environment Setup (macOS)
```bash
uv init
uv python install 3.12
uv python pin 3.12
uv venv
uv add sympy pyyaml pytest
```

## Contribution Basics
- Branching: `main` (stable), `dev`, `feature/*`
- Commits: `feat(parser): implement expression parsing`
- Tests: run `pytest` before PRs
- Documentation: update both `README.md` and `MathLang_SPECIFICATION.md` when altering scope or design.

### Release Checklist (Snapshot)
- [ ] Parser/Evaluator tests green (`pytest`).
- [ ] CLI usage in `README` matches `main.py` behavior for `--file`, `--code`, `--mode`, and `--hello-world-test`.
- [ ] Examples under `edu/examples/` (Edu) and `pro/examples/` (Pro) execute without modification.
- [ ] Symbolic mode verifies steps and prints rendered output.
- [ ] Polynomial mode expands polynomials and reports matching steps.
- [ ] `--hello-world-test` prints the expected Hello World trace.
- [ ] Specification updated for any CLI or directory layout changes.

For coordination guidelines, see `Agent.md`.
