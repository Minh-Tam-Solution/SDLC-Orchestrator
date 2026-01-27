/**
 * Settings Page - SDLC Orchestrator Dashboard
 *
 * @module frontend/landing/src/app/app/settings/page
 * @description User settings, integrations, and API key management
 * @sdlc SDLC 5.1.2 Universal Framework
 * @status Sprint 64 - Route Group Migration
 */

"use client";

import { useState } from "react";
import Image from "next/image";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/hooks/useAuth";

// =============================================================================
// Types
// =============================================================================

interface APIKey {
  id: string;
  name: string;
  prefix: string;
  last_used_at: string | null;
  expires_at: string | null;
  is_active: boolean;
  created_at: string;
}

interface APIKeyCreatedResponse {
  id: string;
  name: string;
  api_key: string;
  prefix: string;
  expires_at: string | null;
  created_at: string;
}

interface GitHubStatus {
  connected: boolean;
  github_username: string | null;
  github_avatar: string | null;
  connected_at: string | null;
  scopes: string[] | null;
  rate_limit: {
    limit: number;
    remaining: number;
    reset_at: string;
  } | null;
}

// =============================================================================
// Icons
// =============================================================================

function KeyIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 5.25a3 3 0 0 1 3 3m3 0a6 6 0 0 1-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 1 1 21.75 8.25Z" />
    </svg>
  );
}

function UserIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z" />
    </svg>
  );
}

function CheckIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
    </svg>
  );
}

function PlusIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
    </svg>
  );
}

function ClipboardIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M15.666 3.888A2.25 2.25 0 0 0 13.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 0 1-.75.75H9a.75.75 0 0 1-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 0 1-2.25 2.25H6.75A2.25 2.25 0 0 1 4.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 0 1 1.927-.184" />
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

function ExclamationTriangleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
    </svg>
  );
}

function GitHubIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
    </svg>
  );
}

// =============================================================================
// API Functions
// =============================================================================

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function fetchWithAuth<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}

// =============================================================================
// Helpers
// =============================================================================

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "Never";
  return new Date(dateStr).toLocaleDateString();
}

