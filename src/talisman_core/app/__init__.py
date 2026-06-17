"""Composition root: dependency wiring and process startup.

The application layer connects concrete adapters and workers to the ports the core
depends on, then starts the process. This is the only layer permitted to import
concrete implementations across boundaries; it contains no business rules.
"""
