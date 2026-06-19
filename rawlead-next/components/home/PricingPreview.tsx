'use client'

import Link from 'next/link'
import ScrollReveal from '@/components/ui/ScrollReveal'

const BULLETS = [
  'Уникальный черновик отклика — ИИ пишет под тебя, ты отправляешь сам',
  'Персональная лента с % совпадения · push при матче · без задержки',
  '10 откликов в час — защита от спама',
]

export default function PricingPreview() {
  return (
    <section className="py-24 md:py-32 bg-rl-page border-b-2 border-rl-inverse">
      <div
        className="mx-auto px-6"
        style={{ maxWidth: 'var(--rl-container)' }}
      >
        <ScrollReveal className="mb-14 text-center">
          <p className="text-[11px] font-display font-black uppercase tracking-[0.2em] text-rl-muted mb-4">
            Тариф
          </p>
          <h2
            className="font-display font-black text-rl-inverse leading-[0.95] tracking-[-0.03em]"
            style={{ fontSize: 'clamp(32px, 5vw, 56px)' }}
          >
            Один тариф. Без уловок.
          </h2>
        </ScrollReveal>

        <ScrollReveal delay={0.1} className="max-w-md mx-auto">
          <div className="bg-rl-page border-2 border-rl-inverse shadow-neo p-8">

            {/* Card header */}
            <div className="flex items-start justify-between gap-4 mb-8">
              <div>
                <p className="font-display font-black text-rl-inverse text-xl tracking-[-0.01em]">
                  RawLead Premium
                </p>
                <p className="font-display font-black text-[40px] leading-none text-rl-inverse mt-2 tracking-[-0.03em]">
                  790 ₽
                  <span className="text-base font-sans font-normal text-rl-muted ml-1">/ мес</span>
                </p>
              </div>
              <span className="mt-1 px-3 py-1.5 bg-[#FACC15] border-2 border-rl-inverse font-display font-black text-[10px] uppercase tracking-[0.1em] text-rl-inverse whitespace-nowrap shadow-[2px_2px_0_#111010]">
                3 дня бесплатно
              </span>
            </div>

            {/* Bullets */}
            <ul className="space-y-4 mb-8 border-t-2 border-rl-section pt-6">
              {BULLETS.map((b, i) => (
                <li key={i} className="flex items-start gap-3">
                  <span className="mt-0.5 w-4 h-4 flex-shrink-0 bg-[#FACC15] border-2 border-rl-inverse flex items-center justify-center">
                    <span className="w-1.5 h-1.5 bg-rl-inverse rounded-full" />
                  </span>
                  <span className="font-sans text-sm text-rl-muted leading-relaxed">{b}</span>
                </li>
              ))}
            </ul>

            {/* CTA */}
            <Link
              href="/pricing/"
              data-testid="home-pricing-cta"
              className="block w-full text-center h-12 leading-[44px] bg-rl-inverse text-white font-display font-black text-sm uppercase tracking-[0.08em] border-2 border-rl-inverse shadow-[4px_4px_0_#111010] hover:shadow-[7px_7px_0_#111010] hover:-translate-x-0.5 hover:-translate-y-0.5 transition-all duration-150"
            >
              Попробовать бесплатно →
            </Link>
          </div>
        </ScrollReveal>
      </div>
    </section>
  )
}
