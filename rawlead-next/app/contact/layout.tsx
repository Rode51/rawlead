import type { Metadata } from 'next'
import { pageMetadata } from '@/lib/seo'

export const metadata: Metadata = {
  ...pageMetadata({
    title: 'Контакт — RawLead',
    description: 'Написать напрямую — @rode_51 в Telegram.',
    path: '/contact/',
  }),
}

export default function ContactLayout({ children }: { children: React.ReactNode }) {
  return children
}
