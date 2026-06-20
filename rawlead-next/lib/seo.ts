import type { Metadata } from 'next'
import { OG_IMAGE, SITE_URL } from './site'

type PageSeo = {
  title: string
  description: string
  path: `/${string}` | '/'
}

export function pageMetadata({ title, description, path }: PageSeo): Metadata {
  const url = path === '/' ? `${SITE_URL}/` : `${SITE_URL}${path}`

  return {
    title,
    description,
    alternates: { canonical: url },
    openGraph: {
      title,
      description,
      url,
      siteName: 'RawLead',
      locale: 'ru_RU',
      type: 'website',
      images: [{ url: OG_IMAGE, width: 1200, height: 630, alt: 'RawLead' }],
    },
    twitter: {
      card: 'summary_large_image',
      title,
      description,
      images: [OG_IMAGE],
    },
  }
}
