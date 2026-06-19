import Link from 'next/link'

const NAV = [
  { label: 'Лента', href: '/lenta/' },
  { label: 'Тарифы', href: '/pricing/' },
  { label: 'Кабинет', href: '/cabinet/' },
  { label: 'Как устроено', href: '/how/' },
  { label: 'FAQ', href: '/faq/' },
  { label: 'Контакт', href: '/contact/' },
]

export default function Footer() {
  return (
    <footer className="bg-rl-inverse text-rl-page border-t-2 border-rl-inverse">
      <div
        className="mx-auto px-6 py-12"
        style={{ maxWidth: 'var(--rl-container)' }}
      >
        <div className="grid grid-cols-1 md:grid-cols-3 gap-10">

          {/* Brand */}
          <div className="space-y-3">
            <div className="font-display font-black text-2xl tracking-tight text-white">
              RawLead
            </div>
            <p className="text-sm text-gray-500 font-sans">by Rode51</p>
            <p className="text-sm text-gray-400 font-sans leading-relaxed">
              Агрегатор фриланс-заказов с ИИ-фильтрацией и персональными черновиками откликов.
            </p>
          </div>

          {/* Nav */}
          <div>
            <p className="text-[10px] font-display font-black tracking-widest uppercase text-gray-600 mb-4">
              Навигация
            </p>
            <ul className="space-y-2">
              {NAV.map(({ label, href }) => (
                <li key={href}>
                  <Link
                    href={href}
                    data-testid={`footer-link-${href.replace(/\//g, '')}`}
                    className="text-sm font-sans text-gray-400 hover:text-white transition-colors"
                  >
                    {label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Contacts */}
          <div>
            <p className="text-[10px] font-display font-black tracking-widest uppercase text-gray-600 mb-4">
              Контакты
            </p>
            <a
              href="https://t.me/rawlead_bot"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-sm font-sans text-gray-400 hover:text-white transition-colors"
            >
              <span className="text-[#FACC15]">→</span>
              Telegram @rawlead_bot
            </a>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="mt-10 pt-6 border-t border-white/10 flex flex-col md:flex-row justify-between items-start md:items-center gap-3 text-xs font-sans text-gray-600">
          <span>© {new Date().getFullYear()} RawLead · by Rode51</span>
          <span>Храмовских Никита Евгеньевич · ИНН 384903841000</span>
        </div>
      </div>
    </footer>
  )
}
