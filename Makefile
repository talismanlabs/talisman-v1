# TalisMan build harness — developer ergonomics.
# These targets wrap uv + the deterministic-check gate so humans and the
# slice-runner use the exact same commands.

.PHONY: setup checks fmt hooks clean

# Create the dev environment (dev tools only; runtime deps are added per-slice).
setup:
	uv venv
	uv pip install -e ".[dev]"

# Run the full deterministic-check gate (ruff, ruff-format, mypy, pytest, lint-imports).
checks:
	./scripts/checks.sh

# Auto-format and auto-fix.
fmt:
	.venv/bin/ruff format .
	.venv/bin/ruff check --fix .

# Install git pre-commit hooks (optional convenience; CI is authoritative).
hooks:
	.venv/bin/pre-commit install

clean:
	rm -rf .venv .mypy_cache .ruff_cache .pytest_cache
