/**
 * =========================================================================
 * WebSocket Hook - Real-time Notifications
 * SDLC Orchestrator - Sprint 153 (Real-time Notifications)
 *
 * Version: 1.0.0
 * Date: February 3, 2026
 * Status: ACTIVE - Sprint 153 Day 1
 * Authority: Frontend Lead + CTO Approved
 * Framework: SDLC 6.0.5
 *
 * Purpose:
 * - Manage WebSocket connection lifecycle
 * - Handle real-time notification events
 * - Auto-reconnect on connection loss
 * - Integrate with React Query for cache invalidation
 *
 * Events:
 * - gate_approved: Gate approval notification
 * - evidence_uploaded: New evidence uploaded
 * - policy_violation: Policy violation detected
 * - comment_added: New comment on entity
 * - notification_created: Generic notification
 *
 * Zero Mock Policy: Production-ready WebSocket client
 * =========================================================================
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';

// ============================================================================
// Types
// ============================================================================

/**
 * WebSocket event types matching backend
 */
export enum WebSocketEventType {
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  PING = 'ping',
  PONG = 'pong',
  GATE_APPROVED = 'gate_approved',
  GATE_REJECTED = 'gate_rejected',
  GATE_APPROVAL_REQUIRED = 'gate_approval_required',
  EVIDENCE_UPLOADED = 'evidence_uploaded',
  POLICY_VIOLATION = 'policy_violation',
  COMMENT_ADDED = 'comment_added',
  NOTIFICATION_READ = 'notification_read',
  NOTIFICATION_CREATED = 'notification_created',
  PROJECT_UPDATED = 'project_updated',
  MEMBER_ADDED = 'member_added',
  MEMBER_REMOVED = 'member_removed',
  VCR_CREATED = 'vcr_created',
  VCR_UPDATED = 'vcr_updated',
  MRP_VALIDATED = 'mrp_validated',
  CONTEXT_SNAPSHOT_CREATED = 'context_snapshot_created',
  TEMPLATE_UPDATED = 'template_updated',
}

/**
 * WebSocket event from server
 */
export interface WebSocketEvent {
  event_type: WebSocketEventType;
  payload: Record<string, unknown>;
  timestamp: string;
  project_id?: string;
  user_id?: string;
}

/**
 * WebSocket connection state
 */
export type WebSocketStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

/**
 * WebSocket hook options
 */
export interface UseWebSocketOptions {
  /** JWT access token for authentication */
  token?: string;
  /** Project IDs to subscribe to */
  projectIds?: string[];
  /** Enable auto-reconnect (default: true) */
  autoReconnect?: boolean;
  /** Reconnect delay in ms (default: 3000) */
  reconnectDelay?: number;
  /** Max reconnect attempts (default: 5) */
  maxReconnectAttempts?: number;
  /** Ping interval in ms (default: 30000) */
  pingInterval?: number;
  /** Callback when event received */
  onEvent?: (event: WebSocketEvent) => void;
  /** Callback when connected */
  onConnect?: () => void;
  /** Callback when disconnected */
  onDisconnect?: () => void;
  /** Callback when error occurs */
  onError?: (error: Event) => void;
}

/**
 * WebSocket hook return type
 */
export interface UseWebSocketReturn {
  /** Current connection status */
  status: WebSocketStatus;
  /** Whether connected */
  isConnected: boolean;
  /** Last received event */
  lastEvent: WebSocketEvent | null;
  /** All received events (limited buffer) */
  events: WebSocketEvent[];
  /** Unread notification count */
  unreadCount: number;
  /** Subscribe to a project */
  subscribe: (projectId: string) => void;
  /** Unsubscribe from a project */
  unsubscribe: (projectId: string) => void;
  /** Send ping to check connection */
  ping: () => void;
  /** Manually disconnect */
  disconnect: () => void;
  /** Manually reconnect */
  reconnect: () => void;
  /** Clear event buffer */
  clearEvents: () => void;
}

// ============================================================================
// Hook Implementation
// ============================================================================

const MAX_EVENT_BUFFER = 100;
const DEFAULT_RECONNECT_DELAY = 3000;
const DEFAULT_MAX_RECONNECT_ATTEMPTS = 5;
const DEFAULT_PING_INTERVAL = 30000;

