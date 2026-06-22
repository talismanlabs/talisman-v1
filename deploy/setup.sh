#!/usr/bin/env bash
#
# deploy/setup.sh — turnkey TalisMan box setup (slice S16.23).
#
# Run this ONCE on the deploy box, as the non-root `talisman` user, from the repo root, AFTER
# placing the operator secret files (see "Secrets" below). It is idempotent — safe to re-run.
#
# It does the build-side, non-secret-creating work:
#   1. preflight   — verify the host has rootless podman + uv + python + git
#   2. venv        — `uv sync` so the orchestrator (the --live-project process) can run
#   3. secrets     — verify the operator's secret files exist with safe permissions (does NOT
#                    create them; the operator supplies the values)
#   4. images      — build the worker image (keyless) and the credential-gateway image
#   5. networks    — create the sealed `talisman-internal` (--internal) + `talisman-egress`
#   6. gateway     — start the credential gateway (holds the real keys; workers stay keyless)
#
# It does NOT start a project run: that is the supervised, human-gated step the operator launches
# by hand (the command is printed at the end).
#
# Secrets it expects in $TALISMAN_SECRETS_DIR (default ~/talisman/secrets, mode 700, files 600):
#   anthropic.key         — a DEDICATED, spend-capped Anthropic API key (held only by the gateway)
#   openai.key            — a DEDICATED, spend-capped OpenAI API key (held only by the gateway)
#   telegram.token        — the Telegram bot token (used by the orchestrator's approval channel)
#   telegram.operator_id  — your numeric Telegram user id (the sole approver + the approval chat)
#
set -euo pipefail

# ---- configuration (override via environment) -------------------------------------------------
SECRETS_DIR="${TALISMAN_SECRETS_DIR:-$HOME/talisman/secrets}"
WORKER_IMAGE="${TALISMAN_WORKER_IMAGE:-talisman/worker:latest}"
GATEWAY_IMAGE="${TALISMAN_GATEWAY_IMAGE:-talisman/gateway:latest}"
INTERNAL_NET="${TALISMAN_INTERNAL_NET:-talisman-internal}"
EGRESS_NET="${TALISMAN_EGRESS_NET:-talisman-egress}"
GATEWAY_NAME="${TALISMAN_GATEWAY_NAME:-talisman-gateway}"

