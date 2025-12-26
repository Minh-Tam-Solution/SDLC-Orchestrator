/**
 * =========================================================================
 * useSessionCheckpoint - Session Checkpoint Hook for Code Generation
 * SDLC Orchestrator - Sprint 51B
 *
 * Version: 1.0.0
 * Date: December 26, 2025
 * Status: ACTIVE - Sprint 51B Implementation
 * Authority: Frontend Team + CTO Approved
 * Foundation: Session-Checkpoint-Design.md
 *
 * Purpose:
 * - Fetch and manage active (resumable) sessions
 * - Resume generation from last checkpoint
 * - Track resume progress
 * - Clear expired sessions from local state
 *
 * References:
 * - docs/02-design/14-Technical-Specs/Session-Checkpoint-Design.md
 * - docs/02-design/15-Pattern-Adoption/Vibecode-Pattern-Adoption-Plan.md
 * =========================================================================
 */

import { useState, useCallback } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient, getAccessToken } from "@/api/client";

// ============================================================================
// Types
// ============================================================================

type SessionStatus =
  | "created"
  | "in_progress"
  | "checkpointed"
  | "completed"
  | "failed"
  | "resumed";

interface ErrorContext {
  error_type: string;
  error_message: string;
  file_path: string | null;
  recoverable: boolean;
}

interface SessionState {
  session_id: string;
  project_id: string;
  status: SessionStatus;
  files_completed: number;
  total_files_expected: number;
  checkpoint_count: number;
  last_checkpoint_at: string | null;
  errors: ErrorContext[];
  can_resume: boolean;
  created_at: string;
  expires_at: string;
}

interface GeneratedFile {
  file_path: string;
  content: string;
  language: string;
  lines: number;
}

interface CompletedFileInfo {
  file_path: string;
  language: string;
  lines: number;
}

// SSE Event types
interface SessionResumedEvent {
  type: "session_resumed";
  session_id: string;
  resumed_from_checkpoint: number;
  files_already_completed: number;
  files_remaining: number;
  completed_files: CompletedFileInfo[];
}

interface FileGeneratedEvent {
  type: "file_generated";
  session_id: string;
  path: string;
  content: string;
  lines: number;
  language: string;
  syntax_valid: boolean;
}

interface CompletedEvent {
  type: "completed";
  session_id: string;
  total_files: number;
  total_lines: number;
  duration_ms: number;
  success: boolean;
}

interface CheckpointEvent {
  type: "checkpoint";
  session_id: string;
  checkpoint_number: number;
  files_completed: number;
  total_files: number;
  last_file: string;
}

interface ErrorEvent {
  type: "error";
  session_id: string;
  message: string;
  recovery_id: string | null;
}

type SSEEvent =
  | SessionResumedEvent
  | FileGeneratedEvent
  | CompletedEvent
  | CheckpointEvent
  | ErrorEvent;

// ============================================================================
// Hook Return Type
// ============================================================================

interface UseSessionCheckpointReturn {
  /** List of active (resumable) sessions */
  activeSessions: SessionState[];
  /** Whether sessions are loading */
  isLoading: boolean;
  /** Error if any */
  error: Error | null;
  /** Resume a specific session */
  resumeSession: (sessionId: string) => Promise<GeneratedFile[]>;
  /** Whether resume is in progress */
  isResuming: boolean;
  /** Files recovered/generated during resume */
  resumedFiles: GeneratedFile[];
  /** Resume progress (0-100) */
  resumeProgress: number;
  /** Current resume status message */
  resumeStatus: string;
  /** Clear a session from local state */
  clearSession: (sessionId: string) => void;
  /** Refetch sessions */
  refetch: () => void;
}

// ============================================================================
// Hook Implementation
// ============================================================================

