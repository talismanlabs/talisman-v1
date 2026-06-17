"""Smoke test: the package imports cleanly and exposes a version string."""

import talisman_core


def test_package_imports_and_has_version() -> None:
    """``talisman_core`` must import and expose a non-empty ``__version__``."""
    assert isinstance(talisman_core.__version__, str)
    assert talisman_core.__version__
