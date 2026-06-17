"""Concrete adapter implementations of ports.

Houses the Telegram control plane, SQLite state store, gateway client, and
filesystem project workspace. Adapters implement ports and may depend on external
libraries. Business rules must not live here.
"""
