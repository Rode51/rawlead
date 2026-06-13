-- O185: allow processing status for atomic payment claim (webhook ∥ confirm).

ALTER TABLE yookassa_payments DROP CONSTRAINT IF EXISTS yookassa_payments_status_check;
ALTER TABLE yookassa_payments ADD CONSTRAINT yookassa_payments_status_check
    CHECK (status IN ('pending', 'processing', 'succeeded', 'canceled', 'failed'));
