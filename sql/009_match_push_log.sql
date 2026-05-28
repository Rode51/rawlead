-- MATCH_PUSH dedupe: один push на user + lead (O28).

CREATE TABLE IF NOT EXISTS match_push_log (
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    lead_id BIGINT NOT NULL REFERENCES leads (id) ON DELETE CASCADE,
    sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, lead_id)
);

CREATE INDEX IF NOT EXISTS idx_match_push_log_sent ON match_push_log (sent_at DESC);
