-- O195: decay + interaction tracking on user_tags
ALTER TABLE user_tags
  ADD COLUMN IF NOT EXISTS last_active_at TIMESTAMPTZ DEFAULT NOW(),
  ADD COLUMN IF NOT EXISTS interaction_count INT DEFAULT 0;
