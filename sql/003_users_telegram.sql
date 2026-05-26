-- P4: Telegram Login → users (Neon SQL Editor или psql).

ALTER TABLE users ADD COLUMN IF NOT EXISTS tg_user_id BIGINT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS tg_username TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS tg_first_name TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS tg_photo_url TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_tg_user_id ON users (tg_user_id) WHERE tg_user_id IS NOT NULL;
