import AnnouncementBar from '@/components/layout/AnnouncementBar'
import Header from '@/components/layout/Header'
import Footer from '@/components/layout/Footer'
import Hero from '@/components/home/Hero'
import SkillsMarquee from '@/components/home/SkillsMarquee'
import LivePreview from '@/components/home/LivePreview'
import FlowSection from '@/components/home/FlowSection'
import Features from '@/components/home/Features'
import PricingPreview from '@/components/home/PricingPreview'

export default function HomePage() {
  return (
    <>
      <AnnouncementBar />
      <Header />
      <main>
        <Hero />
        <SkillsMarquee />
        <LivePreview />
        <FlowSection />
        <Features />
        <PricingPreview />
      </main>
      <Footer />
    </>
  )
}
