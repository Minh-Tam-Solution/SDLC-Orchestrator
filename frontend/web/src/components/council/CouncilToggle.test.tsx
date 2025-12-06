/**
 * Unit Tests: CouncilToggle Component
 * Version: 1.0.0 (Sprint 28 Day 3)
 *
 * Test coverage:
 * - Toggle rendering in enabled/disabled states
 * - onChange callback triggers correctly
 * - Description text updates based on state
 * - Accessibility attributes
 * - Disabled state behavior
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@/test/test-utils'
import userEvent from '@testing-library/user-event'
import { CouncilToggle } from './CouncilToggle'

describe('CouncilToggle', () => {
  describe('rendering', () => {
    it('renders with label', () => {
      render(<CouncilToggle enabled={false} onChange={() => {}} />)

      expect(screen.getByText('Council Mode')).toBeInTheDocument()
    })

    it('renders switch element', () => {
      render(<CouncilToggle enabled={false} onChange={() => {}} />)

      const toggle = screen.getByRole('switch')
      expect(toggle).toBeInTheDocument()
    })

    it('renders unchecked when enabled is false', () => {
      render(<CouncilToggle enabled={false} onChange={() => {}} />)

      const toggle = screen.getByRole('switch')
      expect(toggle).toHaveAttribute('aria-checked', 'false')
    })

    it('renders checked when enabled is true', () => {
      render(<CouncilToggle enabled={true} onChange={() => {}} />)

      const toggle = screen.getByRole('switch')
      expect(toggle).toHaveAttribute('aria-checked', 'true')
    })
  })

  describe('description text', () => {
    it('shows single AI description when disabled', () => {
      render(<CouncilToggle enabled={false} onChange={() => {}} />)

      expect(screen.getByText('Single AI for faster responses')).toBeInTheDocument()
    })

    it('shows 3 AI description when enabled', () => {
      render(<CouncilToggle enabled={true} onChange={() => {}} />)

      expect(screen.getByText('3 AI providers for best answer')).toBeInTheDocument()
    })

    it('updates description when state changes', () => {
      const { rerender } = render(<CouncilToggle enabled={false} onChange={() => {}} />)

      expect(screen.getByText('Single AI for faster responses')).toBeInTheDocument()

      rerender(<CouncilToggle enabled={true} onChange={() => {}} />)

      expect(screen.getByText('3 AI providers for best answer')).toBeInTheDocument()
    })
  })

  describe('onChange callback', () => {
    it('calls onChange with true when toggling from off to on', async () => {
      const user = userEvent.setup()
      const handleChange = vi.fn()

      render(<CouncilToggle enabled={false} onChange={handleChange} />)

      const toggle = screen.getByRole('switch')
      await user.click(toggle)

      expect(handleChange).toHaveBeenCalledTimes(1)
      expect(handleChange).toHaveBeenCalledWith(true)
    })

    it('calls onChange with false when toggling from on to off', async () => {
      const user = userEvent.setup()
      const handleChange = vi.fn()

      render(<CouncilToggle enabled={true} onChange={handleChange} />)

      const toggle = screen.getByRole('switch')
      await user.click(toggle)

      expect(handleChange).toHaveBeenCalledTimes(1)
      expect(handleChange).toHaveBeenCalledWith(false)
    })
  })

  describe('disabled state', () => {
    it('is not disabled by default', () => {
      render(<CouncilToggle enabled={false} onChange={() => {}} />)

      const toggle = screen.getByRole('switch')
      expect(toggle).not.toBeDisabled()
    })

    it('can be disabled', () => {
      render(<CouncilToggle enabled={false} onChange={() => {}} disabled={true} />)

      const toggle = screen.getByRole('switch')
      expect(toggle).toBeDisabled()
    })

    it('does not call onChange when disabled', async () => {
      const user = userEvent.setup()
      const handleChange = vi.fn()

      render(<CouncilToggle enabled={false} onChange={handleChange} disabled={true} />)

      const toggle = screen.getByRole('switch')
      await user.click(toggle)

      expect(handleChange).not.toHaveBeenCalled()
    })

    it('applies disabled styling', () => {
      render(<CouncilToggle enabled={false} onChange={() => {}} disabled={true} />)

      const toggle = screen.getByRole('switch')
      expect(toggle).toHaveClass('disabled:opacity-50')
    })
  })

  describe('accessibility', () => {
    it('has correct aria-label', () => {
      render(<CouncilToggle enabled={false} onChange={() => {}} />)

      const toggle = screen.getByRole('switch')
      expect(toggle).toHaveAttribute('aria-label', 'Council Mode toggle')
    })

    it('has aria-describedby pointing to description', () => {
      render(<CouncilToggle enabled={false} onChange={() => {}} />)

      const toggle = screen.getByRole('switch')
      expect(toggle).toHaveAttribute('aria-describedby', 'council-mode-description')

      // Verify the description exists
      const description = document.getElementById('council-mode-description')
      expect(description).toBeInTheDocument()
    })

    it('label is associated with switch', () => {
      render(<CouncilToggle enabled={false} onChange={() => {}} />)

      const label = screen.getByText('Council Mode')
      expect(label).toHaveAttribute('for', 'council-toggle')

      const toggle = screen.getByRole('switch')
      expect(toggle).toHaveAttribute('id', 'council-toggle')
    })

    it('can be toggled via keyboard', async () => {
      const user = userEvent.setup()
      const handleChange = vi.fn()

      render(<CouncilToggle enabled={false} onChange={handleChange} />)

      const toggle = screen.getByRole('switch')
      toggle.focus()

      // Press space to toggle
      await user.keyboard(' ')

      expect(handleChange).toHaveBeenCalledTimes(1)
      expect(handleChange).toHaveBeenCalledWith(true)
    })
  })

  describe('custom className', () => {
    it('applies custom className to wrapper', () => {
      render(
        <CouncilToggle
          enabled={false}
          onChange={() => {}}
          className="custom-class"
        />
      )

      const wrapper = screen.getByText('Council Mode').closest('div')?.parentElement
      expect(wrapper).toHaveClass('custom-class')
    })
  })
})
