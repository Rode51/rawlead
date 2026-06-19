import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Кабинет — RawLead',
  description: 'Мои отклики, черновики и статус подписки. Войди через Telegram — 3 дня Trial бесплатно.',
  openGraph: {
    title: 'Кабинет — RawLead',
    description: 'Inbox откликов и управление подпиской.',
    url: 'https://rawlead.ru/cabinet/',
  },
}

export default function CabinetLayout({ children }: { children: React.ReactNode }) {
  return children
}
