/**
 * File: frontend/web/src/pages/SettingsPage.tsx
 * Version: 1.1.0
 * Status: ACTIVE - STAGE 03 (BUILD)
 * Date: December 26, 2025
 * Authority: Frontend Lead + CTO Approved
 * Framework: SDLC 5.1.2 Complete Lifecycle
 *
 * Description:
 * Settings page for user preferences and integrations.
 * Includes GitHub connection status, API Keys management, and account management.
 *
 * Sprint 52B - API Key Management:
 * - Generate personal access tokens for VS Code extension
 * - List and revoke API keys
 * - Similar to GitHub Personal Access Tokens
 *
 * SDLC 5.1.2 Compliance:
 * - Pillar 1: Zero Mock Policy (Real API calls)
 * - Pillar 3: Quality Governance (Type hints, validation)
 */

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import DashboardLayout from '@/components/layout/DashboardLayout'
import apiClient from '@/api/client'
import { useAuth } from '@/contexts/AuthContext'
import type { GitHubConnectionStatus } from '@/types/api'

// API Key types
interface APIKey {
  id: string
  name: string
  prefix: string
  last_used_at: string | null
  expires_at: string | null
  is_active: boolean
  created_at: string
}

interface APIKeyCreatedResponse {
  id: string
  name: string
  api_key: string
  prefix: string
  expires_at: string | null
  created_at: string
}

/**
 * Settings page component
 *
 * Features:
 * - GitHub connection status display
 * - Connect/Disconnect GitHub account
 * - API Keys management (generate, list, revoke)
 * - User profile information
 * - Rate limit display
 */
