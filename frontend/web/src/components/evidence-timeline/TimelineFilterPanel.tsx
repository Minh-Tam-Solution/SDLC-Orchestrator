/**
 * Timeline Filter Panel Component
 *
 * SDLC Stage: 04 - BUILD
 * Sprint: 43 - Policy Guards & Evidence UI
 * Framework: SDLC 5.1.1
 * Epic: EP-02 AI Safety Layer v1
 *
 * Purpose:
 * Filter panel for Evidence Timeline with search, date range,
 * AI tool filter, and validation status filter.
 */

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { Calendar } from '@/components/ui/calendar'
import { format } from 'date-fns'
import {
  AIToolType,
  AIToolLabels,
  ValidationStatus,
  type EvidenceFilters,
} from '@/types/evidence-timeline'

interface TimelineFilterPanelProps {
  filters: EvidenceFilters
  onFiltersChange: (filters: EvidenceFilters) => void
  onClear: () => void
}

export default function TimelineFilterPanel({
  filters,
  onFiltersChange,
  onClear,
}: TimelineFilterPanelProps) {
  const [dateStart, setDateStart] = useState<Date | undefined>(
    filters.date_start ? new Date(filters.date_start) : undefined
  )
  const [dateEnd, setDateEnd] = useState<Date | undefined>(
    filters.date_end ? new Date(filters.date_end) : undefined
  )

  const handleSearchChange = (search: string) => {
    onFiltersChange({ ...filters, search: search || undefined })
  }

  const handleAIToolChange = (value: string) => {
    onFiltersChange({
      ...filters,
      ai_tool: value === 'all' ? undefined : (value as AIToolType),
    })
  }

  const handleStatusChange = (value: string) => {
    onFiltersChange({
      ...filters,
      validation_status: value === 'all' ? undefined : (value as ValidationStatus),
    })
  }

  const handleDateStartChange = (date: Date | undefined) => {
    setDateStart(date)
    onFiltersChange({
      ...filters,
      date_start: date ? date.toISOString() : undefined,
    })
  }

  const handleDateEndChange = (date: Date | undefined) => {
    setDateEnd(date)
    onFiltersChange({
      ...filters,
      date_end: date ? date.toISOString() : undefined,
    })
  }

  const hasActiveFilters =
    filters.search ||
    filters.ai_tool ||
    filters.validation_status ||
    filters.date_start ||
    filters.date_end

  return (
    <div className="space-y-4 p-4 bg-muted/30 rounded-lg mb-6">
      <div className="flex flex-wrap gap-4">
        {/* Search Input */}
        <div className="flex-1 min-w-[200px]">
          <div className="relative">
            <svg
              className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            <Input
              placeholder="Search PR number or branch..."
              value={filters.search || ''}
              onChange={(e) => handleSearchChange(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        {/* AI Tool Filter */}
        <Select
          value={filters.ai_tool || 'all'}
          onValueChange={handleAIToolChange}
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="AI Tool" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All AI Tools</SelectItem>
            {Object.entries(AIToolLabels).map(([value, label]) => (
              <SelectItem key={value} value={value}>
                {label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Validation Status Filter */}
        <Select
          value={filters.validation_status || 'all'}
          onValueChange={handleStatusChange}
        >
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value={ValidationStatus.PASSED}>Passed</SelectItem>
            <SelectItem value={ValidationStatus.FAILED}>Failed</SelectItem>
            <SelectItem value={ValidationStatus.PENDING}>Pending</SelectItem>
            <SelectItem value={ValidationStatus.OVERRIDDEN}>Overridden</SelectItem>
          </SelectContent>
        </Select>

        {/* Date Range */}
        <div className="flex gap-2">
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="outline" className="w-[140px] justify-start">
                <svg
                  className="mr-2 h-4 w-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                  />
                </svg>
                {dateStart ? format(dateStart, 'MMM d') : 'From'}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="start">
              <Calendar
                mode="single"
                selected={dateStart}
                onSelect={handleDateStartChange}
                initialFocus
              />
            </PopoverContent>
          </Popover>

          <Popover>
            <PopoverTrigger asChild>
              <Button variant="outline" className="w-[140px] justify-start">
                <svg
                  className="mr-2 h-4 w-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                  />
                </svg>
                {dateEnd ? format(dateEnd, 'MMM d') : 'To'}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="start">
              <Calendar
                mode="single"
                selected={dateEnd}
                onSelect={handleDateEndChange}
                initialFocus
              />
            </PopoverContent>
          </Popover>
        </div>

        {/* Clear Filters */}
        {hasActiveFilters && (
          <Button
            variant="ghost"
            onClick={() => {
              setDateStart(undefined)
              setDateEnd(undefined)
              onClear()
            }}
            className="text-muted-foreground"
          >
            <svg
              className="mr-2 h-4 w-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
            Clear filters
          </Button>
        )}
      </div>

      {/* Active Filters Display */}
      {hasActiveFilters && (
        <div className="flex flex-wrap gap-2">
          {filters.search && (
            <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800">
              Search: {filters.search}
            </span>
          )}
          {filters.ai_tool && (
            <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs bg-purple-100 text-purple-800">
              Tool: {AIToolLabels[filters.ai_tool]}
            </span>
          )}
          {filters.validation_status && (
            <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs bg-green-100 text-green-800">
              Status: {filters.validation_status}
            </span>
          )}
          {(filters.date_start || filters.date_end) && (
            <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs bg-orange-100 text-orange-800">
              Date: {filters.date_start ? format(new Date(filters.date_start), 'MMM d') : '...'} - {filters.date_end ? format(new Date(filters.date_end), 'MMM d') : '...'}
            </span>
          )}
        </div>
      )}
    </div>
  )
}
