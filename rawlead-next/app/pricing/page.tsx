'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useAuth } from '@/lib/auth-context'
import { useAuthModal } from '@/lib/auth-modal-context'
import { meApi, CheckoutApiError } from '@/lib/api'
import { getSubscriptionPayState } from '@/lib/subscription-cta'
import { metrikaGoal } from '@/lib/metrika'
import SubscriptionPayCta from '@/components/subscription/SubscriptionPayCta'

const BULLETS = [
  'Уникальный черновик отклика — ИИ пишет под тебя, ты отправляешь сам',
  'Персональная лента с % совпадения · push при матче · без задержки',
  '10 откликов в час — защита от спама',
  'Пуш в Telegram — только при хорошем совпадении',
]

export default function PricingPage() {
  const auth = useAuth()
  const { openLogin } = useAuthModal()
  const [loading, setLoading] = useState(false)
  const [checkoutError, setCheckoutError] = useState<string | null>(null)

  const pay = getSubscriptionPayState(auth.subscription)

  useEffect(() => {
    if (auth.status !== 'auth') return
    void (async () => {
      try {
        await meApi.confirmSubscription()
      } catch {
        // no pending payment
      }
      await auth.refreshSubscription()
    })()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [auth.status])

  async function handleCheckout() {
    if (loading) return
    if (auth.status === 'anon') {
      openLogin()
      return
    }
    setCheckoutError(null)
    setLoading(true)
    metrikaGoal('pay_click')
    try {
      const { confirmation_url } = await meApi.checkout()
      window.location.href = confirmation_url
    } catch (err) {
      setLoading(false)
      setCheckoutError(
        err instanceof CheckoutApiError
          ? err.detail
          : 'Не удалось открыть оплату. Попробуй ещё раз.',
      )
    }
  }

  return (
    <main style={{ minHeight: '100vh', background: '#F5F5F0', padding: '40px 20px 80px' }}>
      <div style={{ maxWidth: 640, margin: '0 auto' }}>
        <Link href="/" style={{ fontSize: '0.8125rem', fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: '#525252', textDecoration: 'none' }}>
          ← RawLead
        </Link>

        <p
          style={{ fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: '#6B6B6B', marginTop: 24, marginBottom: 8 }}
        >
          RawLead
        </p>

        <h1
          className="font-display font-black"
          style={{ fontSize: '2.25rem', letterSpacing: '-0.05em', marginBottom: 12 }}
        >
          Тарифы
        </h1>
        <p style={{ fontSize: '1rem', color: '#525252', lineHeight: 1.6, marginBottom: 40 }}>
          Пробуй 3 дня бесплатно — автоматически при первом входе.
        </p>

        {/* Pricing card */}
        <div
          style={{
            background: '#FFF',
            border: '2px solid #111010',
            boxShadow: '6px 6px 0 #111010',
            padding: '28px 28px 24px',
            marginBottom: 24,
          }}
        >
          {/* Header */}
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap', marginBottom: 16 }}>
            <h3
              className="font-display font-black"
              style={{ fontSize: '1.25rem', letterSpacing: '-0.04em' }}
            >
              RawLead Premium
            </h3>
            {pay.hasPremiumAccess && (
              <span
                style={{ fontSize: '0.7rem', fontWeight: 700, padding: '4px 10px', background: '#FACC15', border: '1.5px solid #111010' }}
              >
                ✓ Активна
              </span>
            )}
          </div>

          {/* Price */}
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginBottom: 12 }}>
            <span className="font-display font-black" style={{ fontSize: '2rem', letterSpacing: '-0.04em' }}>
              790 ₽
            </span>
            <span style={{ fontSize: '0.9rem', color: '#525252' }}>/ мес</span>
          </div>

          {/* Trial chip */}
          <span
            style={{
              display: 'inline-block', fontSize: '0.78rem', fontWeight: 700,
              padding: '5px 12px', marginBottom: 24,
              background: '#FFFBEB', border: '1.5px solid #FDE68A', color: '#92400E',
            }}
          >
            первые 3 дня бесплатно
          </span>

          {/* Bullets */}
          <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 28px', display: 'flex', flexDirection: 'column', gap: 10 }}>
            {BULLETS.map((b, i) => (
              <li key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                <span style={{ flexShrink: 0, marginTop: 1, fontWeight: 900, fontSize: '0.9rem' }}>✓</span>
                <span style={{ fontSize: '0.9rem', color: '#1A1A1A', lineHeight: 1.55 }}>{b}</span>
              </li>
            ))}
          </ul>

          {/* CTA */}
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'flex-start' }}>
            <div style={{ marginTop: 0 }}>
              <SubscriptionPayCta
                id="rl-price-checkout-sub"
                testId="pricing-checkout"
                subscription={auth.subscription}
                loading={loading}
                error={checkoutError}
                onCheckout={handleCheckout}
              />
            </div>

            {!pay.showPayButton && pay.showPremiumActive ? null : (
              <Link
                href="/cabinet/"
                className="rl-cta-white font-bold text-[13px] uppercase tracking-widest transition-colors duration-150"
                style={{
                  display: 'inline-block', padding: '14px 28px', marginTop: 16,
                  background: '#FFF', border: '2px solid #111010',
                  boxShadow: '4px 4px 0 #111010',
                  textDecoration: 'none', color: '#111010',
                }}
              >
                Открыть кабинет →
              </Link>
            )}

            <Link
              href="/lenta/"
              style={{
                display: 'inline-flex', alignItems: 'center',
                fontSize: '0.875rem', fontWeight: 600,
                color: '#525252', textDecoration: 'underline',
                padding: '14px 4px', marginTop: 16,
              }}
            >
              Смотреть ленту →
            </Link>
          </div>
        </div>

        {/* Legal */}
        <p style={{ fontSize: '0.78rem', color: '#6B6B6B', lineHeight: 1.65 }}>
          3 дня Trial — бесплатно и автоматически при первом входе (1× на аккаунт TG).
          Далее 790 ₽/мес — без автосписания. Оплата картой или СБП через ЮKassa.
        </p>
      </div>
    </main>
  )
}
