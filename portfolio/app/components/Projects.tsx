'use client'

import { useRef, useState, useCallback } from 'react'
import TerminalLog from './TerminalLog'
import Typewriter from './Typewriter'

interface CaseContent {
  title: string
  preview: string
  stack: string[]
  body: string
}

interface Metric { val: string; label: string }

interface ProjectsContent {
  label: string
  subtitle: string
  desc: string
  metrics: Metric[]
  inProd: string
  whatInside: string
  open: string
  close: string
  cases: CaseContent[]
}

interface Props { content?: ProjectsContent }

const DEFAULT: ProjectsContent = {
  label:    '/ ПРОЕКТЫ',
  subtitle: 'Находит заказы. Пишет отклики. Работает сам.',
  desc:     'RawLead следит за биржами вместо тебя: собирает заказы, сортирует по совместимости стека и готовит черновик отклика на каждый подходящий лид. Запущен, работает, обрабатывает заказы в реальном времени.',
  metrics: [
    { val: '7',    label: 'площадок' },
    { val: '~50с', label: 'до появления в ленте' },
    { val: '3',    label: 'слоя ИИ-анализа' },
    { val: '24/7', label: 'на проде' },
  ],
  inProd:      '/ В ПРОДЕ',
  whatInside:  '— ЧТО ВНУТРИ',
  open:        '→ ОТКРЫТЬ',
  close:       '× ЗАКРЫТЬ',
  cases: [
    {
      title:   'ПАРСЕР',
      preview: '7 площадок · ~50с цикл',
      stack:   ['7 площадок одновременно', 'обход антибот-защит', 'цикл обновления ~50 сек', 'дедупликация и фильтрация'],
      body:    'Система сама мониторит FL.ru, Kwork, YouDo и Telegram-каналы — без твоего участия. Новый заказ появляется в ленте через секунды после публикации. Ручной поиск больше не нужен.',
    },
    {
      title:   'AI-ФИЛЬТР',
      preview: '3 уровня · черновик на матч',
      stack:   ['три уровня анализа', 'совместимость по навыкам', 'черновик отклика на каждый матч', 'качество контролирует ИИ-судья'],
      body:    'ИИ читает каждый заказ и оценивает насколько он подходит под твой стек. При совпадении — готовит черновик отклика: не шаблон, а текст под конкретный запрос. Ты тратишь минуту вместо пятнадцати.',
    },
    {
      title:   'TG-БОТЫ',
      preview: 'вход без форм · алерты',
      stack:   ['вход через Telegram — без форм', 'уведомление при новом матче', 'алерт если система встала', 'работает 24/7'],
      body:    'Авторизация — один клик через Telegram, никаких паролей. Новый подходящий заказ — мгновенное уведомление в мессенджер. Если система вдруг остановится — приходит алерт, не молчит.',
    },
    {
      title:   'ИНТЕРФЕЙС',
      preview: 'лента · кабинет · % совместимости',
      stack:   ['открытая лента без регистрации', 'личный кабинет с откликами', 'настройка навыков по нишам', 'сортировка по совместимости %'],
      body:    'Открытая лента с сортировкой заказов по проценту совместимости со стеком — можно смотреть без регистрации. В кабинете: история откликов, настройка навыков по 4 нишам, профиль из Telegram.',
    },
  ],
}

const TECH = ['Python', 'FastAPI', 'Playwright', 'OpenRouter', 'Telegram Bot API', 'WordPress', 'Neon Postgres', 'Tauri']

