'use client'

import { motion } from 'framer-motion'
import Header from '@/components/layout/Header'
import Footer from '@/components/layout/Footer'
import ScrollReveal from '@/components/ui/ScrollReveal'

export default function ContactPage() {
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
              Контакт
            </motion.p>
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ type: 'spring', stiffness: 260, damping: 26, delay: 0.07 }}
              className="font-display font-black text-white leading-[0.92] tracking-[-0.04em]"
              style={{ fontSize: 'clamp(36px, 6vw, 72px)' }}
            >
              Написать напрямую
            </motion.h1>
          </div>
        </section>

        {/* Contact card */}
        <section className="bg-rl-section border-b-2 border-rl-inverse py-20 md:py-28">
          <div className="mx-auto px-6" style={{ maxWidth: 'var(--rl-container)' }}>
            <ScrollReveal>
              <div className="max-w-lg">
                <div className="border-2 border-rl-inverse bg-rl-page shadow-neo p-8 md:p-12">
                  <p className="text-[11px] font-display font-black uppercase tracking-[0.18em] text-rl-muted mb-6">
                    Telegram
                  </p>
                  <p className="font-display font-black text-rl-inverse leading-tight tracking-[-0.03em] mb-8"
                    style={{ fontSize: 'clamp(24px, 3vw, 36px)' }}
                  >
                    @rcnn43
                  </p>
                  <p className="font-sans text-rl-muted text-[15px] leading-relaxed mb-10">
                    По вопросам работы сервиса, ошибкам, предложениям или партнёрству.
                  </p>
                  <a
                    href="https://t.me/rcnn43"
                    data-testid="contact-telegram"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center h-12 px-8 bg-[#FACC15] text-rl-inverse font-display font-black text-[13px] uppercase tracking-[0.1em] border-2 border-rl-inverse shadow-neo hover:shadow-neo-hover hover:-translate-x-0.5 hover:-translate-y-0.5 transition-all duration-150"
                  >
                    Открыть Telegram →
                  </a>
                </div>
              </div>
            </ScrollReveal>
          </div>
        </section>
      </main>
      <Footer />
    </>
  )
}
