#!/usr/bin/env bash
# Cross-family review wrapper: drive Codex CLI (headless, read-only) to review a
# Claude-led slice and emit the YAML review artifact required by
# docs/reviews/README.md.
#
# Usage:   scripts/codex_review.sh <slice-id> [base-ref]
# Example: scripts/codex_review.sh S02.01 main
#
# Codex auth is via `codex login` (ChatGPT) or OPENAI_API_KEY. The review runs in a
# read-only sandbox so it can read the repo but cannot modify it. Only the agent's
# final message (the YAML) is captured via `-o`.
set -euo pipefail
cd "$(dirname "$0")/.."

SLICE_ID="${1:?usage: codex_review.sh <slice-id> [base-ref]}"
BASE_REF="${2:-main}"
OUT="docs/reviews/${SLICE_ID}.yaml"
SANDBOX="${CODEX_SANDBOX:-read-only}"

if ! command -v codex >/dev/null 2>&1; then
  echo "ERROR: 'codex' not found on PATH (Stage A: install Codex CLI + authenticate)." >&2
  echo "Per guardrail #4, a slice cannot be accepted without opposite-family review." >&2
  exit 3
fi

DIFF="$(git diff "${BASE_REF}...HEAD" 2>/dev/null || git diff "${BASE_REF}" 2>/dev/null || true)"
FILES="$(git diff --name-only "${BASE_REF}...HEAD" 2>/dev/null || true)"

PROMPT="$(cat <<EOF
You are Codex CLI acting as the independent CROSS-FAMILY reviewer for the TalisMan
project. The lead implementer was Claude Code. Review slice ${SLICE_ID}.

Read these files in the repo before judging:
- docs/architecture-guardrails.md (non-negotiable rules)
- docs/agent-coding-protocol.md (slice rules + required review-artifact format)
- docs/slice-backlog.md (this slice's acceptance criteria)
- docs/reviews/REVIEW-TEMPLATE.yaml (the exact output shape)

Deterministic checks (ruff, ruff-format, mypy, pytest, lint-imports) already pass;
do not re-run them. Judge: correctness, architecture-boundary compliance (Import
Linter layers), security, and whether the slice meets its acceptance criteria
without scope creep.

Changed files:
${FILES}

Unified diff under review:
${DIFF}

Output ONLY a YAML document matching docs/reviews/REVIEW-TEMPLATE.yaml exactly, with
lead_agent: claude_code and review_agent: codex_cli. Do not include any prose,
preamble, or code fences outside the YAML.
EOF
)"

TMP="$(mktemp)"
ERR="$(mktemp)"
if ! printf '%s' "$PROMPT" | codex exec --sandbox "$SANDBOX" --color never -o "$TMP" - >/dev/null 2>"$ERR"; then
  echo "ERROR: codex exec failed:" >&2
  tail -8 "$ERR" >&2
  rm -f "$TMP" "$ERR"
  exit 4
fi

# Capture only the final message; strip any stray markdown code fences.
sed -E '/^```/d' "$TMP" > "$OUT"
rm -f "$TMP" "$ERR"

if [ ! -s "$OUT" ]; then
  echo "ERROR: review artifact ${OUT} is empty — inspect the Codex run." >&2
  exit 5
fi
echo "$OUT"
