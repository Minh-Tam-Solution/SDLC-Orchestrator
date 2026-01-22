/**
 * Team Detail Page - SDLC Orchestrator Dashboard
 *
 * @module frontend/src/app/app/teams/[id]/page
 * @description Team detail with members management
 * @sdlc SDLC 5.1.3 Framework - Sprint 84 (Teams & Organizations UI)
 * @status Sprint 84 - CTO APPROVED (January 20, 2026)
 */

"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  useTeam,
  useTeamStats,
  useTeamMembers,
  useDeleteTeam,
  useUpdateTeam,
  useAddTeamMember,
  useRemoveTeamMember,
  useUpdateMemberRole,
  type TeamMember,
  type TeamUpdate,
} from "@/hooks/useTeams";
import { useAuth } from "@/hooks/useAuth";
import {
  TEAM_ROLE_META,
  AGENTIC_MATURITY_META,
  type TeamRole,
  type AgenticMaturity,
  type TeamSettings,
} from "@/lib/types/team";

// =============================================================================
// Icons
// =============================================================================

function ArrowLeftIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
    </svg>
  );
}

function PencilIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0 1 15.75 21H5.25A2.25 2.25 0 0 1 3 18.75V8.25A2.25 2.25 0 0 1 5.25 6H10" />
    </svg>
  );
}

function TrashIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
    </svg>
  );
}

function UserPlusIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M18 7.5v3m0 0v3m0-3h3m-3 0h-3m-2.25-4.125a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0ZM3 19.235v-.11a6.375 6.375 0 0 1 12.75 0v.109A12.318 12.318 0 0 1 9.374 21c-2.331 0-4.512-.645-6.374-1.766Z" />
    </svg>
  );
}

function UsersIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-3.07M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0Zm8.25 2.25a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z" />
    </svg>
  );
}

function FolderIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12.75V12A2.25 2.25 0 0 1 4.5 9.75h15A2.25 2.25 0 0 1 21.75 12v.75m-8.69-6.44-2.12-2.12a1.5 1.5 0 0 0-1.061-.44H4.5A2.25 2.25 0 0 0 2.25 6v12a2.25 2.25 0 0 0 2.25 2.25h15A2.25 2.25 0 0 0 21.75 18V9a2.25 2.25 0 0 0-2.25-2.25h-5.379a1.5 1.5 0 0 1-1.06-.44Z" />
    </svg>
  );
}

function XMarkIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
    </svg>
  );
}

function BotIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 0 1-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 0 1 4.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0 1 12 15a9.065 9.065 0 0 0-6.23-.693L5 14.5m14.8.8 1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0 1 12 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
    </svg>
  );
}

function EllipsisVerticalIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5ZM12 12.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5ZM12 18.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5Z" />
    </svg>
  );
}

// =============================================================================
// Components
// =============================================================================

function StatCard({
  label,
  value,
  icon: Icon,
  color,
}: {
  label: string;
  value: number | string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
}) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <div className="flex items-center gap-3">
        <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${color}`}>
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          <p className="text-sm text-gray-500">{label}</p>
        </div>
      </div>
    </div>
  );
}

function RoleBadge({ role }: { role: TeamRole }) {
  const meta = TEAM_ROLE_META[role];
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${meta.color}`}>
      {meta.label}
    </span>
  );
}

