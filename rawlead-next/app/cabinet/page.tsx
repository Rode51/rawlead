'use client'

import { Suspense, useState, useEffect, useRef } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '@/lib/auth-context'
import { displayHandle } from '@/lib/user-meta'
import { meApi, notifApi } from '@/lib/api'
import { BotLoginError, finishBotAuthToken } from '@/lib/bot-login'
import LoginPanel from '@/components/auth/LoginPanel'
import UserAvatar from '@/components/ui/UserAvatar'
import type { LeadItem, NotificationSettings, UserProfile, SubscriptionStatus } from '@/lib/types'
import InboxCard from '@/components/cabinet/InboxCard'
import {
  INBOX_SYNC_KEY,
  INBOX_REFRESH_EVENT,
  readPendingDraftsMap,
  removePendingDraft,
  notifyInboxRefresh,
} from '@/lib/pending-drafts'

// ─── Dev mocks (localhost only) ────────────────────────────────────────────────

const DEV_PROFILE: UserProfile = {
  user_id: 'dev-1', tg_user_id: 123456, username: 'devuser',
  first_name: 'Никита', avatar_url: '', has_avatar: false, can_ops_admin: false,
}

// ?dev=paid — trial auto-activated (как у нового пользователя после первого входа)
const DEV_SUB_PAID: SubscriptionStatus = {
  plan: 'trial', plan_label: 'Trial Premium', is_active: true, effective_access: true,
  active_until: new Date(Date.now() + 86400000 * 2).toISOString(),
  status: 'trial', trial_used_at: new Date(Date.now() - 86400000).toISOString(),
  yookassa_available: true,
}

const DEV_INBOX: LeadItem[] = [
  {
    id: 1, source: 'fl', title: 'Разработка React-приложения для стартапа — SaaS с нуля', body: '',
    task_summary: 'Нужен фронтенд-разработчик для SaaS-платформы, стек React + TypeScript.',
    url: 'https://fl.ru', budget_text: 'от 80 000 ₽', ai_score: 91, keyword_match: 90,
    final_rank: 91, category: 'dev', lead_tags: ['react', 'typescript'],
    lead_tag_labels: { react: 'React', typescript: 'TypeScript' },
    tools_required: [], difficulty: '2', tz_attachment: null,
    created_at: new Date(Date.now() - 7200000).toISOString(), is_hot: true,
    display_views: 12, display_replies: 3,
    reply_draft: 'Привет! Я React-разработчик с 5-летним опытом. Посмотрел задание — интересная архитектурная задача. Готов обсудить детали и сроки.',
    replied_at: new Date(Date.now() - 3600000).toISOString(),
  },
  {
    id: 2, source: 'kwork', title: 'FastAPI бэкенд с интеграцией Telegram Bot API', body: '',
    task_summary: 'Создание Python бэкенда с Telegram-ботом для уведомлений.',
    url: 'https://kwork.ru', budget_text: '25 000 ₽', ai_score: 78, keyword_match: 75,
    final_rank: 78, category: 'dev', lead_tags: ['python', 'fastapi'],
    lead_tag_labels: { python: 'Python', fastapi: 'FastAPI' },
    tools_required: [], difficulty: '3', tz_attachment: null,
    created_at: new Date(Date.now() - 14400000).toISOString(), is_hot: false,
    display_views: 5, display_replies: 1,
    reply_draft: 'Добрый день! Специализируюсь на FastAPI и Telegram-ботах. Выполнял похожие проекты — готов обсудить.',
    replied_at: new Date(Date.now() - 7200000).toISOString(),
  },
]

// ─── Helpers ───────────────────────────────────────────────────────────────────

function daysLeft(isoStr?: string): number | null {
  if (!isoStr) return null
  return Math.max(0, Math.ceil((new Date(isoStr).getTime() - Date.now()) / 86400000))
}

function formatUntil(isoStr: string): string {
  return new Date(isoStr).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' })
}

function mergePendingDrafts(items: LeadItem[]): LeadItem[] {
  const pending = readPendingDraftsMap()
  const byId = new Map(items.map(i => [i.id, i]))

  for (const key of Object.keys(pending)) {
    const id = parseInt(key, 10)
    if (!id) continue
    const row = pending[key]
    const existing = byId.get(id)
    if (existing?.reply_draft?.trim()) {
      removePendingDraft(id)
      continue
    }
    if (!existing) {
      byId.set(id, {
        id,
        source: 'fl',
        title: row.title || `Заказ #${id}`,
        body: '',
        task_summary: 'ИИ генерирует черновик отклика…',
        url: '',
        budget_text: null,
        ai_score: 0,
        keyword_match: null,
        final_rank: 0,
        category: row.category || '',
        lead_tags: [],
        lead_tag_labels: {},
        tools_required: [],
        difficulty: null,
        tz_attachment: null,
        created_at: new Date(row.added).toISOString(),
        is_hot: false,
        display_views: 0,
        display_replies: 0,
        reply_draft: '',
      })
    }
  }

  return Array.from(byId.values()).sort(
    (a, b) => new Date(b.replied_at || b.created_at).getTime() - new Date(a.replied_at || a.created_at).getTime()
  )
}

