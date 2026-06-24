-- BOT-NOTIFY-START: dedup owner ping on first /start per tg_user_id
ALTER TABLE users ADD COLUMN IF NOT EXISTS bot_start_owner_notified_at TIMESTAMPTZ;
