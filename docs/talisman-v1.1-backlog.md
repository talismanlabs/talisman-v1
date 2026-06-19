# TalisMan v1.1 improvement backlog

_Produced by TalisMan's bootstrap self-improvement spiral (slice S14.02)._

- **worker-subprocess-dedup** — Extract shared subprocess plumbing from the Claude/Codex worker adapters.
- **eventlog-idempotency-ports** — Add EventLog and idempotency ports before their first core consumer.
- **agent-family-normalize** — Normalize unknown agent names (case/whitespace) in review enforcement.
- **budget-toctou** — Close the budget check-then-record TOCTOU gap if the gateway becomes concurrent.
- **egress-squid-reconcile** — Reconcile host- vs domain-granular egress allowlists when wiring the proxy.
- **scoped-credentials** — Design host-side scoped/short-lived credential issuance for workers.
- **lessons-retrieval** — Build lessons/retrospective retrieval over the existing SQLite tables.
- **live-telegram** — Wire the live Telegram approval bot runtime.
- **live-run** — Full live self-improvement run (real workers, gateway, real spend).
