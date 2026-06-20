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
PASS as the v1.1-P1 governed slices land. v1.1-P1 update: AT-13 (credential isolation) is the
first to harden to PASS — S16.03 wired the credential scrub into the worker subprocess runner with
a real-child CI test.
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
        AcceptanceStatus.WAIVED,
        "In-process gate interrupt/resume verified (workflow tests + S14.02); but the "
        "checkpointer is in-memory MemorySaver, so resume does NOT survive a process restart.",
        Waiver(
            "Durable LangGraph checkpointer (SqliteSaver) not wired; only in-memory MemorySaver.",
            "A crash mid-gate loses the paused workflow checkpoint.",
            "Single supervised session in v1; gates are re-requestable; durable checkpointer is "
            "the first v1.1 feature project.",
            _APPROVED,
        ),
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
        "workers/codex_cli.py implements WorkerPort (unit-tested); Codex CLI ran all 25 "
        "cross-family reviews this build. A live run THROUGH the adapter needs the corrected "
        f"invocation (prompt on stdin + --skip-git-repo-check). {_PROTOTYPE} (the one-line "
        "adapter fix is the first v1.1-P1 slice).",
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
        AcceptanceStatus.WAIVED,
        "Full-jitter retry / Retry-After handling not implemented in the gateway client.",
        Waiver(
            "Retry-with-jitter was not built in v1.",
            "Transient provider HTTP errors are not auto-retried.",
            "Manual re-run; low frequency at single-session scale; in the v1.1 backlog.",
            _APPROVED,
        ),
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
        "Default-deny egress policy built + unit-tested incl. bypass classes (security/egress.py). "
        "A CONNECT proxy calling is_allowed (tunnelling api.anthropic.com, blocking "
        f"evil-exfiltration.example.com) was shown in the walkthrough. {_PROTOTYPE} (the enforcing "
        "proxy is a v1.1-P1 slice).",
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
        AcceptanceStatus.WAIVED,
        "Automated markdown retrospective generation not implemented.",
        Waiver(
            "Retro generation was not built in v1 (the memory/ layer is empty).",
            "No automatic retrospective at project close.",
            "Manual retro; the lessons table exists; in the v1.1 backlog.",
            _APPROVED,
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
            "The lessons schema exists; retrieval is in the v1.1 backlog.",
            _APPROVED,
        ),
    ),
    AcceptanceResult(
        "AT-18",
        "systemd recovery",
        AcceptanceStatus.COMPONENT_VERIFIED,
        "Unit files built; Restart=on-failure + gateway-first ordering verified byte-match canonical "
        "(S13.01). A live kill -9 → auto-restart (via `--serve`) was shown in the walkthrough. "
        f"{_PROTOTYPE} (the --serve service runtime is a v1.1-P1 slice).",
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
            _APPROVED,
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
        "proof; each flips to PASS as its v1.1-P1 code lands under governance (AT-13 was the first, via "
        "S16.03).",
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
