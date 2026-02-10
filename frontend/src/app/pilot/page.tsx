/**
 * Pilot Landing Page - SDLC Orchestrator
 *
 * @module frontend/src/app/pilot/page
 * @description Public landing page for pilot program recruitment
 * @sprint 171 - Market Expansion Foundation (Phase 6)
 */

"use client";

import { useTranslations } from "next-intl";
import { Header, Footer } from "@/components/landing";
import { PilotSignupForm, PilotBenefits, PilotFAQ } from "@/components/pilot";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

/**
 * Pilot Landing Page Component
 *
 * Sections:
 * 1. Hero - Badge + Headline + Subheadline
 * 2. Benefits - 4 benefit cards
 * 3. Signup Form - Application form with validation
 * 4. FAQ - 5 collapsible questions
 */
export default function PilotPage() {
  const t = useTranslations("pilot.hero");

  return (
    <>
      <Header />
      <main id="main-content" className="min-h-screen">
        {/* Hero Section */}
        <section className="container mx-auto px-4 py-16 text-center">
          <div className="mx-auto max-w-3xl">
            {/* Badge */}
            <div className="mb-6 flex justify-center">
              <Badge
                variant="outline"
                className="border-primary px-4 py-2 text-sm font-medium text-primary"
              >
                {t("badge")}
              </Badge>
            </div>

            {/* Headline */}
            <h1 className="mb-6 text-4xl font-bold tracking-tight text-foreground sm:text-5xl md:text-6xl">
              {t("headline")}
            </h1>

            {/* Subheadline */}
            <p className="mb-8 text-xl text-muted-foreground">
              {t("subheadline")}
            </p>

            {/* CTA Button */}
            <Button
              size="lg"
              onClick={() => {
                const signupSection = document.getElementById("pilot-signup");
                signupSection?.scrollIntoView({ behavior: "smooth" });
              }}
            >
              {t("cta")}
            </Button>
          </div>
        </section>

        {/* Benefits Section */}
        <PilotBenefits />

        {/* Signup Form Section */}
        <PilotSignupForm />

        {/* FAQ Section */}
        <PilotFAQ />
      </main>
      <Footer />
    </>
  );
}
