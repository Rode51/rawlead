'use client'

import { useCallback, useEffect, useState } from 'react'
import { quizApi } from '@/lib/api'
import { useAuth } from '@/lib/auth-context'
import type { QuizCard } from '@/lib/types'

interface Props {
  onClose: () => void
  onLoginNeeded: () => void
}

type QuizStep = 'intro' | 'quiz' | 'done' | 'error'

interface HistoryItem {
  card_id: string
  action: 'like' | 'skip'
  tags: string[]
}

const COMPLETED_KEY = 'rawlead_quiz_completed_v1'
const SESSION_KEY = 'rawlead_quiz_session'

export default function QuizOverlay({ onClose, onLoginNeeded }: Props) {
  const auth = useAuth()
  const [step, setStep] = useState<QuizStep>('intro')
  const [card, setCard] = useState<QuizCard | null>(null)
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [loading, setLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')
  const [importing, setImporting] = useState(false)

  const persistCompleted = useCallback((profile: { tags: Record<string, number>; niches: string[] }) => {
    try {
      localStorage.setItem(COMPLETED_KEY, JSON.stringify({ profile, saved_at: Date.now() }))
      localStorage.removeItem(SESSION_KEY)
    } catch { /* ignore */ }
  }, [])

  async function startQuiz() {
    setLoading(true)
    setErrorMsg('')
    try {
      const res = await quizApi.start()
      if (res.done || !res.card) {
        setStep('done')
      } else {
        setCard(res.card)
        setHistory([])
        setStep('quiz')
      }
    } catch {
      setStep('error')
      setErrorMsg('Не удалось загрузить квиз')
    } finally {
      setLoading(false)
    }
  }

  async function finishQuiz(profile: { tags: Record<string, number>; niches: string[] }) {
    persistCompleted(profile)
    if (auth.status === 'auth') {
      setImporting(true)
      try {
        await quizApi.importTags(profile.tags, profile.niches)
        window.dispatchEvent(new CustomEvent('rawlead-tags-imported'))
        if (typeof localStorage !== 'undefined') {
          localStorage.setItem('rawlead_user_tags_rev', String(Date.now()))
        }
        await auth.refreshTags()
      } catch {
        // import failed but quiz done
      } finally {
        setImporting(false)
      }
    }
    setStep('done')
  }

  async function answer(action: 'like' | 'skip') {
    if (!card || loading) return
    const newHistory: HistoryItem[] = [...history, {
      card_id: card.id,
      action,
      tags: action === 'like' ? card.tags : [],
    }]
    setHistory(newHistory)
    setLoading(true)
    try {
      const res = await quizApi.next(newHistory)
      if (res.done && res.profile) {
        await finishQuiz(res.profile)
      } else if (res.card) {
        setCard(res.card)
      }
    } catch {
      setErrorMsg('Ошибка — попробуй снова')
    } finally {
      setLoading(false)
    }
  }

  function handleRetake() {
    setStep('intro')
    setCard(null)
    setHistory([])
    setErrorMsg('')
    void startQuiz()
  }

  return (
    <div
      id="rl-feed-quiz-overlay"
      data-testid="quiz-overlay"
      className="fixed inset-0 z-[150] flex items-center justify-center"
      aria-hidden="false"
    >
      <div
        id="rl-feed-quiz-overlay-backdrop"
        className="absolute inset-0 bg-black/60"
        onClick={onClose}
      />

      <div
        className="relative bg-white z-10 w-full max-w-[480px] mx-4 p-8"
        style={{ border: '2px solid #111010', boxShadow: '8px 8px 0 #111010' }}
      >
        <button
          id="rl-feed-quiz-overlay-close"
          data-testid="quiz-close"
          className="absolute top-4 right-4 text-[#6B6B6B] hover:text-[#111010] text-[18px]"
          onClick={onClose}
        >
          ✕
        </button>

        <div id="rl-quiz-stage" className={step === 'intro' ? 'rl-quiz-stage--intro' : step === 'quiz' ? 'rl-quiz-stage--cards' : ''}>
          {step === 'intro' && (
            <div id="rl-quiz-intro" data-testid="quiz-intro" className="flex flex-col gap-6">
              <div>
                <h2 className="font-black text-[22px] text-[#111010] leading-tight mb-2">
                  Ответь на карточки — лента найдёт твои заказы
                </h2>
                <p className="text-[14px] text-[#6B6B6B]">
                  Покажем заказы с твоим стеком и %&nbsp;совместимости
                </p>
              </div>
              <button
                id="rl-quiz-intro-start"
                data-testid="quiz-start"
                onClick={startQuiz}
                disabled={loading}
                className="h-12 px-6 font-black text-[13px] uppercase tracking-wider text-white bg-[#111010] border-2 border-[#111010] hover:bg-[#333] transition-colors disabled:opacity-60"
              >
                {loading ? 'Загружаем…' : 'Настроить ленту →'}
              </button>
            </div>
          )}

          {step === 'quiz' && card && (
            <div id="rl-quiz-play" data-testid="quiz-play" className="flex flex-col gap-5">
              <p className="text-[11px] font-bold uppercase tracking-widest text-[#6B6B6B]">Суть задания</p>
              <div id="rl-quiz-card" data-testid="quiz-card">
                <h3 id="rl-quiz-card-title" className="font-black text-[18px] text-[#111010] leading-snug mb-2">{card.title}</h3>
                {card.body && (
                  <p className="text-[14px] text-[#1A1918] leading-relaxed">{card.body}</p>
                )}
              </div>
              {card.tags.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {card.tags.map(tag => (
                    <span key={tag} className="text-[11px] font-semibold px-2 py-0.5 bg-[#F5F5F0] text-[#525252]">
                      #{tag}
                    </span>
                  ))}
                </div>
              )}
              <div className="flex gap-3 pt-2">
                <button
                  id="rl-quiz-nope"
                  data-testid="quiz-nope"
                  onClick={() => answer('skip')}
                  disabled={loading}
                  className="flex-1 h-12 font-bold text-[14px] border-2 border-[#111010] text-[#111010] bg-white hover:bg-[#F5F4F0] transition-colors disabled:opacity-60"
                >
                  Мимо
                </button>
                <button
                  id="rl-quiz-like"
                  data-testid="quiz-like"
                  onClick={() => answer('like')}
                  disabled={loading}
                  className="flex-1 h-12 font-bold text-[14px] border-2 border-[#111010] text-white bg-[#111010] hover:bg-[#333] transition-colors disabled:opacity-60"
                >
                  Берем
                </button>
              </div>
              {loading && <p className="text-[12px] text-[#6B6B6B] text-center">…</p>}
              {errorMsg && (
                <p className="text-[12px] text-red-600 text-center">{errorMsg}</p>
              )}
            </div>
          )}

          {step === 'done' && (
            <div id="rl-quiz-result" data-testid="quiz-result" className="flex flex-col gap-6 text-center">
              <div className="text-[40px]">✦</div>
              <div>
                <h2 className="font-black text-[20px] text-[#111010] mb-2">
                  {importing ? 'Сохраняем профиль…' : 'Лента настроена'}
                </h2>
                {!importing && (
                  <p className="text-[14px] text-[#6B6B6B]">
                    Теперь ты видишь % совместимости на каждом заказе
                  </p>
                )}
              </div>
              {!importing && (
                <div className="flex flex-col gap-3">
                  <button
                    data-testid="quiz-retake"
                    id="rl-quiz-retake-completed"
                    onClick={handleRetake}
                    className="h-12 px-6 font-black text-[13px] uppercase tracking-wider text-[#111010] bg-white border-2 border-[#111010]"
                  >
                    Пройти ещё раз
                  </button>
                  <button
                    onClick={onClose}
                    className="h-12 px-6 font-black text-[13px] uppercase tracking-wider text-white bg-[#111010] border-2 border-[#111010]"
                  >
                    Смотреть ленту →
                  </button>
                </div>
              )}
            </div>
          )}

          {step === 'error' && (
            <div className="flex flex-col gap-4">
              <p className="text-[14px] text-red-600">{errorMsg}</p>
              <button
                onClick={() => { setStep('intro'); setErrorMsg('') }}
                className="h-10 px-4 font-bold text-[12px] uppercase border-2 border-[#111010] text-[#111010]"
              >
                Попробовать снова
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
