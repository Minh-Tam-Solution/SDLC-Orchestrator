/**
 * Test Utilities - Custom render with providers
 * Version: 1.0.0 (Sprint 28 Day 3)
 *
 * Provides wrapper components for testing:
 * - QueryClientProvider (React Query)
 * - BrowserRouter (React Router)
 * - Custom providers as needed
 */

import { ReactElement, ReactNode } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'

// Create a fresh QueryClient for each test
function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false, // Don't retry failed queries in tests
        gcTime: 0, // Don't cache queries
        staleTime: 0, // Always consider data stale
      },
      mutations: {
        retry: false,
      },
    },
  })
}

interface AllProvidersProps {
  children: ReactNode
}

function AllProviders({ children }: AllProvidersProps) {
  const queryClient = createTestQueryClient()

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{children}</BrowserRouter>
    </QueryClientProvider>
  )
}

// Custom render that wraps component with all providers
function customRender(
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) {
  return render(ui, { wrapper: AllProviders, ...options })
}

// Re-export everything from testing-library
export * from '@testing-library/react'
export { userEvent } from '@testing-library/user-event'

// Override render with custom render
export { customRender as render }

// Export query client creator for tests that need direct access
export { createTestQueryClient }

// =========================================================================
// MOCK DATA FACTORIES
// =========================================================================

import type {
  ComplianceTier,
  GateType,
  GateProgressStatus,
  CouncilDeliberation,
  AIResponse,
  Ranking,
  FinalAnswer,
  ChatMessage,
} from '@/types/council'

/**
 * Create mock AI response
 */
export function createMockAIResponse(overrides?: Partial<AIResponse>): AIResponse {
  return {
    provider: 'Claude',
    model: 'claude-3-5-sonnet',
    response: 'This is a mock AI response for testing.',
    duration_ms: 450,
    confidence: 85,
    ...overrides,
  }
}

/**
 * Create mock ranking
 */
export function createMockRanking(overrides?: Partial<Ranking>): Ranking {
  return {
    ranker: 'Claude',
    rankings: ['Claude', 'OpenAI', 'Gemini'],
    reasoning: 'Mock reasoning for test',
    ...overrides,
  }
}

/**
 * Create mock final answer
 */
export function createMockFinalAnswer(overrides?: Partial<FinalAnswer>): FinalAnswer {
  return {
    answer: 'Combined recommendation based on consensus',
    confidence: 92,
    reasoning: 'All AIs agreed on the approach.',
    suggested_action: 'Create evidence item and submit for review.',
    ...overrides,
  }
}

/**
 * Create mock council deliberation
 */
export function createMockDeliberation(overrides?: Partial<CouncilDeliberation>): CouncilDeliberation {
  return {
    stage1_responses: [
      createMockAIResponse({ provider: 'Claude' }),
      createMockAIResponse({ provider: 'OpenAI', model: 'gpt-4o', confidence: 78 }),
      createMockAIResponse({ provider: 'Gemini', model: 'gemini-1.5-pro', confidence: 72 }),
    ],
    stage2_rankings: [
      createMockRanking({ ranker: 'Claude' }),
      createMockRanking({ ranker: 'OpenAI' }),
      createMockRanking({ ranker: 'Gemini' }),
    ],
    stage3_synthesis: createMockFinalAnswer(),
    total_duration_ms: 2300,
    total_cost_usd: 0.0045,
    providers_used: ['Claude', 'OpenAI', 'Gemini'],
    ...overrides,
  }
}

/**
 * Create mock chat message
 */
export function createMockChatMessage(overrides?: Partial<ChatMessage>): ChatMessage {
  return {
    id: `msg_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
    role: 'assistant',
    content: 'This is a test message.',
    timestamp: new Date(),
    ...overrides,
  }
}

/**
 * Create mock gate statuses
 */
export function createMockGateStatuses(
  currentGate: GateType = 'G2'
): Record<GateType, GateProgressStatus> {
  const gateOrder: GateType[] = ['G0.1', 'G0.2', 'G1', 'G2', 'G3', 'G4', 'G5']
  const currentIndex = gateOrder.indexOf(currentGate)

  return gateOrder.reduce((acc, gate, index) => {
    if (index < currentIndex) {
      acc[gate] = 'passed'
    } else if (index === currentIndex) {
      acc[gate] = 'current'
    } else {
      acc[gate] = 'pending'
    }
    return acc
  }, {} as Record<GateType, GateProgressStatus>)
}

/**
 * Create mock project
 */
export function createMockProject(overrides?: Record<string, unknown>) {
  return {
    id: 'project-123',
    name: 'Test Project',
    key: 'TEST',
    description: 'A test project for unit tests',
    current_stage: 'BUILD',
    gate_status: 'pending',
    progress: 65,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    ...overrides,
  }
}

/**
 * Get tier config for testing
 */
export function getTierTestConfig(tier: ComplianceTier) {
  const configs = {
    lite: { label: 'Lite', icon: '🌱', color: 'green' },
    standard: { label: 'Standard', icon: '⚡', color: 'blue' },
    enterprise: { label: 'Enterprise', icon: '👑', color: 'amber' },
  }
  return configs[tier]
}
