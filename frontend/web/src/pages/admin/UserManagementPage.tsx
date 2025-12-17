/**
 * File: frontend/web/src/pages/admin/UserManagementPage.tsx
 * Version: 1.1.0
 * Status: ACTIVE - Sprint 39 Toast Notifications
 * Date: 2025-12-17
 * Authority: CTO Approved (ADR-017)
 * Framework: SDLC 5.1.1 Complete Lifecycle
 *
 * Description:
 * User Management page for admin panel.
 * Lists all users with search, filter, and bulk actions.
 *
 * Security:
 * - Requires is_superuser=true
 * - Self-action prevention (cannot modify own account)
 * - Minimum superuser protection (always keep at least 1)
 *
 * Sprint 39: Toast Notifications
 * - Added toast feedback for user actions
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { useAuth } from '@/contexts/AuthContext'
import { useToast } from '@/hooks/useToast'
import {
  useAdminUsers,
  useUpdateAdminUser,
  useBulkUserAction,
  AdminUserListItem,
} from '@/api/admin'

/**
 * User status badge
 */
function UserStatusBadge({ isActive }: { isActive: boolean }) {
  return (
    <span
      className={`rounded-full px-2 py-1 text-xs font-medium ${
        isActive
          ? 'bg-green-100 text-green-700'
          : 'bg-red-100 text-red-700'
      }`}
    >
      {isActive ? 'Active' : 'Inactive'}
    </span>
  )
}

/**
 * Superuser badge
 */
function SuperuserBadge({ isSuperuser }: { isSuperuser: boolean }) {
  if (!isSuperuser) return null
  return (
    <span className="rounded-full px-2 py-1 text-xs font-medium bg-purple-100 text-purple-700">
      Admin
    </span>
  )
}

/**
 * User Management page component
 */
