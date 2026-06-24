'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import Link from 'next/link'
import { useAuth } from '@/lib/auth-context'
import { hasAnonQuizCompleted } from '@/lib/quiz-guest'

const EXPO_OUT: [number, number, number, number] = [0.16, 1, 0.3, 1]

const LINES = ['Стоп мониторить', 'вручную.']

const CTA_CLASS =
  'inline-flex items-center justify-center gap-2 h-12 px-7 bg-[#111010] text-white font-display font-black text-sm uppercase tracking-[0.08em] border-2 border-[#111010] shadow-[4px_4px_0_#111010] hover:shadow-[7px_7px_0_#111010] hover:-translate-x-0.5 hover:-translate-y-0.5 transition-all duration-150'

export default function Hero() {
  const auth = useAuth()
  const [quizDone, setQuizDone] = useState(() => hasAnonQuizCompleted())

  useEffect(() => {
    const sync = () => setQuizDone(hasAnonQuizCompleted())
    sync()
    window.addEventListener('rawlead-quiz-complete', sync)
    window.addEventListener('rawlead-tags-imported', sync)
    return () => {
      window.removeEventListener('rawlead-quiz-complete', sync)
      window.removeEventListener('rawlead-tags-imported', sync)
    }
  }, [])

  const showFeedCta =
    auth.status === 'auth' && (auth.hasUserSkills || quizDone)

  return (
    <section className="relative overflow-hidden bg-[#FACC15] min-h-[100svh] flex flex-col justify-center py-16 sm:py-20">

      {/* Декоративная сетка */}
      <div
        aria-hidden
        className="absolute inset-0 pointer-events-none opacity-[0.06]"
        style={{
          backgroundImage:
            'linear-gradient(#111010 1px, transparent 1px), linear-gradient(90deg, #111010 1px, transparent 1px)',
          backgroundSize: '40px 40px',
        }}
      />

      {/* Основной контент */}
      <div
        className="relative mx-auto px-6 w-full flex-1 flex flex-col justify-center"
        style={{ maxWidth: 'var(--rl-container)' }}
      >
        {/* Eyebrow */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.05, ease: EXPO_OUT }}
          className="mb-8 flex items-center gap-2.5"
        >
          <span className="w-2.5 h-2.5 rounded-full bg-[#111010]" />
          <span className="text-[11px] font-display font-black uppercase tracking-[0.2em] text-[#111010]">
            Радар онлайн
          </span>
        </motion.div>

        {/* H1 — curtain reveal по строкам */}
        <h1
          className="font-display font-black text-[#111010] leading-[0.9] tracking-[-0.03em] mb-10"
          style={{ fontSize: 'clamp(56px, 9vw, 104px)' }}
        >
          {LINES.map((line, i) => (
            <span key={i} className="block overflow-hidden">
              <motion.span
                className="block"
                initial={{ y: '110%' }}
                animate={{ y: '0%' }}
                transition={{
                  duration: 0.75,
                  delay: 0.25 + i * 0.14,
                  ease: EXPO_OUT,
                }}
              >
                {line}
              </motion.span>
            </span>
          ))}
        </h1>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, delay: 0.63, ease: EXPO_OUT }}
          className="font-sans text-[#1A1918] text-lg sm:text-xl leading-[1.6] max-w-[36rem] mb-10 font-medium"
        >
          Все биржи — в одной ленте. ИИ фильтрует по твоему стеку и пишет черновик отклика.
        </motion.p>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.79, ease: EXPO_OUT }}
          className="flex flex-wrap items-start gap-4"
        >
          <div className="inline-flex flex-col items-stretch gap-2">
            {auth.status === 'pending' ? (
              <div className="h-12" />
            ) : showFeedCta ? (
              <Link
                href="/lenta/"
                data-testid="hero-cta-lenta"
                className={CTA_CLASS}
              >
                Смотреть ленту →
              </Link>
            ) : (
              <>
                <Link
                  href="/lenta/#quiz"
                  data-testid="hero-cta-quiz"
                  className={CTA_CLASS}
                >
                  Подобрать заказы →
                </Link>
                <span className="inline-flex items-center justify-center h-9 px-5 bg-white border-2 border-[#111010] font-display font-black text-[10px] uppercase tracking-[0.1em] text-[#111010] shadow-[2px_2px_0_#111010] whitespace-nowrap">
                  3 дня бесплатно · без карты
                </span>
              </>
            )}
          </div>
        </motion.div>
      </div>
    </section>
  )
}
