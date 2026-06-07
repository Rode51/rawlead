-- O116-W4: support tickets + thread messages (contact form + FAB)
CREATE TABLE IF NOT EXISTS support_tickets (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users (id) ON DELETE SET NULL,
    guest_token TEXT,
    source TEXT NOT NULL DEFAULT 'fab',
    page_url TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT support_tickets_actor CHECK (user_id IS NOT NULL OR guest_token IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_support_tickets_user ON support_tickets (user_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_support_tickets_guest ON support_tickets (guest_token, updated_at DESC);

CREATE TABLE IF NOT EXISTS support_messages (
    id BIGSERIAL PRIMARY KEY,
    ticket_id BIGINT NOT NULL REFERENCES support_tickets (id) ON DELETE CASCADE,
    from_role TEXT NOT NULL CHECK (from_role IN ('user', 'owner')),
    body TEXT NOT NULL,
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_support_messages_ticket ON support_messages (ticket_id, created_at ASC);
CREATE INDEX IF NOT EXISTS idx_support_messages_unread ON support_messages (ticket_id)
    WHERE from_role = 'owner' AND read_at IS NULL;
