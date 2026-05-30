-- O65 delist + O66 legacy catch-up (Neon leads).

ALTER TABLE leads ADD COLUMN IF NOT EXISTS delist_reason TEXT;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS legacy_notified_at TIMESTAMPTZ;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS last_source_check_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_leads_legacy_pending
    ON leads (created_at ASC)
    WHERE is_visible = TRUE AND legacy_notified_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_leads_delist_recheck
    ON leads (last_source_check_at NULLS FIRST, created_at DESC)
    WHERE is_visible = TRUE AND delist_reason IS NULL;
