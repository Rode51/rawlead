'use client'

import { useRef, useState, useCallback, type ReactNode } from 'react'
import TerminalLog from './TerminalLog'
import Typewriter from './Typewriter'

interface CaseData {
  number: string
  title: string
  preview: string
  stack: string[]
  body: string
  extra?: ReactNode
}

const CASES: CaseData[] = [
  {
    number: '01',
    title: 'ПАРСЕР',
    preview: '7 площадок · ~50с цикл',
    stack: [
      '7 площадок одновременно',
      'обход антибот-защит',
      'цикл обновления ~50 сек',
      'дедупликация и фильтрация',
    ],
    body: 'Система сама мониторит FL.ru, Kwork, YouDo и Telegram-каналы — без твоего участия. Новый заказ появляется в ленте через секунды после публикации. Ручной поиск больше не нужен.',
    extra: <TerminalLog />,
  },
  {
    number: '02',
    title: 'AI-ФИЛЬТР',
    preview: '3 уровня · черновик на матч',
    stack: [
      'три уровня анализа',
      'совместимость по навыкам',
      'черновик отклика на каждый матч',
      'качество контролирует ИИ-судья',
    ],
    body: 'ИИ читает каждый заказ и оценивает насколько он подходит под твой стек. При совпадении — готовит черновик отклика: не шаблон, а текст под конкретный запрос. Ты тратишь минуту вместо пятнадцати.',
  },
  {
    number: '03',
    title: 'TG-БОТЫ',
    preview: 'вход без форм · алерты',
    stack: [
      'вход через Telegram — без форм',
      'уведомление при новом матче',
      'алерт если система встала',
      'работает 24/7',
    ],
    body: 'Авторизация — один клик через Telegram, никаких паролей. Новый подходящий заказ — мгновенное уведомление в мессенджер. Если система вдруг остановится — приходит алерт, не молчит.',
  },
  {
    number: '04',
    title: 'ИНТЕРФЕЙС',
    preview: 'лента · кабинет · % совместимости',
    stack: [
      'открытая лента без регистрации',
      'личный кабинет с откликами',
      'настройка навыков по нишам',
      'сортировка по совместимости %',
    ],
    body: 'Открытая лента с сортировкой заказов по проценту совместимости со стеком — можно смотреть без регистрации. В кабинете: история откликов, настройка навыков по 4 нишам, профиль из Telegram.',
  },
]

const TECH = [
  'Python', 'FastAPI', 'Playwright', 'OpenRouter',
  'Telegram Bot API', 'WordPress', 'Neon Postgres', 'Tauri',
]

const DESC = 'RawLead следит за биржами вместо тебя: собирает заказы, сортирует по совместимости стека и готовит черновик отклика на каждый подходящий лид. Запущен, работает, обрабатывает заказы в реальном времени.'

