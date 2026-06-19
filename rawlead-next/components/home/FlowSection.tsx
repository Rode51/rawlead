'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { useEffect, useRef, useState, useCallback } from 'react'
import Link from 'next/link'

/* ── поток ── */
const STREAM = [
  { id: 1,  src: 'FL.ru',    col: '#00A65A', title: 'PHP-сайт визитка под ключ',            match: null,  budget: null },
  { id: 2,  src: 'Kwork',    col: '#EA580C', title: 'Логотип + брендинг стартапа',          match: null,  budget: null },
  { id: 3,  src: 'FL.ru',    col: '#00A65A', title: 'WordPress + WooCommerce магазин',      match: 89,    budget: '25 000 ₽' },
  { id: 4,  src: 'Telegram', col: '#0088CC', title: 'SMM Instagram — 3 месяца ведения',     match: null,  budget: null },
  { id: 5,  src: 'YouDo',    col: '#2563EB', title: 'Ремонт стиральной машины Samsung',     match: null,  budget: null },
  { id: 6,  src: 'Telegram', col: '#0088CC', title: 'Figma landing page для SaaS',          match: 91,    budget: '15 000 ₽' },
  { id: 7,  src: 'Kwork',    col: '#EA580C', title: 'SEO-статья 5000 знаков с ключами',     match: null,  budget: null },
  { id: 8,  src: 'FL.ru',    col: '#00A65A', title: 'Python-парсер цен + Google Sheets',    match: 74,    budget: '8 000 ₽'  },
  { id: 9,  src: 'HH',       col: '#D7001B', title: 'Копирайтер в штат, Москва',            match: null,  budget: null },
  { id: 10, src: 'YouDo',    col: '#2563EB', title: 'Курьер-частник по городу',             match: null,  budget: null },
  { id: 11, src: 'Kwork',    col: '#EA580C', title: 'Telegram-бот на Python aiogram',       match: 83,    budget: '12 000 ₽' },
  { id: 12, src: 'HH',       col: '#D7001B', title: 'Менеджер по продажам B2B',             match: null,  budget: null },
]

type Card = typeof STREAM[0]
type HitCard = Card & { match: number; budget: string }
const HITS = STREAM.filter(c => c.match !== null) as HitCard[]

  interface Flying {
  card: HitCard
  targetSlot: number
}

interface FlyCoords {
  sx: number
  sy: number
  ex: number
  ey: number
  ew: number
  eh: number
}

/* ── карточка потока ── */
function StreamCard({ card, hot }: { card: Card; hot: boolean }) {
  return (
    <motion.div
      data-card-id={card.id}
      className="shrink-0 w-52 mx-3 p-3.5 border-2 bg-[#0D0D0D]"
      animate={{
        y:           hot ? -14       : 0,
        scale:       hot ? 1.06      : 1,
        borderColor: hot ? '#FACC15' : 'rgba(255,255,255,0.12)',
        opacity:     hot ? 1         : 0.22,
      }}
      transition={{ type: 'spring', stiffness: 340, damping: 26 }}
      style={{ boxShadow: hot ? '0 0 28px rgba(250,204,21,0.4)' : 'none' }}
    >
      <span
        className="inline-block text-[10px] font-display font-black uppercase tracking-[0.1em] px-1.5 py-0.5 border mb-2"
        style={{ color: card.col, borderColor: card.col, opacity: hot ? 1 : 0.5 }}
      >
        {card.src}
      </span>
      <p className="font-display font-black text-[12px] leading-snug line-clamp-2 text-white/30">
        {card.title}
      </p>
    </motion.div>
  )
}

