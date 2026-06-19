'use client'

import { motion } from 'framer-motion'
import ScrollReveal from '@/components/ui/ScrollReveal'

const SOURCES = [
  { label: 'FL.ru',    color: '#00A65A', count: '312 заказов' },
  { label: 'Kwork',    color: '#EA580C', count: '198 заказов' },
  { label: 'YouDo',    color: '#2563EB', count: '87 заказов'  },
  { label: 'Telegram', color: '#0088CC', count: '203 заказа'  },
  { label: 'HH',       color: '#D7001B', count: '47 заказов'  },
]

const OUTPUT_CARDS = [
  { source: 'FL.ru', color: '#00A65A', title: 'Сайт на WordPress + WooCommerce', match: 89, budget: 'от 25 000 ₽' },
  { source: 'Tg',    color: '#0088CC', title: 'Figma — landing для SaaS', match: 91, budget: 'от 15 000 ₽' },
  { source: 'Kwork', color: '#EA580C', title: 'Python-парсер с экспортом в GS', match: 74, budget: 'до 8 000 ₽' },
]

function PulseRing({ delay = 0 }: { delay?: number }) {
  return (
    <motion.div
      className="absolute inset-0 rounded-sm border-2 border-[#111010]"
      initial={{ opacity: 0.6, scale: 1 }}
      animate={{ opacity: 0, scale: 1.7 }}
      transition={{
        duration: 2.2,
        delay,
        repeat: Infinity,
        ease: 'easeOut',
      }}
    />
  )
}

export default function HowItWorks() {
  return (
    <section id="flow" className="py-24 md:py-32 bg-rl-page border-b-2 border-rl-inverse overflow-hidden">
      <div className="mx-auto px-6" style={{ maxWidth: 'var(--rl-container)' }}>

        {/* Header */}
        <ScrollReveal className="mb-16 max-w-2xl">
          <p className="text-[11px] font-display font-black uppercase tracking-[0.2em] text-rl-muted mb-4">
            Как устроено
          </p>
          <h2
            className="font-display font-black text-rl-inverse leading-[0.95] tracking-[-0.03em]"
            style={{ fontSize: 'clamp(32px, 5vw, 56px)' }}
          >
            Один поток вместо десяти вкладок
          </h2>
        </ScrollReveal>

        {/* Animation layout */}
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_auto_1fr] gap-8 lg:gap-6 items-center">

          {/* LEFT — Sources */}
          <div className="flex flex-col gap-3">
            {SOURCES.map((src, i) => (
              <motion.div
                key={src.label}
                initial={{ opacity: 0, x: -48 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true, margin: '-60px' }}
                transition={{ type: 'spring', stiffness: 280, damping: 26, delay: i * 0.09 }}
                className="flex items-center justify-between px-4 py-3 border-2 bg-rl-page shadow-[3px_3px_0_#111010] group"
                style={{ borderColor: src.color }}
              >
                <span
                  className="font-display font-black text-xs uppercase tracking-[0.1em]"
                  style={{ color: src.color }}
                >
                  {src.label}
                </span>
                <span className="font-sans text-[11px] text-rl-muted">
                  {src.count}
                </span>
              </motion.div>
            ))}

            {/* Connector line desktop */}
            <motion.div
              className="hidden lg:block absolute right-0 top-1/2"
              initial={{ scaleX: 0 }}
              whileInView={{ scaleX: 1 }}
              viewport={{ once: true }}
              transition={{ delay: 0.5, duration: 0.4 }}
            />
          </div>

          {/* CENTER — RawLead processor */}
          <div className="flex flex-col items-center gap-6">
            {/* Connector from left */}
            <motion.div
              initial={{ scaleX: 0, opacity: 0 }}
              whileInView={{ scaleX: 1, opacity: 1 }}
              viewport={{ once: true, margin: '-60px' }}
              transition={{ delay: 0.55, duration: 0.35 }}
              className="hidden lg:block h-0.5 w-16 bg-rl-inverse origin-left"
            />

            {/* Processor chip */}
            <ScrollReveal delay={0.6} className="relative flex items-center justify-center">
              <PulseRing delay={0} />
              <PulseRing delay={1.1} />
              <div className="relative z-10 px-8 py-6 bg-[#FACC15] border-2 border-rl-inverse shadow-neo text-center min-w-[160px]">
                <div className="font-display font-black text-rl-inverse text-xl uppercase tracking-[0.06em] mb-1">
                  RawLead
                </div>
                <div className="font-sans text-[11px] text-rl-inverse/60 uppercase tracking-[0.1em]">
                  AI · фильтр · скоринг
                </div>
                {/* Processing dots */}
                <div className="flex justify-center gap-1.5 mt-3">
                  {[0, 0.2, 0.4].map((d, i) => (
                    <motion.span
                      key={i}
                      className="w-1.5 h-1.5 rounded-full bg-rl-inverse/50"
                      animate={{ opacity: [0.3, 1, 0.3] }}
                      transition={{ duration: 1.2, repeat: Infinity, delay: d }}
                    />
                  ))}
                </div>
              </div>
            </ScrollReveal>

            {/* Connector to right */}
            <motion.div
              initial={{ scaleX: 0, opacity: 0 }}
              whileInView={{ scaleX: 1, opacity: 1 }}
              viewport={{ once: true, margin: '-60px' }}
              transition={{ delay: 0.75, duration: 0.35 }}
              className="hidden lg:block h-0.5 w-16 bg-rl-inverse origin-left"
            />
          </div>

          {/* RIGHT — Output cards */}
          <div className="flex flex-col gap-3">
            {OUTPUT_CARDS.map((card, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: 48 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true, margin: '-60px' }}
                transition={{ type: 'spring', stiffness: 260, damping: 24, delay: 0.8 + i * 0.11 }}
                className="bg-rl-page border-2 border-rl-inverse shadow-[3px_3px_0_#111010] p-4"
              >
                <div className="flex items-center justify-between mb-2">
                  <span
                    className="text-[10px] font-display font-black uppercase tracking-[0.1em] px-2 py-0.5 border-2"
                    style={{ color: card.color, borderColor: card.color }}
                  >
                    {card.source}
                  </span>
                  <span className="text-[11px] font-display font-black text-rl-inverse">{card.budget}</span>
                </div>
                <p className="font-display font-black text-[13px] text-rl-inverse leading-snug line-clamp-2 mb-3">
                  {card.title}
                </p>
                {/* Match bar */}
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-[3px] bg-rl-section overflow-hidden">
                    <motion.div
                      className="h-full bg-rl-inverse"
                      initial={{ width: 0 }}
                      whileInView={{ width: `${card.match}%` }}
                      viewport={{ once: true }}
                      transition={{ type: 'spring', stiffness: 120, damping: 20, delay: 1.0 + i * 0.1 }}
                    />
                  </div>
                  <span className="text-[11px] font-display font-black text-rl-inverse shrink-0">{card.match}%</span>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Caption */}
        <ScrollReveal delay={0.2} className="mt-16 text-center">
          <p className="font-sans text-rl-muted text-base md:text-lg">
            Меньше вкладок, больше откликов.
          </p>
        </ScrollReveal>
      </div>
    </section>
  )
}
