'use client'

import { useEffect, useRef, useState } from 'react'

export default function Footer() {
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

  return (
    <footer
      id="footer"
      ref={ref}
      className="border-t border-edge px-10 lg:px-20 py-24 lg:py-40"
    >
      <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-12">

        {/* Left — CTA headline */}
        <div>
          <p
            className="font-mono text-muted mb-4"
            style={{ fontSize: '11px', letterSpacing: '0.18em' }}
          >
            / СВЯЗАТЬСЯ
          </p>
          <h2
            className="font-display font-black text-snow"
            style={{
              fontSize: 'clamp(36px, 6vw, 96px)',
              lineHeight: 0.92,
              letterSpacing: '-0.025em',
              opacity: visible ? 1 : 0,
              transform: visible ? 'none' : 'translateY(16px)',
              transition: 'opacity 0.7s ease, transform 0.7s ease',
            }}
          >
            Есть задача<span className="text-amber">?</span>
          </h2>
          <p
            className="font-mono text-muted mt-8"
            style={{
              fontSize: 'clamp(12px, 1vw, 14px)',
              letterSpacing: '0.04em',
              lineHeight: 1.7,
              maxWidth: '380px',
              opacity: visible ? 1 : 0,
              transform: visible ? 'none' : 'translateY(12px)',
              transition: 'opacity 0.7s 150ms ease, transform 0.7s 150ms ease',
            }}
          >
            Напишите — расскажите что нужно сделать.<br />
            Отвечу быстро, без воды.
          </p>
        </div>

        {/* Right — contact block */}
        <div
          className="flex flex-col gap-4"
          style={{
            opacity: visible ? 1 : 0,
            transform: visible ? 'none' : 'translateY(12px)',
            transition: 'opacity 0.7s 300ms ease, transform 0.7s 300ms ease',
          }}
        >
          <a
            href="https://t.me/rcnn43"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-3 font-mono font-medium bg-amber text-void px-8 py-4 hover:opacity-90 transition-opacity"
            style={{ fontSize: 'clamp(12px, 1vw, 15px)', letterSpacing: '0.08em' }}
          >
            → Написать в Telegram
          </a>

          <p
            className="font-mono text-muted text-right"
            style={{ fontSize: '10px', letterSpacing: '0.12em' }}
          >
            @rcnn43
          </p>
        </div>

      </div>

      {/* Bottom bar */}
      <div
        className="mt-20 pt-6 border-t border-edge flex justify-between items-center"
        style={{
          opacity: visible ? 1 : 0,
          transition: 'opacity 0.7s 500ms ease',
        }}
      >
        <span className="font-mono text-muted" style={{ fontSize: '10px', letterSpacing: '0.12em' }}>
          RODE51 · 2026
        </span>
        <span className="font-mono text-muted" style={{ fontSize: '10px', letterSpacing: '0.12em' }}>
          МОСКВА
        </span>
      </div>

    </footer>
  )
}
