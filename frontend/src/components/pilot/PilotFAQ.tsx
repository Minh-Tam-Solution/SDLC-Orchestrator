/**
 * PilotFAQ - FAQ Component with Collapsible Questions
 *
 * @module frontend/src/components/pilot/PilotFAQ
 * @description FAQ section with 5 collapsible questions about the pilot program
 * @sprint 171 - Market Expansion Foundation (Phase 6)
 */

"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { ChevronDown } from "lucide-react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Button } from "@/components/ui/button";

interface FAQItem {
  questionKey: string;
  answerKey: string;
}

export function PilotFAQ() {
  const t = useTranslations("pilot.faq");

  const faqs: FAQItem[] = [
    { questionKey: "items.q1.question", answerKey: "items.q1.answer" },
    { questionKey: "items.q2.question", answerKey: "items.q2.answer" },
    { questionKey: "items.q3.question", answerKey: "items.q3.answer" },
    { questionKey: "items.q4.question", answerKey: "items.q4.answer" },
    { questionKey: "items.q5.question", answerKey: "items.q5.answer" },
  ];

  return (
    <section className="container mx-auto px-4 py-16" id="pilot-faq">
      <div className="mx-auto max-w-3xl">
        {/* Section Header */}
        <div className="mb-12 text-center">
          <h2 className="mb-3 text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
            {t("title")}
          </h2>
          <p className="text-lg text-muted-foreground">
            {t("subtitle")}
          </p>
        </div>

        {/* FAQ List */}
        <div className="space-y-4">
          {faqs.map((faq, index) => (
            <FAQCollapsibleItem
              key={index}
              questionKey={faq.questionKey}
              answerKey={faq.answerKey}
              index={index}
            />
          ))}
        </div>
      </div>
    </section>
  );
}

interface FAQCollapsibleItemProps {
  questionKey: string;
  answerKey: string;
  index: number;
}

function FAQCollapsibleItem({ questionKey, answerKey, index }: FAQCollapsibleItemProps) {
  const t = useTranslations("pilot.faq");
  const [isOpen, setIsOpen] = useState(false);

  return (
    <Collapsible
      open={isOpen}
      onOpenChange={setIsOpen}
      className="rounded-lg border border-border bg-card"
    >
      <CollapsibleTrigger asChild>
        <Button
          variant="ghost"
          className="w-full justify-between px-6 py-4 text-left hover:bg-muted"
          aria-expanded={isOpen}
          aria-controls={`faq-answer-${index}`}
        >
          <span className="font-medium text-foreground">
            {t(questionKey)}
          </span>
          <ChevronDown
            className={`h-5 w-5 text-muted-foreground transition-transform duration-200 ${
              isOpen ? "rotate-180" : ""
            }`}
          />
        </Button>
      </CollapsibleTrigger>
      <CollapsibleContent
        id={`faq-answer-${index}`}
        className="px-6 pb-4 pt-2"
      >
        <p className="text-muted-foreground">{t(answerKey)}</p>
      </CollapsibleContent>
    </Collapsible>
  );
}
