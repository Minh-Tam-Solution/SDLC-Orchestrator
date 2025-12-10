/**
 * File: frontend/web/src/pages/SOPGeneratorPage.tsx
 * Version: 1.0.0
 * Status: ACTIVE - Phase 2-Pilot Week 3 (SE 3.0 Track 1)
 * Date: 2025-01-06
 * Authority: Frontend Lead + CTO Approved
 * Foundation: BRS-PILOT-001, SDLC 5.1.0 Framework
 *
 * Description:
 * SOP Generator page for AI-assisted Standard Operating Procedure creation.
 * Integrates with Ollama via backend API for SOP generation.
 *
 * BRS Reference: BRS-PILOT-001-NQH-Bot-SOP-Generator.yaml
 * Functional Requirements:
 * - FR1: Generate SOP from workflow description
 * - FR2: Include 5 mandatory sections
 * - FR3: Support 5 SOP types
 * - FR6: MRP evidence display
 * - FR7: VCR approval workflow
 *
 * M3 Milestone: UI Complete
 */

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import DashboardLayout from '@/components/layout/DashboardLayout'
import apiClient from '@/api/client'

// ============================================================================
// Types
// ============================================================================

/**
 * SOP Type options (FR3: 5 types)
 */
type SOPType = 'deployment' | 'incident' | 'change' | 'backup' | 'security'

interface SOPTypeOption {
  value: SOPType
  label: string
  description: string
  icon: string
}

/**
 * SOP Generation Request
 */
interface GenerateSOPRequest {
  sop_type: SOPType
  workflow_description: string
  additional_context?: string
  project_id?: string
}

/**
 * Generated SOP Response
 */
interface GeneratedSOPResponse {
  sop_id: string
  sop_type: string
  title: string
  version: string
  status: string
  created_at: string
  purpose: string
  scope: string
  procedure: string
  roles: string
  quality_criteria: string
  markdown_content: string
  sha256_hash: string
  generation_time_ms: number
  ai_model: string
  mrp_id: string
  completeness_score: number
}

// ============================================================================
// Constants
// ============================================================================

/**
 * SOP Type options with metadata (FR3)
 */
const SOP_TYPES: SOPTypeOption[] = [
  {
    value: 'deployment',
    label: 'Deployment SOP',
    description: 'Application deployment procedures with rollback',
    icon: '🚀',
  },
  {
    value: 'incident',
    label: 'Incident Response SOP',
    description: 'P0-P3 incident handling and escalation',
    icon: '🚨',
  },
  {
    value: 'change',
    label: 'Change Management SOP',
    description: 'Change request and CAB approval workflow',
    icon: '📋',
  },
  {
    value: 'backup',
    label: 'Backup & Recovery SOP',
    description: 'Backup schedules and disaster recovery',
    icon: '💾',
  },
  {
    value: 'security',
    label: 'Security SOP',
    description: 'Access control and vulnerability management',
    icon: '🔒',
  },
]

// ============================================================================
// Components
// ============================================================================

/**
 * Markdown renderer for SOP content
 */
function MarkdownContent({ content }: { content: string }) {
  // Simple markdown rendering with proper styling
  const renderMarkdown = (md: string) => {
    return md
      .split('\n')
      .map((line, index) => {
        // Headers
        if (line.startsWith('# ')) {
          return (
            <h1 key={index} className="text-2xl font-bold mt-6 mb-4">
              {line.slice(2)}
            </h1>
          )
        }
        if (line.startsWith('## ')) {
          return (
            <h2 key={index} className="text-xl font-semibold mt-5 mb-3 border-b pb-2">
              {line.slice(3)}
            </h2>
          )
        }
        if (line.startsWith('### ')) {
          return (
            <h3 key={index} className="text-lg font-medium mt-4 mb-2">
              {line.slice(4)}
            </h3>
          )
        }
        // List items
        if (line.startsWith('- ')) {
          return (
            <li key={index} className="ml-6 list-disc">
              {line.slice(2)}
            </li>
          )
        }
        if (line.match(/^\d+\.\s/)) {
          return (
            <li key={index} className="ml-6 list-decimal">
              {line.replace(/^\d+\.\s/, '')}
            </li>
          )
        }
        // Checkboxes
        if (line.startsWith('- [ ]')) {
          return (
            <div key={index} className="ml-6 flex items-center gap-2">
              <input type="checkbox" className="rounded" disabled />
              <span>{line.slice(6)}</span>
            </div>
          )
        }
        if (line.startsWith('- [x]')) {
          return (
            <div key={index} className="ml-6 flex items-center gap-2">
              <input type="checkbox" className="rounded" checked disabled />
              <span className="line-through text-muted-foreground">{line.slice(6)}</span>
            </div>
          )
        }
        // Bold text
        if (line.includes('**')) {
          const parts = line.split(/\*\*(.*?)\*\*/g)
          return (
            <p key={index} className="my-1">
              {parts.map((part, i) => (i % 2 === 1 ? <strong key={i}>{part}</strong> : part))}
            </p>
          )
        }
        // Table rows
        if (line.startsWith('|')) {
          const cells = line.split('|').filter((c) => c.trim())
          if (line.includes('---')) {
            return null // Skip separator row
          }
          return (
            <tr key={index} className="border-b">
              {cells.map((cell, i) => (
                <td key={i} className="px-3 py-2 text-sm">
                  {cell.trim()}
                </td>
              ))}
            </tr>
          )
        }
        // Empty lines
        if (!line.trim()) {
          return <div key={index} className="h-2" />
        }
        // Regular paragraphs
        return (
          <p key={index} className="my-1">
            {line}
          </p>
        )
      })
  }

  return (
    <div className="prose prose-sm max-w-none dark:prose-invert">
      {renderMarkdown(content)}
    </div>
  )
}

