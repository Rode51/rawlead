import type { UserProfile } from './types'

const META_KEY = 'rawlead_user_meta'
const API_BASE = 'https://api.rawlead.ru/v1'

export function avatarApiUrl(): string {
  return `${API_BASE}/me/avatar`
}

/** WP uploads 404 after Next cutover — use API proxy instead. */
export function isBrokenWpAvatarUrl(url: string): boolean {
  const u = url.trim()
  if (!u) return false
  return /wp-content\/uploads/i.test(u) || /rawlead\.ru\/wp-content/i.test(u)
}

export function resolveAvatarSrc(token: string | null, profile: UserProfile | null): string {
  if (!token || !profile) return ''
  const direct = (profile.avatar_url || '').trim()
  if (direct && !isBrokenWpAvatarUrl(direct)) return direct
  if (profile.tg_user_id > 0) return avatarApiUrl()
  if (profile.has_avatar || direct) return avatarApiUrl()
  return ''
}

export function displayHandle(profile: UserProfile | null | undefined): string {
  if (!profile) return 'Telegram'
  const username = (profile.username || '').trim()
  if (username) return `@${username}`
  const first = (profile.first_name || '').trim()
  if (first) return first
  return 'Telegram'
}

export function displayInitial(profile: UserProfile | null | undefined): string {
  const handle = displayHandle(profile)
  const ch = handle.replace(/^@/, '')[0]
  return ch ? ch.toUpperCase() : '?'
}

export function readUserMeta(): Partial<UserProfile> | null {
  if (typeof window === 'undefined') return null
  try {
    const raw = localStorage.getItem(META_KEY)
    return raw ? (JSON.parse(raw) as Partial<UserProfile>) : null
  } catch {
    return null
  }
}

export function saveUserMeta(profile: UserProfile): void {
  if (typeof window === 'undefined') return
  try {
    localStorage.setItem(
      META_KEY,
      JSON.stringify({
        username: profile.username || '',
        first_name: profile.first_name || '',
        avatar_url: profile.avatar_url || '',
        has_avatar: profile.has_avatar,
        can_ops_admin: profile.can_ops_admin,
      }),
    )
  } catch {
    /* private mode */
  }
}

export async function fetchAvatarBlobUrl(token: string): Promise<string | null> {
  try {
    const res = await fetch(avatarApiUrl(), {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!res.ok) return null
    const blob = await res.blob()
    if (!blob.size) return null
    return URL.createObjectURL(blob)
  } catch {
    return null
  }
}
