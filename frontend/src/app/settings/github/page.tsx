"use client";

import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { GitHubSettingsPanel } from "@/components/github/GitHubSettingsPanel";
import { GitHubRepoList } from "@/components/github/GitHubRepoList";
import { useGitHub } from "@/hooks/useGitHub";

export default function GitHubSettingsPage() {
  const router = useRouter();
  const { isConnected, isLoadingConnection } = useGitHub();

  if (isLoadingConnection) {
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

  return (
    <div className="container mx-auto py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-4 mb-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push("/app/settings")}
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
            Back to Settings
          </Button>
        </div>

        <div>
          <h1 className="text-3xl font-bold tracking-tight">GitHub Integration</h1>
          <p className="text-muted-foreground mt-2">
            Manage your GitHub connection and repository access
          </p>
        </div>
      </div>

      {/* Settings Panel */}
      <div className="space-y-6">
        <GitHubSettingsPanel />

        {/* Repository List (only show if connected) */}
        {isConnected && (
          <div>
            <h2 className="text-xl font-semibold mb-4">Your Repositories</h2>
            <GitHubRepoList showConnectButton={false} />
          </div>
        )}
      </div>

      {/* Help Section */}
      <div className="mt-8 rounded-lg border bg-muted/50 p-6">
        <h3 className="text-lg font-semibold mb-3">How GitHub Integration Works</h3>
        <div className="space-y-3 text-sm text-muted-foreground">
          <div className="flex gap-3">
            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs">
              1
            </div>
            <div>
              <p className="font-medium text-foreground">Connect your GitHub account</p>
              <p>Authorize SDLC Orchestrator to access your GitHub repositories</p>
            </div>
          </div>
          <div className="flex gap-3">
            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs">
              2
            </div>
            <div>
              <p className="font-medium text-foreground">Select repositories</p>
              <p>Choose which repositories to connect to your projects</p>
            </div>
          </div>
          <div className="flex gap-3">
            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs">
              3
            </div>
            <div>
              <p className="font-medium text-foreground">Automatic synchronization</p>
              <p>
                Webhooks automatically sync pull requests, commits, and repository changes
              </p>
            </div>
          </div>
          <div className="flex gap-3">
            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs">
              4
            </div>
            <div>
              <p className="font-medium text-foreground">Quality gate integration</p>
              <p>
                SDLC Orchestrator validates code quality before merging pull requests
              </p>
            </div>
          </div>
        </div>

        <div className="mt-6 rounded-lg border border-blue-200 bg-blue-50 p-4 dark:border-blue-900 dark:bg-blue-950">
          <div className="flex items-start gap-3">
            <svg
              className="h-5 w-5 text-blue-600 dark:text-blue-500"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"
              />
            </svg>
            <div>
              <p className="text-sm font-medium text-blue-800 dark:text-blue-200">
                Privacy & Security
              </p>
              <p className="mt-1 text-sm text-blue-700 dark:text-blue-300">
                Your GitHub access token is encrypted and never shared. You can
                disconnect at any time, and all webhooks will be automatically removed.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
