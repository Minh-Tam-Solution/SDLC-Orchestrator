/**
 * =========================================================================
 * Push Notification Opt-In Component
 * SDLC Orchestrator - Sprint 153 (Real-time Notifications)
 *
 * Version: 1.0.0
 * Date: February 4, 2026
 * Status: ACTIVE - Sprint 153 Day 4
 * Authority: Frontend Lead + CTO Approved
 * Framework: SDLC 6.0.3
 *
 * Purpose:
 * - Display push notification opt-in banner/card
 * - Handle permission request flow
 * - Show subscription status
 * - Allow enable/disable toggle
 *
 * Zero Mock Policy: Production-ready opt-in UI
 * =========================================================================
 */

'use client';

import React, { useState } from 'react';
import { Bell, BellOff, BellRing, Check, X, AlertTriangle, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { cn } from '@/lib/utils';
import { usePushNotifications, type PushPermissionState } from '@/hooks/usePushNotifications';

// ============================================================================
// Types
// ============================================================================

interface PushNotificationOptInProps {
  /** Display as banner (horizontal) or card (vertical) */
  variant?: 'banner' | 'card' | 'compact';
  /** Custom class name */
  className?: string;
  /** Callback when subscription state changes */
  onSubscriptionChange?: (isSubscribed: boolean) => void;
  /** Show dismiss button for banner */
  dismissible?: boolean;
  /** Callback when banner is dismissed */
  onDismiss?: () => void;
}

// ============================================================================
// Helper Components
// ============================================================================

function getPermissionIcon(permission: PushPermissionState, isSubscribed: boolean) {
  if (permission === 'denied') {
    return <BellOff className="h-5 w-5 text-red-500" />;
  }
  if (isSubscribed) {
    return <BellRing className="h-5 w-5 text-green-500" />;
  }
  return <Bell className="h-5 w-5 text-muted-foreground" />;
}

function getStatusText(permission: PushPermissionState, isSubscribed: boolean): string {
  if (permission === 'unsupported') {
    return 'Push notifications are not supported in your browser';
  }
  if (permission === 'denied') {
    return 'Push notifications are blocked. Please enable them in your browser settings.';
  }
  if (isSubscribed) {
    return 'You will receive push notifications for important updates';
  }
  return 'Enable push notifications to stay updated on gate approvals and policy violations';
}

// ============================================================================
// Banner Variant
// ============================================================================

function PushNotificationBanner({
  className,
  onSubscriptionChange,
  dismissible,
  onDismiss,
}: PushNotificationOptInProps) {
  const [dismissed, setDismissed] = useState(false);
  const {
    isSupported,
    permission,
    isSubscribed,
    isLoading,
    error,
    subscribe,
    unsubscribe,
  } = usePushNotifications();

  const handleToggle = async () => {
    let success: boolean;
    if (isSubscribed) {
      success = await unsubscribe();
    } else {
      success = await subscribe();
    }
    if (success) {
      onSubscriptionChange?.(!isSubscribed);
    }
  };

  const handleDismiss = () => {
    setDismissed(true);
    onDismiss?.();
  };

  // Don't show if unsupported, denied, already subscribed, or dismissed
  if (!isSupported || permission === 'denied' || isSubscribed || dismissed) {
    return null;
  }

  return (
    <div
      className={cn(
        'flex items-center justify-between gap-4 bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 rounded-lg p-4',
        className
      )}
    >
      <div className="flex items-center gap-3">
        <div className="flex-shrink-0 p-2 bg-blue-100 dark:bg-blue-900/50 rounded-full">
          <Bell className="h-5 w-5 text-blue-600 dark:text-blue-400" />
        </div>
        <div>
          <p className="font-medium text-sm">Enable Push Notifications</p>
          <p className="text-xs text-muted-foreground">
            Get notified about gate approvals and policy violations
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <Button
          size="sm"
          onClick={handleToggle}
          disabled={isLoading}
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin mr-1" />
          ) : (
            <Bell className="h-4 w-4 mr-1" />
          )}
          Enable
        </Button>
        {dismissible && (
          <Button
            variant="ghost"
            size="icon"
            onClick={handleDismiss}
            className="h-8 w-8"
          >
            <X className="h-4 w-4" />
          </Button>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Card Variant
// ============================================================================

function PushNotificationCard({
  className,
  onSubscriptionChange,
}: PushNotificationOptInProps) {
  const {
    isSupported,
    permission,
    isSubscribed,
    isLoading,
    error,
    subscribe,
    unsubscribe,
  } = usePushNotifications();

  const handleToggle = async () => {
    let success: boolean;
    if (isSubscribed) {
      success = await unsubscribe();
    } else {
      success = await subscribe();
    }
    if (success) {
      onSubscriptionChange?.(!isSubscribed);
    }
  };

  return (
    <Card className={cn('', className)}>
      <CardHeader>
        <div className="flex items-center gap-3">
          {getPermissionIcon(permission, isSubscribed)}
          <div>
            <CardTitle className="text-base">Push Notifications</CardTitle>
            <CardDescription className="text-sm">
              {getStatusText(permission, isSubscribed)}
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {permission === 'denied' ? (
          <Alert className="mb-4">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Notifications Blocked</AlertTitle>
            <AlertDescription>
              To enable push notifications, please update your browser settings to allow
              notifications from this site.
            </AlertDescription>
          </Alert>
        ) : (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-sm">
                {isSubscribed ? 'Enabled' : 'Disabled'}
              </span>
              {isSubscribed && (
                <Check className="h-4 w-4 text-green-500" />
              )}
            </div>
            <Switch
              checked={isSubscribed}
              onCheckedChange={handleToggle}
              disabled={isLoading || !isSupported || permission === 'denied'}
            />
          </div>
        )}

        {isLoading && (
          <div className="flex items-center gap-2 mt-4 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>{isSubscribed ? 'Disabling...' : 'Enabling...'}</span>
          </div>
        )}

        {!isSupported && (
          <p className="text-sm text-muted-foreground mt-4">
            Your browser does not support push notifications.
          </p>
        )}
      </CardContent>
    </Card>
  );
}

// ============================================================================
// Compact Variant
// ============================================================================

function PushNotificationCompact({
  className,
  onSubscriptionChange,
}: PushNotificationOptInProps) {
  const {
    isSupported,
    permission,
    isSubscribed,
    isLoading,
    subscribe,
    unsubscribe,
  } = usePushNotifications();

  const handleToggle = async () => {
    let success: boolean;
    if (isSubscribed) {
      success = await unsubscribe();
    } else {
      success = await subscribe();
    }
    if (success) {
      onSubscriptionChange?.(!isSubscribed);
    }
  };

  if (!isSupported || permission === 'denied') {
    return null;
  }

  return (
    <div className={cn('flex items-center justify-between py-2', className)}>
      <div className="flex items-center gap-2">
        {getPermissionIcon(permission, isSubscribed)}
        <span className="text-sm">Browser Push</span>
      </div>
      <Switch
        checked={isSubscribed}
        onCheckedChange={handleToggle}
        disabled={isLoading}
      />
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export function PushNotificationOptIn({
  variant = 'card',
  ...props
}: PushNotificationOptInProps) {
  switch (variant) {
    case 'banner':
      return <PushNotificationBanner {...props} />;
    case 'compact':
      return <PushNotificationCompact {...props} />;
    case 'card':
    default:
      return <PushNotificationCard {...props} />;
  }
}

export default PushNotificationOptIn;
