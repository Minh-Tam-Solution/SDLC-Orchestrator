/**
 * Unit Tests: ComplianceScoreCircle Component
 * Version: 1.0.0 (Sprint 30 Day 4)
 *
 * Test coverage:
 * - Score rendering and color coding
 * - Size variants
 * - Label visibility
 * - Animation toggle
 * - Accessibility
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@/test/test-utils'
import { ComplianceScoreCircle, ComplianceScoreBar } from './ComplianceScoreCircle'

describe('ComplianceScoreCircle', () => {
  describe('score rendering', () => {
    it('renders score value', () => {
      render(<ComplianceScoreCircle score={85} />)

      expect(screen.getByText('85')).toBeInTheDocument()
    })

    it('renders excellent label for score >= 90', () => {
      render(<ComplianceScoreCircle score={95} />)

      expect(screen.getByText('Excellent')).toBeInTheDocument()
    })

    it('renders good label for score >= 70', () => {
      render(<ComplianceScoreCircle score={75} />)

      expect(screen.getByText('Good')).toBeInTheDocument()
    })

    it('renders fair label for score >= 50', () => {
      render(<ComplianceScoreCircle score={55} />)

      expect(screen.getByText('Fair')).toBeInTheDocument()
    })

    it('renders poor label for score < 50', () => {
      render(<ComplianceScoreCircle score={30} />)

      expect(screen.getByText('Poor')).toBeInTheDocument()
    })
  })

  describe('color coding', () => {
    it('uses green for excellent scores', () => {
      render(<ComplianceScoreCircle score={95} />)

      const scoreText = screen.getByText('95')
      expect(scoreText).toHaveClass('text-green-600')
    })

    it('uses yellow for good scores', () => {
      render(<ComplianceScoreCircle score={75} />)

      const scoreText = screen.getByText('75')
      expect(scoreText).toHaveClass('text-yellow-600')
    })

    it('uses orange for fair scores', () => {
      render(<ComplianceScoreCircle score={55} />)

      const scoreText = screen.getByText('55')
      expect(scoreText).toHaveClass('text-orange-600')
    })

    it('uses red for poor scores', () => {
      render(<ComplianceScoreCircle score={30} />)

      const scoreText = screen.getByText('30')
      expect(scoreText).toHaveClass('text-red-600')
    })
  })

  describe('size variants', () => {
    it('renders sm size', () => {
      render(<ComplianceScoreCircle score={85} size="sm" />)

      const scoreText = screen.getByText('85')
      expect(scoreText).toHaveClass('text-sm')
    })

    it('renders md size (default)', () => {
      render(<ComplianceScoreCircle score={85} />)

      const scoreText = screen.getByText('85')
      expect(scoreText).toHaveClass('text-xl')
    })

    it('renders lg size', () => {
      render(<ComplianceScoreCircle score={85} size="lg" />)

      const scoreText = screen.getByText('85')
      expect(scoreText).toHaveClass('text-3xl')
    })
  })

  describe('label visibility', () => {
    it('shows label by default', () => {
      render(<ComplianceScoreCircle score={85} />)

      expect(screen.getByText('Good')).toBeInTheDocument()
    })

    it('hides label when showLabel is false', () => {
      render(<ComplianceScoreCircle score={85} showLabel={false} />)

      expect(screen.queryByText('Good')).not.toBeInTheDocument()
    })
  })

  describe('accessibility', () => {
    it('has role="img"', () => {
      render(<ComplianceScoreCircle score={85} />)

      const container = screen.getByRole('img')
      expect(container).toBeInTheDocument()
    })

    it('has correct aria-label', () => {
      render(<ComplianceScoreCircle score={85} />)

      const container = screen.getByRole('img')
      expect(container).toHaveAttribute('aria-label', 'Compliance score: 85%')
    })
  })
})

describe('ComplianceScoreBar', () => {
  describe('rendering', () => {
    it('renders score percentage', () => {
      render(<ComplianceScoreBar score={75} />)

      expect(screen.getByText('75%')).toBeInTheDocument()
    })

    it('renders label text', () => {
      render(<ComplianceScoreBar score={75} />)

      expect(screen.getByText('Compliance Score')).toBeInTheDocument()
    })

    it('hides label when showLabel is false', () => {
      render(<ComplianceScoreBar score={75} showLabel={false} />)

      expect(screen.queryByText('Compliance Score')).not.toBeInTheDocument()
    })
  })

  describe('accessibility', () => {
    it('has progressbar role', () => {
      render(<ComplianceScoreBar score={75} />)

      const progressbar = screen.getByRole('progressbar')
      expect(progressbar).toBeInTheDocument()
    })

    it('has correct aria values', () => {
      render(<ComplianceScoreBar score={75} />)

      const progressbar = screen.getByRole('progressbar')
      expect(progressbar).toHaveAttribute('aria-valuenow', '75')
      expect(progressbar).toHaveAttribute('aria-valuemin', '0')
      expect(progressbar).toHaveAttribute('aria-valuemax', '100')
    })
  })
})
