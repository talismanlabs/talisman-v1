# TalisMan v1 Decision Audit

## Document control

- **Version:** 1.1 controlled implementation baseline
- **Date:** 2026-05-26
- **Status:** Implementation baseline updated after user acceptance review.
- **Legacy source name:** The source Decision Register and Research Validation Report used the working name `clawdbot`. This document uses the implementation name **TalisMan**.
- **Accepted changes from user review:** rename system to TalisMan; keep LangGraph in v1 instead of deferring it; make two-tier workflow with user override explicit; make structural modularity mandatory; make inter-agent review mandatory; target the full Option C architecture through governed slices rather than a disposable prototype.
- **Change control:** Do not alter architecture decisions without explicit user approval and a recorded decision-audit entry.
- **Acronym discipline:** Application Programming Interface (API), Command Line Interface (CLI), Large Language Model (LLM), Open Web Application Security Project (OWASP), Comma-Separated Values (CSV), JavaScript Object Notation (JSON), Hypertext Transfer Protocol (HTTP), Domain Name System (DNS), Structured Query Language (SQL), Secure Shell (SSH), and Virtual Private Network (VPN) are spelled out on first use in this document.

## Changes from Decision Register v1.0

### D1. Orchestrator architecture

- **Original:** Small Python service under `systemd`; vendor-agnostic brain adapter; Claude Code and Codex CLI invoked as subprocess workers; orchestrator never adjudicates critical reviewer disagreement and always escalates.
- **Revised:** Python service remains, but adopts LangGraph for state-machine, checkpoint, interrupt, and resume mechanics. “Always escalate” becomes confidence-weighted escalation above `T = 0.70`, with irreversible actions always escalated and a daily escalation budget of `B = 6`.
- **Reason:** Research supports orchestrator-worker but warns that blanket escalation causes escalation flooding. LangGraph maps directly to checkpoint and interrupt gates [Anthropic orchestrator-worker sources; Elastic human-in-the-loop post; LangGraph human-in-the-loop middleware; Cemri et al., NeurIPS 2025].

### D2. Workflow tiering

- **Original:** No tier system; uniform spiral methodology for every project.
- **Revised:** Minimal two-tier toggle: `lightweight` and `full_spiral`.
- **Reason:** PMI/PMBOK tailoring guidance says applying the same rigor uniformly is inefficient and ineffective [pmi.org/disciplined-agile/process/process-tailoring-workshops; linkedin.com Langley].
- **Conflict surfaced:** User previously rejected tiering. Research-aligned default is two-tier. User override remains available by disabling lightweight mode.

### D3. Interface

- **Original:** Telegram bot for v1; filesystem inspection; future Tailscale-only dashboard; never public-facing.
- **Revised:** Core decision held. Added Telegram user-ID allowlist, secret-managed bot token, idempotency keys, and message-ordering tolerance.
- **Reason:** Research supports Telegram for personal-scale control but documents bot token leakage, adversarial bot use, and bot-to-bot loop risks [core.telegram.org/bots/features; NVISO; alexhost.com].

### D4. Red-team integration

- **Original:** Hybrid configuration: rotating Claude Code and Codex CLI lead; same-family reviewer by API; cross-family reviewer by other CLI; escalate disagreements.
- **Revised:** Hybrid structure held. Cross-family review is weighted as substantive. Same-family review is optional on routine slices and required on critical slices. Reviewer order is randomized.
- **Reason:** Cross-family review is higher-signal because same-family models share correlated blind spots [arXiv:2506.07962; arXiv:2505.17656; Redis engineering write-up].

### D5. Cost cap structure

- **Original:** Soft daily `$5`, hard daily `$10`, hard monthly `$60`, per-project soft budget.
- **Revised:** Caps held. Added gateway-level pre-call accounting, per-call `max_tokens`, and anomaly pause at `3x` trailing-hour spend rate in a 15-minute window.
- **Reason:** Budget enforcement must live outside agent code; runaway loops can burn material budget before post-hoc accounting catches them [aisecuritygateway.ai; OWASP LLM10:2025].

