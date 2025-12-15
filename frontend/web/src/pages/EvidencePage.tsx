/**
 * File: frontend/web/src/pages/EvidencePage.tsx
 * Version: 2.0.0
 * Status: ACTIVE - Gap Analysis P0 Fix
 * Date: December 2, 2025
 * Authority: Frontend Lead + CPO Approved
 * Foundation: Gap Analysis Report, Zero Mock Policy
 *
 * Description:
 * Evidence Vault page with full API integration.
 * Lists evidence files, supports download, integrity checks, and filtering.
 */

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import DashboardLayout from '@/components/layout/DashboardLayout'
import EvidenceDetailDialog from '@/components/evidence/EvidenceDetailDialog'
import apiClient from '@/api/client'
import {
  EvidenceResponse,
  EvidenceListResponse,
  IntegrityCheckResponse,
} from '@/types/api'

/**
 * Evidence page component with full API integration
 *
 * Features:
 * - List evidence with pagination
 * - Filter by gate_id or evidence_type
 * - Download evidence files
 * - Integrity check functionality
 * - Upload evidence dialog
 */
export default function EvidencePage() {
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false)
  const [detailDialogOpen, setDetailDialogOpen] = useState(false)
  const [selectedEvidence, setSelectedEvidence] = useState<EvidenceResponse | null>(null)
  const [selectedGateId, setSelectedGateId] = useState<string>('')
  const [selectedEvidenceType, setSelectedEvidenceType] = useState<string>('')
  const [searchTerm, setSearchTerm] = useState('')
  const [page, setPage] = useState(1)
  const pageSize = 20

  const queryClient = useQueryClient()

  // Handle view evidence details
  const handleViewDetails = (evidence: EvidenceResponse) => {
    setSelectedEvidence(evidence)
    setDetailDialogOpen(true)
  }

  // Fetch evidence list
  const { data: evidenceData, isLoading } = useQuery<EvidenceListResponse>({
    queryKey: ['evidence', selectedGateId, selectedEvidenceType, page],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
      })
      if (selectedGateId) params.append('gate_id', selectedGateId)
      if (selectedEvidenceType) params.append('evidence_type', selectedEvidenceType)

      const response = await apiClient.get<EvidenceListResponse>(`/evidence?${params}`)
      return response.data
    },
  })

  // Integrity check mutation
  const integrityCheckMutation = useMutation<IntegrityCheckResponse, Error, string>({
    mutationFn: async (evidenceId: string) => {
      const response = await apiClient.post<IntegrityCheckResponse>(
        `/evidence/${evidenceId}/integrity-check`,
        { force: false }
      )
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evidence'] })
    },
  })

  // Download evidence
  const handleDownload = async (evidence: EvidenceResponse) => {
    try {
      // Use download_url if available, otherwise use s3_url
      const downloadUrl = evidence.download_url || evidence.s3_url
      if (downloadUrl) {
        // If it's a full URL (s3_url), open it directly
        if (downloadUrl.startsWith('http')) {
          window.open(downloadUrl, '_blank')
        } else {
          // If it's a relative path (download_url), get presigned URL from API
          // Remove /api/v1 prefix if present since apiClient already has baseURL
          const cleanUrl = downloadUrl.replace(/^\/api\/v1/, '')
          const response = await apiClient.get(cleanUrl)
          const { presigned_url } = response.data
          if (presigned_url) {
            // Open presigned URL in new tab for download
            window.open(presigned_url, '_blank')
          } else {
            alert('Download URL not available')
          }
        }
      } else {
        alert('Download URL not available')
      }
    } catch (error) {
      console.error('Download failed:', error)
      alert('Failed to download evidence file')
    }
  }

  // Integrity check handler
  const handleIntegrityCheck = (evidenceId: string) => {
    integrityCheckMutation.mutate(evidenceId)
  }

  // Filter evidence by search term
  const filteredEvidence = evidenceData?.items.filter(
    (evidence) =>
      !searchTerm ||
      evidence.file_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      evidence.description?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  // Get integrity status badge
  const getIntegrityBadge = (status: string) => {
    switch (status) {
      case 'valid':
        return <Badge variant="success">Valid</Badge>
      case 'failed':
        return <Badge variant="error">Failed</Badge>
      case 'pending':
        return <Badge variant="warning">Pending</Badge>
      default:
        return <Badge variant="outline">Unknown</Badge>
    }
  }

  // Get evidence type label
  const getEvidenceTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      DESIGN_DOCUMENT: 'Design Document',
      TEST_RESULTS: 'Test Results',
      CODE_REVIEW: 'Code Review',
      DEPLOYMENT_PROOF: 'Deployment Proof',
      DOCUMENTATION: 'Documentation',
      COMPLIANCE: 'Compliance',
    }
    return labels[type] || type
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Page header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Evidence Vault</h1>
            <p className="text-muted-foreground">
              Store and manage evidence documents for gate approvals
            </p>
          </div>
          <Button onClick={() => setUploadDialogOpen(true)}>
            <svg className="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
            Upload Evidence
          </Button>
        </div>

        {/* Filters */}
        <Card>
          <CardHeader>
            <CardTitle>Filters</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Input
                placeholder="Search evidence..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
              <Select 
                value={selectedEvidenceType || "all"} 
                onValueChange={(value) => setSelectedEvidenceType(value === "all" ? "" : value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Evidence Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="DESIGN_DOCUMENT">Design Document</SelectItem>
                  <SelectItem value="TEST_RESULTS">Test Results</SelectItem>
                  <SelectItem value="CODE_REVIEW">Code Review</SelectItem>
                  <SelectItem value="DEPLOYMENT_PROOF">Deployment Proof</SelectItem>
                  <SelectItem value="DOCUMENTATION">Documentation</SelectItem>
                  <SelectItem value="COMPLIANCE">Compliance</SelectItem>
                </SelectContent>
              </Select>
              <Input
                placeholder="Gate ID (optional)"
                value={selectedGateId}
                onChange={(e) => setSelectedGateId(e.target.value)}
              />
              <Button
                variant="outline"
                onClick={() => {
                  setSelectedGateId('')
                  setSelectedEvidenceType('')
                  setSearchTerm('')
                  setPage(1)
                }}
              >
                Clear Filters
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Evidence list */}
        <Card>
          <CardHeader>
            <CardTitle>Evidence Documents</CardTitle>
            <CardDescription>
              {evidenceData ? `${evidenceData.total} total evidence files` : 'Loading...'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="text-center py-8 text-muted-foreground">Loading evidence...</div>
            ) : !filteredEvidence || filteredEvidence.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12">
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
                    d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4"
                  />
                </svg>
                <h3 className="text-lg font-medium">No evidence uploaded</h3>
                <p className="text-muted-foreground text-center mt-1">
                  Upload documents, screenshots, or files as evidence for gate approvals
                </p>
                <Button className="mt-4" onClick={() => setUploadDialogOpen(true)}>
                  <svg className="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                  </svg>
                  Upload First Evidence
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-2 font-medium">File Name</th>
                        <th className="text-left p-2 font-medium">Type</th>
                        <th className="text-left p-2 font-medium">Gate</th>
                        <th className="text-left p-2 font-medium">Size</th>
                        <th className="text-left p-2 font-medium">Uploaded</th>
                        <th className="text-left p-2 font-medium">Integrity</th>
                        <th className="text-left p-2 font-medium">SHA256</th>
                        <th className="text-left p-2 font-medium">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredEvidence.map((evidence) => (
                        <tr key={evidence.id} className="border-b hover:bg-muted/50">
                          <td className="p-2">
                            <div className="font-medium">{evidence.file_name}</div>
                            {evidence.description && (
                              <div className="text-sm text-muted-foreground line-clamp-1">
                                {evidence.description}
                              </div>
                            )}
                          </td>
                          <td className="p-2">
                            <Badge variant="outline">{getEvidenceTypeLabel(evidence.evidence_type)}</Badge>
                          </td>
                          <td className="p-2">
                            <Link
                              to={`/gates/${evidence.gate_id}`}
                              className="text-primary hover:underline"
                            >
                              View Gate
                            </Link>
                          </td>
                          <td className="p-2 text-sm text-muted-foreground">
                            {evidence.file_size_mb.toFixed(2)} MB
                          </td>
                          <td className="p-2 text-sm text-muted-foreground">
                            {new Date(evidence.uploaded_at).toLocaleDateString()}
                            <div className="text-xs">by {evidence.uploaded_by_name}</div>
                          </td>
                          <td className="p-2">{getIntegrityBadge(evidence.integrity_status)}</td>
                          <td className="p-2">
                            <code className="text-xs font-mono text-muted-foreground">
                              {evidence.sha256_hash.substring(0, 8)}...
                            </code>
                          </td>
                          <td className="p-2">
                            <div className="flex gap-2">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleViewDetails(evidence)}
                              >
                                View
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleDownload(evidence)}
                              >
                                Download
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleIntegrityCheck(evidence.id)}
                                disabled={integrityCheckMutation.isPending}
                              >
                                {integrityCheckMutation.isPending ? 'Checking...' : 'Verify'}
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Pagination */}
                {evidenceData && evidenceData.pages > 1 && (
                  <div className="flex items-center justify-between pt-4">
                    <div className="text-sm text-muted-foreground">
                      Page {evidenceData.page} of {evidenceData.pages} ({evidenceData.total} total)
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage((p) => Math.max(1, p - 1))}
                        disabled={page === 1}
                      >
                        Previous
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage((p) => Math.min(evidenceData.pages, p + 1))}
                        disabled={page === evidenceData.pages}
                      >
                        Next
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Upload Evidence Dialog - Note: Requires gate selection */}
        {uploadDialogOpen && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <Card className="w-full max-w-md">
              <CardHeader>
                <CardTitle>Upload Evidence</CardTitle>
                <CardDescription>
                  Please select a gate first to upload evidence
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-4">
                  To upload evidence, navigate to a gate detail page and use the "Upload Evidence" button there.
                </p>
                <Button
                  variant="outline"
                  onClick={() => setUploadDialogOpen(false)}
                  className="w-full"
                >
                  Close
                </Button>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Evidence Detail Dialog */}
        {selectedEvidence && (
          <EvidenceDetailDialog
            open={detailDialogOpen}
            onOpenChange={setDetailDialogOpen}
            evidence={selectedEvidence}
          />
        )}
      </div>
    </DashboardLayout>
  )
}
