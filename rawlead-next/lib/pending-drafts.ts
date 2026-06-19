/** Mirrors WP rawlead-feed.js / rawlead-cabinet.js localStorage keys */

export const INBOX_SYNC_KEY = 'rawlead_inbox_rev'
export const PENDING_DRAFTS_KEY = 'rawlead_pending_drafts'

export interface PendingDraftRow {
  id: number
  title: string
  category: string
  added: number
}

export function readPendingDraftsMap(): Record<string, PendingDraftRow> {
  if (typeof window === 'undefined') return {}
  try {
    const raw = localStorage.getItem(PENDING_DRAFTS_KEY)
    if (!raw) return {}
    const data = JSON.parse(raw) as unknown
    return data && typeof data === 'object' ? (data as Record<string, PendingDraftRow>) : {}
  } catch {
    return {}
  }
}

export function writePendingDraftsMap(map: Record<string, PendingDraftRow>) {
  if (typeof window === 'undefined') return
  try {
    localStorage.setItem(PENDING_DRAFTS_KEY, JSON.stringify(map))
  } catch { /* quota / private mode */ }
}

export function addPendingDraft(leadId: number, item?: { title?: string; category?: string }) {
  if (!leadId) return
  const map = readPendingDraftsMap()
  map[String(leadId)] = {
    id: leadId,
    title: item?.title ?? '',
    category: item?.category ?? '',
    added: Date.now(),
  }
  writePendingDraftsMap(map)
}

export function removePendingDraft(leadId: number) {
  if (!leadId) return
  const key = String(leadId)
  const map = readPendingDraftsMap()
  if (!map[key]) return
  delete map[key]
  writePendingDraftsMap(map)
}

export function notifyInboxRefresh() {
  if (typeof window === 'undefined') return
  try {
    localStorage.setItem(INBOX_SYNC_KEY, String(Date.now()))
  } catch { /* ignore */ }
  window.dispatchEvent(new CustomEvent('rawlead-inbox-refresh'))
}

export const INBOX_REFRESH_EVENT = 'rawlead-inbox-refresh'
