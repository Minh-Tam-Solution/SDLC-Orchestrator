/**
 * useProjects Hook Tests
 *
 * @module frontend/src/__tests__/hooks/useProjects.test
 * @description Tests for project list, detail, create, delete, and sync hooks
 * @sdlc SDLC 6.1.1
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import React from "react";

// Mock useAuth
vi.mock("@/hooks/useAuth", () => ({
  useAuth: () => ({ isAuthenticated: true, isLoading: false, user: { id: "u1" } }),
}));

// Mock telemetry
vi.mock("@/lib/telemetry", () => ({
  trackProjectCreated: vi.fn(),
}));

// Mock API functions
const mockGetProjects = vi.fn();
const mockGetProject = vi.fn();
const mockCreateProject = vi.fn();
const mockDeleteProject = vi.fn();
const mockSyncProjectMetadata = vi.fn();
vi.mock("@/lib/api", () => ({
  getProjects: (...args: unknown[]) => mockGetProjects(...args),
  getProject: (...args: unknown[]) => mockGetProject(...args),
  createProject: (...args: unknown[]) => mockCreateProject(...args),
  deleteProject: (...args: unknown[]) => mockDeleteProject(...args),
  syncProjectMetadata: (...args: unknown[]) => mockSyncProjectMetadata(...args),
}));

import { useProjects, useProject, useCreateProject, useDeleteProject, useProjectSync, projectKeys } from "@/hooks/useProjects";

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

describe("useProjects", () => {
  it("fetches project list successfully", async () => {
    const projects = [
      { id: "p1", name: "Project Alpha", status: "active" },
      { id: "p2", name: "Project Beta", status: "active" },
    ];
    mockGetProjects.mockResolvedValueOnce(projects);

    const { result } = renderHook(() => useProjects(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(projects);
    expect(mockGetProjects).toHaveBeenCalledWith(undefined);
  });

  it("passes pagination options to API", async () => {
    mockGetProjects.mockResolvedValueOnce([]);

    const { result } = renderHook(() => useProjects({ skip: 0, limit: 10 }), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mockGetProjects).toHaveBeenCalledWith({ skip: 0, limit: 10 });
  });

  it("handles API error gracefully", async () => {
    mockGetProjects.mockRejectedValueOnce(new Error("Network error"));

    const { result } = renderHook(() => useProjects(), { wrapper });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toBeTruthy();
  });
});

describe("useProject", () => {
  it("fetches single project by ID", async () => {
    const project = { id: "p1", name: "Project Alpha", description: "Test project" };
    mockGetProject.mockResolvedValueOnce(project);

    const { result } = renderHook(() => useProject("p1"), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(project);
    expect(mockGetProject).toHaveBeenCalledWith("p1");
  });

  it("does not fetch when projectId is undefined", () => {
    const { result } = renderHook(() => useProject(undefined), { wrapper });

    expect(result.current.fetchStatus).toBe("idle");
    expect(mockGetProject).not.toHaveBeenCalled();
  });
});

describe("projectKeys", () => {
  it("generates correct cache key structure", () => {
    expect(projectKeys.all).toEqual(["projects"]);
    expect(projectKeys.lists()).toEqual(["projects", "list"]);
    expect(projectKeys.detail("p1")).toEqual(["projects", "detail", "p1"]);
  });
});
