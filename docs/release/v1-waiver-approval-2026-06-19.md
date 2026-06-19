# TalisMan v1 — founder waiver approval & acceptance record

- **Date:** 2026-06-19
- **Approver:** Pat (founder / product owner)
- **Decision:** TalisMan **v1 is ACCEPTED**.

This is the durable approval artifact required by the acceptance plan (S15.02). It records
the founder's explicit sign-off on the deferred acceptance criteria, which formally accepts v1.

## Context

The S15.01 release candidate graded the AT-01..AT-20 acceptance plan honestly as
5 PASS / 8 component-verified / 7 waived — after an independent Codex cross-family review
blocked over-claimed PASS grades. Acceptance required (a) a live operator walkthrough of the
runtime behaviours and (b) the founder's explicit approval of the remaining waivers.

The live operator walkthrough was performed on 2026-06-19; its evidence is the founder audit
package at `founder-audit-package/2026-06-19/` (the command walkthrough and captured transcript
in `walkthrough/`). The founder reviewed that package and gave direction approving the waivers
and confirming the v1.1 P1 sequence.

## Approved waivers

The founder approved deferring the following five acceptance criteria to v1.1. The reason,
risk, and compensating control for each are recorded in `docs/release/v1-acceptance-checklist.md`.

| AT | Area | Disposition |
|---|---|---|
| AT-04 | Durable LangGraph checkpointer | Approved → **first v1.1 feature project** |
| AT-12 | Retry / jitter in the gateway | Approved, deferred to v1.1 |
| AT-16 | Automated retrospective generation | Approved, deferred to v1.1 |
| AT-17 | Lessons retrieval at intake | Approved, deferred to v1.1 |
| AT-19 | Automated incident dump | Approved, deferred to v1.1 |

## Direction recorded

1. **v1 is accepted** on the strength of the five end-to-end PASS criteria (AT-01/02/03/09/20),
   the live-demonstrated runtime behaviours, and these five approved waivers.
2. The five waived items become the **first v1.1 feature project**, starting with the durable
   checkpointer (AT-04).
3. The **P1 consolidation sequence is confirmed**: land the runtime pieces built live during the
   walkthrough (Telegram bot runtime, `--serve` service mode, egress-enforcing proxy), the
   Codex-invocation fix, and the credential-scrub wiring as governed slices (branch + PR +
   cross-family review) before building the waiver features.

## Scope note on the walkthrough evidence

The operator walkthrough demonstrated several component-verified behaviours using **prototype
runtime code built live, outside the governed slice loop**. That demonstration is recorded as
prototype / operator evidence — it is **not** reviewed release proof. Each such acceptance
criterion remains COMPONENT_VERIFIED and flips to PASS only when its v1.1-P1 code lands under
governance. v1 acceptance does not depend on those flips; it stands on the five PASS criteria
plus these approved waivers.