log()  { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32m✓\033[0m %s\n' "$*"; }
warn() { printf '    \033[1;33m!\033[0m %s\n' "$*"; }
die()  { printf '\n\033[1;31mERROR: %s\033[0m\n' "$*" >&2; exit 1; }

# ---- 1. preflight ------------------------------------------------------------------------------
log "Preflight"
[ "$(id -u)" -ne 0 ] || die "Run as the non-root 'talisman' user, not root (rootless podman is required)."
[ -f deploy/gateway/Containerfile ] || die "Run from the talisman-v1 repo root (deploy/ not found here)."
for tool in podman uv git; do
    command -v "$tool" >/dev/null 2>&1 || die "'$tool' not found on PATH. Install it first."
done
if podman info --format '{{.Host.Security.Rootless}}' 2>/dev/null | grep -qi true; then
    ok "podman is rootless"
else
    die "podman is not rootless. Configure rootless podman for the talisman user before continuing."
fi
ok "preflight passed (podman, uv, git present)"

# ---- 2. python env for the orchestrator --------------------------------------------------------
log "Syncing the Python environment (uv sync)"
uv sync
ok ".venv ready (the --live-project orchestrator runs from here)"

# ---- 3. secrets (verify only; never created here) ----------------------------------------------
log "Checking operator secrets in $SECRETS_DIR"
[ -d "$SECRETS_DIR" ] || die "Secrets dir $SECRETS_DIR is missing. Create it (mkdir -p, chmod 700) and add the key files."
# Fail closed on unsafe permissions: TIGHTEN the tree to 700/600 before any secret is mounted, so a
# secret is never read from a group-/world-readable directory or file. chmod failing (wrong owner) is fatal.
chmod 700 "$SECRETS_DIR" || die "Could not secure $SECRETS_DIR to 700 (chmod failed — check ownership)."
ok "secrets dir secured (700)"
require_secret() {
    local f="$SECRETS_DIR/$1"
    [ -s "$f" ] || die "Missing or empty secret: $f"
    chmod 600 "$f" || die "Could not secure $f to 600 (chmod failed — check ownership)."
    ok "$1 (600)"
}
require_secret anthropic.key
require_secret openai.key
require_secret telegram.token
require_secret telegram.operator_id

# ---- 4. build images ---------------------------------------------------------------------------
log "Building the worker image ($WORKER_IMAGE)"
podman build -f deploy/Containerfile.worker -t "$WORKER_IMAGE" deploy/
ok "worker image built (keyless: holds no provider key)"
log "Building the credential-gateway image ($GATEWAY_IMAGE)"
podman build -f deploy/gateway/Containerfile -t "$GATEWAY_IMAGE" deploy/gateway/
ok "gateway image built"

# ---- 5. networks (idempotent) ------------------------------------------------------------------
log "Creating networks"
if podman network exists "$INTERNAL_NET"; then
    # Reuse ONLY if it is genuinely internal (sealed). A same-named non-internal network would have a
    # route off-host and silently defeat the containment this whole deployment depends on.
    is_internal=$(podman network inspect "$INTERNAL_NET" --format '{{.Internal}}' 2>/dev/null || echo unknown)
    [ "$is_internal" = "true" ] || die "Network '$INTERNAL_NET' exists but is NOT --internal (Internal=$is_internal). It would let workers egress. Remove it and re-run: podman network rm $INTERNAL_NET"
    ok "$INTERNAL_NET already exists and is verified --internal"
else
    podman network create --internal "$INTERNAL_NET" >/dev/null
    ok "$INTERNAL_NET created (--internal, no route off-host)"
fi
podman network exists "$EGRESS_NET" || podman network create "$EGRESS_NET" >/dev/null
ok "$EGRESS_NET ready"

# ---- 6. start the credential gateway (idempotent) ----------------------------------------------
log "Starting the credential gateway ($GATEWAY_NAME)"
podman rm -f "$GATEWAY_NAME" >/dev/null 2>&1 || true
podman run -d --name "$GATEWAY_NAME" \
    --restart=always \
    --network "$INTERNAL_NET" --network "$EGRESS_NET" \
    -v "$SECRETS_DIR/anthropic.key:/run/secrets/anthropic_api_key:ro" \
    -v "$SECRETS_DIR/openai.key:/run/secrets/openai_api_key:ro" \
    "$GATEWAY_IMAGE" >/dev/null
sleep 2
if podman ps --filter "name=^${GATEWAY_NAME}$" --format '{{.Status}}' | grep -qi up; then
    ok "gateway running (restart=always)"
else
    die "gateway failed to start. Inspect: podman logs $GATEWAY_NAME"
fi

# ---- done --------------------------------------------------------------------------------------
log "Setup complete — infrastructure is up"
cat <<DONE
    worker image:  $WORKER_IMAGE   (keyless — no provider key inside)
    gateway image: $GATEWAY_IMAGE  (holds the real, dedicated, spend-capped keys)
    networks:      $INTERNAL_NET (sealed) + $EGRESS_NET
    gateway:       $GATEWAY_NAME (running) — workers reach it at
                   http://$GATEWAY_NAME:8800 (Anthropic) / :8801 (OpenAI), placeholder key only.

  The supervised first run is NOT started automatically. When you're ready to watch it, launch:

    .venv/bin/python -m talisman_core.main --live-project \\
      --goal "Build a simple Google News replica" \\
      --workspace \$HOME/talisman/workspaces/news

  It will message your Telegram at each gate (slice approval, implementation); reply APPROVE or
  REJECT. Watch the first run end-to-end — it makes real (capped) provider calls.
DONE
