'use client'

import { useRef, useEffect, useState, useCallback } from 'react'
import type { LeadItem } from '@/lib/types'
import type { FeedTier } from '@/lib/auth-context'
import { meApi, draftErrorUserMessage } from '@/lib/api'
import { addPendingDraft, removePendingDraft, notifyInboxRefresh } from '@/lib/pending-drafts'
import { showDraftToast } from '@/lib/draft-toast'
import MatchBar from './MatchBar'
import { SOURCE_COLOR, SOURCE_LABEL, timeAgo, DIFFICULTY_BADGES } from '@/lib/utils'

const DRAFT_BTN_SLOW_MS = 20000
const DRAFT_BTN_SLOW_RU = 'Сложный бриф, ИИ полирует отклик...'
const DRAFT_BTN_QUEUE_RU = 'В очереди…'

interface Props {
  item: LeadItem
  feedTier: FeedTier
  hasUserSkills: boolean
  isExpanded: boolean
  onToggle: () => void
  onQuizClick: () => void
  onLoginClick: () => void
  anonQuizDone?: boolean
  index?: number
}

function pulseFocusCard(el: HTMLElement | null) {
  if (!el) return
  el.classList.add('rl-lead-card--push-focus')
  window.setTimeout(() => el.classList.remove('rl-lead-card--push-focus'), 2800)
}

