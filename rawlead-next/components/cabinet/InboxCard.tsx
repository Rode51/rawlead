'use client'

import { useRef, useEffect, useState } from 'react'
import { meApi } from '@/lib/api'
import type { LeadItem } from '@/lib/types'
import { SOURCE_LABEL, SOURCE_COLOR, DIFFICULTY_BADGES } from '@/lib/utils'

function formatDate(isoStr: string): string {
  const d = new Date(isoStr)
  const months = ['янв', 'фев', 'мар', 'апр', 'мая', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']
  return `${d.getDate()} ${months[d.getMonth()]}`
}

interface Props {
  item: LeadItem
  onDelete: (id: number) => void
}

export default function InboxCard({ item, onDelete }: Props) {
  const [open, setOpen] = useState(false)
  const [copied, setCopied] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const bodyRef = useRef<HTMLDivElement>(null)
  const [hovered, setHovered] = useState(false)

  const srcColor = SOURCE_COLOR[item.source] ?? '#6B6B6B'
  const srcLabel = SOURCE_LABEL[item.source] ?? item.source
  const displayDate = item.replied_at ? formatDate(item.replied_at) : formatDate(item.created_at)
  const diffBadge = item.difficulty ? DIFFICULTY_BADGES[Number(item.difficulty)] : null

  // Animate accordion body
  useEffect(() => {
    const el = bodyRef.current
    if (!el) return
    el.style.maxHeight = open ? el.scrollHeight + 40 + 'px' : '0px'
  }, [open])

  async function handleCopy() {
    if (!item.reply_draft) return
    try {
      await navigator.clipboard.writeText(item.reply_draft)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {/* clipboard unavailable */}
  }

  async function handleDelete() {
    if (!confirmDelete) { setConfirmDelete(true); return }
    setDeleting(true)
    try {
      await meApi.deleteReply(item.id)
      onDelete(item.id)
    } catch {
      setDeleting(false)
      setConfirmDelete(false)
    }
  }

  const shadow = (open || hovered) ? '7px 7px 0 #111010' : '4px 4px 0 #111010'
  const lift = (open || hovered) ? 'translate(-2px,-2px)' : ''

  return (
    <article
      className="bg-white relative overflow-hidden select-none"
      style={{
        border: '2px solid #111010',
        boxShadow: shadow,
        transform: lift,
        transition: 'box-shadow 160ms ease-out, transform 160ms ease-out',
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {/* Left source accent bar */}
      <div
        className="absolute left-0 top-0 bottom-0"
        style={{ width: 4, background: srcColor }}
        aria-hidden="true"
      />

      {/* Collapsed header — click to toggle */}
      <button
        className="w-full text-left"
        style={{ paddingLeft: 20, paddingRight: 22, paddingTop: 18, paddingBottom: open ? 14 : 18 }}
        onClick={() => setOpen(v => !v)}
      >
        {/* Meta */}
        <div className="flex items-center gap-2 flex-wrap" style={{ marginBottom: 10 }}>
          <span
            className="inline-flex items-center gap-[5px] text-[11px] font-bold uppercase tracking-wide px-2 py-[3px] leading-none"
            style={{ color: srcColor, background: srcColor + '15', border: `1.5px solid ${srcColor}55` }}
          >
            <span aria-hidden="true" style={{ display: 'inline-block', width: 6, height: 6, borderRadius: '50%', background: srcColor }} />
            {srcLabel}
          </span>
          <span className="text-[11px]" style={{ color: '#9B9B97' }}>{displayDate}</span>
          <span className="ml-auto text-[11px]" style={{ color: '#6B6B6B', flexShrink: 0 }}>
            {open ? '▲ Скрыть' : '▼ Черновик'}
          </span>
        </div>

        {/* Title */}
        <h3
          className="font-display font-black text-[#111010] leading-tight"
          style={{ fontSize: '0.9375rem', letterSpacing: '-0.02em', marginBottom: 6 }}
        >
          {item.title}
        </h3>

        {/* Budget + difficulty inline */}
        <div className="flex items-center gap-3 flex-wrap">
          {item.budget_text && (
            <span style={{ fontSize: '0.875rem', fontWeight: 700, color: '#111010' }}>
              {item.budget_text}
            </span>
          )}
          {diffBadge && (
            <span style={{ fontSize: '0.75rem', color: '#525252' }}>
              {diffBadge.badge}
            </span>
          )}
        </div>
      </button>

      {/* Expandable body */}
      <div
        ref={bodyRef}
        style={{
          maxHeight: 0,
          overflow: 'hidden',
          transition: 'max-height 280ms cubic-bezier(0.22, 1, 0.36, 1)',
        }}
        onClick={e => e.stopPropagation()}
      >
        <div style={{ borderTop: '1.5px solid #EAEAE6', padding: '16px 22px 20px 20px' }}>
          {item.reply_draft ? (
            <p className="whitespace-pre-wrap" style={{ fontSize: '0.8125rem', color: '#1A1A1A', lineHeight: 1.65, marginBottom: 16 }}>
              {item.reply_draft}
            </p>
          ) : (
            <p style={{ fontSize: '0.8125rem', color: '#6B6B6B', fontStyle: 'italic', marginBottom: 16 }}>
              Черновик появится после анализа
            </p>
          )}

          <div className="flex items-center gap-3 flex-wrap">
            <button
              onClick={handleCopy}
              disabled={!item.reply_draft}
              className="font-bold text-[12px] uppercase tracking-wider text-[#0A0A0A] bg-white border-2 border-[#0A0A0A] hover:bg-[#F5F5F0] transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              style={{ minHeight: 40, padding: '0 16px', boxShadow: '2px 2px 0 #0A0A0A' }}
            >
              {copied ? 'Скопировано ✓' : 'Скопировать текст'}
            </button>

            {confirmDelete ? (
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="font-bold text-[12px] uppercase tracking-wider border-2 border-red-600 bg-white hover:bg-red-50 transition-colors disabled:opacity-40"
                style={{ minHeight: 40, padding: '0 16px', color: '#DC2626' }}
              >
                {deleting ? 'Удаляем…' : 'Подтвердить?'}
              </button>
            ) : (
              <button
                onClick={handleDelete}
                style={{ fontSize: '0.75rem', color: '#DC2626', background: 'none', border: 'none', cursor: 'pointer', padding: '0 4px', minHeight: 40, textDecoration: 'underline' }}
              >
                Удалить из ЛК
              </button>
            )}
          </div>
        </div>
      </div>
    </article>
  )
}
