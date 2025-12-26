/**
 * File: frontend/web/src/components/onboarding/AIAnalysis.tsx
 * Version: 1.0.0
 * Status: ACTIVE - Sprint 15 Day 5
 * Date: December 2, 2025
 * Authority: Frontend Lead + CPO Approved
 * Foundation: User-Onboarding-Flow-Architecture.md
 *
 * Description:
 * Step 3: AI Analysis - 2 minutes
 * Analyzes repository structure and provides recommendations.
 */

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import OnboardingLayout from './OnboardingLayout'
import OnboardingProgress from './OnboardingProgress'
import apiClient from '@/api/client'
import { GitHubAnalysisResult } from '@/types/api'

type PolicyPack = 'lite' | 'standard' | 'professional' | 'enterprise'

interface PolicyPackInfo {
  name: PolicyPack
  title: string
  description: string
  features: string[]
}

const POLICY_PACKS: PolicyPackInfo[] = [
  {
    name: 'lite',
    title: 'Lite',
    description: 'Minimal governance - trust the team, move fast',
    features: [
      'Basic gates (G0.1, G1, G3, G5)',
      'README + basic docs only',
      'Best for: Solo devs, MVPs, hackathons',
    ],
  },
  {
    name: 'standard',
    title: 'Standard',
    description: 'Balanced governance - quality with agility',
    features: [
      'Core gates (G0.1-G6)',
      'CI/CD + security scanning',
      'Best for: Small teams (3-10), growing startups',
    ],
  },
  {
    name: 'professional',
    title: 'Professional',
    description: 'Strong governance - enterprise-grade quality',
    features: [
      'Full gates + 80% test coverage',
      'SBOM, SAST, OWASP L1',
      'Best for: Medium teams, regulated industries',
    ],
  },
  {
    name: 'enterprise',
    title: 'Enterprise',
    description: 'Maximum governance - audit-ready compliance',
    features: [
      'All gates + quarterly audits',
      'OWASP L2+, 95% coverage',
      'Best for: Large orgs, finance, healthcare',
    ],
  },
]

// Use GitHubAnalysisResult directly - it already has all needed fields

/**
 * AI Analysis component (Step 3)
 *
 * Features:
 * - Repository structure analysis
 * - Project type detection
 * - Team size estimation
 * - Policy pack recommendation
 */
