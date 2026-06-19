import { setToken, authApi, isValidAccessToken } from './api'
import type { BotCompleteResponse, SubscriptionStatus, UserProfile } from './types'
import {
  loginFromBotComplete,
  refreshAuthFromServer,
  BotLoginError,
  AuthProfileError,
} from './auth-session'
import { mergeGuestSkillsAfterAuth } from './guest-skills'

export { BotLoginError }

export interface BotLoginCallbacks {
  onWaiting: (deepLink: string) => void
  onSuccess: (profile: UserProfile, subscription: SubscriptionStatus) => void
  onError: (message: string) => void
}

const DEFAULT_SUBSCRIPTION: SubscriptionStatus = {
  plan: 'free',
  plan_label: 'Free',
  is_active: false,
  status: 'free',
  effective_access: false,
  yookassa_available: true,
  trial_used_at: null,
}

/** Refresh /me before onSuccess so avatar cache + has_avatar are warm. */
export async function completeBotLoginFlow(
  data: BotCompleteResponse,
  login: (profile: UserProfile, subscription: SubscriptionStatus) => void,
): Promise<void> {
  let profile: UserProfile
  try {
    profile = loginFromBotComplete(data).profile
  } catch (err) {
    if (err instanceof AuthProfileError) {
      throw new BotLoginError('Подтверди вход в @rawlead_bot')
    }
    throw err
  }

  const refreshed = await refreshAuthFromServer()
  if (refreshed) {
    login(refreshed.profile, refreshed.subscription)
  } else {
    login(profile, DEFAULT_SUBSCRIPTION)
  }

  void mergeGuestSkillsAfterAuth()
}

export function startBotLoginPoll(
  authToken: string,
  expiresAt: string,
  callbacks: BotLoginCallbacks,
): () => void {
  const deadline = Date.parse(expiresAt) || Date.now() + 5 * 60 * 1000
  let stopped = false
  let timer: ReturnType<typeof setTimeout> | null = null
  let networkErrorStreak = 0

  function stop() {
    stopped = true
    if (timer) clearTimeout(timer)
    timer = null
  }

  async function tick() {
    if (stopped) return
    if (Date.now() > deadline) {
      stop()
      callbacks.onError('Время вышло — попробуй войти снова')
      return
    }

    try {
      const { res, data } = await authApi.botComplete(authToken)

      if (!res.ok || !isValidAccessToken(data.access_token)) {
        if (res.status === 401) {
          networkErrorStreak = 0
          timer = setTimeout(tick, 2000)
          return
        }
        if (res.status === 410) {
          stop()
          callbacks.onError('Сессия уже использована. Закрой Telegram на телефоне и войди снова.')
          return
        }
        const detail =
          (data as { detail?: string }).detail ||
          (data as { message?: string }).message ||
          `HTTP ${res.status}`
        throw new BotLoginError(String(detail))
      }

      networkErrorStreak = 0
      if (process.env.NODE_ENV !== 'production') {
        console.info('[auth] bot-login poll 200')
      }

      stop()
      setToken(data.access_token)

      try {
        await completeBotLoginFlow(data, (profile, subscription) => {
          if (process.env.NODE_ENV !== 'production') {
            console.info('[auth] bot-login success', profile.username || profile.first_name)
          }
          callbacks.onSuccess(profile, subscription)
        })
      } catch (err) {
        callbacks.onError(
          err instanceof BotLoginError ? err.message : 'Подтверди вход в @rawlead_bot',
        )
      }
    } catch (err) {
      if (stopped) return
      if (err instanceof BotLoginError || err instanceof AuthProfileError) {
        stop()
        callbacks.onError(
          err instanceof BotLoginError ? err.message : 'Подтверди вход в @rawlead_bot',
        )
        return
      }

      networkErrorStreak += 1
      if (networkErrorStreak >= 3) {
        stop()
        callbacks.onError('Не удалось связаться с сервером. Проверь сеть и попробуй снова.')
        return
      }
      timer = setTimeout(tick, 2000)
    }
  }

  void tick()
  return stop
}

export async function finishBotAuthToken(
  authToken: string,
  login: (profile: UserProfile, subscription: SubscriptionStatus) => void,
): Promise<void> {
  const { res, data } = await authApi.botComplete(authToken)
  if (!res.ok || !isValidAccessToken(data.access_token)) {
    if (res.status === 410) {
      throw new BotLoginError('Сессия уже использована. Закрой Telegram на телефоне и войди снова.')
    }
    const detail =
      (data as { detail?: string }).detail ||
      (data as { message?: string }).message ||
      'Не удалось завершить вход'
    throw new BotLoginError(String(detail))
  }

  setToken(data.access_token)
  await completeBotLoginFlow(data, login)
}
