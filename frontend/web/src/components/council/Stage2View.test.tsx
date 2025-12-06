/**
 * Unit Tests: Stage2View Component
 * Version: 1.0.0 (Sprint 28 Day 3)
 *
 * Test coverage:
 * - Renders collapsible header
 * - Shows ranker count
 * - Displays rankings when expanded
 * - Shows consensus/majority winner
 * - Loading skeleton
 * - Accessibility
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@/test/test-utils'
import userEvent from '@testing-library/user-event'
import { Stage2View } from './Stage2View'
import { createMockRanking } from '@/test/test-utils'

describe('Stage2View', () => {
  const mockRankings = [
    createMockRanking({
      ranker: 'Claude',
      rankings: ['Claude', 'OpenAI', 'Gemini'],
      reasoning: 'Claude had the most comprehensive answer',
    }),
    createMockRanking({
      ranker: 'OpenAI',
      rankings: ['Claude', 'OpenAI', 'Gemini'],
      reasoning: 'Claude provided better actionable steps',
    }),
    createMockRanking({
      ranker: 'Gemini',
      rankings: ['Claude', 'Gemini', 'OpenAI'],
      reasoning: 'Claude aligned best with SDLC framework',
    }),
  ]

  describe('collapsed state', () => {
    it('renders header with stage name', () => {
      render(<Stage2View rankings={mockRankings} />)

      expect(screen.getByText('Stage 2: Peer Rankings')).toBeInTheDocument()
    })

    it('shows ranker count', () => {
      render(<Stage2View rankings={mockRankings} />)

      expect(screen.getByText('3 rankers')).toBeInTheDocument()
    })

    it('shows completion status when not loading', () => {
      render(<Stage2View rankings={mockRankings} />)

      expect(screen.getByText('Cross-evaluation complete')).toBeInTheDocument()
    })

    it('does not show rankings when collapsed', () => {
      render(<Stage2View rankings={mockRankings} />)

      expect(screen.queryByText('Claude ranked:')).not.toBeInTheDocument()
    })
  })

  describe('expanded state', () => {
    it('shows rankings when clicked', async () => {
      const user = userEvent.setup()
      render(<Stage2View rankings={mockRankings} />)

      const trigger = screen.getByText('Stage 2: Peer Rankings')
      await user.click(trigger)

      expect(screen.getByText('Claude ranked:')).toBeInTheDocument()
      expect(screen.getByText('OpenAI ranked:')).toBeInTheDocument()
      expect(screen.getByText('Gemini ranked:')).toBeInTheDocument()
    })

    it('shows rank badges (1st, 2nd, 3rd)', async () => {
      const user = userEvent.setup()
      render(<Stage2View rankings={mockRankings} />)

      const trigger = screen.getByText('Stage 2: Peer Rankings')
      await user.click(trigger)

      // Should show gold, silver, bronze medals
      expect(screen.getAllByText('🥇').length).toBeGreaterThan(0)
      expect(screen.getAllByText('🥈').length).toBeGreaterThan(0)
      expect(screen.getAllByText('🥉').length).toBeGreaterThan(0)
    })

    it('shows (best) label for first place', async () => {
      const user = userEvent.setup()
      render(<Stage2View rankings={mockRankings} />)

      const trigger = screen.getByText('Stage 2: Peer Rankings')
      await user.click(trigger)

      expect(screen.getAllByText(/\(best\)/).length).toBeGreaterThan(0)
    })

    it('shows reasoning for each ranker', async () => {
      const user = userEvent.setup()
      render(<Stage2View rankings={mockRankings} />)

      const trigger = screen.getByText('Stage 2: Peer Rankings')
      await user.click(trigger)

      expect(screen.getByText(/Claude had the most comprehensive/)).toBeInTheDocument()
      expect(screen.getByText(/Claude provided better actionable/)).toBeInTheDocument()
      expect(screen.getByText(/Claude aligned best/)).toBeInTheDocument()
    })
  })

  describe('consensus winner', () => {
    it('shows consensus winner when all agree', async () => {
      const user = userEvent.setup()
      const unanimousRankings = [
        createMockRanking({ ranker: 'Claude', rankings: ['Claude', 'OpenAI', 'Gemini'] }),
        createMockRanking({ ranker: 'OpenAI', rankings: ['Claude', 'OpenAI', 'Gemini'] }),
        createMockRanking({ ranker: 'Gemini', rankings: ['Claude', 'OpenAI', 'Gemini'] }),
      ]

      render(<Stage2View rankings={unanimousRankings} />)

      const trigger = screen.getByText('Stage 2: Peer Rankings')
      await user.click(trigger)

      expect(screen.getByText(/Consensus Winner: Claude/)).toBeInTheDocument()
      expect(screen.getByText('3/3 AIs ranked #1')).toBeInTheDocument()
    })

    it('shows majority winner when not unanimous', async () => {
      const user = userEvent.setup()
      const splitRankings = [
        createMockRanking({ ranker: 'Claude', rankings: ['Claude', 'OpenAI', 'Gemini'] }),
        createMockRanking({ ranker: 'OpenAI', rankings: ['Claude', 'OpenAI', 'Gemini'] }),
        createMockRanking({ ranker: 'Gemini', rankings: ['Gemini', 'Claude', 'OpenAI'] }),
      ]

      render(<Stage2View rankings={splitRankings} />)

      const trigger = screen.getByText('Stage 2: Peer Rankings')
      await user.click(trigger)

      expect(screen.getByText(/Majority Winner: Claude/)).toBeInTheDocument()
      expect(screen.getByText('2/3 AIs ranked #1')).toBeInTheDocument()
    })
  })

  describe('loading state', () => {
    it('shows ranking message when loading', () => {
      render(<Stage2View rankings={[]} isLoading={true} />)

      expect(screen.getByText('Ranking...')).toBeInTheDocument()
    })

    it('shows loading skeleton when expanded and loading', async () => {
      const user = userEvent.setup()
      render(<Stage2View rankings={[]} isLoading={true} />)

      const trigger = screen.getByText('Stage 2: Peer Rankings')
      await user.click(trigger)

      const skeletons = document.querySelectorAll('[class*="skeleton"], .animate-pulse')
      expect(skeletons.length).toBeGreaterThan(0)
    })
  })

  describe('accessibility', () => {
    it('trigger has correct aria-label', () => {
      render(<Stage2View rankings={mockRankings} />)

      const trigger = screen.getByRole('button')
      expect(trigger).toHaveAttribute(
        'aria-label',
        'Stage 2: Peer Rankings, 3 rankers'
      )
    })

    it('can be toggled with keyboard', async () => {
      const user = userEvent.setup()
      render(<Stage2View rankings={mockRankings} />)

      const trigger = screen.getByRole('button')
      trigger.focus()

      await user.keyboard('{Enter}')

      expect(screen.getByText('Claude ranked:')).toBeInTheDocument()
    })
  })

  describe('self-ranking indicator', () => {
    it('shows (self) when ranker ranks themselves', async () => {
      const user = userEvent.setup()
      render(<Stage2View rankings={mockRankings} />)

      const trigger = screen.getByText('Stage 2: Peer Rankings')
      await user.click(trigger)

      // Each ranker ranks themselves somewhere
      expect(screen.getAllByText('(self)').length).toBeGreaterThan(0)
    })
  })

  describe('empty rankings', () => {
    it('renders with empty rankings array', () => {
      render(<Stage2View rankings={[]} />)

      expect(screen.getByText('Stage 2: Peer Rankings')).toBeInTheDocument()
      expect(screen.getByText('0 rankers')).toBeInTheDocument()
    })
  })
})
