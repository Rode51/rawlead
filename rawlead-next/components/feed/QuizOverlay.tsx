'use client'

import { useCallback, useEffect, useState } from 'react'
import { quizApi } from '@/lib/api'
import { useAuth } from '@/lib/auth-context'
import type { QuizCard, HistoryEntry } from '@/lib/types'
import type { QuizGuestProfile } from '@/lib/quiz-guest'
import { SOURCE_COLOR, SOURCE_LABEL } from '@/lib/utils'
import { notifyQuizComplete, normalizeQuizProfile, writeQuizCompleted } from '@/lib/quiz-guest'
import { metrikaGoal } from '@/lib/metrika'
import QuizCategoryBars from './QuizCategoryBars'

interface Props {
  onClose: () => void
  onLoginNeeded: () => void
}

type QuizStep = 'intro' | 'quiz' | 'done' | 'insufficient' | 'error'

export default function QuizOverlay({ onClose, onLoginNeeded }: Props) {
  const auth = useAuth()
  const [step, setStep] = useState<QuizStep>('intro')
  const [card, setCard] = useState<QuizCard | null>(null)
  const [history, setHistory] = useState<HistoryEntry[]>([])
  const [loading, setLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')
  const [importing, setImporting] = useState(false)
  const [completedProfile, setCompletedProfile] = useState<QuizGuestProfile | null>(null)

  const isAnon = auth.status !== 'auth'

  async function startQuiz() {
    setLoading(true)
    setErrorMsg('')
    metrikaGoal('quiz_start')
    try {
      const res = await quizApi.start()
      if (res.done && !res.profile) {
        setStep('insufficient')
      } else if (res.done || !res.card) {
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

  const finishQuiz = useCallback(async (profileRaw: QuizGuestProfile) => {
    const profile = normalizeQuizProfile(profileRaw) ?? profileRaw
    writeQuizCompleted(profile)
    setCompletedProfile(profile)
    notifyQuizComplete()

    if (auth.status === 'auth') {
      setImporting(true)
      try {
        await quizApi.importTags(profile.tags, profile.niches, profile.cx_pref ?? 1.0)
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
  }, [auth])

  async function answer(action: 'like' | 'skip') {
    if (!card || loading) return
    const newHistory: HistoryEntry[] = [...history, {
      card_id: card.id,
      liked: action === 'like',
      tags: card.tags ?? [],
      complexity: card.complexity,
    }]
    setHistory(newHistory)
    setLoading(true)
    try {
      const res = await quizApi.next(newHistory)
      if (res.done && res.profile) {
        await finishQuiz(res.profile)
      } else if (res.done && !res.profile) {
        setStep('insufficient')
      } else if (res.card) {
        setCard(res.card)
      } else {
        setStep('error')
        setErrorMsg('Не удалось загрузить следующую карточку')
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
    setCompletedProfile(null)
    void startQuiz()
  }

  function handleLoginCta() {
    onClose()
    onLoginNeeded()
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
                <h2 className="font-display font-black text-[22px] text-[#111010] leading-tight mb-2">
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
            <div
              id="rl-quiz-play"
              data-testid="quiz-play"
              className="rl-quiz-feed-card rl-quiz-card flex flex-col gap-3"
            >
              {card.source && (
                <div className="flex items-center gap-2">
                  <span
                    className="inline-flex items-center gap-[5px] text-[11px] font-bold uppercase tracking-wide px-2 py-[3px] leading-none"
                    style={{
                      color: SOURCE_COLOR[card.source] ?? '#6B6B6B',
                      background: (SOURCE_COLOR[card.source] ?? '#6B6B6B') + '15',
                      border: `1.5px solid ${(SOURCE_COLOR[card.source] ?? '#6B6B6B')}55`,
                    }}
                  >
                    <span
                      style={{ display: 'inline-block', width: 6, height: 6, borderRadius: '50%', background: SOURCE_COLOR[card.source] ?? '#6B6B6B' }}
                    />
                    {SOURCE_LABEL[card.source] ?? card.source}
                  </span>
                </div>
              )}

              <h3
                id="rl-quiz-card-title"
                className="font-display font-black text-[#111010] leading-snug"
                style={{ fontSize: '1.0625rem', letterSpacing: '-0.025em' }}
              >
                {card.title}
              </h3>

              {card.budget_text && (
                <p className="text-[15px] font-bold leading-none text-[#111010]">
                  {card.budget_text}
                </p>
              )}

              {card.body && (
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#525252] mb-1">
                    Суть задания
                  </p>
                  <p className="text-[14px] text-[#1A1918] leading-relaxed">{card.body}</p>
                </div>
              )}

              {card.tags.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {card.tags.map(tag => (
                    <span
                      key={tag}
                      className="text-[10px] font-semibold px-2 py-0.5 leading-snug"
                      style={{ background: '#EEEDEA', color: '#6B6B6B' }}
                    >
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

          {step === 'insufficient' && (
            <div id="rl-quiz-insufficient" data-testid="quiz-insufficient" className="flex flex-col gap-5">
              <div>
                <h2 className="font-display font-black text-[20px] text-[#111010] mb-2 leading-tight">
                  Слишком мало данных — ответь ещё на несколько карточек
                </h2>
                <p className="text-[14px] text-[#6B6B6B] leading-relaxed">
                  Нам нужно чуть больше сигналов, чтобы настроить ленту под твой профиль.
                </p>
              </div>
              <button
                type="button"
                data-testid="quiz-retry"
                onClick={() => void startQuiz()}
                disabled={loading}
                className="h-12 px-6 font-black text-[13px] uppercase tracking-wider text-white bg-[#111010] border-2 border-[#111010] hover:bg-[#333] transition-colors disabled:opacity-60"
              >
                {loading ? 'Загружаем…' : 'Попробовать ещё'}
              </button>
            </div>
          )}

          {step === 'done' && (
            <div id="rl-quiz-result" data-testid="quiz-result" className="flex flex-col gap-5">
              {isAnon ? (
                <>
                  <div>
                    <h2 className="font-display font-black text-[20px] text-[#111010] mb-2 leading-tight">
                      {completedProfile?.niches?.length
                        ? 'Готово. Вот что мы узнали:'
                        : 'Пока не нашли конкретного профиля — посмотри весь поток'}
                    </h2>
                    {completedProfile && completedProfile.niches?.length > 0 && (
                      <QuizCategoryBars profile={completedProfile} />
                    )}
                    <p className="text-[14px] text-[#525252] leading-relaxed mt-2">
                      Лента уже настраивается. Войди — сохраним профиль и откроем персональную ленту.
                    </p>
                  </div>

                  <button
                    type="button"
                    data-testid="quiz-login-cta"
                    onClick={handleLoginCta}
                    className="w-full flex items-center justify-center gap-2 h-12 px-4 font-bold text-[13px] text-[#111010] bg-[#FACC15] border-2 border-[#111010] hover:bg-[#FDE047] transition-colors"
                    style={{ boxShadow: '3px 3px 0 #111010' }}
                  >
                    <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
                      <path fill="currentColor" d="M9.04 15.314l-.376 5.302c.538 0 .77-.231 1.049-.508l2.518-2.418 5.217 3.823c.957.527 1.637.251 1.898-.885l3.438-16.08.001-.001c.305-1.423-.514-1.98-1.447-1.634L1.12 9.775c-1.392.541-1.369 1.317-.236 1.667l4.913 1.533L18.9 5.48c.595-.394 1.136-.176.691.218"/>
                    </svg>
                    3 дня Premium бесплатно — автоматически при входе
                  </button>

                  <div className="flex flex-col gap-3 items-center">
                    <button
                      type="button"
                      data-testid="quiz-retake"
                      id="rl-quiz-retake-completed"
                      onClick={handleRetake}
                      className="text-[13px] font-semibold text-[#6B6B6B] hover:text-[#111010] underline hover:no-underline"
                    >
                      Пройти ещё раз
                    </button>
                    <button
                      type="button"
                      onClick={onClose}
                      className="text-[13px] text-[#6B6B6B] hover:text-[#111010] underline hover:no-underline"
                    >
                      Смотреть без входа →
                    </button>
                  </div>
                </>
              ) : (
                <div className="flex flex-col gap-6 text-center">
                  <div className="text-[40px]">✦</div>
                  <div>
                    <h2 className="font-display font-black text-[20px] text-[#111010] mb-2">
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
