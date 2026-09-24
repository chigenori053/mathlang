# MathLang — guide for coding agents

MathLang is a DSL and toolkit for evaluating math expressions and verifying
step-by-step derivations (SymPy-based). This file is read by Codex and, via
`CLAUDE.md`, by Claude Code. `Agent.md` is a separate review persona.

## Setup

- Python 3.11+. Development default: `uv sync` (runtime + all extras + pytest).
- Without uv: `pip install -e ".[all]" pytest`. The CLI alone needs only `pip install .`.
- Codex cloud: put the pip line above in the environment's setup script; the agent
  phase may have no network, so install everything during setup.
- Claude Code on the web: `.claude/hooks/session-start.sh` runs `uv sync` and puts
  `.venv/bin` on `PATH` automatically.

## Tests

```bash
uv run pytest                                   # or: python -m pytest
uv run pytest tests/test_mathlang_cli.py -q     # one file
```

There is no linter configured.

## Use MathLang as your math tool

When a task needs exact arithmetic, algebra, or checking a derivation, run the
CLI instead of computing by hand. Use `--json` and read the exit status
(0 ok, 1 failure / not equivalent / unverified step, 2 usage error).
The command is `mathlang` (or `uv run mathlang` / `python -m mathlang`).

```bash
mathlang eval "sqrt(2)/2 + x" -v x=1/3 --json   # {"result": {"exact": ..., "numeric": ...}}
mathlang simplify "sin(x)^2 + cos(x)^2" --json
mathlang expand "(x + 1)^3" --json
mathlang factor "x^2 - 1" --json
mathlang subs "a*x + b" -v x=5 --json
mathlang equiv "(x + 1)^2" "x^2 + 2*x + 1" --json
mathlang convert "90*minute" hour --json
```

To verify a derivation step by step, write it as a program and pipe it in; the
JSON has `verified`, `mistake_count`, per-step `records` and a `causal` report.

```bash
mathlang run - --json <<'EOF'
problem: (3 + 5) * 4
step: 8 * 4
end: 32
EOF
```

Expressions use Python/SymPy syntax (`^` also means power): `*` is required
for multiplication (`2*x`, not `2x`), and only whitelisted math functions such
as `sqrt`, `sin`, `log`, `factorial`, `integrate` may be called.

## Code layout

| Path | Role |
|---|---|
| `mathlang/api.py` | UI-independent API; every front end (CLI, web UI, future MCP server) calls this |
| `mathlang/cli.py`, `mathlang/repl.py` | The `mathlang` command and its REPL |
| `core/` | Parser, evaluators and engines (symbolic, validation, hints, units, causal) |
| `core/safe_parse.py` | Whitelisted string → SymPy conversion |
| `webapp/`, `tools/lsp/` | Streamlit UI and LSP server (`web` / `lsp` extras) |
| `edu/`, `pro/`, `demo/`, `main.py` | Legacy CLIs |
| `tests/` | pytest suite |

## Rules

- Never pass user-supplied strings to `sympy.sympify` / `parse_expr` directly;
  go through `core.safe_parse.safe_sympify` (sympify uses `eval`).
- Add new capabilities to `mathlang.api` first, then expose them in the CLI.
- Keep runtime dependencies to sympy + PyYAML; UI-only packages belong in extras.