function MemberRow({
  member,
  teamId,
  canManage,
}: {
  member: TeamMember;
  teamId: string;
  canManage: boolean;
}) {
  const [showMenu, setShowMenu] = useState(false);
  const removeMember = useRemoveTeamMember(teamId);
  const updateRole = useUpdateMemberRole(teamId);

  const handleRemove = async () => {
    if (confirm(`Remove ${member.user_name || member.user_email} from team?`)) {
      await removeMember.mutateAsync(member.user_id);
    }
    setShowMenu(false);
  };

  const handleRoleChange = async (newRole: TeamRole) => {
    await updateRole.mutateAsync({ userId: member.user_id, data: { role: newRole } });
    setShowMenu(false);
  };

  return (
    <tr className="border-b border-gray-100 last:border-0">
      <td className="py-3 pr-4">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gray-100">
            {member.member_type === "ai_agent" ? (
              <BotIcon className="h-4 w-4 text-orange-600" />
            ) : (
              <span className="text-sm font-medium text-gray-600">
                {(member.user_name || member.user_email || "?")[0].toUpperCase()}
              </span>
            )}
          </div>
          <div>
            <p className="font-medium text-gray-900">
              {member.user_name || "Unknown User"}
            </p>
            <p className="text-sm text-gray-500">{member.user_email}</p>
          </div>
        </div>
      </td>
      <td className="py-3 px-4">
        <RoleBadge role={member.role} />
      </td>
      <td className="py-3 px-4 text-sm text-gray-500">
        {member.sase_role.replace("_", " ")}
      </td>
      <td className="py-3 px-4 text-sm text-gray-500">
        {member.joined_at
          ? new Date(member.joined_at).toLocaleDateString("vi-VN")
          : "N/A"}
      </td>
      <td className="py-3 pl-4">
        {canManage && (
          <div className="relative">
            <button
              onClick={() => setShowMenu(!showMenu)}
              className="rounded p-1 hover:bg-gray-100"
            >
              <EllipsisVerticalIcon className="h-5 w-5 text-gray-400" />
            </button>

            {showMenu && (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setShowMenu(false)} />
                <div className="absolute right-0 z-20 mt-1 w-48 rounded-lg border border-gray-200 bg-white py-1 shadow-lg">
                  <div className="px-3 py-1.5 text-xs font-medium text-gray-500 uppercase">
                    Change Role
                  </div>
                  {(["owner", "admin", "member"] as TeamRole[]).map((role) => (
                    <button
                      key={role}
                      onClick={() => handleRoleChange(role)}
                      disabled={member.role === role || member.member_type === "ai_agent" && (role === "owner" || role === "admin")}
                      className="block w-full px-3 py-1.5 text-left text-sm hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {TEAM_ROLE_META[role].label}
                    </button>
                  ))}
                  <div className="border-t border-gray-100 my-1" />
                  <button
                    onClick={handleRemove}
                    className="block w-full px-3 py-1.5 text-left text-sm text-red-600 hover:bg-red-50"
                  >
                    Remove from team
                  </button>
                </div>
              </>
            )}
          </div>
        )}
      </td>
    </tr>
  );
}

