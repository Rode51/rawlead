import type { QuizCard, QuizNextResponse } from './types'

/** API returns card_id + lead_tags; UI expects id + tags (WP parity). */
export function normalizeQuizCard(raw: Record<string, unknown> | QuizCard | null | undefined): QuizCard | null {
  if (!raw || typeof raw !== 'object') return null
  const row = raw as Record<string, unknown>
  const id = String(row.card_id ?? row.id ?? '').trim()
  if (!id) return null
  const tagsRaw = row.tags ?? row.lead_tags
  const tags = Array.isArray(tagsRaw) ? tagsRaw.map(t => String(t)) : []
  return {
    id,
    title: String(row.title ?? ''),
    body: String(row.body ?? row.task_summary ?? ''),
    tags,
    source: String(row.source ?? '') || undefined,
    category: String(row.category ?? '') || undefined,
    budget_text: String(row.budget_text ?? '') || undefined,
    complexity: row.complexity != null ? Number(row.complexity) : undefined,
  }
}

export function normalizeQuizResponse(data: QuizNextResponse): QuizNextResponse {
  const card = data.card
    ? normalizeQuizCard(data.card as unknown as Record<string, unknown>) ?? undefined
    : undefined
  return { ...data, card }
}
