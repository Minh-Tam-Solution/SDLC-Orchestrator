/**
 * GDPR Dashboard Page - SDLC Orchestrator
 *
 * @module frontend/src/app/app/gdpr/page
 * @description DSAR management, Data Export (Art. 15/20), Consent management (Art. 7)
 * @sdlc SDLC 6.1.1 — Sprint 214 Track A (ENT Compliance #10)
 * @status Active — ENTERPRISE+ required (ADR-063)
 */

"use client";

import { useState } from "react";
import { LockedFeature } from "@/components/tier-gate/LockedFeature";
import { useUserTier } from "@/hooks/useUserTier";
import {
  useDsarList,
  useCreateDsar,
  useDataExportSummary,
  useFullDataExport,
  useActiveConsents,
  useRecordConsent,
  type DSARCreateRequest,
} from "@/hooks/useGdpr";

export default function GdprPage() {
  const { effectiveTier, isLoading: tierLoading } = useUserTier();
  const currentTier = tierLoading ? "LITE" : effectiveTier;

  return (
    <LockedFeature
      requiredTier="ENTERPRISE"
      currentTier={currentTier}
      featureLabel="GDPR Dashboard"
    >
      <div className="space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">GDPR Compliance Dashboard</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage Data Subject Access Requests, data exports, and consent preferences.
          </p>
        </div>

        <DSARSection />
        <DataExportSection />
        <ConsentSection />
      </div>
    </LockedFeature>
  );
}

// ---------------------------------------------------------------------------
// DSAR Requests Section
// ---------------------------------------------------------------------------

