-- O105-w1: ручная оплата Premium (СБП / crypto) — pending + owner approve.

CREATE TABLE IF NOT EXISTS payment_pending (
    id BIGSERIAL PRIMARY KEY,
    tg_user_id BIGINT NOT NULL,
    tg_chat_id BIGINT,
    user_id UUID REFERENCES users (id) ON DELETE SET NULL,
    method TEXT NOT NULL CHECK (method IN ('sbp', 'crypto')),
    amount_rub INT NOT NULL,
    amount_usdt NUMERIC(18, 6),
    amount_ton NUMERIC(18, 6),
    rate_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'awaiting_owner', 'approved', 'rejected', 'cancelled')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    owner_notified_at TIMESTAMPTZ,
    reviewed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_payment_pending_tg_user
    ON payment_pending (tg_user_id, status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_payment_pending_status
    ON payment_pending (status, created_at DESC);
