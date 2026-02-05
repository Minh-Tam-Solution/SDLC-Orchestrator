/**
 * Spec Converter Hook - API Integration
 * Sprint 154 Day 4 - Visual Editor Frontend
 *
 * Hook for interacting with Spec Converter API endpoints.
 *
 * Endpoints:
 * - POST /parse - Parse content to IR
 * - POST /render - Render IR to format
 * - POST /convert - Convert between formats
 * - POST /detect - Detect format of content
 *
 * Architecture: ADR-050 Frontend Layer
 */

import { useMutation, useQuery } from "@tanstack/react-query";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

// =============================================================================
// Types
// =============================================================================

export type SpecFormat = "BDD" | "OPENSPEC" | "USER_STORY";
export type SpecStatus = "DRAFT" | "PROPOSED" | "APPROVED" | "DEPRECATED";
export type SpecTier = "LITE" | "STANDARD" | "PROFESSIONAL" | "ENTERPRISE";
export type Priority = "P0" | "P1" | "P2" | "P3";

export interface SpecRequirement {
  id: string;
  title: string;
  priority: Priority;
  tier: string[];
  given: string;
  when: string;
  then: string;
  user_story?: string;
  acceptance_criteria: string[];
}

export interface AcceptanceCriterion {
  id: string;
  scenario: string;
  given: string;
  when: string;
  then: string;
  tier: string[];
  testable: boolean;
}

export interface SpecIR {
  spec_id: string;
  title: string;
  version: string;
  status: SpecStatus;
  tier: SpecTier[];
  owner: string;
  last_updated: string;
  tags: string[];
  related_adrs: string[];
  related_specs: string[];
  requirements: SpecRequirement[];
  acceptance_criteria: AcceptanceCriterion[];
}

export interface ParseRequest {
  content: string;
  source_format: SpecFormat;
}

export interface RenderRequest {
  ir: SpecIR;
  target_format: SpecFormat;
}

export interface RenderResponse {
  content: string;
  format: string;
}

export interface ConvertRequest {
  content: string;
  source_format: SpecFormat;
  target_format: SpecFormat;
}

export interface ConvertResponse {
  content: string;
  source_format: string;
  target_format: string;
}

export interface DetectRequest {
  content: string;
}

export interface DetectResponse {
  format: SpecFormat | null;
  confidence: number;
}

// =============================================================================
// API Functions
// =============================================================================

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const defaultHeaders: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (typeof window !== "undefined") {
    const accessToken = localStorage.getItem("access_token");
    if (accessToken) {
      defaultHeaders["Authorization"] = `Bearer ${accessToken}`;
    }
  }

  const response = await fetch(url, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
    credentials: "include",
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({
      detail: "An unexpected error occurred",
    }));
    throw new Error(errorData.detail || "Request failed");
  }

  return response.json();
}

// Parse content to IR
async function parseSpec(request: ParseRequest): Promise<SpecIR> {
  return apiRequest<SpecIR>("/spec-converter/parse", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

// Render IR to format
async function renderSpec(request: RenderRequest): Promise<RenderResponse> {
  return apiRequest<RenderResponse>("/spec-converter/render", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

// Convert between formats
async function convertSpec(request: ConvertRequest): Promise<ConvertResponse> {
  return apiRequest<ConvertResponse>("/spec-converter/convert", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

// Detect format of content
async function detectFormat(request: DetectRequest): Promise<DetectResponse> {
  return apiRequest<DetectResponse>("/spec-converter/detect", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

// =============================================================================
// Hooks
// =============================================================================

/**
 * Hook for parsing spec content to IR
 */
export function useParseSpec() {
  return useMutation({
    mutationFn: parseSpec,
    mutationKey: ["spec-converter", "parse"],
  });
}

/**
 * Hook for rendering IR to spec format
 */
export function useRenderSpec() {
  return useMutation({
    mutationFn: renderSpec,
    mutationKey: ["spec-converter", "render"],
  });
}

/**
 * Hook for converting between spec formats
 */
export function useConvertSpec() {
  return useMutation({
    mutationFn: convertSpec,
    mutationKey: ["spec-converter", "convert"],
  });
}

/**
 * Hook for detecting spec format
 */
export function useDetectFormat() {
  return useMutation({
    mutationFn: detectFormat,
    mutationKey: ["spec-converter", "detect"],
  });
}

/**
 * Combined hook for spec converter operations
 */
export function useSpecConverter() {
  const parseMutation = useParseSpec();
  const renderMutation = useRenderSpec();
  const convertMutation = useConvertSpec();
  const detectMutation = useDetectFormat();

  return {
    // Parse
    parse: parseMutation.mutate,
    parseAsync: parseMutation.mutateAsync,
    isParsing: parseMutation.isPending,
    parseError: parseMutation.error,
    parsedIR: parseMutation.data,

    // Render
    render: renderMutation.mutate,
    renderAsync: renderMutation.mutateAsync,
    isRendering: renderMutation.isPending,
    renderError: renderMutation.error,
    renderedContent: renderMutation.data,

    // Convert
    convert: convertMutation.mutate,
    convertAsync: convertMutation.mutateAsync,
    isConverting: convertMutation.isPending,
    convertError: convertMutation.error,
    convertedContent: convertMutation.data,

    // Detect
    detect: detectMutation.mutate,
    detectAsync: detectMutation.mutateAsync,
    isDetecting: detectMutation.isPending,
    detectError: detectMutation.error,
    detectedFormat: detectMutation.data,

    // Combined states
    isLoading:
      parseMutation.isPending ||
      renderMutation.isPending ||
      convertMutation.isPending ||
      detectMutation.isPending,
  };
}

// =============================================================================
// Utility Functions
// =============================================================================

/**
 * Create an empty SpecIR with default values
 */
export function createEmptySpecIR(specId?: string): SpecIR {
  return {
    spec_id: specId || `SPEC-${Date.now()}`,
    title: "",
    version: "1.0.0",
    status: "DRAFT",
    tier: ["ALL"] as unknown as SpecTier[],
    owner: "",
    last_updated: new Date().toISOString(),
    tags: [],
    related_adrs: [],
    related_specs: [],
    requirements: [],
    acceptance_criteria: [],
  };
}

/**
 * Create an empty requirement
 */
export function createEmptyRequirement(id?: string): SpecRequirement {
  return {
    id: id || `REQ-${Date.now()}`,
    title: "",
    priority: "P1",
    tier: ["ALL"],
    given: "",
    when: "",
    then: "",
    acceptance_criteria: [],
  };
}

/**
 * Create an empty acceptance criterion
 */
export function createEmptyAcceptanceCriterion(id?: string): AcceptanceCriterion {
  return {
    id: id || `AC-${Date.now()}`,
    scenario: "",
    given: "",
    when: "",
    then: "",
    tier: ["ALL"],
    testable: true,
  };
}
