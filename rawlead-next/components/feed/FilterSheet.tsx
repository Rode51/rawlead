'use client'

import { useEffect, useState } from 'react'
import type { FeedTier } from '@/lib/auth-context'

const CATEGORIES = [
  { slug: '', label: 'Все' },
  { slug: 'dev', label: 'Разработка' },
  { slug: 'design', label: 'Дизайн' },
  { slug: 'marketing', label: 'Маркетинг' },
  { slug: 'text', label: 'Тексты' },
]

const SOURCES = [
  { slug: 'fl',            label: 'FL.ru',        color: '#00A65A' },
  { slug: 'kwork',         label: 'Kwork',        color: '#EA580C' },
  { slug: 'youdo',         label: 'YouDo',        color: '#2563EB' },
  { slug: 'tg',            label: 'Telegram',     color: '#0088CC' },
  { slug: 'freelance_ru',  label: 'Freelance.ru', color: '#7C3AED' },
  { slug: 'freelancejob',  label: 'FreelanceJob', color: '#059669' },
  { slug: 'pchyol',        label: 'Пчёл.нет',    color: '#D97706' },
]

interface Props {
  category: string
  source: string
  sort: 'time' | 'match'
  feedTier: FeedTier
  onApply: (category: string, source: string, sort: 'time' | 'match') => void
  onClose: () => void
}

