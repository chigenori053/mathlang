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
Step 1: a = 2
Step 2: b = 3
Step 3: c = a^2 + b^2 → 13
Output: 13
```

## Roadmap (Draft)
1. **Phase 1** – Parser/Evaluator foundation (target: mid Nov 2025)
2. **Phase 2** – SymbolicAI integration & AST optimization (early Dec 2025)
3. **Phase 3** – Jupyter UI + learning logs (late Dec 2025)
4. **Phase 4** – Educational beta release v0.9 (Jan 2026)

## Environment Setup (macOS)
```bash
uv init
uv python install 3.12
uv venv
uv add sympy lark-parser jupyter pytest
```

## Contribution Basics
- Branching: `main` (stable), `dev`, `feature/*`
- Commits: `feat(parser): implement expression parsing`
- Tests: run `pytest` before PRs
- Documentation: update both `README.md` and `MathLang_SPECIFICATION.md` when altering scope or design.

For coordination guidelines, see `Agent.md`.
