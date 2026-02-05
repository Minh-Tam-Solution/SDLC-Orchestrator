/**
 * =========================================================================
 * Push Notifications Hook
 * SDLC Orchestrator - Sprint 153 (Real-time Notifications)
 *
 * Version: 1.0.0
 * Date: February 4, 2026
 * Status: ACTIVE - Sprint 153 Day 4
 * Authority: Frontend Lead + CTO Approved
 * Framework: SDLC 6.0.3
 *
 * Purpose:
 * - Manage push notification permissions
 * - Register/unregister service worker
 * - Handle push subscriptions
 * - Sync subscription with backend
 *
 * Zero Mock Policy: Production-ready push notification management
 * =========================================================================
 */

import { useCallback, useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

// ============================================================================
// Types
// ============================================================================

export type PushPermissionState = 'default' | 'granted' | 'denied' | 'unsupported';

export interface PushSubscriptionState {
  isSupported: boolean;
  permission: PushPermissionState;
  isSubscribed: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface UsePushNotificationsReturn extends PushSubscriptionState {
  subscribe: () => Promise<boolean>;
  unsubscribe: () => Promise<boolean>;
  requestPermission: () => Promise<PushPermissionState>;
  checkSubscription: () => Promise<boolean>;
}

interface VapidKeyResponse {
  public_key: string;
}

interface SubscriptionResponse {
  success: boolean;
  subscription_id?: string;
}

// ============================================================================
// API Functions
// ============================================================================

async function getVapidPublicKey(): Promise<string> {
  const response = await api.get<VapidKeyResponse>('/push/vapid-key');
  return response.data.public_key;
}

async function saveSubscription(subscription: PushSubscription): Promise<SubscriptionResponse> {
  const response = await api.post<SubscriptionResponse>('/push/subscribe', {
    subscription: subscription.toJSON(),
    user_agent: navigator.userAgent,
    platform: navigator.platform,
  });
  return response.data;
}

async function removeSubscription(endpoint: string): Promise<void> {
  await api.post('/push/unsubscribe', { endpoint });
}

async function checkServerSubscription(): Promise<boolean> {
  try {
    const response = await api.get<{ is_subscribed: boolean }>('/push/status');
    return response.data.is_subscribed;
  } catch {
    return false;
  }
}

// ============================================================================
// Helper Functions
// ============================================================================

function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

function isPushSupported(): boolean {
  return (
    typeof window !== 'undefined' &&
    'serviceWorker' in navigator &&
    'PushManager' in window &&
    'Notification' in window
  );
}

async function registerServiceWorker(): Promise<ServiceWorkerRegistration | null> {
  if (!('serviceWorker' in navigator)) {
    return null;
  }

  try {
    const registration = await navigator.serviceWorker.register('/sw-push.js', {
      scope: '/',
    });

    // Wait for the service worker to be ready
    await navigator.serviceWorker.ready;

    console.log('[Push] Service worker registered:', registration.scope);
    return registration;
  } catch (error) {
    console.error('[Push] Service worker registration failed:', error);
    return null;
  }
}

async function getRegistration(): Promise<ServiceWorkerRegistration | null> {
  if (!('serviceWorker' in navigator)) {
    return null;
  }

  try {
    const registration = await navigator.serviceWorker.getRegistration('/');
    return registration || null;
  } catch {
    return null;
  }
}

// ============================================================================
// Hook Implementation
// ============================================================================

export function usePushNotifications(): UsePushNotificationsReturn {
  const [state, setState] = useState<PushSubscriptionState>({
    isSupported: false,
    permission: 'default',
    isSubscribed: false,
    isLoading: true,
    error: null,
  });

  const queryClient = useQueryClient();

  // Fetch VAPID public key
  const { data: vapidKey } = useQuery({
    queryKey: ['push', 'vapid-key'],
    queryFn: getVapidPublicKey,
    enabled: state.isSupported,
    staleTime: Infinity, // VAPID key doesn't change
  });

  // Save subscription mutation
  const saveMutation = useMutation({
    mutationFn: saveSubscription,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['push', 'status'] });
    },
  });

  // Remove subscription mutation
  const removeMutation = useMutation({
    mutationFn: removeSubscription,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['push', 'status'] });
    },
  });

  // Initialize state on mount
  useEffect(() => {
    const initializeState = async () => {
      const supported = isPushSupported();

      if (!supported) {
        setState((prev) => ({
          ...prev,
          isSupported: false,
          permission: 'unsupported',
          isLoading: false,
        }));
        return;
      }

      // Get current permission state
      const permission = Notification.permission as PushPermissionState;

      // Check if already subscribed
      const registration = await getRegistration();
      let isSubscribed = false;

      if (registration) {
        try {
          const subscription = await registration.pushManager.getSubscription();
          isSubscribed = subscription !== null;
        } catch {
          isSubscribed = false;
        }
      }

      setState({
        isSupported: true,
        permission,
        isSubscribed,
        isLoading: false,
        error: null,
      });
    };

    initializeState();
  }, []);

  // Request notification permission
  const requestPermission = useCallback(async (): Promise<PushPermissionState> => {
    if (!state.isSupported) {
      return 'unsupported';
    }

    try {
      const permission = await Notification.requestPermission();
      setState((prev) => ({
        ...prev,
        permission: permission as PushPermissionState,
      }));
      return permission as PushPermissionState;
    } catch (error) {
      console.error('[Push] Permission request failed:', error);
      return 'denied';
    }
  }, [state.isSupported]);

  // Subscribe to push notifications
  const subscribe = useCallback(async (): Promise<boolean> => {
    if (!state.isSupported || !vapidKey) {
      setState((prev) => ({
        ...prev,
        error: 'Push notifications not supported or VAPID key not available',
      }));
      return false;
    }

    setState((prev) => ({ ...prev, isLoading: true, error: null }));

    try {
      // Request permission if not granted
      let permission = state.permission;
      if (permission === 'default') {
        permission = await requestPermission();
      }

      if (permission !== 'granted') {
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: 'Permission denied for push notifications',
        }));
        return false;
      }

      // Register service worker
      let registration = await getRegistration();
      if (!registration) {
        registration = await registerServiceWorker();
      }

      if (!registration) {
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: 'Failed to register service worker',
        }));
        return false;
      }

      // Send VAPID key to service worker
      if (registration.active) {
        registration.active.postMessage({
          type: 'SET_VAPID_KEY',
          data: { key: vapidKey },
        });
      }

      // Subscribe to push manager
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(vapidKey),
      });

      // Save subscription to backend
      await saveMutation.mutateAsync(subscription);

      setState((prev) => ({
        ...prev,
        isSubscribed: true,
        isLoading: false,
        error: null,
      }));

      console.log('[Push] Successfully subscribed to push notifications');
      return true;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to subscribe';
      console.error('[Push] Subscription failed:', error);
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }));
      return false;
    }
  }, [state.isSupported, state.permission, vapidKey, requestPermission, saveMutation]);

  // Unsubscribe from push notifications
  const unsubscribe = useCallback(async (): Promise<boolean> => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }));

    try {
      const registration = await getRegistration();
      if (!registration) {
        setState((prev) => ({
          ...prev,
          isSubscribed: false,
          isLoading: false,
        }));
        return true;
      }

      const subscription = await registration.pushManager.getSubscription();
      if (subscription) {
        // Remove from backend
        await removeMutation.mutateAsync(subscription.endpoint);
        // Unsubscribe locally
        await subscription.unsubscribe();
      }

      setState((prev) => ({
        ...prev,
        isSubscribed: false,
        isLoading: false,
        error: null,
      }));

      console.log('[Push] Successfully unsubscribed from push notifications');
      return true;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to unsubscribe';
      console.error('[Push] Unsubscribe failed:', error);
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }));
      return false;
    }
  }, [removeMutation]);

  // Check current subscription status
  const checkSubscription = useCallback(async (): Promise<boolean> => {
    const registration = await getRegistration();
    if (!registration) {
      return false;
    }

    try {
      const subscription = await registration.pushManager.getSubscription();
      const isSubscribed = subscription !== null;
      setState((prev) => ({ ...prev, isSubscribed }));
      return isSubscribed;
    } catch {
      return false;
    }
  }, []);

  return {
    ...state,
    subscribe,
    unsubscribe,
    requestPermission,
    checkSubscription,
  };
}

export default usePushNotifications;
