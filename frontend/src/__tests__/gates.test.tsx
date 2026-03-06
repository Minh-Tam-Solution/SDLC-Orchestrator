/**
 * Gates Page Tests — Sprint 212 Track A2b
 *
 * Tests gate list rendering, status badge display, and empty state.
 *
 * @module frontend/src/__tests__/gates.test
 * @sprint 212
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { Gate } from "@/lib/api";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
}));

// Mock next/link
vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

// Controlled mock return values
const mockGatesData = { data: undefined as { items: Gate[]; total: number; page: number; page_size: number; pages: number } | undefined, isLoading: false, error: null };
const mockProjectsData = { data: undefined as unknown, isLoading: false, error: null };

vi.mock("@/hooks/useGates", () => ({
  useGates: () => mockGatesData,
}));

vi.mock("@/hooks/useProjects", () => ({
  useProjects: () => mockProjectsData,
}));

import GatesPage from "@/app/app/gates/page";

function makeGate(overrides: Partial<Gate>): Gate {
  return {
    id: "gate-1",
    project_id: "proj-1",
    gate_name: "G1 Consultation",
    gate_type: "CONSULTATION",
    stage: "01",
    status: "DRAFT",
    description: "Test gate",
    exit_criteria: [],
    created_by: "user-1",
    created_at: "2026-01-15T10:00:00Z",
    updated_at: "2026-01-15T10:00:00Z",
    approved_at: null,
    approvals: [],
    evidence_count: 0,
    policy_violations: [],
    ...overrides,
  };
}

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  );
}

describe("GatesPage", () => {
  beforeEach(() => {
    mockGatesData.data = undefined;
    mockGatesData.isLoading = false;
    mockGatesData.error = null;
    mockProjectsData.data = undefined;
  });

  it("renders gate items when data is available", () => {
    mockGatesData.data = {
      items: [
        makeGate({ id: "g1", gate_name: "G1 Consultation", status: "APPROVED", stage: "01" }),
        makeGate({ id: "g2", gate_name: "G2 Design Ready", status: "REJECTED", stage: "02" }),
      ],
      total: 2, page: 1, page_size: 100, pages: 1,
    };

    renderWithProviders(<GatesPage />);

    // getAllByText because gate names appear in both GateCard and EvaluationRow
    expect(screen.getAllByText("G1 Consultation").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("G2 Design Ready").length).toBeGreaterThanOrEqual(1);
  });

  it("displays correct status badges (APPROVED, REJECTED, DRAFT)", () => {
    mockGatesData.data = {
      items: [
        makeGate({ id: "g1", gate_name: "Approved Gate", status: "APPROVED" }),
        makeGate({ id: "g2", gate_name: "Rejected Gate", status: "REJECTED" }),
        makeGate({ id: "g3", gate_name: "Draft Gate", status: "DRAFT" }),
      ],
      total: 3, page: 1, page_size: 100, pages: 1,
    };

    renderWithProviders(<GatesPage />);

    // Status text rendered — status uses .replace("_", " ") so check rendered text
    const approvedBadges = screen.getAllByText("APPROVED");
    expect(approvedBadges.length).toBeGreaterThanOrEqual(1);

    const rejectedBadges = screen.getAllByText("REJECTED");
    expect(rejectedBadges.length).toBeGreaterThanOrEqual(1);

    const draftBadges = screen.getAllByText("DRAFT");
    expect(draftBadges.length).toBeGreaterThanOrEqual(1);
  });

  it("shows empty state message when no gates exist", () => {
    mockGatesData.data = {
      items: [],
      total: 0, page: 1, page_size: 100, pages: 0,
    };

    renderWithProviders(<GatesPage />);

    expect(screen.getByText("No gates found")).toBeInTheDocument();
  });
});
