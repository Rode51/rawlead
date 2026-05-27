-- F-LOCAL: краткая суть заказа для /lenta/ (L1 ingest, не полный body)
ALTER TABLE leads ADD COLUMN IF NOT EXISTS task_summary TEXT;
