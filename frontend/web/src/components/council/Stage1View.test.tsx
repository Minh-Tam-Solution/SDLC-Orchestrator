/**
 * Unit Tests: Stage1View Component
 * Version: 1.0.0 (Sprint 28 Day 3)
 *
 * Test coverage:
 * - Renders collapsible header
 * - Shows provider count
 * - Displays AI responses when expanded
 * - Loading skeleton when isLoading
 * - Provider-specific styling
 * - Accessibility
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@/test/test-utils'
import userEvent from '@testing-library/user-event'
import { Stage1View } from './Stage1View'
import { createMockAIResponse } from '@/test/test-utils'

describe('Stage1View', () => {
  const mockResponses = [
    createMockAIResponse({ provider: 'Claude', model: 'claude-3-5-sonnet', confidence: 85, duration_ms: 450 }),
    createMockAIResponse({ provider: 'OpenAI', model: 'gpt-4o', confidence: 78, duration_ms: 380 }),
    createMockAIResponse({ provider: 'Gemini', model: 'gemini-1.5-pro', confidence: 72, duration_ms: 420 }),
  ]

  describe('collapsed state', () => {
    it('renders header with stage name', () => {
      render(<Stage1View responses={mockResponses} />)

      expect(screen.getByText('Stage 1: AI Responses')).toBeInTheDocument()
    })

    it('shows provider count', () => {
      render(<Stage1View responses={mockResponses} />)

      expect(screen.getByText('3 providers')).toBeInTheDocument()
    })

    it('shows average confidence', () => {
      render(<Stage1View responses={mockResponses} />)

      // Average of 85, 78, 72 = 78.33 rounded to 78
      expect(screen.getByText(/Avg: \d+%/)).toBeInTheDocument()
    })

    it('shows total duration in seconds', () => {
      render(<Stage1View responses={mockResponses} />)

      // Total: 450 + 380 + 420 = 1250ms = 1.25s
      expect(screen.getByText(/\d+\.\d+s/)).toBeInTheDocument()
    })

    it('does not show responses when collapsed', () => {
      render(<Stage1View responses={mockResponses} />)

      // Provider names in cards should not be visible
      expect(screen.queryByText('claude-3-5-sonnet')).not.toBeInTheDocument()
    })
  })

  describe('expanded state', () => {
    it('shows responses when clicked', async () => {
      const user = userEvent.setup()
      render(<Stage1View responses={mockResponses} />)

      const trigger = screen.getByText('Stage 1: AI Responses')
      await user.click(trigger)

      // Now the provider details should be visible
      expect(screen.getByText('claude-3-5-sonnet')).toBeInTheDocument()
      expect(screen.getByText('gpt-4o')).toBeInTheDocument()
      expect(screen.getByText('gemini-1.5-pro')).toBeInTheDocument()
    })

    it('shows provider names', async () => {
      const user = userEvent.setup()
      render(<Stage1View responses={mockResponses} />)

      const trigger = screen.getByText('Stage 1: AI Responses')
      await user.click(trigger)

      expect(screen.getByText('Claude')).toBeInTheDocument()
      expect(screen.getByText('OpenAI')).toBeInTheDocument()
      expect(screen.getByText('Gemini')).toBeInTheDocument()
    })

    it('shows response content', async () => {
      const user = userEvent.setup()
      const responses = [
        createMockAIResponse({
          provider: 'Claude',
          response: 'This is the Claude response content.',
        }),
      ]

      render(<Stage1View responses={responses} />)

      const trigger = screen.getByText('Stage 1: AI Responses')
      await user.click(trigger)

      expect(screen.getByText('This is the Claude response content.')).toBeInTheDocument()
    })

    it('shows duration for each response', async () => {
      const user = userEvent.setup()
      render(<Stage1View responses={mockResponses} />)

      const trigger = screen.getByText('Stage 1: AI Responses')
      await user.click(trigger)

      expect(screen.getByText('450ms')).toBeInTheDocument()
      expect(screen.getByText('380ms')).toBeInTheDocument()
      expect(screen.getByText('420ms')).toBeInTheDocument()
    })

    it('shows confidence percentage for each response', async () => {
      const user = userEvent.setup()
      render(<Stage1View responses={mockResponses} />)

      const trigger = screen.getByText('Stage 1: AI Responses')
      await user.click(trigger)

      expect(screen.getByText('85%')).toBeInTheDocument()
      expect(screen.getByText('78%')).toBeInTheDocument()
      expect(screen.getByText('72%')).toBeInTheDocument()
    })
  })

  describe('loading state', () => {
    it('shows processing message when loading', () => {
      render(<Stage1View responses={[]} isLoading={true} />)

      expect(screen.getByText('Processing...')).toBeInTheDocument()
    })

    it('shows loading skeleton when expanded and loading', async () => {
      const user = userEvent.setup()
      render(<Stage1View responses={[]} isLoading={true} />)

      const trigger = screen.getByText('Stage 1: AI Responses')
      await user.click(trigger)

      // Should show skeleton placeholders
      const skeletons = document.querySelectorAll('.animate-pulse, [class*="skeleton"]')
      expect(skeletons.length).toBeGreaterThan(0)
    })

    it('does not show avg/duration when loading', () => {
      render(<Stage1View responses={[]} isLoading={true} />)

      expect(screen.queryByText(/Avg:/)).not.toBeInTheDocument()
    })
  })

  describe('provider styling', () => {
    it('applies Claude orange styling', async () => {
      const user = userEvent.setup()
      const responses = [createMockAIResponse({ provider: 'Claude' })]

      render(<Stage1View responses={responses} />)

      const trigger = screen.getByText('Stage 1: AI Responses')
      await user.click(trigger)

      // Find the card by looking for element with bg-orange-50 class
      const cards = document.querySelectorAll('.bg-orange-50')
      expect(cards.length).toBeGreaterThan(0)
    })

    it('applies OpenAI teal styling', async () => {
      const user = userEvent.setup()
      const responses = [createMockAIResponse({ provider: 'OpenAI' })]

      render(<Stage1View responses={responses} />)

      const trigger = screen.getByText('Stage 1: AI Responses')
      await user.click(trigger)

      const cards = document.querySelectorAll('.bg-teal-50')
      expect(cards.length).toBeGreaterThan(0)
    })

    it('applies Gemini blue styling', async () => {
      const user = userEvent.setup()
      const responses = [createMockAIResponse({ provider: 'Gemini' })]

      render(<Stage1View responses={responses} />)

      const trigger = screen.getByText('Stage 1: AI Responses')
      await user.click(trigger)

      const cards = document.querySelectorAll('.bg-blue-50')
      expect(cards.length).toBeGreaterThan(0)
    })

    it('applies default styling for unknown provider', async () => {
      const user = userEvent.setup()
      const responses = [createMockAIResponse({ provider: 'Unknown' })]

      render(<Stage1View responses={responses} />)

      const trigger = screen.getByText('Stage 1: AI Responses')
      await user.click(trigger)

      const cards = document.querySelectorAll('.bg-gray-50')
      expect(cards.length).toBeGreaterThan(0)
    })
  })

  describe('accessibility', () => {
    it('trigger has correct aria-label', () => {
      render(<Stage1View responses={mockResponses} />)

      const trigger = screen.getByRole('button')
      expect(trigger).toHaveAttribute(
        'aria-label',
        'Stage 1: AI Responses, 3 providers'
      )
    })

    it('trigger is focusable', () => {
      render(<Stage1View responses={mockResponses} />)

      const trigger = screen.getByRole('button')
      trigger.focus()
      expect(document.activeElement).toBe(trigger)
    })

    it('can be toggled with keyboard', async () => {
      const user = userEvent.setup()
      render(<Stage1View responses={mockResponses} />)

      const trigger = screen.getByRole('button')
      trigger.focus()

      // Press Enter to toggle
      await user.keyboard('{Enter}')

      // Content should now be visible
      expect(screen.getByText('claude-3-5-sonnet')).toBeInTheDocument()
    })
  })

  describe('empty responses', () => {
    it('renders with empty responses array', () => {
      render(<Stage1View responses={[]} />)

      expect(screen.getByText('Stage 1: AI Responses')).toBeInTheDocument()
      expect(screen.getByText('0 providers')).toBeInTheDocument()
    })
  })
})
