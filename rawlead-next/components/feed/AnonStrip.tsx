'use client'

interface Props {
  onLoginClick: () => void
  quizCompleted?: boolean
}

export default function AnonStrip({ onLoginClick, quizCompleted = false }: Props) {
  return (
    <div data-testid="anon-strip" className="bg-[#F5F5F0] border-b-2 border-[#111010] px-4 py-2.5 text-[13px]">
      <div className="max-w-feed mx-auto flex items-center gap-2 flex-wrap">
        {quizCompleted ? (
          <>
            <span className="text-[#525252]">Профиль квиза сохранён локально.</span>
            <span className="text-[#D4D4D4]">·</span>
            <button
              onClick={onLoginClick}
              data-testid="anon-strip-login"
              className="text-[#111010] font-semibold underline hover:no-underline"
            >
              Войди через TG — перенесём в аккаунт + 3 дня Premium →
            </button>
          </>
        ) : (
          <>
            <span className="text-[#6B6B6B]">Заказы с задержкой 30 мин.</span>
            <span className="text-[#D4D4D4]">·</span>
            <button
              onClick={onLoginClick}
              data-testid="anon-strip-login"
              className="text-[#111010] font-semibold underline hover:no-underline"
            >
              Войди через TG — 3 дня Premium бесплатно →
            </button>
          </>
        )}
      </div>
    </div>
  )
}
