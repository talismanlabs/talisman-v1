-- SQLite schema for TalisMan v1 (ported from talisman-v1-config-templates.md).
-- SQLite replaces the draft CSV store so lesson updates are transactional and auditable.
-- Every statement is idempotent (IF NOT EXISTS), so the schema is safe to re-apply.

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS projects (
    project_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    tier TEXT NOT NULL CHECK (tier IN ('lightweight', 'full_spiral')),
    status TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS lessons (
    lesson_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    domain_tags TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    statement TEXT NOT NULL,
    detail_ref TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active', 'retracted', 'superseded')),
    date TEXT NOT NULL,
    supersedes_lesson_id TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supersedes_lesson_id) REFERENCES lessons(lesson_id)
);

CREATE TABLE IF NOT EXISTS lesson_audit (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id TEXT NOT NULL,
    action TEXT NOT NULL,
    reason TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lesson_id) REFERENCES lessons(lesson_id)
);

CREATE TABLE IF NOT EXISTS gate_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    gate_name TEXT NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    state TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scheduler_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    priority TEXT NOT NULL,
    enqueued_at TEXT NOT NULL,
    started_at TEXT,
    total_wait_seconds INTEGER NOT NULL DEFAULT 0,
    last_wait_reason TEXT
);

CREATE TABLE IF NOT EXISTS events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS budget_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT,
    cost_usd REAL NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_events_project_id_event_id
ON events (project_id, event_id);

CREATE INDEX IF NOT EXISTS idx_budget_events_created_at
ON budget_events (created_at);