/**
 * MRP Evidence Card (FR6)
 */
function MRPEvidenceCard({ sop }: { sop: GeneratedSOPResponse }) {
  return (
    <Card className="mt-4">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          <span>📊</span>
          MRP Evidence (FR6)
        </CardTitle>
      </CardHeader>
      <CardContent className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <Label className="text-muted-foreground">MRP ID</Label>
          <p className="font-mono text-xs">{sop.mrp_id}</p>
        </div>
        <div>
          <Label className="text-muted-foreground">SOP ID</Label>
          <p className="font-mono text-xs">{sop.sop_id}</p>
        </div>
        <div>
          <Label className="text-muted-foreground">Generation Time</Label>
          <p>{(sop.generation_time_ms / 1000).toFixed(1)}s</p>
        </div>
        <div>
          <Label className="text-muted-foreground">Completeness</Label>
          <p className="flex items-center gap-2">
            <span>{sop.completeness_score.toFixed(0)}%</span>
            <Badge variant={sop.completeness_score >= 80 ? 'default' : 'destructive'}>
              {sop.completeness_score >= 80 ? 'PASS' : 'NEEDS REVIEW'}
            </Badge>
          </p>
        </div>
        <div className="col-span-2">
          <Label className="text-muted-foreground">SHA256 Hash</Label>
          <p className="font-mono text-xs break-all">{sop.sha256_hash}</p>
        </div>
        <div>
          <Label className="text-muted-foreground">AI Model</Label>
          <p>{sop.ai_model}</p>
        </div>
        <div>
          <Label className="text-muted-foreground">Status</Label>
          <Badge variant="outline">{sop.status}</Badge>
        </div>
      </CardContent>
    </Card>
  )
}

// ============================================================================
// Main Page Component
// ============================================================================

/**
 * SOP Generator Page
 *
 * Features:
 * - SOP type selector (5 types)
 * - Workflow description textarea
 * - AI-powered SOP generation
 * - Markdown preview with sections
 * - MRP evidence display
 * - Download functionality
 */
