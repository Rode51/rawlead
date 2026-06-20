'use client'

import { useCallback, useEffect, useState } from 'react'
import Link from 'next/link'
import { feedApi } from '@/lib/api'
import { useAuth } from '@/lib/auth-context'
import { useAuthModal } from '@/lib/auth-modal-context'
import type { LeadItem } from '@/lib/types'

const MOCK_LEADS: LeadItem[] = [
  { id: 1, source: 'fl', title: 'Разработка Telegram-бота для записи клиентов', body: '', task_summary: 'Бот принимает заявки, отправляет напоминания, интегрируется с Google Sheets. Python + aiogram.', url: 'https://fl.ru', budget_text: '25 000 – 40 000 ₽', ai_score: 91, keyword_match: 88, final_rank: 88, category: 'dev', lead_tags: ['telegram_bot_dev', 'python', 'aiogram'], lead_tag_labels: {}, tools_required: ['python', 'aiogram'], difficulty: '2', tz_attachment: null, created_at: new Date(Date.now() - 18 * 60000).toISOString(), is_hot: true, display_views: 34, display_replies: 4, reply_draft: '' },
  { id: 2, source: 'kwork', title: 'Дизайн лендинга для онлайн-школы по английскому', body: '', task_summary: 'Лендинг под платный курс. Нужен Figma-макет и адаптив. Стиль — минималистичный, современный.', url: 'https://kwork.ru', budget_text: 'до 15 000 ₽', ai_score: 73, keyword_match: null, final_rank: 73, category: 'design', lead_tags: ['ui_ux', 'figma', 'logo_design'], lead_tag_labels: {}, tools_required: ['figma'], difficulty: '1', tz_attachment: null, created_at: new Date(Date.now() - 45 * 60000).toISOString(), is_hot: false, display_views: 12, display_replies: 1, reply_draft: '' },
  { id: 3, source: 'tg', title: 'Парсер маркетплейсов (Wildberries + Ozon) с выгрузкой в Excel', body: '', task_summary: 'Сбор данных по ключевым словам: цены, рейтинг, кол-во отзывов. Нужен планировщик и уведомления при изменении.', url: 'https://t.me', budget_text: '8 000 – 12 000 ₽', ai_score: 85, keyword_match: 92, final_rank: 92, category: 'dev', lead_tags: ['web_scraping', 'python', 'api_integration'], lead_tag_labels: {}, tools_required: ['python'], difficulty: '2', tz_attachment: null, created_at: new Date(Date.now() - 2 * 3600000).toISOString(), is_hot: false, display_views: 67, display_replies: 8, reply_draft: '' },
  { id: 4, source: 'youdo', title: 'SEO-оптимизация интернет-магазина на Bitrix', body: '', task_summary: 'Аудит, семантика, внутренняя оптимизация, настройка мета-тегов. Отчёт в конце.', url: 'https://youdo.ru', budget_text: 'Договорная', ai_score: 61, keyword_match: null, final_rank: 61, category: 'marketing', lead_tags: ['seo', 'seo_copywriting'], lead_tag_labels: {}, tools_required: [], difficulty: '3', tz_attachment: null, created_at: new Date(Date.now() - 4 * 3600000).toISOString(), is_hot: false, display_views: 29, display_replies: 2, reply_draft: '' },
  { id: 5, source: 'fl', title: 'FastAPI бэкенд для мобильного приложения (iOS + Android)', body: '', task_summary: 'REST API с авторизацией JWT, загрузкой файлов, push-уведомлениями. Документация Swagger.', url: 'https://fl.ru', budget_text: '60 000 – 90 000 ₽', ai_score: 94, keyword_match: 100, final_rank: 100, category: 'dev', lead_tags: ['api_integration', 'python', 'llm_integration'], lead_tag_labels: {}, tools_required: ['python', 'fastapi'], difficulty: '3', tz_attachment: null, created_at: new Date(Date.now() - 7 * 3600000).toISOString(), is_hot: true, display_views: 103, display_replies: 14, reply_draft: '' },
  { id: 6, source: 'kwork', title: 'Тексты для 5 карточек товаров на Ozon', body: '', task_summary: 'Продающие описания с ключами для алгоритма Ozon. Товары — умные гаджеты для дома.', url: 'https://kwork.ru', budget_text: '3 000 ₽', ai_score: 55, keyword_match: null, final_rank: 55, category: 'text', lead_tags: ['copywriting', 'seo_copywriting'], lead_tag_labels: {}, tools_required: [], difficulty: '1', tz_attachment: null, created_at: new Date(Date.now() - 10 * 3600000).toISOString(), is_hot: false, display_views: 8, display_replies: 3, reply_draft: '' },
]

