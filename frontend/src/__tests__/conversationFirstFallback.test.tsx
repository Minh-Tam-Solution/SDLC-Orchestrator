/**
 * ConversationFirstFallback Tests — Sprint 212 Track A2e
 *
 * Tests OTT channel button rendering and fallback "Contact admin" message.
 *
 * @module frontend/src/__tests__/conversationFirstFallback.test
 * @sprint 212
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";

// Mock next/link
vi.mock("next/link", () => ({
  default: ({ children, href, ...props }: { children: React.ReactNode; href: string; [k: string]: unknown }) => (
    <a href={href} {...props}>{children}</a>
  ),
}));

describe("ConversationFirstFallback", () => {
  it("renders 'Contact admin' message when no OTT channels are configured", async () => {
    // No env vars set — buildChannels() returns empty array
    const mod = await import("@/components/dashboard/ConversationFirstFallback");
    const ConversationFirstFallback = mod.default;

    render(<ConversationFirstFallback />);

    expect(
      screen.getByText(/No OTT channel configured/i)
    ).toBeInTheDocument();
    expect(screen.getByText("Feature Moved to Conversation-First")).toBeInTheDocument();
  });

  it("renders channel buttons when env vars are set", async () => {
    // Stub env vars before dynamic import so buildChannels() picks them up
    vi.stubEnv("NEXT_PUBLIC_TELEGRAM_BOT_URL", "https://t.me/testbot");
    vi.stubEnv("NEXT_PUBLIC_ZALO_OA_URL", "https://zalo.me/test");

    // Reset module cache so buildChannels() re-runs with new env vars
    vi.resetModules();

    // Re-mock next/link after resetModules
    vi.doMock("next/link", () => ({
      default: ({ children, href, ...props }: { children: React.ReactNode; href: string; [k: string]: unknown }) => (
        <a href={href} {...props}>{children}</a>
      ),
    }));

    const mod = await import("@/components/dashboard/ConversationFirstFallback");
    const ConversationFirstFallback = mod.default;

    render(<ConversationFirstFallback />);

    expect(screen.getByText("Open Telegram")).toBeInTheDocument();
    expect(screen.getByText("Open Zalo")).toBeInTheDocument();
    // "Contact admin" message should NOT appear when channels are configured
    expect(screen.queryByText(/No OTT channel configured/i)).not.toBeInTheDocument();

    vi.unstubAllEnvs();
  });
});
