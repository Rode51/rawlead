'use client'

import { useEffect, useRef, useState } from 'react'

const CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&X'
const TITLE  = 'RODE51'
const LETTERS = TITLE.split('')

// ── Physics constants ──────────────────────────────────────────────
const CURSOR_RADIUS   = 190   // px — influence radius
const CURSOR_STRENGTH = 5.8   // push strength per frame
const SPRING          = 0.038 // spring back to rest
const DAMPING         = 0.88  // velocity retention
const COL_ITERS       = 8     // collision resolution passes per frame
const Y_SCALE         = 0.40  // vertical movement fraction vs horizontal

function randomChar() {
  return CHARS[Math.floor(Math.random() * CHARS.length)]
}

function scramble(target: string, progress: number): string {
  return target
    .split('')
    .map((char, i) =>
      i < Math.floor(progress * target.length) ? char : randomChar()
    )
    .join('')
}

interface Props {
  onDone?: () => void
}

export default function ScrambleTitle({ onDone }: Props) {
  const [displayed,    setDisplayed]    = useState(TITLE)
  const [scrambleDone, setScrambleDone] = useState(false)

  const letterRefs = useRef<(HTMLSpanElement | null)[]>([])
  const mouseRef   = useRef({ x: -9999, y: -9999 })
  const rafRef     = useRef<number>()

  // Physics state — plain object, never triggers re-renders
  const phys = useRef({
    ready: false,
    px:    [] as number[],  // current absolute X
    py:    [] as number[],  // current absolute Y
    ppx:   [] as number[],  // previous X (Verlet)
    ppy:   [] as number[],  // previous Y
    restX: [] as number[],  // natural center X
    restY: [] as number[],  // natural center Y
    halfW: [] as number[],  // collision half-width per letter
  })

  // ── Scramble — 5 s desktop / 2.5 s mobile ──────────────────────
  useEffect(() => {
    const isMobile = window.matchMedia('(pointer: coarse)').matches
    let frame = 0
    const totalFrames = isMobile ? 112 : 300
    let raf: number

    const tick = () => {
      frame++
      const progress = frame / totalFrames  // linear: equal time per letter
      setDisplayed(scramble(TITLE, progress))
      if (frame < totalFrames) {
        raf = requestAnimationFrame(tick)
      } else {
        setDisplayed(TITLE)
        setScrambleDone(true)
        onDone?.()
      }
    }

    const t = setTimeout(() => { raf = requestAnimationFrame(tick) }, 150)
    return () => { clearTimeout(t); cancelAnimationFrame(raf) }
  }, [])

  // ── Physics — starts after scramble ────────────────────────────
  useEffect(() => {
    if (!scrambleDone) return

    // Init: read letter positions & sizes from DOM
    const initPhysics = () => {
      const p = phys.current
      p.px = []; p.py = []; p.ppx = []; p.ppy = []
      p.restX = []; p.restY = []; p.halfW = []

      letterRefs.current.forEach((el) => {
        if (!el) return
        const r  = el.getBoundingClientRect()
        const cx = r.left + r.width  / 2
        const cy = r.top  + r.height / 2
        p.restX.push(cx); p.restY.push(cy)
        p.px.push(cx);    p.py.push(cy)
        p.ppx.push(cx);   p.ppy.push(cy)
        p.halfW.push(r.width / 2)
      })
      p.ready = true
    }

    // Physics frame
    const loop = () => {
      const p  = phys.current
      const mx = mouseRef.current.x
      const my = mouseRef.current.y
      const N  = p.px.length

      if (!p.ready) { rafRef.current = requestAnimationFrame(loop); return }

      // 1 — Verlet + damping
      for (let i = 0; i < N; i++) {
        const vx = (p.px[i] - p.ppx[i]) * DAMPING
        const vy = (p.py[i] - p.ppy[i]) * DAMPING
        p.ppx[i] = p.px[i]
        p.ppy[i] = p.py[i]
        p.px[i] += vx
        p.py[i] += vy
      }

      // 2 — Cursor repulsion (applied as position impulse)
      for (let i = 0; i < N; i++) {
        const dx   = p.px[i] - mx
        const dy   = p.py[i] - my
        const dist = Math.sqrt(dx * dx + dy * dy)
        if (dist > 0.5 && dist < CURSOR_RADIUS) {
          const force = ((CURSOR_RADIUS - dist) / CURSOR_RADIUS) ** 1.4 * CURSOR_STRENGTH
          p.px[i] += (dx / dist) * force
          p.py[i] += (dy / dist) * force * Y_SCALE
        }
      }

      // 3 — Spring back to rest
      for (let i = 0; i < N; i++) {
        p.px[i] += (p.restX[i] - p.px[i]) * SPRING
        p.py[i] += (p.restY[i] - p.py[i]) * SPRING
      }

      // 4 — Collision resolution (adjacent pairs, multiple passes)
      for (let iter = 0; iter < COL_ITERS; iter++) {
        // Left → right
        for (let i = 0; i < N - 1; i++) {
          resolveCollision(p, i, i + 1)
        }
        // Right → left (helps propagate impulses back)
        for (let i = N - 2; i >= 0; i--) {
          resolveCollision(p, i, i + 1)
        }
      }

      // 5 — Apply transforms
      for (let i = 0; i < N; i++) {
        const el = letterRefs.current[i]
        if (el) {
          const ox = (p.px[i] - p.restX[i]).toFixed(2)
          const oy = (p.py[i] - p.restY[i]).toFixed(2)
          el.style.transform = `translate(${ox}px,${oy}px)`
        }
      }

      rafRef.current = requestAnimationFrame(loop)
    }

    const onMove = (e: MouseEvent) => {
      mouseRef.current = { x: e.clientX, y: e.clientY }
    }

    const onTouchStart = (e: TouchEvent) => {
      const t = e.touches[0]
      mouseRef.current = { x: t.clientX, y: t.clientY }
    }

    const onTouchMove = (e: TouchEvent) => {
      const t = e.touches[0]
      mouseRef.current = { x: t.clientX, y: t.clientY }
    }

    const onTouchEnd = () => {
      mouseRef.current = { x: -9999, y: -9999 }
    }

    const onResize = () => {
      phys.current.ready = false
      requestAnimationFrame(initPhysics)
    }

    // Wait one frame for multi-span layout to paint
    const cacheRaf = requestAnimationFrame(initPhysics)
    rafRef.current  = requestAnimationFrame(loop)

    window.addEventListener('mousemove',  onMove,       { passive: true })
    window.addEventListener('touchstart', onTouchStart, { passive: true })
    window.addEventListener('touchmove',  onTouchMove,  { passive: true })
    window.addEventListener('touchend',   onTouchEnd,   { passive: true })
    window.addEventListener('resize',     onResize,     { passive: true })

    return () => {
      cancelAnimationFrame(cacheRaf)
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
      window.removeEventListener('mousemove',  onMove)
      window.removeEventListener('touchstart', onTouchStart)
      window.removeEventListener('touchmove',  onTouchMove)
      window.removeEventListener('touchend',   onTouchEnd)
      window.removeEventListener('resize',     onResize)
    }
  }, [scrambleDone])

  return (
    <h1
      className="font-display font-black leading-[0.82] text-snow"
      style={{ fontSize: 'clamp(60px, 24vw, 520px)', letterSpacing: '-0.02em', userSelect: 'none' }}
      aria-label={TITLE}
    >
      {scrambleDone
        ? LETTERS.map((char, i) => (
            <span
              key={i}
              ref={(el) => { letterRefs.current[i] = el }}
              style={{ display: 'inline-block', willChange: 'transform' }}
            >
              {char}
            </span>
          ))
        : <span style={{ display: 'inline-block' }}>{displayed}</span>
      }
    </h1>
  )
}

// ── Collision helper ────────────────────────────────────────────────
function resolveCollision(
  p: { px: number[]; py: number[]; halfW: number[] },
  i: number,
  j: number,
) {
  const dx      = p.px[i] - p.px[j]
  const dy      = p.py[i] - p.py[j]
  const dist2   = dx * dx + dy * dy
  const minDist = p.halfW[i] + p.halfW[j]

  if (dist2 >= minDist * minDist || dist2 < 0.0001) return

  const dist = Math.sqrt(dist2)
  const corr = (minDist - dist) / dist * 0.5  // split 50/50

  p.px[i] += dx * corr
  p.py[i] += dy * corr * Y_SCALE
  p.px[j] -= dx * corr
  p.py[j] -= dy * corr * Y_SCALE
}
