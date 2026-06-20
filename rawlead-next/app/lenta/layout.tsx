import type { Metadata } from 'next'
import { pageMetadata } from '@/lib/seo'

export const metadata: Metadata = {
  ...pageMetadata({
    title: 'Лента заказов — RawLead',
    description:
      'Актуальные заказы с FL.ru, Kwork, YouDo, Telegram и других бирж. Персональная лента с % совпадения.',
    path: '/lenta/',
  }),
}

export default function LentaLayout({ children }: { children: React.ReactNode }) {
  return children
}
