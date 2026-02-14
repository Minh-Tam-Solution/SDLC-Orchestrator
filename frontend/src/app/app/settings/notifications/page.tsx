/**
 * =========================================================================
 * Notification Settings Page - User Preferences
 * SDLC Orchestrator - Sprint 153 (Real-time Notifications)
 *
 * Version: 1.0.0
 * Date: February 4, 2026
 * Status: ACTIVE - Sprint 153 Day 5
 * Authority: Frontend Lead + CTO Approved
 * Framework: SDLC 6.0.5
 *
 * Purpose:
 * - Manage notification channel preferences (email, push, WebSocket)
 * - Configure notification types to receive
 * - Set quiet hours for notifications
 * - Manage push notification subscriptions
 *
 * Zero Mock Policy: Production-ready notification preferences
 * =========================================================================
 */

'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Bell,
  Mail,
  Smartphone,
  Monitor,
  Moon,
  Save,
  Loader2,
  ChevronLeft,
  AlertTriangle,
  Check,
  Shield,
  FileCheck,
  Users,
  GitPullRequest,
} from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/components/ui/use-toast';
import { api } from '@/lib/api';
import { PushNotificationOptIn } from '@/components/notifications/PushNotificationOptIn';

// ============================================================================
// Types
// ============================================================================

interface NotificationPreferences {
  // Channel preferences
  email_enabled: boolean;
  push_enabled: boolean;
  in_app_enabled: boolean;

  // Notification type preferences
  gate_notifications: boolean;
  evidence_notifications: boolean;
  policy_notifications: boolean;
  team_notifications: boolean;
  system_notifications: boolean;

  // Quiet hours
  quiet_hours_enabled: boolean;
  quiet_hours_start: string;
  quiet_hours_end: string;

  // Email digest
  email_digest_enabled: boolean;
  email_digest_frequency: 'daily' | 'weekly' | 'never';
}

const defaultPreferences: NotificationPreferences = {
  email_enabled: true,
  push_enabled: false,
  in_app_enabled: true,
  gate_notifications: true,
  evidence_notifications: true,
  policy_notifications: true,
  team_notifications: true,
  system_notifications: true,
  quiet_hours_enabled: false,
  quiet_hours_start: '22:00',
  quiet_hours_end: '08:00',
  email_digest_enabled: false,
  email_digest_frequency: 'daily',
};

// ============================================================================
// API Functions
// ============================================================================

async function fetchPreferences(): Promise<NotificationPreferences> {
  try {
    const response = await api.get<NotificationPreferences>('/notifications/preferences');
    return response.data;
  } catch {
    // Return defaults if API fails
    return defaultPreferences;
  }
}

async function savePreferences(preferences: NotificationPreferences): Promise<void> {
  await api.put('/notifications/preferences', preferences);
}

// ============================================================================
// Main Component
// ============================================================================

