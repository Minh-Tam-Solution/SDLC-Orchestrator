/**
 * =========================================================================
 * Push Notification Service Worker
 * SDLC Orchestrator - Sprint 153 (Real-time Notifications)
 *
 * Version: 1.0.0
 * Date: February 4, 2026
 * Status: ACTIVE - Sprint 153 Day 4
 * Authority: Frontend Lead + CTO Approved
 * Framework: SDLC 6.0.3
 *
 * Purpose:
 * - Handle push notification events from server
 * - Display native browser notifications
 * - Handle notification click actions
 * - Cache management for offline support
 *
 * Zero Mock Policy: Production-ready service worker
 * =========================================================================
 */

// Service Worker version for cache busting
const SW_VERSION = '1.0.0';
const CACHE_NAME = `sdlc-push-${SW_VERSION}`;

// ============================================================================
// Installation Event
// ============================================================================

self.addEventListener('install', (event) => {
  console.log('[SW Push] Installing service worker v' + SW_VERSION);

  // Skip waiting to activate immediately
  self.skipWaiting();
});

// ============================================================================
// Activation Event
// ============================================================================

self.addEventListener('activate', (event) => {
  console.log('[SW Push] Activating service worker v' + SW_VERSION);

  // Claim all clients immediately
  event.waitUntil(
    Promise.all([
      self.clients.claim(),
      // Clean up old caches
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((name) => name.startsWith('sdlc-push-') && name !== CACHE_NAME)
            .map((name) => caches.delete(name))
        );
      }),
    ])
  );
});

// ============================================================================
// Push Event - Handle incoming push notifications
// ============================================================================

self.addEventListener('push', (event) => {
  console.log('[SW Push] Push received');

  let data = {
    title: 'SDLC Orchestrator',
    body: 'You have a new notification',
    icon: '/icons/notification-icon.png',
    badge: '/icons/notification-badge.png',
    tag: 'sdlc-notification',
    data: {},
  };

  // Parse push data if available
  if (event.data) {
    try {
      const payload = event.data.json();
      data = {
        title: payload.title || data.title,
        body: payload.body || payload.message || data.body,
        icon: payload.icon || data.icon,
        badge: payload.badge || data.badge,
        tag: payload.tag || `sdlc-${payload.notification_type || 'notification'}-${Date.now()}`,
        data: {
          url: payload.url || payload.data?.url || '/app/notifications',
          notification_id: payload.notification_id || payload.data?.notification_id,
          notification_type: payload.notification_type || payload.data?.notification_type,
          project_id: payload.project_id || payload.data?.project_id,
          ...payload.data,
        },
      };
    } catch (e) {
      console.error('[SW Push] Failed to parse push data:', e);
      data.body = event.data.text();
    }
  }

  // Notification options
  const options = {
    body: data.body,
    icon: data.icon,
    badge: data.badge,
    tag: data.tag,
    data: data.data,
    requireInteraction: isPriorityNotification(data.data?.notification_type),
    actions: getNotificationActions(data.data?.notification_type),
    vibrate: [100, 50, 100],
    timestamp: Date.now(),
  };

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// ============================================================================
// Notification Click Event
// ============================================================================

self.addEventListener('notificationclick', (event) => {
  console.log('[SW Push] Notification clicked:', event.notification.tag);

  // Close the notification
  event.notification.close();

  const data = event.notification.data || {};
  let targetUrl = data.url || '/app/notifications';

  // Handle action button clicks
  if (event.action) {
    switch (event.action) {
      case 'view':
        // Default URL is already set
        break;
      case 'approve':
        targetUrl = `/app/gates?action=approve&id=${data.gate_id}`;
        break;
      case 'dismiss':
        // Just close the notification
        return;
      case 'mark-read':
        // Mark as read via API
        if (data.notification_id) {
          markNotificationAsRead(data.notification_id);
        }
        return;
    }
  }

  // Open or focus the window
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((windowClients) => {
      // Check if there's already a window open
      for (const client of windowClients) {
        if (client.url.includes('/app') && 'focus' in client) {
          // Navigate existing window
          return client.navigate(targetUrl).then((client) => client.focus());
        }
      }
      // Open new window if none exists
      if (clients.openWindow) {
        return clients.openWindow(targetUrl);
      }
    })
  );
});

// ============================================================================
// Notification Close Event
// ============================================================================

self.addEventListener('notificationclose', (event) => {
  console.log('[SW Push] Notification closed:', event.notification.tag);

  // Track notification dismissal for analytics
  const data = event.notification.data || {};
  if (data.notification_id) {
    trackNotificationDismissed(data.notification_id);
  }
});

// ============================================================================
// Push Subscription Change Event
// ============================================================================

self.addEventListener('pushsubscriptionchange', (event) => {
  console.log('[SW Push] Push subscription changed');

  event.waitUntil(
    self.registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(getVapidPublicKey()),
    }).then((subscription) => {
      // Send new subscription to server
      return fetch('/api/v1/push/subscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          subscription: subscription.toJSON(),
          resubscribe: true,
        }),
      });
    })
  );
});

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Check if notification type requires user interaction
 */
function isPriorityNotification(type) {
  const priorityTypes = [
    'gate_approval_required',
    'policy_violation',
    'compliance_violation',
    'critical_alert',
  ];
  return priorityTypes.includes(type);
}

/**
 * Get notification action buttons based on type
 */
function getNotificationActions(type) {
  switch (type) {
    case 'gate_approval_required':
      return [
        { action: 'view', title: 'View Gate', icon: '/icons/view.png' },
        { action: 'approve', title: 'Approve', icon: '/icons/check.png' },
      ];
    case 'gate_approved':
    case 'gate_rejected':
      return [
        { action: 'view', title: 'View Details', icon: '/icons/view.png' },
      ];
    case 'policy_violation':
      return [
        { action: 'view', title: 'View Violation', icon: '/icons/alert.png' },
      ];
    default:
      return [
        { action: 'view', title: 'View', icon: '/icons/view.png' },
        { action: 'mark-read', title: 'Mark Read', icon: '/icons/check.png' },
      ];
  }
}

/**
 * Mark notification as read via API
 */
async function markNotificationAsRead(notificationId) {
  try {
    await fetch(`/api/v1/notifications/${notificationId}/read`, {
      method: 'PUT',
      credentials: 'include',
    });
  } catch (error) {
    console.error('[SW Push] Failed to mark notification as read:', error);
  }
}

/**
 * Track notification dismissal
 */
async function trackNotificationDismissed(notificationId) {
  try {
    await fetch('/api/v1/analytics/notification-dismissed', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ notification_id: notificationId }),
      credentials: 'include',
    });
  } catch (error) {
    // Silently fail - analytics is not critical
    console.debug('[SW Push] Failed to track dismissal:', error);
  }
}

/**
 * Convert VAPID public key from base64 to Uint8Array
 */
function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

/**
 * Get VAPID public key from environment
 * In production, this would be injected during build
 */
function getVapidPublicKey() {
  // This will be replaced during build or fetched from API
  return self.VAPID_PUBLIC_KEY || '';
}

// ============================================================================
// Message Handler - Communication with main thread
// ============================================================================

self.addEventListener('message', (event) => {
  const { type, data } = event.data || {};

  switch (type) {
    case 'SET_VAPID_KEY':
      self.VAPID_PUBLIC_KEY = data.key;
      break;
    case 'SKIP_WAITING':
      self.skipWaiting();
      break;
    case 'GET_VERSION':
      event.source.postMessage({ type: 'VERSION', version: SW_VERSION });
      break;
  }
});

console.log('[SW Push] Service worker loaded v' + SW_VERSION);
