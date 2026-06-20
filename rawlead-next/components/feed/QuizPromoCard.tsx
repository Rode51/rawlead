'use client'

interface Props {
  onQuizClick: () => void
  onLoginClick: () => void
  quizCompleted: boolean
}

/** First card for anon feed — quiz promo or post-quiz login CTA (WP parity). */
export default function QuizPromoCard({ onQuizClick, onLoginClick, quizCompleted }: Props) {
  if (quizCompleted) {
    return (
      <article
        id="rl-feed-quiz-promo"
        data-testid="feed-quiz-login-promo"
        className="rl-feed-quiz-promo rl-lead-card bg-white flex flex-col cursor-default select-none relative overflow-hidden"
        style={{
          minHeight: 280,
          border: '2px solid #111010',
          boxShadow: '4px 4px 0 #111010',
        }}
        onClick={e => e.stopPropagation()}
      >
        <div
          className="absolute left-0 top-0 bottom-0"
          style={{ width: 4, background: '#16A34A' }}
          aria-hidden="true"
        />
        <div className="flex flex-col flex-1" style={{ padding: '20px 22px 18px 20px' }}>
          <div className="flex items-center gap-2 mb-3">
            <span
              className="inline-flex items-center text-[11px] font-bold uppercase tracking-wide px-2 py-[3px] leading-none"
              style={{
                color: '#111010',
                background: '#F0FDF4',
                border: '1.5px solid #16A34A',
              }}
            >
              Профиль готов
            </span>
          </div>
          <h3
            className="font-display font-black text-[#111010] leading-tight mb-2"
            style={{ fontSize: '1.0625rem', letterSpacing: '-0.025em' }}
          >
            Войди — откроем персональную ленту
          </h3>
          <p className="text-[14px] text-[#525252] leading-relaxed mb-4 flex-1">
            Сохраним результат квиза в аккаунт. 3 дня Premium — автоматически при первом входе.
          </p>
          <button
            type="button"
            data-testid="feed-quiz-login-cta"
            onClick={onLoginClick}
            className="w-full h-11 font-black text-[13px] uppercase tracking-wider text-[#111010] bg-[#FACC15] border-2 border-[#111010] hover:bg-[#FDE047] transition-colors"
            style={{ boxShadow: '3px 3px 0 #111010' }}
          >
            Авторизоваться — персональная лента →
          </button>
        </div>
      </article>
    )
  }

  return (
    <article
      id="rl-feed-quiz-promo"
      data-testid="feed-quiz-promo"
      className="rl-feed-quiz-promo rl-lead-card bg-white flex flex-col cursor-default select-none relative overflow-hidden"
      style={{
        minHeight: 280,
        border: '2px solid #111010',
        boxShadow: '4px 4px 0 #111010',
      }}
      onClick={e => e.stopPropagation()}
    >
      <div
        className="absolute left-0 top-0 bottom-0"
        style={{ width: 4, background: '#E8A020' }}
        aria-hidden="true"
      />
      <div className="flex flex-col flex-1" style={{ padding: '20px 22px 18px 20px' }}>
        <div className="flex items-center gap-2 mb-3">
          <span
            className="inline-flex items-center text-[11px] font-bold uppercase tracking-wide px-2 py-[3px] leading-none"
            style={{
              color: '#111010',
              background: '#FFFBEB',
              border: '1.5px solid #E8A020',
            }}
          >
            RawLead
          </span>
        </div>
        <h3
          className="font-display font-black text-[#111010] leading-tight mb-2"
          style={{ fontSize: '1.0625rem', letterSpacing: '-0.025em' }}
        >
          Персональная лента за 2 мин
        </h3>
        <p className="text-[14px] text-[#525252] leading-relaxed mb-4 flex-1">
          Ответь на карточки — ИИ подберёт заказы под твой стек
        </p>
        <button
          type="button"
          data-testid="feed-quiz-promo-cta"
          onClick={onQuizClick}
          className="w-full h-11 font-black text-[13px] uppercase tracking-wider text-[#111010] bg-[#FACC15] border-2 border-[#111010] hover:bg-[#FDE047] transition-colors"
          style={{ boxShadow: '3px 3px 0 #111010' }}
        >
          Настроить ленту →
        </button>
      </div>
    </article>
  )
}
