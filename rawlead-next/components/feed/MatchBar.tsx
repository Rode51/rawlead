'use client'

import type { LeadItem } from '@/lib/types'
import type { FeedTier } from '@/lib/auth-context'

interface Props {
  item: LeadItem
  feedTier: FeedTier
  hasUserSkills: boolean
  onQuizClick: () => void
  onLoginClick: () => void
}

const LOCK_SVG = (
  <svg width="11" height="11" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" style={{ flexShrink: 0 }}>
    <path d="M18 8h-1V6a5 5 0 00-10 0v2H6a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V10a2 2 0 00-2-2zm-7 8a2 2 0 112 0 2 2 0 01-2 0zm3.1-8H9.9V6a3.1 3.1 0 016.2 0v2z"/>
  </svg>
)

const MATCH_TOOLTIP = 'Качество × 60% + Навыки × 40%'
const QUALITY_TOOLTIP = 'Оценка ИИ по полноте ТЗ и ясности задачи'

function Bar({ pct, color }: { pct: number; color: string }) {
  return (
    <div
      style={{ height: 5, background: '#E8E8E4', position: 'relative', borderRadius: 0 }}
      title={pct >= 60 ? 'Хорошее совпадение с вашим профилем' : pct >= 25 ? 'Среднее совпадение' : 'Низкое совпадение'}
    >
      <div
        style={{
          position: 'absolute',
          inset: '0 auto 0 0',
          width: `${pct}%`,
          background: color,
          transition: 'width 700ms ease-out',
        }}
      />
    </div>
  )
}

export default function MatchBar({ item, feedTier, hasUserSkills, onQuizClick, onLoginClick }: Props) {
  const km = item.keyword_match
  const hasLeadTags = !!(item.lead_tags?.length)

  if (feedTier === 'pending') return null

  if (feedTier === 'anon') {
    return (
      <div className="flex flex-col gap-1.5">
        <div className="flex items-center justify-between gap-2">
          <span className="text-[10px] font-bold uppercase tracking-widest text-[#9B9B97]" title="Процент совпадения заказа с вашим профилем">
            Совместимость
          </span>
          <button
            onClick={onLoginClick}
            className="flex items-center gap-1 text-[11px] font-bold text-[#6B6B6B] hover:text-[#111010] transition-colors"
            title="Войдите через Telegram — увидите % совпадения"
          >
            {LOCK_SVG}
            <span>Войди и увидишь</span>
          </button>
        </div>
        <Bar pct={0} color="#D4D4D0" />
      </div>
    )
  }

  if (feedTier === 'free' || feedTier === 'expired_trial') {
    return (
      <div className="flex flex-col gap-1.5">
        <div className="flex items-center justify-between gap-2">
          <span
            className="text-[10px] font-bold uppercase tracking-widest text-[#9B9B97]"
            title="Точный % совместимости — в Premium"
          >
            Совместимость
          </span>
        </div>
        <div
          style={{ height: 5, background: '#E8E8E4', position: 'relative' }}
          role="progressbar"
          aria-valuenow={0}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label="Совместимость — Premium"
        >
          <div
            style={{
              position: 'absolute',
              inset: '0 auto 0 0',
              width: 0,
              background: '#D4D4D0',
            }}
          />
          <span
            className="absolute right-0 top-1/2 -translate-y-1/2 text-[#9B9B97]"
            aria-hidden="true"
          >
            {LOCK_SVG}
          </span>
        </div>
      </div>
    )
  }

  if (!hasUserSkills) {
    return (
      <div className="flex flex-col gap-1.5">
        <div className="flex items-center justify-between gap-2">
          <span className="text-[10px] font-bold uppercase tracking-widest text-[#9B9B97]">
            Совместимость
          </span>
          <button
            onClick={onQuizClick}
            className="text-[11px] font-bold text-[#111010] hover:underline transition-colors"
            title="Пройдите квиз — ИИ узнает ваш стек и покажет % совпадения"
          >
            Пройти квиз →
          </button>
        </div>
        <Bar pct={28} color="#D4D4D0" />
      </div>
    )
  }

  const isNeutral = km == null || !hasLeadTags
  const pct = isNeutral ? Math.round(item.ai_score || 0) : km!
  const label = isNeutral ? 'Качество' : 'Совместимость'
  const labelTip = isNeutral ? QUALITY_TOOLTIP : MATCH_TOOLTIP

  const barColor = pct >= 90 ? '#16A34A' : pct >= 60 ? '#111010' : '#D97706'

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between gap-2">
        <span
          className="text-[10px] font-bold uppercase tracking-widest text-[#9B9B97]"
          title={labelTip}
        >
          {label}
        </span>
      </div>
      <Bar pct={pct} color={barColor} />
    </div>
  )
}
