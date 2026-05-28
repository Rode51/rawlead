-- 3f-B: статус подписки (is_active, paused_until)
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS paused_until TIMESTAMPTZ;

-- dogfood owner + legacy pro rows
UPDATE subscriptions
SET is_active = TRUE
WHERE plan IN ('owner', 'pro', 'agent')
  AND is_active = FALSE;
