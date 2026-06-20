import type { Metadata } from 'next'
import { Unbounded, Manrope } from 'next/font/google'
import './globals.css'
import Providers from '@/components/Providers'
import YandexMetrika from '@/components/analytics/YandexMetrika'
import OrganizationJsonLd from '@/components/seo/OrganizationJsonLd'
import { pageMetadata } from '@/lib/seo'
import { SITE_URL } from '@/lib/site'

const unbounded = Unbounded({
  subsets: ['latin', 'cyrillic'],
  weight: ['400', '600', '700', '800', '900'],
  variable: '--font-display',
  display: 'swap',
})

const manrope = Manrope({
  subsets: ['latin', 'cyrillic'],
  weight: ['400', '500', '600', '700', '800'],
  variable: '--font-body',
  display: 'swap',
})

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  ...pageMetadata({
    title: 'RawLead — ИИ-агрегатор фриланс-заказов',
    description:
      'Заказы с FL, Kwork и Telegram в одной ленте. ИИ пишет черновик отклика. Trial бесплатно.',
    path: '/',
  }),
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru" className={`${unbounded.variable} ${manrope.variable}`}>
      <body className="font-sans">
        <OrganizationJsonLd />
        <Providers>{children}</Providers>
        <YandexMetrika />
      </body>
    </html>
  )
}
