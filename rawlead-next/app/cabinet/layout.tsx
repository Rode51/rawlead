import type { Metadata } from 'next'
import { pageMetadata } from '@/lib/seo'

export const metadata: Metadata = {
  robots: { index: false, follow: false },
  ...pageMetadata({
    title: 'Кабинет — RawLead',
    description:
      'Мои отклики, черновики и статус подписки. Войди через Telegram — 3 дня Trial бесплатно.',
    path: '/cabinet/',
  }),
}

export default function CabinetLayout({ children }: { children: React.ReactNode }) {
  return children
}
