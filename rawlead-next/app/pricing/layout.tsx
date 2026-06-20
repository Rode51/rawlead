import type { Metadata } from 'next'
import PricingJsonLd from '@/components/seo/PricingJsonLd'
import { pageMetadata } from '@/lib/seo'

export const metadata: Metadata = {
  ...pageMetadata({
    title: 'Тарифы — RawLead',
    description:
      'RawLead Premium — 790 ₽/мес. Первые 3 дня бесплатно, автоматически при первом входе. Без автосписания.',
    path: '/pricing/',
  }),
}

export default function PricingLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <PricingJsonLd />
      {children}
    </>
  )
}
