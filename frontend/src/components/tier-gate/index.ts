/**
 * Tier Gate UI Components — Sprint 184
 *
 * LockedFeature: Wraps any feature with a lock overlay when user tier is insufficient.
 * UpgradeModal:  Plan comparison + CTA modal shown on lock overlay click or 402 error.
 *
 * Usage:
 *   import { LockedFeature, UpgradeModal } from "@/components/tier-gate";
 */

export { LockedFeature } from "./LockedFeature";
export type { BackendTier } from "./LockedFeature";
export { UpgradeModal } from "./UpgradeModal";
