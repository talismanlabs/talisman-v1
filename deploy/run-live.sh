#!/usr/bin/env bash
# Launch a supervised live run DETACHED, with a durable log.
#
# The plain `--live-project` command runs in the foreground and dies if your SSH session
# drops. This wrapper starts it with setsid+nohup so it keeps running after you disconnect,
# and points TalisMan's structured run log at a timestamped file you can tail at any time.
#
# Two files are written under ~/talisman/logs/:
#   <project>-<ts>.log          — TalisMan's structured run log (phase started/finished, gates)
#   <project>-<ts>.console.log  — the process's raw stdout/stderr (catches early crashes)
#
# Usage: deploy/run-live.sh "<goal>" <workspace> [project-id]
set -euo pipefail

GOAL="${1:?usage: deploy/run-live.sh \"<goal>\" <workspace> [project-id]}"
WORKSPACE="${2:?usage: deploy/run-live.sh \"<goal>\" <workspace> [project-id]}"
PROJECT_ID="${3:-live}"

cd "$(dirname "$0")/.."

PY=".venv/bin/python"
if [ ! -x "$PY" ]; then
  echo "error: $PY not found — run deploy/setup.sh first (it creates the venv)." >&2
  exit 1
fi

TS="$(date -u +%Y%m%dT%H%M%SZ)"
LOG_DIR="$HOME/talisman/logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/${PROJECT_ID}-${TS}.log"
CONSOLE="$LOG_DIR/${PROJECT_ID}-${TS}.console.log"

setsid nohup "$PY" -m talisman_core.main --live-project \
  --goal "$GOAL" --workspace "$WORKSPACE" --project-id "$PROJECT_ID" \
  --log-file "$LOG" >"$CONSOLE" 2>&1 &
PID=$!

echo "live run started detached: pid=$PID project=$PROJECT_ID"
echo "  structured log: $LOG"
echo "  console/crash:  $CONSOLE"
echo "  watch live:     tail -f $LOG"
echo "  stop the run:   kill $PID"
