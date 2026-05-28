-- MATCH-PUSH-V2 (O30): per-user push threshold + enable toggle.

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS push_min_match INT NOT NULL DEFAULT 60,
    ADD COLUMN IF NOT EXISTS push_enabled   BOOL NOT NULL DEFAULT TRUE;
