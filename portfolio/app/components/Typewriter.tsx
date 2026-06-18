'use client'

import { useEffect, useRef, useState } from 'react'

interface TypewriterProps {
  text: string
  active: boolean
  speed?: number   // ms per character
  delay?: number   // ms before first character
  className?: string
  style?: React.CSSProperties
}

export default function Typewriter({
  text,
  active,
  speed = 20,
  delay = 0,
  className,
  style,
}: TypewriterProps) {
  const [count, setCount] = useState(0)
  const timer = useRef<ReturnType<typeof setTimeout>>()

  useEffect(() => {
    clearTimeout(timer.current)
    if (!active) return

    setCount(0)
    let i = 0

    const tick = () => {
      i++
      setCount(i)
      if (i < text.length) timer.current = setTimeout(tick, speed)
    }

    timer.current = setTimeout(tick, delay)
    return () => clearTimeout(timer.current)
  }, [active]) // intentionally omitting stable deps

  const done = count >= text.length

  return (
    <span className={className} style={style}>
      {text.slice(0, count)}
      {active && !done && <span className="tw-cursor" />}
    </span>
  )
}
