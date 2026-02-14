/**
 * =========================================================================
 * Notifications Page - Full Notification Management
 * SDLC Orchestrator - Sprint 153 (Real-time Notifications)
 *
 * Version: 1.0.0
 * Date: February 4, 2026
 * Status: ACTIVE - Sprint 153 Day 3
 * Authority: Frontend Lead + CTO Approved
 * Framework: SDLC 6.0.5
 *
 * Purpose:
 * - Full notification list with filtering
 * - Pagination support
 * - Mark as read (individual and bulk)
 * - Real-time updates via WebSocket
 *
 * Zero Mock Policy: Production-ready notification page
 * =========================================================================
 */

'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { formatDistanceToNow, format } from 'date-fns';
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
  Filter,
  ChevronLeft,
  ChevronRight,
  Settings,
  Inbox,
  Archive,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Checkbox } from '@/components/ui/checkbox';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';
import { api } from '@/lib/api';
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
  project_name?: string;
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

type NotificationFilter = 'all' | 'unread' | 'read';
type NotificationTypeFilter = 'all' | 'gates' | 'evidence' | 'violations' | 'team';
type PriorityFilter = 'all' | 'critical' | 'high' | 'medium' | 'low';

// ============================================================================
// API Functions
// ============================================================================

const notificationKeys = {
  all: ['notifications'] as const,
  list: (params: {
    filter?: NotificationFilter;
    type?: NotificationTypeFilter;
    priority?: PriorityFilter;
    page?: number;
    page_size?: number;
  }) => [...notificationKeys.all, 'list', params] as const,
  stats: () => [...notificationKeys.all, 'stats'] as const,
};

interface FetchParams {
  filter: NotificationFilter;
  type: NotificationTypeFilter;
  priority: PriorityFilter;
  page: number;
  pageSize: number;
}

async function fetchNotifications(params: FetchParams): Promise<NotificationListResponse> {
  const queryParams: Record<string, string | number | boolean> = {
    page: params.page,
    page_size: params.pageSize,
  };

  if (params.filter === 'unread') {
    queryParams.unread_only = true;
  } else if (params.filter === 'read') {
    queryParams.read_only = true;
  }

  if (params.type !== 'all') {
    queryParams.type_filter = params.type;
  }

  if (params.priority !== 'all') {
    queryParams.priority = params.priority;
  }

  const response = await api.get('/notifications', { params: queryParams });
  return response.data;
}

async function markAsRead(notificationId: string): Promise<void> {
  await api.put(`/notifications/${notificationId}/read`);
}

async function markAllAsRead(): Promise<void> {
  await api.put('/notifications/read-all');
}

async function markMultipleAsRead(notificationIds: string[]): Promise<void> {
  await api.put('/notifications/read-batch', { notification_ids: notificationIds });
}

// ============================================================================
// Helper Functions
// ============================================================================

function getNotificationIcon(type: string) {
  switch (type) {
    case 'gate_approved':
      return <Check className="h-5 w-5 text-green-500" />;
    case 'gate_rejected':
      return <X className="h-5 w-5 text-red-500" />;
    case 'gate_approval_required':
      return <GitPullRequest className="h-5 w-5 text-blue-500" />;
    case 'compliance_violation':
    case 'policy_violation':
      return <AlertTriangle className="h-5 w-5 text-orange-500" />;
    case 'evidence_uploaded':
      return <FileCheck className="h-5 w-5 text-purple-500" />;
    case 'member_invited':
    case 'member_added':
    case 'member_removed':
      return <Users className="h-5 w-5 text-cyan-500" />;
    case 'scan_completed':
      return <Shield className="h-5 w-5 text-teal-500" />;
    default:
      return <Bell className="h-5 w-5 text-gray-500" />;
  }
}

function getPriorityBadge(priority: string) {
  switch (priority) {
    case 'critical':
      return <Badge variant="destructive">Critical</Badge>;
    case 'high':
      return <Badge className="bg-orange-500 hover:bg-orange-600">High</Badge>;
    case 'medium':
      return <Badge className="bg-yellow-500 hover:bg-yellow-600 text-black">Medium</Badge>;
    case 'low':
      return <Badge variant="secondary">Low</Badge>;
    default:
      return <Badge variant="outline">{priority}</Badge>;
  }
}

