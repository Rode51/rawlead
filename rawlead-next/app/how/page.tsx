'use client'

import { useRef, useEffect, useState } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import Header from '@/components/layout/Header'
import Footer from '@/components/layout/Footer'
import ScrollReveal from '@/components/ui/ScrollReveal'

const STEPS = [
  {
    num: '01',
    title: 'Проходишь квиз',
    body: 'Ответь на карточки заказов — RawLead узнает твой профиль. Не нужно вводить навыки вручную.',
    callout: null,
  },
  {
    num: '02',
    title: 'Настраивается профиль',
    body: 'Профиль хранит твои предпочтения. Лента автоматически подбирает заказы с % совпадения.',
    callout: 'ИИ запоминает, что тебе близко — профиль собирается на ходу. Первый профиль — из квиза. Дальше система смотрит, на что ты откликаешься, и уточняет % совпадения под твой реальный стек.',
  },
  {
    num: '03',
    title: 'Радар следит 24/7',
    body: 'Десятки источников проверяются автоматически. Дубликаты, спам и нерелевантные объявления не попадают в ленту.',
    callout: null,
  },
  {
    num: '04',
    title: 'ИИ читает суть заказа',
    body: 'Система понимает задачу и сверяет с твоим стеком — не по ключевым словам, а по смыслу.',
    callout: null,
  },
  {
    num: '05',
    title: 'Ты откликаешься сам',
    body: 'Черновик уже готов — для тебя написан отдельно, не скопирован с чужого. Поправь детали и отправь. Мы не пишем заказчикам за тебя.',
    callout: null,
  },
]

function StepCard({ step, index }: { step: typeof STEPS[0]; index: number }) {
  const [hovered, setHovered] = useState(false)

  return (
    <ScrollReveal delay={index * 0.07}>
      <div
        className={`group border-2 border-rl-inverse p-8 md:p-10 cursor-default transition-all duration-200 ${
          hovered ? 'bg-[#FACC15] shadow-neo-hover -translate-x-0.5 -translate-y-0.5' : 'bg-rl-page shadow-neo'
        }`}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
      >
        <div
          className="font-display font-black leading-none mb-6 tracking-[-0.04em] transition-colors duration-200"
          style={{ fontSize: 'clamp(40px, 5vw, 60px)', color: hovered ? '#111010' : '#FACC15' }}
        >
          {step.num}
        </div>
        <h2 className="font-display font-black text-rl-inverse text-xl mb-4 tracking-[-0.01em]">
          {step.title}
        </h2>
        <p className="font-sans text-rl-muted text-[15px] leading-relaxed transition-colors duration-200"
          style={{ color: hovered ? '#111010cc' : undefined }}
        >
          {step.body}
        </p>
        {step.callout && (
          <div
            className="mt-5 p-4 border-l-4 transition-colors duration-200"
            style={{
              borderLeftColor: hovered ? '#111010' : '#FACC15',
              background: hovered ? 'rgba(0,0,0,0.06)' : '#FFFBEB',
              color: hovered ? '#111010' : '#92400E',
            }}
          >
            <p className="font-sans text-[13px] leading-relaxed">{step.callout}</p>
          </div>
        )}
      </div>
    </ScrollReveal>
  )
}

export default function HowPage() {
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
              Как устроено
            </motion.p>
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ type: 'spring', stiffness: 260, damping: 26, delay: 0.07 }}
              className="font-display font-black text-white leading-[0.92] tracking-[-0.04em] mb-6"
              style={{ fontSize: 'clamp(36px, 6vw, 72px)' }}
            >
              Пять шагов<br />до твоего отклика
            </motion.h1>
            <motion.p
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ type: 'spring', stiffness: 260, damping: 26, delay: 0.16 }}
              className="font-sans text-white/50 max-w-xl"
              style={{ fontSize: '1.0625rem', lineHeight: 1.65 }}
            >
              От биржи до черновика отклика — без ручного мониторинга.
            </motion.p>
          </div>
        </section>

        {/* Steps — editorial list */}
        <section className="bg-rl-section border-b-2 border-rl-inverse py-20 md:py-28">
          <div className="mx-auto px-6" style={{ maxWidth: 800 }}>
            <div className="border-2 border-rl-inverse shadow-neo divide-y-2 divide-rl-inverse">
              {STEPS.map((step, i) => (
                <StepCard key={step.num} step={step} index={i} />
              ))}
            </div>
          </div>
        </section>

        {/* Spam protection — dark editorial */}
        <section className="bg-rl-inverse border-b-2 border-[#FACC15]/20 py-20 md:py-24">
          <div className="mx-auto px-6" style={{ maxWidth: 'var(--rl-container)' }}>
            <ScrollReveal>
              <div className="max-w-2xl">
                <span className="inline-block text-[10px] font-display font-black uppercase tracking-[0.2em] text-white/30 mb-6">
                  Защита от спама
                </span>
                <p
                  className="font-display font-black text-white leading-tight tracking-[-0.02em]"
                  style={{ fontSize: 'clamp(26px, 4vw, 44px)' }}
                >
                  Лимит — <span className="text-[#FACC15]">10 откликов в час.</span>
                  <br />Каждый отклик уникален.
                </p>
              </div>
            </ScrollReveal>
          </div>
        </section>

        {/* CTA */}
        <section className="bg-[#FACC15] border-b-2 border-rl-inverse py-20 md:py-24">
          <div className="mx-auto px-6 text-center" style={{ maxWidth: 'var(--rl-container)' }}>
            <ScrollReveal>
              <p className="font-display font-black text-rl-inverse text-[11px] uppercase tracking-[0.18em] mb-4">
                Premium · 790 ₽/мес
              </p>
              <p className="font-display font-black text-rl-inverse leading-tight tracking-[-0.03em] mb-10"
                style={{ fontSize: 'clamp(28px, 4vw, 48px)' }}
              >
                Начни бесплатно — 3 дня Trial при первом входе
              </p>
              <div className="flex gap-4 justify-center flex-wrap">
                <Link
                  href="/cabinet/"
                  className="inline-flex items-center h-12 px-8 bg-rl-inverse text-white font-display font-black text-[13px] uppercase tracking-[0.1em] border-2 border-rl-inverse shadow-neo hover:shadow-neo-hover hover:-translate-x-0.5 hover:-translate-y-0.5 transition-all duration-150"
                >
                  Войти в кабинет →
                </Link>
                <Link
                  href="/lenta/"
                  className="inline-flex items-center h-12 px-8 bg-transparent text-rl-inverse font-display font-black text-[13px] uppercase tracking-[0.1em] border-2 border-rl-inverse hover:bg-rl-inverse hover:text-white transition-all duration-150"
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
