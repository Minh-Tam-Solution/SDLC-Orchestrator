/**
 * File: frontend/web/src/pages/admin/SystemSettingsPage.tsx
 * Version: 1.1.0
 * Status: ACTIVE - Sprint 39 Toast Notifications
 * Date: 2025-12-17
 * Authority: CTO Approved (ADR-017)
 * Framework: SDLC 5.1.1 Complete Lifecycle
 *
 * Description:
 * System Settings page for admin panel.
 * Manages database-backed configuration with version control for rollback.
 *
 * Security:
 * - Requires is_superuser=true
 * - All changes are audit logged
 * - Rollback capability (CTO requirement)
 *
 * Sprint 39: Toast Notifications
 * - Added toast feedback for settings changes
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { useToast } from '@/hooks/useToast'
import {
  useSystemSettings,
  useUpdateSystemSetting,
  useRollbackSystemSetting,
  SystemSettingItem,
} from '@/api/admin'

/**
 * Category badge
 */
function CategoryBadge({ category }: { category: string }) {
  const defaultConfig = { color: 'bg-gray-100 text-gray-700', label: 'General' }
  const categoryConfig: Record<string, { color: string; label: string }> = {
    security: { color: 'bg-red-100 text-red-700', label: 'Security' },
    limits: { color: 'bg-blue-100 text-blue-700', label: 'Limits' },
    features: { color: 'bg-green-100 text-green-700', label: 'Features' },
    notifications: { color: 'bg-yellow-100 text-yellow-700', label: 'Notifications' },
    general: defaultConfig,
  }

  const config = categoryConfig[category] ?? defaultConfig

  return (
    <span className={`rounded-full px-2 py-1 text-xs font-medium ${config.color}`}>
      {config.label}
    </span>
  )
}

/**
 * Setting value display
 */
function SettingValue({ value }: { value: unknown }) {
  if (typeof value === 'boolean') {
    return (
      <span className={`font-medium ${value ? 'text-green-600' : 'text-red-600'}`}>
        {value ? 'Enabled' : 'Disabled'}
      </span>
    )
  }

  if (typeof value === 'number') {
    return <span className="font-medium">{value}</span>
  }

  if (typeof value === 'string') {
    return <span className="font-medium">{value}</span>
  }

  return <span className="font-medium text-muted-foreground">{JSON.stringify(value)}</span>
}

/**
 * Setting row component with edit capability
 */
