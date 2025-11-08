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
Step 1: a = 2
Step 2: b = 3
Step 3: c = a^2 + b^2 → 13
Output: 13
```

## CLI Usage
- Run a `.mlang` file: `python main.py examples/pythagorean.mlang`
- Run an inline snippet: `python main.py -c "a = 2\nb = 3\nshow a + b"`
- For hands-on demos, execute `python examples/run_example.py` to replay the bundled program under `examples/`.
- Run a symbolic check (requires SymPy): `python main.py --symbolic "(a + b)^2 - (a^2 + 2ab + b^2)"`
- Enable symbolic traces during program execution: `python main.py --symbolic-trace examples/pythagorean.mlang`
- Run the built-in Hello World self-test: `python main.py --hello-world-test`

The CLI prints each evaluator step plus the final `Output` marker, and symbolic mode reports simplified forms, explanations, and tree structures for the provided expression.

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
uv add sympy lark-parser jupyter pytest
```

## Contribution Basics
- Branching: `main` (stable), `dev`, `feature/*`
- Commits: `feat(parser): implement expression parsing`
- Tests: run `pytest` before PRs
- Documentation: update both `README.md` and `MathLang_SPECIFICATION.md` when altering scope or design.

### Release Checklist (Snapshot)
- [ ] Parser/Evaluator tests green (`pytest`).
- [ ] CLI usage in `README` matches `main.py` behavior for both files and `--code` snippets.
- [ ] Examples under `examples/` execute without modification (try `python examples/run_example.py`).
- [ ] `--symbolic` flag works (prints simplify/explain output) or README/Spec are updated if the behavior changes.
- [ ] `--symbolic-trace` flag prints symbolic/explanation/structure sections for `show` 出力（SymPy 導入済み環境）。
- [ ] `--hello-world-test` prints the expected Hello World step/output trace.
- [ ] Specification updated for any CLI or directory layout changes.

For coordination guidelines, see `Agent.md`.
