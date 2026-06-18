'use client'

import { useEffect, useRef, useState } from 'react'

const PILLARS = ['Парсер', 'AI-слои', 'TG-боты', 'Интерфейс']

export default function ProductResult() {
  const ref = useRef<HTMLElement>(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const io = new IntersectionObserver(
      ([e]) => { if (e.isIntersecting) setVisible(true) },
      { threshold: 0.2 },
    )
    io.observe(el)
    return () => io.disconnect()
  }, [])

  const reveal = (delay: number) => ({
    opacity: visible ? 1 : 0,
    transform: visible ? 'none' : 'translateY(16px)',
    transition: `opacity 0.7s ${delay}ms cubic-bezier(0.22,1,0.36,1), transform 0.7s ${delay}ms cubic-bezier(0.22,1,0.36,1)`,
  })

  return (
    <section
      ref={ref}
      className="px-10 lg:px-20 py-24 lg:py-40 border-t border-edge"
    >
      {/* Label */}
      <div style={reveal(0)}>
        <span className="font-mono text-muted" style={{ fontSize: '11px', letterSpacing: '0.18em' }}>
          РЕЗУЛЬТАТ
        </span>
      </div>

      {/* Pillars → arrow → product */}
      <div
        className="mt-10 flex flex-wrap items-center gap-3"
        style={reveal(80)}
      >
        {PILLARS.map((p, i) => (
          <span key={i} className="flex items-center gap-3">
            <span
              className="font-mono border border-edge text-snow px-3 py-1"
              style={{ fontSize: '11px', letterSpacing: '0.1em' }}
            >
              {p}
            </span>
            {i < PILLARS.length - 1 && (
              <span className="font-mono text-muted" style={{ fontSize: '11px' }}>+</span>
            )}
          </span>
        ))}
        <span className="font-mono text-muted" style={{ fontSize: '11px', marginLeft: '4px' }}>→</span>
        <span
          className="font-display font-black text-amber"
          style={{ fontSize: 'clamp(20px, 3vw, 40px)', letterSpacing: '-0.02em', lineHeight: 1 }}
        >
          RAWLEAD
        </span>
      </div>

      {/* Description */}
      <p
        className="font-mono text-muted mt-8 leading-relaxed"
        style={{ fontSize: 'clamp(12px, 1vw, 14px)', maxWidth: '560px', ...reveal(160) }}
      >
        Агрегатор фриланс-заказов с ИИ-модерацией и подбором по стеку.
        Все четыре части работают вместе на одном VPS, 24/7.
        MVP — на проде. Биллинг и O101 в следующем релизе.
      </p>

      {/* Link */}
      <div className="mt-10" style={reveal(240)}>
        <a
          href="https://rawlead.ru"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-3 font-mono text-snow border border-edge px-5 py-3 hover:border-amber hover:text-amber transition-colors"
          style={{ fontSize: '12px', letterSpacing: '0.1em', cursor: 'none' }}
        >
          rawlead.ru
          <span style={{ fontSize: '10px', opacity: 0.6 }}>↗</span>
        </a>
      </div>
    </section>
  )
}
