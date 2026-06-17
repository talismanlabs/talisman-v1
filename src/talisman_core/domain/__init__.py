"""Pure domain model: projects, gates, artifacts, review results, and invariants.

The domain layer is the innermost ring. It must not import adapters, workers,
security, memory, observability, or app wiring (enforced by Import Linter). Keeping
the domain pure makes the core concepts portable across interfaces and future
implementations.
"""
