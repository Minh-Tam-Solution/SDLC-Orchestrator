/**
 * Unit Tests: SDLCTierBadge Component
 * Version: 1.0.0 (Sprint 30 Day 4)
 *
 * Test coverage:
 * - Renders all four SDLC tiers correctly
 * - Size variants work properly
 * - Label visibility toggle
 * - Accessibility attributes
 * - Required stages display in lg size
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@/test/test-utils'
import { SDLCTierBadge, getTierFromScore, getTierColorClasses } from './SDLCTierBadge'
import { SDLC_TIER_CONFIGS, SDLCTier } from '@/types/sdlcValidation'

describe('SDLCTierBadge', () => {
  describe('tier rendering', () => {
    it.each<SDLCTier>(['lite', 'standard', 'professional', 'enterprise'])(
      'renders %s tier correctly',
      (tier) => {
        render(<SDLCTierBadge tier={tier} />)

        const badge = screen.getByRole('status')
        expect(badge).toBeInTheDocument()

        // Check label
        expect(screen.getByText(SDLC_TIER_CONFIGS[tier].label)).toBeInTheDocument()

        // Check icon
        expect(screen.getByText(SDLC_TIER_CONFIGS[tier].icon)).toBeInTheDocument()
      }
    )

    it('renders lite tier with green styling', () => {
      render(<SDLCTierBadge tier="lite" />)

      const badge = screen.getByRole('status')
      expect(badge).toHaveClass('bg-green-100')
      expect(badge).toHaveClass('border-green-300')
      expect(badge).toHaveClass('text-green-800')
    })

    it('renders standard tier with blue styling', () => {
      render(<SDLCTierBadge tier="standard" />)

      const badge = screen.getByRole('status')
      expect(badge).toHaveClass('bg-blue-100')
      expect(badge).toHaveClass('border-blue-300')
      expect(badge).toHaveClass('text-blue-800')
    })

    it('renders professional tier with purple styling', () => {
      render(<SDLCTierBadge tier="professional" />)

      const badge = screen.getByRole('status')
      expect(badge).toHaveClass('bg-purple-100')
      expect(badge).toHaveClass('border-purple-300')
      expect(badge).toHaveClass('text-purple-800')
    })

    it('renders enterprise tier with amber styling', () => {
      render(<SDLCTierBadge tier="enterprise" />)

      const badge = screen.getByRole('status')
      expect(badge).toHaveClass('bg-amber-100')
      expect(badge).toHaveClass('border-amber-300')
      expect(badge).toHaveClass('text-amber-800')
    })
  })

  describe('size variants', () => {
    it('renders sm size correctly', () => {
      render(<SDLCTierBadge tier="standard" size="sm" />)

      const badge = screen.getByRole('status')
      expect(badge).toHaveClass('px-2', 'py-0.5', 'text-xs')
    })

    it('renders md size correctly (default)', () => {
      render(<SDLCTierBadge tier="standard" />)

      const badge = screen.getByRole('status')
      expect(badge).toHaveClass('px-3', 'py-1', 'text-sm')
    })

    it('renders lg size correctly with stages', () => {
      render(<SDLCTierBadge tier="standard" size="lg" />)

      const badge = screen.getByRole('status')
      expect(badge).toHaveClass('px-4', 'py-2', 'text-base')

      // lg size should show required stages
      expect(screen.getByText('8 stages')).toBeInTheDocument()
    })

    it('shows different stages for each tier in lg size', () => {
      const { rerender } = render(<SDLCTierBadge tier="lite" size="lg" />)
      expect(screen.getByText('5 stages')).toBeInTheDocument()

      rerender(<SDLCTierBadge tier="standard" size="lg" />)
      expect(screen.getByText('8 stages')).toBeInTheDocument()

      rerender(<SDLCTierBadge tier="professional" size="lg" />)
      expect(screen.getByText('10 stages')).toBeInTheDocument()

      rerender(<SDLCTierBadge tier="enterprise" size="lg" />)
      expect(screen.getByText('11 stages')).toBeInTheDocument()
    })
  })

  describe('label visibility', () => {
    it('shows label by default', () => {
      render(<SDLCTierBadge tier="standard" />)

      expect(screen.getByText('Standard')).toBeInTheDocument()
    })

    it('hides label when showLabel is false', () => {
      render(<SDLCTierBadge tier="standard" showLabel={false} />)

      expect(screen.queryByText('Standard')).not.toBeInTheDocument()
      // Icon should still be visible
      expect(screen.getByText('⚡')).toBeInTheDocument()
    })

    it('shows label when showLabel is true', () => {
      render(<SDLCTierBadge tier="enterprise" showLabel={true} />)

      expect(screen.getByText('Enterprise')).toBeInTheDocument()
    })
  })

  describe('accessibility', () => {
    it('has role="status"', () => {
      render(<SDLCTierBadge tier="standard" />)

      const badge = screen.getByRole('status')
      expect(badge).toBeInTheDocument()
    })

    it('has correct aria-label for each tier', () => {
      const { rerender } = render(<SDLCTierBadge tier="lite" />)
      expect(screen.getByRole('status')).toHaveAttribute(
        'aria-label',
        'Lite tier - requires 5 stages'
      )

      rerender(<SDLCTierBadge tier="standard" />)
      expect(screen.getByRole('status')).toHaveAttribute(
        'aria-label',
        'Standard tier - requires 8 stages'
      )

      rerender(<SDLCTierBadge tier="professional" />)
      expect(screen.getByRole('status')).toHaveAttribute(
        'aria-label',
        'Professional tier - requires 10 stages'
      )

      rerender(<SDLCTierBadge tier="enterprise" />)
      expect(screen.getByRole('status')).toHaveAttribute(
        'aria-label',
        'Enterprise tier - requires 11 stages'
      )
    })

    it('hides icon from screen readers', () => {
      render(<SDLCTierBadge tier="standard" />)

      // The icon span should have aria-hidden="true"
      const icon = screen.getByText('⚡')
      expect(icon).toHaveAttribute('aria-hidden', 'true')
    })
  })
})

describe('getTierFromScore', () => {
  it('returns enterprise for score >= 95', () => {
    expect(getTierFromScore(95)).toBe('enterprise')
    expect(getTierFromScore(100)).toBe('enterprise')
  })

  it('returns professional for score >= 85 and < 95', () => {
    expect(getTierFromScore(85)).toBe('professional')
    expect(getTierFromScore(94)).toBe('professional')
  })

  it('returns standard for score >= 70 and < 85', () => {
    expect(getTierFromScore(70)).toBe('standard')
    expect(getTierFromScore(84)).toBe('standard')
  })

  it('returns lite for score < 70', () => {
    expect(getTierFromScore(0)).toBe('lite')
    expect(getTierFromScore(69)).toBe('lite')
  })
})

describe('getTierColorClasses', () => {
  it('returns correct colors for lite tier', () => {
    const colors = getTierColorClasses('lite')
    expect(colors.bg).toBe('bg-green-100')
    expect(colors.border).toBe('border-green-300')
    expect(colors.text).toBe('text-green-800')
  })

  it('returns correct colors for standard tier', () => {
    const colors = getTierColorClasses('standard')
    expect(colors.bg).toBe('bg-blue-100')
    expect(colors.border).toBe('border-blue-300')
    expect(colors.text).toBe('text-blue-800')
  })

  it('returns correct colors for professional tier', () => {
    const colors = getTierColorClasses('professional')
    expect(colors.bg).toBe('bg-purple-100')
    expect(colors.border).toBe('border-purple-300')
    expect(colors.text).toBe('text-purple-800')
  })

  it('returns correct colors for enterprise tier', () => {
    const colors = getTierColorClasses('enterprise')
    expect(colors.bg).toBe('bg-amber-100')
    expect(colors.border).toBe('border-amber-300')
    expect(colors.text).toBe('text-amber-800')
  })
})