// ─── Main component (useSearchParams → must be in Suspense) ──────────────────

function CabinetInner() {
  const sp = useSearchParams()
  const auth = useAuth()

  const isDev = typeof window !== 'undefined' && window.location.hostname === 'localhost'
  const devParam = isDev ? (sp?.get('dev') ?? null) : null

  const [authQueryError, setAuthQueryError] = useState<string | null>(null)
  const authQueryRef = useRef(false)

  // Notifications (paid auth)
  const [notif, setNotif] = useState<NotificationSettings>({ threshold: 80, push_enabled: false })
  const [notifStatus, setNotifStatus] = useState<'idle' | 'saving' | 'saved'>('idle')

  // Inbox
  const LIMIT = 10
  const [inbox, setInbox] = useState<LeadItem[]>([])
  const [inboxTotal, setInboxTotal] = useState(0)
  const [inboxLoading, setInboxLoading] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)

  // Checkout
  const [checkoutLoading, setCheckoutLoading] = useState(false)

  // Derived
  const isDevMode = devParam === 'paid'
  const profile: UserProfile | null = isDevMode ? DEV_PROFILE : auth.profile
  const subscription: SubscriptionStatus | null = isDevMode ? DEV_SUB_PAID : auth.subscription
  const isPaid = subscription?.effective_access ?? false
  const isAuth = isDevMode || auth.status === 'auth'

  // Load notification settings on mount (paid auth, not dev)
  useEffect(() => {
    if (!isAuth || !isPaid || isDevMode) return
    notifApi.get().then(setNotif).catch(() => {})
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuth, isPaid])

  // Load inbox when auth is ready
  useEffect(() => {
    if (!isAuth) return
    if (isDevMode) {
      setInbox(DEV_INBOX)
      setInboxTotal(DEV_INBOX.length)
      return
    }
    loadInbox(0)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [auth.status, isDevMode])

  const pendingPollRef = useRef(new Set<number>())

  useEffect(() => {
    if (!isAuth || isDevMode || !isPaid) return

    async function pollPendingDrafts() {
      const pending = readPendingDraftsMap()
      const ids = Object.keys(pending)
        .map((k) => parseInt(k, 10))
        .filter((id) => Number.isFinite(id) && id > 0)
      if (!ids.length) return

      for (const id of ids) {
        if (pendingPollRef.current.has(id)) continue
        pendingPollRef.current.add(id)
        try {
          const res = await meApi.createDraft(id)
          const draft = res.reply_draft?.trim()
          if (draft) {
            removePendingDraft(id)
            setInbox((prev) =>
              prev.map((item) =>
                item.id === id ? { ...item, reply_draft: draft } : item,
              ),
            )
            notifyInboxRefresh()
          }
        } catch {
          // still generating or transient API error
        } finally {
          pendingPollRef.current.delete(id)
        }
      }
    }

    void pollPendingDrafts()
    const onRefresh = () => void pollPendingDrafts()
    window.addEventListener(INBOX_REFRESH_EVENT, onRefresh)
    return () => window.removeEventListener(INBOX_REFRESH_EVENT, onRefresh)
  }, [isAuth, isDevMode, isPaid])

  // Cleanup on unmount — none needed for modal login

  // ?auth= deep link from Telegram (WP consumeBotAuthFromQuery)
  useEffect(() => {
    if (isDevMode || authQueryRef.current) return
    const params = new URLSearchParams(window.location.search)
    const authToken = (params.get('auth') || '').trim()
    if (!authToken) return
    authQueryRef.current = true
    if (window.history?.replaceState) {
      window.history.replaceState({}, document.title, window.location.pathname)
    }
    void (async () => {
      try {
        auth.cancelBootstrap()
        await finishBotAuthToken(authToken, auth.login)
      } catch (err) {
        setAuthQueryError(
          err instanceof BotLoginError
            ? err.message
            : 'Не удалось завершить вход. Нажми «Войти» ещё раз.',
        )
      }
    })()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isDevMode])

  // Reload inbox when feed adds optimistic pending draft
  useEffect(() => {
    if (!isAuth || isDevMode) return
    function refresh() { void loadInbox(0) }
    function onStorage(e: StorageEvent) {
      if (e.key === INBOX_SYNC_KEY) refresh()
    }
    window.addEventListener('storage', onStorage)
    window.addEventListener(INBOX_REFRESH_EVENT, refresh)
    return () => {
      window.removeEventListener('storage', onStorage)
      window.removeEventListener(INBOX_REFRESH_EVENT, refresh)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuth, isDevMode])

  async function loadInbox(offset: number) {
    if (offset === 0) setInboxLoading(true)
    else setLoadingMore(true)
    try {
      const res = await meApi.replies({ limit: LIMIT, offset })
      const merged = offset === 0 ? mergePendingDrafts(res.items) : res.items
      setInbox(prev => offset === 0 ? merged : [...prev, ...res.items])
      setInboxTotal(res.count + (offset === 0 ? merged.length - res.items.length : 0))
    } catch {
      if (offset === 0) setInbox(mergePendingDrafts([]))
    } finally { setInboxLoading(false); setLoadingMore(false) }
  }

  async function handleCheckout() {
    if (!subscription || checkoutLoading) return
    setCheckoutLoading(true)
    try {
      const kind = !subscription.trial_used_at ? 'trial' : 'subscription'
      const { confirmation_url } = await meApi.checkout(kind)
      if (confirmation_url) {
        window.location.href = confirmation_url
      } else {
        await auth.refreshSubscription()
        setCheckoutLoading(false)
      }
    } catch {
      setCheckoutLoading(false)
    }
  }

  async function patchNotif(delta: Partial<NotificationSettings>) {
    const updated = { ...notif, ...delta }
    setNotif(updated)
    setNotifStatus('saving')
    try {
      await notifApi.patch(delta)
      setNotifStatus('saved')
      setTimeout(() => setNotifStatus('idle'), 2000)
    } catch {
      setNotifStatus('idle')
    }
  }

  // ── Pending ──────────────────────────────────────────────────────────────────
  if (auth.status === 'pending' && !isDevMode) {
    return (
      <main id="rl-cabinet-app" data-testid="cabinet-app" style={{ minHeight: '100vh', background: '#F5F5F0', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div className="animate-spin" style={{ width: 32, height: 32, border: '3px solid #111010', borderTopColor: 'transparent', borderRadius: '50%' }} />
      </main>
    )
  }

  // ── Anon gate ────────────────────────────────────────────────────────────────
  if (auth.status === 'anon' && !isDevMode) {
    return (
      <main id="rl-cabinet-app" data-testid="cabinet-app" style={{ minHeight: '100vh', background: '#F5F4F0', padding: '40px 20px 80px' }}>
        <div style={{ maxWidth: 640, margin: '0 auto' }}>
          <Link href="/lenta/" style={{ fontSize: '0.8125rem', fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: '#525252', textDecoration: 'none' }}>
            ← Лента
          </Link>

          {authQueryError && (
            <p role="alert" style={{ fontSize: '0.9rem', color: '#DC2626', marginTop: 16, marginBottom: 0 }}>
              {authQueryError}
            </p>
          )}

          <LoginPanel variant="cabinet" />

          <p style={{ marginTop: 36, fontSize: '0.875rem', color: '#525252' }}>
            Или{' '}
            <Link href="/lenta/" style={{ color: '#111010', fontWeight: 600 }}>
              Смотреть ленту →
            </Link>
          </p>
        </div>
      </main>
    )
  }

  // ── Auth (real or dev) ───────────────────────────────────────────────────────

  const displayUsername = displayHandle(profile)

  const isTrial = subscription?.plan === 'trial' && subscription.effective_access
  const trialDays = daysLeft(subscription?.active_until)
  const subBadgeText = subscription?.effective_access
    ? isTrial ? `✓ Trial · ${trialDays} дн.` : '✓ Premium'
    : 'Нет доступа'
  const subBadgeBg = subscription?.effective_access ? '#FACC15' : '#F5F5F0'
  const subBadgeColor = subscription?.effective_access ? '#111010' : '#525252'

  const showCheckout = !subscription?.effective_access
  const checkoutLabel = 'Подключить Premium →'

  const THRESHOLDS: Array<{ val: 60 | 80 | 100; label: string }> = [
    { val: 60, label: 'Все подходящие (60%+)' },
    { val: 80, label: 'Хорошие (80%+)' },
    { val: 100, label: 'Только идеальные (100%)' },
  ]

  return (
    <main id="rl-cabinet-app" data-testid="cabinet-app" style={{ minHeight: '100vh', background: '#F5F5F0', padding: '40px 20px 80px' }}>
      <div style={{ maxWidth: 640, margin: '0 auto' }}>
        <Link href="/lenta/" style={{ fontSize: '0.8125rem', fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: '#525252', textDecoration: 'none' }}>
          ← Лента
        </Link>

        {/* 1. User bar */}
        <div
          style={{
            marginTop: 24, marginBottom: 24,
            padding: '16px 20px',
            background: '#FFF',
            border: '2px solid #111010',
            boxShadow: '4px 4px 0 #111010',
            display: 'flex', alignItems: 'flex-start', gap: 14,
          }}
        >
          <UserAvatar profile={profile} size={40} style={{ flexShrink: 0 }} />
          <div style={{ flex: 1, minWidth: 0 }}>
            <p style={{ fontWeight: 700, fontSize: '0.875rem', marginBottom: 4 }}>
              В системе: <span>{displayUsername}</span>
            </p>
            <p style={{ fontSize: '0.78rem', color: '#525252' }}>
              Открыть @rawlead_bot · /start — push match-лидов
            </p>
          </div>
          <button
            onClick={auth.logout}
            style={{ fontSize: '0.75rem', color: '#525252', background: 'none', border: 'none', cursor: 'pointer', padding: '4px 0', textDecoration: 'underline', flexShrink: 0, alignSelf: 'center' }}
          >
            Выйти
          </button>
        </div>

        {/* 2. Subscription */}
        <div
          style={{
            marginBottom: 24,
            padding: '20px',
            background: '#FFF',
            border: '2px solid #111010',
            boxShadow: '4px 4px 0 #111010',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap', marginBottom: 8 }}>
            <h2
              className="font-display font-black"
              style={{ fontSize: '1.0625rem', letterSpacing: '-0.03em' }}
            >
              RawLead Premium
            </h2>
            <span
              style={{
                fontSize: '0.7rem', fontWeight: 700, padding: '3px 10px',
                background: subBadgeBg, color: subBadgeColor, border: '1.5px solid #D1D1CD',
              }}
            >
              {subBadgeText}
            </span>
          </div>
          {subscription?.effective_access && subscription.active_until ? (
            <p style={{ fontSize: '0.875rem', color: '#525252' }}>
              Premium активен до {formatUntil(subscription.active_until)}
            </p>
          ) : (
            <p style={{ fontSize: '0.875rem', color: '#525252' }}>
              790 ₽/мес · первые 3 дня бесплатно
            </p>
          )}
          {showCheckout && (
            <button
              onClick={handleCheckout}
              disabled={checkoutLoading}
              className="font-bold text-[13px] uppercase tracking-widest"
              style={{
                marginTop: 16, padding: '12px 24px',
                background: '#FACC15', border: '2px solid #111010',
                boxShadow: '3px 3px 0 #111010',
                cursor: checkoutLoading ? 'not-allowed' : 'pointer',
                opacity: checkoutLoading ? 0.7 : 1,
              }}
            >
              {checkoutLoading ? 'Переходим…' : checkoutLabel}
            </button>
          )}
        </div>

        {/* 3. Notifications (paid only) */}
        {isPaid && (
          <div
            style={{
              marginBottom: 24,
              padding: '20px',
              background: '#FFF',
              border: '2px solid #111010',
              boxShadow: '4px 4px 0 #111010',
            }}
          >
            <h2
              className="font-display font-black"
              style={{ fontSize: '1.0625rem', letterSpacing: '-0.03em', marginBottom: 16 }}
            >
              Уведомления
            </h2>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
              {THRESHOLDS.map(({ val, label }) => {
                const active = notif.threshold === val
                return (
                  <button
                    key={val}
                    onClick={() => patchNotif({ threshold: val })}
                    style={{
                      fontSize: '0.78rem',
                      fontWeight: active ? 700 : 500,
                      padding: '8px 14px',
                      background: active ? '#111010' : '#FFF',
                      color: active ? '#FFF' : '#525252',
                      border: `2px solid ${active ? '#111010' : '#D1D1CD'}`,
                      cursor: 'pointer',
                    }}
                  >
                    {label}
                  </button>
                )
              })}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
              <button
                onClick={() => patchNotif({ push_enabled: !notif.push_enabled })}
                role="switch"
                aria-checked={notif.push_enabled}
                style={{
                  width: 44, height: 24, borderRadius: 12,
                  border: '2px solid #111010',
                  background: notif.push_enabled ? '#111010' : '#E5E5E5',
                  position: 'relative', cursor: 'pointer', flexShrink: 0,
                  transition: 'background 160ms ease-out',
                }}
              >
                <span
                  style={{
                    position: 'absolute', top: 2,
                    left: notif.push_enabled ? 20 : 2,
                    width: 16, height: 16, borderRadius: '50%',
                    background: notif.push_enabled ? '#FACC15' : '#6B6B6B',
                    transition: 'left 160ms ease-out',
                  }}
                />
              </button>
              <span style={{ fontSize: '0.875rem', fontWeight: 500 }}>Push в Telegram</span>
              {notifStatus === 'saving' && <span style={{ fontSize: '0.75rem', color: '#6B6B6B' }}>Сохраняем…</span>}
              {notifStatus === 'saved' && <span style={{ fontSize: '0.75rem', color: '#00A65A' }}>✓ Сохранено</span>}
            </div>
            <p style={{ fontSize: '0.75rem', color: '#6B6B6B' }}>
              Push: напиши /start в @rawlead_bot — иначе уведомления не дойдут.
            </p>
          </div>
        )}

        {/* 4. Inbox */}
        <div>
          <h1
            className="font-display font-black"
            style={{ fontSize: '1.5rem', letterSpacing: '-0.04em', marginBottom: 8 }}
          >
            Мои отклики
          </h1>
          <p style={{ fontSize: '0.9rem', color: '#525252', marginBottom: 20 }}>
            Отклики с ленты — здесь. Новые заказы →{' '}
            <Link href="/lenta/" style={{ color: '#111010', fontWeight: 600 }}>Лента</Link>
          </p>

          {/* List */}
          {inboxLoading ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '48px 0' }}>
              <div className="animate-spin" style={{ width: 24, height: 24, border: '2px solid #111010', borderTopColor: 'transparent', borderRadius: '50%' }} />
            </div>
          ) : inbox.length === 0 ? (
            <div style={{ padding: '32px 0', textAlign: 'center' }}>
              {isPaid ? (
                <p style={{ color: '#525252' }}>
                  Откликов пока нет. Перейди в{' '}
                  <Link href="/lenta/" style={{ color: '#111010', fontWeight: 600 }}>ленту</Link>{' '}
                  и нажми «Написать отклик».
                </p>
              ) : (
                <>
                  <p style={{ color: '#525252', marginBottom: 12 }}>
                    Черновики откликов — с подпиской ИИ-агент.
                  </p>
                  <Link href="/pricing/" style={{ fontSize: '0.875rem', fontWeight: 700, color: '#111010', textDecoration: 'underline' }}>
                    Тарифы →
                  </Link>
                </>
              )}
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {inbox.map(item => (
                <InboxCard
                  key={item.id}
                  item={item}
                  onDelete={id => setInbox(prev => prev.filter(x => x.id !== id))}
                />
              ))}
            </div>
          )}

          {/* Load more */}
          {!inboxLoading && inbox.length > 0 && (
            <div style={{ marginTop: 28, textAlign: 'center' }}>
              {inbox.length < inboxTotal ? (
                <>
                  <p style={{ fontSize: '0.78rem', color: '#6B6B6B', marginBottom: 12 }}>
                    Показано {inbox.length} из {inboxTotal}
                  </p>
                  <button
                    onClick={() => loadInbox(inbox.length)}
                    disabled={loadingMore}
                    style={{
                      fontSize: '0.875rem', fontWeight: 700,
                      color: '#111010', background: '#FFF',
                      border: '2px solid #111010',
                      padding: '10px 24px',
                      cursor: loadingMore ? 'not-allowed' : 'pointer',
                      opacity: loadingMore ? 0.7 : 1,
                    }}
                  >
                    {loadingMore ? 'Загружаем…' : 'Показать ещё →'}
                  </button>
                </>
              ) : (
                <p style={{ fontSize: '0.78rem', color: '#6B6B6B' }}>Все отклики показаны</p>
              )}
            </div>
          )}
        </div>
      </div>
    </main>
  )
}

// ─── Export ────────────────────────────────────────────────────────────────────

export default function CabinetPage() {
  return (
    <Suspense fallback={
      <main style={{ minHeight: '100vh', background: '#F5F5F0', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div className="animate-spin" style={{ width: 32, height: 32, border: '3px solid #111010', borderTopColor: 'transparent', borderRadius: '50%' }} />
      </main>
    }>
      <CabinetInner />
    </Suspense>
  )
}