export default function SOPGeneratorPage() {
  // Form state
  const [sopType, setSopType] = useState<SOPType | ''>('')
  const [workflowDescription, setWorkflowDescription] = useState('')
  const [additionalContext, setAdditionalContext] = useState('')

  // Generated SOP state
  const [generatedSOP, setGeneratedSOP] = useState<GeneratedSOPResponse | null>(null)

  // Generate SOP mutation
  const generateMutation = useMutation({
    mutationFn: async (request: GenerateSOPRequest) => {
      const response = await apiClient.post<GeneratedSOPResponse>('/sop/generate', request)
      return response.data
    },
    onSuccess: (data) => {
      setGeneratedSOP(data)
    },
  })

  // Form validation
  const isFormValid = sopType !== '' && workflowDescription.length >= 50

  // Handle form submission
  const handleGenerate = () => {
    if (!isFormValid || !sopType) return

    generateMutation.mutate({
      sop_type: sopType,
      workflow_description: workflowDescription,
      additional_context: additionalContext || undefined,
    })
  }

  // Handle download
  const handleDownload = () => {
    if (!generatedSOP) return

    const blob = new Blob([generatedSOP.markdown_content], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${generatedSOP.sop_id}.md`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  // Reset form
  const handleReset = () => {
    setSopType('')
    setWorkflowDescription('')
    setAdditionalContext('')
    setGeneratedSOP(null)
    generateMutation.reset()
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">SOP Generator</h1>
            <p className="text-muted-foreground">
              AI-assisted Standard Operating Procedure creation (Phase 2-Pilot)
            </p>
          </div>
          <Badge variant="outline" className="gap-1">
            <span>🤖</span>
            SASE Level 1
          </Badge>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Panel: Input Form */}
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <span>📝</span>
                  Generate SOP
                </CardTitle>
                <CardDescription>
                  Describe your workflow and let AI generate a complete SOP with 5 mandatory sections
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* SOP Type Selector (FR3) */}
                <div className="space-y-2">
                  <Label htmlFor="sop-type">SOP Type *</Label>
                  <Select
                    value={sopType}
                    onValueChange={(value) => setSopType(value as SOPType)}
                    disabled={generateMutation.isPending}
                  >
                    <SelectTrigger id="sop-type">
                      <SelectValue placeholder="Select SOP type..." />
                    </SelectTrigger>
                    <SelectContent>
                      {SOP_TYPES.map((type) => (
                        <SelectItem key={type.value} value={type.value}>
                          <div className="flex items-center gap-2">
                            <span>{type.icon}</span>
                            <div>
                              <div className="font-medium">{type.label}</div>
                              <div className="text-xs text-muted-foreground">
                                {type.description}
                              </div>
                            </div>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Workflow Description (FR1) */}
                <div className="space-y-2">
                  <Label htmlFor="workflow">Workflow Description *</Label>
                  <Textarea
                    id="workflow"
                    placeholder="Describe the workflow or process you want to create an SOP for. Include key steps, systems involved, and any specific requirements. (Minimum 50 characters)"
                    value={workflowDescription}
                    onChange={(e) => setWorkflowDescription(e.target.value)}
                    disabled={generateMutation.isPending}
                    className="min-h-[150px]"
                  />
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>{workflowDescription.length < 50 ? `${50 - workflowDescription.length} more characters needed` : 'Ready'}</span>
                    <span>{workflowDescription.length} / 5000</span>
                  </div>
                </div>

                {/* Additional Context (Optional) */}
                <div className="space-y-2">
                  <Label htmlFor="context">Additional Context (Optional)</Label>
                  <Textarea
                    id="context"
                    placeholder="Any additional context, constraints, or requirements..."
                    value={additionalContext}
                    onChange={(e) => setAdditionalContext(e.target.value)}
                    disabled={generateMutation.isPending}
                    className="min-h-[80px]"
                  />
                </div>

                {/* Action Buttons */}
                <div className="flex gap-2">
                  <Button
                    onClick={handleGenerate}
                    disabled={!isFormValid || generateMutation.isPending}
                    className="flex-1"
                  >
                    {generateMutation.isPending ? (
                      <>
                        <span className="animate-spin mr-2">⚙️</span>
                        Generating SOP...
                      </>
                    ) : (
                      <>
                        <span className="mr-2">🤖</span>
                        Generate SOP
                      </>
                    )}
                  </Button>
                  {generatedSOP && (
                    <Button variant="outline" onClick={handleReset}>
                      Reset
                    </Button>
                  )}
                </div>

                {/* Error Display */}
                {generateMutation.isError && (
                  <div className="p-3 bg-destructive/10 text-destructive rounded-md text-sm">
                    <strong>Error:</strong> {generateMutation.error?.message || 'Failed to generate SOP'}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* MRP Evidence Card (FR6) */}
            {generatedSOP && <MRPEvidenceCard sop={generatedSOP} />}
          </div>

          {/* Right Panel: Generated SOP Preview */}
          <div className="space-y-4">
            <Card className="h-full flex flex-col">
              <CardHeader className="flex-shrink-0">
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <span>📄</span>
                    Generated SOP
                  </CardTitle>
                  {generatedSOP && (
                    <Button variant="outline" size="sm" onClick={handleDownload}>
                      <span className="mr-2">⬇️</span>
                      Download .md
                    </Button>
                  )}
                </div>
                <CardDescription>
                  {generatedSOP
                    ? `${generatedSOP.title} (v${generatedSOP.version})`
                    : 'SOP preview will appear here after generation'}
                </CardDescription>
              </CardHeader>
              <CardContent className="flex-1 min-h-0">
                {generatedSOP ? (
                  <ScrollArea className="h-[600px] pr-4">
                    <MarkdownContent content={generatedSOP.markdown_content} />
                  </ScrollArea>
                ) : (
                  <div className="h-[600px] flex items-center justify-center text-muted-foreground">
                    <div className="text-center">
                      <div className="text-4xl mb-4">📋</div>
                      <p>Select an SOP type and describe your workflow</p>
                      <p className="text-sm">to generate a complete SOP with AI</p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>

        {/* FR2: 5 Mandatory Sections Info */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">FR2: 5 Mandatory Sections (ISO 9001 Compliant)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-5 gap-4 text-center text-sm">
              <div className="p-2 bg-muted rounded">
                <div className="font-medium">1. Purpose</div>
                <div className="text-xs text-muted-foreground">Why this SOP exists</div>
              </div>
              <div className="p-2 bg-muted rounded">
                <div className="font-medium">2. Scope</div>
                <div className="text-xs text-muted-foreground">What's covered</div>
              </div>
              <div className="p-2 bg-muted rounded">
                <div className="font-medium">3. Procedure</div>
                <div className="text-xs text-muted-foreground">Step-by-step</div>
              </div>
              <div className="p-2 bg-muted rounded">
                <div className="font-medium">4. Roles</div>
                <div className="text-xs text-muted-foreground">RACI matrix</div>
              </div>
              <div className="p-2 bg-muted rounded">
                <div className="font-medium">5. Quality</div>
                <div className="text-xs text-muted-foreground">Criteria checklist</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}
