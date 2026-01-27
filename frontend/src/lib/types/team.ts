/**
 * Team & TeamMember Types - Next.js App Router
 * @module frontend/src/lib/types/team
 * @status Sprint 84 - Teams & Organizations UI
 * @description Type definitions for Teams and TeamMember management
 * @note Based on backend schemas from Sprint 71 (Teams Backend API)
 * @see backend/app/schemas/team.py
 */

// =========================================================================
// Team Roles & Member Types (SASE Compliance)
// =========================================================================

/**
 * Team member roles per SASE specification
 * - owner: SE4H Coach (VCR authority, full control)
 * - admin: SE4H Coach (member management, limited control)
 * - member: SE4H Member (implementation)
 * - ai_agent: SE4A Executor (autonomous tasks)
 */
export type TeamRole = "owner" | "admin" | "member" | "ai_agent";

/**
 * Member types for SASE constraints
 * - AI agents cannot be owner or admin (CTO R1/R2)
 */
export type MemberType = "human" | "ai_agent";

/**
 * SASE role mapping for display
 */
export type SASERole = "SE4H_Coach" | "SE4H_Member" | "SE4A_Executor";

/**
 * Agentic maturity levels (L0-L3)
 */
export type AgenticMaturity = "L0" | "L1" | "L2" | "L3";

// =========================================================================
// Team Settings
// =========================================================================

export interface TeamSASEConfig {
  agentic_maturity?: AgenticMaturity;
  mentor_scripts?: string[];
  briefing_templates?: string[];
  crp_threshold?: number; // 0.0 - 1.0, default: 0.7
  auto_approve_mrp?: boolean;
}

export interface TeamSettings {
  default_gate_approvers?: string[];
  notification_channel?: "slack" | "email" | "webhook" | null;
  webhook_url?: string | null;
  auto_assign_projects?: boolean;
  mentor_scripts?: string[];
  briefing_templates?: string[];
  agentic_maturity?: AgenticMaturity;
  crp_threshold?: number;
  auto_approve_mrp?: boolean;
}

// =========================================================================
// Team Model
// =========================================================================

export interface Team {
  id: string;
  organization_id: string;
  name: string;
  slug: string;
  description: string | null;
  settings: TeamSettings;
  members_count: number;
  human_members_count: number;
  ai_agents_count: number;
  projects_count: number;
  created_at: string;
  updated_at: string;
}

export interface TeamDetail extends Team {
  organization_name?: string;
  agentic_maturity: AgenticMaturity;
  crp_threshold: number;
  auto_approve_mrp: boolean;
}

// =========================================================================
// Team CRUD Requests
// =========================================================================

export interface TeamCreate {
  organization_id: string;
  name: string;
  slug: string;
  description?: string | null;
  settings?: TeamSettings;
}

export interface TeamUpdate {
  name?: string;
  description?: string | null;
  settings?: Partial<TeamSettings>;
}

// =========================================================================
// Team Statistics
// =========================================================================

export interface TeamStatistics {
  team_id: string;
  team_name: string;
  total_members: number;
  human_members: number;
  ai_agents: number;
  owners_count: number;
  admins_count: number;
  total_projects: number;
  active_projects: number;
  agentic_maturity: AgenticMaturity;
}

// =========================================================================
// TeamMember Model
// =========================================================================

export interface TeamMember {
  id: string;
  team_id: string;
  user_id: string;
  role: TeamRole;
  member_type: MemberType;
  sase_role: SASERole;
  joined_at: string | null;
  created_at: string;
  updated_at: string;
  user_email: string | null;
  user_name: string | null;
  user_avatar_url: string | null;
}

export interface TeamMemberWithPermissions extends TeamMember {
  is_owner: boolean;
  is_admin: boolean;
  is_admin_or_owner: boolean;
  is_ai_agent: boolean;
  is_human: boolean;
  is_coach: boolean;
  is_executor: boolean;
  can_manage_members: boolean;
  can_approve_vcr: boolean;
  can_modify_settings: boolean;
  can_approve_sprint_gate: boolean;
  can_create_sprint: boolean;
  can_manage_backlog: boolean;
}

// =========================================================================
// TeamMember CRUD Requests
// =========================================================================