/* ── карточка в слоте ── */
function SlotCard({ card }: { card: HitCard }) {
  return (
    <div className="h-[118px] bg-[#0D0D0D] border-2 border-[#FACC15] p-4 flex flex-col justify-between shadow-[0_0_16px_rgba(250,204,21,0.12)]">
      <div className="flex items-center justify-between gap-2">
        <span
          className="text-[10px] font-display font-black uppercase tracking-[0.1em] px-1.5 py-0.5 border-2"
          style={{ color: card.col, borderColor: card.col }}
        >
          {card.src}
        </span>
        <span className="text-[11px] font-display font-black text-[#FACC15]">{card.budget}</span>
      </div>
      <p className="font-display font-black text-white text-[12px] leading-snug line-clamp-2">
        {card.title}
      </p>
      <div className="flex items-center gap-2 mt-1">
        <div className="flex-1 h-[3px] bg-white/10 overflow-hidden">
          <motion.div
            className="h-full bg-[#FACC15]"
            initial={{ width: 0 }}
            animate={{ width: `${card.match}%` }}
            transition={{ type: 'spring', stiffness: 120, damping: 22, delay: 0.1 }}
          />
        </div>
        <span className="text-[10px] font-display font-black text-[#FACC15] shrink-0">{card.match}%</span>
      </div>
    </div>
  )
}

/* ── пустой слот ── */
function EmptySlot() {
  return (
    <div className="h-[118px] border-2 border-dashed border-white/10 flex items-center justify-center">
      <div className="flex items-center gap-2">
        <motion.span
          className="w-1.5 h-1.5 rounded-full bg-white/20"
          animate={{ opacity: [0.2, 0.8, 0.2] }}
          transition={{ duration: 1.8, repeat: Infinity, ease: 'easeInOut' }}
        />
        <span className="text-[10px] font-display font-black uppercase tracking-[0.14em] text-white/20">
          ожидание
        </span>
      </div>
    </div>
  )
}

function findVisibleCardEl(streamEl: HTMLElement, cardId: number): HTMLElement | null {
  const nodes = Array.from(streamEl.querySelectorAll(`[data-card-id="${cardId}"]`))
  const streamRect = streamEl.getBoundingClientRect()
  for (const node of nodes) {
    const rect = node.getBoundingClientRect()
    if (rect.right > streamRect.left + 8 && rect.left < streamRect.right - 8) {
      return node as HTMLElement
    }
  }
  return (nodes[0] as HTMLElement | undefined) ?? null
}

function rectInSection(el: HTMLElement, sectionEl: HTMLElement) {
  const r = el.getBoundingClientRect()
  const root = sectionEl.getBoundingClientRect()
  return {
    left: r.left - root.left,
    top: r.top - root.top,
    width: r.width,
    height: r.height,
  }
}

/* ── летящая карточка (absolute внутри section — scroll-safe) ── */
function computeFlyCoords(
  flying: Flying,
  streamEl: HTMLElement,
  slotEl: HTMLElement,
  sectionEl: HTMLElement,
): FlyCoords {
  const eRect = rectInSection(slotEl, sectionEl)
  const ew = eRect.width
  const eh = eRect.height
  const sw = Math.min(eRect.width, 208)
  const sh = eRect.height

  const cardEl = findVisibleCardEl(streamEl, flying.card.id)
  const startRect = cardEl ? rectInSection(cardEl, sectionEl) : null
  const streamRect = rectInSection(streamEl, sectionEl)
  const sx = startRect
    ? startRect.left + startRect.width / 2 - sw / 2
    : streamRect.left + streamRect.width / 2 - sw / 2
  const sy = startRect
    ? startRect.top + (startRect.height - sh) / 2
    : streamRect.top + (streamRect.height - sh) / 2

  return { sx, sy, ex: eRect.left, ey: eRect.top, ew, eh }
}