### D6. Sandbox

- **Original:** Container isolation with one mounted volume, unrestricted network, global credentials as container environment variables.
- **Revised:** Container isolation held. Credentials move to host-side proxy or gateway. Worker containers receive no long-lived provider keys. Network egress becomes allowlist-based.
- **Reason:** Research directly contradicts global environment credentials and unrestricted egress. OWASP and Anthropic sandboxing guidance identify credential exfiltration and network exfiltration as core risks [OWASP LLM Top 10 2025; OWASP Agentic Top 10; Anthropic Claude Code sandboxing docs].
- **Conflict surfaced:** User accepted global credentials for hands-off simplicity. Research-aligned default is scoped credential proxy plus allowlist. User override exists only for dummy offline testing.

### D7. Failure recovery

- **Original:** Gate checkpointing; exponential backoff `1s`, `5s`, `30s`; three retries; escalation; catastrophic halt; worker timeouts; project circuit breaker.
- **Revised:** Core held. Added full jitter, `Retry-After` handling, and retryable status code set `{408, 429, 500, 502, 503, 504}` plus network errors.
- **Reason:** Jitter is required to avoid retry storms; `Retry-After` reflects server-side capacity [AWS Architecture Blog; grizzlypeaksoftware.com].

### D8. Portfolio management

- **Original:** Three active worker slots; first-in-first-out priority; manual override; pause, resume, archive; cost-aware scheduling.
- **Revised:** Slot count held. Added wait-time instrumentation and automatic aging promotion after 24 hours waiting.
- **Reason:** Pure first-in-first-out can starve projects under burst; aging is the standard remedy [Wikipedia starvation; eng.libretexts.org; Modexa; TrueFoundry; Oracle docs].

### D9. Cross-project memory

- **Original:** Markdown retrospectives plus lessons CSV at `~/talisman/lessons.csv`.
- **Revised:** Markdown retrospectives held. Lessons substrate changes to SQLite from day one, preserving the original fields and adding audit fields.
- **Reason:** SQLite prevents concurrent-write hazards, supports queryability, and provides an audit path for updates, retractions, and supersessions [NASA Lessons Learned Information System sources; PMI lessons-learned guidance; arXiv:1812.05168].
- **Conflict surfaced:** User accepted CSV. Research-aligned default is SQLite. User override exists but is not recommended.

### D10. Project scope

- **Original:** TalisMan accepts whatever the user brings; no pre-screening criteria.
- **Revised:** Held. Tiering from D2 changes workflow intensity, not project eligibility.
- **Reason:** Explicit user preference and no contrary research requirement.

### D11. Acceptance verification

- **Original:** Skip CodeRabbit; use cross-vendor agent review plus local linters; acceptance protocol varies by project type.
- **Revised:** Held. Added mandatory deterministic pre-commit checks before any LLM review: `ruff`, `mypy` or `pyright`, and `pytest` for Python; project equivalents elsewhere.
- **Reason:** Research supports skipping dedicated software-as-a-service review at personal scale and emphasizes deterministic checks as cheap insurance [Greptile benchmark as vendor-published; findskill.ai 2026 comparison; Research Validation Report linter stack].

### D12. Research validation requirement

- **Original:** All decisions subject to research validation before bootstrap.
- **Revised:** Held and closed by this artifact set.
- **Reason:** This final architecture, implementation guide, configuration templates, runbook, and audit are the post-validation baseline.

## Conflicts surfaced for user decision