function DSARSection() {
  const { data, isLoading, error } = useDsarList();
  const createDsar = useCreateDsar();
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState<DSARCreateRequest>({
    request_type: "access",
    requester_email: "",
    description: "",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createDsar.mutate(formData, {
      onSuccess: () => {
        setShowForm(false);
        setFormData({ request_type: "access", requester_email: "", description: "" });
      },
    });
  };

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Data Subject Access Requests</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
        >
          {showForm ? "Cancel" : "New DSAR"}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="mt-4 space-y-3 rounded-lg border border-blue-100 bg-blue-50 p-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Request Type</label>
            <select
              value={formData.request_type}
              onChange={(e) => setFormData({ ...formData, request_type: e.target.value as DSARCreateRequest["request_type"] })}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            >
              <option value="access">Access (Art. 15)</option>
              <option value="rectification">Rectification (Art. 16)</option>
              <option value="erasure">Erasure (Art. 17)</option>
              <option value="portability">Portability (Art. 20)</option>
              <option value="restriction">Restriction (Art. 18)</option>
              <option value="objection">Objection (Art. 21)</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Requester Email</label>
            <input
              type="email"
              required
              value={formData.requester_email}
              onChange={(e) => setFormData({ ...formData, requester_email: e.target.value })}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              placeholder="user@example.com"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Description</label>
            <textarea
              required
              rows={2}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
              placeholder="Describe the request..."
            />
          </div>
          <button
            type="submit"
            disabled={createDsar.isPending}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {createDsar.isPending ? "Submitting..." : "Submit DSAR"}
          </button>
          {createDsar.isError && (
            <p className="text-sm text-red-600">{createDsar.error.message}</p>
          )}
        </form>
      )}

      <div className="mt-4">
        {isLoading && <p className="text-sm text-gray-500">Loading DSARs...</p>}
        {error && <p className="text-sm text-red-600">Error: {error.message}</p>}
        {data && data.items.length === 0 && (
          <p className="text-sm text-gray-500">No DSAR requests found.</p>
        )}
        {data && data.items.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left font-medium text-gray-500">Type</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-500">Email</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-500">Status</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-500">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.items.map((dsar) => (
                  <tr key={dsar.id}>
                    <td className="whitespace-nowrap px-3 py-2 font-medium text-gray-900 capitalize">
                      {dsar.request_type}
                    </td>
                    <td className="whitespace-nowrap px-3 py-2 text-gray-600">{dsar.requester_email}</td>
                    <td className="whitespace-nowrap px-3 py-2">
                      <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                        dsar.status === "completed"
                          ? "bg-green-100 text-green-800"
                          : dsar.status === "pending"
                            ? "bg-yellow-100 text-yellow-800"
                            : "bg-gray-100 text-gray-600"
                      }`}>
                        {dsar.status}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-3 py-2 text-gray-500">
                      {new Date(dsar.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Data Export Section (Art. 15 + Art. 20)
// ---------------------------------------------------------------------------

function DataExportSection() {
  const { data: summary, isLoading } = useDataExportSummary();
  const fullExport = useFullDataExport();

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-gray-900">Data Export</h2>
      <p className="mt-1 text-sm text-gray-500">
        View your data categories (Art. 15) or request a full machine-readable export (Art. 20).
      </p>

      {isLoading && <p className="mt-3 text-sm text-gray-500">Loading export summary...</p>}

      {summary && (
        <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-5">
          {Object.entries(summary.categories).map(([category, count]) => (
            <div key={category} className="rounded-lg bg-gray-50 p-3 text-center">
              <p className="text-xl font-bold text-gray-800">{count}</p>
              <p className="text-xs text-gray-500 capitalize">{category.replace(/_/g, " ")}</p>
            </div>
          ))}
        </div>
      )}

      <div className="mt-4 flex items-center gap-3">
        <button
          onClick={() => fullExport.mutate()}
          disabled={fullExport.isPending}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {fullExport.isPending ? "Exporting..." : "Full Data Export (Art. 20)"}
        </button>
        <span className="text-xs text-gray-400">Rate limit: 1 request per 24 hours</span>
      </div>

      {fullExport.isSuccess && (
        <div className="mt-3 rounded-lg border border-green-200 bg-green-50 p-3">
          <p className="text-sm font-medium text-green-800">Export generated successfully.</p>
          <p className="text-xs text-green-600">
            Exported at: {fullExport.data.exported_at}
          </p>
        </div>
      )}

      {fullExport.isError && (
        <p className="mt-3 text-sm text-red-600">{fullExport.error.message}</p>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Consent Management Section (Art. 7)
// ---------------------------------------------------------------------------

const CONSENT_PURPOSES = [
  { key: "essential", label: "Essential Services", description: "Required for core functionality" },
  { key: "analytics", label: "Analytics", description: "Usage analytics to improve the platform" },
  { key: "marketing", label: "Marketing", description: "Product updates and promotional content" },
  { key: "ai_training", label: "AI Training", description: "Use data for AI model training" },
  { key: "third_party", label: "Third Party", description: "Share data with third-party integrations" },
] as const;

function ConsentSection() {
  const { data: consentsData, isLoading } = useActiveConsents();
  const recordConsent = useRecordConsent();

  const consentMap = new Map(
    (consentsData?.consents || []).map((c) => [c.purpose, c.granted])
  );

  const handleToggle = (purpose: string, currentlyGranted: boolean) => {
    recordConsent.mutate({
      purpose: purpose as "essential" | "analytics" | "marketing" | "ai_training" | "third_party",
      granted: !currentlyGranted,
      version: "1.0",
    });
  };

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-gray-900">Consent Management (Art. 7)</h2>
      <p className="mt-1 text-sm text-gray-500">
        Manage your consent preferences. Changes take effect immediately.
      </p>

      {isLoading && <p className="mt-3 text-sm text-gray-500">Loading consents...</p>}

      <div className="mt-4 divide-y divide-gray-100">
        {CONSENT_PURPOSES.map((purpose) => {
          const granted = consentMap.get(purpose.key) ?? false;
          return (
            <div key={purpose.key} className="flex items-center justify-between py-3">
              <div>
                <p className="text-sm font-medium text-gray-900">{purpose.label}</p>
                <p className="text-xs text-gray-500">{purpose.description}</p>
              </div>
              <button
                onClick={() => handleToggle(purpose.key, granted)}
                disabled={recordConsent.isPending || purpose.key === "essential"}
                className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ${
                  granted ? "bg-blue-600" : "bg-gray-200"
                } ${purpose.key === "essential" ? "cursor-not-allowed opacity-75" : ""}`}
                title={purpose.key === "essential" ? "Essential consent cannot be withdrawn" : undefined}
              >
                <span
                  className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ${
                    granted ? "translate-x-5" : "translate-x-0"
                  }`}
                />
              </button>
            </div>
          );
        })}
      </div>

      {recordConsent.isError && (
        <p className="mt-3 text-sm text-red-600">{recordConsent.error.message}</p>
      )}
    </div>
  );
}
