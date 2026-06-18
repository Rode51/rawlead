'use client'

import { useState } from 'react'
import TerminalLog from './TerminalLog'

const CASES = [
  {
    number: '01',
    title: 'ПАРСЕР',
    stack: ['Python · Playwright · httpx', 'прокси-каскад · автобан по источнику', 'Neon Postgres · SQLite', '7 источников · ~50с цикл'],
    body: 'Радар опрашивает биржи каждую минуту: стандартный HTTP там где пускают, браузерный Playwright — там где антибот. Прокси-каскад с автобаном по источнику, дедупликация по хэшу текста. Заказ попадает в очередь L1 через секунды после публикации.',
    extra: <TerminalLog />,
  },
  {
    number: '02',
    title: 'AI-СЛОИ',
    stack: ['OpenRouter · Flash-lite · Gemini Pro', 'L1 / L2 / L3 pipeline', 'judge-цикл (Sonnet)', '4 воркера · 2 API-ключа'],
    body: 'L1 (дешёвая модель) — каждый лид: теги, score, видимость в ленте. L2 — один shared черновик на заказ при ingest. L3 — персональная переформулировка при первом клике подписчика. Judge-цикл держит качество по combined score, промпты правятся по отчёту.',
    extra: null,
  },
  {
    number: '03',
    title: 'TG-БОТЫ',
    stack: ['Telethon · Telegram Bot API', 'FastAPI JWT auth', 'watchdog · push по матчам', 'TG Login без форм'],
  body: 'Вход на сайт — через Telegram, без форм и паролей. Watchdog следит за радаром: если цикл провалился — алерт в личку. Бот уведомляет при новом матче по стеку навыков. Dogfood-поток шёл через бот ещё до запуска открытой ленты.',
    extra: null,
  },
  {
    number: '04',
    title: 'ИНТЕРФЕЙС',
    stack: ['WordPress · Kadence child theme', 'FastAPI · Neon Postgres', '/lenta/ · /cabinet/', 'skill tree · 51+ тег · % стека'],
    body: 'Открытая лента с сортировкой по % совместимости стека — без регистрации. Кабинет: inbox откликов, skill tree по 4 нишам, TG-аватар. API — FastAPI поверх Neon; WP не лезет в Postgres напрямую. Дизайн — NEO-BRUTALIST, Kadence child theme.',
    extra: null,
  },
]

export default function Cases() {
  const [open, setOpen] = useState<number | null>(null)

  const toggle = (i: number) => setOpen(prev => (prev === i ? null : i))

  return (
    <section className="border-t border-edge">
      {/* Section label */}
      <div className="px-10 lg:px-20 pt-16 pb-6">
        <span className="font-mono text-muted" style={{ fontSize: '11px', letterSpacing: '0.18em' }}>
          КЕЙСЫ — RAWLEAD
        </span>
      </div>

      {/* Accordion */}
      <div>
        {CASES.map((c, i) => {
          const isOpen = open === i
          return (
            <div key={i} className="border-t border-edge">
              {/* Row header */}
              <button
                onClick={() => toggle(i)}
                className="w-full px-10 lg:px-20 py-6 flex items-center justify-between text-left group"
                style={{ cursor: 'none' }}
              >
                <div className="flex items-baseline gap-6">
                  <span className="font-mono text-muted" style={{ fontSize: '11px', letterSpacing: '0.15em' }}>
                    {c.number}
                  </span>
                  <span
                    className="font-display font-black text-snow group-hover:text-amber transition-colors"
                    style={{ fontSize: 'clamp(28px, 5vw, 72px)', letterSpacing: '-0.02em', lineHeight: 1 }}
                  >
                    {c.title}
                  </span>
                </div>
                <span
                  className="font-mono text-muted group-hover:text-snow transition-colors"
                  style={{ fontSize: '20px', lineHeight: 1, flexShrink: 0 }}
                >
                  {isOpen ? '×' : '+'}
                </span>
              </button>

              {/* Expandable content — grid trick for smooth height */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateRows: isOpen ? '1fr' : '0fr',
                  transition: 'grid-template-rows 0.45s cubic-bezier(0.22,1,0.36,1)',
                }}
              >
                <div style={{ overflow: 'hidden' }}>
                  <div className="px-10 lg:px-20 pb-12 pt-2 grid grid-cols-1 lg:grid-cols-[220px_1fr] gap-8 lg:gap-20">
                    {/* Stack */}
                    <div className="flex flex-col gap-3">
                      {c.stack.map((tag, j) => (
                        <span
                          key={j}
                          className="font-mono text-muted"
                          style={{ fontSize: '11px', letterSpacing: '0.08em', lineHeight: 1.6 }}
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                    {/* Description */}
                    <div>
                      <p
                        className="font-mono text-snow leading-relaxed"
                        style={{ fontSize: 'clamp(12px, 1vw, 14px)', maxWidth: '580px' }}
                      >
                        {c.body}
                      </p>
                      {c.extra}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