export default function FilterSheet({
  category,
  source,
  sort,
  feedTier,
  onApply,
  onClose,
}: Props) {
  const [visible, setVisible] = useState(false)
  const [draftCat, setDraftCat] = useState(category)
  const [draftSrc, setDraftSrc] = useState(source)
  const [draftSort, setDraftSort] = useState(sort)
  const [srcOpen, setSrcOpen] = useState(!!source) // open if already has active source
  const isPremium = feedTier === 'premium'

  useEffect(() => {
    const id = requestAnimationFrame(() => setVisible(true))
    return () => cancelAnimationFrame(id)
  }, [])

  function dismiss() {
    setVisible(false)
    setTimeout(onClose, 300)
  }

  function handleApply() {
    onApply(draftCat, draftSrc, draftSort)
    dismiss()
  }

  function handleReset() {
    onApply('', '', 'time')
    dismiss()
  }

  const hasChanges =
    draftCat !== category || draftSrc !== source || draftSort !== sort
  const hasAnyFilter = draftCat !== '' || draftSrc !== '' || draftSort !== 'time'

  return (
    <div className="fixed inset-0" style={{ zIndex: 500 }} id="rl-feed-sheet" data-testid="feed-filter-sheet">
      {/* Overlay */}
      <div
        className="absolute inset-0"
        style={{
          background: 'rgba(0,0,0,0.45)',
          opacity: visible ? 1 : 0,
          transition: 'opacity 300ms ease',
        }}
        onClick={dismiss}
        aria-hidden="true"
      />

      {/* Panel */}
      <div
        className="rl-feed-sheet__panel absolute left-0 right-0 bottom-0 bg-white flex flex-col"
        style={{
          transform: visible ? 'translateY(0)' : 'translateY(100%)',
          transition: 'transform 300ms cubic-bezier(0.22, 1, 0.36, 1)',
          maxHeight: '90vh',
          borderTop: '3px solid #111010',
        }}
        role="dialog"
        aria-modal="true"
        aria-label="Фильтры"
        data-testid="feed-sheet-panel"
      >
        {/* Handle */}
        <div className="flex justify-center pt-3 pb-1 flex-shrink-0">
          <div style={{ width: 40, height: 4, background: '#DADAD6', borderRadius: 2 }} />
        </div>

        {/* Head */}
        <div
          className="flex items-center justify-between flex-shrink-0"
          style={{ padding: '10px 16px 12px', borderBottom: '1px solid #EAEAE6' }}
        >
          <span className="font-black text-[18px] tracking-tight text-[#111010]">Фильтры</span>
          <button
            onClick={dismiss}
            className="w-9 h-9 flex items-center justify-center text-[#111010] text-[18px] font-bold"
            aria-label="Закрыть фильтры"
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="overflow-y-auto flex-1" style={{ padding: '20px 16px' }}>

          {/* Category */}
          <div className="mb-6">
            <p className="text-[10px] font-black uppercase tracking-widest text-[#9B9B97] mb-3">
              Категория
            </p>
            <div className="grid grid-cols-2 gap-2">
              {CATEGORIES.map(cat => {
                const active = draftCat === cat.slug
                return (
                  <button
                    key={cat.slug}
                    onClick={() => setDraftCat(active ? '' : cat.slug)}
                    data-testid={`sheet-cat-${cat.slug || 'all'}`}
                    className="h-11 text-[13px] font-bold border-2 border-[#111010] transition-all duration-100 active:scale-[0.97]"
                    style={{
                      background: active ? '#111010' : '#fff',
                      color: active ? '#fff' : '#111010',
                      boxShadow: active ? '3px 3px 0 #E8A020' : '2px 2px 0 #D4D4D0',
                    }}
                  >
                    {cat.label}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Source — accordion */}
          <div className="mb-6">
            <button
              type="button"
              onClick={() => setSrcOpen(o => !o)}
              className="w-full flex items-center justify-between mb-0 py-1"
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
                className="text-[12px] text-[#9B9B97] transition-transform duration-200"
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
                transition: 'grid-template-rows 220ms ease',
              }}
            >
              <div style={{ overflow: 'hidden' }}>
                <div className="grid grid-cols-2 gap-2 pt-3">
                  {SOURCES.map(src => {
                    const active = draftSrc === src.slug
                    return (
                      <button
                        key={src.slug}
                        onClick={() => setDraftSrc(active ? '' : src.slug)}
                        className="h-10 text-[12px] font-bold border-2 border-[#111010] flex items-center gap-2 px-3 transition-all duration-100 active:scale-[0.97]"
                        style={{
                          background: active ? '#111010' : '#fff',
                          color: active ? '#fff' : '#111010',
                          boxShadow: active ? '3px 3px 0 #E8A020' : '2px 2px 0 #D4D4D0',
                        }}
                      >
                        <span
                          style={{
                            width: 7,
                            height: 7,
                            borderRadius: '50%',
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

          {/* Sort */}
          <div className="mb-2">
            <p className="text-[10px] font-black uppercase tracking-widest text-[#9B9B97] mb-3">
              Сортировка{!isPremium && <span className="ml-1 text-[12px]">🔒</span>}
            </p>
            <div className="flex gap-2">
              {(['time', 'match'] as const).map(s => {
                const active = draftSort === s
                const locked = !isPremium && s === 'match'
                return (
                  <button
                    key={s}
                    onClick={() => !locked && setDraftSort(s)}
                    disabled={locked}
                    className="flex-1 h-11 text-[12px] font-bold border-2 border-[#111010] transition-all duration-100 disabled:opacity-40 disabled:cursor-not-allowed"
                    style={{
                      background: active ? '#111010' : '#fff',
                      color: active ? '#fff' : '#111010',
                      boxShadow: active ? '3px 3px 0 #E8A020' : '2px 2px 0 #D4D4D0',
                    }}
                  >
                    {s === 'time' ? 'Новые' : 'По совместимости'}
                  </button>
                )
              })}
            </div>
          </div>
        </div>

        {/* Actions */}
        <div
          className="flex-shrink-0 flex gap-2"
          style={{
            padding: '12px 16px calc(env(safe-area-inset-bottom, 0px) + 20px)',
            borderTop: '1px solid #EAEAE6',
          }}
        >
          {hasAnyFilter && (
            <button
              onClick={handleReset}
              className="h-12 px-4 text-[12px] font-bold uppercase tracking-wider border-2 border-[#111010] text-[#111010] bg-white shrink-0"
              style={{ boxShadow: '2px 2px 0 #111010' }}
            >
              Сбросить
            </button>
          )}
          <button
            onClick={handleApply}
            id="rl-feed-sheet-apply"
            data-testid="feed-sheet-apply"
            className="flex-1 h-12 text-[12px] font-bold uppercase tracking-wider border-2 border-[#111010] transition-colors"
            style={{
              background: hasChanges ? '#111010' : '#F5F4F0',
              color: hasChanges ? '#fff' : '#111010',
              boxShadow: hasChanges ? '3px 3px 0 #E8A020' : 'none',
            }}
          >
            {hasChanges ? 'Применить' : 'Готово'}
          </button>
        </div>
      </div>
    </div>
  )
}
