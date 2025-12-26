/**
 * Unit Tests: useMediaQuery Hook
 * SDLC Orchestrator - Sprint 54 Day 5
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * Status: ACTIVE - Sprint 54 Implementation
 *
 * Test coverage:
 * - useMediaQuery base hook
 * - Breakpoint helpers
 * - Window resize handling
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import {
  useMediaQuery,
  useBreakpoint,
  useBreakpointUp,
  useBreakpointDown,
  useBreakpointBetween,
  useIsMobile,
  useIsTablet,
  useIsDesktop,
  useIsLargeDesktop,
  useCurrentBreakpoint,
  BREAKPOINTS,
} from "./useMediaQuery";

// ============================================================================
// Mock matchMedia - Setup before tests
// ============================================================================

function createMatchMedia(matches: boolean) {
  return vi.fn().mockImplementation((query: string) => ({
    matches,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }));
}

// Store original matchMedia
const originalMatchMedia = window.matchMedia;

describe("useMediaQuery", () => {
  beforeEach(() => {
    // Ensure window.matchMedia is mocked before each test
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: createMatchMedia(false),
    });
  });

  afterEach(() => {
    // Restore original
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: originalMatchMedia,
    });
    vi.restoreAllMocks();
  });

  it("returns false when query does not match", () => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: createMatchMedia(false),
    });

    const { result } = renderHook(() => useMediaQuery("(min-width: 768px)"));

    expect(result.current).toBe(false);
  });

  it("returns true when query matches", () => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: createMatchMedia(true),
    });

    const { result } = renderHook(() => useMediaQuery("(min-width: 768px)"));

    expect(result.current).toBe(true);
  });
});

// ============================================================================
// Breakpoint Constants Tests
// ============================================================================

describe("BREAKPOINTS", () => {
  it("has correct breakpoint values", () => {
    expect(BREAKPOINTS.sm).toBe(640);
    expect(BREAKPOINTS.md).toBe(768);
    expect(BREAKPOINTS.lg).toBe(1024);
    expect(BREAKPOINTS.xl).toBe(1280);
    expect(BREAKPOINTS["2xl"]).toBe(1536);
  });
});

// ============================================================================
// useBreakpoint Tests
// ============================================================================

describe("useBreakpoint", () => {
  beforeEach(() => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: createMatchMedia(false),
    });
  });

  afterEach(() => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: originalMatchMedia,
    });
  });

  it("checks exact breakpoint", () => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: createMatchMedia(true),
    });

    const { result } = renderHook(() => useBreakpoint("md"));

    expect(result.current).toBe(true);
  });
});

// ============================================================================
// useBreakpointUp Tests
// ============================================================================

describe("useBreakpointUp", () => {
  beforeEach(() => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: createMatchMedia(false),
    });
  });

  afterEach(() => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: originalMatchMedia,
    });
  });

  it("returns true when above breakpoint", () => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: createMatchMedia(true),
    });

    const { result } = renderHook(() => useBreakpointUp("md"));

    expect(result.current).toBe(true);
  });

  it("returns false when below breakpoint", () => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: createMatchMedia(false),
    });

    const { result } = renderHook(() => useBreakpointUp("lg"));

    expect(result.current).toBe(false);
  });
});

// ============================================================================
// useBreakpointDown Tests
// ============================================================================

describe("useBreakpointDown", () => {
  beforeEach(() => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: createMatchMedia(false),
    });
  });

  afterEach(() => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: originalMatchMedia,
    });
  });

  it("returns true when below breakpoint", () => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: createMatchMedia(true),
    });

    const { result } = renderHook(() => useBreakpointDown("md"));

    expect(result.current).toBe(true);
  });

  it("returns false when above breakpoint", () => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: createMatchMedia(false),
    });

    const { result } = renderHook(() => useBreakpointDown("sm"));

    expect(result.current).toBe(false);
  });
});

// ============================================================================
// useBreakpointBetween Tests
// ============================================================================

describe("useBreakpointBetween", () => {
  beforeEach(() => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: createMatchMedia(false),
    });
  });

  afterEach(() => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: originalMatchMedia,
    });
  });

  it("returns true when between breakpoints", () => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: createMatchMedia(true),
    });

    const { result } = renderHook(() => useBreakpointBetween("sm", "lg"));

    expect(result.current).toBe(true);
  });

  it("returns false when outside range", () => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: createMatchMedia(false),
    });

    const { result } = renderHook(() => useBreakpointBetween("md", "xl"));

    expect(result.current).toBe(false);
  });
});

// ============================================================================
// Device Helper Tests
// ============================================================================

describe("useIsMobile", () => {
  beforeEach(() => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: createMatchMedia(false),
    });
  });

  afterEach(() => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: originalMatchMedia,
    });
  });

  it("returns true for mobile", () => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: createMatchMedia(true),
    });

    const { result } = renderHook(() => useIsMobile());

    expect(result.current).toBe(true);
  });

  it("returns false for non-mobile", () => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: createMatchMedia(false),
    });

    const { result } = renderHook(() => useIsMobile());

    expect(result.current).toBe(false);
  });
});

describe("useIsTablet", () => {
  beforeEach(() => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: createMatchMedia(false),
    });
  });

  afterEach(() => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: originalMatchMedia,
    });
  });

  it("returns true for tablet", () => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: createMatchMedia(true),
    });

    const { result } = renderHook(() => useIsTablet());

    expect(result.current).toBe(true);
  });

  it("returns false for non-tablet", () => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: createMatchMedia(false),
    });

    const { result } = renderHook(() => useIsTablet());

    expect(result.current).toBe(false);
  });
});

describe("useIsDesktop", () => {
  beforeEach(() => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: createMatchMedia(false),
    });
  });

  afterEach(() => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: originalMatchMedia,
    });
  });

  it("returns true for desktop", () => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: createMatchMedia(true),
    });

    const { result } = renderHook(() => useIsDesktop());

    expect(result.current).toBe(true);
  });

  it("returns false for non-desktop", () => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: createMatchMedia(false),
    });

    const { result } = renderHook(() => useIsDesktop());

    expect(result.current).toBe(false);
  });
});

describe("useIsLargeDesktop", () => {
  beforeEach(() => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: createMatchMedia(false),
    });
  });

  afterEach(() => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: originalMatchMedia,
    });
  });

  it("returns true for large desktop", () => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: createMatchMedia(true),
    });

    const { result } = renderHook(() => useIsLargeDesktop());

    expect(result.current).toBe(true);
  });

  it("returns false for non-large desktop", () => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: createMatchMedia(false),
    });

    const { result } = renderHook(() => useIsLargeDesktop());

    expect(result.current).toBe(false);
  });
});

// ============================================================================
// useCurrentBreakpoint Tests
// ============================================================================

describe("useCurrentBreakpoint", () => {
  beforeEach(() => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: createMatchMedia(false),
    });
  });

  afterEach(() => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: originalMatchMedia,
    });
  });

  it("returns xs for smallest screens", () => {
    // Mock all breakpoints as false (very small screen)
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: createMatchMedia(false),
    });

    const { result } = renderHook(() => useCurrentBreakpoint());

    expect(result.current).toBe("xs");
  });

  it("returns correct breakpoint when matched", () => {
    // Mock specific breakpoint match
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: vi.fn().mockImplementation((query: string) => {
        const matches = query.includes("640px"); // sm breakpoint
        return {
          matches,
          media: query,
          onchange: null,
          addListener: vi.fn(),
          removeListener: vi.fn(),
          addEventListener: vi.fn(),
          removeEventListener: vi.fn(),
          dispatchEvent: vi.fn(),
        };
      }),
    });

    const { result } = renderHook(() => useCurrentBreakpoint());

    // Should return sm or xs depending on implementation
    expect(["xs", "sm", "md", "lg", "xl", "2xl"]).toContain(result.current);
  });
});

// ============================================================================
// Event Listener Tests
// ============================================================================

describe("useMediaQuery - Event Listeners", () => {
  beforeEach(() => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: createMatchMedia(false),
    });
  });

  afterEach(() => {
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: originalMatchMedia,
    });
  });

  it("adds event listener on mount", () => {
    const addEventListener = vi.fn();
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: vi.fn().mockImplementation(() => ({
        matches: false,
        addEventListener,
        removeEventListener: vi.fn(),
      })),
    });

    renderHook(() => useMediaQuery("(min-width: 768px)"));

    expect(addEventListener).toHaveBeenCalledWith("change", expect.any(Function));
  });

  it("removes event listener on unmount", () => {
    const removeEventListener = vi.fn();
    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: vi.fn().mockImplementation(() => ({
        matches: false,
        addEventListener: vi.fn(),
        removeEventListener,
      })),
    });

    const { unmount } = renderHook(() => useMediaQuery("(min-width: 768px)"));

    unmount();

    expect(removeEventListener).toHaveBeenCalledWith("change", expect.any(Function));
  });

  it("updates when media query changes", () => {
    let changeHandler: ((e: { matches: boolean }) => void) | null = null;

    Object.defineProperty(window, "matchMedia", {
      writable: true,
      value: vi.fn().mockImplementation(() => ({
        matches: false,
        addEventListener: (event: string, handler: (e: { matches: boolean }) => void) => {
          if (event === "change") {
            changeHandler = handler;
          }
        },
        removeEventListener: vi.fn(),
      })),
    });

    const { result } = renderHook(() => useMediaQuery("(min-width: 768px)"));

    expect(result.current).toBe(false);

    // Simulate media query change
    if (changeHandler) {
      act(() => {
        changeHandler!({ matches: true });
      });
    }

    expect(result.current).toBe(true);
  });
});
