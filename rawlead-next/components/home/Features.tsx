'use client'

import ScrollReveal from '@/components/ui/ScrollReveal'

const FEATURES = [
  {
    num: '01',
    title: 'Один поток',
    text: 'Биржи, агрегаторы, Telegram-каналы — всё в одной ленте. Ты не ходишь по вкладкам — заказы приходят к тебе.',
  },
  {
    num: '02',
    title: 'ИИ читает суть заказа',
    text: 'Система понимает задачу и сверяет с твоим стеком — не по ключевым словам, а по смыслу.',
  },
  {
    num: '03',
    title: 'Уникальный отклик',
    text: 'Каждый получает свою формулировку — ИИ адаптирует текст под тебя. Пишешь и отправляешь сам — мы не спамим за тебя.',
  },
]

export default function Features() {
  return (
    <section className="py-24 md:py-32 bg-rl-section border-b-2 border-rl-inverse">
      <div
        className="mx-auto px-6"
        style={{ maxWidth: 'var(--rl-container)' }}
      >
        <div className="grid grid-cols-1 md:grid-cols-3 gap-0 border-2 border-rl-inverse shadow-neo">
          {FEATURES.map((f, i) => (
            <ScrollReveal
              key={f.num}
              delay={i * 0.1}
              className={`p-8 md:p-10 bg-rl-page group hover:bg-[#FACC15] transition-colors duration-200 cursor-default ${
                i < FEATURES.length - 1
                  ? 'border-b-2 md:border-b-0 md:border-r-2 border-rl-inverse'
                  : ''
              }`}
            >
              <div className="font-display font-black text-[52px] leading-none text-[#FACC15] group-hover:text-rl-inverse mb-6 tracking-[-0.04em] transition-colors duration-200">
                {f.num}
              </div>
              <h3 className="font-display font-black text-rl-inverse text-xl mb-4 tracking-[-0.01em]">
                {f.title}
              </h3>
              <p className="font-sans text-rl-muted group-hover:text-rl-inverse/70 text-[15px] leading-relaxed transition-colors duration-200">
                {f.text}
              </p>
            </ScrollReveal>
          ))}
        </div>
      </div>
    </section>
  )
}
