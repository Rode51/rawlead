'use client'

import { useEffect, useRef, useState } from 'react'

const STEPS = [
  {
    num: '01',
    title: 'Описываешь задачу',
    body: 'В Telegram или голосом. Без брифов и технических заданий — просто расскажи что нужно сделать и зачем.',
  },
  {
    num: '02',
    title: 'Согласовываем решение',
    body: 'Я предлагаю что конкретно делаем, сколько займёт и что получишь на выходе. Никаких сюрпризов в процессе.',
  },
  {
    num: '03',
    title: 'Принимаешь результат',
    body: 'Оплата после — когда убедился что всё работает как надо. Сдаю с документацией и остаюсь на связи.',
  },
]

export default function Process() {
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
          / КАК РАБОТАЕМ
        </span>
      </div>

      {/* Steps */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-0 border-l border-t border-edge">
        {STEPS.map((s, i) => (
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
        Обычно от первого сообщения до результата — меньше недели.
      </p>
    </section>
  )
}
