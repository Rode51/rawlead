-- O57: one in-flight L2 per lead (shared draft thundering herd)
CREATE TABLE IF NOT EXISTS lead_draft_jobs (
    lead_id    INTEGER PRIMARY KEY REFERENCES leads (id) ON DELETE CASCADE,
    status     TEXT NOT NULL DEFAULT 'pending',
    error_msg  TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT lead_draft_jobs_status_check CHECK (status IN ('pending', 'failed'))
);

CREATE INDEX IF NOT EXISTS idx_lead_draft_jobs_pending
    ON lead_draft_jobs (updated_at)
    WHERE status = 'pending';
