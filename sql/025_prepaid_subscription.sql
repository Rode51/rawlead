-- O283: оплата Premium во время trial — paid_active_until стартует после trial.active_until
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS paid_active_until TIMESTAMPTZ;
