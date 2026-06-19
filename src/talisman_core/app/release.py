"""v1 release-candidate acceptance results (slice S15.01).

Encodes the outcome of the AT-01..AT-20 acceptance test plan against the built system as
structured data, renders the release checklist, and is validated by tests (every
acceptance test is accounted for; every waiver carries the required fields).

This is an HONEST release-candidate accounting, corrected after an independent Codex
cross-family review challenged over-claimed PASS grades (see docs/reviews/S15.01.yaml).
The lead cannot honestly grade its own work as broadly passing; only end-to-end-proven
criteria are PASS.

Status legend:
- PASS: verified end-to-end (CI checks, or on-disk evidence of the actual behavior).
- COMPONENT_VERIFIED: the component is built and unit-tested, but is NOT yet integrated
  into the running system and/or not live-verified — the AT's full behavior is unproven.
  These are resolved by integration wiring plus the operator walkthrough.
- WAIVED: the feature or runtime is genuinely not built; deferred to v1.1, with a waiver.

Acceptance status: TalisMan v1 is a RELEASE CANDIDATE, not yet accepted. Acceptance
requires (a) the operator walkthrough to verify the COMPONENT_VERIFIED items end-to-end and
(b) the user's explicit approval of every waiver.
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


# Waivers await the user's explicit approval during the walkthrough; until then the
# release is not accepted (the acceptance plan requires real user approval per waiver).
_PENDING = "Pat — PENDING approval (operator walkthrough)"

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
        "pytest: 100 tests pass (CI).",
    ),
    AcceptanceResult(
        "AT-04",
        "LangGraph pause/resume",
        AcceptanceStatus.WAIVED,
        "In-process gate interrupt/resume verified (workflow tests + S14.02); but the "
        "checkpointer is in-memory MemorySaver, so resume does NOT survive a process restart.",
        Waiver(
            "Durable LangGraph checkpointer (SqliteSaver) not wired; only in-memory MemorySaver.",
            "A crash mid-gate loses the paused workflow checkpoint.",
            "Single supervised session in v1; gates are re-requestable; durable checkpointer is "
            "in the v1.1 backlog.",
            _PENDING,
        ),
    ),
    AcceptanceResult(
        "AT-05",
        "Telegram allowlist",
        AcceptanceStatus.WAIVED,
        "Allowlist policy built + unit-tested (adapters/telegram/allowlist.py), but the live "
        "Telegram bot runtime (command handling + logging) is NOT built.",
        Waiver(
            "Live Telegram bot runtime not built; only the allowlist policy exists.",
            "No running command surface to reject a non-allowlisted account against.",
            "The allowlist policy is ready to wire; live-telegram is in the v1.1 backlog.",
            _PENDING,
        ),
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
        "workers/claude_code.py implements WorkerPort (unit-tested). No live controlled-slice "
        "run yet (transcript/artifacts) — pending the walkthrough.",
    ),
    AcceptanceResult(
        "AT-08",
        "Codex CLI worker",
        AcceptanceStatus.COMPONENT_VERIFIED,
        "workers/codex_cli.py implements WorkerPort (unit-tested). Strong practical evidence: "
        "Codex CLI ran all 15 cross-family reviews this build. No live run THROUGH the adapter yet.",
    ),
    AcceptanceResult(
        "AT-09",
        "Cross-family review",
        AcceptanceStatus.PASS,
        "25 structured review artifacts in docs/reviews/ — every slice reviewed by the opposite "
        "family, incl. this S15.01 review which blocked an over-claimed release grading.",
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
        AcceptanceStatus.WAIVED,
        "Full-jitter retry / Retry-After handling not implemented in the gateway client.",
        Waiver(
            "Retry-with-jitter was not built in v1.",
            "Transient provider HTTP errors are not auto-retried.",
            "Manual re-run; low frequency at single-session scale; in the v1.1 backlog.",
            _PENDING,
        ),
    ),
    AcceptanceResult(
        "AT-13",
        "Credential isolation",
        AcceptanceStatus.COMPONENT_VERIFIED,
        "security/credentials.worker_environment scrubs long-lived keys (unit-tested, S10.01), "
        "but it is NOT wired into the worker subprocess runners — keys are not yet proven absent "
        "from a real worker environment (Codex S15.01 finding).",
    ),
    AcceptanceResult(
        "AT-14",
        "Egress allowlist",
        AcceptanceStatus.WAIVED,
        "Default-deny egress policy built + unit-tested incl. bypass classes (security/egress.py), "
        "but the enforcing proxy (squid) is NOT deployed.",
        Waiver(
            "Egress-enforcing proxy not deployed; only the host-side allowlist policy exists.",
            "No proxy actually blocks a disallowed egress at runtime.",
            "The policy is ready to wire to squid; proxy deployment is in the v1.1 backlog.",
            _PENDING,
        ),
    ),
    AcceptanceResult(
        "AT-15",
        "SQLite persistence",
        AcceptanceStatus.COMPONENT_VERIFIED,
        "Event log + schema persist across connections (unit-tested, S04). But there is NO "
        "StatePort project-state store and no service-restart evidence (Codex S15.01 finding) — "
        "full project-state survival is unproven.",
    ),
    AcceptanceResult(
        "AT-16",
        "Retrospective",
        AcceptanceStatus.WAIVED,
        "Automated markdown retrospective generation not implemented.",
        Waiver(
            "Retro generation was not built in v1 (the memory/ layer is empty).",
            "No automatic retrospective at project close.",
            "Manual retro; the lessons table exists; in the v1.1 backlog.",
            _PENDING,
        ),
    ),
    AcceptanceResult(
        "AT-17",
        "Lessons retrieval",
        AcceptanceStatus.WAIVED,
        "Lessons retrieval/surfacing at intake not implemented (S14.03 deferred).",
        Waiver(
            "Lessons retrieval was not built in v1.",
            "Relevant lessons are not surfaced during intake.",
            "The lessons schema exists; retrieval is the lessons-retrieval item in the v1.1 backlog.",
            _PENDING,
        ),
    ),
    AcceptanceResult(
        "AT-18",
        "systemd recovery",
        AcceptanceStatus.COMPONENT_VERIFIED,
        "Unit files built; Restart=on-failure + gateway-first ordering verified, byte-match "
        "canonical (S13.01). No live kill-and-restart yet — pending systemd install (walkthrough).",
    ),
    AcceptanceResult(
        "AT-19",
        "Incident dump",
        AcceptanceStatus.WAIVED,
        "Automated catastrophic-halt state dump not implemented.",
        Waiver(
            "Automated incident-dump trigger was not built in v1.",
            "No automatic state+log dump on catastrophic halt.",
            "The operational runbook documents a manual incident-dump procedure; automation in v1.1.",
            _PENDING,
        ),
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
        "# TalisMan v1 acceptance checklist (release candidate)",
        "",
        "_Produced by slice S15.01 against the AT-01..AT-20 acceptance test plan, corrected after "
        "the independent Codex cross-family review (docs/reviews/S15.01.yaml) blocked over-claimed "
        "PASS grades._",
        "",
        f"**Summary:** {counts[AcceptanceStatus.PASS]} pass · "
        f"{counts[AcceptanceStatus.COMPONENT_VERIFIED]} component-verified (await integration + "
        f"operator walkthrough) · {counts[AcceptanceStatus.WAIVED]} waived to v1.1.",
        "",
        "**Not yet accepted.** Acceptance requires the operator walkthrough (to verify the "
        "component-verified items end-to-end) and the user's explicit approval of every waiver.",
        "",
        "| Test | Area | Status | Evidence |",
        "|---|---|---|---|",
    ]
    lines.extend(
        f"| {r.test_id} | {r.area} | {r.status.value} | {r.evidence} |" for r in ACCEPTANCE_RESULTS
    )
    waived = [r for r in ACCEPTANCE_RESULTS if r.waiver is not None]
    if waived:
        lines.extend(["", "## Waivers (await user approval)", ""])
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
