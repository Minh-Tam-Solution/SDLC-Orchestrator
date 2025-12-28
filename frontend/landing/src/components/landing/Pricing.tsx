/**
 * Pricing Section - SDLC Orchestrator Landing Page
 *
 * @module frontend/landing/src/components/landing/Pricing
 * @description Three-tier pricing with i18n support
 * @sdlc SDLC 5.1.2 Universal Framework
 * @status Sprint 60 - i18n Localization
 */

"use client";

import { useTranslations } from "next-intl";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import Link from "next/link";

const tierKeys = ["free", "founder", "enterprise"] as const;

const tierConfig = {
  free: {
    ctaHref: "/register?plan=free",
    variant: "outline" as const,
    popular: false,
  },
  founder: {
    ctaHref: "/checkout?plan=founder",
    variant: "default" as const,
    popular: true,
  },
  enterprise: {
    ctaHref: "https://calendly.com/sdlc-orchestrator",
    variant: "outline" as const,
    popular: false,
  },
};

/**
 * Pricing component displaying three tiers
 */
export function Pricing() {
  const t = useTranslations("pricing");

  return (
    <section
      id="pricing"
      className="py-16 md:py-24 bg-secondary/30"
      aria-labelledby="pricing-heading"
    >
      <div className="container mx-auto px-4 md:px-6">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-12 md:mb-16">
          <h2
            id="pricing-heading"
            className="text-heading-1 font-bold tracking-tight text-foreground mb-4 md:text-display"
          >
            {t("title")}
          </h2>
          <p className="text-body-lg text-muted-foreground">
            {t("subtitle")}
          </p>
        </div>

        {/* Pricing Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {tierKeys.map((key) => {
            const config = tierConfig[key];
            const features = t.raw(`${key}.features`) as string[];

            return (
              <Card
                key={key}
                className={`relative flex flex-col ${
                  config.popular
                    ? "border-accent shadow-lg shadow-accent/10 scale-105 z-10"
                    : "border-border/50"
                }`}
              >
                {/* Popular Badge */}
                {config.popular && (
                  <Badge
                    className="absolute -top-3 left-1/2 -translate-x-1/2 bg-accent text-accent-foreground px-4 py-1"
                  >
                    {t(`${key}.badge`)}
                  </Badge>
                )}

                <CardHeader className="text-center pb-4">
                  <CardTitle className="text-heading-2 font-bold">
                    {t(`${key}.name`)}
                  </CardTitle>
                  <div className="mt-4">
                    <div className="flex items-baseline justify-center flex-wrap gap-1">
                      <span className="text-4xl md:text-5xl font-bold text-foreground">
                        {t(`${key}.price`)}
                      </span>
                      {t(`${key}.period`) && (
                        <span className="text-body-sm text-muted-foreground">
                          {t(`${key}.period`)}
                        </span>
                      )}
                    </div>
                    {key === "founder" && (
                      <span className="block text-body-sm text-muted-foreground mt-1">
                        {t(`${key}.priceNote`)}
                      </span>
                    )}
                  </div>
                  <CardDescription className="text-body text-muted-foreground mt-2">
                    {t(`${key}.description`)}
                  </CardDescription>
                </CardHeader>

                <CardContent className="flex-1">
                  <ul className="space-y-3" role="list">
                    {features.map((feature, index) => (
                      <li
                        key={index}
                        className="flex items-start gap-3 text-body-sm"
                      >
                        <span
                          className="text-success font-bold mt-0.5 flex-shrink-0"
                          aria-hidden="true"
                        >
                          &#x2713;
                        </span>
                        <span className="text-muted-foreground">{feature}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>

                <CardFooter className="pt-4">
                  <Button
                    asChild
                    className="w-full py-6 text-base font-semibold"
                    variant={config.variant}
                  >
                    <Link
                      href={config.ctaHref}
                      target={config.ctaHref.startsWith("http") ? "_blank" : undefined}
                      rel={config.ctaHref.startsWith("http") ? "noopener noreferrer" : undefined}
                    >
                      {t(`${key}.cta`)}
                    </Link>
                  </Button>
                </CardFooter>
              </Card>
            );
          })}
        </div>

        {/* Founder Plan Note */}
        <div className="text-center mt-8 max-w-2xl mx-auto">
          <p className="text-body-sm text-muted-foreground">
            <span className="font-medium text-accent">{t("founderNote")}</span>
          </p>
        </div>

        {/* Global Teams Note */}
        <div className="text-center mt-4">
          <p className="text-body-sm text-muted-foreground">
            {t("globalNote")}{" "}
            <Link
              href="https://calendly.com/sdlc-orchestrator"
              className="text-primary hover:underline font-medium"
              target="_blank"
              rel="noopener noreferrer"
            >
              {t("globalLink")}
            </Link>
          </p>
        </div>
      </div>
    </section>
  );
}
