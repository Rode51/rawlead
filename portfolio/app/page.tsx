import Hero from './components/Hero'
import Tagline from './components/Tagline'
import Services from './components/Services'
import Projects from './components/Projects'
import Process from './components/Process'
import Footer from './components/Footer'

export default function Home() {
  return (
    <main>
      <Hero />
      <Tagline />
      <Services />
      <Projects />
      <Process />
      <Footer />
    </main>
  )
}
