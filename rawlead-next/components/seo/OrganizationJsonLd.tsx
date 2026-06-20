import { SITE_URL } from '@/lib/site'

export default function OrganizationJsonLd() {
  const data = {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: 'RawLead',
    url: SITE_URL,
    description: 'ИИ-агрегатор фриланс-заказов с FL.ru, Kwork, YouDo и Telegram',
  }

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }}
    />
  )
}
