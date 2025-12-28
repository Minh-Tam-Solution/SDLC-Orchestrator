/**
 * Landing Page - SDLC Orchestrator
 *
 * @module frontend/landing/src/app/page
 * @description Main landing page with all sections per approved Design Spec v1.1.0
 * @sdlc SDLC 5.1.2 Universal Framework
 * @status Sprint 57 - Landing MVP
 * @approved CTO December 26, 2025 (G2 CONDITIONAL PASS)
 */

import {
  Header,
  Hero,
  Features,
  HowItWorks,
  Pricing,
  VietnamFounders,
  CTASection,
  Footer,
} from "@/components/landing";

/**
 * Home page component - Landing page for SDLC Orchestrator
 *
 * Section order per approved Design Spec:
 * 1. Header (sticky navigation)
 * 2. Hero (Control Plane messaging)
 * 3. Features (4 capabilities)
 * 4. How It Works (3 steps)
 * 5. Vietnam Founders (VN SME wedge)
 * 6. Pricing (3 tiers)
 * 7. CTA Section (3 CTAs)
 * 8. Footer
 */
export default function Home() {
  return (
    <>
      <Header />
      <main id="main-content">
        <Hero />
        <section id="features">
          <Features />
        </section>
        <HowItWorks />
        <VietnamFounders />
        <section id="pricing">
          <Pricing />
        </section>
        <CTASection />
      </main>
      <Footer />
    </>
  );
}