export default function Projects({ content }: Props) {
  const c = content ?? DEFAULT

  const [projectOpen, setProjectOpen] = useState(false)
  const [activeCase,  setActiveCase]  = useState<number | null>(null)

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
    if (!isDragging.current) return
    dragDelta.current = Math.abs(e.touches[0].pageX - startX.current)
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

  const activeCase_ = activeCase !== null ? c.cases[activeCase] : null

  return (
    <section id="projects" className="border-t border-edge px-10 lg:px-20 py-20 lg:py-32">

      {/* Section label */}
      <div className="mb-10">
        <span className="font-mono text-muted" style={{ fontSize: '11px', letterSpacing: '0.18em' }}>
          {c.label}
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
          <div className="p-8 lg:p-14 flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4 lg:gap-8">
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
                {c.subtitle}
              </p>
            </div>
            <div className="flex flex-row justify-between items-center lg:flex-col lg:items-end gap-3 lg:pt-1 flex-shrink-0">
              <span className="font-mono text-muted" style={{ fontSize: '10px', letterSpacing: '0.15em' }}>2025</span>
              <span
                className="font-mono transition-colors duration-300"
                style={{ fontSize: '11px', letterSpacing: '0.12em', color: projectOpen ? '#F5A623' : '#444' }}
              >
                {projectOpen ? c.close : c.open}
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
                  <Typewriter text={c.desc} active={projectOpen} delay={200} speed={18} />
                </p>

                {/* Metrics */}
                <div className="flex flex-wrap gap-8 mt-10">
                  {c.metrics.map(({ val, label }) => (
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

                {/* Demo video */}
                <div className="mt-12">
                  <span className="font-mono text-muted block mb-5" style={{ fontSize: '10px', letterSpacing: '0.18em' }}>
                    {c.inProd}
                  </span>
                  <div
                    className="border border-edge overflow-hidden"
                    style={{ maxWidth: 640, background: '#0a0a0a' }}
                  >
                    <div className="border-b border-edge px-3 py-2 flex items-center gap-2" style={{ background: '#111' }}>
                      {[0,1,2].map(j => (
                        <div key={j} style={{ width: 7, height: 7, borderRadius: '50%', background: '#2a2a2a' }} />
                      ))}
                      <span className="font-mono text-muted ml-2" style={{ fontSize: '9px', letterSpacing: '0.1em' }}>
                        rawlead.ru
                      </span>
                    </div>
                    <video
                      src="/rawlead-demo.mp4"
                      autoPlay
                      muted
                      loop
                      playsInline
                      style={{ width: '100%', display: 'block' }}
                    />
                  </div>
                </div>
              </div>

              {/* ─ Cases horizontal rail ─ */}
              <div className="border-t border-edge">

                {/* Rail header */}
                <div className="px-8 lg:px-14 py-5 flex items-center justify-between">
                  <span className="font-mono text-muted" style={{ fontSize: '11px', letterSpacing: '0.15em' }}>
                    <Typewriter text={c.whatInside} active={projectOpen} delay={800} speed={40} />
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
                    WebkitOverflowScrolling: 'touch',
                    touchAction: 'pan-x',
                  }}
                  onMouseDown={onMouseDown}
                  onMouseMove={onMouseMove}
                  onMouseUp={onMouseUp}
                  onMouseLeave={onMouseUp}
                  onTouchStart={onTouchStart}
                  onTouchMove={onTouchMove}
                  onTouchEnd={onTouchEnd}
                >
                  {c.cases.map((cs, i) => (
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
                        {String(i + 1).padStart(2, '0')}
                      </span>

                      <div className="mt-auto pt-6">
                        <h3
                          className="font-mono font-semibold"
                          style={{
                            fontSize: 'clamp(11px, 1.1vw, 14px)',
                            letterSpacing: '0.22em',
                            lineHeight: 1.3,
                            color: activeCase === i ? '#F5A623' : '#e8e8e8',
                            transition: 'color 0.35s ease',
                            userSelect: 'none',
                          }}
                        >
                          {cs.title}
                        </h3>
                        <p
                          className="font-mono text-muted mt-3"
                          style={{ fontSize: '10px', letterSpacing: '0.1em', userSelect: 'none' }}
                        >
                          {cs.preview}
                        </p>
                      </div>
                    </div>
                  ))}

                  <div className="flex-shrink-0" style={{ width: 'clamp(24px, 3vw, 48px)' }} />
                </div>

                {/* ─ Detail panel ─ */}
                <div style={{
                  display: 'grid',
                  gridTemplateRows: activeCase !== null ? '1fr' : '0fr',
                  transition: 'grid-template-rows 0.55s cubic-bezier(0.22,1,0.36,1)',
                }}>
                  <div style={{ overflow: 'hidden' }}>
                    {activeCase_ && (
                      <div
                        className="border-t border-edge grid grid-cols-1 lg:grid-cols-[220px_1fr] gap-8 lg:gap-20"
                        style={{ padding: 'clamp(24px, 4vw, 56px)' }}
                      >
                        {/* Stack */}
                        <div className="flex flex-col gap-3">
                          {activeCase_.stack.map((tag, j) => (
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
                              text={activeCase_.body}
                              active={activeCase !== null}
                              delay={100}
                              speed={15}
                            />
                          </p>
                          {activeCase === 0 && <TerminalLog />}
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