export default function NotificationSettingsPage() {
  const [preferences, setPreferences] = useState<NotificationPreferences>(defaultPreferences);
  const [hasChanges, setHasChanges] = useState(false);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  // Fetch current preferences
  const { isLoading, data } = useQuery({
    queryKey: ['notification-preferences'],
    queryFn: fetchPreferences,
    onSuccess: (data) => {
      setPreferences(data);
    },
  });

  // Save mutation
  const saveMutation = useMutation({
    mutationFn: savePreferences,
    onSuccess: () => {
      setHasChanges(false);
      queryClient.invalidateQueries({ queryKey: ['notification-preferences'] });
      toast({
        title: 'Settings saved',
        description: 'Your notification preferences have been updated.',
        duration: 3000,
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to save notification preferences.',
        variant: 'destructive',
        duration: 5000,
      });
    },
  });

  // Update preference helper
  const updatePreference = <K extends keyof NotificationPreferences>(
    key: K,
    value: NotificationPreferences[K]
  ) => {
    setPreferences((prev) => ({ ...prev, [key]: value }));
    setHasChanges(true);
  };

  const handleSave = () => {
    saveMutation.mutate(preferences);
  };

  if (isLoading) {
    return (
      <div className="container mx-auto py-6 max-w-4xl">
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Link href="/app/notifications">
          <Button variant="ghost" size="icon">
            <ChevronLeft className="h-5 w-5" />
          </Button>
        </Link>
        <div className="flex-1">
          <h1 className="text-2xl font-bold">Notification Settings</h1>
          <p className="text-muted-foreground">
            Manage how and when you receive notifications
          </p>
        </div>
        <Button
          onClick={handleSave}
          disabled={!hasChanges || saveMutation.isPending}
        >
          {saveMutation.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin mr-2" />
          ) : (
            <Save className="h-4 w-4 mr-2" />
          )}
          Save Changes
        </Button>
      </div>

      <div className="space-y-6">
        {/* Notification Channels */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              Notification Channels
            </CardTitle>
            <CardDescription>
              Choose how you want to receive notifications
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Email */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                  <Mail className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <Label className="text-base">Email Notifications</Label>
                  <p className="text-sm text-muted-foreground">
                    Receive notifications via email
                  </p>
                </div>
              </div>
              <Switch
                checked={preferences.email_enabled}
                onCheckedChange={(checked) => updatePreference('email_enabled', checked)}
              />
            </div>

            <Separator />

            {/* Push Notifications */}
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                  <Smartphone className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                </div>
                <div>
                  <Label className="text-base">Browser Push Notifications</Label>
                  <p className="text-sm text-muted-foreground">
                    Receive push notifications in your browser
                  </p>
                </div>
              </div>
              <PushNotificationOptIn
                variant="compact"
                onSubscriptionChange={(isSubscribed) =>
                  updatePreference('push_enabled', isSubscribed)
                }
              />
            </div>

            <Separator />

            {/* In-App */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
                  <Monitor className="h-5 w-5 text-green-600 dark:text-green-400" />
                </div>
                <div>
                  <Label className="text-base">In-App Notifications</Label>
                  <p className="text-sm text-muted-foreground">
                    Show notifications in the notification center
                  </p>
                </div>
              </div>
              <Switch
                checked={preferences.in_app_enabled}
                onCheckedChange={(checked) => updatePreference('in_app_enabled', checked)}
              />
            </div>
          </CardContent>
        </Card>

        {/* Notification Types */}
        <Card>
          <CardHeader>
            <CardTitle>Notification Types</CardTitle>
            <CardDescription>
              Select which types of notifications you want to receive
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Gate Notifications */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <GitPullRequest className="h-5 w-5 text-blue-500" />
                <div>
                  <Label>Gate Notifications</Label>
                  <p className="text-sm text-muted-foreground">
                    Gate approvals, rejections, and approval requests
                  </p>
                </div>
              </div>
              <Switch
                checked={preferences.gate_notifications}
                onCheckedChange={(checked) => updatePreference('gate_notifications', checked)}
              />
            </div>

            <Separator />

            {/* Evidence Notifications */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <FileCheck className="h-5 w-5 text-purple-500" />
                <div>
                  <Label>Evidence Notifications</Label>
                  <p className="text-sm text-muted-foreground">
                    Evidence uploads, reviews, and validations
                  </p>
                </div>
              </div>
              <Switch
                checked={preferences.evidence_notifications}
                onCheckedChange={(checked) => updatePreference('evidence_notifications', checked)}
              />
            </div>

            <Separator />

            {/* Policy Notifications */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <AlertTriangle className="h-5 w-5 text-orange-500" />
                <div>
                  <Label>Policy Violations</Label>
                  <p className="text-sm text-muted-foreground">
                    Policy violations and compliance alerts
                  </p>
                </div>
              </div>
              <Switch
                checked={preferences.policy_notifications}
                onCheckedChange={(checked) => updatePreference('policy_notifications', checked)}
              />
            </div>

            <Separator />

            {/* Team Notifications */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Users className="h-5 w-5 text-cyan-500" />
                <div>
                  <Label>Team Notifications</Label>
                  <p className="text-sm text-muted-foreground">
                    Team member changes and invitations
                  </p>
                </div>
              </div>
              <Switch
                checked={preferences.team_notifications}
                onCheckedChange={(checked) => updatePreference('team_notifications', checked)}
              />
            </div>

            <Separator />

            {/* System Notifications */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Shield className="h-5 w-5 text-gray-500" />
                <div>
                  <Label>System Notifications</Label>
                  <p className="text-sm text-muted-foreground">
                    System updates, maintenance, and announcements
                  </p>
                </div>
              </div>
              <Switch
                checked={preferences.system_notifications}
                onCheckedChange={(checked) => updatePreference('system_notifications', checked)}
              />
            </div>
          </CardContent>
        </Card>

        {/* Quiet Hours */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Moon className="h-5 w-5" />
              Quiet Hours
            </CardTitle>
            <CardDescription>
              Pause notifications during specific times
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <Label>Enable Quiet Hours</Label>
                <p className="text-sm text-muted-foreground">
                  Pause push and in-app notifications
                </p>
              </div>
              <Switch
                checked={preferences.quiet_hours_enabled}
                onCheckedChange={(checked) => updatePreference('quiet_hours_enabled', checked)}
              />
            </div>

            {preferences.quiet_hours_enabled && (
              <div className="grid grid-cols-2 gap-4 pt-4">
                <div>
                  <Label htmlFor="start-time">Start Time</Label>
                  <Select
                    value={preferences.quiet_hours_start}
                    onValueChange={(value) => updatePreference('quiet_hours_start', value)}
                  >
                    <SelectTrigger id="start-time">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Array.from({ length: 24 }, (_, i) => {
                        const hour = i.toString().padStart(2, '0');
                        return (
                          <SelectItem key={hour} value={`${hour}:00`}>
                            {hour}:00
                          </SelectItem>
                        );
                      })}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="end-time">End Time</Label>
                  <Select
                    value={preferences.quiet_hours_end}
                    onValueChange={(value) => updatePreference('quiet_hours_end', value)}
                  >
                    <SelectTrigger id="end-time">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Array.from({ length: 24 }, (_, i) => {
                        const hour = i.toString().padStart(2, '0');
                        return (
                          <SelectItem key={hour} value={`${hour}:00`}>
                            {hour}:00
                          </SelectItem>
                        );
                      })}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Email Digest */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Mail className="h-5 w-5" />
              Email Digest
            </CardTitle>
            <CardDescription>
              Receive a summary of notifications via email
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <Label>Enable Email Digest</Label>
                <p className="text-sm text-muted-foreground">
                  Get a summary instead of individual emails
                </p>
              </div>
              <Switch
                checked={preferences.email_digest_enabled}
                onCheckedChange={(checked) => updatePreference('email_digest_enabled', checked)}
              />
            </div>

            {preferences.email_digest_enabled && (
              <div className="pt-4">
                <Label>Digest Frequency</Label>
                <Select
                  value={preferences.email_digest_frequency}
                  onValueChange={(value) =>
                    updatePreference('email_digest_frequency', value as 'daily' | 'weekly' | 'never')
                  }
                >
                  <SelectTrigger className="w-[200px] mt-2">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="daily">Daily</SelectItem>
                    <SelectItem value="weekly">Weekly</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Save Button (Mobile) */}
        <div className="flex justify-end md:hidden">
          <Button
            onClick={handleSave}
            disabled={!hasChanges || saveMutation.isPending}
            className="w-full"
          >
            {saveMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <Save className="h-4 w-4 mr-2" />
            )}
            Save Changes
          </Button>
        </div>
      </div>
    </div>
  );
}