export default function SettingsPage() {
  const { user } = useAuth()
  const queryClient = useQueryClient()

  // API Keys state
  const [showGenerateDialog, setShowGenerateDialog] = useState(false)
  const [newKeyName, setNewKeyName] = useState('VS Code Extension')
  const [newKeyExpiry, setNewKeyExpiry] = useState('90')
  const [createdKey, setCreatedKey] = useState<APIKeyCreatedResponse | null>(null)
  const [copiedKey, setCopiedKey] = useState(false)

  // Fetch API keys
  const { data: apiKeys, isLoading: isLoadingApiKeys } = useQuery<APIKey[]>({
    queryKey: ['api-keys'],
    queryFn: async () => {
      const response = await apiClient.get<APIKey[]>('/api-keys')
      return response.data
    },
  })

  // Create API key mutation
  const createApiKeyMutation = useMutation({
    mutationFn: async (data: { name: string; expires_in_days: number | null }) => {
      const response = await apiClient.post<APIKeyCreatedResponse>('/api-keys', data)
      return response.data
    },
    onSuccess: (data) => {
      setCreatedKey(data)
      queryClient.invalidateQueries({ queryKey: ['api-keys'] })
    },
  })

  // Revoke API key mutation
  const revokeApiKeyMutation = useMutation({
    mutationFn: async (keyId: string) => {
      await apiClient.delete(`/api-keys/${keyId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['api-keys'] })
    },
  })

  // Handle generate API key
  const handleGenerateApiKey = () => {
    const expiryDays = newKeyExpiry === 'never' ? null : parseInt(newKeyExpiry)
    createApiKeyMutation.mutate({ name: newKeyName, expires_in_days: expiryDays })
  }

  // Handle copy API key
  const handleCopyApiKey = async () => {
    if (createdKey?.api_key) {
      await navigator.clipboard.writeText(createdKey.api_key)
      setCopiedKey(true)
      setTimeout(() => setCopiedKey(false), 2000)
    }
  }

  // Handle close created key dialog
  const handleCloseCreatedKey = () => {
    setCreatedKey(null)
    setShowGenerateDialog(false)
    setNewKeyName('VS Code Extension')
    setNewKeyExpiry('90')
  }

  // Format date helper
  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Never'
    return new Date(dateStr).toLocaleDateString()
  }

  // Format relative time
  const formatRelativeTime = (dateStr: string | null) => {
    if (!dateStr) return 'Never used'
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins} min ago`
    if (diffHours < 24) return `${diffHours} hours ago`
    if (diffDays < 30) return `${diffDays} days ago`
    return formatDate(dateStr)
  }

  // Fetch GitHub connection status
  const { data: githubStatus, isLoading: isLoadingGitHub } = useQuery<GitHubConnectionStatus>({
    queryKey: ['github-status'],
    queryFn: async () => {
      const response = await apiClient.get<GitHubConnectionStatus>('/github/status')
      return response.data
    },
  })

  // Connect GitHub mutation
  const connectMutation = useMutation({
    mutationFn: async () => {
      // Call backend to get GitHub OAuth authorization URL
      // Backend endpoint: GET /api/v1/github/authorize
      const response = await apiClient.get<{ authorization_url: string; state: string }>('/github/authorize')
      return response.data.authorization_url
    },
    onSuccess: (authUrl) => {
      // Redirect to GitHub OAuth
      window.location.href = authUrl
    },
    onError: (error: Error & { response?: { status?: number; data?: { detail?: string } } }) => {
      console.error('Failed to get GitHub authorization URL:', error)
      // Could show a toast notification here
    },
  })

  // Disconnect GitHub mutation
  const disconnectMutation = useMutation({
    mutationFn: async () => {
      await apiClient.delete('/github/disconnect')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['github-status'] })
    },
  })

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Page header */}
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
          <p className="text-muted-foreground">
            Manage your account settings and integrations
          </p>
        </div>

        {/* Profile Section */}
        <Card>
          <CardHeader>
            <CardTitle>Profile</CardTitle>
            <CardDescription>Your account information</CardDescription>
          </CardHeader>
          <CardContent>
            {user ? (
              <div className="space-y-4">
                <div className="flex items-center gap-4">
                  <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 text-primary">
                    <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-lg font-medium">{user.name || user.email}</p>
                    <p className="text-sm text-muted-foreground">{user.email}</p>
                  </div>
                </div>
                <div className="grid gap-2 text-sm">
                  <div className="flex justify-between border-b pb-2">
                    <span className="text-muted-foreground">User ID</span>
                    <span className="font-mono text-xs">{user.id}</span>
                  </div>
                  <div className="flex justify-between border-b pb-2">
                    <span className="text-muted-foreground">Status</span>
                    <span className={user.is_active ? 'text-green-600' : 'text-red-600'}>
                      {user.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  <div className="flex justify-between border-b pb-2">
                    <span className="text-muted-foreground">Roles</span>
                    <span>{user.roles?.join(', ') || 'User'}</span>
                  </div>
                  {user.last_login_at && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Last Login</span>
                      <span>{new Date(user.last_login_at).toLocaleString()}</span>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <p className="text-muted-foreground">Loading profile...</p>
            )}
          </CardContent>
        </Card>

        {/* API Keys Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
              </svg>
              API Keys
            </CardTitle>
            <CardDescription>
              Generate personal access tokens for VS Code extension and CLI tools
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* API Keys List */}
              {isLoadingApiKeys ? (
                <div className="text-muted-foreground">Loading API keys...</div>
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
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <code className="rounded bg-muted px-2 py-0.5 text-xs">
                            {key.prefix}
                          </code>
                          <span>•</span>
                          <span>Last used: {formatRelativeTime(key.last_used_at)}</span>
                          <span>•</span>
                          <span>
                            Expires: {key.expires_at ? formatDate(key.expires_at) : 'Never'}
                          </span>
                        </div>
                      </div>
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-red-600 hover:text-red-700"
                            disabled={!key.is_active}
                          >
                            Revoke
                          </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle>Revoke API Key?</AlertDialogTitle>
                            <AlertDialogDescription>
                              This will immediately invalidate the API key "{key.name}".
                              Any applications using this key will no longer be able to authenticate.
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>Cancel</AlertDialogCancel>
                            <AlertDialogAction
                              onClick={() => revokeApiKeyMutation.mutate(key.id)}
                              className="bg-red-600 hover:bg-red-700"
                            >
                              Revoke Key
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="rounded-lg border border-dashed p-6 text-center">
                  <svg
                    className="mx-auto h-12 w-12 text-muted-foreground"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.5}
                      d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"
                    />
                  </svg>
                  <p className="mt-2 text-sm text-muted-foreground">
                    No API keys yet. Generate one to use with VS Code extension.
                  </p>
                </div>
              )}

              {/* Generate API Key Dialog */}
              <Dialog open={showGenerateDialog} onOpenChange={setShowGenerateDialog}>
                <DialogTrigger asChild>
                  <Button className="w-full">
                    <svg className="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    Generate New API Key
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  {createdKey ? (
                    // Show created key
                    <>
                      <DialogHeader>
                        <DialogTitle className="flex items-center gap-2 text-green-600">
                          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                          API Key Created Successfully
                        </DialogTitle>
                        <DialogDescription>
                          Make sure to copy your API key now. You won't be able to see it again!
                        </DialogDescription>
                      </DialogHeader>
                      <div className="space-y-4 py-4">
                        <div className="rounded-lg border bg-amber-50 p-4">
                          <div className="flex items-start gap-3">
                            <svg className="h-5 w-5 text-amber-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                            </svg>
                            <p className="text-sm text-amber-800">
                              This is the only time you'll see this API key. Save it somewhere secure.
                            </p>
                          </div>
                        </div>
                        <div className="space-y-2">
                          <Label>Your API Key</Label>
                          <div className="flex gap-2">
                            <code className="flex-1 rounded-lg border bg-muted p-3 text-sm font-mono break-all">
                              {createdKey.api_key}
                            </code>
                            <Button
                              variant="outline"
                              size="icon"
                              onClick={handleCopyApiKey}
                              className="shrink-0"
                            >
                              {copiedKey ? (
                                <svg className="h-4 w-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                              ) : (
                                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                </svg>
                              )}
                            </Button>
                          </div>
                        </div>
                        <div className="rounded-lg border p-4 text-sm">
                          <p className="font-medium mb-2">How to use in VS Code:</p>
                          <ol className="list-decimal list-inside space-y-1 text-muted-foreground">
                            <li>Open VS Code Command Palette (Ctrl+Shift+P)</li>
                            <li>Run "SDLC: Login to SDLC Orchestrator"</li>
                            <li>Select "API Token"</li>
                            <li>Paste your API key</li>
                          </ol>
                        </div>
                      </div>
                      <DialogFooter>
                        <Button onClick={handleCloseCreatedKey}>
                          Done, I've saved my key
                        </Button>
                      </DialogFooter>
                    </>
                  ) : (
                    // Generate key form
                    <>
                      <DialogHeader>
                        <DialogTitle>Generate New API Key</DialogTitle>
                        <DialogDescription>
                          Create a personal access token for VS Code extension or CLI tools.
                        </DialogDescription>
                      </DialogHeader>
                      <div className="space-y-4 py-4">
                        <div className="space-y-2">
                          <Label htmlFor="keyName">Name</Label>
                          <Input
                            id="keyName"
                            value={newKeyName}
                            onChange={(e) => setNewKeyName(e.target.value)}
                            placeholder="VS Code Extension"
                          />
                          <p className="text-xs text-muted-foreground">
                            A friendly name to identify this key
                          </p>
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="keyExpiry">Expiration</Label>
                          <Select value={newKeyExpiry} onValueChange={setNewKeyExpiry}>
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="30">30 days</SelectItem>
                              <SelectItem value="90">90 days (Recommended)</SelectItem>
                              <SelectItem value="365">1 year</SelectItem>
                              <SelectItem value="never">Never expires</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                      <DialogFooter>
                        <Button variant="outline" onClick={() => setShowGenerateDialog(false)}>
                          Cancel
                        </Button>
                        <Button
                          onClick={handleGenerateApiKey}
                          disabled={createApiKeyMutation.isPending || !newKeyName.trim()}
                        >
                          {createApiKeyMutation.isPending ? 'Generating...' : 'Generate API Key'}
                        </Button>
                      </DialogFooter>
                    </>
                  )}
                </DialogContent>
              </Dialog>
            </div>
          </CardContent>
        </Card>

        {/* GitHub Integration Section */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <svg className="h-6 w-6" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
              </svg>
              GitHub Integration
            </CardTitle>
            <CardDescription>
              Connect your GitHub account to sync repositories and create projects
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoadingGitHub ? (
              <div className="text-muted-foreground">Loading GitHub status...</div>
            ) : githubStatus?.connected ? (
              <div className="space-y-4">
                {/* Connected status */}
                <div className="flex items-center gap-3 rounded-lg border border-green-200 bg-green-50 p-4">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-100">
                    <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-green-800">Connected</p>
                    <p className="text-sm text-green-700">
                      Signed in as <span className="font-semibold">@{githubStatus.github_username}</span>
                    </p>
                  </div>
                  {githubStatus.github_avatar && (
                    <img
                      src={githubStatus.github_avatar}
                      alt={githubStatus.github_username || 'GitHub avatar'}
                      className="h-10 w-10 rounded-full"
                    />
                  )}
                </div>

                {/* Connection details */}
                <div className="grid gap-2 text-sm">
                  {githubStatus.connected_at && (
                    <div className="flex justify-between border-b pb-2">
                      <span className="text-muted-foreground">Connected Since</span>
                      <span>{new Date(githubStatus.connected_at).toLocaleDateString()}</span>
                    </div>
                  )}
                  {githubStatus.scopes && githubStatus.scopes.length > 0 && (
                    <div className="flex justify-between border-b pb-2">
                      <span className="text-muted-foreground">Permissions</span>
                      <span className="text-right">{githubStatus.scopes.join(', ')}</span>
                    </div>
                  )}
                  {githubStatus.rate_limit && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">API Rate Limit</span>
                      <span>
                        {githubStatus.rate_limit.remaining} / {githubStatus.rate_limit.limit} remaining
                      </span>
                    </div>
                  )}
                </div>

                {/* Disconnect button */}
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button variant="outline" className="text-red-600 hover:text-red-700">
                      <svg className="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                      </svg>
                      Disconnect GitHub
                    </Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>Disconnect GitHub Account?</AlertDialogTitle>
                      <AlertDialogDescription>
                        This will remove the connection between your SDLC Orchestrator account and GitHub.
                        Your existing projects will not be affected, but automatic syncing will stop.
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>Cancel</AlertDialogCancel>
                      <AlertDialogAction
                        onClick={() => disconnectMutation.mutate()}
                        disabled={disconnectMutation.isPending}
                        className="bg-red-600 hover:bg-red-700"
                      >
                        {disconnectMutation.isPending ? 'Disconnecting...' : 'Disconnect'}
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Not connected status */}
                <div className="flex items-center gap-3 rounded-lg border border-gray-200 bg-gray-50 p-4">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gray-200">
                    <svg className="h-6 w-6 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                    </svg>
                  </div>
                  <div>
                    <p className="font-medium text-gray-800">Not Connected</p>
                    <p className="text-sm text-gray-600">
                      Connect your GitHub account to sync repositories
                    </p>
                  </div>
                </div>

                {/* Benefits list */}
                <div className="rounded-lg border p-4">
                  <p className="font-medium mb-2">Benefits of connecting GitHub:</p>
                  <ul className="space-y-2 text-sm text-muted-foreground">
                    <li className="flex items-center gap-2">
                      <svg className="h-4 w-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      Import repositories as projects
                    </li>
                    <li className="flex items-center gap-2">
                      <svg className="h-4 w-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      Automatic evidence collection from PRs
                    </li>
                    <li className="flex items-center gap-2">
                      <svg className="h-4 w-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      Repository analysis for policy recommendations
                    </li>
                    <li className="flex items-center gap-2">
                      <svg className="h-4 w-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      Webhook integration for real-time updates
                    </li>
                  </ul>
                </div>

                {/* Connect button */}
                <Button
                  onClick={() => connectMutation.mutate()}
                  disabled={connectMutation.isPending}
                  className="w-full"
                >
                  {connectMutation.isPending ? (
                    'Redirecting to GitHub...'
                  ) : (
                    <>
                      <svg className="mr-2 h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                      </svg>
                      Connect GitHub Account
                    </>
                  )}
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Danger Zone */}
        <Card className="border-red-200">
          <CardHeader>
            <CardTitle className="text-red-600">Danger Zone</CardTitle>
            <CardDescription>
              Irreversible actions for your account
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between rounded-lg border border-red-200 p-4">
              <div>
                <p className="font-medium">Delete Account</p>
                <p className="text-sm text-muted-foreground">
                  Permanently delete your account and all associated data
                </p>
              </div>
              <Button variant="outline" className="text-red-600 hover:text-red-700" disabled>
                Delete Account
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}
