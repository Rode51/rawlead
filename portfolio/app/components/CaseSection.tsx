'use client'

import { useEffect, useRef, useState, type ReactNode } from 'react'

interface CaseSectionProps {
  number: string
  title: string
  tags: string[]
  body: string
  extra?: ReactNode
}

export default function CaseSection({ number, title, tags, body, extra }: CaseSectionProps) {
  const ref = useRef<HTMLElement>(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const io = new IntersectionObserver(
      ([e]) => { if (e.isIntersecting) setVisible(true) },
      { threshold: 0.1 },
    )
    io.observe(el)
    return () => io.disconnect()
  }, [])

  const reveal = (delay: number) => ({
    opacity: visible ? 1 : 0,
    transform: visible ? 'none' : 'translateY(20px)',
    transition: `opacity 0.75s ${delay}ms cubic-bezier(0.22,1,0.36,1), transform 0.75s ${delay}ms cubic-bezier(0.22,1,0.36,1)`,
  })

  return (
    <section
      ref={ref}
      className="px-10 lg:px-20 pt-20 pb-32 lg:pt-28 lg:pb-44 border-t border-edge min-h-screen flex flex-col justify-between"
    >
      {/* Header */}
      <div>
        <div className="flex items-end justify-between mb-2" style={reveal(0)}>
          <h2
            className="font-display font-black text-snow"
            style={{
              fontSize: 'clamp(72px, 16vw, 260px)',
              lineHeight: 0.88,
              letterSpacing: '-0.03em',
            }}
          >
            {title}
          </h2>
          <span
            className="font-mono text-muted pb-2"
            style={{ fontSize: '11px', letterSpacing: '0.18em', flexShrink: 0, marginLeft: '24px' }}
          >
            {number}
          </span>
        </div>

        {/* Divider */}
        <div className="border-t border-edge mt-8 mb-12" style={reveal(60)} />

        {/* Body */}
        <div className="grid grid-cols-1 lg:grid-cols-[200px_1fr] gap-10 lg:gap-24">
          {/* Tags column */}
          <div className="flex flex-col gap-4 pt-1" style={reveal(120)}>
            {tags.map((tag, i) => (
              <span
                key={i}
                className="font-mono text-muted"
                style={{ fontSize: '11px', letterSpacing: '0.1em', lineHeight: 1.5 }}
              >
                {tag}
              </span>
            ))}
          </div>

          {/* Text + extra column */}
          <div style={reveal(200)}>
            <p
              className="font-mono text-snow leading-relaxed"
              style={{ fontSize: 'clamp(13px, 1.1vw, 15px)', maxWidth: '640px' }}
            >
              {body}
            </p>
            {extra}
          </div>
        </div>
      </div>
    </section>
  )
}