export default function AIAnalysis() {
  const navigate = useNavigate()
  const [repo, setRepo] = useState<any>(null)
  const [selectedTier, setSelectedTier] = useState<PolicyPack>('standard')
  const [recommendedTier, setRecommendedTier] = useState<PolicyPack | null>(null)

  // Get selected repo from sessionStorage
  useEffect(() => {
    const repoData = sessionStorage.getItem('onboarding_repo')
    if (repoData) {
      setRepo(JSON.parse(repoData))
    } else {
      // No repo selected, go back
      navigate('/onboarding/repository')
    }
  }, [navigate])

  // Analyze repository
  const { data: analysis, isLoading } = useQuery<GitHubAnalysisResult>({
    queryKey: ['github', 'analyze', repo?.full_name],
    queryFn: async () => {
      if (!repo) return null
      const [owner, repoName] = repo.full_name.split('/')
      const response = await apiClient.get(
        `/github/repositories/${owner}/${repoName}/analyze`
      )
      return response.data
    },
    enabled: !!repo,
  })

  // Set recommended tier when analysis is ready
  useEffect(() => {
    if (analysis) {
      const rec = (analysis.recommendations?.policy_pack || 'standard') as PolicyPack
      setRecommendedTier(rec)
      setSelectedTier(rec)
    }
  }, [analysis])

  const handleContinue = () => {
    // Store analysis results and selected tier for next step
    if (analysis) {
      sessionStorage.setItem('onboarding_analysis', JSON.stringify({
        ...analysis,
        selected_tier: selectedTier
      }))
    }
    sessionStorage.setItem('onboarding_policy_pack', selectedTier)
    navigate('/onboarding/stage-mapping')
  }

  if (!repo) {
    return null
  }

  return (
    <OnboardingLayout
      step={3}
      title="Analyzing Your Repository"
      subtitle="We're analyzing your project structure to provide personalized recommendations"
    >
      <div className="space-y-4">
        {isLoading ? (
          <div className="space-y-4">
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              <p className="mt-4 text-muted-foreground">Analyzing repository structure...</p>
            </div>
          </div>
        ) : analysis ? (
          <div className="space-y-4">
            {/* Project Analysis Summary */}
            <Card>
              <CardContent className="p-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm font-medium text-muted-foreground">Project Type</div>
                    <div className="text-lg font-semibold capitalize">
                      {analysis.project_type?.replace('_', ' ') || 'Unknown'}
                    </div>
                  </div>
                  {analysis.team_size_estimate && (
                    <div>
                      <div className="text-sm font-medium text-muted-foreground">
                        Team Size Estimate
                      </div>
                      <div className="text-lg font-semibold">
                        {analysis.team_size_estimate} developers
                      </div>
                    </div>
                  )}
                </div>
                {analysis.languages && Object.keys(analysis.languages).length > 0 && (
                  <div className="mt-3">
                    <div className="text-sm font-medium text-muted-foreground">Languages</div>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {Object.entries(analysis.languages)
                        .slice(0, 5)
                        .map(([lang]) => (
                          <span
                            key={lang}
                            className="px-2 py-1 rounded bg-muted text-sm"
                          >
                            {lang}
                          </span>
                        ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Tier Selection */}
            <div>
              <h3 className="text-lg font-semibold mb-2">Choose Your Governance Level</h3>
              <p className="text-sm text-muted-foreground mb-3">
                Select based on your team's governance appetite and compliance needs.
                Higher tiers = more control but more effort.
              </p>
              {recommendedTier && (
                <div className="rounded-lg bg-blue-50 dark:bg-blue-950 p-3 text-sm text-blue-900 dark:text-blue-100 mb-3">
                  💡 Based on codebase analysis, we suggest <strong className="capitalize">{recommendedTier}</strong>.
                  But you know your team best - choose what fits your governance style.
                </div>
              )}
              <div className="grid gap-3">
                {POLICY_PACKS.map((pack) => (
                  <Card
                    key={pack.name}
                    className={`cursor-pointer transition-all ${
                      selectedTier === pack.name
                        ? 'border-primary border-2 bg-primary/5'
                        : 'hover:bg-muted/50'
                    } ${recommendedTier === pack.name && selectedTier !== pack.name ? 'ring-1 ring-blue-400' : ''}`}
                    onClick={() => setSelectedTier(pack.name)}
                  >
                    <CardContent className="p-3">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <div className="font-semibold">{pack.title}</div>
                            {recommendedTier === pack.name && (
                              <span className="text-xs px-2 py-0.5 rounded bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300">
                                Recommended
                              </span>
                            )}
                          </div>
                          <div className="text-sm text-muted-foreground">{pack.description}</div>
                          <div className="mt-2 flex flex-wrap gap-1">
                            {pack.features.slice(0, 3).map((feature, idx) => (
                              <span key={idx} className="text-xs text-muted-foreground">
                                {idx > 0 && '•'} {feature}
                              </span>
                            ))}
                          </div>
                        </div>
                        <div className={`ml-3 w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                          selectedTier === pack.name
                            ? 'border-primary bg-primary text-primary-foreground'
                            : 'border-muted-foreground/30'
                        }`}>
                          {selectedTier === pack.name && (
                            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>

            <Button size="lg" className="w-full" onClick={handleContinue}>
              Continue with {POLICY_PACKS.find((p) => p.name === selectedTier)?.title} Tier
            </Button>
          </div>
        ) : (
          <div className="text-center py-8 text-muted-foreground">
            Analysis failed. Please try again.
          </div>
        )}
      </div>

      <OnboardingProgress current={3} total={6} />
    </OnboardingLayout>
  )
}

