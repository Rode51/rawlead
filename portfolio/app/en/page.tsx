import Hero from '../components/Hero'
import Tagline from '../components/Tagline'
import Services from '../components/Services'
import WhyMe from '../components/WhyMe'
import Projects from '../components/Projects'
import Process from '../components/Process'
import FAQ from '../components/FAQ'
import Footer from '../components/Footer'
import { en, enProjects } from '../../lib/content/en'

export default function HomeEN() {
  return (
    <main>
      <Hero     content={en.hero}    ticker={en.ticker} locale="en" />
      <Tagline  text={en.tagline} />
      <Services content={en.services} />
      <WhyMe    content={en.whyMe} />
      <Projects content={enProjects} />
      <Process  content={en.process} />
      <FAQ      content={en.faq} />
      <Footer   content={en.footer} locale="en" />
    </main>
  )
}
