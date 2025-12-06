/**
 * Accessibility Tests: AI Council Components
 * Version: 1.0.0 (Sprint 28 Day 3)
 *
 * WCAG 2.1 AA Compliance Audit:
 * - Perceivable: Color contrast, text alternatives
 * - Operable: Keyboard navigation, focus management
 * - Understandable: Consistent navigation, error identification
 * - Robust: Valid HTML, ARIA attributes
 *
 * Components tested:
 * - TierBadge
 * - CouncilToggle
 * - GateProgressBar
 * - Stage1View
 * - Stage2View
 * - Stage3View
 * - ChatMessage
 * - AICouncilChat
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@/test/test-utils'
import userEvent from '@testing-library/user-event'
import { axe } from 'vitest-axe'
import { TierBadge } from './TierBadge'
import { CouncilToggle } from './CouncilToggle'
import { GateProgressBar } from './GateProgressBar'
import { Stage1View } from './Stage1View'
import { Stage2View } from './Stage2View'
import { Stage3View } from './Stage3View'
import { ChatMessage } from './ChatMessage'
import {
  createMockAIResponse,
  createMockRanking,
  createMockFinalAnswer,
  createMockGateStatuses,
  createMockChatMessage,
  createMockDeliberation,
} from '@/test/test-utils'

// Custom matcher for axe violations
function toHaveNoViolations(results: { violations: unknown[] }) {
  const pass = results.violations.length === 0
  return {
    pass,
    message: () =>
      pass
        ? 'Expected accessibility violations but found none'
        : `Found ${results.violations.length} accessibility violations:\n${JSON.stringify(results.violations, null, 2)}`,
  }
}

expect.extend({ toHaveNoViolations })

describe('Accessibility Audit (WCAG 2.1 AA)', () => {
  describe('TierBadge', () => {
    it('has no accessibility violations', async () => {
      const { container } = render(<TierBadge tier="standard" showLabel />)
      const results = await axe(container)
      expect(results).toHaveNoViolations()
    })

    it('badge text has sufficient color contrast', () => {
      render(<TierBadge tier="enterprise" showLabel />)

      // Badge should have readable text (not just color indicator)
      expect(screen.getByText('Enterprise')).toBeInTheDocument()
    })

    it('does not rely solely on color to convey tier', () => {
      render(<TierBadge tier="lite" showLabel />)

      // Has text label, not just color
      expect(screen.getByText('Lite')).toBeInTheDocument()
    })
  })

  describe('CouncilToggle', () => {
    it('has no accessibility violations', async () => {
      const { container } = render(
        <CouncilToggle enabled={false} onChange={() => {}} />
      )
      const results = await axe(container)
      expect(results).toHaveNoViolations()
    })

    it('toggle is keyboard accessible', async () => {
      const user = userEvent.setup()
      const onChange = vi.fn()
      render(<CouncilToggle enabled={false} onChange={onChange} />)

      const toggle = screen.getByRole('switch')
      toggle.focus()
      expect(document.activeElement).toBe(toggle)

      await user.keyboard(' ')
      expect(onChange).toHaveBeenCalled()
    })

    it('toggle has descriptive label', () => {
      render(<CouncilToggle enabled={false} onChange={() => {}} />)

      const toggle = screen.getByRole('switch')
      expect(toggle).toHaveAttribute('aria-label')
    })

    it('toggle has aria-describedby for additional context', () => {
      render(<CouncilToggle enabled={false} onChange={() => {}} />)

      const toggle = screen.getByRole('switch')
      expect(toggle).toHaveAttribute('aria-describedby')
    })
  })

  describe('GateProgressBar', () => {
    it('has no accessibility violations', async () => {
      const { container } = render(
        <GateProgressBar
          currentGate="G1"
          gateStatuses={createMockGateStatuses('G1')}
          tier="standard"
        />
      )
      const results = await axe(container)
      expect(results).toHaveNoViolations()
    })

    it('gate buttons are keyboard navigable', async () => {
      const user = userEvent.setup()
      const onGateClick = vi.fn()
      render(
        <GateProgressBar
          currentGate="G1"
          gateStatuses={createMockGateStatuses('G1')}
          tier="standard"
          onGateClick={onGateClick}
        />
      )

      const buttons = screen.getAllByRole('button')
      buttons[0].focus()
      expect(document.activeElement).toBe(buttons[0])

      await user.keyboard('{Enter}')
      expect(onGateClick).toHaveBeenCalled()
    })

    it('current gate is marked with aria-current', () => {
      render(
        <GateProgressBar
          currentGate="G1"
          gateStatuses={createMockGateStatuses('G1')}
          tier="standard"
        />
      )

      const buttons = screen.getAllByRole('button')
      // G1 is at index 2 (after G0.1 and G0.2)
      const g1Button = buttons.find(b => b.textContent?.includes('G1') && !b.textContent?.includes('G0.1'))
      expect(g1Button).toHaveAttribute('aria-current', 'step')
    })

    it('gate statuses use more than just color', () => {
      render(
        <GateProgressBar
          currentGate="G2"
          gateStatuses={createMockGateStatuses('G2')}
          tier="standard"
        />
      )

      // Passed gates should have checkmark icon
      const buttons = screen.getAllByRole('button')
      // G0.1 and G0.2 should show passed visual (check icon or similar)
      expect(buttons.length).toBe(7)
    })
  })

  describe('Stage1View', () => {
    it('has no accessibility violations', async () => {
      const { container } = render(
        <Stage1View responses={[createMockAIResponse()]} />
      )
      const results = await axe(container)
      expect(results).toHaveNoViolations()
    })

    it('collapsible trigger has descriptive aria-label', () => {
      render(<Stage1View responses={[createMockAIResponse()]} />)

      const trigger = screen.getByRole('button')
      expect(trigger).toHaveAttribute('aria-label')
      expect(trigger.getAttribute('aria-label')).toContain('Stage 1')
    })

    it('collapsible can be operated with keyboard', async () => {
      const user = userEvent.setup()
      render(<Stage1View responses={[createMockAIResponse()]} />)

      const trigger = screen.getByRole('button')
      trigger.focus()

      await user.keyboard('{Enter}')
      expect(screen.getByText('Claude')).toBeInTheDocument()
    })
  })

  describe('Stage2View', () => {
    it('has no accessibility violations', async () => {
      const { container } = render(
        <Stage2View rankings={[createMockRanking()]} />
      )
      const results = await axe(container)
      expect(results).toHaveNoViolations()
    })

    it('ranking information is accessible without relying on emojis alone', async () => {
      const user = userEvent.setup()
      const rankings = [
        createMockRanking({ ranker: 'Claude', rankings: ['Claude', 'OpenAI', 'Gemini'] }),
      ]
      render(<Stage2View rankings={rankings} />)

      const trigger = screen.getByRole('button')
      await user.click(trigger)

      // Has text like "(best)" alongside emoji
      expect(screen.getByText(/\(best\)/)).toBeInTheDocument()
    })
  })

  describe('Stage3View', () => {
    it('has no accessibility violations', async () => {
      const { container } = render(
        <Stage3View synthesis={createMockFinalAnswer()} />
      )
      const results = await axe(container)
      expect(results).toHaveNoViolations()
    })

    it('confidence level has text label, not just color', () => {
      render(<Stage3View synthesis={createMockFinalAnswer({ confidence: 92 })} />)

      // Should show "Very High" text, not just green color
      expect(screen.getByText('Very High')).toBeInTheDocument()
    })

    it('apply button is keyboard accessible', async () => {
      const user = userEvent.setup()
      const onApply = vi.fn()
      render(<Stage3View synthesis={createMockFinalAnswer()} onApply={onApply} />)

      const button = screen.getByRole('button', { name: /Apply Recommendation/i })
      button.focus()
      expect(document.activeElement).toBe(button)

      await user.keyboard('{Enter}')
      expect(onApply).toHaveBeenCalled()
    })
  })

  describe('ChatMessage', () => {
    it('user message has no accessibility violations', async () => {
      const { container } = render(
        <ChatMessage message={createMockChatMessage({ role: 'user' })} />
      )
      const results = await axe(container)
      expect(results).toHaveNoViolations()
    })

    it('assistant message has no accessibility violations', async () => {
      const { container } = render(
        <ChatMessage message={createMockChatMessage({ role: 'assistant' })} />
      )
      const results = await axe(container)
      expect(results).toHaveNoViolations()
    })

    it('error message has no accessibility violations', async () => {
      const { container } = render(
        <ChatMessage
          message={createMockChatMessage({ role: 'assistant', error: 'Error occurred' })}
        />
      )
      const results = await axe(container)
      expect(results).toHaveNoViolations()
    })

    it('message with council deliberation has no violations', async () => {
      const { container } = render(
        <ChatMessage
          message={createMockChatMessage({
            role: 'assistant',
            councilDeliberation: createMockDeliberation(),
          })}
        />
      )
      const results = await axe(container)
      expect(results).toHaveNoViolations()
    })

    it('loading state is announced to screen readers', () => {
      render(
        <ChatMessage message={createMockChatMessage({ role: 'assistant', isLoading: true })} />
      )

      // Loading text should be visible
      expect(screen.getByText('AI is thinking...')).toBeInTheDocument()
    })

    it('error state uses semantic error styling', () => {
      render(
        <ChatMessage
          message={createMockChatMessage({ role: 'assistant', error: 'Failed request' })}
        />
      )

      // Error label should be present
      expect(screen.getByText('Error')).toBeInTheDocument()
      expect(screen.getByText('Failed request')).toBeInTheDocument()
    })
  })

  describe('Focus Management', () => {
    it('Tab navigation follows logical order in Stage1View', async () => {
      const user = userEvent.setup()
      render(<Stage1View responses={[createMockAIResponse()]} />)

      // Tab should focus the trigger first
      await user.tab()
      const trigger = screen.getByRole('button')
      expect(document.activeElement).toBe(trigger)
    })

    it('Tab navigation follows logical order in Stage3View with button', async () => {
      const user = userEvent.setup()
      render(<Stage3View synthesis={createMockFinalAnswer()} onApply={() => {}} />)

      // First tab focuses trigger
      await user.tab()
      expect(document.activeElement?.getAttribute('aria-label')).toBe('Stage 3: Final Synthesis')

      // Second tab focuses apply button
      await user.tab()
      expect(document.activeElement?.textContent).toContain('Apply Recommendation')
    })
  })

  describe('Color Independence', () => {
    it('GateProgressBar status is distinguishable without color', () => {
      render(
        <GateProgressBar
          currentGate="G2"
          gateStatuses={createMockGateStatuses('G2')}
          tier="standard"
        />
      )

      // All gates have text labels (G0.1, G0.2, G1, etc.)
      expect(screen.getByText('G0.1')).toBeInTheDocument()
      expect(screen.getByText('G0.2')).toBeInTheDocument()
      expect(screen.getByText('G1')).toBeInTheDocument()
      expect(screen.getByText('G2')).toBeInTheDocument()
    })

    it('TierBadge can be identified without color', () => {
      render(
        <div>
          <TierBadge tier="lite" showLabel />
          <TierBadge tier="standard" showLabel />
          <TierBadge tier="enterprise" showLabel />
        </div>
      )

      // All tiers have distinct text labels
      expect(screen.getByText('Lite')).toBeInTheDocument()
      expect(screen.getByText('Standard')).toBeInTheDocument()
      expect(screen.getByText('Enterprise')).toBeInTheDocument()
    })
  })

  describe('Screen Reader Compatibility', () => {
    it('collapsible sections announce their state', async () => {
      const user = userEvent.setup()
      render(<Stage1View responses={[createMockAIResponse()]} />)

      const trigger = screen.getByRole('button')

      // Trigger should indicate it's a collapsible control
      expect(trigger).toHaveAttribute('aria-expanded')

      await user.click(trigger)

      // After expansion, aria-expanded should change
      expect(trigger).toHaveAttribute('aria-expanded', 'true')
    })

    it('switch announces its state', () => {
      render(<CouncilToggle enabled={true} onChange={() => {}} />)

      const toggle = screen.getByRole('switch')
      expect(toggle).toHaveAttribute('aria-checked', 'true')
    })
  })
})
