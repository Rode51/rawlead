'use client'

import { useEffect, useState } from 'react'
import ScrambleTitle from './ScrambleTitle'
import Ticker from './Ticker'
import Typewriter from './Typewriter'

const ROLE  = 'РАЗРАБОТКА · АВТОМАТИЗАЦИЯ · ИНТЕГРАЦИИ'
const LINE1 = 'Строю боты, парсеры и веб-сервисы.'
const LINE2 = 'Пишу, деплою, поддерживаю — без посредников.'

const SPEED       = 18
const LINE2_DELAY = LINE1.length * SPEED + 250
const CTA_DELAY   = LINE2_DELAY + LINE2.length * SPEED + 400

export default function Hero() {
  const [scrollY, setScrollY] = useState(0)
  const [ready,   setReady]   = useState(false)
  const [ctaShow, setCtaShow] = useState(false)

  // Called by ScrambleTitle exactly when last letter locks in
  const handleScrambleDone = () => {
    setReady(true)
    setTimeout(() => setCtaShow(true), CTA_DELAY)
  }

  useEffect(() => {
    const onScroll = () => setScrollY(window.scrollY)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <section id="hero" className="relative flex flex-col min-h-svh bg-void overflow-hidden">

      {/* Availability badge — top right */}
      <div
        className="absolute top-8 right-10 lg:right-20 flex items-center gap-2"
        style={{ opacity: ready ? 1 : 0, transition: 'opacity 0.6s ease' }}
      >
        <span className="relative flex h-2 w-2">
          <span
            className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-60"
            style={{ background: '#4ade80' }}
          />
          <span
            className="relative inline-flex rounded-full h-2 w-2"
            style={{ background: '#22c55e' }}
          />
        </span>
        <span className="font-mono text-muted" style={{ fontSize: '10px', letterSpacing: '0.16em' }}>
          ДОСТУПЕН ДЛЯ ПРОЕКТОВ
        </span>
      </div>

      {/* Main content */}
      <div
        className="px-6 lg:px-20 pt-20 lg:pt-24 flex flex-col gap-6"
        style={{
          transform: `translateY(${scrollY * 0.18}px)`,
          willChange: 'transform',
        }}
      >
        <ScrambleTitle onDone={handleScrambleDone} />

        {/* Role — typewriter after scramble */}
        <p
          className="font-mono text-muted"
          style={{ fontSize: 'clamp(10px, 1vw, 14px)', letterSpacing: '0.22em', minHeight: '1em' }}
        >
          <Typewriter text={ROLE} active={ready} speed={22} delay={0} />
        </p>

        {/* Value prop — two lines, staggered */}
        <p
          className="font-mono text-snow"
          style={{
            fontSize: 'clamp(12px, 1.1vw, 16px)',
            letterSpacing: '0.04em',
            lineHeight: 1.6,
            maxWidth: '480px',
            minHeight: '2.5em',
          }}
        >
          <Typewriter text={LINE1} active={ready} speed={SPEED} delay={0} />
          {ready && (
            <>
              <br />
              <Typewriter text={LINE2} active={ready} speed={SPEED} delay={LINE2_DELAY} />
            </>
          )}
        </p>

        {/* CTA — appears after text is done */}
        <a
          href="https://t.me/rcnn43"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 self-start font-mono font-medium bg-amber text-void px-6 py-3 hover:opacity-90 transition-opacity"
          style={{
            fontSize: 'clamp(11px, 0.9vw, 14px)',
            letterSpacing: '0.1em',
            opacity: ctaShow ? 1 : 0,
            transform: ctaShow ? 'none' : 'translateY(8px)',
            transition: 'opacity 0.6s ease, transform 0.6s ease',
          }}
        >
          → Написать в Telegram
        </a>
      </div>

      {/* Ticker — bottom */}
      <div className="mt-auto">
        <Ticker />
      </div>

    </section>
  )
}
