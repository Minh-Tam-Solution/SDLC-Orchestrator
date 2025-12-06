/**
 * Unit Tests: ChatMessage Component
 * Version: 1.0.0 (Sprint 28 Day 3)
 *
 * Test coverage:
 * - User message rendering
 * - Assistant message rendering
 * - System message rendering
 * - Loading state (thinking indicator)
 * - Error state
 * - Council deliberation expansion
 * - Time formatting
 * - Accessibility
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@/test/test-utils'
import userEvent from '@testing-library/user-event'
import { ChatMessage } from './ChatMessage'
import { createMockChatMessage, createMockDeliberation } from '@/test/test-utils'

describe('ChatMessage', () => {
  describe('user message', () => {
    it('renders user message with content', () => {
      const message = createMockChatMessage({
        role: 'user',
        content: 'How do I implement authentication?',
      })

      render(<ChatMessage message={message} />)

      expect(screen.getByText('How do I implement authentication?')).toBeInTheDocument()
    })

    it('shows "You" label for user messages', () => {
      const message = createMockChatMessage({ role: 'user' })

      render(<ChatMessage message={message} />)

      expect(screen.getByText(/You/)).toBeInTheDocument()
    })

    it('shows user avatar icon', () => {
      const message = createMockChatMessage({ role: 'user' })

      render(<ChatMessage message={message} />)

      // User avatar container should have primary background
      const avatarContainer = document.querySelector('.bg-primary')
      expect(avatarContainer).toBeInTheDocument()
    })

    it('displays timestamp', () => {
      const timestamp = new Date('2025-12-04T14:30:00')
      const message = createMockChatMessage({
        role: 'user',
        timestamp,
      })

      render(<ChatMessage message={message} />)

      // Check for time (format varies by locale, but should contain numbers)
      const timeText = screen.getByText(/You/)
      expect(timeText.textContent).toMatch(/\d{1,2}:\d{2}/)
    })
  })

  describe('assistant message', () => {
    it('renders assistant message with content', () => {
      const message = createMockChatMessage({
        role: 'assistant',
        content: 'Here is the recommended approach for authentication.',
      })

      render(<ChatMessage message={message} />)

      expect(screen.getByText('Here is the recommended approach for authentication.')).toBeInTheDocument()
    })

    it('shows "AI Assistant" label', () => {
      const message = createMockChatMessage({ role: 'assistant' })

      render(<ChatMessage message={message} />)

      expect(screen.getByText(/AI Assistant/)).toBeInTheDocument()
    })

    it('shows bot avatar icon', () => {
      const message = createMockChatMessage({ role: 'assistant' })

      render(<ChatMessage message={message} />)

      // Bot avatar container should have primary/10 background
      const avatarContainer = document.querySelector('.bg-primary\\/10')
      expect(avatarContainer).toBeInTheDocument()
    })
  })

  describe('system message', () => {
    it('renders system message with centered styling', () => {
      const message = createMockChatMessage({
        role: 'system',
        content: 'Council mode enabled',
      })

      render(<ChatMessage message={message} />)

      expect(screen.getByText('Council mode enabled')).toBeInTheDocument()
    })

    it('has pill-shaped styling', () => {
      const message = createMockChatMessage({
        role: 'system',
        content: 'System notification',
      })

      render(<ChatMessage message={message} />)

      const systemMessage = screen.getByText('System notification')
      expect(systemMessage).toHaveClass('rounded-full')
    })

    it('does not show avatar for system messages', () => {
      const message = createMockChatMessage({
        role: 'system',
        content: 'System message',
      })

      render(<ChatMessage message={message} />)

      // No avatar containers for system messages
      expect(document.querySelector('.bg-primary')).not.toBeInTheDocument()
      expect(document.querySelector('.bg-primary\\/10')).not.toBeInTheDocument()
    })
  })

  describe('loading state', () => {
    it('shows thinking indicator when loading', () => {
      const message = createMockChatMessage({
        role: 'assistant',
        isLoading: true,
      })

      render(<ChatMessage message={message} />)

      expect(screen.getByText('AI is thinking...')).toBeInTheDocument()
    })

    it('shows animated dots when loading', () => {
      const message = createMockChatMessage({
        role: 'assistant',
        isLoading: true,
      })

      render(<ChatMessage message={message} />)

      // Should have bouncing dots
      const bouncingElements = document.querySelectorAll('.animate-bounce')
      expect(bouncingElements.length).toBeGreaterThan(0)
    })

    it('shows pulsing bot icon when loading', () => {
      const message = createMockChatMessage({
        role: 'assistant',
        isLoading: true,
      })

      render(<ChatMessage message={message} />)

      const pulsingIcon = document.querySelector('.animate-pulse')
      expect(pulsingIcon).toBeInTheDocument()
    })
  })

  describe('error state', () => {
    it('shows error message when error is present', () => {
      const message = createMockChatMessage({
        role: 'assistant',
        error: 'Failed to get AI response',
      })

      render(<ChatMessage message={message} />)

      expect(screen.getByText('Failed to get AI response')).toBeInTheDocument()
    })

    it('shows "Error" label', () => {
      const message = createMockChatMessage({
        role: 'assistant',
        error: 'Network error',
      })

      render(<ChatMessage message={message} />)

      expect(screen.getByText('Error')).toBeInTheDocument()
    })

    it('shows destructive styling for error', () => {
      const message = createMockChatMessage({
        role: 'assistant',
        error: 'Error occurred',
      })

      render(<ChatMessage message={message} />)

      const errorContainer = document.querySelector('.bg-destructive\\/10')
      expect(errorContainer).toBeInTheDocument()
    })
  })

  describe('council deliberation', () => {
    it('shows council deliberation toggle for assistant message with deliberation', () => {
      const deliberation = createMockDeliberation()
      const message = createMockChatMessage({
        role: 'assistant',
        councilDeliberation: deliberation,
      })

      render(<ChatMessage message={message} />)

      expect(screen.getByText(/Council Deliberation/)).toBeInTheDocument()
    })

    it('shows provider count in deliberation header', () => {
      const deliberation = createMockDeliberation()
      const message = createMockChatMessage({
        role: 'assistant',
        councilDeliberation: deliberation,
      })

      render(<ChatMessage message={message} />)

      // "(3 stages)" should be visible
      expect(screen.getByText(/3 stages/)).toBeInTheDocument()
    })

    it('shows total duration in deliberation header', () => {
      const deliberation = createMockDeliberation()
      const message = createMockChatMessage({
        role: 'assistant',
        councilDeliberation: deliberation,
      })

      render(<ChatMessage message={message} />)

      // Duration should be visible (e.g., "2.5s")
      expect(screen.getByText(/\d+\.\d+s/)).toBeInTheDocument()
    })

    it('expands deliberation on click', async () => {
      const user = userEvent.setup()
      const deliberation = createMockDeliberation()
      const message = createMockChatMessage({
        role: 'assistant',
        councilDeliberation: deliberation,
      })

      render(<ChatMessage message={message} />)

      const trigger = screen.getByText(/Council Deliberation/)
      await user.click(trigger)

      // Stage views should appear
      expect(screen.getByText('Stage 1: AI Responses')).toBeInTheDocument()
      expect(screen.getByText('Stage 2: Peer Rankings')).toBeInTheDocument()
      expect(screen.getByText('Stage 3: Final Synthesis')).toBeInTheDocument()
    })

    it('shows cost information when expanded', async () => {
      const user = userEvent.setup()
      const deliberation = createMockDeliberation({
        total_cost_usd: 0.0125,
      })
      const message = createMockChatMessage({
        role: 'assistant',
        councilDeliberation: deliberation,
      })

      render(<ChatMessage message={message} />)

      const trigger = screen.getByText(/Council Deliberation/)
      await user.click(trigger)

      expect(screen.getByText(/Cost: \$0\.0125/)).toBeInTheDocument()
    })

    it('shows providers used when expanded', async () => {
      const user = userEvent.setup()
      const deliberation = createMockDeliberation({
        providers_used: ['Claude', 'OpenAI', 'Gemini'],
      })
      const message = createMockChatMessage({
        role: 'assistant',
        councilDeliberation: deliberation,
      })

      render(<ChatMessage message={message} />)

      const trigger = screen.getByText(/Council Deliberation/)
      await user.click(trigger)

      expect(screen.getByText(/Providers: Claude, OpenAI, Gemini/)).toBeInTheDocument()
    })

    it('calls onApplyRecommendation when provided and apply is clicked', async () => {
      const user = userEvent.setup()
      const onApplyRecommendation = vi.fn()
      const deliberation = createMockDeliberation()
      const message = createMockChatMessage({
        role: 'assistant',
        councilDeliberation: deliberation,
      })

      render(<ChatMessage message={message} onApplyRecommendation={onApplyRecommendation} />)

      // Expand deliberation
      const trigger = screen.getByText(/Council Deliberation/)
      await user.click(trigger)

      // Stage3View should have Apply button
      const applyButton = screen.getByRole('button', { name: /Apply Recommendation/i })
      await user.click(applyButton)

      expect(onApplyRecommendation).toHaveBeenCalledTimes(1)
    })
  })

  describe('accessibility', () => {
    it('council deliberation trigger has aria-label', () => {
      const deliberation = createMockDeliberation()
      const message = createMockChatMessage({
        role: 'assistant',
        councilDeliberation: deliberation,
      })

      render(<ChatMessage message={message} />)

      const trigger = screen.getByLabelText(/Toggle Council Deliberation/i)
      expect(trigger).toBeInTheDocument()
    })

    it('message content is readable by screen readers', () => {
      const message = createMockChatMessage({
        role: 'user',
        content: 'Accessible content test',
      })

      render(<ChatMessage message={message} />)

      // Content should be directly accessible text
      expect(screen.getByText('Accessible content test')).toBeInTheDocument()
    })
  })

  describe('without council deliberation', () => {
    it('does not show deliberation section for messages without deliberation', () => {
      const message = createMockChatMessage({
        role: 'assistant',
        councilDeliberation: undefined,
      })

      render(<ChatMessage message={message} />)

      expect(screen.queryByText(/Council Deliberation/)).not.toBeInTheDocument()
    })
  })
})