export function useSessionCheckpoint(): UseSessionCheckpointReturn {
  const queryClient = useQueryClient();
  const [resumedFiles, setResumedFiles] = useState<GeneratedFile[]>([]);
  const [resumeProgress, setResumeProgress] = useState(0);
  const [resumeStatus, setResumeStatus] = useState("");
  const [isResuming, setIsResuming] = useState(false);

  // Fetch active sessions
  const {
    data: activeSessions = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["sessions", "active"],
    queryFn: async () => {
      const response = await apiClient.get<SessionState[]>(
        "/codegen/sessions/active"
      );
      return response.data;
    },
    refetchInterval: 30000, // Refresh every 30s
    staleTime: 10000, // Consider stale after 10s
  });

  // Resume session via SSE
  const resumeSession = useCallback(
    async (sessionId: string): Promise<GeneratedFile[]> => {
      setIsResuming(true);
      setResumedFiles([]);
      setResumeProgress(0);
      setResumeStatus("Connecting to server...");

      return new Promise((resolve, reject) => {
        const files: GeneratedFile[] = [];
        let totalFiles = 0;

        try {
          // Get API base URL from environment or default
          const baseUrl =
            import.meta.env["VITE_API_URL"] || "http://localhost:8320/api/v1";

          // Get auth token for SSE connection
          const token = getAccessToken();
          if (!token) {
            setIsResuming(false);
            reject(new Error("Not authenticated"));
            return;
          }

          // Use fetch with ReadableStream for authenticated SSE
          // Note: EventSource doesn't support custom headers
          fetch(`${baseUrl}/codegen/generate/resume/${sessionId}`, {
            method: "POST",
            headers: {
              Authorization: `Bearer ${token}`,
              Accept: "text/event-stream",
            },
          })
            .then((response) => {
              if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
              }
              if (!response.body) {
                throw new Error("No response body");
              }

              const reader = response.body.getReader();
              const decoder = new TextDecoder();
              let buffer = "";

              const processStream = async () => {
                while (true) {
                  const { done, value } = await reader.read();
                  if (done) break;

                  buffer += decoder.decode(value, { stream: true });
                  const lines = buffer.split("\n");
                  buffer = lines.pop() || "";

                  for (const line of lines) {
                    if (line.startsWith("data: ")) {
                      const eventData = line.slice(6);
                      if (eventData.trim()) {
                        processEvent(eventData);
                      }
                    }
                  }
                }
              };

              const processEvent = (eventData: string) => {
                try {
                  const data: SSEEvent = JSON.parse(eventData);
                  handleSSEEvent(data, files, totalFiles);
                  totalFiles = updateTotalFiles(data, totalFiles);
                } catch (e) {
                  console.error("Failed to parse SSE event:", e);
                }
              };

              const handleSSEEvent = (
                data: SSEEvent,
                files: GeneratedFile[],
                total: number
              ) => {
                switch (data.type) {
                  case "session_resumed":
                    handleSessionResumed(data, files);
                    break;
                  case "file_generated":
                    handleFileGenerated(data, files, total);
                    break;
                  case "checkpoint":
                    handleCheckpoint(data);
                    break;
                  case "completed":
                    handleCompleted(data, files);
                    resolve(files);
                    break;
                  case "error":
                    handleError(data);
                    reject(new Error(data.message));
                    break;
                }
              };

              const updateTotalFiles = (data: SSEEvent, current: number): number => {
                if (data.type === "session_resumed") {
                  return data.files_already_completed + data.files_remaining;
                }
                return current;
              };

              const handleSessionResumed = (
                data: SessionResumedEvent,
                files: GeneratedFile[]
              ) => {
                const total = data.files_already_completed + data.files_remaining;
                setResumeProgress((data.files_already_completed / total) * 100);
                setResumeStatus(
                  `Resumed from checkpoint ${data.resumed_from_checkpoint}. ` +
                    `${data.files_already_completed} files recovered, ` +
                    `${data.files_remaining} remaining.`
                );
                data.completed_files.forEach((f) => {
                  files.push({
                    file_path: f.file_path,
                    content: "",
                    language: f.language,
                    lines: f.lines,
                  });
                });
                setResumedFiles([...files]);
              };

              const handleFileGenerated = (
                data: FileGeneratedEvent,
                files: GeneratedFile[],
                total: number
              ) => {
                const newFile: GeneratedFile = {
                  file_path: data.path,
                  content: data.content,
                  language: data.language,
                  lines: data.lines,
                };
                files.push(newFile);
                setResumedFiles([...files]);
                if (total > 0) {
                  setResumeProgress((files.length / total) * 100);
                }
                setResumeStatus(`Generated: ${data.path}`);
              };

              const handleCheckpoint = (data: CheckpointEvent) => {
                setResumeStatus(
                  `Checkpoint ${data.checkpoint_number} saved (${data.files_completed}/${data.total_files} files)`
                );
              };

              const handleCompleted = (data: CompletedEvent, _files: GeneratedFile[]) => {
                setResumeProgress(100);
                setResumeStatus(
                  `Completed! ${data.total_files} files, ${data.total_lines} lines in ${data.duration_ms}ms`
                );
                setIsResuming(false);
                queryClient.invalidateQueries({ queryKey: ["sessions", "active"] });
              };

              const handleError = (data: ErrorEvent) => {
                setResumeStatus(`Error: ${data.message}`);
                setIsResuming(false);
              };

              processStream().catch((err) => {
                setIsResuming(false);
                reject(err);
              });
            })
            .catch((err) => {
              setIsResuming(false);
              reject(err);
            });

        } catch (error) {
          setIsResuming(false);
          reject(error);
        }
      });
    },
    [queryClient]
  );

  // Clear session from local state (let Redis TTL handle actual cleanup)
  const clearSession = useCallback(
    (sessionId: string) => {
      queryClient.setQueryData<SessionState[]>(
        ["sessions", "active"],
        (old) => old?.filter((s) => s.session_id !== sessionId) || []
      );
    },
    [queryClient]
  );

  return {
    activeSessions,
    isLoading,
    error: error as Error | null,
    resumeSession,
    isResuming,
    resumedFiles,
    resumeProgress,
    resumeStatus,
    clearSession,
    refetch,
  };
}

export default useSessionCheckpoint;