/**
 * Hook for WebSocket real-time notifications
 *
 * @example
 * ```tsx
 * const { status, events, unreadCount, subscribe } = useWebSocket({
 *   token: accessToken,
 *   projectIds: [currentProjectId],
 *   onEvent: (event) => {
 *     if (event.event_type === WebSocketEventType.GATE_APPROVED) {
 *       toast.success('Gate approved!');
 *     }
 *   },
 * });
 * ```
 */
export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const {
    token,
    projectIds = [],
    autoReconnect = true,
    reconnectDelay = DEFAULT_RECONNECT_DELAY,
    maxReconnectAttempts = DEFAULT_MAX_RECONNECT_ATTEMPTS,
    pingInterval = DEFAULT_PING_INTERVAL,
    onEvent,
    onConnect,
    onDisconnect,
    onError,
  } = options;

  const queryClient = useQueryClient();

  // State
  const [status, setStatus] = useState<WebSocketStatus>('disconnected');
  const [lastEvent, setLastEvent] = useState<WebSocketEvent | null>(null);
  const [events, setEvents] = useState<WebSocketEvent[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);

  // Refs
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Build WebSocket URL
  const getWebSocketUrl = useCallback(() => {
    if (!token) return null;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = process.env.NEXT_PUBLIC_API_URL?.replace(/^https?:\/\//, '') || window.location.host;

    let url = `${protocol}//${host}/ws/notifications?token=${encodeURIComponent(token)}`;

    if (projectIds.length > 0) {
      url += `&project_ids=${projectIds.join(',')}`;
    }

    return url;
  }, [token, projectIds]);

  // Handle incoming message
  const handleMessage = useCallback(
    (messageEvent: MessageEvent) => {
      try {
        const event: WebSocketEvent = JSON.parse(messageEvent.data);

        // Update last event
        setLastEvent(event);

        // Add to event buffer (limited size)
        setEvents((prev) => {
          const newEvents = [event, ...prev].slice(0, MAX_EVENT_BUFFER);
          return newEvents;
        });

        // Handle specific event types
        switch (event.event_type) {
          case WebSocketEventType.CONNECTED:
            setStatus('connected');
            reconnectAttempts.current = 0;
            onConnect?.();
            break;

          case WebSocketEventType.PONG:
            // Ping acknowledged
            break;

          case WebSocketEventType.NOTIFICATION_CREATED:
          case WebSocketEventType.EVIDENCE_UPLOADED:
          case WebSocketEventType.POLICY_VIOLATION:
            // Increment unread count
            setUnreadCount((prev) => prev + 1);
            // Invalidate notifications query
            queryClient.invalidateQueries({ queryKey: ['notifications'] });
            break;

          case WebSocketEventType.GATE_APPROVED:
          case WebSocketEventType.GATE_REJECTED:
          case WebSocketEventType.GATE_APPROVAL_REQUIRED:
            // Increment unread count
            setUnreadCount((prev) => prev + 1);
            // Invalidate notifications query
            queryClient.invalidateQueries({ queryKey: ['notifications'] });
            // Invalidate gates queries (Sprint 153 - real-time gate updates)
            queryClient.invalidateQueries({ queryKey: ['gates'] });
            // Invalidate specific project gates if project_id available
            if (event.project_id) {
              queryClient.invalidateQueries({ queryKey: ['gates', event.project_id] });
              queryClient.invalidateQueries({ queryKey: ['project', event.project_id] });
            }
            break;

          case WebSocketEventType.NOTIFICATION_READ:
            // Decrement unread count
            setUnreadCount((prev) => Math.max(0, prev - 1));
            break;

          case WebSocketEventType.PROJECT_UPDATED:
            // Invalidate project query
            if (event.project_id) {
              queryClient.invalidateQueries({ queryKey: ['project', event.project_id] });
            }
            break;

          case WebSocketEventType.VCR_CREATED:
          case WebSocketEventType.VCR_UPDATED:
            // Invalidate VCR queries
            queryClient.invalidateQueries({ queryKey: ['vcr'] });
            break;

          case WebSocketEventType.MRP_VALIDATED:
            // Invalidate MRP queries
            queryClient.invalidateQueries({ queryKey: ['mrp'] });
            break;

          case WebSocketEventType.CONTEXT_SNAPSHOT_CREATED:
          case WebSocketEventType.TEMPLATE_UPDATED:
            // Invalidate Context Authority queries
            queryClient.invalidateQueries({ queryKey: ['contextAuthority'] });
            break;
        }

        // Call custom event handler
        onEvent?.(event);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    },
    [onConnect, onEvent, queryClient]
  );

  // Connect to WebSocket
  const connect = useCallback(() => {
    const url = getWebSocketUrl();
    if (!url) {
      console.warn('WebSocket: No token provided, skipping connection');
      return;
    }

    // Close existing connection
    if (wsRef.current) {
      wsRef.current.close();
    }

    setStatus('connecting');

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        // Status will be set to 'connected' when we receive the CONNECTED event
      };

      ws.onmessage = handleMessage;

      ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        setStatus('disconnected');
        wsRef.current = null;
        onDisconnect?.();

        // Auto-reconnect if enabled and not intentional close
        if (autoReconnect && event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current += 1;
          console.log(`WebSocket reconnecting (attempt ${reconnectAttempts.current}/${maxReconnectAttempts})...`);
          reconnectTimeout.current = setTimeout(connect, reconnectDelay);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setStatus('error');
        onError?.(error);
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      setStatus('error');
    }
  }, [getWebSocketUrl, handleMessage, autoReconnect, maxReconnectAttempts, reconnectDelay, onDisconnect, onError]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    // Clear reconnect timeout
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
      reconnectTimeout.current = null;
    }

    // Clear ping interval
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }

    // Close WebSocket
    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnected');
      wsRef.current = null;
    }

    setStatus('disconnected');
  }, []);

  // Send message to server
  const sendMessage = useCallback((message: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  // Subscribe to project
  const subscribe = useCallback(
    (projectId: string) => {
      sendMessage({ action: 'subscribe', project_id: projectId });
    },
    [sendMessage]
  );

  // Unsubscribe from project
  const unsubscribe = useCallback(
    (projectId: string) => {
      sendMessage({ action: 'unsubscribe', project_id: projectId });
    },
    [sendMessage]
  );

  // Ping server
  const ping = useCallback(() => {
    sendMessage({ action: 'ping' });
  }, [sendMessage]);

  // Reconnect
  const reconnect = useCallback(() => {
    disconnect();
    reconnectAttempts.current = 0;
    connect();
  }, [disconnect, connect]);

  // Clear events
  const clearEvents = useCallback(() => {
    setEvents([]);
    setLastEvent(null);
    setUnreadCount(0);
  }, []);

  // Connect on mount and when token changes
  useEffect(() => {
    if (token) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [token]); // eslint-disable-line react-hooks/exhaustive-deps

  // Setup ping interval when connected
  useEffect(() => {
    if (status === 'connected' && pingInterval > 0) {
      pingIntervalRef.current = setInterval(ping, pingInterval);
    }

    return () => {
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
        pingIntervalRef.current = null;
      }
    };
  }, [status, pingInterval, ping]);

  return {
    status,
    isConnected: status === 'connected',
    lastEvent,
    events,
    unreadCount,
    subscribe,
    unsubscribe,
    ping,
    disconnect,
    reconnect,
    clearEvents,
  };
}

// ============================================================================
// Utility Hooks
// ============================================================================

/**
 * Hook to listen for specific WebSocket event types
 *
 * @example
 * ```tsx
 * useWebSocketEvent(WebSocketEventType.GATE_APPROVED, (event) => {
 *   toast.success(`Gate ${event.payload.gate_code} approved!`);
 * });
 * ```
 */
export function useWebSocketEvent(
  eventType: WebSocketEventType,
  callback: (event: WebSocketEvent) => void,
  deps: unknown[] = []
) {
  const callbackRef = useRef(callback);
  callbackRef.current = callback;

  return useCallback(
    (event: WebSocketEvent) => {
      if (event.event_type === eventType) {
        callbackRef.current(event);
      }
    },
    [eventType, ...deps] // eslint-disable-line react-hooks/exhaustive-deps
  );
}

export default useWebSocket;
