/**
 * Pricing Page — SDLC Orchestrator
 *
 * @module frontend/src/app/pricing/page
 * @description Standalone public pricing page for Sprint 188.
 *   Displays all 4 tiers (LITE / STANDARD / PRO / ENTERPRISE) with feature
 *   comparison table, FAQ section, and trust signals.
 *   No authentication required — public-facing marketing page.
 * @sdlc SDLC 6.1.0 Universal Framework
 * @status Sprint 188 — Pricing Page
 */

import type { Metadata } from "next";
import Link from "next/link";
import { Header, Footer } from "@/components/landing";

export const metadata: Metadata = {
  title: "Pricing — SDLC Orchestrator",
  description:
    "From individual dev with TinySDLC to enterprise compliance with SDLC Orchestrator. Choose the tier that fits your team.",
  openGraph: {
    title: "Pricing — SDLC Orchestrator",
    description:
      "Enterprise AI governance pricing for every team size. Free LITE tier, STANDARD from $99/mo, PROFESSIONAL $499/mo, ENTERPRISE custom.",
    url: "https://sdlc.nhatquangholding.com/pricing",
  },
};

// ---------------------------------------------------------------------------
// Data types
// ---------------------------------------------------------------------------

interface PlanLimit {
  projects: string;
  gates: string;
  storage: string;
  members: string;
}

interface PlanFeature {
  label: string;
  lite: boolean | string;
  standard: boolean | string;
  professional: boolean | string;
  enterprise: boolean | string;
}

interface Plan {
  id: "lite" | "standard" | "professional" | "enterprise";
  name: string;
  badge?: string;
  /** Primary price display line */
  price: string;
  /** Optional sub-price line (e.g. annual or range note) */
  priceNote?: string;
  description: string;
  limits: PlanLimit;
  cta: string;
  ctaHref: string;
  ctaVariant: "primary" | "outline" | "accent";
  highlighted: boolean;
}

interface FaqItem {
  question: string;
  answer: string;
}

// ---------------------------------------------------------------------------
// Static plan data (single source of truth for this page)
// ---------------------------------------------------------------------------

const PLANS: Plan[] = [
  {
    id: "lite",
    name: "LITE",
    price: "Free",
    priceNote: "Forever",
    description: "Perfect for solo developers exploring SDLC governance.",
    limits: {
      projects: "1 project",
      gates: "4 gates / month",
      storage: "100 MB Evidence Vault",
      members: "1 member",
    },
    cta: "Get Started Free",
    ctaHref: "/register?plan=lite",
    ctaVariant: "outline",
    highlighted: false,
  },
  {
    id: "standard",
    name: "STANDARD",
    badge: "Starter from $99",
    price: "$99 – $299",
    priceNote: "per month (Starter / Growth)",
    description: "For growing teams shipping production software with AI.",
    limits: {
      projects: "5 – 15 projects",
      gates: "Unlimited gates",
      storage: "10 – 50 GB storage",
      members: "10 – 30 members",
    },
    cta: "Start 14-Day Trial",
    ctaHref: "/register?plan=standard",
    ctaVariant: "outline",
    highlighted: false,
  },
  {
    id: "professional",
    name: "PRO",
    badge: "Most Popular",
    price: "$499",
    priceNote: "per month",
    description:
      "Full Multi-Agent Team Engine with compliance evidence and all OTT channels.",
    limits: {
      projects: "20 projects",
      gates: "Unlimited gates",
      storage: "100 GB storage",
      members: "Unlimited members",
    },
    cta: "Start 14-Day Trial",
    ctaHref: "/register?plan=professional",
    ctaVariant: "primary",
    highlighted: true,
  },
  {
    id: "enterprise",
    name: "ENTERPRISE",
    price: "Custom",
    priceNote: "from $80 / seat / month",
    description: "Unlimited scale with SOC2 + HIPAA + NIST compliance and dedicated CSM.",
    limits: {
      projects: "Unlimited projects",
      gates: "Unlimited gates",
      storage: "Unlimited storage",
      members: "Unlimited members",
    },
    cta: "Contact Us",
    ctaHref: "https://calendly.com/sdlc-orchestrator",
    ctaVariant: "accent",
    highlighted: false,
  },
];

