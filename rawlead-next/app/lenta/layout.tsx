import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Лента заказов — RawLead',
  description: 'Актуальные заказы с FL.ru, Kwork, YouDo, Telegram и других бирж. Персональная лента с % совпадения.',
  openGraph: {
    title: 'Лента заказов — RawLead',
    description: 'Заказы под твой стек с 7 бирж фриланса.',
    url: 'https://rawlead.ru/lenta/',
  },
}

export default function LentaLayout({ children }: { children: React.ReactNode }) {
  return children
}
