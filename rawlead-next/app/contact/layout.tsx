import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Контакт — RawLead',
  description: 'Написать напрямую — @rcnn43 в Telegram.',
  openGraph: {
    title: 'Контакт — RawLead',
    description: 'Написать напрямую — @rcnn43 в Telegram.',
    url: 'https://rawlead.ru/contact/',
  },
}

export default function ContactLayout({ children }: { children: React.ReactNode }) {
  return children
}
