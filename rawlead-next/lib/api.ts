import type {
  FeedResponse,
  LeadItem,
  UserProfile,
  UserTags,
  BotSessionResponse,
  BotCompleteResponse,
  DraftResponse,
  DraftQuota,
  SubscriptionStatus,
  SiteStats,
  QuizNextResponse,
  HistoryEntry,
  NotificationSettings,
} from './types'
import { normalizeQuizResponse } from './quiz-normalize'

const BASE = 'https://api.rawlead.ru/v1'
const MIN_ACCESS_TOKEN_LEN = 20

export function isValidAccessToken(token: unknown): token is string {
  if (typeof token !== 'string') return false
  const t = token.trim()
  return t.length >= MIN_ACCESS_TOKEN_LEN && t !== 'undefined' && t !== 'null'
}

export function getToken(): string | null {
  if (typeof window === 'undefined') return null
  const t = localStorage.getItem('rawlead_access_token')
  if (!isValidAccessToken(t)) {
    if (t != null) localStorage.removeItem('rawlead_access_token')
    return null
  }
  return t
}

export function setToken(token: string) {
  if (typeof window === 'undefined') return
  if (!isValidAccessToken(token)) return
  localStorage.setItem('rawlead_access_token', token)
}

export function clearToken() {
  if (typeof window === 'undefined') return
  localStorage.removeItem('rawlead_access_token')
  localStorage.removeItem('rawlead_user_meta')
}

function authHeaders(): HeadersInit {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const { data } = await rawFetch<T>(path, options)
  return data
}

async function rawFetch<T>(path: string, options: RequestInit = {}): Promise<{ res: Response; data: T }> {
  const method = (options.method ?? 'GET').toUpperCase()
  const needsContentType = method === 'POST' || method === 'PUT' || method === 'PATCH'

  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      ...(needsContentType ? { 'Content-Type': 'application/json' } : {}),
      ...authHeaders(),
      ...options.headers,
    },
  })

  const rotated = res.headers.get('X-Rawlead-Access-Token')
  if (isValidAccessToken(rotated)) setToken(rotated)

  const data = (await res.json().catch(() => ({}))) as T
  return { res, data }
}

// ─── Draft POST + poll (parity rawlead-feed.js ~L1207–1312) ───────────────────

const DRAFT_POLL_MS = 2000
const DRAFT_POLL_MAX_MS = 180000
const DRAFT_FAIL_RU = 'ИИ временно недоступен — повторите'

export class DraftApiError extends Error {
  status: number
  detail: string
  retryAfterSec?: number
  draft_retry_after_sec?: number

  constructor(status: number, detail: string, extra?: { retryAfterSec?: number; draft_retry_after_sec?: number }) {
    super(detail)
    this.name = 'DraftApiError'
    this.status = status
    this.detail = detail
    if (extra?.retryAfterSec != null) this.retryAfterSec = extra.retryAfterSec
    if (extra?.draft_retry_after_sec != null) this.draft_retry_after_sec = extra.draft_retry_after_sec
  }
}

export class CheckoutApiError extends Error {
  status: number
  detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.name = 'CheckoutApiError'
    this.status = status
    this.detail = detail
  }
}

export class QuizApiError extends Error {
  status: number
  detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.name = 'QuizApiError'
    this.status = status
    this.detail = detail
  }
}

function parseApiDetail(data: unknown): string {
  if (!data || typeof data !== 'object') return ''
  const row = data as Record<string, unknown>
  if (typeof row.detail === 'string') return row.detail
  if (typeof row.message === 'string') return row.message
  return ''
}

function parseDraftApiError(res: Response, data: Record<string, unknown>): DraftApiError {
  let detail = ''
  let retryAfter: number | undefined

  const d = data.detail
  if (typeof d === 'string') {
    detail = d
  } else if (d && typeof d === 'object') {
    const obj = d as Record<string, unknown>
    detail = String(obj.error || obj.detail || '')
    if (obj.retry_after_sec != null) retryAfter = Number(obj.retry_after_sec)
    if (obj.draft_retry_after_sec != null) {
      return new DraftApiError(res.status, detail || `HTTP ${res.status}`, {
        retryAfterSec: retryAfter,
        draft_retry_after_sec: Number(obj.draft_retry_after_sec),
      })
    }
  }
  if (!detail && data.error) detail = String(data.error)
  if (!detail && data.message) detail = String(data.message)
  if (data.retry_after_sec != null) retryAfter = Number(data.retry_after_sec)
  if (data.draft_retry_after_sec != null) {
    return new DraftApiError(res.status, detail || `HTTP ${res.status}`, {
      retryAfterSec: retryAfter,
      draft_retry_after_sec: Number(data.draft_retry_after_sec),
    })
  }
  return new DraftApiError(res.status, detail || `HTTP ${res.status}`, { retryAfterSec: retryAfter })
}

