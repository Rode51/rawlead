'use client'

import { useEffect, useRef } from 'react'

export default function CustomCursor() {
  const dotRef  = useRef<HTMLDivElement>(null)
  const ringRef = useRef<HTMLDivElement>(null)
  const glowRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const dot  = dotRef.current
    const ring = ringRef.current
    const glow = glowRef.current
    if (!dot || !ring) return

    let mx = -999, my = -999
    let rx = -999, ry = -999
    let gx = -999, gy = -999
    let mode: 'mouse' | 'touch' | 'idle' = 'idle'
    let lastTouch = 0   // timestamp of last touchstart — used to skip synthetic mousemove
    let raf: number

    // ── Mouse ────────────────────────────────────────────────────
    const onMouseMove = (e: MouseEvent) => {
      // Mobile browsers fire a synthetic mousemove ~300ms after touch — ignore it
      if (Date.now() - lastTouch < 600) return
      mode = 'mouse'
      mx = e.clientX; my = e.clientY
      dot.style.opacity  = '1'
      ring.style.opacity = '1'
      if (glow) glow.style.opacity = '1'
    }

    // ── Touch ────────────────────────────────────────────────────
    const onTouchStart = (e: TouchEvent) => {
      lastTouch = Date.now()
      mode = 'touch'
      mx = e.touches[0].clientX
      my = e.touches[0].clientY
      dot.style.opacity  = '1'
      ring.style.opacity = '1'
      if (glow) glow.style.opacity = '1'
    }

    const onTouchMove = (e: TouchEvent) => {
      mx = e.touches[0].clientX
      my = e.touches[0].clientY
    }

    const onTouchEnd = () => {
      mode = 'idle'
      dot.style.opacity  = '0'
      ring.style.opacity = '0'
      if (glow) glow.style.opacity = '0'
    }

    // ── RAF loop — always runs ───────────────────────────────────
    const loop = () => {
      if (mode === 'touch') {
        // Instant follow — no lag on touch
        dot.style.transform  = `translate(${mx - 3}px,${my - 3}px)`
        ring.style.transform = `translate(${mx - 18}px,${my - 18}px)`
        if (glow) {
          gx += (mx - gx) * 0.08; gy += (my - gy) * 0.08
          glow.style.transform = `translate(${gx - 350}px,${gy - 350}px)`
        }
      } else if (mode === 'mouse') {
        dot.style.transform = `translate(${mx - 3}px,${my - 3}px)`
        rx += (mx - rx) * 0.14; ry += (my - ry) * 0.14
        ring.style.transform = `translate(${rx - 18}px,${ry - 18}px)`
        if (glow) {
          gx += (mx - gx) * 0.05; gy += (my - gy) * 0.05
          glow.style.transform = `translate(${gx - 350}px,${gy - 350}px)`
        }
      }
      raf = requestAnimationFrame(loop)
    }

    window.addEventListener('mousemove',  onMouseMove,  { passive: true })
    window.addEventListener('touchstart', onTouchStart, { passive: true })
    window.addEventListener('touchmove',  onTouchMove,  { passive: true })
    window.addEventListener('touchend',   onTouchEnd,   { passive: true })
    raf = requestAnimationFrame(loop)

    return () => {
      window.removeEventListener('mousemove',  onMouseMove)
      window.removeEventListener('touchstart', onTouchStart)
      window.removeEventListener('touchmove',  onTouchMove)
      window.removeEventListener('touchend',   onTouchEnd)
      cancelAnimationFrame(raf)
    }
  }, [])

  return (
    <>
      {/* Glow — follows mouse, stays off-screen on touch */}
      <div
        ref={glowRef}
        aria-hidden
        style={{
          position: 'fixed', top: 0, left: 0, zIndex: 9,
          width: 700, height: 700, borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(245,166,35,0.11) 0%, rgba(245,166,35,0.03) 45%, transparent 70%)',
          pointerEvents: 'none',
          opacity: 0,
          transform: 'translate(-9999px,-9999px)',
          transition: 'opacity 0.3s ease',
        }}
      />
      {/* Ring */}
      <div
        ref={ringRef}
        aria-hidden
        style={{
          position: 'fixed', top: 0, left: 0, zIndex: 9999,
          width: 36, height: 36,
          border: '1px solid rgba(245,166,35,0.55)',
          borderRadius: '50%',
          pointerEvents: 'none',
          opacity: 0,
          transform: 'translate(-9999px,-9999px)',
          transition: 'opacity 0.18s ease',
        }}
      />
      {/* Dot */}
      <div
        ref={dotRef}
        aria-hidden
        style={{
          position: 'fixed', top: 0, left: 0, zIndex: 10000,
          width: 6, height: 6,
          background: '#F5A623',
          borderRadius: '50%',
          pointerEvents: 'none',
          opacity: 0,
          transform: 'translate(-9999px,-9999px)',
          transition: 'opacity 0.18s ease',
        }}
      />
    </>
  )
}
