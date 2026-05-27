-- L2 premium для подписчиков (кабинет): инструменты + черновик отклика
ALTER TABLE leads ADD COLUMN IF NOT EXISTS tools_required JSONB;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS reply_draft TEXT;