function formatRelativeTime(dateStr: string | null): string {
  if (!dateStr) return "Never used";
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins} min ago`;
  if (diffHours < 24) return `${diffHours} hours ago`;
  if (diffDays < 30) return `${diffDays} days ago`;
  return formatDate(dateStr);
}

// =============================================================================
// Main Component
// =============================================================================

export default function SettingsPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  // Modal states
  const [showGenerateDialog, setShowGenerateDialog] = useState(false);
  const [showRevokeDialog, setShowRevokeDialog] = useState<string | null>(null);
  const [showDisconnectDialog, setShowDisconnectDialog] = useState(false);

  // Form states
  const [newKeyName, setNewKeyName] = useState("VS Code Extension");
  const [newKeyExpiry, setNewKeyExpiry] = useState("90");
  const [createdKey, setCreatedKey] = useState<APIKeyCreatedResponse | null>(null);
  const [copiedKey, setCopiedKey] = useState(false);

  // Fetch API keys
  const { data: apiKeys, isLoading: isLoadingApiKeys } = useQuery<APIKey[]>({
    queryKey: ["api-keys"],
    queryFn: () => fetchWithAuth<APIKey[]>("/api-keys"),
  });

  // Fetch GitHub status
  const { data: githubStatus, isLoading: isLoadingGitHub } = useQuery<GitHubStatus>({
    queryKey: ["github-status"],
    queryFn: () => fetchWithAuth<GitHubStatus>("/github/status"),
  });

  // Create API key mutation
  const createApiKeyMutation = useMutation({
    mutationFn: (data: { name: string; expires_in_days: number | null }) =>
      fetchWithAuth<APIKeyCreatedResponse>("/api-keys", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    onSuccess: (data) => {
      setCreatedKey(data);
      queryClient.invalidateQueries({ queryKey: ["api-keys"] });
    },
  });

  // Revoke API key mutation
  const revokeApiKeyMutation = useMutation({
    mutationFn: (keyId: string) =>
      fetchWithAuth(`/api-keys/${keyId}`, { method: "DELETE" }),
    onSuccess: () => {
      setShowRevokeDialog(null);
      queryClient.invalidateQueries({ queryKey: ["api-keys"] });
    },
  });

  // GitHub connect mutation
  const connectGitHubMutation = useMutation({
    mutationFn: () =>
      fetchWithAuth<{ authorization_url: string; state: string }>("/github/authorize"),
    onSuccess: (data) => {
      // Store OAuth state in localStorage for CSRF validation on callback
      localStorage.setItem("oauth_state", data.state);
      localStorage.setItem("oauth_flow", "connect");
      localStorage.setItem("oauth_provider", "github");
      localStorage.setItem("oauth_redirect", "/app/settings");
      window.location.href = data.authorization_url;
    },
  });

  // GitHub disconnect mutation
  const disconnectGitHubMutation = useMutation({
    mutationFn: () =>
      fetchWithAuth("/github/disconnect", { method: "DELETE" }),
    onSuccess: () => {
      setShowDisconnectDialog(false);
      queryClient.invalidateQueries({ queryKey: ["github-status"] });
    },
  });

  // Handlers
  const handleGenerateApiKey = () => {
    const expiryDays = newKeyExpiry === "never" ? null : parseInt(newKeyExpiry);
    createApiKeyMutation.mutate({ name: newKeyName, expires_in_days: expiryDays });
  };

  const handleCopyApiKey = async () => {
    if (createdKey?.api_key) {
      await navigator.clipboard.writeText(createdKey.api_key);
      setCopiedKey(true);
      setTimeout(() => setCopiedKey(false), 2000);
    }
  };

  const handleCloseCreatedKey = () => {
    setCreatedKey(null);
    setShowGenerateDialog(false);
    setNewKeyName("VS Code Extension");
    setNewKeyExpiry("90");
  };

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-gray-500">Manage your account settings and integrations</p>
      </div>

      {/* Profile Section */}
      <div className="bg-white rounded-lg border shadow-sm">
        <div className="p-6 border-b">
          <div className="flex items-center gap-2">
            <UserIcon className="h-5 w-5 text-gray-500" />
            <h2 className="text-lg font-semibold">Profile</h2>
          </div>
          <p className="text-sm text-gray-500 mt-1">Your account information</p>
        </div>
        <div className="p-6">
          {user ? (
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-blue-100 text-blue-600">
                  <UserIcon className="h-8 w-8" />
                </div>
                <div>
                  <p className="text-lg font-medium">{user.name || user.email}</p>
                  <p className="text-sm text-gray-500">{user.email}</p>
                </div>
              </div>
              <div className="grid gap-2 text-sm">
                <div className="flex justify-between border-b pb-2">
                  <span className="text-gray-500">User ID</span>
                  <span className="font-mono text-xs">{user.id}</span>
                </div>
                <div className="flex justify-between border-b pb-2">
                  <span className="text-gray-500">Status</span>
                  <span className={user.is_active ? "text-green-600" : "text-red-600"}>
                    {user.is_active ? "Active" : "Inactive"}
                  </span>
                </div>
                <div className="flex justify-between border-b pb-2">
                  <span className="text-gray-500">Roles</span>
                  <span>{user.roles?.join(", ") || "User"}</span>
                </div>
                {user.last_login_at && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Last Login</span>
                    <span>{new Date(user.last_login_at).toLocaleString()}</span>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <p className="text-gray-500">Loading profile...</p>
          )}
        </div>
      </div>

      {/* API Keys Section */}
      <div className="bg-white rounded-lg border shadow-sm">
        <div className="p-6 border-b">
          <div className="flex items-center gap-2">
            <KeyIcon className="h-5 w-5 text-gray-500" />
            <h2 className="text-lg font-semibold">API Keys</h2>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            Generate personal access tokens for VS Code extension and CLI tools
          </p>
        </div>
        <div className="p-6">
          <div className="space-y-4">
            {/* API Keys List */}
            {isLoadingApiKeys ? (
              <div className="text-gray-500">Loading API keys...</div>
            ) : apiKeys && apiKeys.length > 0 ? (
              <div className="space-y-3">
                {apiKeys.map((key) => (
                  <div
                    key={key.id}
                    className="flex items-center justify-between rounded-lg border p-4"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{key.name}</span>
                        {!key.is_active && (
                          <span className="rounded bg-red-100 px-2 py-0.5 text-xs text-red-700">
                            Revoked
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 text-sm text-gray-500">
                        <code className="rounded bg-gray-100 px-2 py-0.5 text-xs">
                          {key.prefix}
                        </code>
                        <span>•</span>
                        <span>Last used: {formatRelativeTime(key.last_used_at)}</span>
                        <span>•</span>
                        <span>Expires: {key.expires_at ? formatDate(key.expires_at) : "Never"}</span>
                      </div>
                    </div>
                    <button
                      onClick={() => setShowRevokeDialog(key.id)}
                      disabled={!key.is_active}
                      className="text-red-600 hover:text-red-700 text-sm font-medium disabled:opacity-50"
                    >
                      Revoke
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="rounded-lg border border-dashed p-6 text-center">
                <KeyIcon className="mx-auto h-12 w-12 text-gray-400" />
                <p className="mt-2 text-sm text-gray-500">
                  No API keys yet. Generate one to use with VS Code extension.
                </p>
              </div>
            )}

            {/* Generate Button */}
            <button
              onClick={() => setShowGenerateDialog(true)}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <PlusIcon className="h-5 w-5" />
              Generate New API Key
            </button>
          </div>
        </div>
      </div>

      {/* GitHub Integration Section */}
      <div className="bg-white rounded-lg border shadow-sm">
        <div className="p-6 border-b">
          <div className="flex items-center gap-2">
            <GitHubIcon className="h-5 w-5" />
            <h2 className="text-lg font-semibold">GitHub Integration</h2>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            Connect your GitHub account to sync repositories and create projects
          </p>
        </div>
        <div className="p-6">
          {isLoadingGitHub ? (
            <div className="text-gray-500">Loading GitHub status...</div>
          ) : githubStatus?.connected ? (
            <div className="space-y-4">
              {/* Connected status */}
              <div className="flex items-center gap-3 rounded-lg border border-green-200 bg-green-50 p-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-100">
                  <CheckIcon className="h-6 w-6 text-green-600" />
                </div>
                <div className="flex-1">
                  <p className="font-medium text-green-800">Connected</p>
                  <p className="text-sm text-green-700">
                    Signed in as <span className="font-semibold">@{githubStatus.github_username}</span>
                  </p>
                </div>
                {githubStatus.github_avatar && (
                  <Image
                    src={githubStatus.github_avatar}
                    alt={githubStatus.github_username || "GitHub avatar"}
                    width={40}
                    height={40}
                    className="rounded-full"
                    unoptimized
                  />
                )}
              </div>

              {/* Connection details */}
              <div className="grid gap-2 text-sm">
                {githubStatus.connected_at && (
                  <div className="flex justify-between border-b pb-2">
                    <span className="text-gray-500">Connected Since</span>
                    <span>{formatDate(githubStatus.connected_at)}</span>
                  </div>
                )}
                {githubStatus.scopes && githubStatus.scopes.length > 0 && (
                  <div className="flex justify-between border-b pb-2">
                    <span className="text-gray-500">Permissions</span>
                    <span className="text-right">{githubStatus.scopes.join(", ")}</span>
                  </div>
                )}
                {githubStatus.rate_limit && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">API Rate Limit</span>
                    <span>
                      {githubStatus.rate_limit.remaining} / {githubStatus.rate_limit.limit} remaining
                    </span>
                  </div>
                )}
              </div>

              {/* Disconnect button */}
              <button
                onClick={() => setShowDisconnectDialog(true)}
                className="flex items-center gap-2 px-4 py-2 border border-red-300 text-red-600 rounded-lg hover:bg-red-50"
              >
                Disconnect GitHub
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Not connected status */}
              <div className="flex items-center gap-3 rounded-lg border border-gray-200 bg-gray-50 p-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gray-200">
                  <GitHubIcon className="h-6 w-6 text-gray-500" />
                </div>
                <div>
                  <p className="font-medium text-gray-800">Not Connected</p>
                  <p className="text-sm text-gray-600">
                    Connect your GitHub account to sync repositories
                  </p>
                </div>
              </div>

              {/* Connect button */}
              <button
                onClick={() => connectGitHubMutation.mutate()}
                disabled={connectGitHubMutation.isPending}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 disabled:opacity-50"
              >
                <GitHubIcon className="h-5 w-5" />
                {connectGitHubMutation.isPending ? "Redirecting..." : "Connect GitHub Account"}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Danger Zone */}
      <div className="bg-white rounded-lg border border-red-200 shadow-sm">
        <div className="p-6 border-b border-red-200">
          <h2 className="text-lg font-semibold text-red-600">Danger Zone</h2>
          <p className="text-sm text-gray-500 mt-1">Irreversible actions for your account</p>
        </div>
        <div className="p-6">
          <div className="flex items-center justify-between rounded-lg border border-red-200 p-4">
            <div>
              <p className="font-medium">Delete Account</p>
              <p className="text-sm text-gray-500">
                Permanently delete your account and all associated data
              </p>
            </div>
            <button
              disabled
              className="px-4 py-2 border border-red-300 text-red-600 rounded-lg opacity-50 cursor-not-allowed"
            >
              Delete Account
            </button>
          </div>
        </div>
      </div>

      {/* Generate API Key Modal */}
      {showGenerateDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            {createdKey ? (
              // Show created key
              <div className="p-6">
                <div className="flex items-center gap-2 text-green-600 mb-4">
                  <CheckIcon className="h-5 w-5" />
                  <h3 className="text-lg font-semibold">API Key Created Successfully</h3>
                </div>
                <p className="text-sm text-gray-500 mb-4">
                  Make sure to copy your API key now. You won&apos;t be able to see it again!
                </p>
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-4">
                  <div className="flex items-start gap-3">
                    <ExclamationTriangleIcon className="h-5 w-5 text-amber-600 mt-0.5" />
                    <p className="text-sm text-amber-800">
                      This is the only time you&apos;ll see this API key. Save it somewhere secure.
                    </p>
                  </div>
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Your API Key</label>
                  <div className="flex gap-2">
                    <code className="flex-1 rounded-lg border bg-gray-100 p-3 text-sm font-mono break-all">
                      {createdKey.api_key}
                    </code>
                    <button
                      onClick={handleCopyApiKey}
                      className="p-3 border rounded-lg hover:bg-gray-50"
                    >
                      {copiedKey ? (
                        <CheckIcon className="h-4 w-4 text-green-600" />
                      ) : (
                        <ClipboardIcon className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                </div>
                <button
                  onClick={handleCloseCreatedKey}
                  className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Done, I&apos;ve saved my key
                </button>
              </div>
            ) : (
              // Generate key form
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold">Generate New API Key</h3>
                  <button onClick={() => setShowGenerateDialog(false)} className="text-gray-400 hover:text-gray-600">
                    <XMarkIcon className="h-5 w-5" />
                  </button>
                </div>
                <p className="text-sm text-gray-500 mb-4">
                  Create a personal access token for VS Code extension or CLI tools.
                </p>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                    <input
                      type="text"
                      value={newKeyName}
                      onChange={(e) => setNewKeyName(e.target.value)}
                      placeholder="VS Code Extension"
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Expiration</label>
                    <select
                      value={newKeyExpiry}
                      onChange={(e) => setNewKeyExpiry(e.target.value)}
                      className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="30">30 days</option>
                      <option value="90">90 days (Recommended)</option>
                      <option value="365">1 year</option>
                      <option value="never">Never expires</option>
                    </select>
                  </div>
                </div>
                <div className="flex gap-3 mt-6">
                  <button
                    onClick={() => setShowGenerateDialog(false)}
                    className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleGenerateApiKey}
                    disabled={createApiKeyMutation.isPending || !newKeyName.trim()}
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                  >
                    {createApiKeyMutation.isPending ? "Generating..." : "Generate API Key"}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Revoke Confirmation Modal */}
      {showRevokeDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
            <h3 className="text-lg font-semibold mb-2">Revoke API Key?</h3>
            <p className="text-sm text-gray-500 mb-4">
              This will immediately invalidate the API key. Any applications using this key will no longer be able to authenticate.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowRevokeDialog(null)}
                className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => revokeApiKeyMutation.mutate(showRevokeDialog)}
                disabled={revokeApiKeyMutation.isPending}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
              >
                {revokeApiKeyMutation.isPending ? "Revoking..." : "Revoke Key"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Disconnect GitHub Confirmation Modal */}
      {showDisconnectDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
            <h3 className="text-lg font-semibold mb-2">Disconnect GitHub Account?</h3>
            <p className="text-sm text-gray-500 mb-4">
              This will remove the connection between your SDLC Orchestrator account and GitHub. Your existing projects will not be affected, but automatic syncing will stop.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowDisconnectDialog(false)}
                className="flex-1 px-4 py-2 border rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => disconnectGitHubMutation.mutate()}
                disabled={disconnectGitHubMutation.isPending}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
              >
                {disconnectGitHubMutation.isPending ? "Disconnecting..." : "Disconnect"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
