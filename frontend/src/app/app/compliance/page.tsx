/**
 * Compliance Overview Page - SDLC Orchestrator
 *
 * @module frontend/src/app/app/compliance/page
 * @description Unified compliance dashboard showing all frameworks
 * @sdlc SDLC 6.0.5 - Sprint 156 (Phase 3: COMPLIANCE)
 * @status Sprint 156 - NIST AI RMF GOVERN
 */

"use client";

import Link from "next/link";
import { cn } from "@/lib/utils";

const frameworks = [
  {
    code: "NIST_AI_RMF",
    name: "NIST AI Risk Management Framework",
    version: "1.0",
    description:
      "The NIST AI RMF provides organizations with a framework for managing risks associated with AI systems throughout their lifecycle. It includes four core functions: GOVERN, MAP, MEASURE, and MANAGE.",
    controls: 19,
    status: "active" as const,
    href: "/app/compliance/nist",
    functions: ["GOVERN", "MAP", "MEASURE", "MANAGE"],
    activeFunction: "MANAGE",
  },
  {
    code: "EU_AI_ACT",
    name: "EU Artificial Intelligence Act",
    version: "2024/1689",
    description:
      "The EU AI Act establishes a comprehensive legal framework for AI systems in the European Union. It classifies AI systems into risk categories: Unacceptable, High-Risk, Limited-Risk, and Minimal-Risk.",
    controls: 0,
    status: "coming_soon" as const,
    href: "/app/compliance/eu-ai-act",
    functions: ["Classification", "Conformity", "Transparency"],
    activeFunction: null,
  },
  {
    code: "ISO_42001",
    name: "ISO/IEC 42001:2023 AI Management Systems",
    version: "2023",
    description:
      "ISO/IEC 42001 specifies requirements for establishing, implementing, maintaining, and continually improving an AI management system (AIMS) within organizations.",
    controls: 0,
    status: "coming_soon" as const,
    href: "/app/compliance/iso-42001",
    functions: ["Leadership", "Risk Assessment", "Operational Controls"],
    activeFunction: null,
  },
];

export default function ComplianceOverviewPage() {
  return (
    <div className="space-y-6">
      {/* Framework Cards */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {frameworks.map((fw) => (
          <div
            key={fw.code}
            className={cn(
              "rounded-lg border p-6 shadow-sm",
              fw.status === "active"
                ? "border-blue-200 bg-white"
                : "border-gray-200 bg-gray-50"
            )}
          >
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{fw.name}</h3>
                <p className="mt-0.5 text-xs text-gray-500">Version {fw.version}</p>
              </div>
              {fw.status === "active" ? (
                <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
                  Active
                </span>
              ) : (
                <span className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-500">
                  Coming Soon
                </span>
              )}
            </div>

            <p className="mt-3 text-sm text-gray-600 line-clamp-3">{fw.description}</p>

            {/* Functions */}
            <div className="mt-4">
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Functions</p>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {fw.functions.map((fn) => (
                  <span
                    key={fn}
                    className={cn(
                      "inline-flex items-center rounded px-2 py-0.5 text-xs font-medium",
                      fn === fw.activeFunction
                        ? "bg-blue-100 text-blue-800"
                        : "bg-gray-100 text-gray-500"
                    )}
                  >
                    {fn}
                  </span>
                ))}
              </div>
            </div>

            {/* Footer */}
            <div className="mt-5 flex items-center justify-between border-t border-gray-100 pt-4">
              <span className="text-sm text-gray-500">
                {fw.controls > 0 ? `${fw.controls} controls` : "No controls yet"}
              </span>
              {fw.status === "active" ? (
                <Link
                  href={fw.href}
                  className="text-sm font-medium text-blue-600 hover:text-blue-500"
                >
                  Open Dashboard →
                </Link>
              ) : (
                <span className="text-sm text-gray-400">Sprint 158+</span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Quick Info */}
      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900">About Compliance Management</h3>
        <p className="mt-2 text-sm text-gray-600">
          The SDLC Orchestrator compliance module provides automated assessment and tracking
          for major AI governance frameworks. Each framework is evaluated using OPA (Open Policy Agent)
          policies that check your project against specific controls.
        </p>
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="rounded-lg bg-blue-50 p-4">
            <p className="text-2xl font-bold text-blue-700">19</p>
            <p className="text-sm text-blue-600">NIST AI RMF Controls</p>
          </div>
          <div className="rounded-lg bg-gray-50 p-4">
            <p className="text-2xl font-bold text-gray-400">0</p>
            <p className="text-sm text-gray-500">EU AI Act Controls</p>
          </div>
          <div className="rounded-lg bg-gray-50 p-4">
            <p className="text-2xl font-bold text-gray-400">0</p>
            <p className="text-sm text-gray-500">ISO 42001 Controls</p>
          </div>
        </div>
      </div>
    </div>
  );
}
