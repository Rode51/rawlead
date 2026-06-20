import type { SubscriptionStatus } from './types'

export type SubscriptionPayState = {
  isTrial: boolean
  hasPrepaid: boolean
  hasPremiumAccess: boolean
  showPayButton: boolean
  showPremiumActive: boolean
  payButtonLabel: string
  canCheckout: boolean
}

/** Same rules as cabinet: pay when free or trial without prepaid. Checkout is always 790 ₽ subscription. */
export function getSubscriptionPayState(
  subscription: SubscriptionStatus | null,
): SubscriptionPayState {
  const isTrial =
    subscription?.plan === 'trial' && !!subscription?.effective_access
  const hasPrepaid = !!subscription?.has_prepaid
  const hasPremiumAccess = !!subscription?.effective_access
  const showPayButton = !hasPremiumAccess || (isTrial && !hasPrepaid)
  const showPremiumActive = hasPremiumAccess && (!isTrial || hasPrepaid)
  const payButtonLabel = isTrial
    ? 'Оплатить Premium →'
    : 'Подключить Premium →'
  const canCheckout = subscription?.yookassa_available !== false

  return {
    isTrial,
    hasPrepaid,
    hasPremiumAccess,
    showPayButton,
    showPremiumActive,
    payButtonLabel,
    canCheckout,
  }
}
