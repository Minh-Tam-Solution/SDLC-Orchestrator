/**
 * Unit Tests: IssueList Component
 * Version: 1.0.0 (Sprint 30 Day 4)
 *
 * Test coverage:
 * - Issue rendering with severity
 * - Filter functionality
 * - Fix suggestions
 * - Empty state
 * - Max items limit
 */

import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@/test/test-utils'
import { IssueList, IssueSummary } from './IssueList'
import type { ValidationIssue } from '@/types/sdlcValidation'

const mockIssues: ValidationIssue[] = [
  {
    code: 'MISSING_STAGE',
    severity: 'error',
    message: 'Stage 04 (Testing & QA) is missing',
    stageId: '04',
    fixSuggestion: 'Create folder docs/04-Testing-QA with Test-Plan.md',
  },
  {
    code: 'MISSING_README',
    severity: 'warning',
    message: 'README.md not found in Stage 02',
    stageId: '02',
    path: 'docs/02-Design-Architecture/',
  },
  {
    code: 'NAMING_CONVENTION',
    severity: 'info',
    message: 'Consider using kebab-case for folder names',
    path: 'docs/01-Planning-Analysis/',
  },
]

describe('IssueList', () => {
  describe('rendering', () => {
    it('renders all issues', () => {
      render(<IssueList issues={mockIssues} />)

      expect(screen.getByText('Stage 04 (Testing & QA) is missing')).toBeInTheDocument()
      expect(screen.getByText('README.md not found in Stage 02')).toBeInTheDocument()
      expect(screen.getByText('Consider using kebab-case for folder names')).toBeInTheDocument()
    })

    it('renders issue codes as badges', () => {
      render(<IssueList issues={mockIssues} />)

      expect(screen.getByText('MISSING_STAGE')).toBeInTheDocument()
      expect(screen.getByText('MISSING_README')).toBeInTheDocument()
      expect(screen.getByText('NAMING_CONVENTION')).toBeInTheDocument()
    })

    it('renders severity icons', () => {
      render(<IssueList issues={mockIssues} />)

      expect(screen.getByText('❌')).toBeInTheDocument() // error
      expect(screen.getByText('⚠️')).toBeInTheDocument() // warning
      expect(screen.getByText('ℹ️')).toBeInTheDocument() // info
    })

    it('renders path when provided', () => {
      render(<IssueList issues={mockIssues} />)

      expect(screen.getByText('docs/02-Design-Architecture/')).toBeInTheDocument()
      expect(screen.getByText('docs/01-Planning-Analysis/')).toBeInTheDocument()
    })
  })

  describe('empty state', () => {
    it('shows success message when no issues', () => {
      render(<IssueList issues={[]} />)

      expect(screen.getByText('No Issues Found')).toBeInTheDocument()
      expect(screen.getByText('SDLC structure validation passed without issues')).toBeInTheDocument()
      expect(screen.getByText('✅')).toBeInTheDocument()
    })
  })

  describe('filter functionality', () => {
    it('shows all filter tabs with counts', () => {
      render(<IssueList issues={mockIssues} />)

      expect(screen.getByText('All (3)')).toBeInTheDocument()
      expect(screen.getByText('Errors (1)')).toBeInTheDocument()
      expect(screen.getByText('Warnings (1)')).toBeInTheDocument()
      expect(screen.getByText('Info (1)')).toBeInTheDocument()
    })

    it('filters to errors when error tab clicked', () => {
      render(<IssueList issues={mockIssues} />)

      fireEvent.click(screen.getByText('Errors (1)'))

      expect(screen.getByText('Stage 04 (Testing & QA) is missing')).toBeInTheDocument()
      expect(screen.queryByText('README.md not found in Stage 02')).not.toBeInTheDocument()
    })

    it('filters to warnings when warning tab clicked', () => {
      render(<IssueList issues={mockIssues} />)

      fireEvent.click(screen.getByText('Warnings (1)'))

      expect(screen.getByText('README.md not found in Stage 02')).toBeInTheDocument()
      expect(screen.queryByText('Stage 04 (Testing & QA) is missing')).not.toBeInTheDocument()
    })
  })

  describe('max items', () => {
    it('limits displayed issues to maxItems', () => {
      const manyIssues = Array.from({ length: 25 }, (_, i) => ({
        code: `ISSUE_${i}`,
        severity: 'warning' as const,
        message: `Issue ${i}`,
      }))

      render(<IssueList issues={manyIssues} maxItems={10} />)

      expect(screen.getByText('Showing 10 of 25 issues')).toBeInTheDocument()
    })

    it('does not show limit message when under maxItems', () => {
      render(<IssueList issues={mockIssues} maxItems={10} />)

      expect(screen.queryByText(/Showing/)).not.toBeInTheDocument()
    })
  })

  describe('fix suggestions', () => {
    it('shows "Show Fix" button when suggestion available', () => {
      render(<IssueList issues={mockIssues} showSuggestions />)

      expect(screen.getAllByText('Show Fix')).toHaveLength(1) // Only one issue has suggestion
    })

    it('hides fix suggestions when showSuggestions is false', () => {
      render(<IssueList issues={mockIssues} showSuggestions={false} />)

      expect(screen.queryByText('Show Fix')).not.toBeInTheDocument()
    })

    it('expands fix suggestion when clicked', () => {
      render(<IssueList issues={mockIssues} showSuggestions />)

      fireEvent.click(screen.getByText('Show Fix'))

      expect(screen.getByText('💡 Suggested Fix:')).toBeInTheDocument()
      expect(screen.getByText('Create folder docs/04-Testing-QA with Test-Plan.md')).toBeInTheDocument()
    })
  })
})

describe('IssueSummary', () => {
  it('shows success when no issues', () => {
    render(<IssueSummary errors={0} warnings={0} info={0} />)

    expect(screen.getByText('No issues')).toBeInTheDocument()
    expect(screen.getByText('✅')).toBeInTheDocument()
  })

  it('shows error count when errors exist', () => {
    render(<IssueSummary errors={3} warnings={0} info={0} />)

    expect(screen.getByText('❌')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
  })

  it('shows warning count when warnings exist', () => {
    render(<IssueSummary errors={0} warnings={5} info={0} />)

    expect(screen.getByText('⚠️')).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument()
  })

  it('shows all counts when multiple issue types exist', () => {
    render(<IssueSummary errors={2} warnings={3} info={1} />)

    expect(screen.getByText('❌')).toBeInTheDocument()
    expect(screen.getByText('⚠️')).toBeInTheDocument()
    expect(screen.getByText('ℹ️')).toBeInTheDocument()
  })
})
