import { YANDEX_METRIKA_ID } from './site'

export function metrikaEnabled(): boolean {
  if (typeof window === 'undefined') return false
  const host = window.location.hostname
  return host === 'rawlead.ru' || host === 'www.rawlead.ru'
}

export function metrikaGoal(name: string): void {
  if (!name || !metrikaEnabled()) return
  if (typeof window.ym !== 'function') return
  window.ym(YANDEX_METRIKA_ID, 'reachGoal', name)
}

export function metrikaTrialLoginOnce(subscription: {
  plan?: string
  status?: string
  is_trial?: boolean
} | null | undefined): void {
  if (!subscription) return
  const plan = String(subscription.plan || '').toLowerCase()
  const status = String(subscription.status || '').toLowerCase()
  const isTrial =
    !!subscription.is_trial || plan === 'trial' || status === 'trial'
  if (!isTrial) return

  const key = 'rl_metrika_trial_login'
  try {
    if (sessionStorage.getItem(key)) return
    sessionStorage.setItem(key, '1')
  } catch {
    /* private mode */
  }
  metrikaGoal('rl_trial_login')
  metrikaGoal('trial_start')
}

declare global {
  interface Window {
    ym?: (...args: unknown[]) => void
  }
}