function FlyingOverlay({
  flying,
  streamRowRef,
  slotRefs,
  sectionRef,
  onDone,
}: {
  flying: Flying
  streamRowRef: React.RefObject<HTMLDivElement | null>
  slotRefs: React.RefObject<(HTMLDivElement | null)[]>
  sectionRef: React.RefObject<HTMLElement | null>
  onDone: () => void
}) {
  const initialRef = useRef<FlyCoords | null>(null)
  const [target, setTarget] = useState<FlyCoords | null>(null)

  const recalcTarget = useCallback(() => {
    const streamEl = streamRowRef.current
    const slotEl = slotRefs.current?.[flying.targetSlot]
    const sectionEl = sectionRef.current
    if (!streamEl || !slotEl || !sectionEl) return

    const coords = computeFlyCoords(flying, streamEl, slotEl, sectionEl)
    if (!initialRef.current) {
      initialRef.current = coords
    }
    setTarget(coords)
  }, [flying, streamRowRef, slotRefs, sectionRef])

  useEffect(() => {
    recalcTarget()
    let raf = 0
    const schedule = () => {
      cancelAnimationFrame(raf)
      raf = requestAnimationFrame(recalcTarget)
    }
    window.addEventListener('scroll', schedule, { passive: true, capture: true })
    window.addEventListener('resize', schedule, { passive: true })
    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener('scroll', schedule, true)
      window.removeEventListener('resize', schedule)
    }
  }, [recalcTarget])

  const initial = initialRef.current ?? target
  if (!initial || !target) return null

  return (
    <motion.div
      className="absolute z-[9999] pointer-events-none border-2 border-[#FACC15] bg-[#0D0D0D] p-4 flex flex-col justify-between"
      style={{ width: target.ew, height: target.eh, top: 0, left: 0 }}
      initial={{
        x: initial.sx,
        y: initial.sy,
        scale: 1.08,
        opacity: 1,
        boxShadow: '0 0 32px rgba(250,204,21,0.5)',
      }}
      animate={{
        x: target.ex,
        y: target.ey,
        scale: 1,
        opacity: 1,
        boxShadow: '0 0 16px rgba(250,204,21,0.15)',
      }}
      transition={{ type: 'spring', stiffness: 180, damping: 22 }}
      onAnimationComplete={onDone}
    >
      <div className="flex items-center justify-between gap-2">
        <span
          className="text-[10px] font-display font-black uppercase tracking-[0.1em] px-1.5 py-0.5 border-2"
          style={{ color: flying.card.col, borderColor: flying.card.col }}
        >
          {flying.card.src}
        </span>
        <span className="text-[11px] font-display font-black text-[#FACC15]">{flying.card.budget}</span>
      </div>
      <p className="font-display font-black text-white text-[12px] leading-snug line-clamp-2">
        {flying.card.title}
      </p>
      <div className="flex items-center gap-2 mt-1">
        <div className="flex-1 h-[3px] bg-white/10">
          <div className="h-full bg-[#FACC15]" style={{ width: `${flying.card.match}%` }} />
        </div>
        <span className="text-[10px] font-display font-black text-[#FACC15]">{flying.card.match}%</span>
      </div>
    </motion.div>
  )
}

