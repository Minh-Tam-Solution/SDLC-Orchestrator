/**
 * Vietnam Founders Section - SDLC Orchestrator Landing Page
 *
 * @module frontend/landing/src/components/landing/VietnamFounders
 * @description EP-06 Vietnamese Founders section with i18n support
 * @sdlc SDLC 5.1.2 Universal Framework
 * @status Sprint 60 - i18n Localization
 */

"use client";

import { useTranslations } from "next-intl";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import Link from "next/link";

const featureIcons = {
  templates: "🛒",
  pipeline: "🛡️",
  compliance: "📋",
  support: "💬",
};

/**
 * VietnamFounders component - dedicated section for Vietnamese SME wedge
 */
export function VietnamFounders() {
  const t = useTranslations("vietnamFounders");

  return (
    <section
      className="py-16 md:py-24 bg-gradient-to-br from-accent/5 via-background to-primary/5"
      aria-labelledby="vietnam-founders-heading"
    >
      <div className="container mx-auto px-4 md:px-6">
        <div className="max-w-4xl mx-auto">
          {/* Vietnamese Flag Badge */}
          <div className="flex justify-center mb-6">
            <Badge
              variant="secondary"
              className="px-4 py-1.5 text-sm font-medium bg-accent/10 text-accent border-accent/20"
            >
              {t("flag")} {t("title")}
            </Badge>
          </div>

          {/* Main Content */}
          <div className="text-center mb-10">
            <h2
              id="vietnam-founders-heading"
              className="text-heading-1 font-bold tracking-tight text-foreground mb-4 md:text-display"
            >
              {t("heading")}
            </h2>
            <p className="text-heading-3 text-muted-foreground mb-6">
              {t("subtitle")}
            </p>

            {/* Key Message */}
            <div className="bg-card border rounded-lg p-6 md:p-8 text-left max-w-3xl mx-auto mb-8">
              <p className="text-body-lg text-foreground leading-relaxed">
                {t("description")}
              </p>
              <p className="text-caption text-muted-foreground mt-3">
                {t("disclaimer")}
              </p>
            </div>
          </div>

          {/* Feature Highlights */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-10">
            {(["templates", "pipeline", "compliance", "support"] as const).map((key) => (
              <div key={key} className="flex items-start gap-3 p-4 bg-card border rounded-lg">
                <span className="text-2xl" role="img" aria-hidden="true">
                  {featureIcons[key]}
                </span>
                <div>
                  <p className="font-semibold text-foreground">
                    {t(`features.${key}`)}
                  </p>
                </div>
              </div>
            ))}
          </div>

          {/* CTA */}
          <div className="text-center">
            <Button
              asChild
              size="lg"
              className="px-8 py-6 text-base font-semibold bg-accent hover:bg-accent/90 text-accent-foreground"
            >
              <Link href="/register?plan=founder">
                {t("cta")}
              </Link>
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}