export interface TeamMemberAdd {
  /** User UUID to add (optional if email provided) */
  user_id?: string;
  /** User email to add (optional if user_id provided) - Sprint 105 */
  email?: string;
  role?: TeamRole;
  member_type?: MemberType;
}

export interface TeamMemberRoleUpdate {
  role: TeamRole;
}

// =========================================================================
// Paginated Responses
// =========================================================================

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

export type TeamListResponse = PaginatedResponse<Team>;
export type TeamMemberListResponse = PaginatedResponse<TeamMember>;

// =========================================================================
// Query Parameters
// =========================================================================

export interface TeamListParams {
  skip?: number;
  limit?: number;
  organization_id?: string;
}

export interface TeamMemberListParams {
  skip?: number;
  limit?: number;
}

// =========================================================================
// Role Metadata for UI
// =========================================================================

export const TEAM_ROLE_META: Record<TeamRole, { label: string; color: string; description: string }> = {
  owner: {
    label: "Owner",
    color: "bg-purple-100 text-purple-800",
    description: "Full control, VCR authority (SE4H Coach)",
  },
  admin: {
    label: "Admin",
    color: "bg-blue-100 text-blue-800",
    description: "Member management, gate approval (SE4H Coach)",
  },
  member: {
    label: "Member",
    color: "bg-green-100 text-green-800",
    description: "Implementation tasks (SE4H Member)",
  },
  ai_agent: {
    label: "AI Agent",
    color: "bg-orange-100 text-orange-800",
    description: "Autonomous execution (SE4A Executor)",
  },
};

export const MEMBER_TYPE_META: Record<MemberType, { label: string; color: string }> = {
  human: { label: "Human", color: "bg-green-100 text-green-800" },
  ai_agent: { label: "AI Agent", color: "bg-orange-100 text-orange-800" },
};

export const SASE_ROLE_META: Record<SASERole, { label: string; description: string }> = {
  SE4H_Coach: {
    label: "SE4H Coach",
    description: "Human coach with governance authority",
  },
  SE4H_Member: {
    label: "SE4H Member",
    description: "Human team member",
  },
  SE4A_Executor: {
    label: "SE4A Executor",
    description: "AI agent executor",
  },
};

export const AGENTIC_MATURITY_META: Record<AgenticMaturity, { label: string; description: string; color: string }> = {
  L0: {
    label: "L0 - Manual",
    description: "No AI agents, fully human team",
    color: "bg-gray-100 text-gray-800",
  },
  L1: {
    label: "L1 - Assisted",
    description: "AI assists with suggestions, human reviews all",
    color: "bg-blue-100 text-blue-800",
  },
  L2: {
    label: "L2 - Collaborative",
    description: "AI and humans collaborate, AI can execute low-risk tasks",
    color: "bg-yellow-100 text-yellow-800",
  },
  L3: {
    label: "L3 - Autonomous",
    description: "AI operates autonomously within defined boundaries",
    color: "bg-green-100 text-green-800",
  },
};

// =========================================================================
// Helper Functions
// =========================================================================

/**
 * Get SASE role from team role and member type
 */
export function getSASERole(role: TeamRole, memberType: MemberType): SASERole {
  if (memberType === "ai_agent") return "SE4A_Executor";
  if (role === "owner" || role === "admin") return "SE4H_Coach";
  return "SE4H_Member";
}

/**
 * Check if role change is valid per SASE constraints
 * AI agents cannot be owner or admin
 */
export function isValidRoleAssignment(role: TeamRole, memberType: MemberType): boolean {
  if (memberType === "ai_agent" && (role === "owner" || role === "admin")) {
    return false;
  }
  return true;
}

/**
 * Format team slug from name
 */
export function formatTeamSlug(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .substring(0, 100);
}

/**
 * Get role badge color class
 */
export function getRoleBadgeClass(role: TeamRole): string {
  return TEAM_ROLE_META[role]?.color ?? "bg-gray-100 text-gray-800";
}

/**
 * Get member type icon
 */
export function getMemberTypeIcon(memberType: MemberType): string {
  return memberType === "ai_agent" ? "Bot" : "User";
}
