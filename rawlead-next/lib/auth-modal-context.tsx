'use client'

import { createContext, useCallback, useContext, useState } from 'react'
import LoginDialog from '@/components/auth/LoginDialog'

interface AuthModalContextValue {
  openLogin: () => void
  closeLogin: () => void
}

const AuthModalContext = createContext<AuthModalContextValue | null>(null)

export function useAuthModal() {
  const ctx = useContext(AuthModalContext)
  if (!ctx) throw new Error('useAuthModal must be inside AuthModalProvider')
  return ctx
}

export function AuthModalProvider({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false)

  const openLogin = useCallback(() => setOpen(true), [])
  const closeLogin = useCallback(() => setOpen(false), [])

  return (
    <AuthModalContext.Provider value={{ openLogin, closeLogin }}>
      {children}
      {open && <LoginDialog onClose={closeLogin} />}
    </AuthModalContext.Provider>
  )
}
