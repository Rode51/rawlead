'use client'

import { useEffect, useRef, useState } from 'react'

const LINES = [
  { text: '[radar] FL.ru   → 14 leads   ok',  color: '#555' },
  { text: '[radar] Kwork   →  9 leads   ok',  color: '#555' },
  { text: '[radar] TG      →  5 leads   ok',  color: '#555' },
  { text: '[L1]    score 87 · web · python  → /lenta/', color: '#F5A623' },
  { text: '[L1]    score 39 · hidden (spam filter)',     color: '#444' },
  { text: '[L1]    score 72 · design · ui   → /lenta/', color: '#F5A623' },
  { text: '[TG]    4 subscribers matched    → notify',  color: '#e8e8e8' },
]

const INTERVAL = 420  // ms between lines
const PAUSE    = 2400 // ms pause before loop

export default function TerminalLog() {
  const ref     = useRef<HTMLDivElement>(null)
  const started = useRef(false)
  const [lines, setLines] = useState<typeof LINES>([])

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const io = new IntersectionObserver(
      ([e]) => { if (e.isIntersecting && !started.current) { started.current = true; run() } },
      { threshold: 0.4 },
    )
    io.observe(el)
    return () => io.disconnect()
  }, [])

  function run() {
    setLines([])
    LINES.forEach((line, i) => {
      setTimeout(() => setLines(prev => [...prev, line]), i * INTERVAL)
    })
    // Loop
    setTimeout(run, LINES.length * INTERVAL + PAUSE)
  }

  return (
    <div
      ref={ref}
      className="mt-10 border border-edge font-mono"
      style={{ background: '#080808', padding: '16px 20px', maxWidth: '500px' }}
    >
      <div
        style={{ color: '#333', fontSize: '10px', letterSpacing: '0.12em', marginBottom: '10px' }}
      >
        — RADAR CYCLE ————————————————
      </div>
      <div style={{ minHeight: `${LINES.length * 22}px` }}>
        {lines.map((l, i) => (
          <div key={i} style={{ color: l.color, fontSize: '12px', lineHeight: '22px' }}>
            {l.text}
          </div>
        ))}
        {lines.length < LINES.length && (
          <span style={{ color: '#333', fontSize: '12px' }}>▋</span>
        )}
      </div>
    </div>
  )
}
