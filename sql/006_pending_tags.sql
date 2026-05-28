-- E2b: теги L1 вне canonical pool → очередь на review (не в UI)
CREATE TABLE IF NOT EXISTS pending_tags (
    id SERIAL PRIMARY KEY,
    tag TEXT NOT NULL,
    category TEXT,
    first_seen_at TIMESTAMPTZ DEFAULT NOW(),
    seen_count INT DEFAULT 1,
    UNIQUE(tag)
);

CREATE INDEX IF NOT EXISTS idx_pending_tags_seen ON pending_tags (seen_count DESC, first_seen_at DESC);
