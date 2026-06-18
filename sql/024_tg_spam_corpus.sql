-- O202: owner-marked TG spam corpus for filter tuning.

CREATE TABLE IF NOT EXISTS tg_spam_corpus (
    id         BIGSERIAL PRIMARY KEY,
    lead_id    BIGINT NOT NULL,
    source     TEXT NOT NULL,
    title      TEXT NOT NULL DEFAULT '',
    body       TEXT NOT NULL DEFAULT '',
    chat_id    BIGINT,
    marked_by  UUID NOT NULL,
    marked_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    category   TEXT
);

CREATE INDEX IF NOT EXISTS idx_tg_spam_corpus_marked_at
    ON tg_spam_corpus (marked_at DESC);

CREATE INDEX IF NOT EXISTS idx_tg_spam_corpus_lead_id
    ON tg_spam_corpus (lead_id);
