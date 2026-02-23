/**
 * User Tier Hook
 *
 * Sprint: 146 - Organization Access Control
 * Reference: ADR-047-Organization-Invitation-System.md
 *
 * Provides the user's effective subscription tier based on all organizations.
 * The effective tier is the HIGHEST tier among all organizations the user belongs to.
 *
 * Tier Hierarchy:
 * - enterprise (4): Highest priority
 * - pro (3)
 * - starter (2)
 * - free (1): Lowest priority
 */

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { SubscriptionTier } from "@/components/user/TierBadge";

/** User organization membership */
export interface UserOrganization {
  id: string;
  name: string;
  slug: string;
  plan: SubscriptionTier;
  role: "owner" | "admin" | "member";
  joined_at: string;
}

/** User profile with tier information */
export interface UserProfile {
  id: string;
  email: string;
  name: string;
  effective_tier: SubscriptionTier;
  organizations: UserOrganization[];
}

/** Tier rank for comparison */
const TIER_RANK: Record<SubscriptionTier, number> = {
  enterprise: 4,
  pro: 3,
  starter: 2,
  free: 1,
};

/**
 * Calculate effective tier from a list of organizations
 *
 * @param organizations - List of user's organizations
 * @returns The highest tier among all organizations
 */
export function calculateEffectiveTier(
  organizations: UserOrganization[]
): SubscriptionTier {
  if (!organizations || organizations.length === 0) {
    return "free";
  }

  let maxTier: SubscriptionTier = "free";
  let maxRank = 1;

  for (const org of organizations) {
    const rank = TIER_RANK[org.plan] ?? 1;
    if (rank > maxRank) {
      maxRank = rank;
      maxTier = org.plan;

      // Early exit optimization (CTO MANDATORY CONDITION #3)
      // Enterprise is highest tier, no need to check further
      if (maxRank === 4) {
        break;
      }
    }
  }

  return maxTier;
}

/**
 * Hook to get the current user's profile with tier information
 *
 * @returns User profile with effective tier and organizations
 *
 * @example
 * ```tsx
 * const { profile, effectiveTier, organizations, isLoading } = useUserTier();
 *
 * return (
 *   <div>
 *     <TierBadge tier={effectiveTier} />
 *     <p>You belong to {organizations.length} organizations</p>
 *   </div>
 * );
 * ```
 */
export function useUserTier() {
  const {
    data: profile,
    isLoading,
    error,
    refetch,
  } = useQuery<UserProfile>({
    queryKey: ["user-profile"],
    queryFn: async (): Promise<UserProfile> => {
      const response = await api.get<UserProfile>("/auth/me");
      return response.data;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Extract organizations
  const organizations: UserOrganization[] = profile?.organizations ?? [];

  // Calculate effective tier (or use from API if available)
  const effectiveTier: SubscriptionTier =
    profile?.effective_tier ?? calculateEffectiveTier(organizations);

  // Group organizations by tier
  const organizationsByTier = organizations.reduce(
    (acc, org) => {
      if (!acc[org.plan]) {
        acc[org.plan] = [];
      }
      acc[org.plan].push(org);
      return acc;
    },
    {} as Record<SubscriptionTier, UserOrganization[]>
  );

  // Count organizations by tier
  const tierCounts = {
    enterprise: organizationsByTier.enterprise?.length ?? 0,
    pro: organizationsByTier.pro?.length ?? 0,
    starter: organizationsByTier.starter?.length ?? 0,
    free: organizationsByTier.free?.length ?? 0,
  };

  return {
    // Data
    profile,
    effectiveTier,
    organizations,
    organizationsByTier,
    tierCounts,

    // Computed
    hasEnterprise: tierCounts.enterprise > 0,
    hasPro: tierCounts.pro > 0 || tierCounts.enterprise > 0,
    organizationCount: organizations.length,

    // States
    isLoading,
    error,
    refetch,
  };
}

export default useUserTier;
