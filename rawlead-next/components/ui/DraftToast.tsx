'use client'

import { useEffect, useRef, useState } from 'react'
import { DRAFT_TOAST_EVENT } from '@/lib/draft-toast'

export default function DraftToast() {
  const [message, setMessage] = useState<string | null>(null)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    function onToast(e: Event) {
      const detail = (e as CustomEvent<string>).detail
      if (!detail) return
      if (timerRef.current) clearTimeout(timerRef.current)
      setMessage(detail)
      timerRef.current = setTimeout(() => setMessage(null), 4200)
    }
    window.addEventListener(DRAFT_TOAST_EVENT, onToast)
    return () => {
      window.removeEventListener(DRAFT_TOAST_EVENT, onToast)
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [])

  if (!message) return null

  return (
    <div
      role="status"
      className="fixed bottom-20 left-1/2 z-[60] -translate-x-1/2 max-w-[min(92vw,420px)] px-4 py-3 text-[13px] font-semibold text-[#111010] border-2 border-[#111010]"
      style={{ background: '#FACC15', boxShadow: '4px 4px 0 #111010' }}
    >
      {message}
    </div>
  )
}
