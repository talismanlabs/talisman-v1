# TalisMan v1 Progress Ledger

The single source of truth for implementation progress. Updated after every slice.
Reference templates and immutable architecture artifacts live in `docs/talisman-v1/`.

## Current status summary

- **Overall status:** TalisMan v1 is **ACCEPTED** (2026-06-19, S15.02 merged as PR #29). Now in
  **v1.1**. A cross-family security audit (Claude + Codex) was run 2026-06-19 before any feature work;
  its detailed findings are tracked **privately** (outside this public repo) and drive the v1.1
  hardening sequence below.
- **Current phase:** Phase 16 — v1.1 supply-chain & consolidation.
- **Current slice:** S16.04 Egress gatekeeper proxy (decision point) — review_ready (Claude lead / Codex
  review). Adds `adapters/egress_proxy.py`, a loopback CONNECT proxy that evaluates `security.egress`
  (tunnels allowed hosts, refuses others 403, refuses non-CONNECT 501), with real-socket integration
  tests. Per ADR-0006. This is **part 1** of audit finding P0-B (the allowlist decision point); a real
  egress boundary also needs **part 2** — OS-level containment (netns/firewall) forcing workers through
  the proxy — so AT-14 stays component-verified (env-var routing alone is cooperative/bypassable; Codex
  round-1 blocked the initial over-claim, now reframed).
- **Last completed slice:** S16.03 Wire credential scrub into the worker subprocess runner (merged, PR #32).
- **Acceptance picture:** 6 PASS end-to-end (AT-01/02/03/09/13/20 — AT-13 hardened to PASS in S16.03) ·
  9 component-verified (6 demonstrated live: AT-05/07/08/14/15/18; 3 unit-only: AT-06/10/11) · 5 waived &
  approved (AT-04/12/16/17/19).
- **Next work:** continue **v1.1-P1 consolidation** — remaining governed slices: the live Telegram bot
  incl. token redaction (→AT-05), `main.py --serve` (→AT-18), and the Codex-invocation fix (→AT-08); then
  add OS-level egress containment (part 2 of P0-B: netns/firewall forcing workers through the proxy, blocking direct egress), wire workers + clients through it, and run a supervised live-run — which
  flips AT-14 and the routed ATs to PASS. Then the five approved-waiver features starting with the durable
  checkpointer (AT-04). (Done: S16.01 supply-chain, S16.02 secrets relocation, S16.03 credential-scrub →
  AT-13 PASS, S16.04 egress proxy decision point built.)
- **Current blocker:** awaiting human review + merge of the S16.04 PR.
- **Next human decision needed:** merge the S16.04 PR; then the next v1.1-P1 slice (live Telegram or
  `--serve`).

## Build harness status (2026-06-17)

- Repo live: https://github.com/talismanlabs/talisman-v1 — **public** (changed from private so
  enforced branch protection is available on the free plan), `main` pushed.
- CI green on `main`: `deterministic-checks` ✓ and `gitleaks` ✓.
- Branch protection: **active via repository ruleset** on `main` — requires the `deterministic-checks`
  and `gitleaks` status checks, requires a pull request, and blocks direct pushes, force-pushes, and
  deletion. The merge gate is now mechanically enforced; the human is the merge authority.

## Phase checklist

| Phase | Name | Status | Start date | Completed date | User approval |
|---:|---|---|---|---|---|
| 0 | Repository constitution | accepted (constitution baseline) | 2026-06-17 | 2026-06-17 | pending |
| 1 | Development environment | accepted (constitution baseline) | 2026-06-17 | 2026-06-17 | pending |
| 2 | Domain and ports | accepted | 2026-06-17 | 2026-06-17 |  |
| 3 | LangGraph workflow skeleton | accepted | 2026-06-17 | 2026-06-17 |  |
| 4 | SQLite state and memory | accepted | 2026-06-17 | 2026-06-17 |  |
| 5 | Telegram approval interface | accepted | 2026-06-17 | 2026-06-17 |  |
| 6 | Claude Code worker adapter | accepted | 2026-06-17 | 2026-06-17 |  |
| 7 | Codex CLI worker adapter | accepted | 2026-06-17 | 2026-06-17 |  |
| 8 | Inter-agent review protocol | accepted | 2026-06-17 | 2026-06-17 |  |
| 9 | Cost gateway | accepted | 2026-06-17 | 2026-06-17 |  |
| 10 | Security profile | accepted | 2026-06-17 | 2026-06-17 |  |
| 11 | Scheduler and portfolio | accepted | 2026-06-17 | 2026-06-18 |  |
| 12 | Observability | accepted | 2026-06-18 | 2026-06-18 |  |
| 13 | systemd service | accepted | 2026-06-18 | 2026-06-18 |  |
| 14 | Bootstrap self-improvement project | accepted | 2026-06-18 | 2026-06-19 |  |
| 15 | v1 release acceptance | accepted | 2026-06-19 | 2026-06-19 | 2026-06-19 (waivers approved) |
| 16 | v1.1 supply-chain & consolidation | in_progress | 2026-06-19 |  |  |

## Slice ledger

| Date | Slice | Phase | Lead agent | Review agent | Status | Checks run | Review artifact | Open risks | Next action |
|---|---|---:|---|---|---|---|---|---|---|
| 2026-06-17 | S00.01 | 0 | Claude Code (constitution) | pending human | accepted (baseline) | ruff, ruff-format, mypy, pytest, lint-imports — all pass | n/a (ADR-0001) | Phase 0 done directly, not via PR loop (bootstrap paradox) | — |
| 2026-06-17 | S00.02 | 0 | Claude Code (constitution) | pending human | accepted (baseline) | lint-imports passes (4 contracts kept) | n/a (ADR-0001) | Fixed artifact bug: `.importlinter` used `kind`; Import Linter requires `type` | — |
| 2026-06-17 | S00.03 | 0 | Claude Code (constitution) | pending human | accepted (baseline) | n/a | n/a (ADR-0001) | docs/progress, docs/reviews, docs/adr created with templates | — |
| 2026-06-17 | S01.01 | 1 | Claude Code (constitution) | pending human | accepted (baseline) | all five checks execute green via `scripts/checks.sh` | n/a (ADR-0001) | dev toolchain via uv; runtime deps deferred per-slice | — |
| 2026-06-17 | S02.01 | 2 | Claude Code | Codex CLI | accepted | ruff, ruff-format, mypy, pytest, lint-imports — all pass | `docs/reviews/S02.01.yaml` (accept) | Codex enriched review YAML vs template — align template (follow-up) | merged (PR #1) |
| 2026-06-17 | S02.02 | 2 | Codex CLI | Claude Code | accepted | ruff, ruff-format, mypy, pytest, lint-imports — all pass | `docs/reviews/S02.02.yaml` (accept) | R1 addressed by S02.03 | merged (PR #2) |
| 2026-06-17 | S02.03 | 2 | Claude Code | Codex CLI | accepted | all five pass; negative test confirms the new contract bites | `docs/reviews/S02.03.yaml` (approve) | none | merged (PR #3) |
| 2026-06-17 | S03.01 | 3 | Claude Code | Codex CLI | accepted | all five pass; graph compiles + walks lightweight (5) and full-spiral (9) to END | `docs/reviews/S03.01.yaml` (approve) | one narrow mypy ignore for langgraph add_node overload | merged (PR #5) |
| 2026-06-17 | S03.02 | 3 | Codex CLI | Claude Code | accepted | all five pass; 17 tests incl. gate pause + 4 resume routes (approve/revise/pause/reject) on MemorySaver | `docs/reviews/S03.02.yaml` (approve) | AT-04 durable resume deferred to Phase 4 (SqliteSaver, same interface) | merged (PR #6) |
| 2026-06-17 | S04.01 | 4 | Claude Code | Codex CLI | accepted | all five pass; 19 tests (tables created + idempotent re-init preserves data) | `docs/reviews/S04.01.yaml` (pass) | SQLite placed in adapters/ (confirmed correct by reviewer) | merged (PR #7) |
| 2026-06-17 | S04.02 | 4 | Codex CLI | Claude Code | accepted | all five pass; 22 tests (cross-connection persistence, per-project isolation, stable ordering) | `docs/reviews/S04.02.yaml` (pass) | EventLog has no port yet — add one before the first core consumer (review finding) | merged (PR #8) |
| 2026-06-17 | S05.01 | 5 | Claude Code | Codex CLI | accepted | all five pass; 26 tests (allowlisted accepted, non-allowlisted rejected, fail-closed, loader) | `docs/reviews/S05.01.yaml` (accept) | none | merged (PR #9) |
| 2026-06-17 | S05.02 | 5 | Codex CLI | Claude Code | accepted | all five pass; 29 tests; INSERT-once dedup verified, error-code discrimination fail-safe (only UNIQUE swallowed) | `docs/reviews/S05.02.yaml` (pass) | no idempotency port yet; insert/advance not atomic — wiring slice to decide (review findings) | merged (PR #11) |
| 2026-06-17 | S06.01 | 6 | Claude Code | Codex CLI | accepted | all five pass; 32 tests; WorkerPort contract via injected runner (no real CLI); argv-list (no shell) | `docs/reviews/S06.01.yaml` (pass) | none | merged (PR #12) |
| 2026-06-17 | S07.01 | 7 | Codex CLI | Claude Code | accepted | all five pass; 35 tests; passes the SHARED worker contract; byte-faithful mirror of S06.01 (vendor argv only) | `docs/reviews/S07.01.yaml` (pass) | subprocess plumbing duplicated across workers — extract to workers/_subprocess once a 3rd lands (review finding) | merged (PR #13) |
| 2026-06-17 | S08.01 | 8 | Claude Code | Codex CLI | accepted | all five pass; 38 tests; ReviewResult extended with Finding + pure dict round-trip; domain stays pure | `docs/reviews/S08.01.yaml` (accept) | Codex review terse (schema-drift follow-up still open) | merged (PR #14) |
| 2026-06-17 | S08.02 | 8 | Codex CLI | Claude Code | accepted | all five pass; 46 tests; pure policy — only an accepted cross-family review permits closure (fail-closed); all branches verified | `docs/reviews/S08.02.yaml` (pass) | low: agent_family unknown-path normalization asymmetry (unreachable today) | merged (PR #15) |
| 2026-06-17 | S09.01 | 9 | Claude Code | Codex CLI | accepted | all five pass; 48 tests; GatewayClient routes via GatewayPort (injected transport); httpx transport; core imports no provider SDK | `docs/reviews/S09.01.yaml` (approve) | none | merged (PR #17) |
| 2026-06-17 | S09.02 | 9 | Codex CLI | Claude Code | accepted | all five pass; 52 tests; pre-call breaker pauses on daily/monthly hard-cap breach; UTC window verified; durable | `docs/reviews/S09.02.yaml` (approve) | TOCTOU under future concurrency (single-orchestrator v1 OK) | merged (PR #18) |
| 2026-06-17 | S10.01 | 10 | Claude Code | Codex CLI | accepted | all five pass; 55 tests; security/credentials strips raw provider/cloud secrets from worker env (D6) | `docs/reviews/S10.01.yaml` (approve) | scoped-credential issuance deferred to v1.1 (v1 workers self-auth) | merged (PR #19) |
| 2026-06-17 | S10.02 | 10 | Codex CLI | Claude Code | accepted | all five pass; 61 tests; default-deny egress allowlist; dot-boundary subdomain match — bypass classes empirically denied | `docs/reviews/S10.02.yaml` (approve) | reconcile host- vs squid domain-granularity when wiring the proxy (info) | merged (PR #20) |
| 2026-06-17 | S11.01 | 11 | Claude Code | Codex CLI | accepted | all five pass; 68 tests; active-slot cap + priority/FIFO. Codex BLOCKED a real cap-bypass (duplicate task_id); fixed (uniqueness + regression tests); re-review approve | `docs/reviews/S11.01.yaml` (approve after fix) | none | merged (PR #21) |
| 2026-06-18 | S11.02 | 11 | Codex CLI | Claude Code | accepted | all five pass; 73 tests; per-project wait metrics + 24h aging (once per window, injected clock); S11.01 preserved | `docs/reviews/S11.02.yaml` (approve) | 2 info notes (aging-boundary asymmetry is self-consistent; per-project last_wait_reason last-writer-wins) | merged (PR #22) |
| 2026-06-18 | S12.01 | 12 | Claude Code | Codex CLI | accepted | all five pass; 80 tests; health aggregation (worst-wins) + to_dict /status payload; structured JSON logging (injected sink+clock). NOTE: impl first committed to local main by mistake; moved to slice branch, main reset, re-reviewed | `docs/reviews/S12.01.yaml` (pass) | none | merged (PR #23) |
| 2026-06-18 | S13.01 | 13 | Codex CLI | Claude Code | accepted | all five pass; 85 tests; pure systemd unit renderer (gateway+orchestrator) — Restart=on-failure, orchestrator orders After+Wants gateway, no secret literals; deploy/systemd files byte-match canonical templates | `docs/reviews/S13.01.yaml` (pass) | AT-18 runtime restart exercised at operator/Phase-15 gate, not CI | merged (PR #24) |
| 2026-06-19 | S14.01 | 14 | Claude Code | Codex CLI | accepted | all five pass; 92 tests; composition root wires graph+checkpointer+scheduler+logging into a runnable TalismanApp; `talisman_core.main` entrypoint (dry-run + demo spiral); concrete wiring isolated to app (boundary held) | `docs/reviews/S14.01.yaml` (pass) | none | merged (PR #26) |
| 2026-06-19 | S14.02 | 14 | Claude Code | Codex CLI | accepted | all five pass; 96 tests; governed v1.1-planning spiral — both gates fire via ApprovalPort interrupt/resume, plan routes through WorkerPort seam, produces docs/talisman-v1.1-backlog.md. Phase 14 acceptance met | `docs/reviews/S14.02.yaml` (approved) | S14.03 lessons-retrieval not needed (deferred to v1.1) | merged (PR #27) |
| 2026-06-19 | S15.01 | 15 | Claude Code | Codex CLI | accepted | all five pass; 101 tests; HONEST v1 acceptance accounting (app/release + checklist). Lead/reviewer SWAPPED (Claude lead) for build context; Codex skeptical review BLOCKED over-claimed PASSes → corrected to 5 pass / 8 component-verified / 7 waived | `docs/reviews/S15.01.yaml` (blocked→corrected; release candidate) | resolved by S15.02 walkthrough + acceptance | merged (PR #28) |
| 2026-06-19 | S15.02 | 15 | Claude Code | Codex CLI | accepted | all five pass; 103 tests; FORMAL v1 acceptance. Records founder waiver approval; reconciles app/release to the post-walkthrough truth without inflating grades (AT-05/AT-14 waived→component-verified as prototype evidence; 5 PASS unchanged); commits operator-walkthrough transcript + founder audit package as evidence | `docs/reviews/S15.02.yaml` (**pass/accept** after 2 revise rounds — Codex caught PII in the public-repo transcript + grade inconsistencies; both fixed pre-push) | live-built v1.1 code (bot.py, --serve, egress proxy) uncommitted until P1 lands it | merged (PR #29) |
| 2026-06-19 | S16.01 | 16 | Claude Code | Codex CLI | accepted | all five pass locally via `uv sync --locked`; gitleaks default full-history scan + PII-config incremental scan both clean locally | `docs/reviews/S16.01.yaml` (pass_with_notes → accept; 2 low notes, no change needed) | supply-chain + review-gate hardening from the 2026-06-19 cross-family audit; PII rules run incrementally to avoid re-flagging redacted history | merged (PR #30) |
| 2026-06-19 | S16.02 | 16 | Claude Code | Codex CLI | accepted | deterministic checks green (docs/ops only); 5 secret files moved + verified by name+size; in-repo `secrets/` removed | `docs/reviews/S16.02.yaml` (pass; accept) | closes audit P2-①; canonical config already points at `~/talisman/secrets/` so no consumer breaks; dated audit-package snapshot left intact | merged (PR #31) |
| 2026-06-20 | S16.03 | 16 | Claude Code | Codex CLI | accepted | all five pass; new real-subprocess contract test spawns a child and proves ANTHROPIC/OPENAI/GITHUB keys absent; both adapters deduped onto the shared scrubbing `default_runner` | `docs/reviews/S16.03.yaml` (pass; accept) | closes audit P0-A; **AT-13 COMPONENT_VERIFIED→PASS** (now 6 PASS / 9 component / 5 waived); checklist regenerated; deduped runner resolves the S07.01 plumbing-duplication finding | merged (PR #32) |
| 2026-06-20 | S16.04 | 16 | Claude Code | Codex CLI | review_ready | all five pass; 3 real-socket integration tests (allowed CONNECT tunnels end-to-end; non-allowlisted → 403 via the real policy; non-CONNECT → 501) | `docs/reviews/S16.04.yaml` (block→pass after revise; round-1 caught the proxy-is-cooperative over-claim) | delivers part 1 (decision point) of P0-B; egress proxy component built per ADR-0006; full closure + AT-14 PASS need OS-level containment (part 2: netns/firewall); Codex round-1 blocked the over-claim, reframed | request Codex review; open PR; human merge |

## Decision log

| Date | Decision | Rationale | Artifact link |
|---|---|---|---|
| 2026-05-26 | Proceed with TalisMan Option C through governed slices. | User accepted full architecture target with LangGraph, structural modularity, and mandatory inter-agent review. | `docs/talisman-v1/talisman-v1-change-summary-for-audit.md` |
| 2026-06-17 | Build TalisMan via a Claude Code slice-runner loop: one branch+PR per slice, CI deterministic-check gate, cross-family review artifact, branch-protection human gate. | Dogfoods TalisMan's own governed workflow; maps the artifacts' gated loop onto GitHub. | This ledger; `README.md` |
| 2026-06-17 | Phases 0–1 established directly as the repository-constitution baseline rather than via PR-gated slices. | Bootstrap paradox: CI (the gate) needs pyproject/.importlinter/skeleton/toolchain to exist on `main` before any PR can be gated. Loop begins at Phase 2. | `docs/adr/0001-bootstrap-constitution.md` |
| 2026-06-17 | Corrected `.importlinter` contract key from `kind` to `type`. | Import Linter 2.x rejects `kind`; the canonical artifact scaffold was buggy. | `.importlinter`; ADR-0001 |
| 2026-06-17 | Baseline `pyproject` declares dev dependencies only; runtime deps added per-slice. | Coding standard: do not add runtime dependencies unless a slice needs them. | `pyproject.toml` |
| 2026-06-17 | Made the repository public and applied a branch ruleset on `main`. | Enforced protection/rulesets are unavailable on free private repos (HTTP 403). User chose public over upgrading to Pro or running unprotected. Ruleset requires the CI checks + a PR and blocks direct/force pushes and deletion. | this ledger; repo ruleset |
| 2026-06-17 | Approved ADR-0002 (Phase 3 LangGraph design); added `langgraph` as the first runtime dependency. | Resolves the Phase 3 spec gap (graph shape, gates→interrupt/resume, checkpointer injection, LangGraph/policy seam) before implementation; user merged the ADR PR. | `docs/adr/0002-langgraph-workflow-design.md`; PR #4 |
| 2026-06-17 | Approved ADR-0003 (approval idempotency design). | Resolves the Phase 5 / S05.02 spec gap (idempotency-key scheme, INSERT-once dedup via gate_events UNIQUE, reordering guard, 72h TTL) before implementation; user merged the ADR PR. | `docs/adr/0003-approval-idempotency.md`; PR #10 |
| 2026-06-17 | Approved ADR-0004 (cost gateway — direct, port-first). | Resolves the Phase 9 spec gap: gateway forwards directly to providers (no LiteLLM) behind the typed GatewayPort, LiteLLM swappable later. User chose this in a plain-English design review; added httpx in S09.01. | `docs/adr/0004-cost-gateway-direct.md`; PR #16 |
| 2026-06-18 | ADR-0005 (Phase 14 = assemble + simulated run). | Resolves the flagged Phase 14 under-specification: build the composition root + entrypoint and run one deterministic governed v1.1-planning spiral (stub workers, in-process approval, stub gateway) — no live spend, CI-testable. Decomposed into S14.01/02/03; full live run deferred to post-v1 operation. User chose this in a plain-English design review. | `docs/adr/0005-bootstrap-project-scope.md` |
| 2026-06-19 | **TalisMan v1 ACCEPTED.** Founder approved the five waivers (AT-04/12/16/17/19) after a full live operator walkthrough verifying the runtime behaviours; the five waived items become the first v1.1 feature project; the P1 sequence is confirmed. | The walkthrough demonstrated every operator capability live (Telegram control plane, both workers, credential scrub, egress proxy, SQLite restart, systemd kill→restart, governed spiral); grades reconciled honestly (no inflation). | `docs/release/v1-acceptance-checklist.md`; `founder-audit-package/2026-06-19/`; S15.02 |
| 2026-06-19 | Ran a cross-family security audit (Claude + Codex) over the public repo + full history before v1.1 feature work; opened v1.1 with a supply-chain & review-gate hardening slice (S16.01). | Founder wanted assurance that no vulnerabilities or PII were left needlessly exposed in the public repo. Result: **no credentials in the 92-commit history**; the only committed PII is the self-published commit-identity email (already permanent in commit metadata). The three "high" code findings are unwired controls that become reachable only when v1.1-P1 wires the prototypes, so each fix is bound to its wiring slice. | private audit report (kept out of repo); `docs/slice-backlog.md` S16.01; this ledger |
| 2026-06-19 | Relocated the live `*.secret` files out of the public-repo working tree to the canonical `~/talisman/secrets/` (dir 0700, files 0600); removed the in-repo `secrets/` directory. | Audit finding P2-①: the secrets sat inside the public checkout, protected only by `.gitignore` — one `git add -f`/typo/zip from exposure. The canonical spec already specifies `~/talisman/secrets/`, so no shipped consumer changes; no rotation (nothing was ever exposed). | S16.02; `docs/talisman-v1/talisman-v1-config-templates.md` |
| 2026-06-20 | Wired the credential scrub into worker execution: a shared `workers/_subprocess.default_runner` always passes `env=worker_environment()`, and a real-child CI test proves the scrubbed provider/cloud keys are absent. AT-13 (credential isolation) hardens COMPONENT_VERIFIED → PASS (first v1.1-P1 grade flip). | Audit finding P0-A: the scrub helper existed but was unwired, so a real worker would inherit the orchestrator's keys. Wiring it at one unbypassable spawn point (also dedups the two adapters) makes the D6 guarantee hold and is provable end-to-end in CI. | S16.03; `tests/workers/test_subprocess_runner.py`; `app/release.py` |
| 2026-06-20 | Built the egress gatekeeper proxy (the allowlist DECISION point): a loopback CONNECT proxy (`adapters/egress_proxy.py`) that consults `security.egress` and tunnels allowed hosts / refuses others (403) / refuses non-CONNECT (501); proven by real-socket integration tests. Per ADR-0006 — Pat chose the gatekeeper-proxy approach over a per-client check. | Audit finding P0-B: the egress allowlist was advisory (no caller). A single proxy enforces it on BOTH orchestrator and worker-subprocess traffic — a per-client check can't cover worker egress, the real exfil path. A proxy is a cooperative control, so a real boundary needs OS-level containment (netns/firewall) forcing workers through it (part 2, required follow-up); Codex round-1 blocked the "closes P0-B" over-claim and it was reframed. AT-14 stays component-verified; no grade inflated. | `docs/adr/0006-egress-gatekeeper-proxy.md`; S16.04; `tests/adapters/test_egress_proxy.py` |

## Risk register

| Risk | Probability | Impact | Mitigation | Owner | Status |
|---|---|---|---|---|---|
| Architecture drift from LLM-generated code | medium | high | Import Linter, typed ports, contract tests, cross-family review, CI gate | Pat / agents | open |
| Scope creep before first full run | medium | high | Slice backlog, phase gates, one-PR-per-slice rule | Pat | open |
| Cost overrun during agentic implementation | medium | medium | Watch usage; per-slice diffs; (Phase 9 gateway does not govern bootstrap spend) | Pat | open |
| Under-specified slices (Phases 3–5, 8–14) cause agent drift | high | medium | Slice-runner halts and writes a proposed ADR instead of guessing | agents | open |
| Codex CLI headless implementation unreliable/costly | medium | medium | Fallback (ADR): Claude implements, Codex still reviews every slice | Pat / agents | open |
| Port-layer purity enforced by review, not Import Linter | low | medium | Added `ports_do_not_import_infrastructure` Import Linter contract (S02.03); verified by negative test | agents | mitigated |
| Review-artifact YAML schema drifts between reviewers (Codex/Claude improvise keys) | low | low | Align `docs/reviews/REVIEW-TEMPLATE.yaml` + pin the schema in both review prompts (follow-up) | agents | open |
| Codex `workspace-write` sandbox blocked by bwrap (no loopback netns) in this env | low | low | Use `--sandbox danger-full-access` for Codex-led implementation; bounded by the outer environment + review + checks | agents | open |
| SQLite event log (S04.02) has no consuming port yet | low | low | Add an `EventLog` port in `talisman_core.ports` before any core layer consumes the log; app wires the adapter (S04.02 review finding) | agents | open |
| Approval idempotency (S05.02) has no port; insert/advance not atomic | low | low | Add an idempotency port before a core consumer; the Telegram-wiring slice decides single-transaction vs recorded-row-as-replay-barrier (S05.02 review findings) | agents | open |
| Worker subprocess plumbing (CommandResult/runner) duplicated across claude_code + codex_cli | low | low | Extract to a shared `talisman_core.workers._subprocess` module (S07.01 review finding). **Resolved in S16.03** — both adapters now use the shared scrubbing `default_runner`; CommandResult/runner live in `workers/_subprocess` | agents | mitigated (S16.03) |
| `agent_family` (S08.02) does not normalize unknown agent names (case/whitespace) | low | low | Normalize the fallback (`key = agent_name.strip().lower(); return map.get(key, key)`); unreachable today since all real agents are in the known map (S08.02 review finding) | agents | open |
| Budget breaker (S09.02) has a check-then-record TOCTOU gap under concurrency | low | low | Single-orchestrator v1 is unaffected; if the gateway becomes concurrent, enforce check+record in one transaction or via a serialized writer (S09.02 review open-risk) | agents | open |
| Egress allowlist (S10.02) is host-granular; squid.conf is domain-granular | low | low | Python layer is the more restrictive (fail-safe). **Resolved by ADR-0006 / S16.04** — the in-repo CONNECT proxy reuses `security.egress` as the single policy (no squid; one source of truth) | agents | mitigated (S16.04) |
| Scoped-credential issuance mechanism for workers not built (S10.01) | low | medium | v1 workers self-authenticate; design + build host-side scoped/short-lived credential issuance in v1.1 if/when the orchestrator brain or workers need proxied provider access | Pat / agents | open |
| systemd kill-and-restart (AT-18) verified only at unit-file level, not in CI | low | low | pytest cannot run `systemd --user`; exercise the real kill-and-restart during operator install and the Phase 15 acceptance run (AT-18) (S13.01 review open-risk) | Pat / agents | open |
| Live-built v1.1 runtime (Telegram `bot.py`, `--serve`, egress proxy) is gate-clean but uncommitted | medium | medium | Built live during the 2026-06-19 walkthrough outside the slice loop; `main.py --serve` is stashed and `bot.py` is untracked. Land each as a governed v1.1-P1 slice (branch+PR+cross-family review) before building on it; do not let it rot in the working tree | agents | open |
| Flagship security controls (worker credential scrub, egress allowlist, Telegram token redaction) are built but NOT wired into a live path | high (once wired) | high | Not reachable in shipped v1 (only stub workers run; no live bot is instantiated) — the 2026-06-19 cross-family audit verified reachability. Each fix is a **blocking acceptance criterion** on the v1.1-P1 slice that wires its path, gated by a contract test before the AT may flip to PASS. **cred-scrub→AT-13 DONE (S16.03).** **egress proxy DECISION POINT built (S16.04, enforces in integration tests); a proxy is cooperative, so AT-14 flips only when OS-level containment (netns/firewall) forces all worker egress through it (part 2, required follow-up).** Remaining: egress containment (part 2), live-telegram token redaction→AT-05 | agents | in_progress |
| Supply chain: unpinned CI actions, no committed lockfile, unverified gitleaks binary, PII-blind secret scan | medium | medium | S16.01 commits `uv.lock` + `uv sync --locked`, SHA-pins actions, checksum-verifies the gitleaks binary, and adds a PII-aware incremental gitleaks config | agents | mitigated (S16.01) |
| `secrets/` lives inside the public-repo working tree (gitignored, never committed) | low | high | Single `git add -f`/typo/zip away from exposing live keys. Relocate to `~/talisman/secrets/` (the documented external location) as the v1.1 step after S16.01; keep `.gitignore` entries as belt-and-suspenders. **Done in S16.02** (moved to `~/talisman/secrets/`; in-repo dir removed) | Pat / agents | mitigated (S16.02) |
