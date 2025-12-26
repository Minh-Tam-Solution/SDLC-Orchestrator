/**
 * =========================================================================
 * SessionResumeBanner - Banner for Resumable Sessions
 * SDLC Orchestrator - Sprint 51B
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * Status: ACTIVE - Sprint 51B Implementation
 * Authority: Frontend Team + CTO Approved
 * Foundation: Session-Checkpoint-Design.md
 *
 * Purpose:
 * - Display banner when resumable sessions are available
 * - Allow user to resume from last checkpoint
 * - Show resume progress
 * - Option to dismiss/clear session
 *
 * References:
 * - docs/02-design/14-Technical-Specs/Session-Checkpoint-Design.md
 * =========================================================================
 */

// React import not needed for JSX transform
import { AlertCircle, Play, X, Clock, RefreshCw } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { useSessionCheckpoint } from "@/hooks/useSessionCheckpoint";
import { formatDistanceToNow } from "date-fns";

// ============================================================================
// Types
// ============================================================================

interface SessionResumeBannerProps {
  /** Callback when resume is initiated */
  onResume?: (sessionId: string) => void;
  /** Callback when resume is complete */
  onResumeComplete?: (files: Array<{ file_path: string; content: string }>) => void;
  /** Optional class name for styling */
  className?: string;
}

// ============================================================================
// Component
// ============================================================================

export function SessionResumeBanner({
  onResume,
  onResumeComplete,
  className = "",
}: SessionResumeBannerProps) {
  const {
    activeSessions,
    isLoading,
    resumeSession,
    isResuming,
    resumeProgress,
    resumeStatus,
    clearSession,
  } = useSessionCheckpoint();

  // Don't render if loading or no sessions
  if (isLoading || activeSessions.length === 0) {
    return null;
  }

  // Find most recent resumable session
  const resumableSession = activeSessions.find(
    (s) =>
      s.can_resume &&
      (s.status === "checkpointed" ||
        s.status === "in_progress" ||
        (s.status === "failed" && s.errors.some((e) => e.recoverable)))
  );

  if (!resumableSession) {
    return null;
  }

  const handleResume = async () => {
    try {
      onResume?.(resumableSession.session_id);
      const files = await resumeSession(resumableSession.session_id);
      onResumeComplete?.(files);
    } catch (error) {
      console.error("Resume failed:", error);
    }
  };

  const handleDismiss = () => {
    clearSession(resumableSession.session_id);
  };

  // Determine status color and message
  const getStatusInfo = () => {
    switch (resumableSession.status) {
      case "checkpointed":
        return {
          icon: <Clock className="h-4 w-4" />,
          title: "Incomplete generation detected",
          description: `Checkpoint ${resumableSession.checkpoint_count} saved`,
          borderColor: "border-yellow-500",
          bgColor: "bg-yellow-50",
          textColor: "text-yellow-800",
          subTextColor: "text-yellow-700",
        };
      case "in_progress":
        return {
          icon: <RefreshCw className="h-4 w-4" />,
          title: "Generation was interrupted",
          description: "Session can be resumed",
          borderColor: "border-blue-500",
          bgColor: "bg-blue-50",
          textColor: "text-blue-800",
          subTextColor: "text-blue-700",
        };
      case "failed":
        return {
          icon: <AlertCircle className="h-4 w-4" />,
          title: "Generation failed - can retry",
          description: resumableSession.errors[0]?.error_message || "Unknown error",
          borderColor: "border-red-500",
          bgColor: "bg-red-50",
          textColor: "text-red-800",
          subTextColor: "text-red-700",
        };
      default:
        return {
          icon: <Clock className="h-4 w-4" />,
          title: "Session available",
          description: "Resume available",
          borderColor: "border-gray-500",
          bgColor: "bg-gray-50",
          textColor: "text-gray-800",
          subTextColor: "text-gray-700",
        };
    }
  };

  const statusInfo = getStatusInfo();

  return (
    <Alert
      className={`mb-4 ${statusInfo.borderColor} ${statusInfo.bgColor} ${className}`}
    >
      <div className="flex items-center gap-2">
        {statusInfo.icon}
        <AlertDescription className="flex-1">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <span className={`font-medium ${statusInfo.textColor}`}>
                {statusInfo.title}
              </span>
              <p className={`text-sm ${statusInfo.subTextColor}`}>
                {resumableSession.files_completed} of{" "}
                {resumableSession.total_files_expected} files completed
                {resumableSession.last_checkpoint_at && (
                  <span className="ml-2 inline-flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {formatDistanceToNow(
                      new Date(resumableSession.last_checkpoint_at),
                      { addSuffix: true }
                    )}
                  </span>
                )}
              </p>

              {/* Show resume progress */}
              {isResuming && (
                <div className="mt-2">
                  <Progress value={resumeProgress} className="h-2 w-48" />
                  <p className="mt-1 text-xs text-gray-600">{resumeStatus}</p>
                </div>
              )}
            </div>

            {/* Action buttons */}
            <div className="flex gap-2 ml-4">
              <Button
                variant="outline"
                size="sm"
                onClick={handleResume}
                disabled={isResuming}
                className={`${statusInfo.textColor}`}
              >
                {isResuming ? (
                  <>
                    <RefreshCw className="mr-1 h-4 w-4 animate-spin" />
                    Resuming...
                  </>
                ) : (
                  <>
                    <Play className="mr-1 h-4 w-4" />
                    Resume
                  </>
                )}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleDismiss}
                disabled={isResuming}
                title="Dismiss (session will expire in 24h)"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </AlertDescription>
      </div>
    </Alert>
  );
}

export default SessionResumeBanner;
