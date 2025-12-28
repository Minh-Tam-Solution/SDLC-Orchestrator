/**
 * Features Section - SDLC Orchestrator Landing Page
 *
 * @module frontend/landing/src/components/landing/Features
 * @description Four core capabilities with i18n support
 * @sdlc SDLC 5.1.2 Universal Framework
 * @status Sprint 60 - i18n Localization
 */

"use client";

import { useTranslations } from "next-intl";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const featureKeys = ["gateEngine", "evidenceVault", "aiContext", "policyGuards"] as const;

const featureIcons: Record<typeof featureKeys[number], string> = {
  gateEngine: "🚪",
  evidenceVault: "📦",
  aiContext: "⚡",
  policyGuards: "🛡️",
};

/**
 * Features component displaying four core capabilities
 */
export function Features() {
  const t = useTranslations("features");

  return (
    <section
      id="features"
      className="py-16 md:py-24 bg-background"
      aria-labelledby="features-heading"
    >
      <div className="container mx-auto px-4 md:px-6">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-12 md:mb-16">
          <h2
            id="features-heading"
            className="text-heading-1 font-bold tracking-tight text-foreground mb-4 md:text-display"
          >
            {t("title")}
          </h2>
          <p className="text-body-lg text-muted-foreground">
            {t("subtitle")}
          </p>
        </div>

        {/* Feature Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {featureKeys.map((key) => (
            <Card
              key={key}
              className="group relative overflow-hidden border-border/50 hover:border-primary/50 hover:shadow-lg transition-all duration-300"
            >
              <CardHeader className="pb-2">
                <div
                  className="text-4xl mb-4 group-hover:scale-110 transition-transform duration-300"
                  role="img"
                  aria-label={t(`items.${key}.title`)}
                >
                  {featureIcons[key]}
                </div>
                <CardTitle className="text-heading-3 font-semibold">
                  {t(`items.${key}.title`)}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription className="text-body text-muted-foreground">
                  {t(`items.${key}.description`)}
                </CardDescription>
              </CardContent>

              {/* Hover gradient effect */}
              <div className="absolute inset-0 -z-10 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}
