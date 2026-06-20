import { meApi, quizApi } from './api'
import { readQuizCompleted } from './quiz-guest'

const GUEST_SKILLS_KEYS = ['rawlead_lenta_skills', 'rawlead_guest_skills'] as const

function readGuestSkillTags(): string[] {
  const tags: string[] = []
  if (typeof window === 'undefined') return tags

  for (const key of GUEST_SKILLS_KEYS) {
    try {
      const raw = localStorage.getItem(key)
      if (!raw) continue
      const parsed = JSON.parse(raw)
      if (!Array.isArray(parsed)) continue
      for (const item of parsed) {
        if (typeof item === 'string' && item && !tags.includes(item)) {
          tags.push(item)
        }
      }
    } catch {
      /* ignore */
    }
  }
  return tags
}

function readQuizCompletedProfile(): { tags: Record<string, number>; niches: string[] } | null {
  const snap = readQuizCompleted()
  if (!snap?.profile) return null
  return {
    tags: snap.profile.tags,
    niches: Array.isArray(snap.profile.niches) ? snap.profile.niches : [],
  }
}

function clearGuestSkillKeys(): void {
  if (typeof window === 'undefined') return
  for (const key of GUEST_SKILLS_KEYS) {
    try {
      localStorage.removeItem(key)
    } catch {
      /* ignore */
    }
  }
}

/** WP rawlead-cabinet.js mergeGuestSkillsAfterAuth — after bot login. */
export async function mergeGuestSkillsAfterAuth(): Promise<void> {
  const quizProfile = readQuizCompletedProfile()
  if (quizProfile) {
    try {
      await quizApi.importTags(quizProfile.tags, quizProfile.niches)
      clearGuestSkillKeys()
      window.dispatchEvent(new CustomEvent('rawlead-tags-imported'))
      return
    } catch {
      /* fall through to string-tag merge */
    }
  }

  const guest = readGuestSkillTags()
  if (!guest.length) return

  try {
    const data = await meApi.tags()
    const server = data.tags || []
    const merged = [...server]
    for (const tag of guest) {
      if (!merged.includes(tag)) merged.push(tag)
    }
    if (merged.length === server.length) {
      clearGuestSkillKeys()
      return
    }
    await meApi.putTags(merged)
    clearGuestSkillKeys()
    window.dispatchEvent(new CustomEvent('rawlead-tags-imported'))
  } catch {
    /* keep guest keys if merge failed — WP parity */
  }
}
