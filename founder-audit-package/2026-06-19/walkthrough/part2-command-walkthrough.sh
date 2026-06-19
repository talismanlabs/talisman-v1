#!/usr/bin/env bash
# =============================================================================
# TalisMan v1 — Founder Audit Package · Part 2 of 3
# ANNOTATED COMPANION to the captured transcript (part2-live-transcript.txt, 2026-06-19).
# This is NOT a clean-checkout reproducible script. Several steps are illustrative echoes,
# and the Telegram / --serve / egress sections depend on PROTOTYPE v1.1-P1 runtime code that
# was built live during the walkthrough and is NOT yet committed under governance. Treat it as
# documentation of what was run (read alongside the transcript), not as reviewed release code.
#
# To actually run the live sections you need: the project venv (.venv), `claude` + `codex` on
# PATH, the gitignored secrets/ files, AND the uncommitted v1.1-P1 prototypes
# (adapters/telegram/bot.py, main.py --serve, the egress proxy).
# =============================================================================
set -u
PY=.venv/bin/python
say(){ printf '\n\033[1;36m### %s\033[0m\n' "$*"; }

say "0. Deterministic gate (AT-01/02/03) — ruff, mypy --strict, pytest, import-linter"
./scripts/checks.sh | tail -6

say "1. TalisMan assembles into a running service (entrypoint)"
$PY -m talisman_core.main --dry-run

say "2. Governed self-improvement spiral — TalisMan plans its own v1.1 through its gates (AT-20)"
$PY - <<'PY'
from talisman_core.app.bootstrap import run_self_improvement_spiral
r = run_self_improvement_spiral()
print("phases:", " -> ".join(r.final_state["completed_phases"]))
print("gates fired:", r.gates_fired)
PY

say "3. SQLite state survives a restart (AT-15)"
$PY - <<'PY'
import tempfile; from pathlib import Path
from talisman_core.adapters.sqlite.migrations import initialize_database
from talisman_core.adapters.sqlite.budget import SQLiteBudgetAdapter
db = Path(tempfile.gettempdir())/"tm_wt.db"; db.unlink(missing_ok=True)
initialize_database(db); SQLiteBudgetAdapter(db).record_spend(4.25, "demo")
print("fresh handle reads:", SQLiteBudgetAdapter(db).current_daily_spend_usd(), "<- survived restart")
db.unlink(missing_ok=True)
PY

say "4. Worker families run real controlled slices (AT-07 Claude, AT-08 Codex)"
echo "   Claude:  ClaudeCodeWorker runs 'claude -p <prompt>' and saves a transcript artifact."
echo "   Codex :  CodexCliWorker runs 'codex exec --sandbox … --skip-git-repo-check -' (prompt on stdin)."
echo "   (see transcript DEMO 4 / DEMO 11b for the live runs)"

say "5. Credential isolation — long-lived keys scrubbed from the worker env (AT-13)"
$PY - <<'PY'
import os; from talisman_core.security.credentials import worker_environment, DEFAULT_SCRUBBED_VARS
os.environ["ANTHROPIC_API_KEY"]="sk-DEMO"; os.environ["OPENAI_API_KEY"]="sk-DEMO"
print("scrubbed worker env still holds:", [k for k in DEFAULT_SCRUBBED_VARS if k in worker_environment()], "<- empty")
PY

say "6. Telegram control plane (AT-05) — needs secrets/telegram_*.secret"
if [ -s secrets/telegram_bot_token.secret ]; then
  $PY - <<'PY'
from pathlib import Path
from talisman_core.adapters.telegram.bot import TelegramBot
bot = TelegramBot.from_secret_files(Path("secrets/telegram_bot_token.secret"), Path("secrets/telegram_user_allowlist.secret"))
me = bot.get_me(); print(f"live bot @{me['username']} reachable; allowlist enforces accept/reject")
PY
else echo "   (skipped — set up secrets/telegram_bot_token.secret to run live)"; fi

say "7. systemd auto-restart after crash (AT-18)"
echo "   Install a user unit running 'python -m talisman_core.main --serve', then:"
echo "     systemctl --user start talisman-demo ; kill -9 \$(MainPID) ; systemd restarts it"
echo "   (see transcript DEMO 10: code=killed status=9/KILL -> Scheduled restart -> Started)"

say "8. Egress allowlist enforced by a proxy (AT-14)"
echo "   A CONNECT proxy calls security/egress.is_allowed before tunneling:"
echo "     api.anthropic.com  -> ALLOWED (tunneled, reached)"
echo "     *.example.com      -> BLOCKED (403 before any connection)"

say "Walkthrough complete — see part2-live-transcript.txt for the captured live output."