const FEATURE_ROWS: PlanFeature[] = [
  {
    label: "Multi-Agent Team Engine",
    lite: false,
    standard: false,
    professional: true,
    enterprise: true,
  },
  {
    label: "OTT Channels (Teams, Slack)",
    lite: false,
    standard: "Telegram only",
    professional: "All channels",
    enterprise: "All channels",
  },
  {
    label: "Compliance Evidence",
    lite: false,
    standard: false,
    professional: "SOC2",
    enterprise: "SOC2 + HIPAA + NIST",
  },
  {
    label: "Jira / GitHub Integration",
    lite: false,
    standard: false,
    professional: true,
    enterprise: true,
  },
  {
    label: "Enterprise SSO (SAML/Azure AD)",
    lite: false,
    standard: false,
    professional: false,
    enterprise: true,
  },
  {
    label: "Custom SLA + Dedicated CSM",
    lite: false,
    standard: false,
    professional: false,
    enterprise: true,
  },
  {
    label: "Audit Log Retention",
    lite: "30 days",
    standard: "90 days",
    professional: "1 year",
    enterprise: "Unlimited",
  },
  {
    label: "API Access",
    lite: false,
    standard: "Read-only",
    professional: "Full",
    enterprise: "Full + Webhooks",
  },
  {
    label: "Priority Support",
    lite: false,
    standard: "Email",
    professional: "Email + Slack",
    enterprise: "Phone + Slack + CSM",
  },
];

const FAQ_ITEMS: FaqItem[] = [
  {
    question: "What is the difference between TinySDLC and SDLC Orchestrator?",
    answer:
      "TinySDLC is an open-source, local CLI tool for individual developers to apply SDLC methodology on their machine — no account required. SDLC Orchestrator is the cloud enterprise platform built on top of TinySDLC patterns: it adds team collaboration, Evidence Vault, OPA-powered quality gates, Multi-Agent Team Engine, and compliance reporting. You can graduate from TinySDLC to Orchestrator when your team grows.",
  },
  {
    question: "Is the LITE tier really free forever?",
    answer:
      "Yes. The LITE tier is free with no time limit. It gives you 1 project, 4 quality gate evaluations per month, and 100 MB of Evidence Vault storage. No credit card required. You can upgrade to a paid tier at any time.",
  },
  {
    question: "What is included in the 14-day free trial?",
    answer:
      "The trial unlocks the full feature set of the selected plan — STANDARD or PROFESSIONAL — with no usage restrictions for 14 days. After the trial ends, your data is retained and you can choose to subscribe or revert to LITE.",
  },
  {
    question: "Do you offer Vietnam-local pricing?",
    answer:
      "Yes. The PROFESSIONAL plan is available at approximately 12.5M VND per month when billed in VND via VNPay. Contact our Vietnam sales team for exact rates and annual discounts. Enterprise custom pricing is always negotiated locally.",
  },
  {
    question: "How does the Multi-Agent Team Engine work?",
    answer:
      "The Multi-Agent Team Engine (EP-07) lets you configure AI agent teams — for example an Initializer → Coder → Reviewer chain — that collaborate on SDLC tasks. Agents communicate via a lane-based message queue with SKIP LOCKED concurrency, parent-child session inheritance, and budget circuit breakers. It is available on PRO and ENTERPRISE tiers.",
  },
  {
    question: "Is my code and evidence data secure?",
    answer:
      "All data is encrypted at rest (AES-256) and in transit (TLS 1.3). Evidence files are stored in an S3-compatible vault with SHA256 integrity verification and an immutable audit trail. GDPR Article 20 data portability is supported on all paid tiers. SOC2 compliance reports are available on PRO; SOC2 + HIPAA + NIST on ENTERPRISE.",
  },
];

// ---------------------------------------------------------------------------
// Icon helpers (inline SVG, no dependency needed)
// ---------------------------------------------------------------------------

function CheckIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 20 20"
      fill="currentColor"
      className="h-5 w-5 text-emerald-500 flex-shrink-0"
      aria-hidden="true"
    >
      <path
        fillRule="evenodd"
        d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z"
        clipRule="evenodd"
      />
    </svg>
  );
}

function XIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 20 20"
      fill="currentColor"
      className="h-5 w-5 text-gray-300 flex-shrink-0"
      aria-hidden="true"
    >
      <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

/** Renders a table cell value as a checkmark, X, or text string. */
function FeatureCell({ value }: { value: boolean | string }) {
  if (value === true) return <CheckIcon />;
  if (value === false) return <XIcon />;
  return <span className="text-sm text-gray-700 font-medium">{value}</span>;
}

