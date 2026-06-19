import { clearToken, meApi } from './api'
import { saveUserMeta } from './user-meta'
import type { BotCompleteResponse, SubscriptionStatus, UserProfile } from './types'

export class AuthProfileError extends Error {
  constructor(message = 'AUTH_PROFILE_INCOMPLETE') {
    super(message)
    this.name = 'AuthProfileError'
  }
}

export class BotLoginError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'BotLoginError'
  }
}

function assertCompleteProfile(profile: UserProfile): void {
  if (!profile.user_id?.trim()) throw new AuthProfileError()
  const username = (profile.username || '').trim()
  const firstName = (profile.first_name || '').trim()
  if (!username && !firstName && profile.tg_user_id <= 0) throw new AuthProfileError()
}

/** Build profile from bot-complete body (WP saveUserMeta parity). */
export function profileFromBotComplete(data: BotCompleteResponse): UserProfile {
  const tgUserId = data.tg_user_id ?? 0
  const userId = data.user_id || ''
  let username = data.username || ''
  let firstName = data.first_name || ''
  if (userId.trim() && tgUserId > 0 && !username.trim() && !firstName.trim()) {
    firstName = 'Telegram'
  }
  return {
    user_id: userId,
    tg_user_id: tgUserId,
    username,
    first_name: firstName,
    avatar_url: data.avatar_url || '',
    has_avatar: !!data.has_avatar,
    can_ops_admin: false,
  }
}

/** Immediate login from bot-complete — does not wait on /me. */
export function loginFromBotComplete(data: BotCompleteResponse): { profile: UserProfile } {
  const profile = profileFromBotComplete(data)
  assertCompleteProfile(profile)
  saveUserMeta(profile)
  return { profile }
}

/** Background /me refresh — never clears token on failure. */
export async function refreshAuthFromServer(): Promise<{
  profile: UserProfile
  subscription: SubscriptionStatus
} | null> {
  try {
    const [profile, subscription] = await Promise.all([
      meApi.profile(),
      meApi.subscription(),
    ])
    assertCompleteProfile(profile)
    saveUserMeta(profile)
    return { profile, subscription }
  } catch {
    return null
  }
}

/** After setToken — full /me refresh (mount / ensureProfileFromServer). */
export async function completeAuthAfterToken(): Promise<{
  profile: UserProfile
  subscription: SubscriptionStatus
}> {
  const [profile, subscription] = await Promise.all([
    meApi.profile(),
    meApi.subscription(),
  ])
  try {
    assertCompleteProfile(profile)
  } catch {
    clearToken()
    throw new AuthProfileError()
  }
  saveUserMeta(profile)
  return { profile, subscription }
}
