'use client'

import { useRef, useEffect, useState } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import Header from '@/components/layout/Header'
import Footer from '@/components/layout/Footer'
import ScrollReveal from '@/components/ui/ScrollReveal'

type FAQItem = { q: string; a: React.ReactNode }

const GROUPS: { title: string; items: FAQItem[] }[] = [
  {
    title: 'Начало',
    items: [
      {
        q: 'Как начать пользоваться?',
        a: <>Открой <Link href="/lenta/" className="underline text-rl-inverse">ленту заказов</Link> — регистрация не нужна. Пройди квиз — ИИ узнает твой профиль. Войди через Telegram в <Link href="/cabinet/" className="underline text-rl-inverse">кабинете</Link> — черновики и персональная лента.</>,
      },
      {
        q: 'Это автоматическая рассылка заказчикам?',
        a: 'Нет. RawLead только находит заказы и присылает тебе уведомление. Писать заказчикам — сам, в удобное время. Никакого автоспама.',
      },
      {
        q: 'Нужен ли мой основной аккаунт Telegram?',
        a: 'Да, авторизация происходит через официальный безопасный виджет Telegram. Сервер получает только твой публичный ID и юзернейм. RawLead не имеет доступа к личным перепискам, контактам или паролям — всё полностью безопасно.',
      },
    ],
  },
  {
    title: 'Как работает',
    items: [
      {
        q: 'Подходит ли для нетехнических специалистов?',
        a: 'Да. RawLead работает с четырьмя нишами: разработка, дизайн, маркетинг, тексты. Пройди квиз — ИИ узнает твой профиль и найдёт совпадения.',
      },
      {
        q: 'Как система подбирает заказы именно под меня?',
        a: 'Сначала — по профилю из квиза. Потом ИИ запоминает, на что ты откликаешься, и уточняет % совпадения под твой реальный стек. Лента становится точнее сама.',
      },
      {
        q: 'Какие источники поддерживаются?',
        a: 'FL.ru, Kwork, YouDo, Freelance.ru, FreelanceJob, Пчёл.нет, Telegram-каналы. База расширяется.',
      },
      {
        q: 'Не получу ли бан на бирже?',
        a: 'Нет. Отклики пишешь ты — своими словами, в своё время. RawLead только подбирает заказы и черновик. Автоспама с твоего аккаунта нет.',
      },
      {
        q: 'Почему лимит 10 откликов в час?',
        a: <>Чтобы защитить твой аккаунт от спам-фильтров бирж: не более <strong>10 откликов в час (включая Premium)</strong>. Это сохраняет качество и не даёт предложениям теряться в спаме.</>,
      },
      {
        q: 'Что такое % совпадения?',
        a: 'Это насколько заказ подходит под твой профиль из квиза. 90%+ — отлично совпадает. Алгоритм учитывает категорию, навыки и тип задачи. Не рейтинг среди других фрилансеров — только твой личный match.',
      },
    ],
  },
  {
    title: 'Premium',
    items: [
      {
        q: 'Сервис платный?',
        a: <>Лента открыта бесплатно — с задержкой <strong>30 мин</strong>. Для Trial и Premium (<strong>790 ₽/мес</strong>) — без задержки, персональная лента, черновики, push. <Link href="/pricing/" className="underline text-rl-inverse">Тарифы →</Link></>,
      },
      {
        q: 'Есть пробный период?',
        a: <>Да — <strong>бесплатно, автоматически при входе</strong> · 3 дня Premium (1× на аккаунт TG). Далее — <strong>790 ₽/мес</strong>. <Link href="/pricing/" className="underline text-rl-inverse">Тарифы →</Link></>,
      },
      {
        q: 'Есть ли автопродление?',
        a: 'Нет. После Trial — лента без персонализации. Продлить Premium — вручную.',
      },
      {
        q: 'Зачем Premium, если лента и так без задержки после входа?',
        a: 'После первого входа — 3 дня Trial бесплатно: персональная лента, черновики, push. После Trial — лента с задержкой 30 мин и без персонализации. Premium возвращает всё за 790 ₽/мес.',
      },
    ],
  },
]

function FaqItem({ item, groupIndex, itemIndex }: { item: FAQItem; groupIndex: number; itemIndex: number }) {
  const [open, setOpen] = useState(false)
  const bodyRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = bodyRef.current
    if (!el) return
    el.style.maxHeight = open ? el.scrollHeight + 24 + 'px' : '0px'
  }, [open])

  return (
    <div className="border-b border-rl-inverse/10 last:border-b-0">
      <button
        type="button"
        onClick={() => setOpen(v => !v)}
        data-testid={`faq-item-${groupIndex}-${itemIndex}`}
        className="w-full text-left flex items-start justify-between gap-6 py-5 group"
        style={{ background: 'none', border: 'none', cursor: 'pointer' }}
      >
        <span className="font-display font-black text-rl-inverse leading-snug tracking-[-0.02em] group-hover:text-[#111010]" style={{ fontSize: '0.9375rem' }}>
          {item.q}
        </span>
        <span
          className="flex-shrink-0 w-6 h-6 border-2 border-rl-inverse flex items-center justify-center transition-all duration-200"
          style={{
            background: open ? '#FACC15' : 'transparent',
            transform: open ? 'rotate(45deg)' : 'rotate(0deg)',
          }}
          aria-hidden="true"
        >
          <span className="font-display font-black text-rl-inverse leading-none" style={{ fontSize: '0.875rem', marginTop: '-1px' }}>+</span>
        </span>
      </button>
      <div
        ref={bodyRef}
        data-testid={`faq-answer-${groupIndex}-${itemIndex}`}
        style={{ maxHeight: 0, overflow: 'hidden', transition: 'max-height 300ms cubic-bezier(0.22, 1, 0.36, 1)' }}
      >
        <p className="font-sans pb-5 leading-relaxed" style={{ fontSize: '0.9rem', color: '#525252' }}>
          {item.a}
        </p>
      </div>
    </div>
  )
}

