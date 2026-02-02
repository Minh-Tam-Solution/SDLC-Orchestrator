import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface TeamInvitation {
  id: string;
  team_id: string;
  invited_email: string;
  role: "owner" | "admin" | "member" | "viewer";
  status: "pending" | "accepted" | "declined" | "expired";
  invited_by: string;
  invited_by_name?: string;
  expires_at: string;
  created_at: string;
  accepted_at?: string;
  declined_at?: string;
}

export interface SendInvitationRequest {
  email: string;
  role: "owner" | "admin" | "member" | "viewer";
}

export interface ResendInvitationRequest {
  invitation_id: string;
}

export function useInvitations(teamId: string) {
  const queryClient = useQueryClient();

  // Fetch team invitations
  const {
    data: invitationsData,
    isLoading,
    error,
    refetch,
  } = useQuery<TeamInvitation[]>({
    queryKey: ["team-invitations", teamId],
    queryFn: async (): Promise<TeamInvitation[]> => {
      const response = await api.get<TeamInvitation[]>(`/teams/${teamId}/invitations`);
      return response.data;
    },
    enabled: !!teamId,
  });

  // Sprint 136: Explicitly type invitations to fix TanStack Query type inference
  const invitations: TeamInvitation[] = invitationsData ?? [];

  // Send invitation mutation
  const {
    mutateAsync: sendInvitation,
    isPending: isSending,
    error: sendError,
  } = useMutation({
    mutationFn: async (data: SendInvitationRequest) => {
      const response = await api.post(`/teams/${teamId}/invitations`, data);
      return response.data;
    },
    onSuccess: () => {
      // Invalidate and refetch invitations list
      queryClient.invalidateQueries({ queryKey: ["team-invitations", teamId] });
    },
  });

  // Cancel invitation mutation
  const {
    mutateAsync: cancelInvitation,
    isPending: isCanceling,
    error: cancelError,
  } = useMutation({
    mutationFn: async (invitationId: string) => {
      const response = await api.delete(
        `/teams/${teamId}/invitations/${invitationId}`
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["team-invitations", teamId] });
    },
  });

  // Resend invitation mutation
  const {
    mutateAsync: resendInvitation,
    isPending: isResending,
    error: resendError,
  } = useMutation({
    mutationFn: async (invitationId: string) => {
      const response = await api.post(
        `/teams/${teamId}/invitations/${invitationId}/resend`
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["team-invitations", teamId] });
    },
  });

  // Accept invitation mutation (for invited user)
  const {
    mutateAsync: acceptInvitation,
    isPending: isAccepting,
    error: acceptError,
  } = useMutation({
    mutationFn: async (token: string) => {
      const response = await api.post(`/invitations/${token}/accept`);
      return response.data;
    },
    onSuccess: () => {
      // Invalidate team membership queries
      queryClient.invalidateQueries({ queryKey: ["teams"] });
      queryClient.invalidateQueries({ queryKey: ["user-teams"] });
    },
  });

  // Decline invitation mutation (for invited user)
  const {
    mutateAsync: declineInvitation,
    isPending: isDeclining,
    error: declineError,
  } = useMutation({
    mutationFn: async (token: string) => {
      const response = await api.post(`/invitations/${token}/decline`);
      return response.data;
    },
  });

  // Get invitation by token (for invited user)
  const getInvitationByToken = async (token: string) => {
    const response = await api.get(`/invitations/${token}`);
    return response.data as TeamInvitation;
  };

  // Computed values
  const pendingInvitations = invitations.filter((i) => i.status === "pending");
  const expiredInvitations = invitations.filter((i) => i.status === "expired");
  const acceptedInvitations = invitations.filter(
    (i) => i.status === "accepted"
  );
  const declinedInvitations = invitations.filter(
    (i) => i.status === "declined"
  );

  return {
    // Data
    invitations,
    pendingInvitations,
    expiredInvitations,
    acceptedInvitations,
    declinedInvitations,

    // Loading states
    isLoading,
    isSending,
    isCanceling,
    isResending,
    isAccepting,
    isDeclining,

    // Errors
    error,
    sendError,
    cancelError,
    resendError,
    acceptError,
    declineError,

    // Actions
    sendInvitation,
    cancelInvitation,
    resendInvitation,
    acceptInvitation,
    declineInvitation,
    getInvitationByToken,
    refetch,
  };
}

// Hook for accepting invitation from email link
export function useAcceptInvitation(token: string | null) {
  return useQuery<TeamInvitation>({
    queryKey: ["invitation", token],
    queryFn: async (): Promise<TeamInvitation> => {
      if (!token) throw new Error("No invitation token provided");
      const response = await api.get<TeamInvitation>(`/invitations/${token}`);
      return response.data;
    },
    enabled: !!token,
  });
}
