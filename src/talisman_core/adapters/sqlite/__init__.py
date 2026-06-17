"""SQLite adapter: the shared state-database engine and schema migrations.

SQLite is infrastructure, so it lives in the adapters layer. Core layers (domain,
workflow, policies) reach persistence through ports such as ``StatePort`` and
``MemoryPort`` and must never import ``sqlite3`` directly. The shared state database
(``TalisMan.sqlite3``) holds project state, gate events, scheduler events, and the
lessons store; its schema is applied idempotently by ``migrations.initialize_database``.
"""
