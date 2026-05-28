-- O23: inbox откликов в /cabinet/ (per user, soft-delete)
CREATE TABLE IF NOT EXISTS user_lead_replies (
    user_id    UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    lead_id    INTEGER NOT NULL REFERENCES leads (id) ON DELETE CASCADE,
    reply_draft TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    PRIMARY KEY (user_id, lead_id)
);

CREATE INDEX IF NOT EXISTS idx_user_lead_replies_user_active
    ON user_lead_replies (user_id, created_at DESC)
    WHERE deleted_at IS NULL;
