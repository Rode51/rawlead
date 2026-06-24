import Hero from './components/Hero'
import Tagline from './components/Tagline'
import Services from './components/Services'
import WhyMe from './components/WhyMe'
import Projects from './components/Projects'
import Process from './components/Process'
import FAQ from './components/FAQ'
import Footer from './components/Footer'
import { ru } from '../lib/content/ru'

export default function Home() {
  return (
    <main>
      <Hero />
      <Tagline />
      <Services />
      <WhyMe />
      <Projects />
      <Process />
      <FAQ      content={ru.faq} />
      <Footer />
    </main>
  )
}
