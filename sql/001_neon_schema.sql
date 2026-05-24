-- Neon Postgres: лиды радара + key/value настройки (фаза 0+).
--
-- Куда вставлять:
--   Neon Console → SQL Editor — только блоки SQL ниже (без psql, без $DATABASE_URL).
--   Терминал:  psql "%DATABASE_URL%" -f sql/001_neon_schema.sql

CREATE TABLE IF NOT EXISTS leads (
    id BIGSERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    external_id TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    url TEXT NOT NULL DEFAULT '',
    budget_text TEXT NOT NULL DEFAULT '',
    content_hash TEXT,
    ai_verdict TEXT,
    notified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (source, external_id)
);

CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads (created_at DESC);

-- Миграция существующей таблицы (если leads уже была без content_hash):
ALTER TABLE leads ADD COLUMN IF NOT EXISTS content_hash TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_leads_content_hash ON leads (content_hash);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