export default function FeedCard({
  item,
  feedTier,
  hasUserSkills,
  isExpanded,
  onToggle,
  onQuizClick,
  onLoginClick,
  anonQuizDone = false,
  index = 0,
}: Props) {
  const cardRef = useRef<HTMLElement>(null)
  const bodyRef = useRef<HTMLDivElement>(null)
  const draftStartedRef = useRef<number | null>(null)
  const [hovered, setHovered] = useState(false)
  const [draftText, setDraftText] = useState(item.reply_draft || '')
  const [draftOpen, setDraftOpen] = useState(false)
  const [draftGenerating, setDraftGenerating] = useState(false)
  const [draftDone, setDraftDone] = useState(!!item.reply_draft?.trim())
  const [draftQueued, setDraftQueued] = useState(false)
  const [draftSlow, setDraftSlow] = useState(false)
  const [copied, setCopied] = useState(false)
  const [freePremiumStep, setFreePremiumStep] = useState(false)
  const [showUpsell, setShowUpsell] = useState(false)
  const [shakeCta, setShakeCta] = useState(false)

  const syncGeneratingLabel = useCallback(() => {
    const started = draftStartedRef.current
    if (!started) {
      setDraftSlow(false)
      return
    }
    setDraftSlow(Date.now() - started > DRAFT_BTN_SLOW_MS)
  }, [])

  useEffect(() => {
    if (!draftGenerating) return
    syncGeneratingLabel()
    const id = window.setInterval(syncGeneratingLabel, 1000)
    return () => clearInterval(id)
  }, [draftGenerating, syncGeneratingLabel])

  useEffect(() => {
    setFreePremiumStep(false)
    setShowUpsell(false)
  }, [feedTier])

  useEffect(() => {
    const el = bodyRef.current
    if (!el) return
    if (isExpanded) {
      el.style.maxHeight = el.scrollHeight + 40 + 'px'
    } else {
      el.style.maxHeight = '0px'
      if (!draftGenerating) setDraftOpen(false)
    }
  }, [isExpanded, draftText, draftOpen, draftGenerating])

  const tags = item.lead_tags?.slice(0, 3) ?? []

  function getTagLabel(tag: string): string {
    if (item.lead_tag_labels?.[tag]) return item.lead_tag_labels[tag]
    return tag.replace(/_/g, ' ')
  }

  function handleReplyClick(e: React.MouseEvent) {
    e.stopPropagation()
    if (feedTier === 'anon') {
      if (anonQuizDone) {
        onLoginClick()
      } else {
        onQuizClick()
      }
      return
    }
    if (feedTier === 'expired_trial') {
      window.location.href = '/pricing/'
      return
    }
    if (feedTier === 'free') {
      if (freePremiumStep) {
        window.location.href = '/pricing/'
        return
      }
      if (!isExpanded) onToggle()
      setShowUpsell(true)
      setShakeCta(true)
      window.setTimeout(() => setShakeCta(false), 500)
      setFreePremiumStep(true)
      return
    }
    if (feedTier !== 'premium') return
    void generateDraft()
  }

  async function generateDraft() {
    if (draftGenerating) return
    if (!isExpanded) onToggle()

    draftStartedRef.current = Date.now()
    setDraftGenerating(true)
    setDraftOpen(true)
    setDraftQueued(false)
    setDraftSlow(false)

    addPendingDraft(item.id, { title: item.title, category: item.category })
    notifyInboxRefresh()
    showDraftToast('Черновик появится в личном кабинете после генерации')

    try {
      const res = await meApi.createDraft(item.id, {
        onPoll: data => { if (data.queued) setDraftQueued(true) },
      })
      if (res.queued) setDraftQueued(true)
      const text = res.reply_draft || ''
      setDraftText(text)
      setDraftDone(true)
      removePendingDraft(item.id)
      notifyInboxRefresh()
      pulseFocusCard(cardRef.current)
    } catch (err) {
      removePendingDraft(item.id)
      notifyInboxRefresh()
      setDraftText('')
      setDraftOpen(false)
      showDraftToast(draftErrorUserMessage(err))
    } finally {
      draftStartedRef.current = null
      setDraftGenerating(false)
      setDraftQueued(false)
      setDraftSlow(false)
    }
  }

  async function copyDraft() {
    if (!draftText) return
    try {
      await navigator.clipboard.writeText(draftText)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch { /* ignore */ }
  }

  const isAnon = feedTier === 'anon'
  const isExpiredTrial = feedTier === 'expired_trial'
  const isPremium = feedTier === 'premium'
  const ctaLabel = isAnon
    ? (anonQuizDone ? 'Войти — персональная лента →' : 'Настроить ленту →')
    : isExpiredTrial
    ? 'Premium — черновики и персонализация →'
    : feedTier === 'free' && freePremiumStep
    ? 'Купить Premium →'
    : 'Написать отклик →'

  const replyBtnLabel = draftGenerating
    ? (draftSlow ? DRAFT_BTN_SLOW_RU : draftQueued ? DRAFT_BTN_QUEUE_RU : 'Генерируем…')
    : ctaLabel

  const shadow = (isExpanded || hovered)
    ? '7px 7px 0 #111010'
    : '4px 4px 0 #111010'

  const lift = (isExpanded || hovered) ? 'translate(-2px,-2px)' : ''

  const cardClass = [
    'rl-lead-card rl-feed-card bg-white flex flex-col cursor-pointer select-none relative overflow-hidden',
    draftGenerating ? 'rl-lead-card--draft-pending' : '',
    draftDone && isExpanded ? 'rl-lead-card--draft-done is-expanded' : '',
    isExpanded ? 'is-expanded' : '',
    shakeCta ? 'rl-lead-card--shake-cta' : '',
  ].filter(Boolean).join(' ')

  return (
    <article
      ref={cardRef}
      data-testid="feed-card"
      data-id={item.id}
      className={cardClass}
      style={{
        minHeight: isExpanded ? undefined : 280,
        alignSelf: isExpanded ? 'start' : undefined,
        border: '2px solid #111010',
        boxShadow: draftGenerating ? undefined : shadow,
        transform: lift,
        transition: 'box-shadow 160ms ease-out, transform 160ms ease-out',
        animationDelay: `${Math.min(index, 8) * 55}ms`,
      }}
      onClick={onToggle}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      tabIndex={0}
      role="button"
      aria-label="Карточка заказа"
      onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onToggle() } }}
    >
      <div
        className="absolute left-0 top-0 bottom-0"
        style={{ width: 4, background: SOURCE_COLOR[item.source] ?? '#6B6B6B', transition: 'background 300ms' }}
        aria-hidden="true"
      />

      <div className="rl-feed-card__body-inner flex flex-col flex-1" style={{ paddingLeft: 20, paddingRight: 22, paddingTop: 20, paddingBottom: 18 }}>
        <div className="flex items-center gap-2 mb-3">
          <span
            className="inline-flex items-center gap-[5px] text-[11px] font-bold uppercase tracking-wide px-2 py-[3px] leading-none shrink-0"
            style={{
              color: SOURCE_COLOR[item.source] ?? '#6B6B6B',
              background: (SOURCE_COLOR[item.source] ?? '#6B6B6B') + '15',
              border: `1.5px solid ${(SOURCE_COLOR[item.source] ?? '#6B6B6B')}55`,
            }}
          >
            <span
              aria-hidden="true"
              style={{ display: 'inline-block', width: 6, height: 6, borderRadius: '50%', background: SOURCE_COLOR[item.source] ?? '#6B6B6B', flexShrink: 0 }}
            />
            {SOURCE_LABEL[item.source] ?? item.source}
          </span>

          {item.is_hot && (
            <span
              className="text-[9px] font-black uppercase px-1.5 py-[3px] text-white tracking-widest leading-none shrink-0"
              style={{ background: '#EA580C' }}
            >
              HOT
            </span>
          )}

          <span className="text-[11px] ml-auto shrink-0 tabular-nums" style={{ color: '#9B9B97' }}>
            {timeAgo(item.created_at)}
          </span>
        </div>

        <h3
          className={`font-display font-black text-[#111010] leading-tight mb-2 ${isExpanded ? '' : 'line-clamp-2'}`}
          style={{ fontSize: '1.0625rem', letterSpacing: '-0.025em', minHeight: isExpanded ? undefined : '2.65em' }}
        >
          {item.title}
        </h3>

        {item.budget_text && (
          <p className="text-[15px] font-bold leading-none mb-4" style={{ color: '#111010' }}>
            {item.budget_text}
          </p>
        )}

        <div onClick={e => e.stopPropagation()} className="rl-match mb-3" data-testid="feed-match-bar">
          <MatchBar
            item={item}
            feedTier={feedTier}
            hasUserSkills={hasUserSkills}
            onQuizClick={onQuizClick}
            onLoginClick={onLoginClick}
            anonQuizDone={anonQuizDone}
          />
        </div>

        {tags.length > 0 && (
          <div className="flex gap-1.5 overflow-hidden" style={{ flexWrap: 'nowrap', minHeight: 22, maxHeight: 22 }}>
            {tags.map(tag => (
              <span
                key={tag}
                className="text-[10px] font-semibold px-2 py-0.5 leading-snug shrink-0 whitespace-nowrap"
                style={{ background: '#EEEDEA', color: '#6B6B6B' }}
                title={getTagLabel(tag)}
              >
                {getTagLabel(tag)}
              </span>
            ))}
          </div>
        )}

        <div className="flex-1" style={{ minHeight: 12 }} />

        <div onClick={e => e.stopPropagation()} className="mt-3">
          {showUpsell && feedTier === 'free' && (
            <p
              className="rl-card-upsell text-[11px] text-[#525252] leading-snug mb-2 text-center"
              data-card-upsell
            >
              <span aria-hidden="true">✍️ </span>
              Черновик ИИ — только Premium
              <br />
              →{' '}
              <a href="/pricing/" className="underline font-semibold text-[#111010]" onClick={e => e.stopPropagation()}>
                Подключить Premium 790 ₽
              </a>{' '}
              или{' '}
              <a href="/pricing/" className="underline font-semibold text-[#111010]" onClick={e => e.stopPropagation()}>
                Trial бесплатно 3 дня
              </a>
            </p>
          )}
          <button
            data-testid="feed-card-cta"
            data-free-premium-step={freePremiumStep ? '1' : undefined}
            className={`rl-feed-card__reply-btn w-full h-9 text-[11px] font-bold uppercase tracking-widest border-2 border-[#111010] text-[#111010] bg-white transition-colors duration-150 hover:bg-[#111010] hover:text-white ${draftGenerating ? 'is-generating' : ''} ${freePremiumStep ? 'rl-card-cta--buy-premium' : ''}`}
            onClick={handleReplyClick}
            disabled={draftGenerating}
          >
            {replyBtnLabel}
          </button>
        </div>
      </div>

      <div
        ref={bodyRef}
        className="rl-feed-card__section"
        data-testid="feed-card-body"
        style={{
          maxHeight: 0,
          overflow: 'hidden',
          transition: 'max-height 280ms cubic-bezier(0.22, 1, 0.36, 1)',
        }}
        onClick={e => e.stopPropagation()}
      >
        <div style={{ borderTop: '2px solid #EAEAE6', padding: '16px 22px 20px 20px' }}>
          {item.difficulty && DIFFICULTY_BADGES[Number(item.difficulty)] && (
            <p className="text-[12px] mb-3" style={{ color: '#525252' }}>
              <span className="font-semibold">Сложность: </span>
              <span title={DIFFICULTY_BADGES[Number(item.difficulty)].tip}>
                {DIFFICULTY_BADGES[Number(item.difficulty)].badge}
              </span>
            </p>
          )}

          {item.task_summary && (
            <p className="text-[14px] leading-relaxed mb-4" style={{ color: '#3D3D3A' }}>
              {item.task_summary}
            </p>
          )}
          {item.url && (
            <a
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[12px] font-semibold underline underline-offset-2 transition-colors hover:text-[#111010]"
              style={{ color: '#9B9B97' }}
              onClick={e => e.stopPropagation()}
            >
              Читать на бирже ↗
            </a>
          )}

          {isPremium && (draftOpen || draftGenerating) && (
            <div className="mt-4 pt-4 border-t border-[#EAEAE6]" data-testid="feed-draft-panel">
              {draftGenerating ? (
                <div className="rl-feed-card__draft-skeleton flex flex-col gap-2">
                  <div className="h-3 bg-[#EEEDEA] animate-pulse w-full" />
                  <div className="h-3 bg-[#EEEDEA] animate-pulse w-[92%]" />
                  <div className="h-3 bg-[#EEEDEA] animate-pulse w-[78%]" />
                  <p className="text-[13px] text-[#6B6B6B] mt-1">{replyBtnLabel}</p>
                </div>
              ) : draftText ? (
                <>
                  <p
                    className="rl-feed-card__reply text-[14px] leading-relaxed mb-3 whitespace-pre-wrap"
                    data-testid="feed-draft-text"
                    data-reply-text
                  >
                    {draftText}
                  </p>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      data-testid="feed-draft-copy"
                      onClick={() => void copyDraft()}
                      className="h-8 px-3 text-[11px] font-bold border-2 border-[#111010] bg-white"
                    >
                      {copied ? 'Скопировано' : 'Копировать'}
                    </button>
                    <button
                      type="button"
                      data-testid="feed-draft-collapse"
                      onClick={() => setDraftOpen(false)}
                      className="h-8 px-3 text-[11px] font-bold border-2 border-[#111010] bg-[#F5F4F0]"
                    >
                      Свернуть
                    </button>
                  </div>
                </>
              ) : null}
            </div>
          )}
        </div>
      </div>
    </article>
  )
}
