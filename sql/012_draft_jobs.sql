-- O56: async on-demand draft status (pending / failed); ready → user_lead_replies
CREATE TABLE IF NOT EXISTS draft_jobs (
    user_id    UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    lead_id    INTEGER NOT NULL REFERENCES leads (id) ON DELETE CASCADE,
    status     TEXT NOT NULL DEFAULT 'pending',
    error_msg  TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, lead_id),
    CONSTRAINT draft_jobs_status_check CHECK (status IN ('pending', 'failed'))
);

CREATE INDEX IF NOT EXISTS idx_draft_jobs_pending
    ON draft_jobs (updated_at)
    WHERE status = 'pending';
