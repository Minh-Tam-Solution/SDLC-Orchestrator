import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface GitHubRepository {
  id: number;
  name: string;
  full_name: string;
  description: string | null;
  private: boolean;
  url: string;
  html_url: string;
  clone_url: string;
  default_branch: string;
  language: string | null;
  stargazers_count: number;
  forks_count: number;
  open_issues_count: number;
  created_at: string;
  updated_at: string;
  pushed_at: string;
  owner: {
    login: string;
    avatar_url: string;
  };
}

export interface GitHubConnection {
  id: string;
  user_id: string;
  github_user_id: number;
  github_username: string;
  github_avatar_url: string;
  access_token_expires_at: string;
  installation_id?: number;
  connected_at: string;
  last_synced_at?: string;
}

export interface ConnectGitHubRequest {
  code: string;
  state?: string;
}

export interface ConnectRepositoryRequest {
  repository_id: number;
  repository_name: string;
  repository_owner: string;
  default_branch: string;
}

export interface ProjectGitHubConnection {
  id: string;
  project_id: string;
  repository_id: number;
  repository_name: string;
  repository_owner: string;
  repository_full_name: string;
  default_branch: string;
  webhook_id?: number;
  connected_at: string;
  last_sync_at?: string;
  sync_status: "idle" | "syncing" | "error";
  last_error?: string;
}

export function useGitHub() {
  const queryClient = useQueryClient();

  // Fetch GitHub connection status
  const {
    data: connectionData,
    isLoading: isLoadingConnection,
    error: connectionError,
    refetch: refetchConnection,
  } = useQuery<GitHubConnection | null>({
    queryKey: ["github-connection"],
    queryFn: async (): Promise<GitHubConnection | null> => {
      try {
        const response = await api.get<GitHubConnection>("/github/connection");
        return response.data;
      } catch (err: unknown) {
        const error = err as { response?: { status?: number } };
        if (error.response?.status === 404) {
          return null; // Not connected
        }
        throw err;
      }
    },
  });

  // Sprint 136: Explicitly type connection to fix TanStack Query type inference
  const connection: GitHubConnection | null | undefined = connectionData;

  // Fetch GitHub repositories (only if connected)
  const {
    data: repositoriesData,
    isLoading: isLoadingRepositories,
    error: repositoriesError,
    refetch: refetchRepositories,
  } = useQuery<GitHubRepository[]>({
    queryKey: ["github-repositories"],
    queryFn: async (): Promise<GitHubRepository[]> => {
      const response = await api.get<GitHubRepository[]>("/github/repositories");
      return response.data;
    },
    enabled: !!connection,
  });

  // Sprint 136: Explicitly type repositories to fix TanStack Query type inference
  const repositories: GitHubRepository[] = repositoriesData ?? [];

  // Connect GitHub account (OAuth flow)
  const {
    mutateAsync: connectGitHub,
    isPending: isConnecting,
    error: connectError,
  } = useMutation({
    mutationFn: async (data: ConnectGitHubRequest) => {
      const response = await api.post("/github/connect", data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["github-connection"] });
      queryClient.invalidateQueries({ queryKey: ["github-repositories"] });
    },
  });

  // Disconnect GitHub account
  const {
    mutateAsync: disconnectGitHub,
    isPending: isDisconnecting,
    error: disconnectError,
  } = useMutation({
    mutationFn: async () => {
      const response = await api.delete("/github/connection");
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["github-connection"] });
      queryClient.invalidateQueries({ queryKey: ["github-repositories"] });
      queryClient.invalidateQueries({ queryKey: ["project-github-connections"] });
    },
  });

  // Sync repositories from GitHub
  const {
    mutateAsync: syncRepositories,
    isPending: isSyncing,
    error: syncError,
  } = useMutation({
    mutationFn: async () => {
      const response = await api.post("/github/repositories/sync");
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["github-repositories"] });
    },
  });

  // Connect repository to project
  const {
    mutateAsync: connectRepository,
    isPending: isConnectingRepository,
    error: connectRepositoryError,
  } = useMutation({
    mutationFn: async ({
      projectId,
      data,
    }: {
      projectId: string;
      data: ConnectRepositoryRequest;
    }) => {
      const response = await api.post(
        `/projects/${projectId}/github/repository`,
        data
      );
      return response.data;
    },
    onSuccess: (_, { projectId }) => {
      queryClient.invalidateQueries({
        queryKey: ["project-github-connection", projectId],
      });
    },
  });

  // Disconnect repository from project
  const {
    mutateAsync: disconnectRepository,
    isPending: isDisconnectingRepository,
    error: disconnectRepositoryError,
  } = useMutation({
    mutationFn: async (projectId: string) => {
      const response = await api.delete(`/projects/${projectId}/github/repository`);
      return response.data;
    },
    onSuccess: (_, projectId) => {
      queryClient.invalidateQueries({
        queryKey: ["project-github-connection", projectId],
      });
    },
  });

  // Trigger manual sync for project repository
  const {
    mutateAsync: triggerProjectSync,
    isPending: isTriggeringSync,
    error: triggerSyncError,
  } = useMutation({
    mutationFn: async (projectId: string) => {
      const response = await api.post(`/projects/${projectId}/github/sync`);
      return response.data;
    },
    onSuccess: (_, projectId) => {
      queryClient.invalidateQueries({
        queryKey: ["project-github-connection", projectId],
      });
    },
  });

  // Computed values
  const isConnected = !!connection;
  const hasRepositories = repositories.length > 0;

  return {
    // Connection data
    connection,
    isConnected,
    isLoadingConnection,
    connectionError,

    // Repositories data
    repositories,
    hasRepositories,
    isLoadingRepositories,
    repositoriesError,

    // Connection actions
    connectGitHub,
    isConnecting,
    connectError,
    disconnectGitHub,
    isDisconnecting,
    disconnectError,

    // Repository actions
    syncRepositories,
    isSyncing,
    syncError,
    connectRepository,
    isConnectingRepository,
    connectRepositoryError,
    disconnectRepository,
    isDisconnectingRepository,
    disconnectRepositoryError,
    triggerProjectSync,
    isTriggeringSync,
    triggerSyncError,

    // Refetch functions
    refetchConnection,
    refetchRepositories,
  };
}

