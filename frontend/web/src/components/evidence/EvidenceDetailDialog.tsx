/**
 * File: frontend/web/src/components/evidence/EvidenceDetailDialog.tsx
 * Version: 1.0.0
 * Status: ACTIVE - STAGE 03 (BUILD)
 * Date: November 28, 2025
 * Authority: Frontend Lead + CPO Approved
 * Foundation: Sprint 18 - Evidence Integration
 * Framework: SDLC 4.9 Complete Lifecycle
 *
 * Description:
 * Dialog for viewing evidence file details including:
 * - File information (name, size, type)
 * - Integrity verification status
 * - SHA256 hash with copy functionality
 * - Upload information
 * - Download and verify actions
 *
 * SDLC 4.9 Compliance:
 * - Pillar 1: Zero Mock Policy (Real API calls)
 * - Pillar 3: Quality Governance (Type hints)
 */

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import apiClient from '@/api/client'
import type { EvidenceResponse, IntegrityCheckResponse } from '@/types/api'

interface EvidenceDetailDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  evidence: EvidenceResponse
}

/**
 * Evidence Detail Dialog Component
 *
 * Features:
 * - Display all evidence metadata
 * - Copy SHA256 hash to clipboard
 * - Download evidence file
 * - Verify integrity on demand
 * - Link to associated gate
 */
