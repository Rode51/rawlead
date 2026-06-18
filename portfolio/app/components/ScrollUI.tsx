'use client'

import { useEffect, useRef, useState } from 'react'

const SECTIONS = [
  { id: 'hero',     label: 'INTRO' },
  { id: 'tagline',  label: 'ПРИНЦИП' },
  { id: 'services', label: 'УСЛУГИ' },
  { id: 'projects', label: 'ПРОЕКТЫ' },
  { id: 'process',  label: 'ПРОЦЕСС' },
  { id: 'footer',   label: 'КОНТАКТ' },
]

export default function ScrollUI() {
  const [progress, setProgress] = useState(0)
  const [active, setActive] = useState(0)
  const rafRef = useRef<number>()

  useEffect(() => {
    const update = () => {
      const scrolled = window.scrollY
      const total = document.body.scrollHeight - window.innerHeight
      setProgress(total > 0 ? scrolled / total : 0)

      // Active section detection
      const mid = window.innerHeight * 0.5
      const els = SECTIONS.map(s => document.getElementById(s.id))
      let current = 0
      els.forEach((el, i) => {
        if (!el) return
        const rect = el.getBoundingClientRect()
        if (rect.top <= mid) current = i
      })
      setActive(current)
    }

    const onScroll = () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
      rafRef.current = requestAnimationFrame(update)
    }

    window.addEventListener('scroll', onScroll, { passive: true })
    update()
    return () => {
      window.removeEventListener('scroll', onScroll)
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
    }
  }, [])

  const scrollTo = (id: string) => {
    const el = document.getElementById(id)
    if (el) el.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <>
      {/* Progress bar — top */}
      <div
        className="fixed top-0 left-0 z-50 h-[2px]"
        style={{
          width: `${progress * 100}%`,
          background: 'linear-gradient(90deg, #F5A623 0%, rgba(245,166,35,0.6) 100%)',
          transition: 'width 0.05s linear',
          transformOrigin: 'left',
        }}
      />

      {/* Section dots — fixed right */}
      <nav
        className="hidden lg:flex fixed right-8 top-1/2 z-50 flex-col gap-5 -translate-y-1/2"
      >
        {SECTIONS.map((s, i) => (
          <button
            key={s.id}
            onClick={() => scrollTo(s.id)}
            className="group flex items-center gap-3 justify-end"
            aria-label={s.label}
          >
            {/* Label — appears on hover */}
            <span
              className="font-mono text-muted transition-all duration-200"
              style={{
                fontSize: '9px',
                letterSpacing: '0.16em',
                opacity: active === i ? 0.7 : 0,
                transform: active === i ? 'translateX(0)' : 'translateX(6px)',
              }}
            >
              {s.label}
            </span>

            {/* Dot */}
            <span
              className="block rounded-full transition-all duration-300"
              style={{
                width:  active === i ? '6px' : '3px',
                height: active === i ? '6px' : '3px',
                background: active === i ? '#F5A623' : '#444',
                boxShadow: active === i ? '0 0 8px rgba(245,166,35,0.6)' : 'none',
              }}
            />
          </button>
        ))}
      </nav>
    </>
  )
}
