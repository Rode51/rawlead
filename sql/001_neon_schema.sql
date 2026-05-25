-- Neon Postgres: SaaS-ready schema (фаза 3b).
--
-- Куда вставлять:
--   Neon Console → SQL Editor — блоки ниже (без psql, без $DATABASE_URL).
--   Терминал:  psql "%DATABASE_URL%" -f sql/001_neon_schema.sql
--
-- Таблица `leads` = эволюция `raw_leads` из NEON_SCHEMA.md (имя не меняем — совместимость ingest).

-- --- users (SaaS) ---
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    wp_user_id BIGINT UNIQUE,
    email TEXT,
    tg_chat_id BIGINT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Владелец dogfood: фиксированный id «#1» (UUID)
INSERT INTO users (id, email)
VALUES ('00000000-0000-0000-0000-000000000001'::uuid, 'owner@rawlead.local')
ON CONFLICT (id) DO NOTHING;

CREATE TABLE IF NOT EXISTS user_tags (
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    tag TEXT NOT NULL,
    weight REAL NOT NULL DEFAULT 1.0,
    PRIMARY KEY (user_id, tag)
);

CREATE INDEX IF NOT EXISTS idx_user_tags_user ON user_tags (user_id);

CREATE TABLE IF NOT EXISTS subscriptions (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    plan TEXT NOT NULL DEFAULT 'free',
    active_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id)
);

INSERT INTO subscriptions (user_id, plan)
VALUES ('00000000-0000-0000-0000-000000000001'::uuid, 'owner')
ON CONFLICT (user_id) DO NOTHING;

-- --- leads (raw_leads) ---
CREATE TABLE IF NOT EXISTS leads (
    id BIGSERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    external_id TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    body TEXT NOT NULL DEFAULT '',
    url TEXT NOT NULL DEFAULT '',
    budget_text TEXT NOT NULL DEFAULT '',
    ai_score SMALLINT,
    ai_verdict TEXT,
    lead_tags JSONB NOT NULL DEFAULT '[]'::jsonb,
    ai_reasons JSONB,
    is_visible BOOLEAN NOT NULL DEFAULT TRUE,
    content_hash TEXT,
    notified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (source, external_id)
);

CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads (created_at DESC);

-- Миграция существующей таблицы (фаза 0 → 3b) — до индексов по новым колонкам:
ALTER TABLE leads ADD COLUMN IF NOT EXISTS body TEXT NOT NULL DEFAULT '';
ALTER TABLE leads ADD COLUMN IF NOT EXISTS ai_score SMALLINT;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS lead_tags JSONB NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS ai_reasons JSONB;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS is_visible BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS content_hash TEXT;

CREATE INDEX IF NOT EXISTS idx_leads_is_visible ON leads (is_visible) WHERE is_visible = TRUE;
CREATE INDEX IF NOT EXISTS idx_leads_lead_tags ON leads USING GIN (lead_tags);
CREATE UNIQUE INDEX IF NOT EXISTS idx_leads_content_hash ON leads (content_hash);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