function draftReadyPayload(data: DraftResponse | null): DraftResponse | null {
  if (!data || data.status === 'failed') {
    throw new DraftApiError(503, data?.error || DRAFT_FAIL_RU)
  }
  if (data.status === 'ready' || (data.reply_draft && String(data.reply_draft).trim())) {
    return data
  }
  return null
}

function sleep(ms: number) {
  return new Promise<void>(resolve => setTimeout(resolve, ms))
}

async function pollDraftStatus(
  leadId: number,
  startedMs: number,
  autoRetried = false,
  onPoll?: (data: DraftResponse) => void,
): Promise<DraftResponse> {
  if (Date.now() - startedMs > DRAFT_POLL_MAX_MS) {
    if (!autoRetried) return pollDraftStatus(leadId, Date.now(), true, onPoll)
    throw new DraftApiError(503, 'Сложный бриф, ИИ полирует отклик...')
  }

  await sleep(DRAFT_POLL_MS)

  const { res, data } = await rawFetch<DraftResponse>(`/me/leads/${leadId}/draft`)
  const payload = data as DraftResponse & Record<string, unknown>

  if (res.status === 429 || res.status === 403 || res.status === 404) {
    throw parseDraftApiError(res, payload)
  }
  if (payload.status === 'failed') {
    throw draftReadyPayload(payload)
  }
  onPoll?.(payload)

  const ready = draftReadyPayload(payload)
  if (ready) return ready

  if (res.status >= 500 && !payload.status) {
    throw parseDraftApiError(res, payload)
  }

  return pollDraftStatus(leadId, startedMs, autoRetried, onPoll)
}

export async function createDraftAndPoll(
  leadId: number,
  opts?: { onPoll?: (data: DraftResponse) => void },
): Promise<DraftResponse> {
  const startedMs = Date.now()
  const { res, data } = await rawFetch<DraftResponse>(`/me/leads/${leadId}/draft`, { method: 'POST' })
  const payload = data as DraftResponse & Record<string, unknown>

  if (res.status === 429 || res.status === 403 || res.status === 404) {
    throw parseDraftApiError(res, payload)
  }

  const ready = draftReadyPayload(payload)
  if (ready) return ready

  if (res.status === 202 || payload.status === 'pending') {
    return pollDraftStatus(leadId, startedMs, false, opts?.onPoll)
  }

  if (!res.ok) throw parseDraftApiError(res, payload)
  return pollDraftStatus(leadId, startedMs, false, opts?.onPoll)
}

export function draftErrorUserMessage(err: unknown): string {
  if (err instanceof DraftApiError) {
    if (err.status === 429) {
      const sec = err.retryAfterSec ?? err.draft_retry_after_sec
      const mins = sec ? Math.max(1, Math.ceil(sec / 60)) : null
      return err.detail || (mins ? `Лимит черновиков в час · обновится через ${mins} мин` : 'Лимит черновиков в час')
    }
    return err.detail || err.message
  }
  if (err instanceof Error) return err.message
  return 'Ошибка, попробуй снова'
}

