#!/bin/bash
# Install MathLang's dependencies for Claude Code on the web sessions.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-$(dirname "$0")/../..}"

if command -v uv >/dev/null 2>&1; then
  # Runtime + all extras + pytest into .venv (dev group is synced by default).
  uv sync
else
  python3 -m venv .venv
  .venv/bin/pip install -q -e ".[all]" pytest
fi

# Make `mathlang` and `pytest` available without `uv run`.
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo "export PATH=\"$PWD/.venv/bin:\$PATH\"" >> "$CLAUDE_ENV_FILE"
fi
