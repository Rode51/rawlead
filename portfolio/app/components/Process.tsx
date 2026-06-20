'use client'

import { useEffect, useRef, useState } from 'react'

const DEFAULT_STEPS = [
  { num: '01', title: 'Рассказываешь задачу',  body: 'Без брифов и ТЗ. Напиши в Telegram что нужно и зачем — разберёмся в деталях вместе.' },
  { num: '02', title: 'Получаешь план',         body: 'Что делаю, сколько займёт, что получишь на выходе. Называю цену до начала — без сюрпризов.' },
  { num: '03', title: 'Забираешь результат',    body: 'Оплата после проверки — убеждаешься что работает, потом платишь. Деплой, документация, поддержка.' },
]
const DEFAULT_NOTE = 'Обычно от первого сообщения до готового бота или лендинга — 3–5 дней.'

interface ProcessStep { num: string; title: string; body: string }
interface ProcessContent { label: string; steps: ProcessStep[]; note: string }
interface Props { content?: ProcessContent }

export default function Process({ content }: Props) {
  const label = content?.label ?? '/ КАК РАБОТАЕМ'
  const steps = content?.steps ?? DEFAULT_STEPS
  const note  = content?.note  ?? DEFAULT_NOTE
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
      id="process"
      className="border-t border-edge px-10 lg:px-20 py-20 lg:py-32"
    >
      {/* Label */}
      <div className="mb-12">
        <span className="font-mono text-muted" style={{ fontSize: '11px', letterSpacing: '0.18em' }}>
          {label}
        </span>
      </div>

      {/* Steps */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-0 border-l border-t border-edge">
        {steps.map((s, i) => (
          <div
            key={s.num}
            className="border-r border-b border-edge"
            style={{
              opacity:   visible ? 1 : 0,
              transform: visible ? 'none' : 'translateY(20px)',
              transition: `opacity 0.6s ${i * 120}ms ease, transform 0.6s ${i * 120}ms ease`,
            }}
          >
            <div className="p-8 lg:p-12 flex flex-col h-full">

              {/* Big number */}
              <span
                className="font-display font-black block mb-8"
                style={{
                  fontSize: 'clamp(64px, 8vw, 120px)',
                  lineHeight: 0.85,
                  letterSpacing: '-0.04em',
                  color: 'rgba(232,232,232,0.06)',
                }}
              >
                {s.num}
              </span>

              {/* Title */}
              <h3
                className="font-display font-black text-snow mb-5"
                style={{
                  fontSize: 'clamp(24px, 2.4vw, 38px)',
                  lineHeight: 0.95,
                  letterSpacing: '-0.02em',
                }}
              >
                {s.title}
              </h3>

              {/* Body */}
              <p
                className="font-mono text-muted mt-auto"
                style={{
                  fontSize: 'clamp(11px, 0.9vw, 13px)',
                  letterSpacing: '0.04em',
                  lineHeight: 1.75,
                }}
              >
                {s.body}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Bottom note */}
      <p
        className="font-mono text-muted mt-8"
        style={{
          fontSize: '11px',
          letterSpacing: '0.06em',
          opacity: visible ? 0.6 : 0,
          transition: 'opacity 0.6s 500ms ease',
        }}
      >
        {note}
      </p>
    </section>
  )
}