function FaqGroup({ group, index, startOpen }: { group: typeof GROUPS[0]; index: number; startOpen: boolean }) {
  const [open, setOpen] = useState(startOpen)
  const bodyRef = useRef<HTMLDivElement>(null)
  const [initialized, setInitialized] = useState(false)

  useEffect(() => {
    const el = bodyRef.current
    if (!el) return
    if (!initialized) {
      el.style.maxHeight = open ? 'none' : '0px'
      setInitialized(true)
      return
    }
    el.style.maxHeight = open ? el.scrollHeight + 48 + 'px' : '0px'
  }, [open])

  return (
    <ScrollReveal delay={index * 0.08}>
      <div className="border-2 border-rl-inverse shadow-neo mb-4">
        <button
          type="button"
          onClick={() => setOpen(v => !v)}
          className="w-full flex items-center justify-between gap-4 px-7 py-5 transition-colors duration-200 group"
          style={{
            background: open ? '#111010' : 'transparent',
            border: 'none',
            cursor: 'pointer',
            borderBottom: open ? '2px solid #111010' : 'none',
          }}
        >
          <span
            className="font-display font-black uppercase tracking-[0.12em] transition-colors duration-200"
            style={{ fontSize: '0.8125rem', color: open ? '#FACC15' : '#111010' }}
          >
            {group.title}
          </span>
          <span
            className="font-display font-black transition-all duration-200"
            style={{ color: open ? '#FACC15' : '#6B6B6B', fontSize: '0.75rem' }}
            aria-hidden="true"
          >
            {open ? '▲' : '▼'}
          </span>
        </button>
        <div
          ref={bodyRef}
          style={{ maxHeight: startOpen ? 'none' : '0px', overflow: 'hidden', transition: 'max-height 320ms cubic-bezier(0.22, 1, 0.36, 1)' }}
        >
          <div className="px-7 pt-2 pb-2">
            {group.items.map((item, i) => (
              <FaqItem key={i} item={item} groupIndex={index} itemIndex={i} />
            ))}
          </div>
        </div>
      </div>
    </ScrollReveal>
  )
}

export default function FaqPage() {
  return (
    <>
      <Header />
      <main>
        {/* Hero */}
        <section className="bg-rl-inverse border-b-2 border-rl-inverse">
          <div className="mx-auto px-6 py-20 md:py-28" style={{ maxWidth: 'var(--rl-container)' }}>
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.4 }}
              className="text-[11px] font-display font-black uppercase tracking-[0.2em] text-white/30 mb-6"
            >
              FAQ
            </motion.p>
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ type: 'spring', stiffness: 260, damping: 26, delay: 0.07 }}
              className="font-display font-black text-white leading-[0.92] tracking-[-0.04em] mb-6"
              style={{ fontSize: 'clamp(36px, 6vw, 72px)' }}
            >
              Частые вопросы
            </motion.h1>
            <motion.p
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ type: 'spring', stiffness: 260, damping: 26, delay: 0.16 }}
              className="font-sans text-white/50 max-w-xl"
              style={{ fontSize: '1.0625rem', lineHeight: 1.65 }}
            >
              Коротко о RawLead для любой ниши фриланса
            </motion.p>
          </div>
        </section>

        {/* FAQ content */}
        <section className="bg-rl-section py-20 md:py-28 border-b-2 border-rl-inverse">
          <div className="mx-auto px-6" style={{ maxWidth: 720 }}>
            {GROUPS.map((group, i) => (
              <FaqGroup key={i} group={group} index={i} startOpen={i === 0} />
            ))}
          </div>
        </section>

        {/* CTA */}
        <section className="bg-rl-page border-b-2 border-rl-inverse py-20 md:py-24">
          <div className="mx-auto px-6 text-center" style={{ maxWidth: 'var(--rl-container)' }}>
            <ScrollReveal>
              <p className="font-display font-black text-rl-inverse leading-tight tracking-[-0.03em] mb-8"
                style={{ fontSize: 'clamp(24px, 3.5vw, 40px)' }}
              >
                Остались вопросы — напиши напрямую
              </p>
              <div className="flex gap-4 justify-center flex-wrap">
                <Link
                  href="/contact/"
                  className="inline-flex items-center h-12 px-8 bg-rl-inverse text-white font-display font-black text-[13px] uppercase tracking-[0.1em] border-2 border-rl-inverse shadow-neo hover:shadow-neo-hover hover:-translate-x-0.5 hover:-translate-y-0.5 transition-all duration-150"
                >
                  Написать →
                </Link>
                <Link
                  href="/lenta/"
                  className="inline-flex items-center h-12 px-8 bg-transparent text-rl-inverse font-display font-black text-[13px] uppercase tracking-[0.1em] border-2 border-rl-inverse hover:bg-[#FACC15] transition-all duration-150"
                >
                  Смотреть ленту
                </Link>
              </div>
            </ScrollReveal>
          </div>
        </section>
      </main>
      <Footer />
    </>
  )
}
