/**
 * NIST AI RMF Overview Page - SDLC Orchestrator
 *
 * @module frontend/src/app/app/compliance/nist/page
 * @description Sprint 156 - NIST AI RMF GOVERN: Overview of NIST AI RMF functions
 * @sdlc SDLC 6.0.5 Universal Framework
 * @status Sprint 156 - NIST AI RMF GOVERN
 */

"use client";

import Link from "next/link";
import { cn } from "@/lib/utils";

// =============================================================================
// Icon Components
// =============================================================================

function ShieldCheckIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" />
    </svg>
  );
}

function MapIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 6.75V15m6-6v8.25m.503 3.498 4.875-2.437c.381-.19.622-.58.622-1.006V4.82c0-.836-.88-1.38-1.628-1.006l-3.869 1.934c-.317.159-.69.159-1.006 0L9.503 3.252a1.125 1.125 0 0 0-1.006 0L3.622 5.689C3.24 5.88 3 6.27 3 6.695V19.18c0 .836.88 1.38 1.628 1.006l3.869-1.934c.317-.159.69-.159 1.006 0l4.994 2.497c.317.158.69.158 1.006 0Z" />
    </svg>
  );
}

function ChartBarIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
    </svg>
  );
}

function CogIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
    </svg>
  );
}

// =============================================================================
// NIST AI RMF Functions Data
// =============================================================================

const nistFunctions = [
  {
    name: "GOVERN",
    description: "Establish and monitor AI governance policies, risk management structures, and accountability frameworks.",
    href: "/app/compliance/nist/govern",
    controls: 5,
    status: "active" as const,
    icon: ShieldCheckIcon,
    iconColor: "bg-blue-100 text-blue-600",
    subcategories: [
      "GOVERN 1 - Policies & Procedures",
      "GOVERN 2 - Accountability Structures",
      "GOVERN 3 - Workforce Diversity",
      "GOVERN 4 - Organizational Culture",
      "GOVERN 5 - Stakeholder Engagement",
    ],
  },
  {
    name: "MAP",
    description: "Identify and catalog AI systems, assess context, and map risks and impacts across the organization.",
    href: "/app/compliance/nist/map",
    controls: 5,
    status: "active" as const,
    icon: MapIcon,
    iconColor: "bg-amber-100 text-amber-600",
    subcategories: [
      "MAP 1.1 - Context Establishment",
      "MAP 1.2 - Stakeholder Identification",
      "MAP 2.1 - System Categorization",
      "MAP 3.1 - Risk & Impact Mapping",
      "MAP 3.2 - Dependency Mapping",
    ],
  },
  {
    name: "MEASURE",
    description: "Quantify AI system performance, evaluate bias, and track risk metrics over time.",
    href: "/app/compliance/nist/measure",
    controls: 4,
    status: "active" as const,
    icon: ChartBarIcon,
    iconColor: "bg-emerald-100 text-emerald-600",
    subcategories: [
      "MEASURE 1.1 - Performance Thresholds",
      "MEASURE 2.1 - Bias Detection",
      "MEASURE 2.2 - Disparity Analysis",
      "MEASURE 3.1 - Metric Trending",
    ],
  },
  {
    name: "MANAGE",
    description: "Implement risk responses, allocate resources, and maintain continuous monitoring of AI systems.",
    href: "/app/compliance/nist/manage",
    controls: 0,
    status: "coming_soon" as const,
    icon: CogIcon,
    iconColor: "bg-purple-100 text-purple-600",
    subcategories: [
      "MANAGE 1 - Risk Response",
      "MANAGE 2 - Resource Allocation",
      "MANAGE 3 - Continuous Monitoring",
      "MANAGE 4 - Risk Communication",
    ],
  },
];

// =============================================================================
// Main Page
// =============================================================================

export default function NistOverviewPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900">NIST AI Risk Management Framework</h2>
        <p className="mt-1 text-sm text-gray-500">
          Version 1.0 - Four core functions for managing AI system risks throughout their lifecycle.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        {nistFunctions.map((fn) => {
          const Icon = fn.icon;
          return (
            <div
              key={fn.name}
              className={cn(
                "rounded-lg border p-6 shadow-sm",
                fn.status === "active"
                  ? "border-blue-200 bg-blue-50"
                  : "border-gray-200 bg-gray-50"
              )}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={cn("rounded-lg p-2", fn.iconColor)}>
                    <Icon className="h-5 w-5" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900">{fn.name}</h3>
                </div>
                {fn.status === "active" ? (
                  <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
                    Active
                  </span>
                ) : (
                  <span className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-500">
                    Coming Soon
                  </span>
                )}
              </div>
              <p className="mt-3 text-sm text-gray-600">{fn.description}</p>

              {/* Subcategories */}
              <div className="mt-4">
                <p className="text-xs font-medium uppercase tracking-wider text-gray-500">Subcategories</p>
                <ul className="mt-2 space-y-1">
                  {fn.subcategories.map((sub) => (
                    <li key={sub} className="flex items-center gap-2 text-xs text-gray-600">
                      <span className={cn(
                        "h-1.5 w-1.5 rounded-full",
                        fn.status === "active" ? "bg-blue-400" : "bg-gray-300"
                      )} />
                      {sub}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="mt-5 flex items-center justify-between border-t border-gray-200 pt-4">
                <span className="text-sm text-gray-500">
                  {fn.controls > 0 ? `${fn.controls} controls` : "Controls pending"}
                </span>
                {fn.status === "active" ? (
                  <Link
                    href={fn.href}
                    className="text-sm font-medium text-blue-600 hover:text-blue-500"
                  >
                    View Dashboard
                  </Link>
                ) : (
                  <span className="text-sm text-gray-400">Sprint 157+</span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* NIST AI RMF Reference */}
      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <h3 className="text-sm font-semibold text-gray-900">Reference</h3>
        <p className="mt-2 text-sm text-gray-600">
          The NIST AI Risk Management Framework (AI RMF 1.0) was published by the National Institute
          of Standards and Technology in January 2023. It is a voluntary framework intended to help
          organizations manage AI-related risks. The framework is structured around four core functions
          that form a continuous cycle: GOVERN, MAP, MEASURE, and MANAGE.
        </p>
        <p className="mt-2 text-sm text-gray-500">
          SDLC Orchestrator implements these functions using OPA (Open Policy Agent) policies for
          automated assessment, with evidence collection stored in the Evidence Vault for audit compliance.
        </p>
      </div>
    </div>
  );
}
