import type { Metadata } from 'next'
import { Unbounded, Manrope } from 'next/font/google'
import './globals.css'
import Providers from '@/components/Providers'

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
  title: 'RawLead — заказы под твой стек',
  description: 'AI-агрегатор заказов с фриланс-бирж. Персональная лента, умный match, автоответы.',
  openGraph: {
    title: 'RawLead — заказы под твой стек',
    description: 'AI-агрегатор заказов с фриланс-бирж.',
    url: 'https://rawlead.ru',
    siteName: 'RawLead',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru" className={`${unbounded.variable} ${manrope.variable}`}>
      <body className="font-sans">
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
