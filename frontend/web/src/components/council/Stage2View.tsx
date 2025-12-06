/**
 * File: frontend/web/src/components/council/Stage2View.tsx
 * Version: 1.0.0
 * Status: ACTIVE - STAGE 03 (BUILD)
 * Date: 2025-12-04
 * Authority: Frontend Lead + CTO Approved
 * Sprint: 28 - Web Dashboard AI Assistant
 *
 * Description:
 * Stage 2 view component for AI Council deliberation.
 * Displays peer rankings from each AI provider.
 */

import { useState, memo } from 'react'
import { ChevronDown, ChevronRight, Trophy, Medal } from 'lucide-react'
import { cn } from '@/lib/utils'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { Skeleton } from '@/components/ui/skeleton'
import type { Stage2ViewProps, Ranking } from '@/types/council'

// Rank badge colors
const RANK_COLORS = {
  1: { bg: 'bg-yellow-100', text: 'text-yellow-700', icon: '🥇' },
  2: { bg: 'bg-gray-100', text: 'text-gray-600', icon: '🥈' },
  3: { bg: 'bg-orange-100', text: 'text-orange-700', icon: '🥉' },
}

function getRankStyle(rank: number) {
  return RANK_COLORS[rank as keyof typeof RANK_COLORS] || {
    bg: 'bg-muted',
    text: 'text-muted-foreground',
    icon: `#${rank}`,
  }
}

function RankingCard({ ranking }: { ranking: Ranking }) {
  return (
    <div className="rounded-lg border p-4 bg-card">
      {/* Header */}
      <div className="flex items-center gap-2 mb-3">
        <Medal className="h-4 w-4 text-muted-foreground" />
        <h4 className="font-medium">{ranking.ranker} ranked:</h4>
      </div>

      {/* Rankings list */}
      <div className="space-y-2 mb-3">
        {ranking.rankings.map((provider, index) => {
          const rankNum = index + 1
          const style = getRankStyle(rankNum)
          return (
            <div
              key={provider}
              className={cn(
                'flex items-center gap-2 rounded-md px-3 py-1.5',
                style.bg
              )}
            >
              <span className="text-sm">{style.icon}</span>
              <span className={cn('text-sm font-medium', style.text)}>
                {rankNum === 1 ? `${provider} (best)` : provider}
              </span>
              {provider.toLowerCase() === ranking.ranker.toLowerCase() && (
                <span className="text-xs text-muted-foreground">(self)</span>
              )}
            </div>
          )
        })}
      </div>

      {/* Reasoning */}
      {ranking.reasoning && (
        <p className="text-xs text-muted-foreground italic border-t pt-2">
          &ldquo;{ranking.reasoning}&rdquo;
        </p>
      )}
    </div>
  )
}

function ConsensusWinner({ rankings }: { rankings: Ranking[] }) {
  // Calculate consensus winner
  const votes: Record<string, number> = {}

  rankings.forEach((ranking) => {
    const winner = ranking.rankings[0]
    if (winner) {
      votes[winner] = (votes[winner] || 0) + 1
    }
  })

  const entries = Object.entries(votes)
  if (entries.length === 0) return null

  const [winner, winnerVotes] = entries.reduce((max, curr) =>
    curr[1] > max[1] ? curr : max
  )

  const isConsensus = winnerVotes === rankings.length

  return (
    <div
      className={cn(
        'rounded-lg border-2 p-3 flex items-center gap-3',
        isConsensus ? 'border-yellow-400 bg-yellow-50' : 'border-primary/20 bg-primary/5'
      )}
    >
      <Trophy className={cn(
        'h-5 w-5',
        isConsensus ? 'text-yellow-600' : 'text-primary'
      )} />
      <div>
        <div className="font-medium">
          {isConsensus ? 'Consensus' : 'Majority'} Winner: {winner}
        </div>
        <div className="text-xs text-muted-foreground">
          {winnerVotes}/{rankings.length} AIs ranked #1
        </div>
      </div>
    </div>
  )
}

function LoadingSkeleton() {
  return (
    <div className="space-y-3">
      {[1, 2, 3].map((i) => (
        <div key={i} className="rounded-lg border p-4 bg-card">
          <div className="flex items-center gap-2 mb-3">
            <Skeleton className="h-4 w-4" />
            <Skeleton className="h-4 w-32" />
          </div>
          <div className="space-y-2">
            {[1, 2, 3].map((j) => (
              <Skeleton key={j} className="h-8 w-full rounded-md" />
            ))}
          </div>
        </div>
      ))}
      <Skeleton className="h-14 w-full rounded-lg" />
    </div>
  )
}

export const Stage2View = memo(function Stage2View({ rankings, isLoading = false }: Stage2ViewProps) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <CollapsibleTrigger
        className={cn(
          'flex w-full items-center justify-between rounded-lg border p-3',
          'bg-muted/50 hover:bg-muted transition-colors',
          'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2'
        )}
        aria-label={`Stage 2: Peer Rankings, ${rankings.length} rankers`}
      >
        <div className="flex items-center gap-2">
          {isOpen ? (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronRight className="h-4 w-4 text-muted-foreground" />
          )}
          <span className="font-medium">Stage 2: Peer Rankings</span>
          <span className="text-xs text-muted-foreground px-2 py-0.5 bg-background rounded">
            {rankings.length} rankers
          </span>
        </div>
        <div className="text-xs text-muted-foreground">
          {isLoading ? (
            <span className="animate-pulse">Ranking...</span>
          ) : (
            rankings.length > 0 && <span>Cross-evaluation complete</span>
          )}
        </div>
      </CollapsibleTrigger>

      <CollapsibleContent className="pt-3">
        {isLoading ? (
          <LoadingSkeleton />
        ) : (
          <div className="space-y-3">
            <div className="text-xs text-muted-foreground mb-2">
              Rankings by each AI:
            </div>
            {rankings.map((ranking, index) => (
              <RankingCard key={`${ranking.ranker}-${index}`} ranking={ranking} />
            ))}
            {rankings.length > 0 && <ConsensusWinner rankings={rankings} />}
          </div>
        )}
      </CollapsibleContent>
    </Collapsible>
  )
})

export default Stage2View
