import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Как устроено — RawLead',
  description: 'Пять шагов от биржи до твоего отклика. Без ручного мониторинга — ИИ находит, пишет черновик, ты откликаешься.',
  openGraph: {
    title: 'Как устроено — RawLead',
    description: 'Пять шагов от биржи до твоего отклика.',
    url: 'https://rawlead.ru/how/',
  },
}

export default function HowLayout({ children }: { children: React.ReactNode }) {
  return children
}
