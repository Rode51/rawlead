'use client'

import { useEffect } from 'react'

export default function CursorGlow() {
  useEffect(() => {
    const move = (e: MouseEvent) => {
      document.documentElement.style.setProperty('--mx', `${e.clientX}px`)
      document.documentElement.style.setProperty('--my', `${e.clientY}px`)
    }
    window.addEventListener('mousemove', move, { passive: true })
    return () => window.removeEventListener('mousemove', move)
  }, [])

  return (
    <div
      aria-hidden
      style={{
        position: 'fixed',
        left: 'var(--mx, -9999px)',
        top: 'var(--my, -9999px)',
        transform: 'translate(-50%, -50%)',
        width: '700px',
        height: '700px',
        borderRadius: '50%',
        background:
          'radial-gradient(circle, rgba(245,166,35,0.13) 0%, rgba(245,166,35,0.04) 40%, transparent 70%)',
        pointerEvents: 'none',
        zIndex: 5,
      }}
    />
  )
}
