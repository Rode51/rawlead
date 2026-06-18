'use client'

import { useEffect, useRef } from 'react'

export default function CustomCursor() {
  const dotRef  = useRef<HTMLDivElement>(null)
  const ringRef = useRef<HTMLDivElement>(null)
  const glowRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    let mx = -999, my = -999
    let rx = -999, ry = -999
    let gx = -999, gy = -999
    let raf: number

    const onMove = (e: MouseEvent) => {
      mx = e.clientX
      my = e.clientY
    }

    const loop = () => {
      // Dot — instant
      if (dotRef.current) {
        dotRef.current.style.transform = `translate(${mx - 3}px,${my - 3}px)`
      }
      // Ring — slight lag
      rx += (mx - rx) * 0.14
      ry += (my - ry) * 0.14
      if (ringRef.current) {
        ringRef.current.style.transform = `translate(${rx - 18}px,${ry - 18}px)`
      }
      // Glow — very slow
      gx += (mx - gx) * 0.05
      gy += (my - gy) * 0.05
      if (glowRef.current) {
        glowRef.current.style.transform = `translate(${gx - 350}px,${gy - 350}px)`
      }
      raf = requestAnimationFrame(loop)
    }

    window.addEventListener('mousemove', onMove, { passive: true })
    raf = requestAnimationFrame(loop)
    return () => {
      window.removeEventListener('mousemove', onMove)
      cancelAnimationFrame(raf)
    }
  }, [])

  return (
    <>
      {/* Ambient glow */}
      <div
        ref={glowRef}
        aria-hidden
        style={{
          position: 'fixed', top: 0, left: 0, zIndex: 9,
          width: 700, height: 700, borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(245,166,35,0.11) 0%, rgba(245,166,35,0.03) 45%, transparent 70%)',
          pointerEvents: 'none',
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
          transition: 'width 0.2s, height 0.2s, border-color 0.2s',
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
        }}
      />
    </>
  )
}