// Hook for fetching project-specific GitHub connection
export function useProjectGitHub(projectId: string | null) {
  const _queryClient = useQueryClient(); // eslint-disable-line @typescript-eslint/no-unused-vars

  const {
    data: projectConnection,
    isLoading,
    error,
    refetch,
  } = useQuery<ProjectGitHubConnection | null>({
    queryKey: ["project-github-connection", projectId],
    queryFn: async (): Promise<ProjectGitHubConnection | null> => {
      if (!projectId) return null;
      try {
        const response = await api.get<ProjectGitHubConnection>(`/projects/${projectId}/github/repository`);
        return response.data;
      } catch (err: unknown) {
        const error = err as { response?: { status?: number } };
        if (error.response?.status === 404) {
          return null; // Project not connected to GitHub
        }
        throw err;
      }
    },
    enabled: !!projectId,
  });

  const isProjectConnected = !!projectConnection;

  return {
    projectConnection,
    isProjectConnected,
    isLoading,
    error,
    refetch,
  };
}

// Hook for initiating GitHub OAuth flow
export function useGitHubOAuth() {
  const initiateOAuth = () => {
    const clientId = process.env.NEXT_PUBLIC_GITHUB_CLIENT_ID;
    const redirectUri = `${window.location.origin}/settings/github/callback`;
    const state = Math.random().toString(36).substring(7);

    // Store state in sessionStorage for verification
    sessionStorage.setItem("github_oauth_state", state);

    const authUrl = `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${redirectUri}&scope=read:user,repo&state=${state}`;

    window.location.href = authUrl;
  };

  return { initiateOAuth };
}
