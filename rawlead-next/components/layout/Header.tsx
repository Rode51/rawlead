'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import { useAuth } from '@/lib/auth-context'
import { useAuthModal } from '@/lib/auth-modal-context'
import { displayHandle } from '@/lib/user-meta'
import UserAvatar from '@/components/ui/UserAvatar'

const NAV = [
  { href: '/lenta/', label: 'Лента' },
  { href: '/pricing/', label: 'Тарифы' },
  { href: '/how/', label: 'Как устроено' },
]

interface Props {
  onLoginClick?: () => void
}

export default function Header({ onLoginClick }: Props) {
  const auth = useAuth()
  const { openLogin } = useAuthModal()
  const handleLogin = onLoginClick ?? openLogin
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 4)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <header
      className={`sticky top-0 z-50 h-14 bg-rl-page border-b-2 border-rl-inverse transition-shadow duration-150 ${
        scrolled ? 'shadow-[0_3px_0_#111010]' : ''
      }`}
    >
      <div
        className="mx-auto px-6 h-full flex items-center justify-between gap-4"
        style={{ maxWidth: 'var(--rl-container)' }}
      >
        {/* Logo */}
        <Link
          href="/"
          data-testid="header-logo"
          className="font-display font-black text-[1.05rem] tracking-[-0.02em] text-rl-inverse no-underline hover:opacity-80 transition-opacity"
        >
          RawLead
        </Link>

        {/* Nav */}
        <nav className="hidden md:flex items-center gap-6">
          {NAV.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              data-testid={`header-nav-${href.replace(/\//g, '') || 'home'}`}
              className="text-[11px] font-display font-black uppercase tracking-[0.12em] text-[#1A1918] no-underline hover:text-rl-inverse transition-colors"
            >
              {label}
            </Link>
          ))}
        </nav>

        {/* Auth CTA */}
        {auth.status === 'auth' && auth.profile ? (
          <div className="flex items-center gap-3">
            <Link
              href="/cabinet/"
              data-testid="header-cabinet"
              className="flex items-center gap-2 no-underline hover:opacity-90 transition-opacity"
            >
              <UserAvatar profile={auth.profile} size={36} />
              <span className="text-[11px] font-display font-black uppercase tracking-[0.08em] text-[#111010]">
                {displayHandle(auth.profile)}
              </span>
            </Link>
            <button
              onClick={auth.logout}
              className="text-[11px] text-[#6B6B6B] hover:text-[#111010]"
            >
              Выйти
            </button>
          </div>
        ) : auth.status === 'pending' ? (
          <div className="h-8 w-24 bg-[#EEEDEA] animate-pulse" />
        ) : (
          <button
            onClick={handleLogin}
            data-testid="header-login"
            className="inline-flex items-center h-8 px-4 bg-rl-inverse text-white font-display font-black text-[11px] uppercase tracking-[0.1em] border-2 border-rl-inverse shadow-[2px_2px_0_#111010] hover:shadow-[4px_4px_0_#111010] hover:-translate-x-px hover:-translate-y-px transition-all duration-150"
          >
            Войти
          </button>
        )}
      </div>
    </header>
  )
}
