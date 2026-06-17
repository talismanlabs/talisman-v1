"""TalisMan core package.

TalisMan v1 is a local-first, approval-gated AI orchestration system. This package
holds the orchestrator's modular layers (domain, ports, workflow, policies,
adapters, workers, memory, security, scheduler, observability, app). Module
boundaries between these layers are enforced mechanically by Import Linter; see
``.importlinter`` and ``docs/architecture-guardrails.md``.
"""

__version__ = "0.1.0"
