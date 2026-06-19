'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import Link from 'next/link'
import { feedApi } from '@/lib/api'
import type { LeadItem } from '@/lib/types'
import ScrollReveal from '@/components/ui/ScrollReveal'

const SOURCE_MAP: Record<string, { label: string; color: string }> = {
  fl:     { label: 'FL.ru',    color: '#00A65A' },
  kwork:  { label: 'Kwork',    color: '#EA580C' },
  youdo:  { label: 'YouDo',    color: '#2563EB' },
  tg:     { label: 'Telegram', color: '#0088CC' },
  'freelance-ru': { label: 'Freelance', color: '#8B5CF6' },
}

// Показывается когда API недоступен с localhost
const DEMO: Partial<LeadItem>[] = [
  {
    id: 1, source: 'fl',    is_hot: true,
    title: 'Разработка интернет-магазина на WordPress + WooCommerce',
    budget_text: 'от 25 000 ₽',
    ai_score: 89,
    task_summary: 'Каталог, корзина, оплата, адаптив. Сроки 3 недели.',
  },
  {
    id: 2, source: 'kwork', is_hot: false,
    title: 'Python-парсер цен конкурентов с экспортом в Google Sheets',
    budget_text: 'до 8 000 ₽',
    ai_score: 74,
    task_summary: 'Ежедневный обход 3 сайтов, cron, gspread.',
  },
  {
    id: 3, source: 'tg',    is_hot: false,
    title: 'Дизайн landing page для SaaS — Figma + адаптив',
    budget_text: 'от 15 000 ₽',
    ai_score: 91,
    task_summary: 'Бренд-кит есть, нужен лендинг 5 секций.',
  },
]

function MatchBar({ score }: { score: number }) {
  return (
    <div className="mt-4 pt-3 border-t-2 border-[#EEEDEA]">
      <div className="flex items-center justify-between text-[11px] font-display font-black uppercase tracking-[0.06em] mb-2">
        <span className="text-[#6B6B6B]">Совпадение</span>
        <span className="text-[#111010]">{score}%</span>
      </div>
      <div className="h-[3px] bg-[#EEEDEA] overflow-hidden">
        <motion.div
          className="h-full bg-[#111010]"
          initial={{ width: 0 }}
          whileInView={{ width: `${score}%` }}
          viewport={{ once: true }}
          transition={{ type: 'spring', stiffness: 180, damping: 28, delay: 0.3 }}
        />
      </div>
    </div>
  )
}

function Card({ lead, index }: { lead: Partial<LeadItem>; index: number }) {
  const src = SOURCE_MAP[lead.source ?? ''] ?? { label: lead.source ?? '', color: '#6B6B6B' }

  return (
    <motion.article
      initial={{ opacity: 0, y: 36 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-40px' }}
      transition={{ type: 'spring', stiffness: 260, damping: 22, delay: index * 0.1 }}
      className="group bg-[#F5F4F0] border-2 border-[#111010] shadow-neo p-5 cursor-pointer hover:shadow-neo-hover hover:-translate-x-0.5 hover:-translate-y-0.5 transition-all duration-150"
    >
      {/* Source + hot badge */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <span
          className="text-[11px] font-display font-black uppercase tracking-[0.08em] px-2 py-1 border-2"
          style={{ color: src.color, borderColor: src.color }}
        >
          {src.label}
        </span>
        {lead.is_hot && (
          <span className="text-[11px] font-display font-black uppercase px-2 py-1 bg-[#EA580C] text-white border-2 border-[#EA580C]">
            HOT
          </span>
        )}
      </div>

      {/* Title */}
      <h3 className="font-display font-black text-[#111010] text-[15px] leading-snug mb-2 line-clamp-2">
        {lead.title}
      </h3>

      {/* Summary */}
      {lead.task_summary && (
        <p className="font-sans text-[#6B6B6B] text-xs leading-relaxed line-clamp-2 mb-1">
          {lead.task_summary}
        </p>
      )}

      {/* Budget */}
      {lead.budget_text && (
        <p className="font-display font-black text-[#111010] text-sm mt-2">{lead.budget_text}</p>
      )}

      {/* Match bar */}
      {lead.ai_score != null && <MatchBar score={lead.ai_score} />}
    </motion.article>
  )
}

function Skeleton() {
  return (
    <div className="bg-[#EEEDEA] border-2 border-[#D4D3D0] h-52 animate-pulse" />
  )
}

export default function LivePreview() {
  const [leads, setLeads] = useState<Partial<LeadItem>[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    feedApi.list({ limit: 3 })
      .then(r => setLeads(r.items.slice(0, 3)))
      .catch(() => setLeads(DEMO))
      .finally(() => setLoading(false))
  }, [])

  return (
    <section className="py-24 bg-[#EEEDEA] border-b-2 border-[#111010]">
      <div
        className="mx-auto px-6"
        style={{ maxWidth: 'var(--rl-container)' }}
      >
        <ScrollReveal className="mb-14">
          <p className="text-[11px] font-display font-black uppercase tracking-[0.2em] text-[#6B6B6B] mb-4">
            Живая лента
          </p>
          <h2
            className="font-display font-black text-[#111010] leading-[0.95] tracking-[-0.03em]"
            style={{ fontSize: 'clamp(36px, 5vw, 56px)' }}
          >
            Заказы прямо сейчас
          </h2>
        </ScrollReveal>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {loading
            ? [0, 1, 2].map(i => <Skeleton key={i} />)
            : leads.map((lead, i) => <Card key={lead.id ?? i} lead={lead} index={i} />)
          }
        </div>

        <ScrollReveal delay={0.15} className="mt-10 text-center">
          <Link
            href="/lenta/"
            className="inline-flex items-center gap-2 font-display font-black text-sm uppercase tracking-[0.08em] text-[#111010] underline underline-offset-4 hover:no-underline hover:text-[#E8A020] transition-colors"
          >
            Смотреть все заказы →
          </Link>
        </ScrollReveal>
      </div>
    </section>
  )
}
