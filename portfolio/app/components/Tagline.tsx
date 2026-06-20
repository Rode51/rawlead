'use client'

import { useEffect, useRef, useState } from 'react'
import { useParallax } from '../hooks/useParallax'

const DEFAULT = 'Больше делаю, меньше обещаю.'

interface Props { text?: string }

export default function Tagline({ text = DEFAULT }: Props) {
  const sectionRef = useRef<HTMLElement>(null)
  const timer      = useRef<ReturnType<typeof setTimeout>>()
  const [active, setActive] = useState(false)
  const [count,  setCount]  = useState(0)

  const { ref: pRef, offset } = useParallax(0.12)

  const full = text.endsWith('.') ? text : text + '.'

  useEffect(() => {
    const el = sectionRef.current
    if (!el) return
    const io = new IntersectionObserver(
      ([e]) => { if (e.isIntersecting) setActive(true) },
      { threshold: 0.25 },
    )
    io.observe(el)
    return () => io.disconnect()
  }, [])

  useEffect(() => {
    if (!active) return
    clearTimeout(timer.current)
    setCount(0)
    let i = 0
    const tick = () => {
      i++
      setCount(i)
      if (i < full.length) timer.current = setTimeout(tick, 38)
    }
    timer.current = setTimeout(tick, 120)
    return () => clearTimeout(timer.current)
  }, [active])

  const displayed = full.slice(0, count)
  const done      = count >= full.length
  const showDot   = displayed.endsWith('.')
  const bodyPart  = showDot ? displayed.slice(0, -1) : displayed

  return (
    <section
      id="tagline"
      ref={sectionRef}
      className="px-10 lg:px-20 py-20 lg:py-52 border-t border-edge"
    >
      <p
        ref={pRef as React.RefObject<HTMLParagraphElement>}
        className="font-display font-black text-snow"
        style={{
          fontSize: 'clamp(36px, 7.5vw, 120px)',
          lineHeight: 1,
          letterSpacing: '-0.025em',
          minHeight: '1em',
          transform: `translateY(${offset}px)`,
          willChange: 'transform',
        }}
      >
        {bodyPart}
        {showDot && <span className="text-amber">.</span>}
        {active && !done && <span className="tw-cursor" style={{ height: '0.75em' }} />}
      </p>
    </section>
  )
}