| Decision | Original user-aligned commitment | Research finding | Recommended default | User override |
|---|---|---|---|---|
| D2 | No workflow tiering | Uniform rigor is inefficient and ineffective under PMI tailoring guidance | Minimal `lightweight` / `full_spiral` toggle | `workflow.allow_lightweight = false` |
| D6 | Global credentials in container environment variables | Credentials reachable by agent process are exfiltration risk | Host-side proxy with scoped credentials | `security.credentials_mode = global_env_unrecommended` for dummy offline tests only |
| D6 | Unrestricted network egress | Network egress is the exfiltration channel | Egress allowlist via proxy | `security.egress_mode = unrestricted_unrecommended` for dummy offline tests only |
| D9 | CSV lessons database | CSV has query, concurrency, and audit limitations | SQLite from day one | `memory.store = csv_unrecommended` |

## Items deferred to v1.1+

1. Calibrate D1 escalation threshold after two to four weeks.
2. Measure whether cross-family review catches material defects often enough to justify its cost.
3. Reassess the `$60` monthly API budget after real slice telemetry.
4. Decide on Tailscale Funnel versus Cloudflare Tunnel only if v2 dashboard requirements change.
5. Implement semantic lesson retrieval at 50 lessons or first retrieval complaint.
6. Evaluate gVisor or Kata Containers before broad autonomous web ingestion.
7. Add read-only Model Context Protocol (MCP) state exposure only after the core security model is stable.
8. Revisit CodeRabbit or comparable code-review software-as-a-service only after code-heavy projects become routine.

## Migration notes

1. **The final architecture is more secure than the draft.** Credentials and egress changed materially. This is the largest implementation difference.
2. **The final architecture is less uniform than the draft.** Tiering appears in D2 and routine-versus-critical review appears in D4, but both are intentionally minimal.
3. **The final architecture adopts LangGraph.** The draft allowed a custom Python state machine. The final design uses LangGraph to avoid rebuilding checkpoint, interrupt, and resume mechanics.
4. **SQLite is mandatory by default.** The draft CSV path is preserved only as an override for experimentation.
5. **Cost controls move outward.** The orchestrator does not self-police API spend; the gateway blocks calls before money is spent.
6. **Irreversibility is the approval boundary.** Replit and Gemini CLI incidents show that destructive operations must be gated even when the model sounds confident.


## Controlled acceptance-review updates

These updates were accepted by the user after review of the original artifact set. They are not ad hoc redesigns; they are recorded here for traceability.

### A1. System implementation name

- **Original:** Working name was `clawdbot`.
- **Revised:** Implementation name is **TalisMan**. Repository/package naming uses `talisman` and `talisman_core` to avoid dependency-name collisions.
- **Reason:** User requested a cooler and more unique name while preserving the architecture.

### A2. LangGraph timing

- **Original final synthesis:** LangGraph was already recommended as the v1 orchestration substrate, but the implementation conversation considered whether to delay it.
- **Revised:** LangGraph is included from the initial implementation baseline.
- **Reason:** The user accepted LangGraph as a mandatory v1 element after reviewing the trade: durable workflow, checkpointing, pause/resume, and human approval gates are core rather than optional.

### A3. Structural modularity

- **Original final synthesis:** Architecture was modular, but enforcement was not elevated to a first-class success criterion.
- **Revised:** Structural modularity is mandatory and mechanically enforced with package boundaries, typed ports, Import Linter contracts, contract tests, and agent-facing repository instructions.
- **Reason:** Long-term self-improvability is as important as inter-model review. TalisMan must be safe for future Large Language Model (LLM) agents to modify.

### A4. Implementation target

- **Original final synthesis:** v1 implementation guide described the full architecture, while conversation explored a thinner first slice.
- **Revised:** Target the full Option C architecture, but implement through governed slices inside the final architecture from day one.
- **Reason:** The user wants to build the architecture as specified and use LLM coding agents to accelerate implementation while maintaining progress control.

### A5. Progress control documents

- **Original:** Five architecture and operations deliverables.
- **Revised:** Add master roadmap, slice backlog, agent coding protocol, progress ledger template, acceptance test plan, architecture guardrails, and audit summary.
- **Reason:** Option C requires explicit development governance to prevent drift and loss of momentum.
