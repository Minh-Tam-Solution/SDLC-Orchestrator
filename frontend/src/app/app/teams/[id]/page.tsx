/**
 * Team Detail Page - SDLC Orchestrator Dashboard
 *
 * @module frontend/src/app/app/teams/[id]/page
 * @description Team detail with members management
 * @sdlc SDLC 5.1.3 Framework - Sprint 84 (Teams & Organizations UI)
 * @status Sprint 84 - CTO APPROVED (January 20, 2026)
 */

"use client";

import React, { useState, useRef } from "react";
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

function CheckIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
    </svg>
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
  const [menuPosition, setMenuPosition] = useState({ top: 0, left: 0 });
  // Sprint 105: Track delete in progress to prevent double-delete
  const [isDeleting, setIsDeleting] = useState(false);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const removeMember = useRemoveTeamMember(teamId);
  const updateRole = useUpdateMemberRole(teamId);

  const handleOpenMenu = () => {
    if (buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      const dropdownHeight = 280; // Approximate height of dropdown
      const viewportHeight = window.innerHeight;
      const spaceBelow = viewportHeight - rect.bottom;

      // If not enough space below, position above
      if (spaceBelow < dropdownHeight) {
        setMenuPosition({
          top: rect.top - dropdownHeight - 4,
          left: rect.right - 224, // 224px = w-56 (14rem)
        });
      } else {
        setMenuPosition({
          top: rect.bottom + 4,
          left: rect.right - 224,
        });
      }
    }
    setShowMenu(!showMenu);
  };

  const handleRemove = async (e: React.MouseEvent) => {
    // Prevent event bubbling
    e.stopPropagation();
    e.preventDefault();

    console.log("[RemoveMember] handleRemove called", {
      userId: member.user_id,
      isDeleting,
      isPending: removeMember.isPending,
    });

    // Sprint 105: Prevent double-delete
    if (isDeleting || removeMember.isPending) {
      console.log("[RemoveMember] Already deleting, skipping");
      return;
    }

    if (confirm(`Remove ${member.user_name || member.user_email} from team?`)) {
      setIsDeleting(true);
      setShowMenu(false); // Close menu immediately

      try {
        console.log("[RemoveMember] Calling mutateAsync for:", member.user_id);
        await removeMember.mutateAsync(member.user_id);
        console.log("[RemoveMember] mutateAsync completed successfully");
      } catch (err: unknown) {
        console.log("[RemoveMember] Caught error:", err);

        // Sprint 105: Don't show error for 404 - member is already deleted
        const errorStatus = err && typeof err === "object" && "status" in err
          ? (err as { status: number }).status
          : null;

        if (errorStatus === 404) {
          // Member already deleted - this is success from user's perspective
          console.log("[RemoveMember] 404 = member already deleted, ignoring");
          return;
        }

        // Log and show error for real errors only
        console.error("[RemoveMember] Real error:", err);
        const errorMsg = err && typeof err === "object" && "detail" in err
          ? (err as { detail: string }).detail
          : "Failed to remove member. Please try again.";
        alert(errorMsg);
      } finally {
        setIsDeleting(false);
      }
    } else {
      setShowMenu(false);
    }
  };

  const handleRoleChange = async (newRole: TeamRole) => {
    // Skip if same role
    if (newRole === member.role) {
      setShowMenu(false);
      return;
    }
    await updateRole.mutateAsync({ userId: member.user_id, data: { role: newRole } });
    setShowMenu(false);
  };

  // Role descriptions for better UX
  const roleDescriptions: Record<TeamRole, string> = {
    owner: "Full control, can delete team",
    admin: "Manage members and settings",
    member: "View and contribute",
    ai_agent: "AI automation agent",
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
          <>
            <button
              ref={buttonRef}
              onClick={handleOpenMenu}
              className="rounded p-1 hover:bg-gray-100"
              disabled={updateRole.isPending || removeMember.isPending}
            >
              {updateRole.isPending ? (
                <svg className="h-5 w-5 text-blue-500 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
              ) : (
                <EllipsisVerticalIcon className="h-5 w-5 text-gray-400" />
              )}
            </button>

            {showMenu && (
              <>
                <div className="fixed inset-0 z-40" onClick={() => setShowMenu(false)} />
                <div
                  className="fixed z-50 w-56 rounded-lg border border-gray-200 bg-white py-1 shadow-xl"
                  style={{ top: menuPosition.top, left: menuPosition.left }}
                >
                  <div className="px-3 py-2 border-b border-gray-100">
                    <p className="text-xs font-medium text-gray-500 uppercase">Change Role</p>
                    <p className="text-xs text-gray-400 mt-0.5">Select a new role for this member</p>
                  </div>
                  {(["owner", "admin", "member"] as TeamRole[]).map((role) => {
                    const isCurrentRole = member.role === role;
                    const isDisabledForAI = member.member_type === "ai_agent" && (role === "owner" || role === "admin");
                    const isDisabled = isCurrentRole || isDisabledForAI;

                    return (
                      <button
                        key={role}
                        onClick={() => handleRoleChange(role)}
                        disabled={isDisabled}
                        className={`flex items-center justify-between w-full px-3 py-2 text-left text-sm transition-colors ${
                          isCurrentRole
                            ? "bg-blue-50 text-blue-700"
                            : isDisabledForAI
                              ? "opacity-40 cursor-not-allowed text-gray-400"
                              : "hover:bg-gray-50 text-gray-700"
                        }`}
                      >
                        <div>
                          <p className={`font-medium ${isCurrentRole ? "text-blue-700" : ""}`}>
                            {TEAM_ROLE_META[role].label}
                          </p>
                          <p className={`text-xs ${isCurrentRole ? "text-blue-500" : "text-gray-400"}`}>
                            {roleDescriptions[role]}
                          </p>
                        </div>
                        {isCurrentRole && (
                          <CheckIcon className="h-4 w-4 text-blue-600 shrink-0" />
                        )}
                      </button>
                    );
                  })}
                  <div className="border-t border-gray-100 my-1" />
                  <button
                    onClick={handleRemove}
                    disabled={removeMember.isPending || isDeleting}
                    className="flex items-center w-full px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50 transition-colors disabled:opacity-50"
                  >
                    <TrashIcon className="h-4 w-4 mr-2" />
                    {isDeleting ? "Removing..." : "Remove from team"}
                  </button>
                </div>
              </>
            )}
          </>
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
  const [userEmail, setUserEmail] = useState("");
  const [role, setRole] = useState<TeamRole>("member");
  const [memberType, setMemberType] = useState<"human" | "ai_agent">("human");
  const [error, setError] = useState<string | null>(null);

  // Sprint 105 Fix: Get error from mutation state as fallback
  // This ensures errors are displayed even if try/catch doesn't work properly
  const mutationError = addMember.error as { detail?: string } | null;
  const displayError = error || mutationError?.detail || (addMember.isError ? "Failed to add member" : null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    // Reset mutation error state
    addMember.reset();

    if (!userEmail.trim()) {
      setError("User email is required");
      return;
    }

    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(userEmail.trim())) {
      setError("Please enter a valid email address");
      return;
    }

    // SASE constraint: AI agents cannot be owner or admin
    if (memberType === "ai_agent" && (role === "owner" || role === "admin")) {
      setError("AI agents cannot have owner or admin roles (SASE compliance)");
      return;
    }

    try {
      console.log("[AddMember] Starting mutation with:", {
        email: userEmail.trim(),
        role,
        member_type: memberType,
      });
      await addMember.mutateAsync({
        email: userEmail.trim(),
        role,
        member_type: memberType,
      });
      console.log("[AddMember] Mutation succeeded");
      onClose();
      setUserEmail("");
      setRole("member");
      setMemberType("human");
    } catch (err: unknown) {
      // Handle API errors (thrown as { detail, status } objects)
      console.log("[AddMember] Caught error:", err);
      console.log("[AddMember] Error type:", typeof err);
      console.log("[AddMember] Has detail:", err && typeof err === "object" && "detail" in err);

      if (err && typeof err === "object" && "detail" in err) {
        const errorDetail = (err as { detail: string }).detail;
        console.log("[AddMember] Setting error detail:", errorDetail);
        setError(errorDetail);
      } else if (err instanceof Error) {
        console.log("[AddMember] Setting error message:", err.message);
        setError(err.message);
      } else {
        console.log("[AddMember] Setting default error");
        setError("Failed to add member");
      }
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
          {displayError && (
            <div className="rounded-lg bg-red-50 border border-red-200 p-3">
              <p className="text-sm text-red-700">{displayError}</p>
            </div>
          )}

          <div>
            <label htmlFor="userEmail" className="block text-sm font-medium text-gray-700 mb-1">
              User Email <span className="text-red-500">*</span>
            </label>
            <input
              type="email"
              id="userEmail"
              value={userEmail}
              onChange={(e) => setUserEmail(e.target.value)}
              placeholder="Enter user email address"
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
                const newMemberType = e.target.value as "human" | "ai_agent";
                setMemberType(newMemberType);
                // AI Agent member type can ONLY have "ai_agent" role (SASE compliance)
                if (newMemberType === "ai_agent") {
                  setRole("ai_agent");
                } else if (role === "ai_agent") {
                  // Switching from AI Agent to Human, default to "member" role
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
            {memberType === "ai_agent" ? (
              // AI Agent: Fixed role, no selection needed (SASE compliance)
              <>
                <div className="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-700">
                  AI Agent (SE4A Executor)
                </div>
                <p className="mt-1 text-xs text-amber-600">
                  AI agents are automatically assigned the AI Agent role (SASE compliance)
                </p>
              </>
            ) : (
              // Human: Can select from owner, admin, member
              <select
                id="role"
                value={role}
                onChange={(e) => setRole(e.target.value as TeamRole)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <option value="owner">Owner (SE4H Coach)</option>
                <option value="admin">Admin (SE4H Coach)</option>
                <option value="member">Member (SE4H Member)</option>
              </select>
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
