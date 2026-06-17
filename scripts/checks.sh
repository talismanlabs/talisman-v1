#!/usr/bin/env bash
# Authoritative deterministic-check gate for TalisMan.
#
# Runs the four mandated checks (ruff, ruff-format, mypy, pytest, lint-imports) in
# the order the architecture guardrails require. This single script is the source
# of truth used by humans, the slice-runner harness, and CI — so "what CI runs" and
# "what I can run locally" are guaranteed identical.
#
# Usage: ./scripts/checks.sh         (run from the repo root)
set -euo pipefail

cd "$(dirname "$0")/.."

# Prefer the project virtualenv if present, so the script works whether or not the
# venv is activated.
BIN=""
if [ -x ".venv/bin/ruff" ]; then
  BIN=".venv/bin/"
fi

echo "== ruff check =="
"${BIN}ruff" check .

echo "== ruff format --check =="
"${BIN}ruff" format --check .

echo "== mypy (strict) =="
"${BIN}mypy" src/talisman_core

echo "== pytest =="
"${BIN}pytest"

echo "== lint-imports (architecture boundaries) =="
# Import Linter must import the root package; src-layout needs it on PYTHONPATH.
PYTHONPATH="src:${PYTHONPATH:-}" "${BIN}lint-imports"

echo ""
echo "ALL DETERMINISTIC CHECKS PASSED"
