'use client'

import { useEffect, useRef, useState } from 'react'

const DEFAULT_ITEMS = [
  { q: 'Как быстро?',           a: 'Бот или лендинг — 3–5 дней. Парсер и автоматизация — зависит от задачи. Называю срок до начала, не после.' },
  { q: 'Нужно ли ТЗ?',          a: 'Нет. Расскажи своими словами что нужно и зачем — разберёмся в деталях вместе.' },
  { q: 'Если не понравится?',   a: 'Оплата только после проверки. Убедился что работает — платишь. Не устроило — не платишь.' },
  { q: 'Как работаем удалённо?', a: 'Telegram. Без обязательных звонков. Пишешь когда удобно — отвечаю в течение 24ч.' },
]

interface FAQItem { q: string; a: string }
interface FAQContent { label: string; items: FAQItem[] }
interface Props { content?: FAQContent }

export default function FAQ({ content }: Props) {
  const label = content?.label ?? '/ FAQ'
  const items = content?.items ?? DEFAULT_ITEMS
  const ref = useRef<HTMLElement>(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const io = new IntersectionObserver(
      ([e]) => { if (e.isIntersecting) setVisible(true) },
      { threshold: 0.1 },
    )
    io.observe(el)
    return () => io.disconnect()
  }, [])

  return (
    <section
      ref={ref}
      id="faq"
      className="border-t border-edge px-10 lg:px-20 py-20 lg:py-32"
    >
      <div className="mb-12">
        <span className="font-mono text-muted" style={{ fontSize: '11px', letterSpacing: '0.18em' }}>
          {label}
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 border-l border-t border-edge">
        {items.map((item, i) => (
          <div
            key={i}
            className="border-r border-b border-edge"
            style={{
              opacity:   visible ? 1 : 0,
              transform: visible ? 'none' : 'translateY(16px)',
              transition: `opacity 0.55s ${i * 80}ms ease, transform 0.55s ${i * 80}ms ease`,
            }}
          >
            <div className="p-8 lg:p-12 flex flex-col gap-4">
              <p
                className="font-display font-black text-snow"
                style={{
                  fontSize: 'clamp(20px, 2vw, 30px)',
                  lineHeight: 0.95,
                  letterSpacing: '-0.02em',
                }}
              >
                {item.q}
              </p>
              <p
                className="font-mono text-muted"
                style={{
                  fontSize: 'clamp(11px, 0.9vw, 13px)',
                  letterSpacing: '0.04em',
                  lineHeight: 1.75,
                }}
              >
                {item.a}
              </p>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
