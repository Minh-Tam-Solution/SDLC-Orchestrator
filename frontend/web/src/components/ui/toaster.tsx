/**
 * File: frontend/web/src/components/ui/toaster.tsx
 * Version: 1.0.0
 * Status: ACTIVE - Sprint 39 Toast Notification System
 * Date: 2025-12-17
 * Authority: CTO Approved (Sprint 39 Directive)
 * Framework: SDLC 5.1.1 Complete Lifecycle
 *
 * Description:
 * Toaster component that renders toast notifications from the useToast hook.
 * Mount this once in your app (typically in App.tsx or layout).
 */

import { CheckCircle2, AlertCircle, AlertTriangle, Info } from 'lucide-react'

import {
  Toast,
  ToastClose,
  ToastDescription,
  ToastProvider,
  ToastTitle,
  ToastViewport,
} from '@/components/ui/toast'
import { useToast } from '@/hooks/useToast'

/**
 * Get icon for toast variant
 */
function ToastIcon({ variant }: { variant?: string }) {
  switch (variant) {
    case 'success':
      return <CheckCircle2 className="h-5 w-5 text-green-600" />
    case 'error':
    case 'destructive':
      return <AlertCircle className="h-5 w-5 text-red-600" />
    case 'warning':
      return <AlertTriangle className="h-5 w-5 text-yellow-600" />
    case 'info':
      return <Info className="h-5 w-5 text-blue-600" />
    default:
      return null
  }
}

export function Toaster() {
  const { toasts } = useToast()

  return (
    <ToastProvider>
      {toasts.map(function ({ id, title, description, action, variant, ...props }) {
        const variantValue = variant ?? 'default'
        return (
          <Toast key={id} variant={variantValue} {...props}>
            <div className="flex gap-3">
              <ToastIcon variant={variantValue} />
              <div className="grid gap-1">
                {title && <ToastTitle>{title}</ToastTitle>}
                {description && (
                  <ToastDescription>{description}</ToastDescription>
                )}
              </div>
            </div>
            {action}
            <ToastClose />
          </Toast>
        )
      })}
      <ToastViewport />
    </ToastProvider>
  )
}
