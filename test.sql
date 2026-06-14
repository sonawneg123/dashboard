-- ============================================================
--  User Dashboard - Database Schema
--  Database: SQLite (compatible with MySQL/PostgreSQL with minor changes)
-- ============================================================

-- Drop table if it already exists (for fresh setup)
DROP TABLE IF EXISTS users;

-- Users table
CREATE TABLE users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    email       TEXT    NOT NULL UNIQUE,
    created_at  DATETIME DEFAULT (datetime('now'))
);

-- ── Sample data ──────────────────────────────────────────────
INSERT INTO users (name, email, created_at) VALUES
    ('Alice Johnson',  'alice@example.com',  datetime('now', '-5 days')),
    ('Bob Martinez',   'bob@example.com',    datetime('now', '-3 days')),
    ('Carol Singh',    'carol@example.com',  datetime('now', '-1 day'));
