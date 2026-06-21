'use client'

import { useState } from 'react'
import type { FeedTier } from '@/lib/auth-context'
import {
  CATEGORY_OPTIONS,
  formatCategoryPill,
  formatSourcePill,
  toggleCategorySelection,
} from '@/lib/feed-filters'
import FilterSheet from './FilterSheet'
import FilterDropdown from './FilterDropdown'

const ALL_CATEGORY = { slug: '', label: 'Все' }

interface Props {
  categories: string[]
  sources: string[]
  sort: 'time' | 'match'
  feedTier: FeedTier
  onCategoriesChange: (cats: string[]) => void
  onSourcesChange: (srcs: string[]) => void
  onSortChange: (sort: 'time' | 'match') => void
}

export default function FilterBar({
  categories,
  sources,
  sort,
  feedTier,
  onCategoriesChange,
  onSourcesChange,
  onSortChange,
}: Props) {
  const [showSheet, setShowSheet] = useState(false)
  const [showDropdown, setShowDropdown] = useState(false)
  const hasFilter = categories.length > 0 || sources.length > 0 || sort !== 'time'

  const categoryPill = formatCategoryPill(categories)
  const sourcePill = formatSourcePill(sources)
  const pillParts = [
    categoryPill,
    sourcePill,
    sort === 'match' ? 'По совм.' : '',
  ].filter(Boolean)
  const pillText = pillParts.join(' · ')

  function handleSheetApply(cats: string[], srcs: string[], srt: 'time' | 'match') {
    onCategoriesChange(cats)
    onSourcesChange(srcs)
    onSortChange(srt)
  }

  function handleDropdownApply(srcs: string[], srt: 'time' | 'match') {
    onSourcesChange(srcs)
    onSortChange(srt)
  }

  function handleCategoryClick(slug: string) {
    if (!slug) {
      onCategoriesChange([])
      return
    }
    onCategoriesChange(toggleCategorySelection(categories, slug))
  }

  return (
    <>
      <div
        className="sticky z-40 bg-[#F5F4F0] border-b-2 border-[#111010]"
        style={{ top: 'var(--rl-header-h, 56px)', overflow: showDropdown ? 'visible' : undefined }}
      >
        <div className="max-w-feed mx-auto px-4 sm:px-6 h-[52px] flex items-center gap-3">

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

          <div className="hidden sm:flex items-center gap-3 flex-1 min-w-0">
            <div className="flex items-center gap-1.5 overflow-x-auto scrollbar-hide shrink-0">
              {[ALL_CATEGORY, ...CATEGORY_OPTIONS].map(cat => {
                const active = cat.slug
                  ? categories.includes(cat.slug)
                  : categories.length === 0
                return (
                  <button
                    key={cat.slug || 'all'}
                    onClick={() => handleCategoryClick(cat.slug)}
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

            <div className="shrink-0 h-5 w-px bg-[#D4D4D0]" />

            <div className="flex items-center gap-2 shrink-0 ml-auto" style={{ position: 'relative' }}>
              {(sources.length > 0 || sort !== 'time') && (
                <span
                  className="text-[11px] font-semibold px-2 py-1 leading-none whitespace-nowrap"
                  style={{ background: '#EEEDEA', color: '#111010' }}
                >
                  {[
                    sources.length ? formatSourcePill(sources) : '',
                    sort === 'match' ? 'По совм.' : '',
                  ].filter(Boolean).join(' · ')}
                </span>
              )}
              <button
                onClick={() => setShowDropdown(v => !v)}
                data-testid="feed-filter-dropdown"
                id="rl-feed-sort-dd"
                className="inline-flex items-center gap-1 h-8 px-3 text-[12px] font-bold border-2 border-[#111010] shrink-0 transition-all duration-100 whitespace-nowrap"
                style={{
                  background: (sources.length > 0 || sort !== 'time') ? '#111010' : '#fff',
                  color: (sources.length > 0 || sort !== 'time') ? '#fff' : '#111010',
                  boxShadow: (sources.length > 0 || sort !== 'time') ? '2px 2px 0 #E8A020' : '2px 2px 0 #D4D4D0',
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
                  sources={sources}
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
          categories={categories}
          sources={sources}
          sort={sort}
          feedTier={feedTier}
          onApply={handleSheetApply}
          onClose={() => setShowSheet(false)}
        />
      )}
    </>
  )
}
