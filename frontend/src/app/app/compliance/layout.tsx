/**
 * Compliance Layout - SDLC Orchestrator
 *
 * @module frontend/src/app/app/compliance/layout
 * @description Sprint 156 - NIST AI RMF GOVERN: Sub-navigation layout for compliance frameworks
 * @sdlc SDLC 6.0.6 Universal Framework
 * @status Sprint 156 - NIST AI RMF GOVERN
 */

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const complianceTabs = [
  { name: "Overview", href: "/app/compliance" },
  { name: "NIST AI RMF", href: "/app/compliance/nist", disabled: true },
  { name: "EU AI Act", href: "/app/compliance/eu-ai-act", disabled: true },
  { name: "ISO 42001", href: "/app/compliance/iso-42001", disabled: true },
];

export default function ComplianceLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance</h1>
        <p className="mt-1 text-sm text-gray-500">
          Enterprise compliance framework management - NIST AI RMF, EU AI Act, ISO 42001
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {complianceTabs.map((tab) => {
            const isActive = tab.href === "/app/compliance"
              ? pathname === "/app/compliance"
              : pathname.startsWith(tab.href);
            return (
              <Link
                key={tab.name}
                href={tab.disabled ? "#" : tab.href}
                className={cn(
                  "whitespace-nowrap border-b-2 px-1 py-4 text-sm font-medium",
                  tab.disabled
                    ? "cursor-not-allowed border-transparent text-gray-300"
                    : isActive
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700"
                )}
                onClick={tab.disabled ? (e) => e.preventDefault() : undefined}
              >
                {tab.name}
                {tab.disabled && (
                  <span className="ml-2 inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-500">
                    Coming Soon
                  </span>
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Page Content */}
      {children}
    </div>
  );
}
