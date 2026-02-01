"use client";

import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { InvitationList } from "@/components/teams/InvitationList";
import { useTeams } from "@/hooks/useTeams";
import { useAuth } from "@/hooks/useAuth";

export default function TeamInvitationsPage() {
  const params = useParams();
  const router = useRouter();
  const teamId = params.id as string;

  const { user } = useAuth();
  const { teams, isLoading } = useTeams();

  // Find the current team
  const team = teams?.find((t) => t.id === teamId);

  // Check if user has permission to manage invitations
  const canManageInvitations =
    team?.role === "owner" || team?.role === "admin";

  if (isLoading) {
    return (
      <div className="container mx-auto py-8">
        <div className="flex items-center justify-center py-12">
          <svg
            className="h-8 w-8 animate-spin text-muted-foreground"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        </div>
      </div>
    );
  }

  if (!team) {
    return (
      <div className="container mx-auto py-8">
        <div className="flex flex-col items-center justify-center py-12">
          <svg
            className="h-16 w-16 text-muted-foreground/50"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
            />
          </svg>
          <h2 className="mt-4 text-lg font-semibold">Team Not Found</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            The team you're looking for doesn't exist or you don't have access to
            it.
          </p>
          <Button
            onClick={() => router.push("/app/teams")}
            variant="outline"
            className="mt-6"
          >
            Back to Teams
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-4 mb-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push(`/app/teams/${teamId}`)}
          >
            <svg
              className="mr-2 h-4 w-4"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18"
              />
            </svg>
            Back to Team
          </Button>
        </div>

        <div>
          <h1 className="text-3xl font-bold tracking-tight">{team.name}</h1>
          <p className="text-muted-foreground mt-2">
            Manage team invitations and pending member requests
          </p>
        </div>
      </div>

      {/* Permission Check */}
      {!canManageInvitations && (
        <div className="mb-6 rounded-lg border border-yellow-200 bg-yellow-50 p-4 dark:border-yellow-900 dark:bg-yellow-950">
          <div className="flex items-start gap-3">
            <svg
              className="h-5 w-5 text-yellow-600 dark:text-yellow-500"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
              />
            </svg>
            <div>
              <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                Limited Access
              </p>
              <p className="mt-1 text-sm text-yellow-700 dark:text-yellow-300">
                You can view invitations but cannot send or manage them. Contact
                a team owner or admin to invite new members.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Invitations List */}
      <InvitationList
        teamId={teamId}
        teamName={team.name}
        canInvite={canManageInvitations}
      />
    </div>
  );
}