function AddMemberModal({
  isOpen,
  onClose,
  teamId,
}: {
  isOpen: boolean;
  onClose: () => void;
  teamId: string;
}) {
  const addMember = useAddTeamMember(teamId);
  const [userId, setUserId] = useState("");
  const [role, setRole] = useState<TeamRole>("member");
  const [memberType, setMemberType] = useState<"human" | "ai_agent">("human");
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!userId.trim()) {
      setError("User ID is required");
      return;
    }

    // SASE constraint: AI agents cannot be owner or admin
    if (memberType === "ai_agent" && (role === "owner" || role === "admin")) {
      setError("AI agents cannot have owner or admin roles (SASE compliance)");
      return;
    }

    try {
      await addMember.mutateAsync({
        user_id: userId.trim(),
        role,
        member_type: memberType,
      });
      onClose();
      setUserId("");
      setRole("member");
      setMemberType("human");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add member");
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />

      <div className="relative z-10 w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Add Team Member</h2>
          <button
            onClick={onClose}
            className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="rounded-lg bg-red-50 border border-red-200 p-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          <div>
            <label htmlFor="userId" className="block text-sm font-medium text-gray-700 mb-1">
              User ID <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="userId"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              placeholder="Enter user UUID"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div>
            <label htmlFor="memberType" className="block text-sm font-medium text-gray-700 mb-1">
              Member Type
            </label>
            <select
              id="memberType"
              value={memberType}
              onChange={(e) => {
                setMemberType(e.target.value as "human" | "ai_agent");
                if (e.target.value === "ai_agent" && (role === "owner" || role === "admin")) {
                  setRole("member");
                }
              }}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="human">Human</option>
              <option value="ai_agent">AI Agent</option>
            </select>
          </div>

          <div>
            <label htmlFor="role" className="block text-sm font-medium text-gray-700 mb-1">
              Role
            </label>
            <select
              id="role"
              value={role}
              onChange={(e) => setRole(e.target.value as TeamRole)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              {memberType === "human" ? (
                <>
                  <option value="owner">Owner (SE4H Coach)</option>
                  <option value="admin">Admin (SE4H Coach)</option>
                  <option value="member">Member (SE4H Member)</option>
                </>
              ) : (
                <>
                  <option value="member">Member (SE4A Executor)</option>
                  <option value="ai_agent">AI Agent (SE4A Executor)</option>
                </>
              )}
            </select>
            {memberType === "ai_agent" && (
              <p className="mt-1 text-xs text-amber-600">
                AI agents cannot be assigned owner or admin roles (SASE compliance)
              </p>
            )}
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={addMember.isPending}
              className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {addMember.isPending ? "Adding..." : "Add Member"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

/**
 * Edit Team Modal
 * Sprint 91: Added edit functionality for team name/description/settings
 */
function EditTeamModal({
  isOpen,
  onClose,
  team,
}: {
  isOpen: boolean;
  onClose: () => void;
  team: { id: string; name: string; description: string | null; settings: TeamSettings };
}) {
  const updateTeam = useUpdateTeam(team.id);
  const [name, setName] = useState(team.name);
  const [description, setDescription] = useState(team.description || "");
  const [agenticMaturity, setAgenticMaturity] = useState<AgenticMaturity>(
    (team.settings?.agentic_maturity || "L0") as AgenticMaturity
  );
  const [error, setError] = useState<string | null>(null);

  // Reset form when modal opens with new team data
  useState(() => {
    setName(team.name);
    setDescription(team.description || "");
    setAgenticMaturity((team.settings?.agentic_maturity || "L0") as AgenticMaturity);
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!name.trim()) {
      setError("Team name is required");
      return;
    }

    try {
      const updateData: TeamUpdate = {
        name: name.trim(),
        description: description.trim() || null,
        settings: {
          ...team.settings,
          agentic_maturity: agenticMaturity,
        },
      };
      await updateTeam.mutateAsync(updateData);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update team");
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />

      <div className="relative z-10 w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Edit Team</h2>
          <button
            onClick={onClose}
            className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="rounded-lg bg-red-50 border border-red-200 p-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          <div>
            <label htmlFor="teamName" className="block text-sm font-medium text-gray-700 mb-1">
              Team Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="teamName"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter team name"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div>
            <label htmlFor="teamDescription" className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              id="teamDescription"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Team description (optional)"
              rows={3}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div>
            <label htmlFor="agenticMaturity" className="block text-sm font-medium text-gray-700 mb-1">
              Agentic Maturity Level
            </label>
            <select
              id="agenticMaturity"
              value={agenticMaturity}
              onChange={(e) => setAgenticMaturity(e.target.value as AgenticMaturity)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              {(["L0", "L1", "L2", "L3"] as AgenticMaturity[]).map((level) => (
                <option key={level} value={level}>
                  {AGENTIC_MATURITY_META[level].label}
                </option>
              ))}
            </select>
            <p className="mt-1 text-xs text-gray-500">
              {AGENTIC_MATURITY_META[agenticMaturity].description}
            </p>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={updateTeam.isPending}
              className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {updateTeam.isPending ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
    </div>
  );
}

// =============================================================================
// Main Page
// =============================================================================

export default function TeamDetailPage() {
  const params = useParams();
  const router = useRouter();
  const teamId = params.id as string;

  const [isAddMemberOpen, setIsAddMemberOpen] = useState(false);
  const [isEditTeamOpen, setIsEditTeamOpen] = useState(false);

  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const { data: team, isLoading: teamLoading, error: teamError } = useTeam(teamId);
  const { data: stats } = useTeamStats(teamId);
  const { data: membersData } = useTeamMembers(teamId);
  const deleteTeam = useDeleteTeam();
  const members = membersData?.items || [];
  const maturity = (team?.settings?.agentic_maturity || "L0") as AgenticMaturity;

  // Check if current user can manage team based on their role in this team
  // Sprint 91: Fixed P0 Security - was hardcoded to true
  const currentUserMembership = members.find((m) => m.user_id === user?.id);
  const canManage = currentUserMembership?.role === "owner" || currentUserMembership?.role === "admin";

  const handleDeleteTeam = async () => {
    if (confirm(`Are you sure you want to delete team "${team?.name}"? This action cannot be undone.`)) {
      await deleteTeam.mutateAsync(teamId);
      router.push("/app/teams");
    }
  };

  if (authLoading || teamLoading) {
    return <LoadingSpinner />;
  }

  if (!isAuthenticated) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <div className="text-amber-600 mb-4">Please log in to view team details.</div>
        <Link
          href="/login"
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Go to Login
        </Link>
      </div>
    );
  }

  if (teamError || !team) {
    return (
      <div className="space-y-4">
        <Link
          href="/app/teams"
          className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700"
        >
          <ArrowLeftIcon className="h-4 w-4" />
          Back to Teams
        </Link>
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="text-sm text-red-700">
            Team not found or you don&apos;t have access.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <Link
            href="/app/teams"
            className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700"
          >
            <ArrowLeftIcon className="h-4 w-4" />
            Back to Teams
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">{team.name}</h1>
          <p className="text-gray-500">{team.description || "No description"}</p>
          <div className="flex items-center gap-2 pt-1">
            <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${AGENTIC_MATURITY_META[maturity].color}`}>
              {AGENTIC_MATURITY_META[maturity].label}
            </span>
          </div>
        </div>

        {canManage && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsEditTeamOpen(true)}
              className="inline-flex items-center gap-2 rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              <PencilIcon className="h-4 w-4" />
              Edit
            </button>
            <button
              onClick={handleDeleteTeam}
              disabled={deleteTeam.isPending}
              className="inline-flex items-center gap-2 rounded-lg border border-red-300 px-3 py-2 text-sm font-medium text-red-600 hover:bg-red-50 disabled:opacity-50"
            >
              <TrashIcon className="h-4 w-4" />
              Delete
            </button>
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Total Members"
          value={stats?.total_members || team.members_count}
          icon={UsersIcon}
          color="bg-indigo-50 text-indigo-600"
        />
        <StatCard
          label="Human Members"
          value={stats?.human_members || team.human_members_count}
          icon={UsersIcon}
          color="bg-green-50 text-green-600"
        />
        <StatCard
          label="AI Agents"
          value={stats?.ai_agents || team.ai_agents_count}
          icon={BotIcon}
          color="bg-orange-50 text-orange-600"
        />
        <StatCard
          label="Projects"
          value={stats?.total_projects || team.projects_count}
          icon={FolderIcon}
          color="bg-blue-50 text-blue-600"
        />
      </div>

      {/* Members */}
      <div className="rounded-lg border border-gray-200 bg-white">
        <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
          <h2 className="text-lg font-semibold text-gray-900">
            Team Members ({members.length})
          </h2>
          {canManage && (
            <button
              onClick={() => setIsAddMemberOpen(true)}
              className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              <UserPlusIcon className="h-4 w-4" />
              Add Member
            </button>
          )}
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-100 text-left text-sm text-gray-500">
                <th className="py-3 pr-4 pl-6 font-medium">Member</th>
                <th className="py-3 px-4 font-medium">Role</th>
                <th className="py-3 px-4 font-medium">SASE Role</th>
                <th className="py-3 px-4 font-medium">Joined</th>
                <th className="py-3 pl-4 pr-6 font-medium w-12"></th>
              </tr>
            </thead>
            <tbody className="px-6">
              {members.map((member) => (
                <MemberRow
                  key={member.id}
                  member={member}
                  teamId={teamId}
                  canManage={canManage}
                />
              ))}
              {members.length === 0 && (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-gray-500">
                    No members found. Add the first member to this team.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Member Modal */}
      <AddMemberModal
        isOpen={isAddMemberOpen}
        onClose={() => setIsAddMemberOpen(false)}
        teamId={teamId}
      />

      {/* Edit Team Modal - Sprint 91 */}
      {team && (
        <EditTeamModal
          isOpen={isEditTeamOpen}
          onClose={() => setIsEditTeamOpen(false)}
          team={team}
        />
      )}
    </div>
  );
}
