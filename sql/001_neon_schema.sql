-- Neon Postgres: лиды радара + key/value настройки (фаза 0+).
-- Применить в Neon SQL Editor или: psql "$DATABASE_URL" -f sql/001_neon_schema.sql

CREATE TABLE IF NOT EXISTS leads (
    id BIGSERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    external_id TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    url TEXT NOT NULL DEFAULT '',
    budget_text TEXT NOT NULL DEFAULT '',
    ai_verdict TEXT,
    notified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (source, external_id)
);

CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads (created_at DESC);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
