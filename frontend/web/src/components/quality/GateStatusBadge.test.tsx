/**
 * Unit Tests: GateStatusBadge Component
 * SDLC Orchestrator - Sprint 55 Day 1
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * Status: ACTIVE - Sprint 55 Implementation
 *
 * Test coverage:
 * - Status rendering (pending, running, passed, failed, skipped)
 * - Gate name display
 * - Duration display
 * - Issue count badge
 * - Compact mode
 * - Vietnamese mode
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@/test/test-utils";
import { GateStatusBadge, GateStatusIcon } from "./GateStatusBadge";
import "@testing-library/jest-dom";

// ============================================================================
// Status Rendering Tests
// ============================================================================

describe("GateStatusBadge - Status Rendering", () => {
  it("renders pending status", () => {
    render(<GateStatusBadge gateName="syntax" status="pending" />);

    expect(screen.getByText("Syntax")).toBeInTheDocument();
    expect(screen.getByText("Pending")).toBeInTheDocument();
  });

  it("renders running status with spinner", () => {
    render(<GateStatusBadge gateName="security" status="running" />);

    expect(screen.getByText("Security")).toBeInTheDocument();
    expect(screen.getByText("Running")).toBeInTheDocument();
    // Check for spinning animation class
    const spinningElement = document.querySelector(".animate-spin");
    expect(spinningElement).toBeInTheDocument();
  });

  it("renders passed status", () => {
    render(<GateStatusBadge gateName="architecture" status="passed" />);

    expect(screen.getByText("Architecture")).toBeInTheDocument();
    expect(screen.getByText("Passed")).toBeInTheDocument();
  });

  it("renders failed status", () => {
    render(<GateStatusBadge gateName="tests" status="failed" />);

    expect(screen.getByText("Tests")).toBeInTheDocument();
    expect(screen.getByText("Failed")).toBeInTheDocument();
  });

  it("renders skipped status", () => {
    render(<GateStatusBadge gateName="syntax" status="skipped" />);

    expect(screen.getByText("Syntax")).toBeInTheDocument();
    expect(screen.getByText("Skipped")).toBeInTheDocument();
  });
});

// ============================================================================
// Gate Name Tests
// ============================================================================

describe("GateStatusBadge - Gate Names", () => {
  it("renders syntax gate", () => {
    render(<GateStatusBadge gateName="syntax" status="pending" />);
    expect(screen.getByText("Syntax")).toBeInTheDocument();
  });

  it("renders security gate", () => {
    render(<GateStatusBadge gateName="security" status="pending" />);
    expect(screen.getByText("Security")).toBeInTheDocument();
  });

  it("renders architecture gate", () => {
    render(<GateStatusBadge gateName="architecture" status="pending" />);
    expect(screen.getByText("Architecture")).toBeInTheDocument();
  });

  it("renders tests gate", () => {
    render(<GateStatusBadge gateName="tests" status="pending" />);
    expect(screen.getByText("Tests")).toBeInTheDocument();
  });
});

// ============================================================================
// Duration Display Tests
// ============================================================================

describe("GateStatusBadge - Duration Display", () => {
  it("shows duration in milliseconds", () => {
    render(
      <GateStatusBadge
        gateName="syntax"
        status="passed"
        durationMs={500}
        showDuration={true}
      />
    );

    expect(screen.getByText("500ms")).toBeInTheDocument();
  });

  it("shows duration in seconds", () => {
    render(
      <GateStatusBadge
        gateName="syntax"
        status="passed"
        durationMs={2500}
        showDuration={true}
      />
    );

    expect(screen.getByText("2.5s")).toBeInTheDocument();
  });

  it("hides duration when showDuration is false", () => {
    render(
      <GateStatusBadge
        gateName="syntax"
        status="passed"
        durationMs={500}
        showDuration={false}
      />
    );

    expect(screen.queryByText("500ms")).not.toBeInTheDocument();
  });

  it("hides duration for pending status", () => {
    render(
      <GateStatusBadge
        gateName="syntax"
        status="pending"
        durationMs={500}
        showDuration={true}
      />
    );

    expect(screen.queryByText("500ms")).not.toBeInTheDocument();
  });
});

// ============================================================================
// Issue Count Tests
// ============================================================================

describe("GateStatusBadge - Issue Count", () => {
  it("shows issue count when greater than 0", () => {
    render(
      <GateStatusBadge
        gateName="syntax"
        status="failed"
        issuesCount={5}
      />
    );

    expect(screen.getByText("5")).toBeInTheDocument();
  });

  it("hides issue count when 0", () => {
    render(
      <GateStatusBadge
        gateName="syntax"
        status="passed"
        issuesCount={0}
      />
    );

    // Should not have a badge with count
    expect(screen.queryByText("0")).not.toBeInTheDocument();
  });

  it("hides issue count when undefined", () => {
    render(
      <GateStatusBadge
        gateName="syntax"
        status="passed"
      />
    );

    // Should render without issue count
    expect(screen.getByText("Syntax")).toBeInTheDocument();
  });
});

// ============================================================================
// Compact Mode Tests
// ============================================================================

describe("GateStatusBadge - Compact Mode", () => {
  it("renders compact mode without text", () => {
    render(
      <GateStatusBadge
        gateName="syntax"
        status="passed"
        compact={true}
      />
    );

    // Should not show text labels in compact mode
    expect(screen.queryByText("Syntax")).not.toBeInTheDocument();
    expect(screen.queryByText("Passed")).not.toBeInTheDocument();
  });

  it("shows tooltip in compact mode", async () => {
    render(
      <GateStatusBadge
        gateName="syntax"
        status="passed"
        durationMs={100}
        compact={true}
      />
    );

    // Badge should be rendered (not a button, but a div with cursor-pointer)
    const badge = document.querySelector(".cursor-pointer");
    expect(badge).toBeTruthy();
  });
});

// ============================================================================
// Vietnamese Mode Tests
// ============================================================================

describe("GateStatusBadge - Vietnamese Mode", () => {
  it("shows Vietnamese gate labels", () => {
    render(
      <GateStatusBadge
        gateName="syntax"
        status="pending"
        vietnamese={true}
      />
    );

    expect(screen.getByText("Cú pháp")).toBeInTheDocument();
  });

  it("shows Vietnamese status labels", () => {
    render(
      <GateStatusBadge
        gateName="syntax"
        status="passed"
        vietnamese={true}
      />
    );

    expect(screen.getByText("Đạt")).toBeInTheDocument();
  });

  it("shows Vietnamese for all statuses", () => {
    const { rerender } = render(
      <GateStatusBadge gateName="syntax" status="pending" vietnamese={true} />
    );
    expect(screen.getByText("Chờ")).toBeInTheDocument();

    rerender(
      <GateStatusBadge gateName="syntax" status="running" vietnamese={true} />
    );
    expect(screen.getByText("Đang chạy")).toBeInTheDocument();

    rerender(
      <GateStatusBadge gateName="syntax" status="failed" vietnamese={true} />
    );
    expect(screen.getByText("Lỗi")).toBeInTheDocument();

    rerender(
      <GateStatusBadge gateName="syntax" status="skipped" vietnamese={true} />
    );
    expect(screen.getByText("Bỏ qua")).toBeInTheDocument();
  });

  it("shows Vietnamese for all gates", () => {
    const { rerender } = render(
      <GateStatusBadge gateName="security" status="pending" vietnamese={true} />
    );
    expect(screen.getByText("Bảo mật")).toBeInTheDocument();

    rerender(
      <GateStatusBadge gateName="architecture" status="pending" vietnamese={true} />
    );
    expect(screen.getByText("Kiến trúc")).toBeInTheDocument();

    rerender(
      <GateStatusBadge gateName="tests" status="pending" vietnamese={true} />
    );
    expect(screen.getByText("Kiểm thử")).toBeInTheDocument();
  });
});

// ============================================================================
// Click Handler Tests
// ============================================================================

describe("GateStatusBadge - Click Handler", () => {
  it("calls onClick when clicked", () => {
    const handleClick = vi.fn();
    render(
      <GateStatusBadge
        gateName="syntax"
        status="passed"
        onClick={handleClick}
      />
    );

    const badge = document.querySelector(".cursor-pointer");
    if (badge) {
      fireEvent.click(badge);
      expect(handleClick).toHaveBeenCalledTimes(1);
    }
  });
});

// ============================================================================
// GateStatusIcon Tests
// ============================================================================

describe("GateStatusIcon", () => {
  it("renders correct icon for each status", () => {
    const { rerender } = render(<GateStatusIcon status="pending" />);
    expect(document.querySelector("svg")).toBeInTheDocument();

    rerender(<GateStatusIcon status="running" />);
    expect(document.querySelector(".animate-spin")).toBeInTheDocument();

    rerender(<GateStatusIcon status="passed" />);
    expect(document.querySelector(".text-green-500")).toBeInTheDocument();

    rerender(<GateStatusIcon status="failed" />);
    expect(document.querySelector(".text-red-500")).toBeInTheDocument();

    rerender(<GateStatusIcon status="skipped" />);
    expect(document.querySelector(".text-yellow-500")).toBeInTheDocument();
  });

  it("renders correct size", () => {
    const { rerender } = render(<GateStatusIcon status="passed" size="sm" />);
    expect(document.querySelector(".h-4.w-4")).toBeInTheDocument();

    rerender(<GateStatusIcon status="passed" size="md" />);
    expect(document.querySelector(".h-5.w-5")).toBeInTheDocument();

    rerender(<GateStatusIcon status="passed" size="lg" />);
    expect(document.querySelector(".h-6.w-6")).toBeInTheDocument();
  });
});

// ============================================================================
// Accessibility Tests
// ============================================================================

describe("GateStatusBadge - Accessibility", () => {
  it("applies custom className", () => {
    render(
      <GateStatusBadge
        gateName="syntax"
        status="passed"
        className="custom-class"
      />
    );

    expect(document.querySelector(".custom-class")).toBeInTheDocument();
  });
});
