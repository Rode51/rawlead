-- O84: deep-link cabinet login via @rawlead_bot (/start auth_<token>).

CREATE TABLE IF NOT EXISTS auth_bot_sessions (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token_hash   TEXT NOT NULL UNIQUE,
    expires_at   TIMESTAMPTZ NOT NULL,
    tg_user_id   BIGINT,
    tg_username  TEXT,
    tg_first_name TEXT,
    tg_photo_url TEXT,
    authorized_at TIMESTAMPTZ,
    consumed_at  TIMESTAMPTZ,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_auth_bot_sessions_expires
    ON auth_bot_sessions (expires_at);
