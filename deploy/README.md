# TalisMan deployment artifacts

These are the pieces an operator deploys onto the always-on box (a cheap Ubuntu 24.04 VM).
A turnkey deploy script that installs and wires them together lands in a later slice; this
directory holds the building blocks.

## Worker image — `Containerfile.worker` (S16.18; ADR-0007)

The locked-down image that `workers/_container.ContainerRunner` executes each worker inside.
On Ubuntu 24.04 it carries the **Claude Code** and **Codex** CLIs and **git**, and runs as a
non-root `worker` user. It holds **no credentials** and grants no special access — at run time
the container is attached to an `--internal` podman network whose only off-host route is the
egress proxy (ADR-0007), so the worker physically cannot reach the internet except through it.

Build it:

```sh
podman build -f deploy/Containerfile.worker -t talisman/worker:latest deploy/
```

**Verified locally (S16.18), not in CI** — CI has no podman, so the image build is
operator-/local-verified, like the other container checks (S16.06):

- the CLIs resolve in the image (`claude --version` → 2.1.185, `codex --version` → 0.141.0, `git` 2.43.0);
- it runs as the non-root `worker` user;
- on an `--internal` network the worker cannot reach a provider API directly
  (`curl https://api.anthropic.com` → "couldn't connect" / no route) — ADR-0007 containment holds
  with the real image;
- the non-root worker **can write the bind-mounted workspace** when run with `--userns=keep-id`
  (which `ContainerRunner` sets) — without it, rootless podman maps the worker to an unprivileged
  subuid that cannot write host-owned files, so a real branch-and-commit would fail (S16.18).

## Egress gateway (S16.19; ADR-0009)

The boundary that lets a worker reach **only** the allowlisted AI providers — and nothing else.
Two podman networks + a dual-homed proxy container:

```sh
# the workers' sealed network (no route off-host) + the proxy's outbound network
podman network create --internal talisman-internal
podman network create talisman-egress

# the egress proxy: dual-homed, runs EgressProxy bound to 0.0.0.0:8888, enforcing the
# security.egress allowlist (api.anthropic.com, api.openai.com, github, package mirrors)
podman run -d --name talisman-egress-proxy \
  --network talisman-internal --network talisman-egress \
  -v /home/talisman/talisman-v1/src:/app/src:ro -e PYTHONPATH=/app/src \
  python:3.12-slim python -m talisman_core.adapters.egress_proxy --host 0.0.0.0 --port 8888
```

Workers run on `talisman-internal` **only**, with `HTTPS_PROXY=http://talisman-egress-proxy:8888`
(the `ContainerRunner`'s `proxy_url`). **Verified locally (S16.19):** a worker reached
`api.anthropic.com` *only* through the proxy (HTTP 401 over the tunnel), a non-allowlisted host was
denied, and a direct attempt with no proxy was blocked (no route out).

## systemd units — `systemd/` (S13.01, S16.10)

The host-side gateway and the orchestrator units. The orchestrator unit launches the
persistent `--serve` runtime (S16.10), which systemd keeps alive and restarts on failure.
