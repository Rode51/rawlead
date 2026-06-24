'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import { getToken } from '@/lib/api'

const BASE = 'https://api.rawlead.ru/v1'
const GUEST_KEY = 'rawlead_support_guest'

function getGuestToken(): string {
  try {
    const existing = localStorage.getItem(GUEST_KEY)
    if (existing && existing.length >= 8) return existing
    const token = 'g' + Date.now().toString(36) + Math.random().toString(36).slice(2, 10)
    localStorage.setItem(GUEST_KEY, token)
    return token
  } catch {
    return 'g' + Date.now().toString(36)
  }
}

function supportHeaders(): HeadersInit {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  const token = getToken()
  if (token) headers['Authorization'] = `Bearer ${token}`
  const guest = getGuestToken()
  if (guest) headers['X-RawLead-Guest-Token'] = guest
  return headers
}

interface Message {
  from: 'user' | 'owner'
  body: string
}

export default function SupportButton() {
  const [open, setOpen] = useState(false)
  const [unread, setUnread] = useState(0)
  const [messages, setMessages] = useState<Message[]>([])
  const [text, setText] = useState('')
  const [sending, setSending] = useState(false)
  const [sent, setSent] = useState(false)
  const [sendError, setSendError] = useState(false)
  const threadRef = useRef<HTMLDivElement>(null)

  const loadThread = useCallback(async () => {
    try {
      const r = await fetch(`${BASE}/support/thread`, { headers: supportHeaders() })
      const data = r.ok ? await r.json() : {}
      setMessages((data.messages as Message[]) ?? [])
      setUnread(0)
    } catch { /* ignore */ }
  }, [])

  const refreshUnread = useCallback(async () => {
    if (open) return
    try {
      const r = await fetch(`${BASE}/support/unread`, { headers: supportHeaders() })
      const data = r.ok ? await r.json() : {}
      setUnread(data?.unread ?? 0)
    } catch { /* ignore */ }
  }, [open])

  useEffect(() => {
    refreshUnread()
    const id = setInterval(refreshUnread, 60_000)
    return () => clearInterval(id)
  }, [refreshUnread])

  useEffect(() => {
    if (open) {
      loadThread()
      const id = setInterval(loadThread, 15_000)
      return () => clearInterval(id)
    }
  }, [open, loadThread])

  // Scroll thread to bottom on new messages
  useEffect(() => {
    if (threadRef.current && messages.length > 0) {
      threadRef.current.scrollTop = threadRef.current.scrollHeight
    }
  }, [messages])

  // Escape closes
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setOpen(false) }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [])

  async function handleSend() {
    const msg = text.trim()
    if (!msg || sending) return
    setSending(true)
    try {
      const r = await fetch(`${BASE}/support/ticket`, {
        method: 'POST',
        headers: supportHeaders(),
        body: JSON.stringify({ message: msg, url: window.location.href, source: 'fab' }),
      })
      if (!r.ok) {
        setSendError(true)
        setTimeout(() => setSendError(false), 2500)
        return
      }
      setText('')
      setSent(true)
      await loadThread()
      setTimeout(() => setSent(false), 2500)
    } catch {
      setSendError(true)
      setTimeout(() => setSendError(false), 2500)
    } finally {
      setSending(false)
    }
  }

  return (
    <>
      {/* FAB */}
        <button
          onClick={() => setOpen(v => !v)}
          data-testid="support-fab"
          aria-label="Поддержка"
          className={`rl-support-fab fixed bottom-6 right-6 z-50 flex items-center justify-center font-display font-black text-[13px] uppercase tracking-widest transition-all duration-150${open ? ' rl-support-fab--open' : ''}`}
        >
        {open ? '✕' : '?'}
        {!open && unread > 0 && (
          <span
            className="absolute -top-1 -right-1 flex items-center justify-center font-display font-black text-white"
            style={{
              width: 18, height: 18, fontSize: 9,
              background: '#111010',
              border: '1.5px solid #FACC15',
              borderRadius: '50%',
            }}
          >
            !
          </span>
        )}
      </button>

      {/* Backdrop */}
      {open && (
        <div
          className="fixed inset-0 z-40"
          style={{ background: 'rgba(17,16,16,0.35)' }}
          onClick={() => setOpen(false)}
        />
      )}

      {/* Modal */}
      {open && (
        <div
          className="fixed z-50 bg-white"
          style={{
            bottom: 72, right: 24,
            width: 'min(340px, calc(100vw - 32px))',
            border: '2px solid #111010',
            boxShadow: '6px 6px 0 #111010',
          }}
        >
          {/* Header */}
          <div
            className="px-5 py-4 font-display font-black text-[13px] uppercase tracking-wider"
            style={{ background: '#111010', color: '#FACC15', borderBottom: '2px solid #111010' }}
          >
            Поддержка
          </div>

          {/* Thread */}
          <div
            ref={threadRef}
            className="px-4 py-3 overflow-y-auto"
            style={{ maxHeight: 240, minHeight: messages.length > 0 ? 80 : 0 }}
          >
            {messages.length === 0 ? (
              <p className="text-[13px] font-sans" style={{ color: '#6B6B6B', lineHeight: 1.6 }}>
                Напиши — ответим в Telegram. Обычно быстро.
              </p>
            ) : (
              <div className="flex flex-col gap-2">
                {messages.map((m, i) => (
                  <div
                    key={i}
                    className="text-[13px] font-sans leading-snug px-3 py-2 max-w-[85%]"
                    style={{
                      alignSelf: m.from === 'owner' ? 'flex-start' : 'flex-end',
                      background: m.from === 'owner' ? '#F5F5F0' : '#FACC15',
                      border: '1.5px solid #111010',
                      color: '#111010',
                    }}
                  >
                    {m.body}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Composer */}
          <div style={{ borderTop: '1.5px solid #EAEAE6', padding: '12px 16px' }}>
            {sendError ? (
              <p className="text-[13px] font-display font-black text-center py-1" style={{ color: '#B91C1C' }}>
                Не отправилось, попробуй ещё
              </p>
            ) : sent ? (
              <p className="text-[13px] font-display font-black text-center py-1" style={{ color: '#111010' }}>
                ✓ Отправлено
              </p>
            ) : (
              <>
                <textarea
                  value={text}
                  onChange={e => setText(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleSend() }}
                  placeholder="Напиши сообщение…"
                  rows={3}
                  className="w-full font-sans text-[13px] resize-none outline-none bg-transparent"
                  style={{ color: '#111010', lineHeight: 1.6, marginBottom: 10, border: 'none' }}
                />
                <button
                  onClick={handleSend}
                  disabled={sending || !text.trim()}
                  className="w-full font-bold font-display text-[12px] uppercase tracking-widest transition-all duration-150"
                  style={{
                    height: 38,
                    background: '#FACC15',
                    border: '2px solid #111010',
                    boxShadow: '3px 3px 0 #111010',
                    cursor: sending || !text.trim() ? 'not-allowed' : 'pointer',
                    opacity: sending || !text.trim() ? 0.5 : 1,
                  }}
                >
                  {sending ? 'Отправляем…' : 'Отправить →'}
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </>
  )
}
