/**
 * File: frontend/web/src/components/onboarding/PolicyPackSelection.tsx
 * Version: 1.0.0
 * Status: ACTIVE - Sprint 15 Day 5
 * Date: December 2, 2025
 * Authority: Frontend Lead + CPO Approved
 * Foundation: User-Onboarding-Flow-Architecture.md
 *
 * Description:
 * Step 4: Policy Pack Selection - 30 seconds
 * Allows users to select or confirm policy pack recommendation.
 */

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import OnboardingLayout from './OnboardingLayout'
import OnboardingProgress from './OnboardingProgress'

type PolicyPack = 'lite' | 'standard' | 'enterprise'

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
    description: 'Essential gates for small teams',
    features: ['G0.1, G0.2', 'Basic evidence tracking', 'Up to 10 projects'],
  },
  {
    name: 'standard',
    title: 'Standard',
    description: 'Complete SDLC 5.1.1 gates for growing teams',
    features: ['All gates (G0.1-G6)', 'Full evidence vault', 'Unlimited projects', 'AI recommendations'],
  },
  {
    name: 'enterprise',
    title: 'Enterprise',
    description: 'Advanced governance for large organizations',
    features: [
      'All Standard features',
      'Custom policies',
      'Advanced analytics',
      'SLA support',
      'Dedicated account manager',
    ],
  },
]

/**
 * Policy Pack Selection component (Step 4)
 *
 * Features:
 * - Show AI recommendation
 * - Allow manual override
 * - Explain differences between packs
 */
export default function PolicyPackSelection() {
  const navigate = useNavigate()
  const [selected, setSelected] = useState<PolicyPack>('standard')
  const [recommended, setRecommended] = useState<PolicyPack | null>(null)

  // Get recommendation from analysis
  useEffect(() => {
    const analysisData = sessionStorage.getItem('onboarding_analysis')
    if (analysisData) {
      const analysis = JSON.parse(analysisData)
      if (analysis.recommendations?.policy_pack) {
        const rec = analysis.recommendations.policy_pack
        setRecommended(rec)
        setSelected(rec)
      }
    }
  }, [])

  const handleContinue = () => {
    // Store selected policy pack
    sessionStorage.setItem('onboarding_policy_pack', selected)
    navigate('/onboarding/stage-mapping')
  }

  return (
    <OnboardingLayout
      step={4}
      title="Choose Your Policy Pack"
      subtitle="Select the governance level that fits your team"
    >
      <div className="space-y-4">
        {recommended && (
          <div className="rounded-lg bg-blue-50 dark:bg-blue-950 p-4 text-sm text-blue-900 dark:text-blue-100">
            💡 We recommend <strong className="capitalize">{recommended}</strong> based on your
            project analysis
          </div>
        )}

        <div className="grid gap-4">
          {POLICY_PACKS.map((pack) => (
            <Card
              key={pack.name}
              className={`cursor-pointer transition-colors ${
                selected === pack.name
                  ? 'border-primary bg-primary/5'
                  : 'hover:bg-muted'
              } ${recommended === pack.name ? 'ring-2 ring-blue-500' : ''}`}
              onClick={() => setSelected(pack.name)}
            >
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <div className="font-semibold text-lg">{pack.title}</div>
                      {recommended === pack.name && (
                        <span className="text-xs px-2 py-1 rounded bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300">
                          Recommended
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-muted-foreground mt-1">{pack.description}</div>
                    <ul className="mt-3 space-y-1 text-sm">
                      {pack.features.map((feature, idx) => (
                        <li key={idx} className="flex items-center gap-2">
                          <span className="text-primary">✓</span>
                          <span>{feature}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  {selected === pack.name && (
                    <div className="ml-4 text-primary text-xl">✓</div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <Button size="lg" className="w-full" onClick={handleContinue}>
          Continue with {POLICY_PACKS.find((p) => p.name === selected)?.title} Pack
        </Button>
      </div>

      <OnboardingProgress current={4} total={6} />
    </OnboardingLayout>
  )
}

