/**
 * File: frontend/web/src/components/admin/CreateUserDialog.tsx
 * Version: 1.0.0
 * Status: ACTIVE - Sprint 40 Admin Panel CRUD
 * Date: 2025-12-17
 * Authority: CTO Approved (Sprint 40)
 * Framework: SDLC 5.1.1 Complete Lifecycle
 *
 * Description:
 * Dialog component for creating new users in Admin Panel.
 * Validates email uniqueness and password strength (12+ chars).
 *
 * Security:
 * - Password minimum 12 characters (enforced)
 * - Email format validation
 * - Toast feedback on success/error
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
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { useToast } from '@/hooks/useToast'
import { useCreateAdminUser } from '@/api/admin'

interface CreateUserDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function CreateUserDialog({ open, onOpenChange }: CreateUserDialogProps) {
  const { toast } = useToast()
  const createUserMutation = useCreateAdminUser()

  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
    is_active: true,
    is_superuser: false,
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  const validateForm = () => {
    const newErrors: Record<string, string> = {}

    // Email validation
    if (!formData.email) {
      newErrors.email = 'Email is required'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Invalid email format'
    }

    // Password validation
    if (!formData.password) {
      newErrors.password = 'Password is required'
    } else if (formData.password.length < 12) {
      newErrors.password = 'Password must be at least 12 characters'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) {
      return
    }

    try {
      await createUserMutation.mutateAsync({
        email: formData.email,
        password: formData.password,
        name: formData.name || undefined,
        is_active: formData.is_active,
        is_superuser: formData.is_superuser,
      })

      toast({
        title: 'User Created',
        description: `User ${formData.email} has been created successfully`,
        variant: 'success',
      })

      // Reset form and close dialog
      setFormData({
        email: '',
        password: '',
        name: '',
        is_active: true,
        is_superuser: false,
      })
      setErrors({})
      onOpenChange(false)
    } catch (error: any) {
      console.error('Failed to create user:', error)

      // Check for specific error messages
      const errorMessage =
        error.response?.data?.detail || 'Failed to create user. Please try again.'

      toast({
        title: 'Error',
        description: errorMessage,
        variant: 'error',
      })
    }
  }

  const handleCancel = () => {
    setFormData({
      email: '',
      password: '',
      name: '',
      is_active: true,
      is_superuser: false,
    })
    setErrors({})
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Create New User</DialogTitle>
            <DialogDescription>
              Create a new user account. The user will be able to login with the email and
              password provided.
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            {/* Email */}
            <div className="grid gap-2">
              <Label htmlFor="email">
                Email <span className="text-red-500">*</span>
              </Label>
              <Input
                id="email"
                type="email"
                placeholder="user@example.com"
                value={formData.email}
                onChange={(e) => {
                  setFormData({ ...formData, email: e.target.value })
                  setErrors({ ...errors, email: '' })
                }}
                className={errors.email ? 'border-red-500' : ''}
              />
              {errors.email && (
                <p className="text-sm text-red-500">{errors.email}</p>
              )}
            </div>

            {/* Password */}
            <div className="grid gap-2">
              <Label htmlFor="password">
                Password <span className="text-red-500">*</span>
              </Label>
              <Input
                id="password"
                type="password"
                placeholder="Min 12 characters"
                value={formData.password}
                onChange={(e) => {
                  setFormData({ ...formData, password: e.target.value })
                  setErrors({ ...errors, password: '' })
                }}
                className={errors['password'] ? 'border-red-500' : ''}
              />
              {errors['password'] && (
                <p className="text-sm text-red-500">{errors['password']}</p>
              )}
              <p className="text-sm text-muted-foreground">
                Password must be at least 12 characters long
              </p>
            </div>

            {/* Name */}
            <div className="grid gap-2">
              <Label htmlFor="name">Full Name (Optional)</Label>
              <Input
                id="name"
                type="text"
                placeholder="John Doe"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </div>

            {/* Active Status */}
            <div className="flex items-center space-x-2">
              <Checkbox
                id="is_active"
                checked={formData.is_active}
                onCheckedChange={(checked: boolean) =>
                  setFormData({ ...formData, is_active: checked === true })
                }
              />
              <Label htmlFor="is_active" className="cursor-pointer font-normal">
                Active (user can login)
              </Label>
            </div>

            {/* Superuser Status */}
            <div className="flex items-center space-x-2">
              <Checkbox
                id="is_superuser"
                checked={formData.is_superuser}
                onCheckedChange={(checked: boolean) =>
                  setFormData({ ...formData, is_superuser: checked === true })
                }
              />
              <Label htmlFor="is_superuser" className="cursor-pointer font-normal">
                <span>Administrator (full platform access)</span>
                <p className="text-sm text-muted-foreground font-normal">
                  Admins can manage all users and system settings
                </p>
              </Label>
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleCancel}>
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={createUserMutation.isPending}
            >
              {createUserMutation.isPending ? 'Creating...' : 'Create User'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
