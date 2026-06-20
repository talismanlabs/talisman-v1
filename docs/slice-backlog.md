# TalisMan v1 Slice Backlog

## Document control

- **Version:** 1.0 implementation-management baseline
- **Date:** 2026-05-26
- **Purpose:** Ordered implementation backlog for Large Language Model (LLM) coding agents.
- **Acronym discipline:** Application Programming Interface (API), Command Line Interface (CLI), Structured Query Language (SQL), and Architecture Decision Record (ADR) are spelled out on first use in this document.

## Slice status legend

- `not_started`
- `in_progress`
- `blocked`
- `review_ready`
- `accepted`
- `rejected`

## Backlog

| Slice | Phase | Title | Lead | Reviewer | Status | Acceptance criteria |
|---|---:|---|---|---|---|---|
| S00.01 | 0 | Create repository skeleton | Claude Code | Codex CLI | accepted | Required folders, `AGENTS.md`, `CLAUDE.md`, and `pyproject.toml` exist. (constitution baseline, ADR-0001) |
| S00.02 | 0 | Add import-boundary contracts | Codex CLI | Claude Code | accepted | `.importlinter` exists and `lint-imports` passes. (constitution baseline) |
| S00.03 | 0 | Add progress and review directories | Claude Code | Codex CLI | accepted | `docs/progress`, `docs/reviews`, and `docs/adr` exist with templates. (constitution baseline) |
| S01.01 | 1 | Install local development environment | Codex CLI | Claude Code | accepted | `.venv` created and all deterministic checks execute. (constitution baseline) |
| S02.01 | 2 | Implement domain models | Claude Code | Codex CLI | accepted | `Project`, `Gate`, `Artifact`, and `ReviewResult` models exist with tests. (merged PR #1) |
| S02.02 | 2 | Implement ports | Codex CLI | Claude Code | accepted | Worker, approval, state, gateway, memory, and notifier ports exist. (merged PR #2) |
| S02.03 | 2 | Harden ports import boundary | Claude Code | Codex CLI | accepted | `.importlinter` forbids `ports` importing `adapters`/`workers`; `lint-imports` passes (from S02.02 review finding R1). (merged PR #3) |
| S03.01 | 3 | Implement LangGraph spiral state | Claude Code | Codex CLI | accepted | Serializable state schema and basic graph compile. (per ADR-0002; merged PR #5) |
| S03.02 | 3 | Add approval interrupt and resume | Codex CLI | Claude Code | accepted | Fake approval gate pauses and resumes after decision. (interrupt()/Command resume; per ADR-0002; merged PR #6) |
| S04.01 | 4 | Add SQLite migrations | Claude Code | Codex CLI | accepted | Database initializes idempotently. (adapters/sqlite; canonical schema; merged PR #7) |
| S04.02 | 4 | Add project event log | Codex CLI | Claude Code | accepted | Events persist and can be queried by project. (SQLite events table + adapter; merged PR #8) |
| S05.01 | 5 | Add Telegram allowlist | Claude Code | Codex CLI | accepted | Non-allowlisted user is rejected. (adapters/telegram; fail-closed; merged PR #9) |
| S05.02 | 5 | Add approval idempotency | Codex CLI | Claude Code | accepted | Duplicate approval messages do not double-advance state. (INSERT-once via gate_events UNIQUE; per ADR-0003; merged PR #11) |
| S06.01 | 6 | Add Claude Code worker adapter | Claude Code | Codex CLI | accepted | Adapter passes worker contract tests. (workers/claude_code; injected runner; shared contract fixture; merged PR #12) |
| S07.01 | 7 | Add Codex CLI worker adapter | Codex CLI | Claude Code | accepted | Adapter passes worker contract tests. (workers/codex_cli; reuses shared contract fixture; merged PR #13) |
| S08.01 | 8 | Add structured review artifact format | Claude Code | Codex CLI | accepted | Reviews save status, findings, and required fixes. (domain Finding + ReviewResult.findings + dict round-trip; merged PR #14) |
| S08.02 | 8 | Enforce cross-family review before acceptance | Codex CLI | Claude Code | accepted | Slice cannot close without review artifact. (policies/review_enforcement; fail-closed; cross-family + accept required; merged PR #15) |
| S09.01 | 9 | Add gateway adapter | Claude Code | Codex CLI | accepted | Model calls route through gateway port. (adapters/gateway_client; injected transport + httpx; per ADR-0004; merged PR #17) |
| S09.02 | 9 | Add budget circuit breakers | Codex CLI | Claude Code | accepted | Simulated daily/monthly cap pauses work. (adapters/sqlite/budget; pre-call hard-cap breaker; budget_events; merged PR #18) |
| S10.01 | 10 | Add credential proxy | Claude Code | Codex CLI | accepted | Worker environment lacks raw provider keys. (security/credentials env-scrub; scoped issuance is v1.1; merged PR #19) |
| S10.02 | 10 | Add egress allowlist | Codex CLI | Claude Code | accepted | Disallowed domain access fails in test profile. (security/egress; default-deny; dot-boundary subdomain match; merged PR #20) |
| S11.01 | 11 | Add portfolio scheduler | Claude Code | Codex CLI | accepted | Active worker slots cap is enforced. (scheduler/portfolio; priority/FIFO; task_id uniqueness from review R1; merged PR #21) |
| S11.02 | 11 | Add wait-time aging metrics | Codex CLI | Claude Code | accepted | Wait time tracked per project. (per-project wait metrics + 24h aging; injected clock; merged PR #22) |
| S12.01 | 12 | Add health check and logs | Claude Code | Codex CLI | accepted | `/status` and log files expose health. (observability/health worst-wins + to_dict; observability/logs structured JSON; merged PR #23) |
| S13.01 | 13 | Add systemd units | Codex CLI | Claude Code | accepted | Services install and restart locally. (app/systemd_units renderer; Restart=on-failure; gateway-first ordering; deploy/systemd/*.service; merged PR #24) |
| S14.01 | 14 | Composition root + entrypoint | Claude Code | Codex CLI | accepted | App assembles + `talisman_core.main` entrypoint runs a deterministic cycle. (per ADR-0005; app/composition + main; merged PR #26) |
| S14.02 | 14 | Governed self-improvement spiral run | Claude Code | Codex CLI | accepted | TalisMan completes one deterministic governed v1.1-planning spiral; gates fire; v1.1 backlog artifact produced. (app/bootstrap + run_gated_project; merged PR #27) |
| S14.03 | 14 | Minimal lessons retrieval (conditional) | Codex CLI | Claude Code | not_needed | S14.02 completed the governed spiral without lessons retrieval; deferred to v1.1 (tracked in v1.1 backlog). |
| S15.01 | 15 | Execute acceptance test plan | Claude Code | Codex CLI | accepted | Release checklist passes or has explicit waivers. (app/release; honest 5 pass / 8 component-verified / 7 waived after Codex blocked over-claims; release candidate; merged PR #28) |
| S15.02 | 15 | Formal v1 acceptance — record founder waiver approval | Claude Code | Codex CLI | accepted | Driven by the founder's 2026-06-19 acceptance decision (durable artifact: `docs/release/v1-waiver-approval-2026-06-19.md`). **Acceptance criteria:** (1) a committed founder-approval artifact covers AT-04/12/16/17/19; (2) `app/release` + checklist + ledger mark v1 ACCEPTED; (3) the five end-to-end PASS criteria are unchanged (no grade inflation); (4) live-demonstrated items stay component-verified as **prototype/operator evidence** and flip to PASS only when their governed v1.1-P1 code lands; (5) no PII in committed evidence. (accepted; merged PR #29) |

## v1.1 backlog (post-acceptance; phases 16+)

v1 was ACCEPTED 2026-06-19 (PR #29). v1.1 continues the same governed slice loop and
S-numbering at phase 16. Consolidation themes are tracked in `docs/talisman-v1.1-backlog.md`;
the hardening below derives from the 2026-06-19 cross-family security audit (Claude + Codex;
detailed findings kept private, outside this public repo).

| Slice | Phase | Title | Lead | Reviewer | Status | Acceptance criteria |
|---|---:|---|---|---|---|---|
| S16.01 | 16 | Supply-chain & review-gate hardening | Claude Code | Codex CLI | accepted | First v1.1 slice; lands the audit's P1 supply-chain bundle. **Acceptance criteria:** (1) `uv.lock` is committed and CI installs via `uv sync --locked` (reproducible, pinned builds); (2) third-party GitHub Actions are SHA-pinned and the gitleaks binary is checksum-verified before use; (3) a committed `.gitleaks.toml` adds public-repo PII rules (email / absolute home path) run incrementally over new commits, without re-flagging redacted history; (4) `scripts/codex_review.sh` strictly validates the slice id (path-traversal), nonce-fences the untrusted diff (prompt-injection of the review gate), and structurally checks the emitted artifact; (5) all five deterministic checks stay green and **no application/runtime behavior changes** (CI/tooling/governance only). (merged PR #30) |
| S16.02 | 16 | Relocate secrets out of the repo working tree | Claude Code | Codex CLI | accepted | Closes audit finding P2-① (the live secret files lived inside the public-repo checkout, protected only by `.gitignore`). **Acceptance criteria:** (1) the live `*.secret` files are moved to the canonical `~/talisman/secrets/` (dir 0700, files 0600), verified by name+size; (2) the in-repo `secrets/` directory no longer exists; (3) `.gitignore` keeps `secrets/` / `*.secret` as belt-and-suspenders; (4) no committed runtime consumer breaks (the canonical config already uses `~/talisman/secrets/`; the dated audit-package snapshot is left intact); (5) deterministic checks stay green (docs/ops only). (merged PR #31) |
| S16.03 | 16 | Wire credential scrub into the worker subprocess runner | Claude Code | Codex CLI | review_ready | Closes audit finding P0-A and flips **AT-13 → PASS**. **Acceptance criteria:** (1) a shared `workers/_subprocess.default_runner` is the single spawn point for both worker adapters and ALWAYS passes `env=worker_environment()` (scrub unbypassable by construction; also dedups the duplicated runner — the `worker-subprocess-dedup` v1.1 item); (2) a CI contract test spawns a REAL child process and proves the scrubbed provider/cloud keys (`ANTHROPIC_API_KEY`/`OPENAI_API_KEY`/`GITHUB_TOKEN`) are absent from the worker environment; (3) `app/release` AT-13 moves COMPONENT_VERIFIED → PASS with that test as evidence, and the locking test + rendered checklist are updated honestly (no other grade changes); (4) all five deterministic checks stay green and import boundaries hold (workers→security is permitted). |

## Slice rule

If a slice needs more than one reviewable diff, split it. Small slices preserve momentum and make inter-agent review meaningful.