import Header from '@/components/layout/Header'
import Footer from '@/components/layout/Footer'
import FilterBar from '@/components/feed/FilterBar'
import AnonStrip from '@/components/feed/AnonStrip'
import FeedCard from '@/components/feed/FeedCard'
import QuizOverlay from '@/components/feed/QuizOverlay'
import QuizPromoCard from '@/components/feed/QuizPromoCard'
import { hasAnonQuizCompleted } from '@/lib/quiz-guest'

function openQuiz(setShowQuiz: (v: boolean) => void) {
  setShowQuiz(true)
  if (typeof window !== 'undefined') {
    const base = window.location.pathname + window.location.search
    window.history.replaceState(null, '', `${base}#quiz`)
  }
}

function closeQuiz(setShowQuiz: (v: boolean) => void) {
  setShowQuiz(false)
  if (typeof window !== 'undefined' && window.location.hash === '#quiz') {
    const base = window.location.pathname + window.location.search
    window.history.replaceState(null, '', base)
  }
}

const LIMIT = 20
const FETCH_TIMEOUT_MS = 5000

function withTimeout<T>(promise: Promise<T>, ms: number): Promise<T> {
  return Promise.race([
    promise,
    new Promise<T>((_, reject) =>
      setTimeout(() => reject(new Error('fetch timeout')), ms)
    ),
  ])
}

function CardSkeleton() {
  return (
    <div
      className="bg-[#F5F4F0] animate-pulse"
      style={{ height: 140, borderRadius: 4, boxShadow: '4px 4px 0 #D4D4D0' }}
    />
  )
}

