/**
 * TierBadge Tests — Sprint 212 Track A2
 *
 * Tests tier label display, color classes per tier,
 * size variants, and compact mode.
 *
 * @module frontend/src/__tests__/components/TierBadge.test
 * @sprint 212
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";

import { TierBadge } from "@/components/user/TierBadge";
import type { SubscriptionTier } from "@/components/user/TierBadge";

describe("TierBadge", () => {
  it("displays full tier name by default", () => {
    render(<TierBadge tier="enterprise" />);
    expect(screen.getByText("Enterprise")).toBeInTheDocument();
  });

  it("displays abbreviated label in compact variant", () => {
    render(<TierBadge tier="pro" variant="compact" />);
    expect(screen.getByText("PRO")).toBeInTheDocument();
    expect(screen.queryByText("Pro")).not.toBeInTheDocument();
  });

  const tierColorCases: { tier: SubscriptionTier; bgClass: string }[] = [
    { tier: "free", bgClass: "bg-gray-100" },
    { tier: "starter", bgClass: "bg-green-100" },
    { tier: "pro", bgClass: "bg-blue-100" },
    { tier: "enterprise", bgClass: "bg-purple-100" },
  ];

  it.each(tierColorCases)(
    "applies correct color class for $tier tier",
    ({ tier, bgClass }) => {
      const { container } = render(<TierBadge tier={tier} />);
      const badge = container.querySelector("span");
      expect(badge?.className).toContain(bgClass);
    }
  );

  it("renders sm size with smaller padding", () => {
    const { container } = render(<TierBadge tier="free" size="sm" />);
    const badge = container.querySelector("span");
    expect(badge?.className).toContain("px-1.5");
  });

  it("renders lg size with larger padding", () => {
    const { container } = render(<TierBadge tier="free" size="lg" />);
    const badge = container.querySelector("span");
    expect(badge?.className).toContain("px-3");
  });
});