function SettingRow({
  setting,
  onUpdate,
  onRollback,
  isUpdating,
}: {
  setting: SystemSettingItem
  onUpdate: (key: string, value: unknown) => void
  onRollback: (key: string) => void
  isUpdating: boolean
}) {
  const [isEditing, setIsEditing] = useState(false)
  const [editValue, setEditValue] = useState<string>('')

  const handleEdit = () => {
    setEditValue(JSON.stringify(setting.value))
    setIsEditing(true)
  }

  const handleSave = () => {
    try {
      const parsedValue = JSON.parse(editValue)
      onUpdate(setting.key, parsedValue)
      setIsEditing(false)
    } catch {
      // Try as plain value
      onUpdate(setting.key, editValue)
      setIsEditing(false)
    }
  }

  const handleCancel = () => {
    setIsEditing(false)
    setEditValue('')
  }

  return (
    <div className="p-4 border rounded-lg hover:bg-muted/30 transition-colors">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h4 className="font-medium">{setting.key}</h4>
            <CategoryBadge category={setting.category} />
            <span className="text-xs text-muted-foreground">v{setting.version}</span>
          </div>
          {setting.description && (
            <p className="text-sm text-muted-foreground mb-2">{setting.description}</p>
          )}

          {isEditing ? (
            <div className="flex gap-2 mt-2">
              <Input
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                className="flex-1 font-mono text-sm"
                placeholder="Enter value (JSON format for complex values)"
              />
              <Button size="sm" onClick={handleSave} disabled={isUpdating}>
                Save
              </Button>
              <Button size="sm" variant="ghost" onClick={handleCancel}>
                Cancel
              </Button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <span className="text-sm">Value:</span>
              <SettingValue value={setting.value} />
            </div>
          )}

          {setting.updated_at && (
            <p className="text-xs text-muted-foreground mt-2">
              Last updated: {new Date(setting.updated_at).toLocaleString()}
              {setting.updated_by && ` by ${setting.updated_by}`}
            </p>
          )}
        </div>

        <div className="flex gap-2">
          {!isEditing && (
            <>
              <Button variant="outline" size="sm" onClick={handleEdit} disabled={isUpdating}>
                Edit
              </Button>
              {setting.version > 1 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onRollback(setting.key)}
                  disabled={isUpdating}
                  title="Rollback to previous version"
                >
                  Rollback
                </Button>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

/**
 * Settings category section
 */
function SettingsSection({
  title,
  description,
  settings,
  onUpdate,
  onRollback,
  isUpdating,
}: {
  title: string
  description: string
  settings: SystemSettingItem[]
  onUpdate: (key: string, value: unknown) => void
  onRollback: (key: string) => void
  isUpdating: boolean
}) {
  if (settings.length === 0) return null

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {settings.map((setting) => (
            <SettingRow
              key={setting.key}
              setting={setting}
              onUpdate={onUpdate}
              onRollback={onRollback}
              isUpdating={isUpdating}
            />
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * System Settings page component
 */
export default function SystemSettingsPage() {
  const navigate = useNavigate()
  const { toast } = useToast()

  // Fetch settings
  const { data: settings, isLoading, refetch } = useSystemSettings()

  // Mutations
  const updateMutation = useUpdateSystemSetting()
  const rollbackMutation = useRollbackSystemSetting()

  // Handle update
  const handleUpdate = async (key: string, value: unknown) => {
    try {
      await updateMutation.mutateAsync({ key, data: { value } })
      toast({
        title: 'Setting Updated',
        description: `"${key}" has been updated successfully`,
        variant: 'success',
      })
    } catch (error) {
      console.error('Failed to update setting:', error)
      toast({
        title: 'Update Failed',
        description: `Failed to update "${key}"`,
        variant: 'error',
      })
    }
  }

  // Handle rollback
  const handleRollback = async (key: string) => {
    if (!confirm(`Are you sure you want to rollback "${key}" to the previous version?`)) {
      return
    }

    try {
      await rollbackMutation.mutateAsync(key)
      toast({
        title: 'Setting Rolled Back',
        description: `"${key}" has been reverted to the previous version`,
        variant: 'info',
      })
    } catch (error) {
      console.error('Failed to rollback setting:', error)
      toast({
        title: 'Rollback Failed',
        description: `Failed to rollback "${key}"`,
        variant: 'error',
      })
    }
  }

  const isUpdating = updateMutation.isPending || rollbackMutation.isPending

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
              <h1 className="text-3xl font-bold tracking-tight">System Settings</h1>
            </div>
            <p className="text-muted-foreground">
              Configure system parameters with version control for rollback
            </p>
          </div>
          <Button variant="outline" onClick={() => refetch()} disabled={isLoading}>
            Refresh
          </Button>
        </div>

        {/* Settings sections */}
        {isLoading ? (
          <Card>
            <CardContent className="py-8">
              <div className="text-center text-muted-foreground">
                Loading settings...
              </div>
            </CardContent>
          </Card>
        ) : settings ? (
          <div className="space-y-6">
            <SettingsSection
              title="Security Settings"
              description="Authentication, authorization, and security parameters"
              settings={settings.security || []}
              onUpdate={handleUpdate}
              onRollback={handleRollback}
              isUpdating={isUpdating}
            />

            <SettingsSection
              title="System Limits"
              description="Rate limits, quotas, and resource constraints"
              settings={settings.limits || []}
              onUpdate={handleUpdate}
              onRollback={handleRollback}
              isUpdating={isUpdating}
            />

            <SettingsSection
              title="Feature Flags"
              description="Enable or disable specific features"
              settings={settings.features || []}
              onUpdate={handleUpdate}
              onRollback={handleRollback}
              isUpdating={isUpdating}
            />

            <SettingsSection
              title="Notification Settings"
              description="Email, webhook, and alert configurations"
              settings={settings.notifications || []}
              onUpdate={handleUpdate}
              onRollback={handleRollback}
              isUpdating={isUpdating}
            />

            <SettingsSection
              title="General Settings"
              description="General system configuration"
              settings={settings.general || []}
              onUpdate={handleUpdate}
              onRollback={handleRollback}
              isUpdating={isUpdating}
            />

            {/* Empty state if no settings */}
            {!settings.security?.length &&
              !settings.limits?.length &&
              !settings.features?.length &&
              !settings.notifications?.length &&
              !settings.general?.length && (
                <Card>
                  <CardContent className="py-8">
                    <div className="text-center text-muted-foreground">
                      <p>No system settings configured</p>
                      <p className="text-sm mt-1">
                        Settings will appear here when they are added to the system
                      </p>
                    </div>
                  </CardContent>
                </Card>
              )}
          </div>
        ) : (
          <Card>
            <CardContent className="py-8">
              <div className="text-center text-muted-foreground">
                Failed to load settings
              </div>
            </CardContent>
          </Card>
        )}

        {/* Info card */}
        <Card className="bg-muted/50">
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <svg className="h-5 w-5 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <p className="text-sm font-medium">Version Control</p>
                <p className="text-xs text-muted-foreground">
                  All settings changes are tracked with version numbers. Use the Rollback button to revert to the previous value.
                  Changes are audit logged for compliance.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}
