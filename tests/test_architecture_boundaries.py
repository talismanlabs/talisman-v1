"""Architecture smoke test.

Import Linter performs the authoritative import-boundary check (run via
``lint-imports``; see ``.importlinter``). This pytest file keeps an explicit,
human-visible reminder in the normal test suite that architecture boundaries are
verified on purpose, not by accident.
"""


def test_architecture_boundaries_are_enforced_by_import_linter() -> None:
    """Document, in the pytest suite, where boundary enforcement actually happens."""
    assert True
