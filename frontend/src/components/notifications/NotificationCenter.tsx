/**
 * =========================================================================
 * Notification Center Component - Real-time Notifications UI
 * SDLC Orchestrator - Sprint 153 (Real-time Notifications)
 *
 * Version: 1.0.0
 * Date: February 3, 2026
 * Status: ACTIVE - Sprint 153 Day 1
 * Authority: Frontend Lead + CTO Approved
 * Framework: SDLC 6.0.5
 *
 * Purpose:
 * - Display notification bell icon with unread count
 * - Dropdown panel with notification list
 * - Real-time updates via WebSocket
 * - Mark as read functionality
 *
 * Zero Mock Policy: Production-ready notification UI
 * =========================================================================
 */

'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { formatDistanceToNow } from 'date-fns';
import {
  Bell,
  Check,
  CheckCheck,
  AlertTriangle,
  Shield,
  FileCheck,
  Users,
  GitPullRequest,
  X,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';
import { api } from '@/lib/api';
import { useWebSocket, WebSocketEventType, type WebSocketEvent } from '@/hooks/useWebSocket';
import { useToast } from '@/components/ui/use-toast';

// ============================================================================
// Types
// ============================================================================

interface Notification {
  id: string;
  notification_type: string;
  title: string;
  message: string;
  priority: 'critical' | 'high' | 'medium' | 'low';
  project_id?: string;
  is_read: boolean;
  created_at: string;
  metadata?: Record<string, unknown>;
}

interface NotificationListResponse {
  notifications: Notification[];
  total: number;
  unread_count: number;
  page: number;
  page_size: number;
}

// ============================================================================
// API Functions
// ============================================================================

const notificationKeys = {
  all: ['notifications'] as const,
  list: (params?: { unread_only?: boolean }) =>
    [...notificationKeys.all, 'list', params] as const,
  stats: () => [...notificationKeys.all, 'stats'] as const,
};

async function fetchNotifications(unreadOnly = false): Promise<NotificationListResponse> {
  const response = await api.get('/notifications', {
    params: { unread_only: unreadOnly, page_size: 20 },
  });
  return response.data;
}

async function markAsRead(notificationId: string): Promise<void> {
  await api.put(`/notifications/${notificationId}/read`);
}

async function markAllAsRead(): Promise<void> {
  await api.put('/notifications/read-all');
}

// ============================================================================
// Helper Functions
// ============================================================================

function getNotificationIcon(type: string) {
  switch (type) {
    case 'gate_approved':
      return <Check className="h-4 w-4 text-green-500" />;
    case 'gate_rejected':
      return <X className="h-4 w-4 text-red-500" />;
    case 'gate_approval_required':
      return <GitPullRequest className="h-4 w-4 text-blue-500" />;
    case 'compliance_violation':
    case 'policy_violation':
      return <AlertTriangle className="h-4 w-4 text-orange-500" />;
    case 'evidence_uploaded':
      return <FileCheck className="h-4 w-4 text-purple-500" />;
    case 'member_invited':
    case 'member_added':
      return <Users className="h-4 w-4 text-cyan-500" />;
    case 'scan_completed':
      return <Shield className="h-4 w-4 text-teal-500" />;
    default:
      return <Bell className="h-4 w-4 text-gray-500" />;
  }
}

function getPriorityColor(priority: string) {
  switch (priority) {
    case 'critical':
      return 'bg-red-500';
    case 'high':
      return 'bg-orange-500';
    case 'medium':
      return 'bg-yellow-500';
    case 'low':
      return 'bg-green-500';
    default:
      return 'bg-gray-500';
  }
}

// ============================================================================
// Notification Item Component
// ============================================================================

interface NotificationItemProps {
  notification: Notification;
  onMarkAsRead: (id: string) => void;
}

function NotificationItem({ notification, onMarkAsRead }: NotificationItemProps) {
  return (
    <div
      className={cn(
        'flex items-start gap-3 p-3 hover:bg-muted/50 cursor-pointer transition-colors',
        !notification.is_read && 'bg-blue-50 dark:bg-blue-950/20'
      )}
      onClick={() => !notification.is_read && onMarkAsRead(notification.id)}
    >
      <div className="flex-shrink-0 mt-0.5">
        {getNotificationIcon(notification.notification_type)}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <p className={cn(
            'text-sm font-medium truncate',
            !notification.is_read && 'font-semibold'
          )}>
            {notification.title}
          </p>
          <div className="flex items-center gap-1.5 flex-shrink-0">
            <div
              className={cn(
                'h-2 w-2 rounded-full',
                getPriorityColor(notification.priority)
              )}
              title={`${notification.priority} priority`}
            />
            {!notification.is_read && (
              <div className="h-2 w-2 rounded-full bg-blue-500" />
            )}
          </div>
        </div>
        <p className="text-xs text-muted-foreground line-clamp-2 mt-0.5">
          {notification.message}
        </p>
        <p className="text-xs text-muted-foreground mt-1">
          {formatDistanceToNow(new Date(notification.created_at), { addSuffix: true })}
        </p>
      </div>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

interface NotificationCenterProps {
  /** JWT token for WebSocket authentication */
  token?: string;
  /** Project IDs to subscribe for real-time updates */
  projectIds?: string[];
}

export function NotificationCenter({ token, projectIds }: NotificationCenterProps) {
  const [isOpen, setIsOpen] = useState(false);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  // Fetch notifications
  const {
    data: notificationData,
    isLoading,
    refetch,
  } = useQuery({
    queryKey: notificationKeys.list({ unread_only: false }),
    queryFn: () => fetchNotifications(false),
    refetchInterval: 60000, // Refetch every minute as fallback
  });

  // Mark as read mutation
  const markAsReadMutation = useMutation({
    mutationFn: markAsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: notificationKeys.all });
    },
  });

  // Mark all as read mutation
  const markAllAsReadMutation = useMutation({
    mutationFn: markAllAsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: notificationKeys.all });
      toast({
        title: 'All notifications marked as read',
        duration: 2000,
      });
    },
  });

  // WebSocket for real-time updates
  const { unreadCount: wsUnreadCount } = useWebSocket({
    token,
    projectIds,
    onEvent: (event: WebSocketEvent) => {
      // Show toast for important events
      switch (event.event_type) {
        case WebSocketEventType.GATE_APPROVED:
          toast({
            title: 'Gate Approved',
            description: event.payload.title as string || 'A gate has been approved',
            duration: 5000,
          });
          break;
        case WebSocketEventType.GATE_REJECTED:
          toast({
            title: 'Gate Rejected',
            description: event.payload.title as string || 'A gate has been rejected',
            variant: 'destructive',
            duration: 5000,
          });
          break;
        case WebSocketEventType.POLICY_VIOLATION:
          toast({
            title: 'Policy Violation',
            description: event.payload.title as string || 'A policy violation was detected',
            variant: 'destructive',
            duration: 5000,
          });
          break;
        case WebSocketEventType.NOTIFICATION_CREATED:
          // Refetch notifications on new notification
          refetch();
          break;
      }
    },
  });

  const notifications = notificationData?.notifications || [];
  const unreadCount = notificationData?.unread_count || wsUnreadCount;

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <Badge
              variant="destructive"
              className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center p-0 text-xs"
            >
              {unreadCount > 99 ? '99+' : unreadCount}
            </Badge>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-96 p-0" align="end">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b">
          <h3 className="font-semibold">Notifications</h3>
          {unreadCount > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => markAllAsReadMutation.mutate()}
              disabled={markAllAsReadMutation.isPending}
            >
              <CheckCheck className="h-4 w-4 mr-1" />
              Mark all read
            </Button>
          )}
        </div>

        {/* Notification List */}
        <ScrollArea className="h-[400px]">
          {isLoading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary" />
            </div>
          ) : notifications.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-32 text-muted-foreground">
              <Bell className="h-8 w-8 mb-2 opacity-50" />
              <p className="text-sm">No notifications yet</p>
            </div>
          ) : (
            <div className="divide-y">
              {notifications.map((notification) => (
                <NotificationItem
                  key={notification.id}
                  notification={notification}
                  onMarkAsRead={(id) => markAsReadMutation.mutate(id)}
                />
              ))}
            </div>
          )}
        </ScrollArea>

        {/* Footer */}
        <Separator />
        <div className="p-2">
          <Button
            variant="ghost"
            size="sm"
            className="w-full"
            onClick={() => {
              setIsOpen(false);
              // Navigate to notifications page if exists
              window.location.href = '/app/notifications';
            }}
          >
            View all notifications
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  );
}

export default NotificationCenter;