/** CTA button with three visual variants, rendered as an anchor. */
function CtaButton({
  href,
  variant,
  children,
}: {
  href: string;
  variant: "primary" | "outline" | "accent";
  children: React.ReactNode;
}) {
  const base =
    "inline-flex w-full items-center justify-center rounded-lg px-6 py-3 text-sm font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2";

  const styles: Record<"primary" | "outline" | "accent", string> = {
    primary:
      "bg-blue-600 text-white hover:bg-blue-700 focus-visible:ring-blue-600",
    outline:
      "border border-gray-300 bg-white text-gray-800 hover:bg-gray-50 focus-visible:ring-gray-400",
    accent:
      "bg-amber-500 text-white hover:bg-amber-600 focus-visible:ring-amber-500",
  };

  const isExternal = href.startsWith("http");

  return (
    <Link
      href={href}
      target={isExternal ? "_blank" : undefined}
      rel={isExternal ? "noopener noreferrer" : undefined}
      className={`${base} ${styles[variant]}`}
    >
      {children}
    </Link>
  );
}

/** Single pricing card. */
function PricingCard({ plan }: { plan: Plan }) {
  const isHighlighted = plan.highlighted;

  return (
    <div
      className={[
        "relative flex flex-col rounded-2xl p-8",
        isHighlighted
          ? "bg-blue-600 text-white shadow-2xl shadow-blue-600/30 ring-2 ring-blue-600 scale-[1.02] z-10"
          : "bg-white text-gray-900 shadow-sm ring-1 ring-gray-200",
      ].join(" ")}
    >
      {/* Popular badge */}
      {plan.badge && (
        <span
          className={[
            "absolute -top-3.5 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-full px-4 py-1 text-xs font-semibold",
            isHighlighted
              ? "bg-amber-400 text-amber-900"
              : "bg-blue-100 text-blue-700",
          ].join(" ")}
        >
          {plan.badge}
        </span>
      )}

      {/* Plan name */}
      <div className="mb-2">
        <span
          className={[
            "text-xs font-bold uppercase tracking-widest",
            isHighlighted ? "text-blue-200" : "text-blue-600",
          ].join(" ")}
        >
          {plan.name}
        </span>
      </div>

      {/* Price */}
      <div className="mb-1">
        <span
          className={[
            "text-4xl font-extrabold",
            isHighlighted ? "text-white" : "text-gray-900",
          ].join(" ")}
        >
          {plan.price}
        </span>
      </div>
      {plan.priceNote && (
        <p
          className={[
            "text-sm mb-4",
            isHighlighted ? "text-blue-200" : "text-gray-500",
          ].join(" ")}
        >
          {plan.priceNote}
        </p>
      )}

      {/* Description */}
      <p
        className={[
          "text-sm leading-relaxed mb-6",
          isHighlighted ? "text-blue-100" : "text-gray-600",
        ].join(" ")}
      >
        {plan.description}
      </p>

      {/* Limits */}
      <ul className="space-y-2.5 mb-8 flex-1">
        {Object.values(plan.limits).map((limit) => (
          <li key={limit} className="flex items-center gap-2.5 text-sm">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 20 20"
              fill="currentColor"
              className={[
                "h-4 w-4 flex-shrink-0",
                isHighlighted ? "text-blue-300" : "text-emerald-500",
              ].join(" ")}
              aria-hidden="true"
            >
              <path
                fillRule="evenodd"
                d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z"
                clipRule="evenodd"
              />
            </svg>
            <span className={isHighlighted ? "text-blue-100" : "text-gray-700"}>
              {limit}
            </span>
          </li>
        ))}
      </ul>

      {/* CTA */}
      {isHighlighted ? (
        <Link
          href={plan.ctaHref}
          className="inline-flex w-full items-center justify-center rounded-lg bg-white px-6 py-3 text-sm font-semibold text-blue-600 transition-colors hover:bg-blue-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-blue-600"
        >
          {plan.cta}
        </Link>
      ) : (
        <CtaButton href={plan.ctaHref} variant={plan.ctaVariant}>
          {plan.cta}
        </CtaButton>
      )}
    </div>
  );
}

