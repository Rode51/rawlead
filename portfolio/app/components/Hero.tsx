'use client'

import { useEffect, useState } from 'react'
import ScrambleTitle from './ScrambleTitle'
import Ticker from './Ticker'
import Typewriter from './Typewriter'

interface HeroContent {
  role: string
  line1: string
  line2: string
  cta: string
  available: string
}

interface Props {
  content?: HeroContent
  ticker?: string
  locale?: 'ru' | 'en'
}

const DEFAULT: HeroContent = {
  role:      'FULL-STACK РАЗРАБОТЧИК · БОТЫ · ПАРСЕРЫ · АВТОМАТИЗАЦИЯ · САЙТЫ',
  line1:     'Строю боты, парсеры, сайты и автоматизацию.',
  line2:     'Пишу, деплою, поддерживаю — без посредников.',
  cta:       '→ Написать в Telegram',
  available: 'ДОСТУПЕН ДЛЯ ПРОЕКТОВ',
}

const SPEED       = 18
const getLine2Delay = (line1: string) => line1.length * SPEED + 250
const getCtaDelay   = (line1: string, line2: string) =>
  getLine2Delay(line1) + line2.length * SPEED + 400

export default function Hero({ content, ticker, locale = 'ru' }: Props) {
  const c = content ?? DEFAULT

  const LINE2_DELAY = getLine2Delay(c.line1)
  const CTA_DELAY   = getCtaDelay(c.line1, c.line2)

  const [scrollY, setScrollY] = useState(0)
  const [ready,   setReady]   = useState(false)
  const [ctaShow, setCtaShow] = useState(false)

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

      {/* Top-right: availability + lang toggle */}
      <div
        className="absolute top-8 right-10 lg:right-20 flex items-center gap-5"
        style={{ opacity: ready ? 1 : 0, transition: 'opacity 0.6s ease' }}
      >
        {/* Lang toggle */}
        <div className="flex items-center gap-2 font-mono" style={{ fontSize: '10px', letterSpacing: '0.14em' }}>
          <a
            href="/"
            className="transition-colors duration-200"
            style={{ color: locale === 'ru' ? '#e8e8e8' : '#555555' }}
          >
            RU
          </a>
          <span className="text-muted opacity-40">/</span>
          <a
            href="/en"
            className="transition-colors duration-200"
            style={{ color: locale === 'en' ? '#e8e8e8' : '#555555' }}
          >
            EN
          </a>
        </div>

        {/* Availability badge */}
        <div className="flex items-center gap-2">
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
            {c.available}
          </span>
        </div>
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

        {/* Role */}
        <p
          className="font-mono text-muted"
          style={{ fontSize: 'clamp(10px, 1vw, 14px)', letterSpacing: '0.22em', minHeight: '1em' }}
        >
          <Typewriter text={c.role} active={ready} speed={22} delay={0} />
        </p>

        {/* Value prop */}
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
          <Typewriter text={c.line1} active={ready} speed={SPEED} delay={0} />
          {ready && (
            <>
              <br />
              <Typewriter text={c.line2} active={ready} speed={SPEED} delay={LINE2_DELAY} />
            </>
          )}
        </p>

        {/* CTA */}
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
          {c.cta}
        </a>
      </div>

      {/* Ticker */}
      <div className="mt-auto">
        <Ticker text={ticker} />
      </div>

    </section>
  )
}
