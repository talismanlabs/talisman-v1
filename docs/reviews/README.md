# Cross-family review artifacts

Every implementation slice requires an **opposite-family** review before it can be accepted
(guardrail #4). Claude-lead slices are reviewed by Codex CLI; Codex-lead slices are reviewed by
Claude. The review is recorded here as a YAML artifact named `<slice-id>.yaml` (for example
`S02.01.yaml`), committed in the slice's pull request.

Deterministic checks (`ruff`, `mypy`, `pytest`, `lint-imports`) run **before** review and are the
authoritative correctness gate; LLM review never substitutes for them (guardrail #5).

See [`REVIEW-TEMPLATE.yaml`](REVIEW-TEMPLATE.yaml) for the required structure, and
`scripts/codex_review.sh` for the Codex review wrapper.