/* ── главный компонент ── */
export default function FlowSection() {
  const [hotId, setHotId]       = useState<number | null>(null)
  const [slots, setSlots]       = useState<(HitCard | null)[]>([null, null, null])
  const [flying, setFlying]     = useState<Flying | null>(null)

  const streamRowRef            = useRef<HTMLDivElement>(null)
  const sectionRef              = useRef<HTMLElement>(null)
  const slotRefs                = useRef<(HTMLDivElement | null)[]>([null, null, null])
  const hitIndexRef             = useRef(0)
  const lastSlotRef             = useRef(-1)

  useEffect(() => {
    let interval: ReturnType<typeof setInterval>

    const fire = () => {
      const card = HITS[hitIndexRef.current % HITS.length]
      hitIndexRef.current++

      // выбираем слот рандомно, не повторяя предыдущий
      let slot: number
      do { slot = Math.floor(Math.random() * 3) } while (slot === lastSlotRef.current)
      lastSlotRef.current = slot

      setHotId(card.id)

      // после подсветки — запускаем полёт
      setTimeout(() => {
        const streamEl = streamRowRef.current
        const slotEl   = slotRefs.current[slot]
        const sectionEl = sectionRef.current
        if (!streamEl || !slotEl || !sectionEl) return

        setFlying({ card, targetSlot: slot })
        setHotId(null)
      }, 550)
    }

    const timeout = setTimeout(() => {
      fire()
      interval = setInterval(fire, 3600 + Math.random() * 1200)
    }, 1400)

    return () => {
      clearTimeout(timeout)
      if (interval) clearInterval(interval)
    }
  }, [])

  const onFlyDone = () => {
    if (!flying) return
    const { card, targetSlot } = flying
    setSlots(prev => {
      const next = [...prev]
      next[targetSlot] = card
      return next
    })
    setFlying(null)
  }

  return (
      <section ref={sectionRef} className="relative bg-[#111010] border-b-2 border-[#FACC15]/20 overflow-hidden">
      {flying && (
        <FlyingOverlay
          key={`${flying.card.id}-${flying.targetSlot}`}
          flying={flying}
          streamRowRef={streamRowRef}
          slotRefs={slotRefs}
          sectionRef={sectionRef}
          onDone={onFlyDone}
        />
      )}

        {/* Заголовок */}
        <div className="mx-auto px-6 pt-24 pb-12" style={{ maxWidth: 'var(--rl-container)' }}>
          <motion.p
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-[11px] font-display font-black uppercase tracking-[0.2em] text-white/30 mb-5"
          >
            Как устроено
          </motion.p>
          <motion.h2
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.08 }}
            className="font-display font-black text-white leading-[0.95] tracking-[-0.03em] max-w-2xl"
            style={{ fontSize: 'clamp(32px, 5vw, 56px)' }}
          >
            Один поток вместо десяти вкладок
          </motion.h2>
        </div>

        {/* Поток карточек */}
        <div
          ref={streamRowRef}
          className="overflow-hidden py-5 border-y border-white/8"
          style={{ contain: 'layout paint', isolation: 'isolate' }}
        >
          <div
            className="marquee-run"
            style={{ '--marquee-dur': '78s' } as React.CSSProperties}
          >
            {[...STREAM, ...STREAM, ...STREAM].map((card, i) => (
              <StreamCard key={`${card.id}-${i}`} card={card} hot={card.id === hotId} />
            ))}
          </div>
        </div>

        {/* Стрелка */}
        <div className="mx-auto px-6 pt-8 pb-4 flex items-center gap-3" style={{ maxWidth: 'var(--rl-container)' }}>
          <motion.span
            animate={{ y: [0, 5, 0] }}
            transition={{ duration: 1.6, repeat: Infinity, ease: 'easeInOut' }}
            className="text-[#FACC15] text-lg leading-none"
          >
            ↓
          </motion.span>
          <span className="text-[11px] font-display font-black uppercase tracking-[0.18em] text-white/35">
            Твоя лента
          </span>
        </div>

        {/* Три фиксированных слота */}
        <div className="mx-auto px-6 pb-16" style={{ maxWidth: 'var(--rl-container)' }}>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {slots.map((card, i) => (
              <div
                key={i}
                ref={el => { slotRefs.current[i] = el }}
              >
                <AnimatePresence mode="wait">
                  {flying?.targetSlot === i ? (
                    <motion.div
                      key="flying-target"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ duration: 0.15 }}
                    >
                      <EmptySlot />
                    </motion.div>
                  ) : card ? (
                    <motion.div
                      key={card.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ duration: 0.2 }}
                    >
                      <SlotCard card={card} />
                    </motion.div>
                  ) : (
                    <motion.div
                      key="empty"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 0.15 }}
                    >
                      <EmptySlot />
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ))}
          </div>
        </div>

        {/* Манифест — статичен, не зависит от слотов */}
        <div className="border-t border-white/8">
          <div className="mx-auto px-6 py-20 text-center" style={{ maxWidth: 'var(--rl-container)' }}>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-80px' }}
              transition={{ type: 'spring', stiffness: 240, damping: 28 }}
              className="font-display font-black text-white leading-tight tracking-[-0.02em]"
              style={{ fontSize: 'clamp(28px, 4.5vw, 52px)' }}
            >
              Перестань мониторить.
              <br />
              <span className="text-[#FACC15]">Начни откликаться.</span>
            </motion.p>
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-80px' }}
              transition={{ type: 'spring', stiffness: 240, damping: 28, delay: 0.14 }}
              className="mt-8"
            >
              <Link
                href="/lenta/"
                className="inline-flex items-center h-12 px-8 bg-[#FACC15] text-[#111010] font-display font-black text-sm uppercase tracking-[0.1em] border-2 border-[#FACC15] shadow-[4px_4px_0_rgba(250,204,21,0.25)] hover:shadow-[7px_7px_0_rgba(250,204,21,0.25)] hover:-translate-x-0.5 hover:-translate-y-0.5 transition-all duration-150"
              >
                Смотреть ленту →
              </Link>
            </motion.div>
          </div>
        </div>

      </section>
  )
}
