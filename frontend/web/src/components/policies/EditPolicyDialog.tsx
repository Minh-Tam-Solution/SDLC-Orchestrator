/**
 * File: frontend/web/src/components/policies/EditPolicyDialog.tsx
 * Version: 1.0.0
 * Status: ACTIVE - STAGE 03 (BUILD)
 * Date: December 15, 2025
 * Authority: Frontend Lead + CTO Approved
 * Framework: SDLC 4.9 Complete Lifecycle
 *
 * Description:
 * Dialog for editing existing policies.
 * Uses PUT /policies/{id} API endpoint.
 *
 * SDLC 4.9 Compliance:
 * - Pillar 1: Zero Mock Policy (Real API calls)
 * - Pillar 3: Quality Governance (Type hints, validation)
 */

import { useState, useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import apiClient from '@/api/client'
import type { PolicyResponse } from '@/types/api'

interface PolicyUpdateRequest {
  policy_name?: string | undefined
  description?: string | undefined
  rego_code?: string | undefined
  severity?: string | undefined
  is_active?: boolean | undefined
  version?: string | undefined
}

interface EditPolicyDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  policy: PolicyResponse
  onSuccess?: (policy: PolicyResponse) => void
}

// Severity levels
const SEVERITY_LEVELS = [
  { value: 'INFO', label: 'Info', color: 'text-blue-600' },
  { value: 'WARNING', label: 'Warning', color: 'text-yellow-600' },
  { value: 'ERROR', label: 'Error', color: 'text-orange-600' },
  { value: 'CRITICAL', label: 'Critical', color: 'text-red-600' },
]

/**
 * Edit Policy Dialog Component
 *
 * Features:
 * - Pre-populated form with current policy data
 * - Validation for required fields
 * - Error handling with user feedback
 * - Query invalidation on success
 */
export default function EditPolicyDialog({
  open,
  onOpenChange,
  policy,
  onSuccess,
}: EditPolicyDialogProps) {
  const [policyName, setPolicyName] = useState(policy.policy_name)
  const [description, setDescription] = useState(policy.description || '')
  const [regoCode, setRegoCode] = useState(policy.rego_code || '')
  const [severity, setSeverity] = useState<string>(policy.severity)
  const [isActive, setIsActive] = useState(policy.is_active)
  const [version, setVersion] = useState(policy.version)
  const [error, setError] = useState<string | null>(null)
  const queryClient = useQueryClient()

  // Update form when policy changes
  useEffect(() => {
    setPolicyName(policy.policy_name)
    setDescription(policy.description || '')
    setRegoCode(policy.rego_code || '')
    setSeverity(policy.severity)
    setIsActive(policy.is_active)
    setVersion(policy.version)
    setError(null)
  }, [policy])

  // Update policy mutation
  const updateMutation = useMutation<PolicyResponse, Error, PolicyUpdateRequest>({
    mutationFn: async (data) => {
      const response = await apiClient.put<PolicyResponse>(`/policies/${policy.id}`, data)
      return response.data
    },
    onSuccess: (updatedPolicy) => {
      // Invalidate policies list and policy detail
      queryClient.invalidateQueries({ queryKey: ['policies'] })
      queryClient.invalidateQueries({ queryKey: ['policy', policy.id] })
      // Reset error
      setError(null)
      // Close dialog
      onOpenChange(false)
      // Call onSuccess callback if provided
      onSuccess?.(updatedPolicy)
    },
    onError: (err: Error & { response?: { data?: { detail?: string } } }) => {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to update policy'
      setError(errorMessage)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    const trimmedName = policyName.trim()

    if (!trimmedName) {
      setError('Policy name is required')
      return
    }

    if (trimmedName.length < 3) {
      setError('Policy name must be at least 3 characters')
      return
    }

    // Validate version format (x.y.z)
    const versionRegex = /^\d+\.\d+\.\d+$/
    if (!versionRegex.test(version)) {
      setError('Version must be in format x.y.z (e.g., 1.0.0)')
      return
    }

    const updateData: PolicyUpdateRequest = {
      policy_name: trimmedName,
      description: description.trim() || undefined,
      rego_code: regoCode.trim() || undefined,
      severity,
      is_active: isActive,
      version,
    }

    updateMutation.mutate(updateData)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Edit Policy</DialogTitle>
          <DialogDescription>
            Update policy settings. Policy code and stage cannot be changed.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            {/* Policy Code (read-only) */}
            <div className="grid grid-cols-4 items-center gap-4">
              <Label className="text-right text-muted-foreground">
                Policy Code
              </Label>
              <div className="col-span-3">
                <code className="px-2 py-1 bg-muted rounded text-sm">
                  {policy.policy_code}
                </code>
              </div>
            </div>

            {/* Stage (read-only) */}
            <div className="grid grid-cols-4 items-center gap-4">
              <Label className="text-right text-muted-foreground">
                Stage
              </Label>
              <div className="col-span-3">
                <code className="px-2 py-1 bg-muted rounded text-sm">
                  {policy.stage}
                </code>
              </div>
            </div>

            {/* Policy Name */}
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="policy-name" className="text-right">
                Name *
              </Label>
              <Input
                id="policy-name"
                value={policyName}
                onChange={(e) => setPolicyName(e.target.value)}
                className="col-span-3"
                placeholder="e.g., FRD Completeness Check"
              />
            </div>

            {/* Description */}
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="description" className="text-right">
                Description
              </Label>
              <Textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="col-span-3"
                placeholder="Describe what this policy checks..."
                rows={2}
              />
            </div>

            {/* Severity */}
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="severity" className="text-right">
                Severity *
              </Label>
              <Select value={severity} onValueChange={setSeverity}>
                <SelectTrigger className="col-span-3">
                  <SelectValue placeholder="Select severity" />
                </SelectTrigger>
                <SelectContent>
                  {SEVERITY_LEVELS.map((level) => (
                    <SelectItem key={level.value} value={level.value}>
                      <span className={level.color}>{level.label}</span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Version */}
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="version" className="text-right">
                Version *
              </Label>
              <Input
                id="version"
                value={version}
                onChange={(e) => setVersion(e.target.value)}
                className="col-span-3"
                placeholder="e.g., 1.0.0"
              />
            </div>

            {/* Is Active */}
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="is-active" className="text-right">
                Active
              </Label>
              <div className="col-span-3 flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setIsActive(!isActive)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    isActive ? 'bg-primary' : 'bg-muted'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      isActive ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
                <span className="text-sm text-muted-foreground">
                  {isActive ? 'Policy is active and enforced' : 'Policy is disabled'}
                </span>
              </div>
            </div>

            {/* Rego Code */}
            <div className="grid grid-cols-4 items-start gap-4">
              <Label htmlFor="rego-code" className="text-right pt-2">
                Rego Code
              </Label>
              <Textarea
                id="rego-code"
                value={regoCode}
                onChange={(e) => setRegoCode(e.target.value)}
                className="col-span-3 font-mono text-sm"
                placeholder="package sdlc.policy..."
                rows={8}
              />
            </div>

            {/* Error message */}
            {error && (
              <div className="col-span-4 rounded-md bg-destructive/15 p-3 text-sm text-destructive">
                {error}
              </div>
            )}
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={updateMutation.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={updateMutation.isPending}>
              {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
