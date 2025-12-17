/**
 * File: frontend/web/src/components/admin/EditUserDialog.tsx
 * Version: 1.0.0
 * Status: ACTIVE - Sprint 40 Part 2 Admin Panel CRUD
 * Date: 2025-12-17
 * Authority: CTO Approved (Sprint 40 Part 2)
 * Framework: SDLC 5.1.1 Complete Lifecycle
 *
 * Description:
 * Dialog component for editing existing users in Admin Panel.
 * Supports email change, password reset, name update, and status changes.
 *
 * Sprint 40 Part 2 Features:
 * - Edit user email with uniqueness validation
 * - Reset user password (optional, 12+ chars if provided)
 * - Update name, is_active, is_superuser
 * - Pre-filled form with current user data
 * - Toast feedback on success/error
 *
 * Security:
 * - Password minimum 12 characters (if provided)
 * - Email format and uniqueness validation
 * - Cannot edit self status (handled by backend)
 */

import { useState, useEffect } from 'react'
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
import { Checkbox } from '@/components/ui/checkbox'
import { useToast } from '@/hooks/useToast'
import { useUpdateAdminUserFull, type AdminUserListItem } from '@/api/admin'

interface EditUserDialogProps {
  user: AdminUserListItem | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function EditUserDialog({ user, open, onOpenChange }: EditUserDialogProps) {
  const { toast } = useToast()
  const updateUserMutation = useUpdateAdminUserFull()

  const [formData, setFormData] = useState({
    email: '',
    name: '',
    new_password: '',
    is_active: true,
    is_superuser: false,
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  // Pre-fill form when user changes
  useEffect(() => {
    if (user && open) {
      setFormData({
        email: user.email,
        name: user.name || '',
        new_password: '', // Always empty for security
        is_active: user.is_active,
        is_superuser: user.is_superuser,
      })
      setErrors({}) // Clear errors when opening dialog
    }
  }, [user, open])

  const validateForm = () => {
    const newErrors: Record<string, string> = {}

    // Email validation (required)
    if (!formData.email) {
      newErrors.email = 'Email is required'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Invalid email format'
    }

    // Password validation (optional, but must be 12+ chars if provided)
    if (formData.new_password && formData.new_password.length < 12) {
      newErrors.new_password = 'Password must be at least 12 characters'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!user || !validateForm()) {
      return
    }

    try {
      await updateUserMutation.mutateAsync({
        userId: user.id,
        data: {
          email: formData.email !== user.email ? formData.email : undefined,
          name: formData.name !== user.name ? formData.name : undefined,
          new_password: formData.new_password || undefined,
          is_active: formData.is_active !== user.is_active ? formData.is_active : undefined,
          is_superuser: formData.is_superuser !== user.is_superuser ? formData.is_superuser : undefined,
        },
      })

      toast({
        title: 'User Updated',
        description: `User ${formData.email} has been updated successfully`,
        variant: 'success',
      })

      // Close dialog (parent will refresh data)
      onOpenChange(false)
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to update user',
        variant: 'error',
      })
    }
  }

  const handleChange = (field: string, value: string | boolean) => {
    setFormData((prev) => ({ ...prev, [field]: value }))

    // Clear error for this field when user types
    if (errors[field]) {
      setErrors((prev) => {
        const newErrors = { ...prev }
        delete newErrors[field]
        return newErrors
      })
    }
  }

  if (!user) return null

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Edit User</DialogTitle>
            <DialogDescription>
              Update user information. Leave password empty to keep current password.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            {/* Email Field */}
            <div className="space-y-2">
              <Label htmlFor="email">
                Email <span className="text-red-500">*</span>
              </Label>
              <Input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => handleChange('email', e.target.value)}
                placeholder="user@example.com"
                className={errors.email ? 'border-red-500' : ''}
              />
              {errors.email && (
                <p className="text-sm text-red-500">{errors.email}</p>
              )}
            </div>

            {/* Password Field (Optional) */}
            <div className="space-y-2">
              <Label htmlFor="new_password">
                New Password <span className="text-gray-400">(Optional)</span>
              </Label>
              <Input
                id="new_password"
                type="password"
                value={formData.new_password}
                onChange={(e) => handleChange('new_password', e.target.value)}
                placeholder="Leave empty to keep current password"
                className={errors.new_password ? 'border-red-500' : ''}
              />
              {errors.new_password && (
                <p className="text-sm text-red-500">{errors.new_password}</p>
              )}
              <p className="text-xs text-gray-500">
                Password must be at least 12 characters (if changing)
              </p>
            </div>

            {/* Name Field */}
            <div className="space-y-2">
              <Label htmlFor="name">Full Name</Label>
              <Input
                id="name"
                type="text"
                value={formData.name}
                onChange={(e) => handleChange('name', e.target.value)}
                placeholder="John Doe"
              />
            </div>

            {/* Active Checkbox */}
            <div className="flex items-center space-x-2">
              <Checkbox
                id="is_active"
                checked={formData.is_active}
                onCheckedChange={(checked) => handleChange('is_active', !!checked)}
              />
              <Label
                htmlFor="is_active"
                className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
              >
                Active (user can login to the system)
              </Label>
            </div>

            {/* Superuser Checkbox */}
            <div className="flex items-center space-x-2">
              <Checkbox
                id="is_superuser"
                checked={formData.is_superuser}
                onCheckedChange={(checked) => handleChange('is_superuser', !!checked)}
              />
              <Label
                htmlFor="is_superuser"
                className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
              >
                Administrator (full platform access)
              </Label>
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={updateUserMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={updateUserMutation.isPending}
            >
              {updateUserMutation.isPending ? 'Updating...' : 'Update User'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
