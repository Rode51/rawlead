import type { Metadata } from 'next'

const BASE_URL = 'https://rode51.ru'

export const metadata: Metadata = {
  metadataBase: new URL(BASE_URL),
  title: {
    default: 'Rode51 — Bots, parsers, automation',
    template: '%s — Rode51',
  },
  description:
    'I build Telegram bots, parsers and web services. From idea to production — I code, deploy and support without middlemen. Remote.',
  keywords: ['telegram bot development', 'web scraping', 'automation', 'python developer', 'api integration', 'freelance developer'],
  authors: [{ name: 'Rode51', url: BASE_URL }],
  openGraph: {
    type: 'website',
    url: `${BASE_URL}/en`,
    siteName: 'Rode51',
    title: 'Rode51 — Bots, parsers, automation',
    description:
      'I build Telegram bots, parsers and web services. From idea to production — remote.',
    locale: 'en_US',
  },
  twitter: {
    card: 'summary',
    title: 'Rode51 — Bots, parsers, automation',
    description: 'I build Telegram bots, parsers and web services. Remote.',
    creator: '@rode_51',
  },
  alternates: {
    canonical: `${BASE_URL}/en`,
    languages: { 'ru': BASE_URL, 'en': `${BASE_URL}/en` },
  },
}

export default function EnLayout({ children }: { children: React.ReactNode }) {
  return <div lang="en">{children}</div>
}
