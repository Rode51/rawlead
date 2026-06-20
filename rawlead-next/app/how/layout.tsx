import type { Metadata } from 'next'
import { pageMetadata } from '@/lib/seo'

export const metadata: Metadata = {
  ...pageMetadata({
    title: 'Как устроено — RawLead',
    description:
      'Пять шагов от биржи до твоего отклика. Без ручного мониторинга — ИИ находит, пишет черновик, ты откликаешься.',
    path: '/how/',
  }),
}

export default function HowLayout({ children }: { children: React.ReactNode }) {
  return children
}
