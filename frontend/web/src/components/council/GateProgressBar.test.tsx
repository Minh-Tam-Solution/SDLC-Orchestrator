/**
 * Unit Tests: GateProgressBar Component
 * Version: 1.0.0 (Sprint 28 Day 3)
 *
 * Test coverage:
 * - All 7 gates render correctly
 * - Status styling for passed/current/pending/blocked
 * - Click handler triggers correctly
 * - Accessibility attributes
 * - Legend display
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@/test/test-utils'
import userEvent from '@testing-library/user-event'
import { GateProgressBar } from './GateProgressBar'
import { GateType, GateProgressStatus, GATE_DEFINITIONS } from '@/types/council'
import { createMockGateStatuses } from '@/test/test-utils'

const GATE_ORDER: GateType[] = ['G0.1', 'G0.2', 'G1', 'G2', 'G3', 'G4', 'G5']

describe('GateProgressBar', () => {
  const defaultProps = {
    currentGate: 'G2' as GateType,
    gateStatuses: createMockGateStatuses('G2'),
    tier: 'standard' as const,
  }

  describe('rendering', () => {
    it('renders all 7 gates', () => {
      render(<GateProgressBar {...defaultProps} />)

      GATE_ORDER.forEach((gate) => {
        expect(screen.getByText(gate)).toBeInTheDocument()
      })
    })

    it('renders gate labels', () => {
      render(<GateProgressBar {...defaultProps} />)

      // Check that gate labels are rendered
      Object.values(GATE_DEFINITIONS).forEach(({ label }) => {
        expect(screen.getByText(label)).toBeInTheDocument()
      })
    })

    it('renders legend items', () => {
      render(<GateProgressBar {...defaultProps} />)

      expect(screen.getByText('Passed')).toBeInTheDocument()
      expect(screen.getByText('Current')).toBeInTheDocument()
      expect(screen.getByText('Pending')).toBeInTheDocument()
      expect(screen.getByText('Blocked')).toBeInTheDocument()
    })
  })

  describe('gate status styling', () => {
    it('shows checkmark for passed gates', () => {
      const gateStatuses = createMockGateStatuses('G2')
      render(<GateProgressBar {...defaultProps} gateStatuses={gateStatuses} />)

      // G0.1, G0.2, G1 should be passed (before G2)
      const passedGates = ['G0.1', 'G0.2', 'G1']
      passedGates.forEach((gate) => {
        const button = screen.getByLabelText(new RegExp(`Gate ${gate}.*passed`, 'i'))
        expect(button).toHaveClass('bg-green-500')
      })
    })

    it('shows current indicator with pulse animation for current gate', () => {
      render(<GateProgressBar {...defaultProps} currentGate="G2" />)

      const currentButton = screen.getByLabelText(/Gate G2.*current/i)
      expect(currentButton).toHaveClass('bg-blue-500')
      expect(currentButton).toHaveClass('animate-pulse')
    })

    it('shows pending indicator for future gates', () => {
      const gateStatuses = createMockGateStatuses('G2')
      render(<GateProgressBar {...defaultProps} gateStatuses={gateStatuses} />)

      // G3, G4, G5 should be pending (after G2)
      const pendingGates = ['G3', 'G4', 'G5']
      pendingGates.forEach((gate) => {
        const button = screen.getByLabelText(new RegExp(`Gate ${gate}.*pending`, 'i'))
        expect(button).toHaveClass('bg-gray-300')
      })
    })

    it('shows blocked indicator for blocked gates', () => {
      const gateStatuses: Record<GateType, GateProgressStatus> = {
        'G0.1': 'passed',
        'G0.2': 'passed',
        'G1': 'blocked',
        'G2': 'pending',
        'G3': 'pending',
        'G4': 'pending',
        'G5': 'pending',
      }

      render(
        <GateProgressBar
          {...defaultProps}
          currentGate="G1"
          gateStatuses={gateStatuses}
        />
      )

      const blockedButton = screen.getByLabelText(/Gate G1.*blocked/i)
      expect(blockedButton).toHaveClass('bg-red-500')
    })
  })

  describe('click handler', () => {
    it('calls onGateClick when gate is clicked', async () => {
      const user = userEvent.setup()
      const handleClick = vi.fn()

      render(<GateProgressBar {...defaultProps} onGateClick={handleClick} />)

      const gate = screen.getByLabelText(/Gate G2/i)
      await user.click(gate)

      expect(handleClick).toHaveBeenCalledTimes(1)
      expect(handleClick).toHaveBeenCalledWith('G2')
    })

    it('can click any gate', async () => {
      const user = userEvent.setup()
      const handleClick = vi.fn()

      render(<GateProgressBar {...defaultProps} onGateClick={handleClick} />)

      // Click each gate
      for (const gate of GATE_ORDER) {
        const button = screen.getByLabelText(new RegExp(`Gate ${gate}`, 'i'))
        await user.click(button)
        expect(handleClick).toHaveBeenCalledWith(gate)
      }

      expect(handleClick).toHaveBeenCalledTimes(7)
    })

    it('buttons are disabled when no onGateClick provided', () => {
      render(<GateProgressBar {...defaultProps} />)

      const gate = screen.getByLabelText(/Gate G2/i)
      expect(gate).toBeDisabled()
    })

    it('buttons are enabled when onGateClick provided', () => {
      render(<GateProgressBar {...defaultProps} onGateClick={() => {}} />)

      const gate = screen.getByLabelText(/Gate G2/i)
      expect(gate).not.toBeDisabled()
    })
  })

  describe('accessibility', () => {
    it('each gate button has aria-label with gate info', () => {
      render(<GateProgressBar {...defaultProps} />)

      GATE_ORDER.forEach((gate) => {
        const def = GATE_DEFINITIONS[gate]
        const button = screen.getByLabelText(new RegExp(`Gate ${gate}.*${def.label}`, 'i'))
        expect(button).toBeInTheDocument()
      })
    })

    it('current gate has aria-current="step"', () => {
      render(<GateProgressBar {...defaultProps} currentGate="G2" />)

      const currentButton = screen.getByLabelText(/Gate G2/i)
      expect(currentButton).toHaveAttribute('aria-current', 'step')
    })

    it('non-current gates do not have aria-current', () => {
      render(<GateProgressBar {...defaultProps} currentGate="G2" />)

      const otherGates = GATE_ORDER.filter((g) => g !== 'G2')
      otherGates.forEach((gate) => {
        const button = screen.getByLabelText(new RegExp(`Gate ${gate}`, 'i'))
        expect(button).not.toHaveAttribute('aria-current')
      })
    })

    it('connector lines are hidden from screen readers', () => {
      render(<GateProgressBar {...defaultProps} />)

      // Connector lines should have aria-hidden
      const connectors = document.querySelectorAll('[aria-hidden="true"]')
      // There are 6 connector lines (between 7 gates) + icons
      expect(connectors.length).toBeGreaterThanOrEqual(6)
    })

    it('icons are hidden from screen readers', () => {
      render(<GateProgressBar {...defaultProps} />)

      // The icons (✓, ●, ○) should have aria-hidden
      const icons = screen.getAllByText(/[✓●○⊘]/)
      icons.forEach((icon) => {
        // Some icons are in legend (visible) but gate icons should be hidden
        if (icon.closest('button')) {
          expect(icon).toHaveAttribute('aria-hidden', 'true')
        }
      })
    })
  })

  describe('different current gate positions', () => {
    it.each<GateType>(GATE_ORDER)(
      'correctly shows %s as current gate',
      (currentGate) => {
        const gateStatuses = createMockGateStatuses(currentGate)

        render(
          <GateProgressBar
            {...defaultProps}
            currentGate={currentGate}
            gateStatuses={gateStatuses}
          />
        )

        const currentButton = screen.getByLabelText(new RegExp(`Gate ${currentGate}`, 'i'))
        expect(currentButton).toHaveAttribute('aria-current', 'step')
        expect(currentButton).toHaveClass('animate-pulse')
      }
    )
  })

  describe('custom className', () => {
    it('applies custom className to wrapper', () => {
      const { container } = render(
        <GateProgressBar {...defaultProps} className="custom-class" />
      )

      const wrapper = container.firstChild
      expect(wrapper).toHaveClass('custom-class')
    })
  })
})
