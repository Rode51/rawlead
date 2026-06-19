'use client'

import { useEffect, useRef, useState } from 'react'
import type { FeedTier } from '@/lib/auth-context'

const SOURCES = [
  { slug: 'fl',           label: 'FL.ru',        color: '#00A65A' },
  { slug: 'kwork',        label: 'Kwork',        color: '#EA580C' },
  { slug: 'youdo',        label: 'YouDo',        color: '#2563EB' },
  { slug: 'tg',           label: 'Telegram',     color: '#0088CC' },
  { slug: 'freelance_ru', label: 'Freelance.ru', color: '#7C3AED' },
  { slug: 'freelancejob', label: 'FreelanceJob', color: '#059669' },
  { slug: 'pchyol',       label: 'Пчёл.нет',    color: '#D97706' },
]

interface Props {
  source: string
  sort: 'time' | 'match'
  feedTier: FeedTier
  onApply: (source: string, sort: 'time' | 'match') => void
  onClose: () => void
}

export default function FilterDropdown({ source, sort, feedTier, onApply, onClose }: Props) {
  const [draftSrc, setDraftSrc] = useState(source)
  const [draftSort, setDraftSort] = useState(sort)
  const [srcOpen, setSrcOpen] = useState(!!source)
  const [visible, setVisible] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const isPremium = feedTier === 'premium'

  // Animate in
  useEffect(() => {
    const id = requestAnimationFrame(() => setVisible(true))
    return () => cancelAnimationFrame(id)
  }, [])

  // Close on outside click or Escape
  useEffect(() => {
    function onDown(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose()
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('mousedown', onDown)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onDown)
      document.removeEventListener('keydown', onKey)
    }
  }, [onClose])

  function handleApply() {
    onApply(draftSrc, draftSort)
    onClose()
  }

  function handleReset() {
    onApply('', 'time')
    onClose()
  }

  const hasChanges = draftSrc !== source || draftSort !== sort
  const hasAny = draftSrc !== '' || draftSort !== 'time'

  return (
    <div
      ref={ref}
      id="rl-feed-sort-panel"
      data-testid="feed-sort-panel"
      style={{
        position: 'absolute',
        top: 'calc(100% + 8px)',
        right: 0,
        width: 260,
        background: '#fff',
        border: '2px solid #111010',
        boxShadow: '4px 4px 0 #111010',
        zIndex: 200,
        opacity: visible ? 1 : 0,
        transform: visible ? 'translateY(0)' : 'translateY(-6px)',
        transition: 'opacity 160ms ease, transform 160ms ease',
      }}
    >
      <div style={{ padding: '14px 14px 0' }}>

        {/* Sort */}
        <p className="text-[10px] font-black uppercase tracking-widest text-[#9B9B97] mb-2">
          Сортировка{!isPremium && <span className="ml-1">🔒</span>}
        </p>
        <div className="flex gap-1.5 mb-4">
          {(['time', 'match'] as const).map(s => {
            const active = draftSort === s
            const locked = !isPremium && s === 'match'
            return (
              <button
                key={s}
                onClick={() => !locked && setDraftSort(s)}
                disabled={locked}
                className="flex-1 h-8 text-[11px] font-bold border-2 border-[#111010] transition-all duration-100 disabled:opacity-40 disabled:cursor-not-allowed"
                style={{
                  background: active ? '#111010' : '#fff',
                  color: active ? '#fff' : '#111010',
                }}
              >
                {s === 'time' ? 'Новые' : 'По совм.'}
              </button>
            )
          })}
        </div>

        {/* Source — accordion */}
        <button
          type="button"
          onClick={() => setSrcOpen(o => !o)}
          className="w-full flex items-center justify-between py-1 mb-0"
        >
          <span className="text-[10px] font-black uppercase tracking-widest text-[#9B9B97] flex items-center gap-2">
            Биржа
            {draftSrc && (
              <span
                className="text-[9px] font-black px-1.5 py-0.5 leading-none"
                style={{ background: '#111010', color: '#fff' }}
              >
                {SOURCES.find(s => s.slug === draftSrc)?.label}
              </span>
            )}
          </span>
          <span
            className="text-[11px] text-[#9B9B97] transition-transform duration-200"
            style={{ transform: srcOpen ? 'rotate(180deg)' : 'rotate(0deg)' }}
            aria-hidden="true"
          >
            ▾
          </span>
        </button>

        <div
          style={{
            display: 'grid',
            gridTemplateRows: srcOpen ? '1fr' : '0fr',
            transition: 'grid-template-rows 200ms ease',
          }}
        >
          <div style={{ overflow: 'hidden' }}>
            <div className="flex flex-col gap-1 pt-2 pb-1">
              {SOURCES.map(src => {
                const active = draftSrc === src.slug
                return (
                  <button
                    key={src.slug}
                    onClick={() => setDraftSrc(active ? '' : src.slug)}
                    className="w-full h-8 text-[12px] font-bold border-2 border-[#111010] flex items-center gap-2 px-3 transition-all duration-100 text-left"
                    style={{
                      background: active ? '#111010' : '#fff',
                      color: active ? '#fff' : '#111010',
                    }}
                  >
                    <span
                      style={{
                        width: 7, height: 7, borderRadius: '50%',
                        background: active ? '#fff' : src.color,
                        flexShrink: 0,
                      }}
                    />
                    {src.label}
                  </button>
                )
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div
        className="flex gap-2"
        style={{ padding: '10px 14px 14px', borderTop: '1px solid #EAEAE6', marginTop: 10 }}
      >
        {hasAny && (
          <button
            onClick={handleReset}
            className="h-8 px-3 text-[11px] font-bold border-2 border-[#111010] text-[#111010] bg-white shrink-0 hover:bg-[#F5F4F0] transition-colors"
          >
            Сбросить
          </button>
        )}
        <button
          onClick={handleApply}
          className="flex-1 h-8 text-[11px] font-bold border-2 border-[#111010] transition-colors"
          style={{
            background: hasChanges ? '#111010' : '#F5F4F0',
            color: hasChanges ? '#fff' : '#111010',
          }}
        >
          {hasChanges ? 'Применить' : 'Готово'}
        </button>
      </div>
    </div>
  )
}
