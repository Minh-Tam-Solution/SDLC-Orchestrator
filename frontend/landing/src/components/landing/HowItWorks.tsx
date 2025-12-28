/**
 * How It Works Section - SDLC Orchestrator Landing Page
 *
 * @module frontend/landing/src/components/landing/HowItWorks
 * @description Three-step flow with i18n support
 * @sdlc SDLC 5.1.2 Universal Framework
 * @status Sprint 60 - i18n Localization
 */

"use client";

import { useTranslations } from "next-intl";

const stepKeys = ["step1", "step2", "step3"] as const;

/**
 * HowItWorks component displaying three-step flow
 */
export function HowItWorks() {
  const t = useTranslations("howItWorks");

  return (
    <section
      className="py-16 md:py-24 bg-background"
      aria-labelledby="how-it-works-heading"
    >
      <div className="container mx-auto px-4 md:px-6">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-12 md:mb-16">
          <h2
            id="how-it-works-heading"
            className="text-heading-1 font-bold tracking-tight text-foreground mb-4 md:text-display"
          >
            {t("title")}
          </h2>
          <p className="text-body-lg text-muted-foreground">
            {t("subtitle")}
          </p>
        </div>

        {/* Steps */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto">
          {stepKeys.map((key, index) => (
            <div
              key={key}
              className="relative text-center"
            >
              {/* Connector Line (hidden on mobile, between steps) */}
              {index < stepKeys.length - 1 && (
                <div
                  className="hidden md:block absolute top-8 left-1/2 w-full h-0.5 bg-border"
                  aria-hidden="true"
                />
              )}

              {/* Step Number Circle */}
              <div className="relative inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary text-primary-foreground text-heading-2 font-bold mb-6 z-10">
                {t(`${key}.number`)}
              </div>

              {/* Step Content */}
              <h3 className="text-heading-3 font-semibold text-foreground mb-2">
                {t(`${key}.title`)}
              </h3>
              <p className="text-body text-muted-foreground">
                {t(`${key}.description`)}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