export default function LentaPage() {
  const auth = useAuth()
  const { openLogin } = useAuthModal()

  const [items, setItems] = useState<LeadItem[]>([])
  const [offset, setOffset] = useState(0)
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [done, setDone] = useState(false)
  const [category, setCategory] = useState('')
  const [source, setSource] = useState('')
  const [sort, setSort] = useState<'time' | 'match'>('time')
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const [showQuiz, setShowQuiz] = useState(false)
  const [anonQuizDone, setAnonQuizDone] = useState(false)
  const loadFeed = useCallback(async (reset: boolean, currentOffset: number) => {
    const isReset = reset
    if (isReset) {
      setLoading(true)
      setError(null)
      setDone(false)
    } else {
      setLoadingMore(true)
    }

    try {
      const params: Parameters<typeof feedApi.list>[0] = {
        offset: isReset ? 0 : currentOffset,
        limit: LIMIT,
        sort,
      }
      if (category) params.category = category
      if (source) params.source = source

      const data = await withTimeout(feedApi.list(params), FETCH_TIMEOUT_MS)

      if (isReset) {
        setItems(data.items)
        setOffset(data.items.length)
        setTotal(data.count)
        setExpandedId(null)
      } else {
        setItems(prev => [...prev, ...data.items])
        setOffset(prev => prev + data.items.length)
      }

      if (data.items.length < LIMIT) setDone(true)
    } catch {
      if (isReset) {
        const isDevHost =
          typeof window !== 'undefined' &&
          (window.location.hostname === 'localhost' ||
            window.location.hostname === '127.0.0.1')
        if (isDevHost) {
          let filtered = MOCK_LEADS
          if (category) filtered = filtered.filter(l => l.category === category)
          if (source) filtered = filtered.filter(l => l.source === source)
          setItems(filtered)
          setOffset(filtered.length)
          setTotal(filtered.length)
          setDone(true)
          setExpandedId(null)
        } else {
          setError('Не удалось загрузить ленту. Обновите страницу или зайдите позже.')
          setItems([])
          setOffset(0)
          setTotal(0)
          setDone(true)
          setExpandedId(null)
        }
      }
    } finally {
      setLoading(false)
      setLoadingMore(false)
    }
  }, [category, source, sort])

  // Load feed on mount and when auth/filters change.
  // auth.status 'pending' is treated as 'anon' in feedTier — no blocking wait.
  useEffect(() => {
    loadFeed(true, 0)
  }, [auth.status, category, source, sort, loadFeed])

  useEffect(() => {
    setAnonQuizDone(hasAnonQuizCompleted())
    function onQuizComplete() {
      setAnonQuizDone(true)
    }
    window.addEventListener('rawlead-quiz-complete', onQuizComplete)
    return () => window.removeEventListener('rawlead-quiz-complete', onQuizComplete)
  }, [])

  useEffect(() => {
    function syncQuizFromHash() {
      if (typeof window !== 'undefined' && window.location.hash === '#quiz') {
        setShowQuiz(true)
      }
    }
    syncQuizFromHash()
    window.addEventListener('hashchange', syncQuizFromHash)
    return () => window.removeEventListener('hashchange', syncQuizFromHash)
  }, [])

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const focusRaw = params.get('lead') || params.get('id') || ''
    const focusId = parseInt(focusRaw, 10)
    if (focusId > 0) {
      setExpandedId(focusId)
      window.setTimeout(() => {
        const card = document.querySelector(`.rl-lead-card[data-id="${focusId}"]`)
        if (card instanceof HTMLElement) {
          card.scrollIntoView({ behavior: 'smooth', block: 'center' })
          card.classList.add('rl-lead-card--push-focus')
          window.setTimeout(() => card.classList.remove('rl-lead-card--push-focus'), 2800)
        }
      }, 400)
    }
  }, [])

  function handleToggle(id: number) {
    setExpandedId(prev => (prev === id ? null : id))
  }

  function handleLoadMore() {
    loadFeed(false, offset)
  }

  function handleCategoryChange(cat: string) { setCategory(cat) }
  function handleSourceChange(src: string) { setSource(src) }
  function handleSortChange(s: 'time' | 'match') { setSort(s) }

  return (
    <>
      <Header />
      <FilterBar
        category={category}
        source={source}
        sort={sort}
        feedTier={auth.feedTier}
        onCategoryChange={handleCategoryChange}
        onSourceChange={handleSourceChange}
        onSortChange={handleSortChange}
      />

      {auth.feedTier === 'anon' && !loading && (
        <AnonStrip onLoginClick={openLogin} quizCompleted={anonQuizDone} />
      )}

      <main
        data-rl-app="feed"
        data-testid="feed-app"
        data-feed-tier={auth.feedTier}
        className="min-h-screen py-8 pb-16"
      >
        <div className="max-w-feed mx-auto px-4 sm:px-6">
          {/* Header row */}
          <div className="flex items-baseline justify-between gap-4 mb-6">
            <h1 className="font-black text-[#111010] text-[28px] md:text-[32px] tracking-[-0.02em]">
              Лента заказов
            </h1>
            <div className="shrink-0">
              <Link
                id="rl-feed-cabinet-link"
                href="/cabinet/"
                data-testid="feed-cabinet-link"
                className="text-[12px] font-bold text-[#6B6B6B] hover:text-[#111010] underline hover:no-underline transition-colors"
              >
                {auth.status === 'auth' ? 'Кабинет →' : 'Войти в кабинет →'}
              </Link>
            </div>
          </div>

          {/* Error state */}
          {error && (
            <div className="mb-6 p-4 border-2 border-red-500 text-red-600 text-[13px]">
              {error}{' '}
              <button onClick={() => loadFeed(true, 0)} className="underline font-semibold">
                Попробовать снова
              </button>
            </div>
          )}

          {/* Feed grid */}
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[1, 2, 3, 4].map(i => <CardSkeleton key={i} />)}
            </div>
          ) : items.length === 0 ? (
            <div className="py-16 text-center">
              <p className="text-[#6B6B6B] text-[15px]">Пока нет заказов в этой категории</p>
            </div>
          ) : (
            <div id="rl-feed-list" data-testid="feed-list" className="grid grid-cols-1 md:grid-cols-2 gap-4 items-start">
              {auth.feedTier === 'anon' && (
                <QuizPromoCard
                  quizCompleted={anonQuizDone}
                  onQuizClick={() => openQuiz(setShowQuiz)}
                  onLoginClick={openLogin}
                />
              )}
              {items.map((item, idx) => (
                <FeedCard
                  key={item.id}
                  item={item}
                  feedTier={auth.feedTier}
                  hasUserSkills={auth.hasUserSkills}
                  isExpanded={expandedId === item.id}
                  onToggle={() => handleToggle(item.id)}
                  onQuizClick={() => openQuiz(setShowQuiz)}
                  onLoginClick={openLogin}
                  anonQuizDone={anonQuizDone}
                  index={idx}
                />
              ))}
            </div>
          )}

          {/* Load more */}
          {!loading && items.length > 0 && (
            <div className="mt-8 text-center">
              {done ? (
                <p className="text-[13px] text-[#6B6B6B]">Все заказы показаны</p>
              ) : (
                <div className="flex flex-col items-center gap-2">
                  <button
                    onClick={handleLoadMore}
                    disabled={loadingMore}
                    data-testid="feed-load-more"
                    className="h-11 px-8 font-bold text-[13px] uppercase tracking-wider border-2 border-[#111010] text-[#111010] bg-white hover:bg-[#F5F4F0] disabled:opacity-60 transition-colors"
                    style={{ boxShadow: '3px 3px 0 #111010' }}
                  >
                    {loadingMore ? 'Загружаем…' : 'Показать ещё'}
                  </button>
                  <span className="text-[12px] text-[#6B6B6B]">
                    Показано {items.length} из {total}
                  </span>
                </div>
              )}
            </div>
          )}
        </div>
      </main>

      <Footer />

      {showQuiz && (
        <QuizOverlay
          onClose={() => closeQuiz(setShowQuiz)}
          onLoginNeeded={() => { closeQuiz(setShowQuiz); openLogin() }}
        />
      )}
    </>
  )
}
