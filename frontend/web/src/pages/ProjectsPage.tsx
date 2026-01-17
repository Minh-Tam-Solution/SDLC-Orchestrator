/**
 * File: frontend/web/src/pages/ProjectsPage.tsx
 * Version: 1.1.0
 * Status: ACTIVE - STAGE 03 (BUILD)
 * Date: 2026-01-17
 * Authority: Frontend Lead + CTO Approved
 * Foundation: SDLC 4.9 Complete Lifecycle, Zero Mock Policy
 *
 * Description:
 * Projects list page showing all SDLC projects with their gate status.
 * Sprint 73: Added team filter functionality (S73-T06~T08)
 */

import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import DashboardLayout from '@/components/layout/DashboardLayout'
import CreateProjectDialog from '@/components/projects/CreateProjectDialog'
import EditProjectDialog from '@/components/projects/EditProjectDialog'
import DeleteProjectDialog from '@/components/projects/DeleteProjectDialog'
import { useTeams, type Team } from '@/hooks/useTeams'
import apiClient from '@/api/client'
import type { Project as ApiProject } from '@/types/api'

interface Project {
  id: string
  name: string
  description: string
  current_stage: string
  gate_status: 'passed' | 'failed' | 'pending' | 'not_started'
  progress: number
  team_id?: string
  team?: {
    id: string
    name: string
    slug: string
  }
  created_at: string
  updated_at: string
}

/** Filter state for projects */
interface ProjectFilters {
  search: string
  teamId: string | null
  status: string | null
}

/**
 * Projects page component
 *
 * @returns Projects list with gate status and team filtering
 */
