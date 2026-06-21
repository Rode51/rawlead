export const CATEGORY_OPTIONS = [
  { slug: 'dev', label: 'Разработка' },
  { slug: 'design', label: 'Дизайн' },
  { slug: 'marketing', label: 'Маркетинг' },
  { slug: 'text', label: 'Тексты' },
] as const

export const CATEGORY_LABEL: Record<string, string> = Object.fromEntries(
  CATEGORY_OPTIONS.map(c => [c.slug, c.label]),
)

export const SOURCE_OPTIONS = [
  { slug: 'fl', label: 'FL.ru', color: '#00A65A' },
  { slug: 'kwork', label: 'Kwork', color: '#EA580C' },
  { slug: 'youdo', label: 'YouDo', color: '#2563EB' },
  { slug: 'tg', label: 'Telegram', color: '#0088CC' },
  { slug: 'freelance_ru', label: 'Freelance.ru', color: '#7C3AED' },
  { slug: 'freelancejob', label: 'FreelanceJob', color: '#059669' },
  { slug: 'pchyol', label: 'Пчёл.нет', color: '#D97706' },
] as const

export const SOURCE_LABEL: Record<string, string> = Object.fromEntries(
  SOURCE_OPTIONS.map(s => [s.slug, s.label]),
)

export function toggleCategorySelection(current: string[], slug: string): string[] {
  if (!slug) return []
  const set = new Set(current)
  if (set.has(slug)) {
    set.delete(slug)
  } else {
    set.add(slug)
  }
  return Array.from(set)
}

export function toggleSourceSelection(current: string[], slug: string): string[] {
  const set = new Set(current)
  if (set.has(slug)) {
    set.delete(slug)
  } else {
    set.add(slug)
  }
  return Array.from(set)
}

export function formatCategoryPill(categories: string[]): string {
  if (!categories.length) return ''
  if (categories.length <= 2) {
    return categories.map(slug => CATEGORY_LABEL[slug] || slug).join(' · ')
  }
  return `${categories.length} категории`
}

export function formatSourcePill(sources: string[]): string {
  if (!sources.length) return ''
  if (sources.length <= 2) {
    return sources.map(slug => SOURCE_LABEL[slug] || slug).join(' · ')
  }
  return `${sources.length} биржи`
}
