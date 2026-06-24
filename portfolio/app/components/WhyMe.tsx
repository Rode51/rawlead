'use client'

import { useEffect, useRef, useState } from 'react'

const DEFAULT_REASONS = [
  { title: 'ФИКСИРОВАННАЯ ЦЕНА', body: 'Называю стоимость до начала работы. Никаких «немного доплатить» в процессе.' },
  { title: 'ОПЛАТА ПОСЛЕ',       body: 'Проверяешь что всё работает как надо — потом платишь.' },
  { title: 'УДАЛЕННО',           body: 'Работаю из любой точки. Без офиса, без митингов без причины.' },
  { title: 'ПОДДЕРЖКА',          body: 'Остаюсь на связи после сдачи. Сломается — починю.' },
]

interface ContentItem { title: string; body: string }
interface WhyMeContent { label: string; items: ContentItem[] }
interface Props { content?: WhyMeContent }

export default function WhyMe({ content }: Props) {
  const label   = content?.label ?? '/ ПОЧЕМУ Я'
  const reasons = content?.items ?? DEFAULT_REASONS
  const ref = useRef<HTMLElement>(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const io = new IntersectionObserver(
      ([e]) => { if (e.isIntersecting) setVisible(true) },
      { threshold: 0.15 },
    )
    io.observe(el)
    return () => io.disconnect()
  }, [])

  return (
    <section
      ref={ref}
      id="why"
      className="border-t border-edge px-10 lg:px-20 py-20 lg:py-32"
    >
      <div className="mb-12">
        <span className="font-mono text-muted" style={{ fontSize: '11px', letterSpacing: '0.18em' }}>
          {label}
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 border-l border-t border-edge">
        {reasons.map((r, i) => (
          <div
            key={r.title}
            className="border-r border-b border-edge"
            style={{
              opacity:   visible ? 1 : 0,
              transform: visible ? 'none' : 'translateY(18px)',
              transition: `opacity 0.55s ${i * 90}ms ease, transform 0.55s ${i * 90}ms ease`,
            }}
          >
            <div className="p-8 lg:p-10 flex flex-col gap-5 h-full">
              <h3
                className="font-display font-black text-snow"
                style={{
                  fontSize: 'clamp(22px, 2.2vw, 34px)',
                  lineHeight: 0.92,
                  letterSpacing: '-0.02em',
                }}
              >
                {r.title}
              </h3>
              <p
                className="font-mono text-muted mt-auto"
                style={{
                  fontSize: 'clamp(11px, 0.85vw, 12px)',
                  letterSpacing: '0.04em',
                  lineHeight: 1.75,
                }}
              >
                {r.body}
              </p>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
