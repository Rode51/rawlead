/**
 * Feed filter prefs — parity rawlead-feed.js (PREFS_KEY + /v1/me/feed-prefs merge on login).
 * v3 (2026-06-22): sources are local-only; v2 exchange filters discarded on migrate.
 */

import { getToken, isValidAccessToken, setToken } from './api'

/** Legacy v1 — removed on read; never migrated (stale TG/source filters). */
export const FEED_PREFS_KEY_V1 = 'rawlead_feed_prefs'
/** Legacy v2 — one-shot migrate sort/category/min_match; sources reset to []. */
export const FEED_PREFS_KEY_V2 = 'rawlead_feed_prefs_v2'
export const FEED_PREFS_KEY = 'rawlead_feed_prefs_v3'

export type FeedSort = 'time' | 'match'

export interface FeedFilterState {
  categories: string[]
  sources: string[]
  sort: FeedSort
}

export interface StoredFeedPrefs {
  sort: FeedSort
  min_match: number
  category: string
  source: string
  sources: string[]
  updated_at: string | null
}

const API_BASE = 'https://api.rawlead.ru/v1'

function authHeaders(): HeadersInit {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function rawFeedPrefsFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<{ res: Response; data: T }> {
  const method = (options.method ?? 'GET').toUpperCase()
  const needsContentType = method === 'PUT' || method === 'POST' || method === 'PATCH'
  const res = await fetch(`${API_BASE}${path}`, {
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

export function dropLegacyFeedPrefsV1(): void {
  if (typeof window === 'undefined') return
  try {
    localStorage.removeItem(FEED_PREFS_KEY_V1)
  } catch {
    /* quota / private mode */
  }
}

function dropLegacyFeedPrefsV2(): void {
  if (typeof window === 'undefined') return
  try {
    localStorage.removeItem(FEED_PREFS_KEY_V2)
  } catch {
    /* quota / private mode */
  }
}

/** v2 → v3: keep sort/category/min_match; force sources=[] (stuck TG fix). */
function migrateV2FeedPrefsToV3(): StoredFeedPrefs | null {
  if (typeof window === 'undefined') return null
  try {
    const raw = localStorage.getItem(FEED_PREFS_KEY_V2)
    if (!raw) return null
    const v2 = normalizeFeedPrefs(JSON.parse(raw))
    const migrated: StoredFeedPrefs = {
      sort: v2.sort,
      min_match: v2.min_match,
      category: v2.category,
      source: '',
      sources: [],
      updated_at: v2.updated_at ?? new Date().toISOString(),
    }
    writeLocalFeedPrefs(migrated)
    dropLegacyFeedPrefsV2()
    return migrated
  } catch {
    dropLegacyFeedPrefsV2()
    return null
  }
}

export function defaultFeedPrefs(): StoredFeedPrefs {
  return {
    sort: 'time',
    min_match: 80,
    category: '',
    source: '',
    sources: [],
    updated_at: null,
  }
}

export function sourcesFromPrefs(prefs: Partial<StoredFeedPrefs> | null | undefined): string[] {
  if (!prefs) return []
  if (Array.isArray(prefs.sources)) {
    return prefs.sources.filter((s): s is string => typeof s === 'string' && Boolean(s))
  }
  if (typeof prefs.source === 'string' && prefs.source) {
    return prefs.source.split(',').filter(Boolean)
  }
  return []
}

export function categoriesFromPrefs(prefs: Partial<StoredFeedPrefs> | null | undefined): string[] {
  if (!prefs?.category || typeof prefs.category !== 'string') return []
  return prefs.category.split(',').filter(Boolean)
}

export function normalizeFeedPrefs(raw: unknown): StoredFeedPrefs {
  const prefs = raw && typeof raw === 'object' ? (raw as Record<string, unknown>) : null
  const sort: FeedSort = prefs?.sort === 'match' ? 'match' : 'time'
  let min_match = 80
  if (prefs?.min_match != null) {
    const mm = parseInt(String(prefs.min_match), 10)
    if ([0, 50, 60, 70, 80, 90].includes(mm)) min_match = mm
  }
  const category = typeof prefs?.category === 'string' ? prefs.category : ''
  const sources = sourcesFromPrefs(prefs as Partial<StoredFeedPrefs>)
  return {
    sort,
    min_match,
    category,
    source: sources.join(','),
    sources,
    updated_at: prefs?.updated_at != null ? String(prefs.updated_at) : null,
  }
}

export function prefsToFilterState(prefs: StoredFeedPrefs): FeedFilterState {
  return {
    categories: categoriesFromPrefs(prefs),
    sources: prefs.sources.slice(),
    sort: prefs.sort,
  }
}

export function filterStateToPrefsPayload(state: FeedFilterState): StoredFeedPrefs {
  return {
    sort: state.sort,
    min_match: 80,
    category: state.categories.join(','),
    source: state.sources.join(','),
    sources: state.sources.slice(),
    updated_at: new Date().toISOString(),
  }
}

export function readLocalFeedPrefs(): StoredFeedPrefs | null {
  if (typeof window === 'undefined') return null
  dropLegacyFeedPrefsV1()
  try {
    const raw = localStorage.getItem(FEED_PREFS_KEY)
    if (raw) return normalizeFeedPrefs(JSON.parse(raw))
    return migrateV2FeedPrefsToV3()
  } catch {
    return null
  }
}

export function writeLocalFeedPrefs(prefs: StoredFeedPrefs): void {
  if (typeof window === 'undefined') return
  try {
    localStorage.setItem(FEED_PREFS_KEY, JSON.stringify(prefs))
  } catch {
    /* quota / private mode */
  }
}

function prefsTimestamp(prefs: StoredFeedPrefs | null | undefined): number {
  if (!prefs?.updated_at) return 0
  const t = Date.parse(prefs.updated_at)
  return Number.isNaN(t) ? 0 : t
}

export function stripFeedFilterParamsFromUrl(): void {
  if (typeof window === 'undefined') return
  const url = new URL(window.location.href)
  if (!url.searchParams.has('category') && !url.searchParams.has('source')) return
  url.searchParams.delete('category')
  url.searchParams.delete('source')
  const qs = url.searchParams.toString()
  window.history.replaceState(null, '', url.pathname + (qs ? `?${qs}` : '') + url.hash)
}

export function readUrlFilterOverrides(): Partial<FeedFilterState> | null {
  if (typeof window === 'undefined') return null
  const params = new URLSearchParams(window.location.search)
  const category = params.get('category')
  const source = params.get('source')
  if (!category && !source) return null
  const out: Partial<FeedFilterState> = {}
  if (category) out.categories = category.split(',').filter(Boolean)
  if (source) out.sources = source.split(',').filter(Boolean)
  return out
}

/** Prefs-only hydrate — never reads ?source= / ?category= (use applyUrlFilterOverridesOnce for deep links). */
export function hydrateFilterState(): FeedFilterState {
  const local = readLocalFeedPrefs()
  return prefsToFilterState(local ?? defaultFeedPrefs())
}

/**
 * One-shot deep-link: merge URL overrides → localStorage → strip query.
 * Returns merged state when URL had filter params; otherwise null.
 */
export function applyUrlFilterOverridesOnce(): FeedFilterState | null {
  const url = readUrlFilterOverrides()
  if (!url) return null
  const base = hydrateFilterState()
  const merged: FeedFilterState = {
    categories: url.categories ?? base.categories,
    sources: url.sources ?? base.sources,
    sort: base.sort,
  }
  writeLocalFeedPrefs(filterStateToPrefsPayload(merged))
  stripFeedFilterParamsFromUrl()
  return merged
}

export function initFilterState(): { state: FeedFilterState; urlApplied: boolean } {
  const fromUrl = applyUrlFilterOverridesOnce()
  if (fromUrl) return { state: fromUrl, urlApplied: true }
  return { state: hydrateFilterState(), urlApplied: false }
}

export async function persistFeedPrefs(state: FeedFilterState): Promise<StoredFeedPrefs> {
  const payload = filterStateToPrefsPayload(state)
  writeLocalFeedPrefs(payload)
  stripFeedFilterParamsFromUrl()
  const token = getToken()
  if (!token) return payload

  try {
    const { res, data } = await rawFeedPrefsFetch<StoredFeedPrefs>('/me/feed-prefs', {
      method: 'PUT',
      body: JSON.stringify({
        sort: payload.sort,
        min_match: payload.min_match,
        category: payload.category,
        source: payload.source,
      }),
    })
    if (res.ok) {
      const saved = normalizeFeedPrefs(data)
      writeLocalFeedPrefs(saved)
      return saved
    }
  } catch {
    /* keep local */
  }
  return payload
}

async function putFeedPrefsNonSources(prefs: StoredFeedPrefs): Promise<void> {
  const token = getToken()
  if (!token) return
  try {
    const { res, data } = await rawFeedPrefsFetch<StoredFeedPrefs>('/me/feed-prefs', {
      method: 'PUT',
      body: JSON.stringify({
        sort: prefs.sort,
        min_match: prefs.min_match,
        category: prefs.category,
      }),
    })
    if (res.ok) {
      const saved = normalizeFeedPrefs(data)
      writeLocalFeedPrefs({
        ...saved,
        source: prefs.source,
        sources: prefs.sources.slice(),
      })
    }
  } catch {
    /* keep local */
  }
}

/** Login merge: sort · category · min_match only — sources stay local, never from server. */
export async function mergeFeedPrefsOnLogin(): Promise<FeedFilterState> {
  const local = readLocalFeedPrefs() ?? defaultFeedPrefs()
  const localSources = local.sources.slice()
  const token = getToken()
  if (!token) return prefsToFilterState({ ...local, sources: localSources })

  try {
    const { res, data } = await rawFeedPrefsFetch<StoredFeedPrefs>('/me/feed-prefs')
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const remote = normalizeFeedPrefs(data)
    const remoteWins = prefsTimestamp(remote) >= prefsTimestamp(local)
    const merged: StoredFeedPrefs = {
      sort: remoteWins ? remote.sort : local.sort,
      min_match: remoteWins ? remote.min_match : local.min_match,
      category: remoteWins ? remote.category : local.category,
      source: localSources.join(','),
      sources: localSources,
      updated_at: remoteWins && remote.updated_at ? remote.updated_at : (local.updated_at ?? new Date().toISOString()),
    }
    writeLocalFeedPrefs(merged)
    if (!remoteWins) {
      await putFeedPrefsNonSources(merged)
    }
    return prefsToFilterState(merged)
  } catch {
    return prefsToFilterState({ ...local, sources: localSources })
  }
}
