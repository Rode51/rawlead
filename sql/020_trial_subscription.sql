-- O107: Trial Premium 3 дня (1× на user_id)
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS trial_used_at TIMESTAMPTZ;
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS trial_remind_24h_at TIMESTAMPTZ;
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS trial_ended_notified_at TIMESTAMPTZ;
