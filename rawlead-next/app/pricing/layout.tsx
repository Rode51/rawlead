import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Тарифы — RawLead',
  description: 'RawLead Premium — 790 ₽/мес. Первые 3 дня бесплатно, автоматически при первом входе. Без автосписания.',
  openGraph: {
    title: 'Тарифы — RawLead',
    description: '790 ₽/мес · 3 дня Trial бесплатно · без автосписания.',
    url: 'https://rawlead.ru/pricing/',
  },
}

export default function PricingLayout({ children }: { children: React.ReactNode }) {
  return children
}
