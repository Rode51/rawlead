import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Частые вопросы — RawLead',
  description: 'Ответы на частые вопросы о RawLead: как начать, как работает ИИ-подбор, что такое Premium и Trial.',
  openGraph: {
    title: 'Частые вопросы — RawLead',
    description: 'Ответы на частые вопросы о RawLead.',
    url: 'https://rawlead.ru/faq/',
  },
}

export default function FaqLayout({ children }: { children: React.ReactNode }) {
  return children
}
