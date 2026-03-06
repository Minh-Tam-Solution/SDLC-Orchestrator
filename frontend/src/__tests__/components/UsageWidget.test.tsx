/**
 * UsageWidget Tests — Sprint 212 Track F
 *
 * Tests progress bar rendering, skeleton loading state,
 * upgrade CTA visibility, and null-data fallback.
 *
 * @module frontend/src/__tests__/components/UsageWidget.test
 * @sprint 212
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

// Mock global fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

import UsageWidget from "@/components/dashboard/UsageWidget";

function makeStats(overrides: Record<string, { current: number; limit: number; percent: number }> = {}) {
  return {
    tier: "starter",
    usage: {
      projects: { current: 2, limit: 5, percent: 40 },
      storage_mb: { current: 30.5, limit: 100, percent: 30.5 },
      gates_this_month: { current: 3, limit: 10, percent: 30 },
      members: { current: 1, limit: 3, percent: 33 },
      ...overrides,
    },
  };
}

describe("UsageWidget", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (window.localStorage.getItem as ReturnType<typeof vi.fn>).mockReturnValue("test-token");
  });

  it("shows skeleton placeholders while loading", () => {
    // Never resolve fetch so component stays in loading state
    mockFetch.mockReturnValue(new Promise(() => {}));
    render(<UsageWidget />);

    const skeleton = document.querySelector(".animate-pulse");
    expect(skeleton).toBeInTheDocument();
  });

  it("renders 4 progress rows when data loaded", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => makeStats(),
    });

    render(<UsageWidget />);

    await waitFor(() => {
      expect(screen.getByText("Projects")).toBeInTheDocument();
    });

    expect(screen.getByText("Storage")).toBeInTheDocument();
    expect(screen.getByText("Gates / Month")).toBeInTheDocument();
    expect(screen.getByText("Team Members")).toBeInTheDocument();
    expect(screen.getByText("Usage — STARTER Tier")).toBeInTheDocument();
  });

  it("shows Upgrade CTA when any bucket >= 80%", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () =>
        makeStats({ projects: { current: 4, limit: 5, percent: 85 } }),
    });

    render(<UsageWidget />);

    await waitFor(() => {
      expect(screen.getByText("Upgrade")).toBeInTheDocument();
    });

    const upgradeLink = screen.getByText("Upgrade");
    expect(upgradeLink.closest("a")).toHaveAttribute("href", "/pricing");
  });

  it("hides Upgrade CTA when all buckets < 80%", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => makeStats(),
    });

    render(<UsageWidget />);

    await waitFor(() => {
      expect(screen.getByText("Projects")).toBeInTheDocument();
    });

    expect(screen.queryByText("Upgrade")).not.toBeInTheDocument();
  });

  it("renders nothing when API returns non-ok response", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false });

    const { container } = render(<UsageWidget />);

    await waitFor(() => {
      expect(container.querySelector(".animate-pulse")).not.toBeInTheDocument();
    });

    expect(screen.queryByText("Projects")).not.toBeInTheDocument();
  });
});