export const feedApi = {
  list: (params?: {
    offset?: number
    limit?: number
    /** Comma-separated category slugs, e.g. dev,design */
    category?: string
    categories?: string[]
    sort?: string
    skills?: string
    min_match?: number
    /** Comma-separated source keys, e.g. fl,youdo */
    source?: string
    sources?: string[]
  }) => {
    const q = new URLSearchParams()
    if (params?.offset) q.set('offset', String(params.offset))
    if (params?.limit) q.set('limit', String(params.limit))
    const categoryParam = params?.category
      ?? (params?.categories?.length ? params.categories.join(',') : undefined)
    if (categoryParam) q.set('category', categoryParam)
    if (params?.sort) q.set('sort', params.sort)
    if (params?.skills) q.set('skills', params.skills)
    if (params?.min_match) q.set('min_match', String(params.min_match))
    const sourceParam = params?.source
      ?? (params?.sources?.length ? params.sources.join(',') : undefined)
    if (sourceParam) q.set('source', sourceParam)
    const qs = q.toString()
    return apiFetch<FeedResponse>(`/feed${qs ? '?' + qs : ''}`)
  },
  lead: (id: number) => apiFetch<LeadItem>(`/leads/${id}`),
  siteStats: () => apiFetch<SiteStats>('/public/site-stats'),
}

export const authApi = {
  botSession: () => apiFetch<BotSessionResponse>('/auth/bot-session', { method: 'POST' }),
  /** Poll until bot confirms — caller must check res.ok + isValidAccessToken(data.access_token). */
  botComplete: (authToken: string) =>
    rawFetch<BotCompleteResponse>(`/auth/bot-complete?auth=${encodeURIComponent(authToken)}`),
}

export const meApi = {
  profile: () => apiFetch<UserProfile>('/me'),
  tags: () => apiFetch<UserTags>('/me/tags'),
  putTags: (tags: string[]) =>
    apiFetch<{ tags: string[] }>('/me/tags', {
      method: 'PUT',
      body: JSON.stringify({ tags }),
    }),
  subscription: () => apiFetch<SubscriptionStatus>('/me/subscription'),
  replies: (params?: { limit?: number; offset?: number }) => {
    const q = new URLSearchParams()
    if (params?.limit) q.set('limit', String(params.limit))
    if (params?.offset) q.set('offset', String(params.offset))
    return apiFetch<FeedResponse>(`/me/replies${q.toString() ? '?' + q.toString() : ''}`)
  },
  deleteReply: (leadId: number) =>
    apiFetch<void>(`/me/replies/${leadId}`, { method: 'DELETE' }),
  draftQuota: () => apiFetch<DraftQuota>('/me/draft/quota'),
  getDraft: (leadId: number) =>
    apiFetch<DraftResponse>(`/me/leads/${leadId}/draft`),
  createDraft: (leadId: number, opts?: { onPoll?: (data: DraftResponse) => void }) =>
    createDraftAndPoll(leadId, opts),
  checkout: async () => {
    const { res, data } = await rawFetch<{ confirmation_url?: string }>(
      '/me/subscription/checkout',
      { method: 'POST', body: JSON.stringify({ kind: 'subscription' }) },
    )
    if (!res.ok) {
      throw new CheckoutApiError(
        res.status,
        parseApiDetail(data) || 'Не удалось открыть оплату',
      )
    }
    if (!data.confirmation_url) {
      throw new CheckoutApiError(res.status, 'Не удалось получить ссылку на оплату')
    }
    return { confirmation_url: data.confirmation_url }
  },
  confirmSubscription: () =>
    apiFetch<{ status: string; subscription?: SubscriptionStatus }>(
      '/me/subscription/confirm',
      { method: 'POST', body: '{}' },
    ),
}

export const notifApi = {
  get: () => apiFetch<NotificationSettings>('/me/notification-settings'),
  patch: (data: Partial<NotificationSettings>) =>
    apiFetch<NotificationSettings>('/me/notification-settings', {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
}

export const quizApi = {
  start: async () => {
    const { res, data } = await rawFetch<QuizNextResponse>('/quiz/start')
    if (!res.ok) throw new QuizApiError(res.status, parseApiDetail(data) || 'Не удалось загрузить квиз')
    return normalizeQuizResponse(data)
  },
  next: async (history: HistoryEntry[]) => {
    const { res, data } = await rawFetch<QuizNextResponse>('/quiz/next', {
      method: 'POST',
      body: JSON.stringify({ history }),
    })
    if (!res.ok) throw new QuizApiError(res.status, parseApiDetail(data) || 'Ошибка квиза')
    return normalizeQuizResponse(data)
  },
  importTags: (tags: Record<string, number>, niches: string[], cx_pref = 1.0) =>
    apiFetch<{ ok: boolean; imported: number }>('/me/tags/import', {
      method: 'POST',
      body: JSON.stringify({ tags, niches, cx_pref }),
    }),
}
