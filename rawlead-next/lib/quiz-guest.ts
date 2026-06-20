export const QUIZ_COMPLETED_KEY = 'rawlead_quiz_completed_v1'

const IMPORT_WEIGHT = 4.0

export interface QuizGuestProfile {
  tags: Record<string, number>
  niches: string[]
  leads_per_week?: number
  cx_pref?: number
}

export interface QuizCompletedSnapshot {
  profile: QuizGuestProfile
  saved_at?: number
  history?: unknown[]
  completed_at?: string
}

export function normalizeQuizProfile(raw: unknown): QuizGuestProfile | null {
  if (!raw || typeof raw !== 'object') return null
  const row = raw as Record<string, unknown>

  const niches: string[] = []
  const nichesRaw = row.niches
  if (Array.isArray(nichesRaw)) {
    for (const item of nichesRaw) {
      if (typeof item === 'string' && item.trim()) {
        niches.push(item.trim())
      } else if (item && typeof item === 'object' && 'niche' in item) {
        const niche = String((item as { niche: unknown }).niche || '').trim()
        if (niche) niches.push(niche)
      }
    }
  }

  const tags: Record<string, number> = {}
  const tagsRaw = row.tags
  if (tagsRaw && typeof tagsRaw === 'object' && !Array.isArray(tagsRaw)) {
    for (const [key, weight] of Object.entries(tagsRaw as Record<string, unknown>)) {
      if (!key) continue
      tags[key] = typeof weight === 'number' ? weight : Number(weight) || IMPORT_WEIGHT
    }
  }
  const tagsImport = row.tags_to_import
  if (Array.isArray(tagsImport)) {
    for (const tag of tagsImport) {
      const canonical = String(tag || '').trim()
      if (canonical) tags[canonical] = IMPORT_WEIGHT
    }
  }

  const leads = row.leads_per_week
  const cxPref = row.cx_pref

  return {
    tags,
    niches: Array.from(new Set(niches)),
    leads_per_week: typeof leads === 'number' ? leads : Number(leads) || 0,
    cx_pref: cxPref != null ? Number(cxPref) : undefined,
  }
}

function profileHasQuizSignal(profile: QuizGuestProfile): boolean {
  return Object.keys(profile.tags).length > 0 || profile.niches.length > 0
}

export function readQuizCompleted(): QuizCompletedSnapshot | null {
  if (typeof window === 'undefined') return null
  try {
    const raw = localStorage.getItem(QUIZ_COMPLETED_KEY)
    if (!raw) return null
    const data = JSON.parse(raw) as QuizCompletedSnapshot
    const profile = normalizeQuizProfile(data?.profile)
    if (!profile || !profileHasQuizSignal(profile)) return null
    return { ...data, profile }
  } catch {
    return null
  }
}

export function hasAnonQuizCompleted(): boolean {
  return readQuizCompleted() != null
}

export function writeQuizCompleted(profile: QuizGuestProfile | unknown): void {
  if (typeof window === 'undefined') return
  const normalized = normalizeQuizProfile(profile)
  if (!normalized) return
  try {
    localStorage.setItem(
      QUIZ_COMPLETED_KEY,
      JSON.stringify({ profile: normalized, saved_at: Date.now(), completed_at: new Date().toISOString() }),
    )
    localStorage.removeItem('rawlead_quiz_session')
  } catch {
    /* ignore */
  }
}

export function notifyQuizComplete(): void {
  if (typeof window === 'undefined') return
  window.dispatchEvent(new CustomEvent('rawlead-quiz-complete'))
}
