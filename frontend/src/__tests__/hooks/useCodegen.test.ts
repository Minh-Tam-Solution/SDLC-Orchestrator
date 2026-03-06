/**
 * useCodegen Hook Tests
 *
 * @module frontend/src/__tests__/hooks/useCodegen.test
 * @description Tests for codegen templates, sessions, and session creation hooks
 * @sdlc SDLC 6.1.1
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import React from "react";

// Mock useAuth
vi.mock("@/hooks/useAuth", () => ({
  useAuth: () => ({ isAuthenticated: true, isLoading: false, user: { id: "u1" } }),
}));

// Mock API functions
const mockGetCodegenTemplates = vi.fn();
const mockGetCodegenSessions = vi.fn();
const mockCreateCodegenSession = vi.fn();
vi.mock("@/lib/api", () => ({
  getCodegenTemplates: (...args: unknown[]) => mockGetCodegenTemplates(...args),
  getCodegenSessions: (...args: unknown[]) => mockGetCodegenSessions(...args),
  createCodegenSession: (...args: unknown[]) => mockCreateCodegenSession(...args),
}));

import {
  useCodegenTemplates,
  useCodegenSessions,
  useCreateCodegenSession,
  codegenKeys,
} from "@/hooks/useCodegen";

let queryClient: QueryClient;

function wrapper({ children }: { children: ReactNode }) {
  return React.createElement(QueryClientProvider, { client: queryClient }, children);
}

beforeEach(() => {
  vi.clearAllMocks();
  queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
});

describe("useCodegenTemplates", () => {
  it("fetches templates successfully", async () => {
    const templates = [
      { id: "t1", name: "FastAPI CRUD", language: "python" },
      { id: "t2", name: "React Component", language: "typescript" },
    ];
    mockGetCodegenTemplates.mockResolvedValueOnce(templates);

    const { result } = renderHook(() => useCodegenTemplates(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(templates);
  });

  it("handles API error", async () => {
    mockGetCodegenTemplates.mockRejectedValueOnce(new Error("Service unavailable"));

    const { result } = renderHook(() => useCodegenTemplates(), { wrapper });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
  });
});

describe("useCodegenSessions", () => {
  it("fetches session list successfully", async () => {
    const sessions = [
      { id: "s1", status: "completed", template_id: "t1" },
      { id: "s2", status: "running", template_id: "t2" },
    ];
    mockGetCodegenSessions.mockResolvedValueOnce(sessions);

    const { result } = renderHook(() => useCodegenSessions(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(sessions);
  });

  it("passes options to API", async () => {
    mockGetCodegenSessions.mockResolvedValueOnce([]);

    renderHook(() => useCodegenSessions({ project_id: "p1" }), { wrapper });

    await waitFor(() => {
      expect(mockGetCodegenSessions).toHaveBeenCalledWith({ project_id: "p1" });
    });
  });
});

describe("useCreateCodegenSession", () => {
  it("creates session and invalidates cache", async () => {
    const newSession = { id: "s3", status: "pending", template_id: "t1" };
    mockCreateCodegenSession.mockResolvedValueOnce(newSession);

    const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries");

    const { result } = renderHook(() => useCreateCodegenSession(), { wrapper });

    await act(async () => {
      await result.current.mutateAsync({ template_id: "t1", project_id: "p1" });
    });

    expect(mockCreateCodegenSession).toHaveBeenCalledWith({ template_id: "t1", project_id: "p1" });
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: codegenKeys.sessions() });
  });
});

describe("codegenKeys", () => {
  it("generates correct cache key structure", () => {
    expect(codegenKeys.all).toEqual(["codegen"]);
    expect(codegenKeys.templates()).toEqual(["codegen", "templates"]);
    expect(codegenKeys.sessions()).toEqual(["codegen", "sessions"]);
    expect(codegenKeys.session("s1")).toEqual(["codegen", "sessions", "detail", "s1"]);
  });
});
