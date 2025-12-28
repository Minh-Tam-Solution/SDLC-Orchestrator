/**
 * CTA Section - SDLC Orchestrator Landing Page
 *
 * @module frontend/landing/src/components/landing/CTASection
 * @description Three CTAs for SME funnel with i18n support
 * @sdlc SDLC 5.1.2 Universal Framework
 * @status Sprint 60 - i18n Localization
 */

"use client";

import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import Link from "next/link";

const ctaKeys = ["demo", "free", "talk"] as const;

const ctaConfig = {
  demo: {
    href: "/demo",
    primary: false,
    external: false,
  },
  free: {
    href: "/register",
    primary: true,
    external: false,
  },
  talk: {
    href: "https://calendly.com/sdlc-orchestrator",
    primary: false,
    external: true,
  },
};

/**
 * CTASection component displaying three call-to-action cards
 */
export function CTASection() {
  const t = useTranslations("ctas");

  return (
    <section
      className="py-16 md:py-24 bg-primary/5"
      aria-labelledby="cta-heading"
    >
      <div className="container mx-auto px-4 md:px-6">
        {/* CTA Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
          {ctaKeys.map((key) => {
            const config = ctaConfig[key];

            return (
              <Card
                key={key}
                className={`text-center ${
                  config.primary
                    ? "border-primary shadow-lg shadow-primary/10"
                    : "border-border/50"
                }`}
              >
                <CardHeader className="pb-2">
                  <div
                    className="text-4xl mb-4"
                    role="img"
                    aria-label={t(`${key}.title`)}
                  >
                    {t(`${key}.icon`)}
                  </div>
                  <CardTitle className="text-heading-3 font-semibold">
                    {t(`${key}.title`)}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-body text-muted-foreground mb-6">
                    {t(`${key}.description`)}
                  </CardDescription>
                  <Button
                    asChild
                    variant={config.primary ? "default" : "outline"}
                    className="w-full py-5 font-semibold"
                  >
                    <Link
                      href={config.href}
                      target={config.external ? "_blank" : undefined}
                      rel={config.external ? "noopener noreferrer" : undefined}
                    >
                      {t(`${key}.cta`)}
                    </Link>
                  </Button>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    </section>
  );
}