export default function EvidenceDetailDialog({
  open,
  onOpenChange,
  evidence,
}: EvidenceDetailDialogProps) {
  const [copySuccess, setCopySuccess] = useState(false)
  const queryClient = useQueryClient()

  // Integrity check mutation
  const integrityCheckMutation = useMutation<IntegrityCheckResponse, Error>({
    mutationFn: async () => {
      const response = await apiClient.post<IntegrityCheckResponse>(
        `/evidence/${evidence.id}/integrity-check`,
        { force: true }
      )
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evidence'] })
    },
  })

  // Handle download
  const handleDownload = async () => {
    try {
      const downloadUrl = evidence.download_url || evidence.s3_url
      if (downloadUrl) {
        if (downloadUrl.startsWith('http')) {
          window.open(downloadUrl, '_blank')
        } else {
          // Remove /api/v1 prefix if present since apiClient already has baseURL
          const cleanUrl = downloadUrl.replace(/^\/api\/v1/, '')
          const response = await apiClient.get(cleanUrl)
          const { presigned_url } = response.data
          if (presigned_url) {
            window.open(presigned_url, '_blank')
          }
        }
      }
    } catch (error) {
      console.error('Download failed:', error)
    }
  }

  // Copy SHA256 hash to clipboard
  const handleCopyHash = async () => {
    try {
      await navigator.clipboard.writeText(evidence.sha256_hash)
      setCopySuccess(true)
      setTimeout(() => setCopySuccess(false), 2000)
    } catch (error) {
      console.error('Failed to copy:', error)
    }
  }

  // Get integrity badge
  const getIntegrityBadge = (status: string) => {
    switch (status) {
      case 'valid':
        return (
          <Badge className="bg-green-100 text-green-800 hover:bg-green-100">
            <svg className="mr-1 h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            Valid
          </Badge>
        )
      case 'failed':
        return (
          <Badge className="bg-red-100 text-red-800 hover:bg-red-100">
            <svg className="mr-1 h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
            Failed
          </Badge>
        )
      case 'pending':
        return (
          <Badge className="bg-yellow-100 text-yellow-800 hover:bg-yellow-100">
            <svg className="mr-1 h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Pending
          </Badge>
        )
      default:
        return (
          <Badge variant="outline">
            <svg className="mr-1 h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Unknown
          </Badge>
        )
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

  // Format file size
  const formatFileSize = (mb: number) => {
    if (mb < 1) {
      return `${(mb * 1024).toFixed(0)} KB`
    }
    return `${mb.toFixed(2)} MB`
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <svg className="h-5 w-5 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            {evidence.file_name}
          </DialogTitle>
          <DialogDescription>
            Evidence file details and integrity information
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* File Information Section */}
          <div className="space-y-3">
            <h4 className="font-medium text-sm text-muted-foreground uppercase tracking-wide">
              File Information
            </h4>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">File Name</p>
                <p className="font-medium break-all">{evidence.file_name}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">File Size</p>
                <p className="font-medium">{formatFileSize(evidence.file_size_mb)}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">File Type</p>
                <p className="font-medium">{evidence.file_type || 'Unknown'}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Evidence Type</p>
                <Badge variant="outline">{getEvidenceTypeLabel(evidence.evidence_type)}</Badge>
              </div>
            </div>
            {evidence.description && (
              <div>
                <p className="text-sm text-muted-foreground">Description</p>
                <p className="text-sm mt-1">{evidence.description}</p>
              </div>
            )}
          </div>

          {/* Integrity Section */}
          <div className="space-y-3">
            <h4 className="font-medium text-sm text-muted-foreground uppercase tracking-wide">
              Integrity Verification
            </h4>
            <div className="flex items-center justify-between p-4 rounded-lg bg-muted/50">
              <div className="flex items-center gap-3">
                <div className="flex-shrink-0">
                  {getIntegrityBadge(evidence.integrity_status)}
                </div>
                <div>
                  <p className="text-sm font-medium">
                    {evidence.integrity_status === 'valid'
                      ? 'File integrity verified'
                      : evidence.integrity_status === 'failed'
                      ? 'Integrity check failed'
                      : 'Integrity not verified'}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    SHA256 hash verification
                  </p>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => integrityCheckMutation.mutate()}
                disabled={integrityCheckMutation.isPending}
              >
                {integrityCheckMutation.isPending ? 'Verifying...' : 'Verify Now'}
              </Button>
            </div>

            {/* SHA256 Hash */}
            <div>
              <p className="text-sm text-muted-foreground mb-1">SHA256 Hash</p>
              <div className="flex items-center gap-2">
                <code className="flex-1 text-xs font-mono bg-muted p-2 rounded break-all">
                  {evidence.sha256_hash}
                </code>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleCopyHash}
                  className="flex-shrink-0"
                >
                  {copySuccess ? (
                    <svg className="h-4 w-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                    </svg>
                  )}
                </Button>
              </div>
            </div>
          </div>

          {/* Upload Information Section */}
          <div className="space-y-3">
            <h4 className="font-medium text-sm text-muted-foreground uppercase tracking-wide">
              Upload Information
            </h4>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Uploaded By</p>
                <p className="font-medium">{evidence.uploaded_by_name}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Uploaded At</p>
                <p className="font-medium">
                  {new Date(evidence.uploaded_at).toLocaleString()}
                </p>
              </div>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Associated Gate</p>
              <Link
                to={`/gates/${evidence.gate_id}`}
                className="text-primary hover:underline text-sm font-medium"
              >
                View Gate Details
              </Link>
            </div>
          </div>

          {/* Integrity Check Result */}
          {integrityCheckMutation.isSuccess && (
            <div className={`p-4 rounded-lg ${
              integrityCheckMutation.data.is_valid
                ? 'bg-green-50 border border-green-200'
                : 'bg-red-50 border border-red-200'
            }`}>
              <p className={`font-medium ${
                integrityCheckMutation.data.is_valid ? 'text-green-800' : 'text-red-800'
              }`}>
                {integrityCheckMutation.data.is_valid
                  ? 'Integrity Check Passed'
                  : 'Integrity Check Failed'}
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                Verified at: {new Date(integrityCheckMutation.data.checked_at).toLocaleString()}
              </p>
              {integrityCheckMutation.data.error_message && (
                <p className="text-sm text-red-600 mt-1">
                  Error: {integrityCheckMutation.data.error_message}
                </p>
              )}
            </div>
          )}

          {integrityCheckMutation.isError && (
            <div className="p-4 rounded-lg bg-red-50 border border-red-200">
              <p className="font-medium text-red-800">Integrity Check Error</p>
              <p className="text-sm text-red-600 mt-1">
                {integrityCheckMutation.error.message || 'Failed to verify integrity'}
              </p>
            </div>
          )}
        </div>

        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
          <Button onClick={handleDownload}>
            <svg className="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Download
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
