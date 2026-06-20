const FAQ = [
  {
    q: 'Как начать пользоваться RawLead?',
    a: 'Откройте ленту заказов, пройдите квиз и войдите через Telegram в кабинете.',
  },
  {
    q: 'Сколько стоит RawLead?',
    a: 'Trial бесплатно 3 дня при первом входе. Premium — 790 ₽/мес без автосписания.',
  },
  {
    q: 'Какие биржи поддерживаются?',
    a: 'FL.ru, Kwork, YouDo, Freelance.ru, FreelanceJob, Пчёл.нет и Telegram-каналы.',
  },
]

export default function FaqJsonLd() {
  const data = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: FAQ.map(item => ({
      '@type': 'Question',
      name: item.q,
      acceptedAnswer: {
        '@type': 'Answer',
        text: item.a,
      },
    })),
  }

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data) }}
    />
  )
}
