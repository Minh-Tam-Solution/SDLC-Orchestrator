/**
 * =========================================================================
 * useMediaQuery - Responsive Media Query Hook
 * SDLC Orchestrator - Sprint 54 Day 5
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * Status: ACTIVE - Sprint 54 Implementation
 * Authority: Frontend Team + CTO Approved
 *
 * Purpose:
 * - React hook for responsive media queries
 * - SSR-safe with proper hydration
 * - Pre-defined breakpoints matching Tailwind
 * - Type-safe breakpoint helpers
 *
 * Breakpoints (Tailwind defaults):
 * - sm: 640px
 * - md: 768px
 * - lg: 1024px
 * - xl: 1280px
 * - 2xl: 1536px
 * =========================================================================
 */

import { useState, useEffect } from "react";

// ============================================================================
// Types
// ============================================================================

type Breakpoint = "sm" | "md" | "lg" | "xl" | "2xl";

export const BREAKPOINTS: Record<Breakpoint, number> = {
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  "2xl": 1536,
};

// ============================================================================
// Main Hook
// ============================================================================

/**
 * Custom hook to check if a media query matches
 * @param query - CSS media query string
 * @returns boolean indicating if the query matches
 */
export function useMediaQuery(query: string): boolean {
  // Default to false for SSR
  const [matches, setMatches] = useState<boolean>(false);

  useEffect(() => {
    // Check if window is available (client-side)
    if (typeof window === "undefined") return;

    const mediaQueryList = window.matchMedia(query);

    // Set initial value
    setMatches(mediaQueryList.matches);

    // Create event listener
    const listener = (event: MediaQueryListEvent) => {
      setMatches(event.matches);
    };

    // Add listener
    mediaQueryList.addEventListener("change", listener);

    // Cleanup
    return () => {
      mediaQueryList.removeEventListener("change", listener);
    };
  }, [query]);

  return matches;
}

// ============================================================================
// Breakpoint Helpers
// ============================================================================

/**
 * Check if screen is at least the given breakpoint
 * @param breakpoint - Tailwind breakpoint name
 */
export function useBreakpoint(breakpoint: Breakpoint): boolean {
  return useMediaQuery(`(min-width: ${BREAKPOINTS[breakpoint]}px)`);
}

/**
 * Alias for useBreakpoint - check if screen is at least the given breakpoint
 * @param breakpoint - Tailwind breakpoint name
 */
export function useBreakpointUp(breakpoint: Breakpoint): boolean {
  return useBreakpoint(breakpoint);
}

/**
 * Check if screen is smaller than the given breakpoint
 * @param breakpoint - Tailwind breakpoint name
 */
export function useBreakpointDown(breakpoint: Breakpoint): boolean {
  return useMediaQuery(`(max-width: ${BREAKPOINTS[breakpoint] - 1}px)`);
}

/**
 * Check if screen is between two breakpoints
 * @param min - Minimum breakpoint (inclusive)
 * @param max - Maximum breakpoint (exclusive)
 */
export function useBreakpointBetween(min: Breakpoint, max: Breakpoint): boolean {
  return useMediaQuery(
    `(min-width: ${BREAKPOINTS[min]}px) and (max-width: ${BREAKPOINTS[max] - 1}px)`
  );
}

// ============================================================================
// Convenience Hooks
// ============================================================================

/**
 * Check if device is mobile (< md breakpoint)
 */
export function useIsMobile(): boolean {
  return useBreakpointDown("md");
}

/**
 * Check if device is tablet (md - lg breakpoint)
 */
export function useIsTablet(): boolean {
  return useBreakpointBetween("md", "lg");
}

/**
 * Check if device is desktop (>= lg breakpoint)
 */
export function useIsDesktop(): boolean {
  return useBreakpoint("lg");
}

/**
 * Check if device is large desktop (>= xl breakpoint)
 */
export function useIsLargeDesktop(): boolean {
  return useBreakpoint("xl");
}

/**
 * Get current breakpoint name
 */
export function useCurrentBreakpoint(): Breakpoint | "xs" {
  const is2xl = useBreakpoint("2xl");
  const isXl = useBreakpoint("xl");
  const isLg = useBreakpoint("lg");
  const isMd = useBreakpoint("md");
  const isSm = useBreakpoint("sm");

  if (is2xl) return "2xl";
  if (isXl) return "xl";
  if (isLg) return "lg";
  if (isMd) return "md";
  if (isSm) return "sm";
  return "xs";
}

// ============================================================================
// Screen Size Hook
// ============================================================================

interface WindowSize {
  width: number;
  height: number;
}

/**
 * Get current window dimensions
 * Updates on resize
 */
export function useWindowSize(): WindowSize {
  const [size, setSize] = useState<WindowSize>({
    width: typeof window !== "undefined" ? window.innerWidth : 0,
    height: typeof window !== "undefined" ? window.innerHeight : 0,
  });

  useEffect(() => {
    if (typeof window === "undefined") return;

    const handleResize = () => {
      setSize({
        width: window.innerWidth,
        height: window.innerHeight,
      });
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return size;
}

export default useMediaQuery;
