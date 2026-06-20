'use client'

import type { QuizGuestProfile } from '@/lib/quiz-guest'

const QUIZ_NICHES = ['dev', 'design', 'marketing', 'text'] as const

const CATEGORY_META: Record<string, { emoji: string; label: string }> = {
  dev: { emoji: '💻', label: 'Разработка' },
  design: { emoji: '🎨', label: 'Дизайн' },
  marketing: { emoji: '📣', label: 'Маркетинг' },
  text: { emoji: '✍️', label: 'Тексты' },
}

function nicheConfidence(profile: QuizGuestProfile): Record<string, number> {
  const conf: Record<string, number> = {}
  for (const niche of QUIZ_NICHES) conf[niche] = 0
  for (const niche of profile.niches || []) {
    if (niche in conf) conf[niche] = Math.max(conf[niche], 2)
  }
  for (const [tag, weight] of Object.entries(profile.tags || {})) {
    if (tag.startsWith('niche:')) {
      const n = tag.slice(6)
      if (n in conf) conf[n] = Math.max(conf[n], weight)
    }
  }
  return conf
}

interface Props {
  profile: QuizGuestProfile
}

export default function QuizCategoryBars({ profile }: Props) {
  const conf = nicheConfidence(profile)
  let maxConf = 1
  for (const niche of QUIZ_NICHES) {
    if (conf[niche] > maxConf) maxConf = conf[niche]
  }

  const rows = QUIZ_NICHES.map(niche => {
    const raw = Math.max(0, conf[niche] || 0)
    const pct = raw <= 0 ? 0 : Math.round((raw / maxConf) * 100)
    return { niche, pct, raw, meta: CATEGORY_META[niche] }
  })
    .filter(row => row.pct > 0)
    .sort((a, b) => b.raw - a.raw)
    .slice(0, 3)

  if (!rows.length) return null

  return (
    <div className="flex flex-col gap-2 mb-2" data-testid="quiz-category-bars">
      {rows.map(row => (
        <div key={row.niche} className="flex items-center gap-2">
          <span className="text-[13px] font-semibold text-[#111010] shrink-0 min-w-[108px]">
            {row.meta.emoji} {row.meta.label}
          </span>
          <span className="flex-1 h-2 bg-[#EEEDEA] relative overflow-hidden">
            <span
              className="absolute inset-y-0 left-0 bg-[#FACC15]"
              style={{ width: `${row.pct}%` }}
              aria-hidden="true"
            />
          </span>
        </div>
      ))}
    </div>
  )
}
