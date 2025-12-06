/**
 * Unit Tests: Stage3View Component
 * Version: 1.0.0 (Sprint 28 Day 3)
 *
 * Test coverage:
 * - Renders collapsible header (expanded by default)
 * - Shows confidence score
 * - Displays reasoning
 * - Shows suggested action when present
 * - Apply button functionality
 * - Loading skeleton
 * - Confidence levels (Very High, High, Medium, Low)
 * - Accessibility
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@/test/test-utils'
import userEvent from '@testing-library/user-event'
import { Stage3View } from './Stage3View'
import { createMockFinalAnswer } from '@/test/test-utils'

describe('Stage3View', () => {
  const mockSynthesis = createMockFinalAnswer({
    answer: 'The recommended approach is to use authentication tokens.',
    confidence: 92,
    reasoning: 'Based on cross-evaluation from 3 AI providers, authentication tokens provide the best security.',
    suggested_action: 'Implement JWT tokens with 15-minute expiry',
  })

  describe('default expanded state', () => {
    it('renders header with stage name', () => {
      render(<Stage3View synthesis={mockSynthesis} />)

      expect(screen.getByText('Stage 3: Final Synthesis')).toBeInTheDocument()
    })

    it('shows confidence percentage in header', () => {
      render(<Stage3View synthesis={mockSynthesis} />)

      expect(screen.getByText('92% confidence')).toBeInTheDocument()
    })

    it('is expanded by default', () => {
      render(<Stage3View synthesis={mockSynthesis} />)

      // Content should be visible by default
      expect(screen.getByText('Confidence Score')).toBeInTheDocument()
      expect(screen.getByText('Reasoning')).toBeInTheDocument()
    })

    it('shows reasoning content', () => {
      render(<Stage3View synthesis={mockSynthesis} />)

      expect(screen.getByText(/Based on cross-evaluation from 3 AI providers/)).toBeInTheDocument()
    })

    it('shows suggested action when present', () => {
      render(<Stage3View synthesis={mockSynthesis} />)

      expect(screen.getByText('Suggested Action')).toBeInTheDocument()
      expect(screen.getByText('Implement JWT tokens with 15-minute expiry')).toBeInTheDocument()
    })
  })

  describe('collapsed state', () => {
    it('hides content when collapsed', async () => {
      const user = userEvent.setup()
      render(<Stage3View synthesis={mockSynthesis} />)

      // Click to collapse
      const trigger = screen.getByText('Stage 3: Final Synthesis')
      await user.click(trigger)

      expect(screen.queryByText('Confidence Score')).not.toBeInTheDocument()
      expect(screen.queryByText('Reasoning')).not.toBeInTheDocument()
    })

    it('shows content again when re-expanded', async () => {
      const user = userEvent.setup()
      render(<Stage3View synthesis={mockSynthesis} />)

      // Collapse
      const trigger = screen.getByText('Stage 3: Final Synthesis')
      await user.click(trigger)

      // Re-expand
      await user.click(trigger)

      expect(screen.getByText('Confidence Score')).toBeInTheDocument()
    })
  })

  describe('confidence levels', () => {
    it('shows Very High for confidence >= 90', () => {
      const synthesis = createMockFinalAnswer({ confidence: 92 })
      render(<Stage3View synthesis={synthesis} />)

      expect(screen.getByText('Very High')).toBeInTheDocument()
    })

    it('shows High for confidence >= 75', () => {
      const synthesis = createMockFinalAnswer({ confidence: 80 })
      render(<Stage3View synthesis={synthesis} />)

      expect(screen.getByText('High')).toBeInTheDocument()
    })

    it('shows Medium for confidence >= 50', () => {
      const synthesis = createMockFinalAnswer({ confidence: 60 })
      render(<Stage3View synthesis={synthesis} />)

      expect(screen.getByText('Medium')).toBeInTheDocument()
    })

    it('shows Low for confidence < 50', () => {
      const synthesis = createMockFinalAnswer({ confidence: 40 })
      render(<Stage3View synthesis={synthesis} />)

      expect(screen.getByText('Low')).toBeInTheDocument()
    })

    it('applies correct color class for Very High confidence', () => {
      const synthesis = createMockFinalAnswer({ confidence: 92 })
      render(<Stage3View synthesis={synthesis} />)

      const veryHighLabel = screen.getByText('Very High')
      expect(veryHighLabel).toHaveClass('text-green-700')
    })

    it('applies correct color class for Low confidence', () => {
      const synthesis = createMockFinalAnswer({ confidence: 30 })
      render(<Stage3View synthesis={synthesis} />)

      const lowLabel = screen.getByText('Low')
      expect(lowLabel).toHaveClass('text-red-700')
    })
  })

  describe('apply button', () => {
    it('does not show apply button when onApply is not provided', () => {
      render(<Stage3View synthesis={mockSynthesis} />)

      expect(screen.queryByRole('button', { name: /Apply Recommendation/i })).not.toBeInTheDocument()
    })

    it('shows apply button when onApply is provided', () => {
      const onApply = vi.fn()
      render(<Stage3View synthesis={mockSynthesis} onApply={onApply} />)

      expect(screen.getByRole('button', { name: /Apply Recommendation/i })).toBeInTheDocument()
    })

    it('calls onApply when button is clicked', async () => {
      const user = userEvent.setup()
      const onApply = vi.fn()
      render(<Stage3View synthesis={mockSynthesis} onApply={onApply} />)

      const applyButton = screen.getByRole('button', { name: /Apply Recommendation/i })
      await user.click(applyButton)

      expect(onApply).toHaveBeenCalledTimes(1)
    })
  })

  describe('loading state', () => {
    it('shows synthesizing message when loading', () => {
      render(<Stage3View synthesis={null} isLoading={true} />)

      expect(screen.getByText('Synthesizing...')).toBeInTheDocument()
    })

    it('shows loading skeleton when expanded and loading', () => {
      render(<Stage3View synthesis={null} isLoading={true} />)

      const skeletons = document.querySelectorAll('.animate-pulse, [class*="skeleton"]')
      expect(skeletons.length).toBeGreaterThan(0)
    })

    it('does not show confidence score when loading', () => {
      render(<Stage3View synthesis={null} isLoading={true} />)

      expect(screen.queryByText(/% confidence$/)).not.toBeInTheDocument()
    })
  })

  describe('no synthesis state', () => {
    it('shows no synthesis message when synthesis is null and not loading', () => {
      render(<Stage3View synthesis={null} />)

      expect(screen.getByText('No synthesis available')).toBeInTheDocument()
    })
  })

  describe('suggested action visibility', () => {
    it('does not show suggested action section when not provided', () => {
      const synthesis = createMockFinalAnswer({ suggested_action: undefined })
      render(<Stage3View synthesis={synthesis} />)

      expect(screen.queryByText('Suggested Action')).not.toBeInTheDocument()
    })
  })

  describe('accessibility', () => {
    it('trigger has correct aria-label', () => {
      render(<Stage3View synthesis={mockSynthesis} />)

      const trigger = screen.getByRole('button')
      expect(trigger).toHaveAttribute('aria-label', 'Stage 3: Final Synthesis')
    })

    it('can be toggled with keyboard', async () => {
      const user = userEvent.setup()
      render(<Stage3View synthesis={mockSynthesis} />)

      const trigger = screen.getByRole('button', { name: /Stage 3: Final Synthesis/i })
      trigger.focus()

      // Press Enter to collapse
      await user.keyboard('{Enter}')

      expect(screen.queryByText('Confidence Score')).not.toBeInTheDocument()

      // Press Enter again to expand
      await user.keyboard('{Enter}')

      await waitFor(() => {
        expect(screen.getByText('Confidence Score')).toBeInTheDocument()
      })
    })

    it('shows confidence percentage value', () => {
      render(<Stage3View synthesis={mockSynthesis} />)

      // Confidence value should be visible in text
      const confidenceTexts = screen.getAllByText('92%')
      expect(confidenceTexts.length).toBeGreaterThan(0)
    })
  })
})
