'use client'

import { useEffect, useRef, useState } from 'react'

const SERVICES = [
  {
    title: 'БОТ',
    body: 'Telegram-бот под задачу — уведомления, очереди, приём заявок без приложения',
    icon: (
      <svg width="36" height="36" viewBox="0 0 36 36" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
        <rect x="7" y="11" width="22" height="18" rx="3" />
        <circle cx="13" cy="19" r="2" />
        <circle cx="23" cy="19" r="2" />
        <line x1="18" y1="11" x2="18" y2="7" />
        <circle cx="18" cy="6" r="1.8" fill="currentColor" stroke="none" />
        <line x1="7"  y1="23" x2="4"  y2="23" />
        <line x1="29" y1="23" x2="32" y2="23" />
        <line x1="13" y1="26" x2="23" y2="26" strokeOpacity="0.4" />
      </svg>
    ),
  },
  {
    title: 'ПАРСЕР',
    body: 'Собираю данные с любых сайтов — включая те, где стоит защита',
    icon: (
      <svg width="36" height="36" viewBox="0 0 36 36" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round">
        <circle cx="15" cy="15" r="8" />
        <line x1="21" y1="21" x2="30" y2="30" />
        <line x1="10" y1="15" x2="20" y2="15" strokeOpacity="0.5" />
        <line x1="15" y1="10" x2="15" y2="20" strokeOpacity="0.5" />
      </svg>
    ),
  },
  {
    title: 'АВТОМАТИЗАЦИЯ',
    body: 'Убираю ручной труд — скрипты, воркеры, расписания вместо человека',
    icon: (
      <svg width="36" height="36" viewBox="0 0 36 36" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
        <path d="M18 6 A12 12 0 1 1 6 18" />
        <polyline points="6,10 6,18 14,18" />
        <circle cx="18" cy="18" r="3" fill="currentColor" stroke="none" opacity="0.5" />
      </svg>
    ),
  },
  {
    title: 'ИНТЕГРАЦИЯ',
    body: 'Соединяю сервисы между собой — API, вебхуки, базы данных, внешние источники',
    icon: (
      <svg width="36" height="36" viewBox="0 0 36 36" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round">
        <rect x="2"  y="13" width="10" height="10" rx="2" />
        <rect x="24" y="13" width="10" height="10" rx="2" />
        <line x1="12" y1="18" x2="24" y2="18" />
        <circle cx="18" cy="18" r="2.5" fill="currentColor" stroke="none" />
      </svg>
    ),
  },
]

export default function Services() {
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
      id="services"
      className="border-t border-edge px-10 lg:px-20 py-20 lg:py-32"
    >
      {/* Label */}
      <div className="mb-12">
        <span className="font-mono text-muted" style={{ fontSize: '11px', letterSpacing: '0.18em' }}>
          / ЧТО ДЕЛАЮ
        </span>
      </div>

      {/* Cards grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 border-l border-t border-edge">
        {SERVICES.map((s, i) => (
          <div
            key={s.title}
            className="border-r border-b border-edge group"
            style={{
              opacity:   visible ? 1 : 0,
              transform: visible ? 'none' : 'translateY(18px)',
              transition: `opacity 0.55s ${i * 90}ms ease, transform 0.55s ${i * 90}ms ease`,
            }}
          >
            <div
              className="h-full flex flex-col gap-6 p-8 lg:p-10 transition-colors duration-300"
              style={{ background: 'transparent' }}
            >
              {/* Icon */}
              <div
                className="text-muted group-hover:text-snow transition-colors duration-300"
                style={{ lineHeight: 0 }}
              >
                {s.icon}
              </div>

              {/* Title */}
              <h3
                className="font-display font-black text-snow"
                style={{
                  fontSize: 'clamp(22px, 2.2vw, 34px)',
                  lineHeight: 0.92,
                  letterSpacing: '-0.02em',
                }}
              >
                {s.title}
              </h3>

              {/* Body */}
              <p
                className="font-mono text-muted mt-auto"
                style={{
                  fontSize: 'clamp(10px, 0.85vw, 12px)',
                  letterSpacing: '0.04em',
                  lineHeight: 1.7,
                }}
              >
                {s.body}
              </p>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
