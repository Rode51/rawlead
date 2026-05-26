-- P7: категория заказа из биржи (vision §0i)
-- Neon Console / psql "%DATABASE_URL%" -f sql/002_leads_category.sql

ALTER TABLE leads ADD COLUMN IF NOT EXISTS category TEXT;

CREATE INDEX IF NOT EXISTS idx_leads_category ON leads (category)
    WHERE category IS NOT NULL;
