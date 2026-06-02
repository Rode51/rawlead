-- O90: биржа → ingest → L1 (lag observability)

ALTER TABLE leads ADD COLUMN IF NOT EXISTS source_published_at TIMESTAMPTZ;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS l1_completed_at TIMESTAMPTZ;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS last_fetch_ok_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_leads_source_published_at
    ON leads (source_published_at DESC)
    WHERE source_published_at IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_leads_created_at_source
    ON leads (source, created_at DESC);