export default function ProjectsPage() {
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [editProject, setEditProject] = useState<Project | null>(null)
  const [deleteProject, setDeleteProject] = useState<Project | null>(null)
  
  // Filter state - Sprint 73 Team Filter
  const [filters, setFilters] = useState<ProjectFilters>({
    search: '',
    teamId: null,
    status: null,
  })

  // Fetch teams for filter dropdown
  const { data: teams = [], isLoading: teamsLoading } = useTeams()

  // Fetch projects
  const { data: projects, isLoading: projectsLoading } = useQuery<Project[]>({
    queryKey: ['projects'],
    queryFn: async () => {
      try {
        const response = await apiClient.get<Project[]>('/projects')
        return response.data
      } catch {
        // Return empty array if API not available yet
        return []
      }
    },
  })

  // Filter projects based on current filters
  const filteredProjects = useMemo(() => {
    if (!projects) return []
    
    return projects.filter((project) => {
      // Search filter - name or description
      if (filters.search) {
        const searchLower = filters.search.toLowerCase()
        const matchesSearch =
          project.name.toLowerCase().includes(searchLower) ||
          project.description?.toLowerCase().includes(searchLower)
        if (!matchesSearch) return false
      }
      
      // Team filter
      if (filters.teamId) {
        // "no-team" special value for projects without team
        if (filters.teamId === 'no-team') {
          if (project.team_id) return false
        } else {
          if (project.team_id !== filters.teamId) return false
        }
      }
      
      // Status filter
      if (filters.status && project.gate_status !== filters.status) {
        return false
      }
      
      return true
    })
  }, [projects, filters])

  // Get team name for display
  const getTeamName = (teamId: string | undefined) => {
    if (!teamId) return null
    const team = teams.find((t: Team) => t.id === teamId)
    return team?.name || null
  }

  const isLoading = projectsLoading || teamsLoading

  const getStatusColor = (status: Project['gate_status']) => {
    switch (status) {
      case 'passed':
        return 'bg-green-100 text-green-700'
      case 'failed':
        return 'bg-red-100 text-red-700'
      case 'pending':
        return 'bg-yellow-100 text-yellow-700'
      default:
        return 'bg-gray-100 text-gray-700'
    }
  }

  const getStageLabel = (stage: string) => {
    const stages: Record<string, string> = {
      '00': 'WHY - Foundation',
      '01': 'WHAT - Planning',
      '02': 'HOW - Design',
      '03': 'BUILD - Development',
      '04': 'VERIFY - Testing',
      '05': 'LAUNCH - Deployment',
      '06': 'OPERATE - Maintenance',
      '07': 'OPTIMIZE - Improvement',
      '08': 'SUNSET - End of Life',
      '09': 'ARCHIVE - Documentation',
    }
    return stages[stage] || stage
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Page header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Projects</h1>
            <p className="text-muted-foreground">
              Manage your SDLC projects and track gate progress
            </p>
          </div>
          <Button onClick={() => setCreateDialogOpen(true)}>
            <svg className="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            New Project
          </Button>
        </div>

        {/* Filters Section - Sprint 73 S73-T06~T08 */}
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search Input */}
          <div className="relative flex-1 max-w-sm">
            <svg
              className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            <Input
              placeholder="Search projects..."
              className="pl-9"
              value={filters.search}
              onChange={(e) => setFilters((prev) => ({ ...prev, search: e.target.value }))}
            />
          </div>

          {/* Team Filter */}
          <Select
            value={filters.teamId || 'all'}
            onValueChange={(value) =>
              setFilters((prev) => ({ ...prev, teamId: value === 'all' ? null : value }))
            }
          >
            <SelectTrigger className="w-full sm:w-[200px]">
              <div className="flex items-center gap-2">
                <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
                <SelectValue placeholder="All Teams" />
              </div>
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Teams</SelectItem>
              <SelectItem value="no-team">No Team</SelectItem>
              {teams.map((team: Team) => (
                <SelectItem key={team.id} value={team.id}>
                  {team.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {/* Status Filter */}
          <Select
            value={filters.status || 'all'}
            onValueChange={(value) =>
              setFilters((prev) => ({ ...prev, status: value === 'all' ? null : value }))
            }
          >
            <SelectTrigger className="w-full sm:w-[160px]">
              <div className="flex items-center gap-2">
                <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <SelectValue placeholder="All Status" />
              </div>
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="passed">Passed</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="failed">Failed</SelectItem>
              <SelectItem value="not_started">Not Started</SelectItem>
            </SelectContent>
          </Select>

          {/* Clear Filters */}
          {(filters.search || filters.teamId || filters.status) && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setFilters({ search: '', teamId: null, status: null })}
              className="h-10"
            >
              <svg className="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
              Clear
            </Button>
          )}
        </div>

        {/* Filter Summary */}
        {(filters.teamId || filters.status) && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span>Showing</span>
            <span className="font-medium text-foreground">{filteredProjects.length}</span>
            <span>of</span>
            <span className="font-medium text-foreground">{projects?.length || 0}</span>
            <span>projects</span>
            {filters.teamId && (
              <Badge variant="secondary" className="ml-2">
                Team: {filters.teamId === 'no-team' ? 'None' : getTeamName(filters.teamId) || 'Unknown'}
              </Badge>
            )}
            {filters.status && (
              <Badge variant="secondary" className="ml-1 capitalize">
                {filters.status.replace('_', ' ')}
              </Badge>
            )}
          </div>
        )}

        {/* Create Project Dialog */}
        <CreateProjectDialog
          open={createDialogOpen}
          onOpenChange={setCreateDialogOpen}
        />

        {/* Edit Project Dialog */}
        {editProject && (
          <EditProjectDialog
            open={!!editProject}
            onOpenChange={(open) => !open && setEditProject(null)}
            project={editProject as ApiProject}
            onSuccess={() => setEditProject(null)}
          />
        )}

        {/* Delete Project Dialog */}
        {deleteProject && (
          <DeleteProjectDialog
            open={!!deleteProject}
            onOpenChange={(open) => !open && setDeleteProject(null)}
            project={deleteProject as ApiProject}
            redirectAfterDelete={false}
            onSuccess={() => setDeleteProject(null)}
          />
        )}

        {/* Projects grid */}
        {isLoading ? (
          <div className="text-center text-muted-foreground py-12">Loading projects...</div>
        ) : filteredProjects.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredProjects.map((project) => (
              <Card key={project.id} className="h-full hover:shadow-md transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <Link to={`/projects/${project.id}`} className="flex-1 cursor-pointer">
                      <CardTitle className="text-lg hover:text-primary transition-colors">
                        {project.name}
                      </CardTitle>
                      <CardDescription className="mt-1 line-clamp-2">
                        {project.description}
                      </CardDescription>
                    </Link>
                    <div className="flex items-center gap-2 ml-2">
                      <span
                        className={`rounded-full px-2 py-1 text-xs font-medium ${getStatusColor(
                          project.gate_status
                        )}`}
                      >
                        {project.gate_status}
                      </span>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                            </svg>
                            <span className="sr-only">Open menu</span>
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem asChild>
                            <Link to={`/projects/${project.id}`}>
                              <svg className="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                              </svg>
                              View Details
                            </Link>
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => setEditProject(project)}>
                            <svg className="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                            </svg>
                            Edit Project
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            className="text-red-600 focus:text-red-600"
                            onClick={() => setDeleteProject(project)}
                          >
                            <svg className="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                            Delete Project
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </div>
                  {/* Team Badge - Sprint 73 S73-T06~T08 */}
                  {project.team_id && (
                    <div className="mt-2">
                      <Badge variant="outline" className="text-xs">
                        <svg className="mr-1 h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                        {project.team?.name || getTeamName(project.team_id) || 'Team'}
                      </Badge>
                    </div>
                  )}
                </CardHeader>
                <Link to={`/projects/${project.id}`}>
                  <CardContent className="cursor-pointer">
                    <div className="space-y-3">
                      {/* Current stage */}
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Current Stage</span>
                        <span className="font-medium">{getStageLabel(project.current_stage)}</span>
                      </div>

                      {/* Progress bar */}
                      <div className="space-y-1">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">Progress</span>
                          <span className="font-medium">{project.progress}%</span>
                        </div>
                        <div className="h-2 w-full rounded-full bg-muted">
                          <div
                            className="h-2 rounded-full bg-primary transition-all"
                            style={{ width: `${project.progress}%` }}
                          />
                        </div>
                      </div>

                      {/* Updated at */}
                      <div className="text-xs text-muted-foreground">
                        Updated {new Date(project.updated_at).toLocaleDateString()}
                      </div>
                    </div>
                  </CardContent>
                </Link>
              </Card>
            ))}
          </div>
        ) : projects && projects.length > 0 ? (
          /* No results matching current filters */
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <svg
                className="h-12 w-12 text-muted-foreground mb-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
              <h3 className="text-lg font-medium">No projects match your filters</h3>
              <p className="text-muted-foreground text-center mt-1">
                Try adjusting your search or filter criteria
              </p>
              <Button
                className="mt-4"
                variant="outline"
                onClick={() => setFilters({ search: '', teamId: null, status: null })}
              >
                <svg className="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
                Clear Filters
              </Button>
            </CardContent>
          </Card>
        ) : (
          /* No projects exist yet */
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <svg
                className="h-12 w-12 text-muted-foreground mb-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
                />
              </svg>
              <h3 className="text-lg font-medium">No projects yet</h3>
              <p className="text-muted-foreground text-center mt-1">
                Get started by creating your first SDLC project
              </p>
              <Button className="mt-4" onClick={() => setCreateDialogOpen(true)}>
                <svg className="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Create Project
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  )
}
