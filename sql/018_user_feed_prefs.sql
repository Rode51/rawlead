-- O116-WP-FEED R1: persist feed sort / min_match / category per user
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS feed_prefs JSONB DEFAULT NULL;
