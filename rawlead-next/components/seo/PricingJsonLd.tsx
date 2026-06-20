import { SITE_URL } from '@/lib/site'

export default function PricingJsonLd() {
  const data = {
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    name: 'RawLead',
    applicationCategory: 'BusinessApplication',
    operatingSystem: 'Web',
    url: `${SITE_URL}/pricing/`,
    offers: {
      '@type': 'Offer',
      price: '790',
      priceCurrency: 'RUB',
      billingIncrement: 'P1M',
    },
  }

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }}
    />
  )
}
