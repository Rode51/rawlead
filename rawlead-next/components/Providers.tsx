'use client'

import { AuthProvider } from '@/lib/auth-context'
import { AuthModalProvider } from '@/lib/auth-modal-context'
import SmoothScroll from '@/components/ui/SmoothScroll'
import SupportButton from '@/components/ui/SupportButton'
import DraftToast from '@/components/ui/DraftToast'

export default function Providers({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <AuthModalProvider>
        <SmoothScroll>{children}</SmoothScroll>
        <SupportButton />
        <DraftToast />
      </AuthModalProvider>
    </AuthProvider>
  )
}
