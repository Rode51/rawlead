'use client'

import { useState } from 'react'
import type { FeedTier } from '@/lib/auth-context'
import FilterSheet from './FilterSheet'
import FilterDropdown from './FilterDropdown'

const CATEGORIES = [
  { slug: '', label: 'Все' },
  { slug: 'dev', label: 'Разработка' },
  { slug: 'design', label: 'Дизайн' },
  { slug: 'marketing', label: 'Маркетинг' },
  { slug: 'text', label: 'Тексты' },
]

const CATEGORY_LABEL: Record<string, string> = {
  dev: 'Разработка', design: 'Дизайн', marketing: 'Маркетинг', text: 'Тексты',
}

const SOURCE_LABEL: Record<string, string> = {
  fl: 'FL.ru', kwork: 'Kwork', youdo: 'YouDo', tg: 'Telegram',
  freelance_ru: 'Freelance.ru', freelancejob: 'FreelanceJob', pchyol: 'Пчёл.нет',
}

interface Props {
  category: string
  source: string
  sort: 'time' | 'match'
  feedTier: FeedTier
  onCategoryChange: (cat: string) => void
  onSourceChange: (src: string) => void
  onSortChange: (sort: 'time' | 'match') => void
}

export default function FilterBar({
  category,
  source,
  sort,
  feedTier,
  onCategoryChange,
  onSourceChange,
  onSortChange,
}: Props) {
  const [showSheet, setShowSheet] = useState(false)    // mobile
  const [showDropdown, setShowDropdown] = useState(false) // desktop
  const isPremium = feedTier === 'premium'
  const hasFilter = category !== '' || source !== '' || sort !== 'time'

  // Build pill text for mobile
  const pillParts = [
    category ? CATEGORY_LABEL[category] : '',
    source ? SOURCE_LABEL[source] : '',
    sort === 'match' ? 'По совм.' : '',
  ].filter(Boolean)
  const pillText = pillParts.length ? pillParts.join(' · ') : ''

  function handleSheetApply(cat: string, src: string, srt: 'time' | 'match') {
    onCategoryChange(cat)
    onSourceChange(src)
    onSortChange(srt)
  }

  function handleDropdownApply(src: string, srt: 'time' | 'match') {
    onSourceChange(src)
    onSortChange(srt)
  }

  return (
    <>
      <div
        className="sticky z-40 bg-[#F5F4F0] border-b-2 border-[#111010]"
        style={{ top: 'var(--rl-header-h, 56px)', overflow: showDropdown ? 'visible' : undefined }}
      >
        <div className="max-w-feed mx-auto px-4 sm:px-6 h-[52px] flex items-center gap-3">

          {/* ── MOBILE: trigger + active pill ── */}
          <div className="flex sm:hidden items-center gap-2 flex-1 min-w-0">
            <button
              onClick={() => setShowSheet(true)}
              data-testid="feed-filters-open"
              id="rl-feed-filters-open"
              className="inline-flex items-center gap-1.5 h-8 px-3 text-[12px] font-bold border-2 border-[#111010] shrink-0 transition-all duration-100"
              style={{
                background: hasFilter ? '#111010' : '#fff',
                color: hasFilter ? '#fff' : '#111010',
                boxShadow: hasFilter ? '2px 2px 0 #E8A020' : '2px 2px 0 #D4D4D0',
              }}
              aria-label="Открыть фильтры"
            >
              <span aria-hidden="true" className="text-[14px]">☰</span>
              <span>Фильтр</span>
            </button>

            {pillText && (
              <span
                className="text-[11px] font-semibold px-2 py-1 leading-none truncate"
                style={{ background: '#EEEDEA', color: '#111010' }}
              >
                {pillText}
              </span>
            )}
          </div>

          {/* ── DESKTOP: category chips + фильтр button ── */}
          <div className="hidden sm:flex items-center gap-3 flex-1 min-w-0">
            {/* Category chips */}
            <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-hide shrink-0">
              {CATEGORIES.map(cat => {
                const active = category === cat.slug
                return (
                  <button
                    key={cat.slug}
                    onClick={() => onCategoryChange(cat.slug)}
                    data-testid={`feed-cat-${cat.slug || 'all'}`}
                    className="shrink-0 h-8 px-3 text-[12px] font-bold border-2 border-[#111010] transition-all duration-100 whitespace-nowrap"
                    style={{
                      background: active ? '#111010' : '#fff',
                      color: active ? '#fff' : '#111010',
                    }}
                  >
                    {cat.label}
                  </button>
                )
              })}
            </div>

            {/* Divider */}
            <div className="shrink-0 h-5 w-px bg-[#D4D4D0]" />

            {/* Фильтр ▾ — opens dropdown */}
            <div className="flex items-center gap-2 shrink-0 ml-auto" style={{ position: 'relative' }}>
              {(source || sort !== 'time') && (
                <span
                  className="text-[11px] font-semibold px-2 py-1 leading-none whitespace-nowrap"
                  style={{ background: '#EEEDEA', color: '#111010' }}
                >
                  {[source ? SOURCE_LABEL[source] : '', sort === 'match' ? 'По совм.' : ''].filter(Boolean).join(' · ')}
                </span>
              )}
              <button
                onClick={() => setShowDropdown(v => !v)}
                data-testid="feed-filter-dropdown"
                id="rl-feed-sort-dd"
                className="inline-flex items-center gap-1 h-8 px-3 text-[12px] font-bold border-2 border-[#111010] shrink-0 transition-all duration-100 whitespace-nowrap"
                style={{
                  background: (source !== '' || sort !== 'time') ? '#111010' : '#fff',
                  color: (source !== '' || sort !== 'time') ? '#fff' : '#111010',
                  boxShadow: (source !== '' || sort !== 'time') ? '2px 2px 0 #E8A020' : '2px 2px 0 #D4D4D0',
                }}
              >
                Фильтр
                <span
                  aria-hidden="true"
                  className="text-[10px] transition-transform duration-150"
                  style={{ transform: showDropdown ? 'rotate(180deg)' : 'rotate(0deg)' }}
                >▾</span>
              </button>

              {showDropdown && (
                <FilterDropdown
                  source={source}
                  sort={sort}
                  feedTier={feedTier}
                  onApply={handleDropdownApply}
                  onClose={() => setShowDropdown(false)}
                />
              )}
            </div>
          </div>

        </div>
      </div>

      {showSheet && (
        <FilterSheet
          category={category}
          source={source}
          sort={sort}
          feedTier={feedTier}
          onApply={handleSheetApply}
          onClose={() => setShowSheet(false)}
        />
      )}
    </>
  )
}
