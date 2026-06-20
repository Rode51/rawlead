'use client'

import type { CSSProperties } from 'react'
import type { SubscriptionStatus } from '@/lib/types'
import { getSubscriptionPayState } from '@/lib/subscription-cta'

type Props = {
  subscription: SubscriptionStatus | null
  loading?: boolean
  error?: string | null
  onCheckout: () => void
  id?: string
  testId?: string
}

const btnBase: CSSProperties = {
  padding: '12px 24px',
  border: '2px solid #111010',
  fontSize: '13px',
  fontWeight: 700,
  letterSpacing: '0.1em',
  textTransform: 'uppercase',
}

export default function SubscriptionPayCta({
  subscription,
  loading = false,
  error = null,
  onCheckout,
  id,
  testId,
}: Props) {
  const pay = getSubscriptionPayState(subscription)

  if (pay.showPremiumActive) {
    return (
      <span
        className="font-bold text-[13px] uppercase tracking-widest"
        style={{
          ...btnBase,
          display: 'inline-block',
          marginTop: 16,
          background: '#F5F5F0',
          color: '#111010',
          boxShadow: '3px 3px 0 #111010',
          cursor: 'default',
        }}
      >
        Premium активен
      </span>
    )
  }

  if (!pay.showPayButton) return null

  const disabled = loading || !pay.canCheckout

  return (
    <div style={{ marginTop: 16 }}>
      <button
        id={id}
        data-testid={testId}
        type="button"
        onClick={onCheckout}
        disabled={disabled}
        className="font-bold text-[13px] uppercase tracking-widest"
        style={{
          ...btnBase,
          background: '#FACC15',
          boxShadow: '3px 3px 0 #111010',
          cursor: disabled ? 'not-allowed' : 'pointer',
          opacity: disabled ? 0.7 : 1,
        }}
      >
        {loading ? 'Переходим…' : pay.payButtonLabel}
      </button>
      {!pay.canCheckout && (
        <p style={{ fontSize: '0.8rem', color: '#6B6B6B', marginTop: 8, marginBottom: 0 }}>
          Оплата временно недоступна. Попробуй позже.
        </p>
      )}
      {error && (
        <p role="alert" style={{ fontSize: '0.85rem', color: '#DC2626', marginTop: 8, marginBottom: 0 }}>
          {error}
        </p>
      )}
    </div>
  )
}
