import type { Metadata } from 'next'
import FaqJsonLd from '@/components/seo/FaqJsonLd'
import { pageMetadata } from '@/lib/seo'

export const metadata: Metadata = {
  ...pageMetadata({
    title: 'Частые вопросы — RawLead',
    description:
      'Ответы на частые вопросы о RawLead: как начать, как работает ИИ-подбор, что такое Premium и Trial.',
    path: '/faq/',
  }),
}

export default function FaqLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <FaqJsonLd />
      {children}
    </>
  )
}