/** Full feature comparison table (desktop). */
function ComparisonTable() {
  const TIERS = ["lite", "standard", "professional", "enterprise"] as const;

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm border-separate border-spacing-0">
        <thead>
          <tr>
            <th className="sticky left-0 bg-white text-left py-4 pr-6 font-semibold text-gray-500 w-52 border-b border-gray-200">
              Feature
            </th>
            <th className="text-center py-4 px-4 font-semibold text-gray-700 border-b border-gray-200">
              LITE
            </th>
            <th className="text-center py-4 px-4 font-semibold text-gray-700 border-b border-gray-200">
              STANDARD
            </th>
            <th className="text-center py-4 px-4 font-semibold text-blue-700 bg-blue-50 rounded-t-lg border-b border-blue-200">
              PRO
            </th>
            <th className="text-center py-4 px-4 font-semibold text-amber-700 border-b border-gray-200">
              ENTERPRISE
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {FEATURE_ROWS.map((row) => (
            <tr key={row.label} className="group">
              <td className="sticky left-0 bg-white py-3.5 pr-6 text-gray-700 group-hover:text-gray-900">
                {row.label}
              </td>
              <td className="text-center py-3.5 px-4">
                <div className="flex justify-center">
                  <FeatureCell value={row[TIERS[0]]} />
                </div>
              </td>
              <td className="text-center py-3.5 px-4">
                <div className="flex justify-center">
                  <FeatureCell value={row[TIERS[1]]} />
                </div>
              </td>
              <td className="text-center py-3.5 px-4 bg-blue-50/60">
                <div className="flex justify-center">
                  <FeatureCell value={row[TIERS[2]]} />
                </div>
              </td>
              <td className="text-center py-3.5 px-4">
                <div className="flex justify-center">
                  <FeatureCell value={row[TIERS[3]]} />
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** Accordion-style FAQ item. Pure CSS — no JS needed (details/summary). */
function FaqAccordionItem({ item }: { item: FaqItem }) {
  return (
    <details className="group border-b border-gray-200 last:border-b-0">
      <summary className="flex cursor-pointer list-none items-center justify-between gap-4 py-5 text-left font-semibold text-gray-900 hover:text-blue-600 transition-colors">
        {item.question}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          className="h-5 w-5 flex-shrink-0 text-gray-400 transition-transform group-open:rotate-180"
          aria-hidden="true"
        >
          <path
            fillRule="evenodd"
            d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z"
            clipRule="evenodd"
          />
        </svg>
      </summary>
      <p className="pb-5 text-gray-600 leading-relaxed text-sm">{item.answer}</p>
    </details>
  );
}

/** Trust signal badge. */
function TrustBadge({
  icon,
  label,
}: {
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <div className="flex items-center gap-2.5 rounded-xl bg-white px-5 py-3.5 shadow-sm ring-1 ring-gray-200">
      <span className="text-xl leading-none" aria-hidden="true">
        {icon}
      </span>
      <span className="text-sm font-medium text-gray-700">{label}</span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page (React Server Component)
// ---------------------------------------------------------------------------

export default function PricingPage() {
  return (
    <>
      <Header />

      <main id="main-content" className="bg-gray-50">
        {/* ----------------------------------------------------------------- */}
        {/* Hero                                                               */}
        {/* ----------------------------------------------------------------- */}
        <section
          aria-labelledby="pricing-hero-heading"
          className="relative overflow-hidden bg-white pt-20 pb-16 text-center"
        >
          {/* Subtle gradient backdrop */}
          <div
            className="pointer-events-none absolute inset-0 -z-10"
            aria-hidden="true"
          >
            <div className="absolute left-1/2 top-0 -translate-x-1/2 h-96 w-[800px] rounded-full bg-blue-50/70 blur-3xl" />
          </div>

          <div className="mx-auto max-w-3xl px-4">
            <span className="inline-block rounded-full bg-blue-100 px-4 py-1.5 text-xs font-semibold uppercase tracking-widest text-blue-700 mb-6">
              Pricing — Sprint 188
            </span>
            <h1
              id="pricing-hero-heading"
              className="text-4xl font-extrabold tracking-tight text-gray-900 sm:text-5xl mb-4"
            >
              Enterprise AI Governance for Software Teams
            </h1>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              From individual dev with{" "}
              <span className="font-semibold text-gray-800">TinySDLC</span> →
              enterprise compliance with{" "}
              <span className="font-semibold text-gray-800">Orchestrator</span>.
              Pick the plan that fits your team today.
            </p>
          </div>
        </section>

        {/* ----------------------------------------------------------------- */}
        {/* Pricing Cards                                                      */}
        {/* ----------------------------------------------------------------- */}
        <section
          aria-labelledby="pricing-cards-heading"
          className="py-16 px-4"
        >
          <h2 className="sr-only" id="pricing-cards-heading">
            Plan comparison
          </h2>
          <div className="mx-auto max-w-7xl">
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4 items-start">
              {PLANS.map((plan) => (
                <PricingCard key={plan.id} plan={plan} />
              ))}
            </div>

            {/* Vietnam pricing note */}
            <p className="mt-8 text-center text-sm text-gray-500">
              Vietnam-local pricing available via VNPay — PROFESSIONAL from{" "}
              <span className="font-medium text-gray-700">12.5M VND / month</span>.{" "}
              <Link
                href="https://calendly.com/sdlc-orchestrator"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline font-medium"
              >
                Book a call for local rates →
              </Link>
            </p>
          </div>
        </section>

        {/* ----------------------------------------------------------------- */}
        {/* Feature Comparison Table                                           */}
        {/* ----------------------------------------------------------------- */}
        <section
          aria-labelledby="comparison-heading"
          className="bg-white py-16 px-4"
        >
          <div className="mx-auto max-w-5xl">
            <div className="text-center mb-10">
              <h2
                id="comparison-heading"
                className="text-2xl font-bold text-gray-900 mb-2"
              >
                Full Feature Comparison
              </h2>
              <p className="text-gray-500 text-sm">
                Every plan includes 4-Gate Quality Pipeline, Evidence Vault, and OPA
                Policy Guards.
              </p>
            </div>
            <ComparisonTable />
          </div>
        </section>

        {/* ----------------------------------------------------------------- */}
        {/* Trust Signals                                                      */}
        {/* ----------------------------------------------------------------- */}
        <section aria-label="Trust signals" className="py-12 px-4 bg-gray-50">
          <div className="mx-auto max-w-5xl">
            <p className="text-center text-xs font-semibold uppercase tracking-widest text-gray-400 mb-6">
              Trusted by early adopters
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <TrustBadge icon="🇻🇳" label="5 Vietnam pilot customers" />
              <TrustBadge icon="✅" label="Gate G4 Production Ready" />
              <TrustBadge icon="🔒" label="GDPR Art. 20 compliant" />
              <TrustBadge icon="🛡️" label="OWASP ASVS L2 — 98.4%" />
              <TrustBadge icon="⚡" label="API p95 &lt; 100 ms" />
            </div>
          </div>
        </section>

        {/* ----------------------------------------------------------------- */}
        {/* FAQ                                                                */}
        {/* ----------------------------------------------------------------- */}
        <section
          aria-labelledby="faq-heading"
          className="bg-white py-16 px-4"
        >
          <div className="mx-auto max-w-3xl">
            <div className="text-center mb-10">
              <h2
                id="faq-heading"
                className="text-2xl font-bold text-gray-900 mb-2"
              >
                Frequently Asked Questions
              </h2>
              <p className="text-gray-500 text-sm">
                Still have questions?{" "}
                <Link
                  href="https://calendly.com/sdlc-orchestrator"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline font-medium"
                >
                  Book a 30-min call with the team
                </Link>
                .
              </p>
            </div>

            <div className="divide-y divide-gray-200 rounded-2xl border border-gray-200 bg-white overflow-hidden px-6">
              {FAQ_ITEMS.map((item) => (
                <FaqAccordionItem key={item.question} item={item} />
              ))}
            </div>
          </div>
        </section>

        {/* ----------------------------------------------------------------- */}
        {/* Bottom CTA                                                         */}
        {/* ----------------------------------------------------------------- */}
        <section
          aria-labelledby="bottom-cta-heading"
          className="bg-blue-600 py-16 px-4 text-center"
        >
          <div className="mx-auto max-w-2xl">
            <h2
              id="bottom-cta-heading"
              className="text-2xl font-bold text-white mb-3"
            >
              Ready to govern your AI-generated code?
            </h2>
            <p className="text-blue-200 mb-8 text-sm">
              Start with LITE for free — no credit card required. Upgrade when your
              team grows.
            </p>
            <div className="flex flex-wrap items-center justify-center gap-4">
              <Link
                href="/register?plan=lite"
                className="inline-flex items-center justify-center rounded-lg bg-white px-8 py-3 text-sm font-semibold text-blue-600 transition-colors hover:bg-blue-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-blue-600"
              >
                Get Started Free
              </Link>
              <Link
                href="https://calendly.com/sdlc-orchestrator"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center rounded-lg border border-blue-400 px-8 py-3 text-sm font-semibold text-white transition-colors hover:bg-blue-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-blue-600"
              >
                Talk to Sales →
              </Link>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </>
  );
}
