'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { feedApi } from '@/lib/api'

export default function AnnouncementBar() {
  const [stat, setStat] = useState<string | null>(null)

  useEffect(() => {
    feedApi.siteStats().then(s => {
      if (s.leads_week_display) setStat(s.leads_week_display)
    }).catch(() => {})
  }, [])

  const ITEMS = [
    { text: stat ? `Радар онлайн · ${stat} лидов за неделю` : 'Радар онлайн', cta: true },
    { text: 'Агрегатор фриланс-бирж RawLead', cta: false },
    { text: 'Поиск заказов для Python · FastAPI · WordPress · Design', cta: false },
  ]

  // duplicate for seamless loop
  const track = [...ITEMS, ...ITEMS]

  return (
    <div className="bg-rl-inverse overflow-hidden border-b-2 border-rl-inverse select-none h-8 flex items-center">
      <div
        className="marquee-run"
        style={{ '--marquee-dur': '34s' } as React.CSSProperties}
      >
        {track.map((item, i) => (
          <span
            key={i}
            className="inline-flex items-center gap-4 px-8 text-[11px] font-display font-black uppercase tracking-[0.14em] text-rl-amber whitespace-nowrap"
          >
            <span className="opacity-40">·</span>
            <span>{item.text}</span>
            {item.cta && (
              <Link
                href="/lenta/"
                className="underline underline-offset-2 hover:text-white transition-colors"
              >
                Смотреть ленту →
              </Link>
            )}
          </span>
        ))}
      </div>
    </div>
  )
}
