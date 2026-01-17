/**
 * File: frontend/web/src/components/projects/CreateProjectDialog.tsx
 * Version: 2.3.0
 * Status: ACTIVE - Sprint 45
 * Date: December 23, 2025
 * Authority: Frontend Lead + CTO Approved
 * Foundation: User-Onboarding-Flow-Architecture.md v2.2
 *
 * Description:
 * Dialog for creating new SDLC projects with three scenarios:
 * - Scenario A: New Project (From Scratch) - Name, Description, Tier → Create project in backend
 * - Scenario B: Import from Local - VSCode Extension for local file operations
 * - Scenario C: Import from GitHub - Clone + AI Analysis + Tier Selection
 *
 * Note: Local filesystem operations (Scenarios A folder creation, B full flow)
 * are handled by the VSCode Extension. Web app manages project metadata.
 */

import { useState, useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import apiClient from '@/api/client'
import { GitHubRepository, GitHubRepositoryListResponse } from '@/types/api'
import { useTeams } from '@/hooks/useTeams'

type CreationStep = 'choice' | 'new-form' | 'local-info' | 'github-select' | 'github-analyze' | 'github-tier'
type PolicyPack = 'lite' | 'standard' | 'professional' | 'enterprise'

interface CreateProjectDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

interface ProjectCreateData {
  name: string
  description: string
  policy_pack?: PolicyPack
  team_id?: string
  github_repo_id?: number
  github_repo_full_name?: string
}

interface ProjectResponse {
  id: string
  name: string
  slug: string
  description: string | null
}

interface PolicyPackInfo {
  name: PolicyPack
  title: string
  description: string
  features: string[]
  bestFor: string
}

const POLICY_PACKS: PolicyPackInfo[] = [
  {
    name: 'lite',
    title: 'Lite',
    description: 'Minimal governance - trust the team, move fast',
    features: ['Basic gates (G0.1, G1, G3, G5)', 'README + basic docs only'],
    bestFor: 'Solo devs, MVPs, hackathons',
  },
  {
    name: 'standard',
    title: 'Standard',
    description: 'Balanced governance - quality with agility',
    features: ['Core gates (G0.1-G6)', 'CI/CD + security scanning'],
    bestFor: 'Small teams (3-10), growing startups',
  },
  {
    name: 'professional',
    title: 'Professional',
    description: 'Strong governance - enterprise-grade quality',
    features: ['Full gates + 80% test coverage', 'SBOM, SAST, OWASP L1'],
    bestFor: 'Medium teams, regulated industries',
  },
  {
    name: 'enterprise',
    title: 'Enterprise',
    description: 'Maximum governance - audit-ready compliance',
    features: ['All gates + quarterly audits', 'OWASP L2+, 95% coverage'],
    bestFor: 'Large orgs, finance, healthcare',
  },
]

interface RepositoryAnalysis {
  project_type: string
  languages: Record<string, number>
  recommended_policy_pack?: PolicyPack
  stage_mappings?: Array<{ folder: string; stage: string }>
  repository?: {
    name: string
    full_name: string
    description: string | null
    language: string | null
  }
  team_size_estimate?: number
}

/**
 * Create Project Dialog Component (v2.2)
 * Supports 3 project creation scenarios per User-Onboarding-Flow-Architecture.md v2.2
 */
export default function CreateProjectDialog({
  open,
  onOpenChange,
}: CreateProjectDialogProps) {
  const [step, setStep] = useState<CreationStep>('choice')
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [selectedTier, setSelectedTier] = useState<PolicyPack>('standard')
  const [selectedTeam, setSelectedTeam] = useState<string>('')
  const [recommendedTier, setRecommendedTier] = useState<PolicyPack | null>(null)
  const [selectedRepo, setSelectedRepo] = useState<GitHubRepository | null>(null)
  const [repoSearch, setRepoSearch] = useState('')
  const [error, setError] = useState<string | null>(null)
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  // Fetch teams for selection (Sprint 73)
  const { data: teams = [] } = useTeams()

  // Check if GitHub is connected
  const { data: githubStatus } = useQuery({
    queryKey: ['github', 'status'],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/github/status')
        return response.data
      } catch {
        return { connected: false }
      }
    },
    enabled: open,
  })

  // Fetch repositories when on GitHub select step
  const { data: repos = [], isLoading: loadingRepos } = useQuery<GitHubRepository[]>({
    queryKey: ['github', 'repositories'],
    queryFn: async () => {
      const response = await apiClient.get<GitHubRepositoryListResponse>('/github/repositories')
      const repositories = response.data.repositories || []
      return repositories.sort((a, b) => {
        const scoreA = (a.stargazers_count || 0) * 10 + new Date(a.updated_at || 0).getTime()
        const scoreB = (b.stargazers_count || 0) * 10 + new Date(b.updated_at || 0).getTime()
        return scoreB - scoreA
      })
    },
    enabled: step === 'github-select' && githubStatus?.connected,
  })

  // Analyze repository when selected
  const { data: analysis } = useQuery<RepositoryAnalysis>({
    queryKey: ['github', 'analyze', selectedRepo?.full_name],
    queryFn: async () => {
      if (!selectedRepo) return null
      const [owner, repoName] = selectedRepo.full_name.split('/')
      const response = await apiClient.get(`/github/repositories/${owner}/${repoName}/analyze`)
      return response.data
    },
    enabled: step === 'github-analyze' && !!selectedRepo,
  })

  // Set recommended tier when analysis is ready
  useEffect(() => {
    if (analysis && step === 'github-analyze') {
      const rec = (analysis.recommended_policy_pack || 'standard') as PolicyPack
      setRecommendedTier(rec)
      setSelectedTier(rec)
      // Auto-advance to tier selection
      setStep('github-tier')
    }
  }, [analysis, step])

  // Create project mutation
  const createMutation = useMutation<ProjectResponse, Error, ProjectCreateData>({
    mutationFn: async (data) => {
      const response = await apiClient.post<ProjectResponse>('/projects', data)
      return response.data
    },
    onSuccess: (project) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      handleClose()
      navigate(`/projects/${project.id}`)
    },
    onError: (err) => {
      setError(err.message || 'Failed to create project')
    },
  })

  const handleClose = () => {
    setStep('choice')
    setName('')
    setDescription('')
    setSelectedTier('standard')
    setSelectedTeam('')
    setRecommendedTier(null)
    setSelectedRepo(null)
    setRepoSearch('')
    setError(null)
    onOpenChange(false)
  }

  // Scenario A: Create new project from scratch
  const handleCreateNew = (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) {
      setError('Project name is required')
      return
    }

    createMutation.mutate({
      name: name.trim(),
      description: description.trim(),
      policy_pack: selectedTier,
      team_id: selectedTeam || undefined,
    })
  }

  // Scenario C: Import from GitHub
  const handleGitHubImport = () => {
    if (!githubStatus?.connected) {
      // Redirect to connect GitHub
      window.location.href = '/api/github/oauth/authorize'
      return
    }
    setStep('github-select')
  }

  const handleSelectRepo = (repo: GitHubRepository) => {
    setSelectedRepo(repo)
    setName(repo.name)
    setDescription(repo.description || '')
    setRecommendedTier(null)
    setStep('github-analyze')
  }

  const handleCreateFromGitHub = () => {
    if (!selectedRepo) return

    createMutation.mutate({
      name: name.trim() || selectedRepo.name,
      description: description.trim() || selectedRepo.description || '',
      policy_pack: selectedTier,
      team_id: selectedTeam || undefined,
      github_repo_id: selectedRepo.id,
      github_repo_full_name: selectedRepo.full_name,
    })
  }

  const filteredRepos = repos.filter(
    (repo) =>
      repo.name.toLowerCase().includes(repoSearch.toLowerCase()) ||
      repo.full_name.toLowerCase().includes(repoSearch.toLowerCase())
  )

  // Tier Selection Component (reused across scenarios)
  const TierSelection = ({ showRecommendation = false }: { showRecommendation?: boolean }) => (
    <div>
      <div className="text-sm font-medium mb-2">Choose Governance Tier</div>
      {showRecommendation && recommendedTier && (
        <div className="rounded-lg bg-blue-50 dark:bg-blue-950 p-2 text-xs text-blue-900 dark:text-blue-100 mb-2">
          💡 Based on codebase analysis, we recommend <strong className="capitalize">{recommendedTier}</strong>.
          You can choose a different tier based on your governance appetite.
        </div>
      )}
      <div className="grid gap-2">
        {POLICY_PACKS.map((pack) => (
          <Card
            key={pack.name}
            className={`cursor-pointer transition-all ${
              selectedTier === pack.name
                ? 'border-primary border-2 bg-primary/5'
                : 'hover:bg-muted/50'
            }`}
            onClick={() => setSelectedTier(pack.name)}
          >
            <CardContent className="p-2">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-sm">{pack.title}</span>
                    {showRecommendation && recommendedTier === pack.name && (
                      <span className="text-xs px-1.5 py-0.5 rounded bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300">
                        Recommended
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-muted-foreground">{pack.description}</div>
                  <div className="text-xs text-muted-foreground mt-0.5">Best for: {pack.bestFor}</div>
                </div>
                <div className={`w-4 h-4 rounded-full border-2 flex-shrink-0 ${
                  selectedTier === pack.name
                    ? 'border-primary bg-primary'
                    : 'border-muted-foreground/30'
                }`} />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )

  // Render based on current step
  const renderContent = () => {
    switch (step) {
      // Step: Choose creation method
      case 'choice':
        return (
          <>
            <DialogHeader>
              <DialogTitle>Create New Project</DialogTitle>
              <DialogDescription>
                Choose how you want to create your project
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-3 py-4">
              {/* Scenario A: New Project from scratch */}
              <Card
                className="cursor-pointer hover:bg-muted/50 transition-colors"
                onClick={() => setStep('new-form')}
              >
                <CardContent className="p-4">
                  <div className="flex items-center gap-4">
                    <div className="text-2xl">✨</div>
                    <div className="flex-1">
                      <div className="font-semibold">Create New Project</div>
                      <div className="text-sm text-muted-foreground">
                        Start fresh with SDLC 5.1.1 folder structure
                      </div>
                    </div>
                    <div className="text-muted-foreground">→</div>
                  </div>
                </CardContent>
              </Card>

              {/* Scenario B: Import from Local (VSCode Extension or Desktop) */}
              <Card
                className="cursor-pointer hover:bg-muted/50 transition-colors"
                onClick={() => setStep('local-info')}
              >
                <CardContent className="p-4">
                  <div className="flex items-center gap-4">
                    <div className="text-2xl">📁</div>
                    <div className="flex-1">
                      <div className="font-semibold">Import from Local Folder</div>
                      <div className="text-sm text-muted-foreground">
                        Link existing project from your computer
                      </div>
                      <div className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                        Use VSCode Extension for local operations
                      </div>
                    </div>
                    <div className="text-muted-foreground">→</div>
                  </div>
                </CardContent>
              </Card>

              {/* Scenario C: Import from GitHub */}
              <Card
                className="cursor-pointer hover:bg-muted/50 transition-colors"
                onClick={handleGitHubImport}
              >
                <CardContent className="p-4">
                  <div className="flex items-center gap-4">
                    <div className="text-2xl">🐙</div>
                    <div className="flex-1">
                      <div className="font-semibold">Import from GitHub</div>
                      <div className="text-sm text-muted-foreground">
                        Connect repository with AI-powered tier recommendation
                      </div>
                      {!githubStatus?.connected && (
                        <div className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                          Will connect GitHub first
                        </div>
                      )}
                    </div>
                    <div className="text-muted-foreground">→</div>
                  </div>
                </CardContent>
              </Card>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={handleClose}>
                Cancel
              </Button>
            </DialogFooter>
          </>
        )

      // Step: New project form (Scenario A)
      case 'new-form':
        return (
          <form onSubmit={handleCreateNew}>
            <DialogHeader>
              <DialogTitle>Create New Project</DialogTitle>
              <DialogDescription>
                Set up a new project with SDLC 5.1.1 governance
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4 max-h-[60vh] overflow-y-auto">
              {/* Project Info */}
              <div className="grid gap-3">
                <div className="grid gap-2">
                  <Label htmlFor="new-name">Project Name *</Label>
                  <Input
                    id="new-name"
                    placeholder="E.g., E-commerce Platform v2.0"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    disabled={createMutation.isPending}
                    autoFocus
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="new-description">Description</Label>
                  <Textarea
                    id="new-description"
                    placeholder="Describe your project goals and scope..."
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    disabled={createMutation.isPending}
                    rows={2}
                  />
                </div>
                {/* Team Selection - Sprint 73 */}
                <div className="grid gap-2">
                  <Label htmlFor="new-team">Team (optional)</Label>
                  <Select
                    value={selectedTeam}
                    onValueChange={setSelectedTeam}
                    disabled={createMutation.isPending}
                  >
                    <SelectTrigger id="new-team">
                      <SelectValue placeholder="Select a team..." />
                    </SelectTrigger>
                    <SelectContent>
                      {teams.length === 0 ? (
                        <div className="px-2 py-1.5 text-sm text-muted-foreground">
                          No teams available
                        </div>
                      ) : (
                        teams.map((team) => (
                          <SelectItem key={team.id} value={team.id}>
                            {team.name}
                          </SelectItem>
                        ))
                      )}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-muted-foreground">
                    Assign this project to a team for better organization
                  </p>
                </div>
              </div>

              {/* Tier Selection */}
              <TierSelection />

              {/* Info about folder creation */}
              <div className="rounded-lg bg-muted p-3 text-xs text-muted-foreground">
                <strong>What happens next:</strong>
                <ul className="list-disc list-inside mt-1 space-y-0.5">
                  <li>Project registered in Orchestrator database</li>
                  <li>SDLC configuration created with selected tier</li>
                  <li>Quality gates configured based on tier</li>
                </ul>
              </div>

              {error && (
                <div className="text-sm text-red-500 bg-red-50 dark:bg-red-950 rounded-md p-2">
                  {error}
                </div>
              )}
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setStep('choice')}
                disabled={createMutation.isPending}
              >
                Back
              </Button>
              <Button type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending ? 'Creating...' : 'Create Project'}
              </Button>
            </DialogFooter>
          </form>
        )

      // Step: Local import info (Scenario B - VSCode Extension)
      case 'local-info':
        return (
          <>
            <DialogHeader>
              <DialogTitle>Import from Local Folder</DialogTitle>
              <DialogDescription>
                Use the VSCode Extension for local folder operations
              </DialogDescription>
            </DialogHeader>
            <div className="py-6 text-center">
              <div className="text-4xl mb-4">💻</div>
              <p className="text-muted-foreground mb-4">
                To import projects from your local machine, use the <strong>SDLC Orchestrator VSCode Extension</strong>.
              </p>
              <div className="bg-muted rounded-lg p-4 text-left max-w-sm mx-auto">
                <p className="text-sm font-medium mb-2">In VSCode:</p>
                <ol className="text-sm text-muted-foreground list-decimal list-inside space-y-1">
                  <li>Open the Command Palette (Cmd/Ctrl + Shift + P)</li>
                  <li>Type "SDLC: Import Project"</li>
                  <li>Select your project folder</li>
                  <li>Choose governance tier</li>
                </ol>
              </div>
              <p className="text-sm text-muted-foreground mt-4">
                The VSCode Extension can:
              </p>
              <ul className="text-sm text-muted-foreground list-disc list-inside mt-2 text-left max-w-xs mx-auto">
                <li>Detect existing SDLC projects</li>
                <li>Analyze local codebases</li>
                <li>Create SDLC folder structures</li>
                <li>Initialize git repositories</li>
              </ul>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setStep('choice')}>
                Back
              </Button>
              <Button
                variant="secondary"
                onClick={() => window.open('vscode:extension/sdlc-orchestrator.sdlc-orchestrator', '_blank')}
              >
                Open in VSCode
              </Button>
            </DialogFooter>
          </>
        )

      // Step: GitHub repository selection (Scenario C)
      case 'github-select':
        return (
          <>
            <DialogHeader>
              <DialogTitle>Select Repository</DialogTitle>
              <DialogDescription>
                Choose a GitHub repository to import
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <Input
                placeholder="Search repositories..."
                value={repoSearch}
                onChange={(e) => setRepoSearch(e.target.value)}
              />
              <div className="max-h-72 overflow-y-auto space-y-2">
                {loadingRepos ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-primary mb-2"></div>
                    <p>Loading repositories...</p>
                  </div>
                ) : filteredRepos.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    No repositories found
                  </div>
                ) : (
                  filteredRepos.map((repo) => (
                    <Card
                      key={repo.id}
                      className="cursor-pointer hover:bg-muted/50 transition-colors"
                      onClick={() => handleSelectRepo(repo)}
                    >
                      <CardContent className="p-3">
                        <div className="font-medium">{repo.name}</div>
                        <div className="text-sm text-muted-foreground">{repo.full_name}</div>
                        {repo.description && (
                          <div className="text-sm text-muted-foreground mt-1 line-clamp-1">
                            {repo.description}
                          </div>
                        )}
                        <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                          {repo.language && <span>● {repo.language}</span>}
                          {repo.stargazers_count > 0 && <span>⭐ {repo.stargazers_count}</span>}
                        </div>
                      </CardContent>
                    </Card>
                  ))
                )}
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setStep('choice')}>
                Back
              </Button>
            </DialogFooter>
          </>
        )

      // Step: Analyzing GitHub repo (Scenario C)
      case 'github-analyze':
        return (
          <>
            <DialogHeader>
              <DialogTitle>Analyzing Repository</DialogTitle>
              <DialogDescription>
                Analyzing {selectedRepo?.full_name} to recommend governance tier
              </DialogDescription>
            </DialogHeader>
            <div className="py-8 text-center">
              <div className="inline-block animate-spin rounded-full h-10 w-10 border-b-2 border-primary mb-4"></div>
              <p className="text-muted-foreground">Analyzing codebase...</p>
              <p className="text-xs text-muted-foreground mt-2">
                Scanning languages, file structure, and team activity
              </p>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setStep('github-select')}>
                Cancel
              </Button>
            </DialogFooter>
          </>
        )

      // Step: Configure GitHub project with tier (Scenario C)
      case 'github-tier':
        return (
          <>
            <DialogHeader>
              <DialogTitle>Configure Project</DialogTitle>
              <DialogDescription>
                Review analysis and select governance tier for {selectedRepo?.name}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4 max-h-[60vh] overflow-y-auto">
              {/* Project Info */}
              <div className="grid gap-3">
                <div className="grid gap-2">
                  <Label htmlFor="github-name">Project Name</Label>
                  <Input
                    id="github-name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="github-description">Description</Label>
                  <Textarea
                    id="github-description"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    rows={2}
                  />
                </div>
                {/* Team Selection - Sprint 73 */}
                <div className="grid gap-2">
                  <Label htmlFor="github-team">Team (optional)</Label>
                  <Select
                    value={selectedTeam}
                    onValueChange={setSelectedTeam}
                    disabled={createMutation.isPending}
                  >
                    <SelectTrigger id="github-team">
                      <SelectValue placeholder="Select a team..." />
                    </SelectTrigger>
                    <SelectContent>
                      {teams.length === 0 ? (
                        <div className="px-2 py-1.5 text-sm text-muted-foreground">
                          No teams available
                        </div>
                      ) : (
                        teams.map((team) => (
                          <SelectItem key={team.id} value={team.id}>
                            {team.name}
                          </SelectItem>
                        ))
                      )}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Analysis Summary */}
              {analysis && (
                <Card>
                  <CardContent className="p-3">
                    <div className="text-sm font-medium text-muted-foreground mb-2">
                      Analysis Results
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>Type: <span className="font-medium capitalize">{analysis.project_type?.replace('_', ' ') || 'Unknown'}</span></div>
                      {analysis.team_size_estimate && (
                        <div>Team: <span className="font-medium">{analysis.team_size_estimate} devs</span></div>
                      )}
                    </div>
                    {analysis.languages && Object.keys(analysis.languages).length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {Object.keys(analysis.languages).slice(0, 4).map((lang) => (
                          <span key={lang} className="px-2 py-0.5 rounded bg-muted text-xs">
                            {lang}
                          </span>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}

              {/* Tier Selection with recommendation */}
              <TierSelection showRecommendation={true} />

              {error && (
                <div className="text-sm text-red-500 bg-red-50 dark:bg-red-950 rounded-md p-2">
                  {error}
                </div>
              )}
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setStep('github-select')}>
                Back
              </Button>
              <Button
                onClick={handleCreateFromGitHub}
                disabled={createMutation.isPending}
              >
                {createMutation.isPending ? 'Creating...' : 'Create Project'}
              </Button>
            </DialogFooter>
          </>
        )

      default:
        return null
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[550px]">
        {renderContent()}
      </DialogContent>
    </Dialog>
  )
}
