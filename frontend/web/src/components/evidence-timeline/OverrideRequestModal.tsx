/**
 * Override Request Modal Component
 *
 * SDLC Stage: 04 - BUILD
 * Sprint: 43 - Policy Guards & Evidence UI
 * Framework: SDLC 5.1.1
 * Epic: EP-02 AI Safety Layer v1
 *
 * Purpose:
 * Modal dialog for requesting an override on a failed validation.
 * Collects override type and justification reason.
 */

import { useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  OverrideType,
  OverrideTypeLabels,
  type OverrideRequest,
} from '@/types/evidence-timeline'

interface OverrideRequestModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  eventId: string
  prNumber: string
  onSubmit: (eventId: string, request: OverrideRequest) => void
  isSubmitting: boolean
  error?: string
}

const MIN_REASON_LENGTH = 50
const MAX_REASON_LENGTH = 2000

const overrideTypeDescriptions: Record<OverrideType, string> = {
  [OverrideType.FALSE_POSITIVE]: 'The validation flagged something that is not actually a problem (e.g., test file, false pattern match).',
  [OverrideType.APPROVED_RISK]: 'The risk has been reviewed and accepted by the team/security lead.',
  [OverrideType.EMERGENCY]: 'Critical hotfix required - bypasses normal review process.',
}

export default function OverrideRequestModal({
  open,
  onOpenChange,
  eventId,
  prNumber,
  onSubmit,
  isSubmitting,
  error,
}: OverrideRequestModalProps) {
  const [overrideType, setOverrideType] = useState<OverrideType | ''>('')
  const [reason, setReason] = useState('')

  const isReasonValid = reason.length >= MIN_REASON_LENGTH && reason.length <= MAX_REASON_LENGTH
  const canSubmit = overrideType && isReasonValid && !isSubmitting

  const handleSubmit = () => {
    if (!canSubmit || !overrideType) return

    onSubmit(eventId, {
      override_type: overrideType,
      reason: reason.trim(),
    })
  }

  const handleClose = () => {
    if (!isSubmitting) {
      setOverrideType('')
      setReason('')
      onOpenChange(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <svg className="h-5 w-5 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            Request Override
          </DialogTitle>
          <DialogDescription>
            Request an override for PR #{prNumber} validation failure.
            This will require approval from an admin or manager.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Override Type Selection */}
          <div className="space-y-2">
            <Label htmlFor="override-type">Override Type</Label>
            <Select
              value={overrideType}
              onValueChange={(value) => setOverrideType(value as OverrideType)}
            >
              <SelectTrigger id="override-type">
                <SelectValue placeholder="Select override type..." />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(OverrideTypeLabels).map(([value, label]) => (
                  <SelectItem key={value} value={value}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {overrideType && (
              <p className="text-sm text-muted-foreground">
                {overrideTypeDescriptions[overrideType]}
              </p>
            )}
          </div>

          {/* Reason Textarea */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="reason">Justification</Label>
              <span className={`text-xs ${
                reason.length < MIN_REASON_LENGTH
                  ? 'text-red-500'
                  : reason.length > MAX_REASON_LENGTH
                  ? 'text-red-500'
                  : 'text-muted-foreground'
              }`}>
                {reason.length}/{MIN_REASON_LENGTH} min
              </span>
            </div>
            <Textarea
              id="reason"
              placeholder="Provide a detailed justification for why this override should be approved. Include context about why the validation failure is not applicable or why the risk is acceptable..."
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="min-h-[150px]"
              maxLength={MAX_REASON_LENGTH}
            />
            <p className="text-xs text-muted-foreground">
              Minimum {MIN_REASON_LENGTH} characters required. Be specific and include relevant context.
            </p>
          </div>

          {/* Warning for Emergency */}
          {overrideType === OverrideType.EMERGENCY && (
            <Alert variant="destructive">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <AlertDescription>
                Emergency overrides are logged and will be reviewed post-merge.
                Use only for critical production issues.
              </AlertDescription>
            </Alert>
          )}

          {/* Error Display */}
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={!canSubmit}>
            {isSubmitting ? (
              <>
                <svg className="mr-2 h-4 w-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Submitting...
              </>
            ) : (
              'Submit Request'
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