export default function Projects() {
  const [projectOpen, setProjectOpen] = useState(false)
  const [activeCase,  setActiveCase]  = useState<number | null>(null)

  // ── Drag state (refs = no re-renders during drag) ──
  const railRef     = useRef<HTMLDivElement>(null)
  const isDragging  = useRef(false)
  const startX      = useRef(0)
  const startScroll = useRef(0)
  const dragDelta   = useRef(0)
  const [grabbing, setGrabbing] = useState(false)
  const [hinted,   setHinted]   = useState(false)

  const onMouseDown = useCallback((e: React.MouseEvent) => {
    if (!railRef.current) return
    isDragging.current  = true
    dragDelta.current   = 0
    startX.current      = e.pageX
    startScroll.current = railRef.current.scrollLeft
    setGrabbing(true)
    setHinted(true)
  }, [])

  const onMouseMove = useCallback((e: React.MouseEvent) => {
    if (!isDragging.current || !railRef.current) return
    const dx = e.pageX - startX.current
    dragDelta.current = Math.abs(dx)
    railRef.current.scrollLeft = startScroll.current - dx * 1.15
  }, [])

  const onMouseUp = useCallback(() => {
    isDragging.current = false
    setGrabbing(false)
  }, [])

  const onTouchStart = useCallback((e: React.TouchEvent) => {
    if (!railRef.current) return
    isDragging.current  = true
    dragDelta.current   = 0
    startX.current      = e.touches[0].pageX
    startScroll.current = railRef.current.scrollLeft
    setHinted(true)
  }, [])

  const onTouchMove = useCallback((e: React.TouchEvent) => {
    if (!isDragging.current || !railRef.current) return
    const dx = e.touches[0].pageX - startX.current
    dragDelta.current = Math.abs(dx)
    railRef.current.scrollLeft = startScroll.current - dx
  }, [])

  const onTouchEnd = useCallback(() => {
    isDragging.current = false
  }, [])

  const handleCardClick = (i: number) => {
    if (dragDelta.current > 6) return
    setActiveCase(prev => prev === i ? null : i)
  }

  const toggleProject = () => {
    setProjectOpen(p => !p)
    if (projectOpen) setActiveCase(null)
  }

  const active = activeCase !== null ? CASES[activeCase] : null

  return (
    <section id="projects" className="border-t border-edge px-10 lg:px-20 py-20 lg:py-32">

      {/* Section label */}
      <div className="mb-10">
        <span className="font-mono text-muted" style={{ fontSize: '11px', letterSpacing: '0.18em' }}>
          / ПРОЕКТЫ
        </span>
      </div>

      {/* ── Project card ── */}
      <div
        className="border transition-colors duration-500"
        style={{
          borderColor: projectOpen ? 'rgba(245,166,35,0.28)' : '#1e1e1e',
          background: '#0c0c0c',
        }}
      >
        {/* ─ Card header ─ */}
        <button onClick={toggleProject} className="w-full text-left">
          <div className="p-8 lg:p-14 flex items-start justify-between gap-8">
            <div>
              <h2
                className="font-display font-black transition-colors duration-300"
                style={{
                  fontSize: 'clamp(56px, 12vw, 190px)',
                  lineHeight: 0.88,
                  letterSpacing: '-0.03em',
                  color: projectOpen ? '#F5A623' : '#e8e8e8',
                }}
              >
                RAWLEAD
              </h2>
              <p
                className="font-mono text-muted mt-4"
                style={{ fontSize: 'clamp(11px, 0.9vw, 13px)', letterSpacing: '0.1em' }}
              >
                Находит заказы. Пишет отклики. Работает сам.
              </p>
            </div>
            <div className="flex flex-col items-end gap-3 pt-1 flex-shrink-0">
              <span className="font-mono text-muted" style={{ fontSize: '10px', letterSpacing: '0.15em' }}>2025</span>
              <span
                className="font-mono transition-colors duration-300"
                style={{ fontSize: '11px', letterSpacing: '0.12em', color: projectOpen ? '#F5A623' : '#444' }}
              >
                {projectOpen ? '× ЗАКРЫТЬ' : '→ ОТКРЫТЬ'}
              </span>
            </div>
          </div>
        </button>

        {/* ─ Expandable body ─ */}
        <div style={{
          display: 'grid',
          gridTemplateRows: projectOpen ? '1fr' : '0fr',
          transition: 'grid-template-rows 0.6s cubic-bezier(0.22,1,0.36,1)',
        }}>
          <div style={{ overflow: 'hidden' }}>
            <div className="border-t border-edge">

              {/* Description */}
              <div className="p-8 lg:p-14">
                <p className="font-mono text-snow leading-relaxed"
                  style={{ fontSize: 'clamp(12px, 1.1vw, 15px)', maxWidth: '600px', minHeight: '4em' }}>
                  <Typewriter text={DESC} active={projectOpen} delay={200} speed={18} />
                </p>

                {/* Metrics */}
                <div className="flex flex-wrap gap-8 mt-10">
                  {[
                    ['7',    'площадок'],
                    ['~50с', 'до появления в ленте'],
                    ['3',    'слоя ИИ-анализа'],
                    ['24/7', 'на проде'],
                  ].map(([val, label]) => (
                    <div key={label} className="flex flex-col gap-1">
                      <span className="font-display font-black text-amber"
                        style={{ fontSize: 'clamp(22px, 2.8vw, 38px)', lineHeight: 1, letterSpacing: '-0.02em' }}>
                        {val}
                      </span>
                      <span className="font-mono text-muted" style={{ fontSize: '10px', letterSpacing: '0.1em' }}>
                        {label}
                      </span>
                    </div>
                  ))}
                </div>

                {/* Tech */}
                <div className="flex flex-wrap gap-2 mt-10">
                  {TECH.map(t => (
                    <span key={t} className="font-mono border border-edge text-muted px-3 py-1"
                      style={{ fontSize: '10px', letterSpacing: '0.08em' }}>
                      {t}
                    </span>
                  ))}
                </div>

                {/* Link */}
                <div className="mt-8">
                  <a href="https://rawlead.ru" target="_blank" rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 font-mono text-snow border border-edge px-5 py-2 hover:border-amber hover:text-amber transition-colors"
                    style={{ fontSize: '11px', letterSpacing: '0.1em' }}>
                    rawlead.ru <span style={{ fontSize: '10px', opacity: 0.7 }}>↗</span>
                  </a>
                </div>
              </div>

              {/* ─ Cases horizontal rail ─ */}
              <div className="border-t border-edge">

                {/* Rail header */}
                <div className="px-8 lg:px-14 py-5 flex items-center justify-between">
                  <span className="font-mono text-muted" style={{ fontSize: '11px', letterSpacing: '0.15em' }}>
                    <Typewriter text="— ЧТО ВНУТРИ" active={projectOpen} delay={800} speed={40} />
                  </span>
                  <span
                    className="font-mono text-muted transition-opacity duration-700"
                    style={{ fontSize: '10px', letterSpacing: '0.14em', opacity: hinted ? 0 : 0.5 }}
                  >
                    ← DRAG →
                  </span>
                </div>

                {/* Draggable rail */}
                <div
                  ref={railRef}
                  className="flex border-t border-edge select-none"
                  style={{
                    overflowX: 'auto',
                    overflowY: 'hidden',
                    scrollbarWidth: 'none',
                    cursor: grabbing ? 'grabbing' : 'grab',
                    msOverflowStyle: 'none',
                  }}
                  onMouseDown={onMouseDown}
                  onMouseMove={onMouseMove}
                  onMouseUp={onMouseUp}
                  onMouseLeave={onMouseUp}
                  onTouchStart={onTouchStart}
                  onTouchMove={onTouchMove}
                  onTouchEnd={onTouchEnd}
                >
                  {CASES.map((c, i) => (
                    <div
                      key={i}
                      onClick={() => handleCardClick(i)}
                      className="flex-shrink-0 border-r border-edge flex flex-col justify-between"
                      style={{
                        width: 'clamp(240px, 28vw, 380px)',
                        padding: 'clamp(24px, 3vw, 48px)',
                        paddingBottom: 'clamp(28px, 3.5vw, 56px)',
                        opacity: activeCase === i ? 1 : activeCase === null ? 0.55 : 0.28,
                        borderLeft: activeCase === i ? '1px solid rgba(245,166,35,0.35)' : '1px solid transparent',
                        transition: 'opacity 0.4s ease, border-color 0.4s ease',
                        background: activeCase === i ? 'rgba(245,166,35,0.03)' : 'transparent',
                      }}
                    >
                      {/* Number */}
                      <span
                        className="font-display font-black block"
                        style={{
                          fontSize: 'clamp(56px, 10vw, 140px)',
                          lineHeight: 0.85,
                          letterSpacing: '-0.04em',
                          color: activeCase === i ? 'rgba(245,166,35,0.18)' : 'rgba(232,232,232,0.06)',
                          transition: 'color 0.4s ease',
                          userSelect: 'none',
                        }}
                      >
                        {c.number}
                      </span>

                      {/* Title */}
                      <div className="mt-auto pt-6">
                        <h3
                          className="font-display font-black"
                          style={{
                            fontSize: 'clamp(28px, 4vw, 58px)',
                            lineHeight: 0.92,
                            letterSpacing: '-0.025em',
                            color: activeCase === i ? '#F5A623' : '#e8e8e8',
                            transition: 'color 0.35s ease',
                            userSelect: 'none',
                          }}
                        >
                          {c.title}
                        </h3>
                        <p
                          className="font-mono text-muted mt-3"
                          style={{ fontSize: '10px', letterSpacing: '0.1em', userSelect: 'none' }}
                        >
                          {c.preview}
                        </p>
                      </div>
                    </div>
                  ))}

                  {/* Trailing spacer so last card isn't flush right */}
                  <div className="flex-shrink-0" style={{ width: 'clamp(24px, 3vw, 48px)' }} />
                </div>

                {/* ─ Detail panel ─ */}
                <div style={{
                  display: 'grid',
                  gridTemplateRows: activeCase !== null ? '1fr' : '0fr',
                  transition: 'grid-template-rows 0.55s cubic-bezier(0.22,1,0.36,1)',
                }}>
                  <div style={{ overflow: 'hidden' }}>
                    {active && (
                      <div
                        className="border-t border-edge grid grid-cols-1 lg:grid-cols-[220px_1fr] gap-8 lg:gap-20"
                        style={{ padding: 'clamp(24px, 4vw, 56px)' }}
                      >
                        {/* Stack */}
                        <div className="flex flex-col gap-3">
                          {active.stack.map((tag, j) => (
                            <span
                              key={j}
                              className="font-mono text-muted"
                              style={{
                                fontSize: '11px',
                                letterSpacing: '0.08em',
                                lineHeight: 1.6,
                                opacity: activeCase !== null ? 1 : 0,
                                transform: activeCase !== null ? 'none' : 'translateX(-10px)',
                                transition: `opacity 0.4s ${j * 55 + 60}ms ease, transform 0.4s ${j * 55 + 60}ms ease`,
                              }}
                            >
                              {tag}
                            </span>
                          ))}
                        </div>

                        {/* Body */}
                        <div>
                          <p
                            className="font-mono text-snow leading-relaxed"
                            style={{ fontSize: 'clamp(12px, 1vw, 15px)', maxWidth: '560px', minHeight: '3em' }}
                          >
                            <Typewriter
                              key={activeCase}
                              text={active.body}
                              active={activeCase !== null}
                              delay={100}
                              speed={15}
                            />
                          </p>
                          {active.extra}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

              </div>
            </div>
          </div>
        </div>

      </div>
    </section>
  )
}