function getTypeLabel(type: string): string {
  switch (type) {
    case 'gate_approved':
      return 'Gate Approved';
    case 'gate_rejected':
      return 'Gate Rejected';
    case 'gate_approval_required':
      return 'Approval Required';
    case 'policy_violation':
    case 'compliance_violation':
      return 'Policy Violation';
    case 'evidence_uploaded':
      return 'Evidence Uploaded';
    case 'member_added':
      return 'Member Added';
    case 'member_removed':
      return 'Member Removed';
    case 'member_invited':
      return 'Member Invited';
    case 'scan_completed':
      return 'Scan Completed';
    default:
      return type.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
  }
}

// ============================================================================
// Notification Row Component
// ============================================================================

interface NotificationRowProps {
  notification: Notification;
  selected: boolean;
  onSelect: (selected: boolean) => void;
  onMarkAsRead: (id: string) => void;
}

function NotificationRow({
  notification,
  selected,
  onSelect,
  onMarkAsRead,
}: NotificationRowProps) {
  return (
    <div
      className={cn(
        'flex items-start gap-4 p-4 hover:bg-muted/50 transition-colors border-b',
        !notification.is_read && 'bg-blue-50/50 dark:bg-blue-950/20'
      )}
    >
      <Checkbox
        checked={selected}
        onCheckedChange={onSelect}
        className="mt-1"
      />
      <div className="flex-shrink-0 mt-1">
        {getNotificationIcon(notification.notification_type)}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <h4
                className={cn(
                  'text-sm font-medium',
                  !notification.is_read && 'font-semibold'
                )}
              >
                {notification.title}
              </h4>
              {!notification.is_read && (
                <div className="h-2 w-2 rounded-full bg-blue-500" />
              )}
            </div>
            <p className="text-sm text-muted-foreground line-clamp-2">
              {notification.message}
            </p>
            <div className="flex items-center gap-3 mt-2">
              <span className="text-xs text-muted-foreground">
                {getTypeLabel(notification.notification_type)}
              </span>
              {notification.project_name && (
                <>
                  <span className="text-xs text-muted-foreground">•</span>
                  <span className="text-xs text-muted-foreground">
                    {notification.project_name}
                  </span>
                </>
              )}
              <span className="text-xs text-muted-foreground">•</span>
              <span className="text-xs text-muted-foreground">
                {formatDistanceToNow(new Date(notification.created_at), {
                  addSuffix: true,
                })}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {getPriorityBadge(notification.priority)}
            {!notification.is_read && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onMarkAsRead(notification.id)}
                className="h-8"
              >
                <Check className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Main Page Component
// ============================================================================

export default function NotificationsPage() {
  const [filter, setFilter] = useState<NotificationFilter>('all');
  const [typeFilter, setTypeFilter] = useState<NotificationTypeFilter>('all');
  const [priorityFilter, setPriorityFilter] = useState<PriorityFilter>('all');
  const [page, setPage] = useState(1);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const pageSize = 20;

  const queryClient = useQueryClient();
  const { toast } = useToast();

  // Fetch notifications
  const { data, isLoading, isFetching } = useQuery({
    queryKey: notificationKeys.list({
      filter,
      type: typeFilter,
      priority: priorityFilter,
      page,
      page_size: pageSize,
    }),
    queryFn: () =>
      fetchNotifications({
        filter,
        type: typeFilter,
        priority: priorityFilter,
        page,
        pageSize,
      }),
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

  // Mark selected as read mutation
  const markSelectedAsReadMutation = useMutation({
    mutationFn: markMultipleAsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: notificationKeys.all });
      setSelectedIds(new Set());
      toast({
        title: `${selectedIds.size} notifications marked as read`,
        duration: 2000,
      });
    },
  });

  const notifications = data?.notifications || [];
  const total = data?.total || 0;
  const unreadCount = data?.unread_count || 0;
  const totalPages = Math.ceil(total / pageSize);

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedIds(new Set(notifications.map((n) => n.id)));
    } else {
      setSelectedIds(new Set());
    }
  };

  const handleSelect = (id: string, checked: boolean) => {
    const newSet = new Set(selectedIds);
    if (checked) {
      newSet.add(id);
    } else {
      newSet.delete(id);
    }
    setSelectedIds(newSet);
  };

  const allSelected =
    notifications.length > 0 && notifications.every((n) => selectedIds.has(n.id));

  return (
    <div className="container mx-auto py-6 max-w-6xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Notifications</h1>
          <p className="text-muted-foreground">
            {unreadCount > 0
              ? `You have ${unreadCount} unread notification${unreadCount > 1 ? 's' : ''}`
              : 'All caught up!'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" asChild>
            <a href="/app/settings/notifications">
              <Settings className="h-4 w-4 mr-2" />
              Settings
            </a>
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader className="pb-3">
          {/* Filters */}
          <div className="flex items-center justify-between">
            <Tabs
              value={filter}
              onValueChange={(v) => {
                setFilter(v as NotificationFilter);
                setPage(1);
              }}
            >
              <TabsList>
                <TabsTrigger value="all" className="gap-2">
                  <Inbox className="h-4 w-4" />
                  All
                </TabsTrigger>
                <TabsTrigger value="unread" className="gap-2">
                  <Bell className="h-4 w-4" />
                  Unread
                  {unreadCount > 0 && (
                    <Badge variant="secondary" className="ml-1">
                      {unreadCount}
                    </Badge>
                  )}
                </TabsTrigger>
                <TabsTrigger value="read" className="gap-2">
                  <Archive className="h-4 w-4" />
                  Read
                </TabsTrigger>
              </TabsList>
            </Tabs>

            <div className="flex items-center gap-2">
              <Select
                value={typeFilter}
                onValueChange={(v) => {
                  setTypeFilter(v as NotificationTypeFilter);
                  setPage(1);
                }}
              >
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="gates">Gates</SelectItem>
                  <SelectItem value="evidence">Evidence</SelectItem>
                  <SelectItem value="violations">Violations</SelectItem>
                  <SelectItem value="team">Team</SelectItem>
                </SelectContent>
              </Select>

              <Select
                value={priorityFilter}
                onValueChange={(v) => {
                  setPriorityFilter(v as PriorityFilter);
                  setPage(1);
                }}
              >
                <SelectTrigger className="w-[130px]">
                  <SelectValue placeholder="Priority" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Priority</SelectItem>
                  <SelectItem value="critical">Critical</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="low">Low</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>

        <Separator />

        {/* Bulk Actions */}
        {selectedIds.size > 0 && (
          <div className="flex items-center gap-4 px-4 py-2 bg-muted/50">
            <span className="text-sm text-muted-foreground">
              {selectedIds.size} selected
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() =>
                markSelectedAsReadMutation.mutate(Array.from(selectedIds))
              }
              disabled={markSelectedAsReadMutation.isPending}
            >
              <CheckCheck className="h-4 w-4 mr-1" />
              Mark as read
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSelectedIds(new Set())}
            >
              Clear selection
            </Button>
          </div>
        )}

        {/* Header Row */}
        <div className="flex items-center gap-4 px-4 py-2 border-b bg-muted/30">
          <Checkbox
            checked={allSelected}
            onCheckedChange={handleSelectAll}
          />
          <div className="flex-1 flex items-center justify-between">
            <span className="text-sm font-medium">
              {total} notification{total !== 1 ? 's' : ''}
            </span>
            {unreadCount > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => markAllAsReadMutation.mutate()}
                disabled={markAllAsReadMutation.isPending}
              >
                <CheckCheck className="h-4 w-4 mr-1" />
                Mark all as read
              </Button>
            )}
          </div>
        </div>

        <CardContent className="p-0">
          {/* Loading State */}
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
            </div>
          ) : notifications.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
              <Bell className="h-12 w-12 mb-4 opacity-50" />
              <p className="text-lg font-medium">No notifications</p>
              <p className="text-sm">
                {filter === 'unread'
                  ? 'All caught up!'
                  : 'No notifications match your filters'}
              </p>
            </div>
          ) : (
            <>
              {/* Notification List */}
              <div className={cn(isFetching && 'opacity-50')}>
                {notifications.map((notification) => (
                  <NotificationRow
                    key={notification.id}
                    notification={notification}
                    selected={selectedIds.has(notification.id)}
                    onSelect={(checked) => handleSelect(notification.id, checked)}
                    onMarkAsRead={(id) => markAsReadMutation.mutate(id)}
                  />
                ))}
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between px-4 py-3 border-t">
                  <p className="text-sm text-muted-foreground">
                    Showing {(page - 1) * pageSize + 1} to{' '}
                    {Math.min(page * pageSize, total)} of {total}
                  </p>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={page === 1}
                    >
                      <ChevronLeft className="h-4 w-4 mr-1" />
                      Previous
                    </Button>
                    <span className="text-sm text-muted-foreground px-2">
                      Page {page} of {totalPages}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                      disabled={page === totalPages}
                    >
                      Next
                      <ChevronRight className="h-4 w-4 ml-1" />
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
