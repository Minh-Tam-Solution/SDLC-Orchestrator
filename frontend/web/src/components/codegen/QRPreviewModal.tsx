/**
 * =========================================================================
 * QRPreviewModal - QR Code Mobile Preview Component
 * SDLC Orchestrator - Sprint 51B
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * Status: ACTIVE - Sprint 51B Implementation
 * Authority: Frontend Team + CTO Approved
 * Foundation: QR-Preview-Design.md
 *
 * Purpose:
 * - Display QR code for mobile preview
 * - Allow password protection for previews
 * - Show expiration time and copy link
 * - Manage preview lifecycle
 *
 * References:
 * - docs/02-design/14-Technical-Specs/QR-Preview-Design.md
 * =========================================================================
 */

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  QrCode,
  Copy,
  Check,
  Lock,
  Clock,
  ExternalLink,
  Loader2,
  Trash2,
} from "lucide-react";
import { useToast } from "@/hooks/useToast";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/api/client";

// ============================================================================
// Types
// ============================================================================

interface PreviewResponse {
  preview_url: string;
  token: string;
  expires_at: string;
  qr_data: string;
}

interface QRPreviewModalProps {
  /** Session ID to create preview for */
  sessionId: string;
  /** Whether modal is open */
  isOpen: boolean;
  /** Callback when modal closes */
  onClose: () => void;
  /** Optional existing preview data */
  existingPreview?: PreviewResponse | null;
}

// ============================================================================
// Component
// ============================================================================

export function QRPreviewModal({
  sessionId,
  isOpen,
  onClose,
  existingPreview,
}: QRPreviewModalProps) {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Form state
  const [passwordEnabled, setPasswordEnabled] = useState(false);
  const [password, setPassword] = useState("");
  const [expiresInHours, setExpiresInHours] = useState("24");
  const [copied, setCopied] = useState(false);

  // Preview data state
  const [preview, setPreview] = useState<PreviewResponse | null>(
    existingPreview || null
  );

  // Create preview mutation
  const createPreviewMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post<PreviewResponse>(
        `/codegen/sessions/${sessionId}/preview`,
        {
          password: passwordEnabled ? password : null,
          expires_in_hours: parseInt(expiresInHours),
        }
      );
      return response.data;
    },
    onSuccess: (data) => {
      setPreview(data);
      toast({
        title: "Preview created",
        description: "QR code ready for mobile preview",
      });
    },
    onError: (error: Error) => {
      toast({
        title: "Failed to create preview",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  // Delete preview mutation
  const deletePreviewMutation = useMutation({
    mutationFn: async (token: string) => {
      await apiClient.delete(`/codegen/preview/${token}`);
    },
    onSuccess: () => {
      setPreview(null);
      queryClient.invalidateQueries({ queryKey: ["sessions", sessionId] });
      toast({
        title: "Preview deleted",
        description: "Preview link has been revoked",
      });
    },
    onError: (error: Error) => {
      toast({
        title: "Failed to delete preview",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  // Copy link to clipboard
  const handleCopyLink = async () => {
    if (!preview) return;

    try {
      await navigator.clipboard.writeText(preview.preview_url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      toast({
        title: "Link copied",
        description: "Preview URL copied to clipboard",
      });
    } catch {
      toast({
        title: "Copy failed",
        description: "Please copy the link manually",
        variant: "destructive",
      });
    }
  };

  // Format expiration time
  const formatExpiration = (expiresAt: string) => {
    const expires = new Date(expiresAt);
    const now = new Date();
    const diffMs = expires.getTime() - now.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffMins = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));

    if (diffHours > 0) {
      return `${diffHours}h ${diffMins}m remaining`;
    }
    return `${diffMins}m remaining`;
  };

  // Reset form when closing
  const handleClose = () => {
    if (!existingPreview) {
      setPasswordEnabled(false);
      setPassword("");
      setExpiresInHours("24");
      setPreview(null);
    }
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <QrCode className="h-5 w-5" />
            Mobile Preview
          </DialogTitle>
          <DialogDescription>
            {preview
              ? "Scan QR code to preview on mobile device"
              : "Create a shareable preview link with QR code"}
          </DialogDescription>
        </DialogHeader>

        {preview ? (
          // Show QR code and preview info
          <div className="flex flex-col items-center gap-4 py-4">
            {/* QR Code */}
            <div className="rounded-lg border bg-white p-4">
              {preview.qr_data ? (
                <img
                  src={preview.qr_data}
                  alt="Preview QR Code"
                  className="h-48 w-48"
                />
              ) : (
                <div className="flex h-48 w-48 items-center justify-center bg-gray-100">
                  <QrCode className="h-16 w-16 text-gray-400" />
                </div>
              )}
            </div>

            {/* Preview URL */}
            <div className="flex w-full items-center gap-2">
              <Input
                value={preview.preview_url}
                readOnly
                className="flex-1 font-mono text-sm"
              />
              <Button
                variant="outline"
                size="icon"
                onClick={handleCopyLink}
                title="Copy link"
              >
                {copied ? (
                  <Check className="h-4 w-4 text-green-500" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </Button>
              <Button
                variant="outline"
                size="icon"
                onClick={() => window.open(preview.preview_url, "_blank")}
                title="Open preview"
              >
                <ExternalLink className="h-4 w-4" />
              </Button>
            </div>

            {/* Expiration info */}
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock className="h-4 w-4" />
              <span>{formatExpiration(preview.expires_at)}</span>
              {passwordEnabled && (
                <>
                  <span className="mx-1">•</span>
                  <Lock className="h-4 w-4" />
                  <span>Password protected</span>
                </>
              )}
            </div>
          </div>
        ) : (
          // Show creation form
          <div className="flex flex-col gap-4 py-4">
            {/* Password protection */}
            <div className="flex items-center justify-between">
              <Label
                htmlFor="password-switch"
                className="flex items-center gap-2"
              >
                <Lock className="h-4 w-4" />
                Password protection
              </Label>
              <Switch
                id="password-switch"
                checked={passwordEnabled}
                onCheckedChange={setPasswordEnabled}
              />
            </div>

            {passwordEnabled && (
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Enter preview password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
            )}

            {/* Expiration time */}
            <div className="space-y-2">
              <Label htmlFor="expires">Expires after</Label>
              <Select value={expiresInHours} onValueChange={setExpiresInHours}>
                <SelectTrigger id="expires">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">1 hour</SelectItem>
                  <SelectItem value="6">6 hours</SelectItem>
                  <SelectItem value="24">24 hours</SelectItem>
                  <SelectItem value="48">48 hours</SelectItem>
                  <SelectItem value="168">7 days</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        )}

        <DialogFooter className="flex gap-2">
          {preview ? (
            <>
              <Button
                variant="destructive"
                onClick={() => deletePreviewMutation.mutate(preview.token)}
                disabled={deletePreviewMutation.isPending}
              >
                {deletePreviewMutation.isPending ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Trash2 className="mr-2 h-4 w-4" />
                )}
                Delete Preview
              </Button>
              <Button variant="outline" onClick={handleClose}>
                Close
              </Button>
            </>
          ) : (
            <>
              <Button variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button
                onClick={() => createPreviewMutation.mutate()}
                disabled={
                  createPreviewMutation.isPending ||
                  (passwordEnabled && !password)
                }
              >
                {createPreviewMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    <QrCode className="mr-2 h-4 w-4" />
                    Generate QR Code
                  </>
                )}
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default QRPreviewModal;
