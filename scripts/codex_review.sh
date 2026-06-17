#!/usr/bin/env bash
# Cross-family review wrapper: drive Codex CLI (headless) to review a Claude-led
# slice and emit the YAML review artifact required by docs/reviews/README.md.
#
# Usage:
#   scripts/codex_review.sh <slice-id> [base-ref]
# Example:
#   scripts/codex_review.sh S02.01 main
#
# The exact Codex invocation is intentionally overridable, because the Codex CLI
# flags are finalized during Stage A verification (after the user installs Codex):
#   CODEX_REVIEW_CMD='codex exec --sandbox read-only -'   # reads prompt from stdin
# Defaults to `codex exec` reading the prompt from stdin.
set -euo pipefail
cd "$(dirname "$0")/.."

SLICE_ID="${1:?usage: codex_review.sh <slice-id> [base-ref]}"
BASE_REF="${2:-main}"
OUT="docs/reviews/${SLICE_ID}.yaml"
CODEX_REVIEW_CMD="${CODEX_REVIEW_CMD:-codex exec --sandbox read-only -}"

# Fail clearly if Codex is unavailable — the cross-family guarantee depends on it.
if ! command -v codex >/dev/null 2>&1 && [ -z "${CODEX_REVIEW_CMD_OVERRIDDEN:-}" ]; then
  echo "ERROR: 'codex' not found on PATH." >&2
  echo "Install Codex CLI and set OPENAI_API_KEY (Stage A), or set CODEX_REVIEW_CMD." >&2
  echo "Per guardrail #4, a slice cannot be accepted without opposite-family review." >&2
  exit 3
fi

DIFF="$(git diff "${BASE_REF}"...HEAD 2>/dev/null || git diff "${BASE_REF}" 2>/dev/null || true)"
FILES="$(git diff --name-only "${BASE_REF}"...HEAD 2>/dev/null || git diff --name-only "${BASE_REF}" 2>/dev/null || true)"

PROMPT="$(cat <<EOF
You are Codex CLI acting as the independent CROSS-FAMILY reviewer for the TalisMan
project. The lead implementer was Claude Code. Review slice ${SLICE_ID}.

Authoritative context (read these files in the repo before judging):
- docs/architecture-guardrails.md (non-negotiable rules)
- docs/agent-coding-protocol.md (slice rules + the required review artifact format)
- docs/slice-backlog.md (this slice's acceptance criteria)
- docs/talisman-v1/ (immutable architecture reference)

Deterministic checks (ruff, ruff-format, mypy, pytest, lint-imports) have already
passed; do not re-run them — judge correctness, architecture-boundary compliance,
security, and whether the slice meets its acceptance criteria without scope creep.

Changed files:
${FILES}

Unified diff under review:
${DIFF}

Output ONLY a YAML document matching docs/reviews/REVIEW-TEMPLATE.yaml exactly
(slice_id, lead_agent, review_agent, review_status, risk_level, checks_observed,
architecture_boundary_check, security_check, findings, final_recommendation).
Set review_agent: codex_cli and lead_agent: claude_code. Do not include prose
outside the YAML.
EOF
)"

echo ">> Requesting Codex cross-family review for ${SLICE_ID} (base ${BASE_REF})..." >&2
RAW="$(printf '%s' "$PROMPT" | ${CODEX_REVIEW_CMD})"

# Strip any markdown code fences the model may add.
printf '%s\n' "$RAW" | sed -E '/^```/d' > "$OUT"
echo ">> Wrote ${OUT}" >&2
echo "$OUT"
