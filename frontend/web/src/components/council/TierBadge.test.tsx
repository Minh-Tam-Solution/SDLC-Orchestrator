/**
 * Unit Tests: TierBadge Component
 * Version: 1.0.0 (Sprint 28 Day 3)
 *
 * Test coverage:
 * - Renders all three tiers correctly
 * - Size variants work properly
 * - Label visibility toggle
 * - Accessibility attributes
 * - Coverage display in lg size
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@/test/test-utils'
import { TierBadge } from './TierBadge'
import { TIER_CONFIGS, ComplianceTier } from '@/types/council'

describe('TierBadge', () => {
  describe('tier rendering', () => {
    it.each<ComplianceTier>(['lite', 'standard', 'enterprise'])(
      'renders %s tier correctly',
      (tier) => {
        render(<TierBadge tier={tier} />)

        const badge = screen.getByRole('status')
        expect(badge).toBeInTheDocument()

        // Check label
        expect(screen.getByText(TIER_CONFIGS[tier].label)).toBeInTheDocument()

        // Check icon
        expect(screen.getByText(TIER_CONFIGS[tier].icon)).toBeInTheDocument()

        // Check aria-label
        expect(badge).toHaveAttribute(
          'aria-label',
          `${TIER_CONFIGS[tier].label} tier`
        )
      }
    )

    it('renders lite tier with green styling', () => {
      render(<TierBadge tier="lite" />)

      const badge = screen.getByRole('status')
      expect(badge).toHaveClass('bg-green-100')
      expect(badge).toHaveClass('border-green-300')
      expect(badge).toHaveClass('text-green-800')
    })

    it('renders standard tier with blue styling', () => {
      render(<TierBadge tier="standard" />)

      const badge = screen.getByRole('status')
      expect(badge).toHaveClass('bg-blue-100')
      expect(badge).toHaveClass('border-blue-300')
      expect(badge).toHaveClass('text-blue-800')
    })

    it('renders enterprise tier with amber styling', () => {
      render(<TierBadge tier="enterprise" />)

      const badge = screen.getByRole('status')
      expect(badge).toHaveClass('bg-amber-100')
      expect(badge).toHaveClass('border-amber-300')
      expect(badge).toHaveClass('text-amber-800')
    })
  })

  describe('size variants', () => {
    it('renders sm size correctly', () => {
      render(<TierBadge tier="standard" size="sm" />)

      const badge = screen.getByRole('status')
      expect(badge).toHaveClass('px-2', 'py-0.5', 'text-xs')
    })

    it('renders md size correctly (default)', () => {
      render(<TierBadge tier="standard" />)

      const badge = screen.getByRole('status')
      expect(badge).toHaveClass('px-3', 'py-1', 'text-sm')
    })

    it('renders lg size correctly with coverage', () => {
      render(<TierBadge tier="standard" size="lg" />)

      const badge = screen.getByRole('status')
      expect(badge).toHaveClass('px-4', 'py-2', 'text-base')

      // lg size should show coverage percentage
      expect(screen.getByText('80% coverage')).toBeInTheDocument()
    })

    it('shows different coverage for each tier in lg size', () => {
      const { rerender } = render(<TierBadge tier="lite" size="lg" />)
      expect(screen.getByText('70% coverage')).toBeInTheDocument()

      rerender(<TierBadge tier="standard" size="lg" />)
      expect(screen.getByText('80% coverage')).toBeInTheDocument()

      rerender(<TierBadge tier="enterprise" size="lg" />)
      expect(screen.getByText('85% coverage')).toBeInTheDocument()
    })
  })

  describe('label visibility', () => {
    it('shows label by default', () => {
      render(<TierBadge tier="standard" />)

      expect(screen.getByText('Standard')).toBeInTheDocument()
    })

    it('hides label when showLabel is false', () => {
      render(<TierBadge tier="standard" showLabel={false} />)

      expect(screen.queryByText('Standard')).not.toBeInTheDocument()
      // Icon should still be visible
      expect(screen.getByText('⚡')).toBeInTheDocument()
    })

    it('shows label when showLabel is true', () => {
      render(<TierBadge tier="enterprise" showLabel={true} />)

      expect(screen.getByText('Enterprise')).toBeInTheDocument()
    })
  })

  describe('accessibility', () => {
    it('has role="status"', () => {
      render(<TierBadge tier="standard" />)

      const badge = screen.getByRole('status')
      expect(badge).toBeInTheDocument()
    })

    it('has correct aria-label for each tier', () => {
      const { rerender } = render(<TierBadge tier="lite" />)
      expect(screen.getByRole('status')).toHaveAttribute('aria-label', 'Lite tier')

      rerender(<TierBadge tier="standard" />)
      expect(screen.getByRole('status')).toHaveAttribute('aria-label', 'Standard tier')

      rerender(<TierBadge tier="enterprise" />)
      expect(screen.getByRole('status')).toHaveAttribute('aria-label', 'Enterprise tier')
    })

    it('hides icon from screen readers', () => {
      render(<TierBadge tier="standard" />)

      // The icon span should have aria-hidden="true"
      const icon = screen.getByText('⚡')
      expect(icon).toHaveAttribute('aria-hidden', 'true')
    })
  })

  describe('custom className', () => {
    it('applies custom className', () => {
      render(<TierBadge tier="standard" className="custom-class" />)

      const badge = screen.getByRole('status')
      expect(badge).toHaveClass('custom-class')
    })

    it('merges custom className with default classes', () => {
      render(<TierBadge tier="standard" className="custom-class" />)

      const badge = screen.getByRole('status')
      expect(badge).toHaveClass('custom-class')
      expect(badge).toHaveClass('rounded-md')
      expect(badge).toHaveClass('bg-blue-100')
    })
  })
})
