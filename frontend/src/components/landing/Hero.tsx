/**
 * Hero Section - SDLC Orchestrator Landing Page
 *
 * @module frontend/landing/src/components/landing/Hero
 * @description Primary hero section with "Control Plane" messaging
 * @sdlc SDLC 5.2.0 Universal Framework (7-Pillar Architecture)
 * @status Sprint 105 - SDLC 5.2.0 Updates
 */

"use client";

import { useTranslations } from "next-intl";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import Link from "next/link";

/**
 * Hero component for the landing page
 */
export function Hero() {
  const t = useTranslations("hero");

  return (
    <section
      className="relative overflow-hidden bg-gradient-to-b from-background to-secondary/20 pt-20 pb-16 md:pt-28 md:pb-24"
      aria-labelledby="hero-heading"
    >
      {/* Background decoration */}
      <div className="absolute inset-0 -z-10 overflow-hidden">
        <div className="absolute left-1/2 top-0 -translate-x-1/2 -translate-y-1/2 h-[600px] w-[600px] rounded-full bg-primary/5 blur-3xl" />
        <div className="absolute right-0 top-1/4 h-[400px] w-[400px] rounded-full bg-accent/5 blur-3xl" />
      </div>

      <div className="container mx-auto px-4 md:px-6">
        <div className="flex flex-col items-center text-center max-w-4xl mx-auto">
          {/* Badge */}
          <Badge
            variant="secondary"
            className="mb-6 px-4 py-1.5 text-sm font-medium bg-primary/10 text-primary border-primary/20 hover:bg-primary/15"
          >
            {t("badge")}
          </Badge>

          {/* Main Headline */}
          <h1
            id="hero-heading"
            className="text-display font-bold tracking-tight text-foreground mb-6 md:text-display-lg"
          >
            {t("headline")}
          </h1>

          {/* Subheadline */}
          <p className="text-body-lg text-muted-foreground max-w-2xl mb-8 md:text-xl">
            {t("subheadline")}
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 mb-10">
            <Button
              asChild
              size="lg"
              className="px-8 py-6 text-base font-semibold"
            >
              <Link href="/register">
                {t("cta.primary")}
              </Link>
            </Button>
            <Button
              asChild
              variant="outline"
              size="lg"
              className="px-8 py-6 text-base font-semibold"
            >
              <Link href="/demo">
                {t("cta.secondary")}
              </Link>
            </Button>
          </div>

          {/* Trust Badges */}
          <div className="flex flex-wrap justify-center gap-4 text-sm text-muted-foreground">
            <div className="flex items-center gap-2 px-4 py-2 bg-card rounded-full border">
              <span className="text-success font-medium" aria-hidden="true">
                &#x2713;
              </span>
              <span>{t("stats.gates")}</span>
            </div>
            <div className="flex items-center gap-2 px-4 py-2 bg-card rounded-full border">
              <span className="text-success font-medium" aria-hidden="true">
                &#x2713;
              </span>
              <span>{t("stats.latency")}</span>
            </div>
            <div className="flex items-center gap-2 px-4 py-2 bg-card rounded-full border">
              <span className="text-success font-medium" aria-hidden="true">
                &#x2713;
              </span>
              <span>{t("stats.coverage")}</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
