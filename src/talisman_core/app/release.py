"""v1 acceptance results (slice S15.01 candidate → S15.02 formal acceptance).

Encodes the outcome of the AT-01..AT-20 acceptance test plan against the built system as
structured data, renders the release checklist, and is validated by tests (every
acceptance test is accounted for; every waiver carries the required fields).

This is an HONEST accounting. The release-candidate grading (S15.01) was corrected after an
independent Codex cross-family review challenged over-claimed PASS grades
(docs/reviews/S15.01.yaml): the lead cannot honestly grade its own work as broadly passing.
S15.02 then records the founder's formal acceptance (docs/release/v1-waiver-approval-2026-06-19.md)
but deliberately does NOT inflate grades: the only PASS criteria remain those proven end-to-end
through merged code + CI/artifacts.

Status legend:
- PASS: proven end-to-end through merged code plus CI checks or on-disk artifacts.
- COMPONENT_VERIFIED: the component is built and unit-tested. Several were also demonstrated in
  the 2026-06-19 operator walkthrough using PROTOTYPE runtime code built live OUTSIDE the
  governed slice loop — that is recorded as prototype/operator evidence, NOT reviewed release
  proof. Each flips to PASS only when its v1.1-P1 runtime code lands under governance.
- WAIVED: the feature/runtime is genuinely not built; deferred to v1.1 with an approved waiver.

Acceptance status: TalisMan v1 is ACCEPTED (2026-06-19; see the approval artifact above). The
founder approved the five remaining waivers after the operator walkthrough. Acceptance stood on
five end-to-end PASS criteria (as of 2026-06-19) plus the five approved waivers — it does NOT
depend on the prototype walkthrough demonstrations, which are tracked separately and harden into
PASS as the v1.1-P1 governed slices land. v1.1-P1 hardenings so far: AT-13 (credential isolation,
S16.03, real-child CI test), AT-04 (durable SqliteSaver checkpointer surviving a restart, S16.07), and
AT-12 (full-jitter gateway retry with Retry-After, S16.08), and AT-16 (automatic retrospective at
project close, S16.11), AT-19 (automatic incident dump on catastrophic halt, S16.12), and AT-17
(durable lessons surfaced at intake, S16.13) — every v1 waiver now hardened to PASS.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AcceptanceStatus(str, Enum):
    """Outcome of one acceptance test against the built v1 system."""

    PASS = "pass"
    COMPONENT_VERIFIED = "component_verified"
    WAIVED = "waived"


@dataclass(frozen=True)
class Waiver:
    """A documented waiver for a deferred acceptance test (per the acceptance plan)."""

    reason: str
    risk: str
    compensating_control: str
    approval: str


@dataclass(frozen=True)
class AcceptanceResult:
    """The result of one acceptance test, with evidence and any waiver."""

    test_id: str
    area: str
    status: AcceptanceStatus
    evidence: str
    waiver: Waiver | None = None


# The founder approved every remaining waiver on 2026-06-19, recorded in the durable artifact
# docs/release/v1-waiver-approval-2026-06-19.md, which formally accepts v1.
_APPROVED = "Pat (founder) — APPROVED 2026-06-19 (docs/release/v1-waiver-approval-2026-06-19.md)"

# Prototype/operator-walkthrough evidence (built live OUTSIDE governance; not reviewed proof).
_PROTOTYPE = (
    "Prototype/operator evidence only (built live outside the governed slice loop, 2026-06-19; "
    "transcript: founder-audit-package/2026-06-19/walkthrough/part2-live-transcript.txt) — NOT "
    "reviewed release proof; flips to PASS when its governed v1.1-P1 code lands."
)

ACCEPTANCE_RESULTS: tuple[AcceptanceResult, ...] = (
    AcceptanceResult(
        "AT-01",
        "Architecture",
        AcceptanceStatus.PASS,
        "lint-imports: 5 contracts kept, 0 broken (CI).",
    ),
    AcceptanceResult(
        "AT-02",
        "Static checks",
        AcceptanceStatus.PASS,
        "ruff check + mypy --strict pass on every PR (CI).",
    ),
    AcceptanceResult(
        "AT-03",
        "Unit tests",
        AcceptanceStatus.PASS,
        "pytest: 100+ tests pass (CI).",
    ),
    AcceptanceResult(
        "AT-04",
        "LangGraph pause/resume",
        AcceptanceStatus.PASS,
        "Durable resume survives a process restart (hardened from its v1 waiver in S16.07): "
        "composition.build_sqlite_checkpointer wires a SqliteSaver, and a CI test "
        "(tests/app/test_durable_checkpointer.py) pauses a gate under one checkpointer and resumes it "
        "under a BRAND-NEW checkpointer on the same on-disk DB — recovering the paused run from disk "
        "(a contrast test confirms MemorySaver loses it).",
    ),
    AcceptanceResult(
        "AT-05",
        "Telegram allowlist",
        AcceptanceStatus.COMPONENT_VERIFIED,
        "allowlist policy built + unit-tested (adapters/telegram/allowlist.py). The live "
        "@Talisman0_bot runtime accepting an allowlisted account and rejecting others was shown "
        f"in the operator walkthrough. {_PROTOTYPE} (bot runtime: adapters/telegram/bot.py).",
    ),
    AcceptanceResult(
        "AT-06",
        "Approval idempotency",
        AcceptanceStatus.COMPONENT_VERIFIED,
        "SQLiteApprovalIdempotency dedups a repeated key (INSERT-once; unit-tested, ADR-0003). "
        "NOT yet wired into a live approval flow — integrated single-advance behavior unproven.",
    ),
    AcceptanceResult(
        "AT-07",
        "Claude Code worker",
        AcceptanceStatus.COMPONENT_VERIFIED,
        "workers/claude_code.py implements WorkerPort (unit-tested). A live controlled-slice run "
        f"was shown in the operator walkthrough. {_PROTOTYPE} (runner wiring is v1.1-P1).",
    ),
    AcceptanceResult(
        "AT-08",
        "Codex CLI worker",
        AcceptanceStatus.COMPONENT_VERIFIED,
        "workers/codex_cli.py implements WorkerPort and now uses the invocation Codex CLI actually "
        "requires — prompt on stdin + --skip-git-repo-check (S16.05, unit-tested incl. a real-subprocess "
        "stdin test); Codex CLI also ran the cross-family reviews throughout this build. Flips to PASS on "
        "a live run through the adapter (real Codex, not exercisable in CI).",
    ),
    AcceptanceResult(
        "AT-09",
        "Cross-family review",
        AcceptanceStatus.PASS,
        "25 structured review artifacts in docs/reviews/ — every slice reviewed by the opposite "
        "family, incl. the S15.01 review which blocked an over-claimed release grading.",
    ),
    AcceptanceResult(
        "AT-10",
        "Budget cap",
        AcceptanceStatus.COMPONENT_VERIFIED,
        "SQLiteBudgetAdapter pauses (BudgetCircuitOpen) on a simulated hard-cap breach "
        "(unit-tested, ADR-0004). Not wired to a live model path or a user-alert path.",
    ),
    AcceptanceResult(
        "AT-11",
        "Gateway pre-call accounting",
        AcceptanceStatus.COMPONENT_VERIFIED,
        "check_call blocks at the cap before a call (unit-tested). Not integrated with a live "
        "model request path.",
    ),
    AcceptanceResult(
        "AT-12",
        "Retry jitter",
        AcceptanceStatus.PASS,
        "Full-jitter retry with Retry-After handling implemented in the gateway client "
        "(adapters/gateway_client.retrying_transport, wired into GatewayClient.over_http) and "
        "CI-tested: transport errors and 429 / any 5xx retry with full-jitter backoff capped at "
        "max_delay (a numeric Retry-After is honored as a minimum, not truncated); non-retryable 4xx "
        "surface immediately, and attempts exhaust then re-raise. Hardened from its v1 waiver in S16.08.",
    ),
    AcceptanceResult(
        "AT-13",
        "Credential isolation",
        AcceptanceStatus.PASS,
        "security/credentials.worker_environment is wired (S16.03) as the single, unbypassable spawn "
        "point in workers/_subprocess.default_runner used by both worker adapters; a CI contract test "
        "spawns a REAL child process and proves ANTHROPIC_API_KEY / OPENAI_API_KEY / GITHUB_TOKEN are "
        "absent from the worker environment (D6).",
    ),
    AcceptanceResult(
        "AT-14",
        "Egress allowlist",
        AcceptanceStatus.COMPONENT_VERIFIED,
        "Two of three parts done, honestly. (1) Decision point: the gatekeeper CONNECT proxy enforces "
        "the allowlist (adapters/egress_proxy.py, ADR-0006, S16.04; 403-vs-tunnel integration-tested). "
        "(2) Containment: workers/_container.py runs a worker in a rootless-podman container on an "
        "--internal network, and an integration test proves such a container CANNOT egress — a kernel "
        "routing failure, not cooperation (ADR-0007, S16.06). (3) Remaining for PASS: the composition "
        "root must actually run real workers through the container runner with the proxy as their only "
        "off-network route, proven end-to-end (allow + deny + no-bypass). Until that wiring lands this "
        "stays component-verified — no inflation.",
    ),
    AcceptanceResult(
        "AT-15",
        "SQLite persistence",
        AcceptanceStatus.COMPONENT_VERIFIED,
        "Event log + schema persist across connections (unit-tested, S04); a fresh-handle restart "
        f"was shown in the walkthrough. {_PROTOTYPE} A StatePort project-state store remains a v1.1 "
        "item; flips to PASS when that store lands.",
    ),
    AcceptanceResult(
        "AT-16",
        "Retrospective",
        AcceptanceStatus.PASS,
        "app/project_run.generate_retrospective renders a markdown retrospective (outcome, phases "
        "completed, gates fired, artifacts) and run_project produces it automatically at every project "
        "close; CI-tested (tests/app/test_project_run.py). Hardened from its v1 waiver in S16.11.",
    ),
    AcceptanceResult(
        "AT-17",
        "Lessons retrieval",
        AcceptanceStatus.PASS,
        "adapters/sqlite.SQLiteMemoryStore implements MemoryPort (durable lessons + retrospectives in "
        "the shared state DB) and run_project retrieves active lessons relevant to the spec's domain_tags "
        "and surfaces them at intake (logged + returned on the result); CI-tested "
        "(tests/adapters/test_memory_store.py, tests/app/test_project_run.py). Hardened from its v1 "
        "waiver in S16.13.",
    ),
    AcceptanceResult(
        "AT-18",
        "systemd recovery",
        AcceptanceStatus.COMPONENT_VERIFIED,
        "Unit files built; Restart=on-failure + gateway-first ordering verified byte-match canonical "
        "(S13.01). The `--serve` service runtime the unit launches is now built + governed (S16.10): a "
        "signal-driven heartbeat loop, unit-tested (starts, beats, stops cleanly on SIGTERM/SIGINT). The "
        "live kill -9 → auto-restart needs a real `systemd --user` and is operator-verified, not CI; it "
        "flips to PASS at that operator step.",
    ),
    AcceptanceResult(
        "AT-19",
        "Incident dump",
        AcceptanceStatus.PASS,
        "observability/incident.write_incident_dump writes a timestamped, secret-redacted markdown dump "
        "(reason + recent log lines stripped via redact_secrets; filesystem-safe filename) and "
        "run_project triggers it (best-effort) automatically when a run halts "
        "catastrophically — an unhandled error escaping the spiral — before re-raising; CI-tested "
        "(tests/app/test_project_run.py). Hardened from its v1 waiver in S16.12.",
    ),
    AcceptanceResult(
        "AT-20",
        "Bootstrap project",
        AcceptanceStatus.PASS,
        "S14.02 ran the governed v1.1-planning spiral to completion through both gates; produced "
        "docs/talisman-v1.1-backlog.md.",
    ),
)


def status_counts() -> dict[AcceptanceStatus, int]:
    """Count acceptance results by status."""
    counts = {status: 0 for status in AcceptanceStatus}
    for result in ACCEPTANCE_RESULTS:
        counts[result.status] += 1
    return counts


def render_acceptance_checklist() -> str:
    """Render the v1 acceptance checklist as markdown — the release deliverable."""
    counts = status_counts()
    lines = [
        "# TalisMan v1 acceptance checklist — ACCEPTED 2026-06-19",
        "",
        "_Produced by slice S15.01 against the AT-01..AT-20 acceptance test plan (corrected after the "
        "independent Codex cross-family review blocked over-claimed PASS grades), then formally "
        "accepted in S15.02. Founder approval: docs/release/v1-waiver-approval-2026-06-19.md._",
        "",
        f"**Summary:** v1 ACCEPTED (2026-06-19). {counts[AcceptanceStatus.PASS]} criteria PASS "
        f"end-to-end (CI/artifacts) · {counts[AcceptanceStatus.COMPONENT_VERIFIED]} component-verified "
        "(several also shown live in the operator walkthrough as prototype evidence; hardening tracked "
        f"as v1.1-P1) · {counts[AcceptanceStatus.WAIVED]} waived with founder approval.",
        "",
        "**ACCEPTED 2026-06-19** on five end-to-end PASS criteria plus the five founder-approved waivers "
        "(durable approval artifact: docs/release/v1-waiver-approval-2026-06-19.md). The operator "
        "walkthrough demonstrated several component-verified behaviours using prototype runtime code "
        "built live outside governance — recorded as prototype/operator evidence, not reviewed release "
        "proof; each flips to PASS as its v1.1-P1 code lands under governance (AT-13 via S16.03, then "
        "AT-04 via S16.07, AT-12 via S16.08, AT-16 via S16.11, AT-19 via S16.12, then AT-17 via S16.13).",
        "",
        "| Test | Area | Status | Evidence |",
        "|---|---|---|---|",
    ]
    lines.extend(
        f"| {r.test_id} | {r.area} | {r.status.value} | {r.evidence} |" for r in ACCEPTANCE_RESULTS
    )
    waived = [r for r in ACCEPTANCE_RESULTS if r.waiver is not None]
    if waived:
        lines.extend(["", "## Waivers (approved by founder 2026-06-19)", ""])
        for r in waived:
            waiver = r.waiver
            assert waiver is not None
            lines.extend(
                [
                    f"### {r.test_id} — {r.area}",
                    f"- **Reason:** {waiver.reason}",
                    f"- **Risk:** {waiver.risk}",
                    f"- **Compensating control:** {waiver.compensating_control}",
                    f"- **Approval:** {waiver.approval}",
                    "",
                ]
            )
    return "\n".join(lines) + "\n"
