-- O174b: YooKassa payments + saved payment method for auto-renewal.

CREATE TABLE IF NOT EXISTS yookassa_payments (
    id BIGSERIAL PRIMARY KEY,
    yookassa_payment_id TEXT NOT NULL UNIQUE,
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    kind TEXT NOT NULL CHECK (kind IN ('trial', 'subscription', 'renewal')),
    amount_rub NUMERIC(12, 2) NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'succeeded', 'canceled', 'failed')),
    payment_method_id TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_yookassa_payments_user
    ON yookassa_payments (user_id, status, created_at DESC);

ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS yookassa_payment_method_id TEXT;
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS auto_renew BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS renew_canceled_at TIMESTAMPTZ;