export default function UserManagementPage() {
  const navigate = useNavigate()
  const { user: currentUser } = useAuth()
  const { toast } = useToast()

  // Search and filter state
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [activeFilter, setActiveFilter] = useState<boolean | undefined>(undefined)
  const [superuserFilter, setSuperuserFilter] = useState<boolean | undefined>(undefined)

  // Selected users for bulk actions
  const [selectedUsers, setSelectedUsers] = useState<string[]>([])

  // Fetch users
  const { data: usersData, isLoading, refetch } = useAdminUsers({
    page,
    page_size: 20,
    ...(search ? { search } : {}),
    ...(activeFilter !== undefined ? { is_active: activeFilter } : {}),
    ...(superuserFilter !== undefined ? { is_superuser: superuserFilter } : {}),
  })

  // Mutations
  const updateUserMutation = useUpdateAdminUser()
  const bulkActionMutation = useBulkUserAction()

  // Handle toggle active
  const handleToggleActive = async (user: AdminUserListItem) => {
    try {
      await updateUserMutation.mutateAsync({
        userId: user.id,
        data: { is_active: !user.is_active },
      })
      toast({
        title: user.is_active ? 'User Deactivated' : 'User Activated',
        description: `${user.email} has been ${user.is_active ? 'deactivated' : 'activated'}`,
        variant: user.is_active ? 'warning' : 'success',
      })
    } catch (error) {
      console.error('Failed to update user:', error)
      toast({
        title: 'Error',
        description: 'Failed to update user status',
        variant: 'error',
      })
    }
  }

  // Handle toggle superuser
  const handleToggleSuperuser = async (user: AdminUserListItem) => {
    try {
      await updateUserMutation.mutateAsync({
        userId: user.id,
        data: { is_superuser: !user.is_superuser },
      })
      toast({
        title: user.is_superuser ? 'Admin Removed' : 'Admin Added',
        description: `${user.email} ${user.is_superuser ? 'is no longer an admin' : 'is now an admin'}`,
        variant: 'success',
      })
    } catch (error) {
      console.error('Failed to update user:', error)
      toast({
        title: 'Error',
        description: 'Failed to update admin status',
        variant: 'error',
      })
    }
  }

  // Handle bulk action
  const handleBulkAction = async (action: 'activate' | 'deactivate') => {
    if (selectedUsers.length === 0) return

    try {
      const result = await bulkActionMutation.mutateAsync({
        user_ids: selectedUsers,
        action,
      })

      if (result.failed_count > 0) {
        toast({
          title: 'Partial Success',
          description: `${result.success_count} users ${action}d, ${result.failed_count} failed`,
          variant: 'warning',
        })
      } else {
        toast({
          title: 'Bulk Action Complete',
          description: `${result.success_count} user(s) ${action}d successfully`,
          variant: 'success',
        })
      }

      setSelectedUsers([])
      refetch()
    } catch (error) {
      console.error('Bulk action failed:', error)
      toast({
        title: 'Bulk Action Failed',
        description: `Failed to ${action} users`,
        variant: 'error',
      })
    }
  }

  // Toggle user selection
  const toggleUserSelection = (userId: string) => {
    setSelectedUsers((prev) =>
      prev.includes(userId)
        ? prev.filter((id) => id !== userId)
        : [...prev, userId]
    )
  }

  // Select all users (except current user)
  const selectAllUsers = () => {
    if (!usersData?.items) return

    const allIds = usersData.items
      .filter((u) => u.id !== currentUser?.id)
      .map((u) => u.id)

    setSelectedUsers((prev) =>
      prev.length === allIds.length ? [] : allIds
    )
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Page header */}
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/admin')}
                className="h-8 w-8 p-0"
              >
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </Button>
              <h1 className="text-3xl font-bold tracking-tight">User Management</h1>
            </div>
            <p className="text-muted-foreground">
              Manage user accounts, permissions, and access
            </p>
          </div>
          <div className="text-sm text-muted-foreground">
            {usersData?.total ?? 0} users total
          </div>
        </div>

        {/* Search and filters */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-wrap gap-4">
              <div className="flex-1 min-w-[200px]">
                <Input
                  placeholder="Search by email or name..."
                  value={search}
                  onChange={(e) => {
                    setSearch(e.target.value)
                    setPage(1)
                  }}
                  className="w-full"
                />
              </div>
              <div className="flex gap-2">
                <Button
                  variant={activeFilter === true ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => {
                    setActiveFilter(activeFilter === true ? undefined : true)
                    setPage(1)
                  }}
                >
                  Active
                </Button>
                <Button
                  variant={activeFilter === false ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => {
                    setActiveFilter(activeFilter === false ? undefined : false)
                    setPage(1)
                  }}
                >
                  Inactive
                </Button>
                <Button
                  variant={superuserFilter === true ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => {
                    setSuperuserFilter(superuserFilter === true ? undefined : true)
                    setPage(1)
                  }}
                >
                  Admins Only
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Bulk actions */}
        {selectedUsers.length > 0 && (
          <Card className="border-primary">
            <CardContent className="py-3">
              <div className="flex items-center justify-between">
                <span className="text-sm">
                  {selectedUsers.length} user(s) selected
                </span>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleBulkAction('activate')}
                    disabled={bulkActionMutation.isPending}
                  >
                    Activate Selected
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => handleBulkAction('deactivate')}
                    disabled={bulkActionMutation.isPending}
                  >
                    Deactivate Selected
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSelectedUsers([])}
                  >
                    Clear Selection
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Users table */}
        <Card>
          <CardHeader>
            <CardTitle>Users</CardTitle>
            <CardDescription>
              Click on actions to manage individual users or select multiple for bulk operations
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="text-center py-8 text-muted-foreground">
                Loading users...
              </div>
            ) : usersData?.items && usersData.items.length > 0 ? (
              <>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b text-left">
                        <th className="p-3 w-8">
                          <input
                            type="checkbox"
                            checked={
                              selectedUsers.length > 0 &&
                              selectedUsers.length ===
                                usersData.items.filter((u) => u.id !== currentUser?.id).length
                            }
                            onChange={selectAllUsers}
                            className="rounded"
                          />
                        </th>
                        <th className="p-3 font-medium">User</th>
                        <th className="p-3 font-medium">Status</th>
                        <th className="p-3 font-medium">Created</th>
                        <th className="p-3 font-medium">Last Login</th>
                        <th className="p-3 font-medium">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {usersData.items.map((user) => (
                        <tr key={user.id} className="border-b hover:bg-muted/50">
                          <td className="p-3">
                            <input
                              type="checkbox"
                              checked={selectedUsers.includes(user.id)}
                              onChange={() => toggleUserSelection(user.id)}
                              disabled={user.id === currentUser?.id}
                              className="rounded"
                            />
                          </td>
                          <td className="p-3">
                            <div className="flex items-center gap-3">
                              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted text-muted-foreground">
                                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                                </svg>
                              </div>
                              <div>
                                <p className="font-medium">
                                  {user.name || 'No Name'}
                                  {user.id === currentUser?.id && (
                                    <span className="ml-2 text-xs text-muted-foreground">(You)</span>
                                  )}
                                </p>
                                <p className="text-sm text-muted-foreground">{user.email}</p>
                              </div>
                            </div>
                          </td>
                          <td className="p-3">
                            <div className="flex gap-2">
                              <UserStatusBadge isActive={user.is_active} />
                              <SuperuserBadge isSuperuser={user.is_superuser} />
                            </div>
                          </td>
                          <td className="p-3 text-sm text-muted-foreground">
                            {new Date(user.created_at).toLocaleDateString()}
                          </td>
                          <td className="p-3 text-sm text-muted-foreground">
                            {user.last_login
                              ? new Date(user.last_login).toLocaleDateString()
                              : 'Never'}
                          </td>
                          <td className="p-3">
                            <div className="flex gap-2">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleToggleActive(user)}
                                disabled={user.id === currentUser?.id || updateUserMutation.isPending}
                                title={user.id === currentUser?.id ? 'Cannot modify your own account' : ''}
                              >
                                {user.is_active ? 'Deactivate' : 'Activate'}
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleToggleSuperuser(user)}
                                disabled={user.id === currentUser?.id || updateUserMutation.isPending}
                                title={user.id === currentUser?.id ? 'Cannot modify your own account' : ''}
                              >
                                {user.is_superuser ? 'Remove Admin' : 'Make Admin'}
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Pagination */}
                {usersData.pages > 1 && (
                  <div className="flex items-center justify-between mt-4 pt-4 border-t">
                    <div className="text-sm text-muted-foreground">
                      Page {usersData.page} of {usersData.pages}
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
                        onClick={() => setPage((p) => Math.min(usersData.pages, p + 1))}
                        disabled={page === usersData.pages}
                      >
                        Next
                      </Button>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <p>No users found</p>
                {search && (
                  <p className="text-sm mt-1">
                    Try adjusting your search or filters
                  </p>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}
