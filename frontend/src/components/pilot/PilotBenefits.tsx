/**
 * PilotBenefits - Benefits Grid Component
 *
 * @module frontend/src/components/pilot/PilotBenefits
 * @description Showcases 4 key benefits of joining the pilot program
 * @sprint 171 - Market Expansion Foundation (Phase 6)
 */

"use client";

import { useTranslations } from "next-intl";
import { Sparkles, Headphones, BadgePercent, Users } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface Benefit {
  icon: React.ReactNode;
  titleKey: string;
  descriptionKey: string;
}

export function PilotBenefits() {
  const t = useTranslations("pilot.benefits");

  const benefits: Benefit[] = [
    {
      icon: <Sparkles className="h-8 w-8 text-primary" />,
      titleKey: "items.earlyAccess.title",
      descriptionKey: "items.earlyAccess.description",
    },
    {
      icon: <Headphones className="h-8 w-8 text-primary" />,
      titleKey: "items.freeSupport.title",
      descriptionKey: "items.freeSupport.description",
    },
    {
      icon: <BadgePercent className="h-8 w-8 text-primary" />,
      titleKey: "items.lifetime.title",
      descriptionKey: "items.lifetime.description",
    },
    {
      icon: <Users className="h-8 w-8 text-primary" />,
      titleKey: "items.community.title",
      descriptionKey: "items.community.description",
    },
  ];

  return (
    <section className="container mx-auto px-4 py-16" id="pilot-benefits">
      <div className="mx-auto max-w-5xl">
        {/* Section Header */}
        <div className="mb-12 text-center">
          <h2 className="mb-3 text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
            {t("title")}
          </h2>
          <p className="text-lg text-muted-foreground">
            {t("subtitle")}
          </p>
        </div>

        {/* Benefits Grid */}
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {benefits.map((benefit, index) => (
            <Card
              key={index}
              className="border-border transition-shadow hover:shadow-lg"
            >
              <CardHeader>
                <div className="mb-4 flex justify-center">{benefit.icon}</div>
                <CardTitle className="text-center text-lg">
                  {t(benefit.titleKey)}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-center text-sm text-muted-foreground">
                  {t(benefit.descriptionKey)}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}
