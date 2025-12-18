/**
 * File: frontend/web/src/components/admin/BulkDeleteUsersDialog.tsx
 * Version: 1.0.0
 * Status: ACTIVE - Sprint 40 Part 3 (Bulk Delete)
 * Date: 2025-12-18
 * Authority: CTO Approved (Dec 18, 2025)
 * Framework: SDLC 5.1.1 Complete Lifecycle
 *
 * Description:
 * Confirmation dialog for bulk deleting multiple users.
 * Requires typing "DELETE" to confirm (safety measure).
 *
 * Security:
 * - Cannot delete self (blocked in selection)
 * - Cannot delete last superuser (backend protection)
 * - Maximum 50 users per request (CTO condition)
 * - Soft delete preserves audit trail
 * - Toast feedback on success/error/partial success
 *
 * CTO Conditions Applied:
 * 1. Batch Size Limit: Maximum 50 users
 * 2. Partial Success Handling: Shows detailed report
 * 3. Rate Limiting: 5 requests/minute (backend)
 */

import { useState, useEffect } from 'react'
import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useToast } from '@/hooks/useToast'
import { useBulkDeleteUsers, AdminUserListItem } from '@/api/admin'
import { AlertTriangle, Trash2 } from 'lucide-react'

interface BulkDeleteUsersDialogProps {
  users: AdminUserListItem[]
  open: boolean
  onOpenChange: (open: boolean) => void
  onSuccess?: () => void
}

export function BulkDeleteUsersDialog({
  users,
  open,
  onOpenChange,
  onSuccess,
}: BulkDeleteUsersDialogProps) {
  const { toast } = useToast()
  const bulkDeleteMutation = useBulkDeleteUsers()
  const [confirmText, setConfirmText] = useState('')

  // Reset confirm text when dialog opens/closes
  useEffect(() => {
    if (!open) {
      setConfirmText('')
    }
  }, [open])

  const isConfirmValid = confirmText === 'DELETE'
  const userCount = users.length

  const handleDelete = async () => {
    if (!isConfirmValid || userCount === 0) return

    // Prevent double-click/double-submit
    if (bulkDeleteMutation.isPending) return

    try {
      const result = await bulkDeleteMutation.mutateAsync({
        user_ids: users.map((u) => u.id),
      })

      // Handle different outcomes
      if (result.failed_count === 0) {
        // All successful
        toast({
          title: 'Users Deleted',
          description: `${result.success_count} user${result.success_count !== 1 ? 's' : ''} deleted successfully`,
          variant: 'success',
        })
      } else if (result.success_count === 0) {
        // All failed
        const reasons = result.failed_users.map((f) => f.reason).join(', ')
        toast({
          title: 'Delete Failed',
          description: `No users were deleted. Reasons: ${reasons}`,
          variant: 'error',
        })
      } else {
        // Partial success
        const failedReasons = result.failed_users.map((f) => f.reason).join(', ')
        toast({
          title: 'Partial Success',
          description: `${result.success_count} deleted, ${result.failed_count} failed. Failed: ${failedReasons}`,
          variant: 'warning',
        })
      }

      onOpenChange(false)
      onSuccess?.()
    } catch (error: any) {
      console.error('Failed to bulk delete users:', error)

      // Check for specific error messages
      const errorMessage =
        error.response?.data?.detail || 'Failed to delete users. Please try again.'

      toast({
        title: 'Error',
        description: errorMessage,
        variant: 'error',
      })
    }
  }

  if (userCount === 0) return null

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent className="max-w-md">
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2">
            <Trash2 className="h-5 w-5 text-red-600" />
            Delete {userCount} User{userCount !== 1 ? 's' : ''}
          </AlertDialogTitle>
          <AlertDialogDescription>
            This action will permanently deactivate the following user accounts.
          </AlertDialogDescription>
        </AlertDialogHeader>

        {/* User list */}
        <div className="rounded-lg border bg-muted/50 p-3">
          <ScrollArea className={userCount > 5 ? 'h-40' : 'h-auto'}>
            <ul className="space-y-1 text-sm">
              {users.map((user) => (
                <li key={user.id} className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-red-500 flex-shrink-0" />
                  <span className="truncate">{user.email}</span>
                  {user.is_superuser && (
                    <span className="text-xs bg-yellow-100 text-yellow-800 px-1.5 py-0.5 rounded">
                      Admin
                    </span>
                  )}
                </li>
              ))}
            </ul>
          </ScrollArea>
          {userCount > 5 && (
            <p className="text-xs text-muted-foreground mt-2 text-center">
              Scroll to see all {userCount} users
            </p>
          )}
        </div>

        {/* Warning box */}
        <div className="rounded-lg bg-amber-50 border border-amber-200 p-4">
          <div className="flex gap-3">
            <AlertTriangle className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h4 className="text-sm font-medium text-amber-800">Warning</h4>
              <div className="mt-1 text-sm text-amber-700 space-y-1">
                <p>This action will:</p>
                <ul className="list-disc list-inside ml-2">
                  <li>Soft delete all selected accounts</li>
                  <li>Prevent future logins for these users</li>
                  <li>Keep all data for audit purposes</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Confirmation input */}
        <div className="space-y-2">
          <Label htmlFor="confirm-delete" className="text-sm">
            Type <span className="font-mono font-bold">DELETE</span> to confirm:
          </Label>
          <Input
            id="confirm-delete"
            value={confirmText}
            onChange={(e) => setConfirmText(e.target.value)}
            placeholder="Type DELETE to confirm"
            className={
              confirmText && !isConfirmValid
                ? 'border-red-300 focus:border-red-500'
                : ''
            }
            disabled={bulkDeleteMutation.isPending}
          />
          {confirmText && !isConfirmValid && (
            <p className="text-xs text-red-600">Please type DELETE exactly</p>
          )}
        </div>

        <AlertDialogFooter>
          <AlertDialogCancel disabled={bulkDeleteMutation.isPending}>
            Cancel
          </AlertDialogCancel>
          <Button
            variant="destructive"
            onClick={handleDelete}
            disabled={!isConfirmValid || bulkDeleteMutation.isPending}
            className="min-w-[140px]"
          >
            {bulkDeleteMutation.isPending
              ? 'Deleting...'
              : `Delete ${userCount} User${userCount !== 1 ? 's' : ''}`}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
