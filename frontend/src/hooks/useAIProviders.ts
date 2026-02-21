/**
 * AI Providers Hooks - TanStack Query
 * @module frontend/landing/src/hooks/useAIProviders
 * @status Sprint 70 - AI Provider Admin UI
 * @description Hooks for managing AI provider configuration
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Fetch helper with httpOnly cookies
async function fetchWithAuth<T>(
  url: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE}${url}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// Types
export interface ProviderStatus {
  available: boolean;
  configured: boolean;
  url?: string;
  model?: string;
  timeout?: number;
  lastTest?: {
    success: boolean;
    latency_ms: number;
    error?: string;
    tested_at: string;
  };
}

export interface CodegenConfig {
  url: string;
  model_primary: string;
  model_fast: string;
  timeout: number;
}

export interface AIProviderConfig {
  ollama: ProviderStatus;
  claude: ProviderStatus;
  openai: ProviderStatus;
  codegen: CodegenConfig;
  default_provider: string;
  fallback_enabled: boolean;
  fallback_chain: string[];
  available_models?: {
    ollama: string[];
    claude: string[];
    openai: string[];
  };
}

export interface TestResult {
  success: boolean;
  latency_ms: number;
  error?: string;
  provider: string;
  model?: string;
  tested_at: string;
}

// Query keys
export const aiProviderKeys = {
  all: ["ai-providers"] as const,
  config: () => [...aiProviderKeys.all, "config"] as const,
  models: (provider: string) => [...aiProviderKeys.all, "models", provider] as const,
};

/**
 * Get AI provider configuration
 */
export function useAIProviderConfig() {
  return useQuery({
    queryKey: aiProviderKeys.config(),
    queryFn: () => fetchWithAuth<AIProviderConfig>("/admin/ai-providers/config"),
  });
}

/**
 * Get available models for a provider (fetches from Ollama API for local models)
 */
export function useAvailableModels(provider: string) {
  return useQuery({
    queryKey: aiProviderKeys.models(provider),
    queryFn: () => fetchWithAuth<{ models: string[] }>(
      `/admin/ai-providers/${provider}/models`
    ).then(r => r.models),
    enabled: provider === "ollama", // Only fetch for Ollama (local)
  });
}

/**
 * Update AI provider configuration
 */
export function useUpdateAIProvider() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      provider,
      data,
    }: {
      provider: string;
      data: Record<string, unknown>;
    }) => {
      return fetchWithAuth(`/admin/ai-providers/${provider}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: aiProviderKeys.all });
    },
  });
}

/**
 * Test AI provider connection
 */
export function useTestAIProvider() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (provider: string) => {
      return fetchWithAuth<TestResult>(
        `/admin/ai-providers/${provider}/test`,
        { method: "POST" }
      );
    },
    onSuccess: () => {
      // Refetch config to update lastTest status
      queryClient.invalidateQueries({ queryKey: aiProviderKeys.config() });
    },
  });
}

/**
 * Refresh available Ollama models
 */
export function useRefreshOllamaModels() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      return fetchWithAuth<{ models: string[] }>(
        "/admin/ai-providers/ollama/refresh-models",
        { method: "POST" }
      ).then(r => r.models);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: aiProviderKeys.models("ollama") });
      queryClient.invalidateQueries({ queryKey: aiProviderKeys.config() });
    },
  });
}
