/**
 * Timeline Stats Bar Component
 *
 * SDLC Stage: 04 - BUILD
 * Sprint: 43 - Policy Guards & Evidence UI
 * Framework: SDLC 5.1.1
 * Epic: EP-02 AI Safety Layer v1
 *
 * Purpose:
 * Displays aggregated statistics at the top of the Evidence Timeline.
 * Shows key metrics: total events, AI-detected count, pass rate, override rate.
 */

import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import type { EvidenceTimelineStats } from '@/types/evidence-timeline'

interface TimelineStatsBarProps {
  stats: EvidenceTimelineStats | undefined
  isLoading: boolean
}

export default function TimelineStatsBar({ stats, isLoading }: TimelineStatsBarProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i}>
            <CardContent className="p-4">
              <Skeleton className="h-4 w-20 mb-2" />
              <Skeleton className="h-8 w-16" />
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  if (!stats) {
    return null
  }

  const statItems = [
    {
      label: 'Total Events',
      value: stats.total_events.toLocaleString(),
      icon: (
        <svg className="h-5 w-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
        </svg>
      ),
      bgColor: 'bg-blue-50',
    },
    {
      label: 'AI Detected',
      value: stats.ai_detected.toLocaleString(),
      icon: (
        <svg className="h-5 w-5 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
      ),
      bgColor: 'bg-purple-50',
    },
    {
      label: 'Pass Rate',
      value: `${stats.pass_rate.toFixed(1)}%`,
      icon: (
        <svg className="h-5 w-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      bgColor: 'bg-green-50',
      textColor: stats.pass_rate >= 80 ? 'text-green-600' : stats.pass_rate >= 50 ? 'text-yellow-600' : 'text-red-600',
    },
    {
      label: 'Override Rate',
      value: `${stats.override_rate.toFixed(1)}%`,
      icon: (
        <svg className="h-5 w-5 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      ),
      bgColor: 'bg-orange-50',
    },
  ]

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      {statItems.map((item) => (
        <Card key={item.label} className="overflow-hidden">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-lg ${item.bgColor}`}>
                {item.icon}
              </div>
              <div>
                <p className="text-sm text-muted-foreground">{item.label}</p>
                <p className={`text-2xl font-bold ${item.textColor || ''}`}>
                  {item.value}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
