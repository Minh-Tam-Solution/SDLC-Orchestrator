/**
 * File: frontend/web/src/pages/CodegenOnboardingPage.tsx
 * Version: 1.0.0
 * Status: ACTIVE - Sprint 47 P1
 * Date: 2025-12-23
 * Authority: Frontend Lead + CTO Approved
 * Foundation: SPRINT-47-SCANNER-CONFIG-GENERATOR.md
 *
 * Description:
 * Minimal Vietnamese onboarding flow to produce a schema-valid AppBlueprint (IR)
 * and display the generated IR for copy/export.
 */

import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'

import DashboardLayout from '@/components/layout/DashboardLayout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useToast } from '@/hooks/useToast'
import apiClient, { getErrorMessage } from '@/api/client'
import { BlueprintJsonViewer } from '@/components/codegen/BlueprintJsonViewer'

// ============================================================================
// Types (mirrors backend response models)
// ============================================================================

type Locale = 'vi' | 'en'

type DomainOption = {
  key: string
  name: string
  name_en: string
  description: string
  icon: string
  example_apps: string[]
}

type FeatureOption = {
  key: string
  name: string
  description: string
}

type ScaleOption = {
  key: string
  label: string
  employee_min: number
  employee_max: number
  cgf_tier: string
}

type OnboardingSessionResponse = {
  session_id: string
  current_step: string
  completed_steps: string[]
  domain?: string | null
  app_name?: string | null
  app_name_display?: string | null
  features: string[]
  scale?: string | null
  has_blueprint: boolean
  locale: string
}

type OnboardingBlueprintResponse = {
  success: boolean
  errors: string[]
  blueprint?: Record<string, unknown> | null
  stats: Record<string, unknown>
}

export default function CodegenOnboardingPage() {
  const { toast } = useToast()
  const navigate = useNavigate()

  const [locale] = useState<Locale>('vi')
  const [sessionId, setSessionId] = useState<string | null>(null)

  const [domain, setDomain] = useState<string>('')
  const [appName, setAppName] = useState<string>('')
  const [scale, setScale] = useState<string>('')
  const [selectedFeatures, setSelectedFeatures] = useState<string[]>([])

  const [generatedBlueprint, setGeneratedBlueprint] = useState<Record<string, unknown> | null>(null)
  const [generatedStats, setGeneratedStats] = useState<Record<string, unknown> | null>(null)

  // --------------------------------------------------------------------------
  // Queries (enabled only after session is started)
  // --------------------------------------------------------------------------

  const domainsQuery = useQuery<DomainOption[]>({
    queryKey: ['codegen-onboarding', 'domains', sessionId],
    queryFn: async () => {
      const res = await apiClient.get<DomainOption[]>('/codegen/onboarding/options/domains')
      return res.data
    },
    enabled: !!sessionId,
  })

  const scalesQuery = useQuery<ScaleOption[]>({
    queryKey: ['codegen-onboarding', 'scales', sessionId],
    queryFn: async () => {
      const res = await apiClient.get<ScaleOption[]>('/codegen/onboarding/options/scales')
      return res.data
    },
    enabled: !!sessionId,
  })

  const featuresQuery = useQuery<FeatureOption[]>({
    queryKey: ['codegen-onboarding', 'features', sessionId, domain],
    queryFn: async () => {
      const res = await apiClient.get<FeatureOption[]>(`/codegen/onboarding/options/features/${domain}`)
      return res.data
    },
    enabled: !!sessionId && !!domain,
  })

  const domainOptions = domainsQuery.data ?? []
  const featureOptions = featuresQuery.data ?? []
  const scaleOptions = scalesQuery.data ?? []

  const selectedDomainMeta = useMemo(() => {
    return domainOptions.find((d) => d.key === domain)
  }, [domain, domainOptions])

  // --------------------------------------------------------------------------
  // Mutations
  // --------------------------------------------------------------------------

  const startMutation = useMutation({
    mutationFn: async () => {
      const res = await apiClient.post<OnboardingSessionResponse>('/codegen/onboarding/start', {
        locale,
      })
      return res.data
    },
    onSuccess: (data) => {
      setSessionId(data.session_id)
      setDomain('')
      setAppName('')
      setScale('')
      setSelectedFeatures([])
      setGeneratedBlueprint(null)
      setGeneratedStats(null)

      toast({
        title: 'Onboarding Started',
        description: `Session ${data.session_id} created`,
        variant: 'success',
      })
    },
    onError: (err) => {
      toast({
        title: 'Failed to start onboarding',
        description: getErrorMessage(err),
        variant: 'error',
      })
    },
  })

  const generateMutation = useMutation({
    mutationFn: async () => {
      if (!sessionId) {
        throw new Error('Session not started')
      }

      // Apply session inputs (minimal “wizard” behavior, single page)
      await apiClient.post(`/codegen/onboarding/${sessionId}/domain`, { domain })
      await apiClient.post(`/codegen/onboarding/${sessionId}/app_name`, { app_name: appName })
      await apiClient.post(`/codegen/onboarding/${sessionId}/features`, { features: selectedFeatures })
      await apiClient.post(`/codegen/onboarding/${sessionId}/scale`, { scale })

      const res = await apiClient.post<OnboardingBlueprintResponse>(
        `/codegen/onboarding/${sessionId}/generate`
      )
      return res.data
    },
    onSuccess: (data) => {
      if (!data.success || !data.blueprint) {
        toast({
          title: 'Blueprint generation failed',
          description: data.errors?.join('\n') || 'Unknown error',
          variant: 'error',
        })
        setGeneratedBlueprint(null)
        setGeneratedStats(null)
        return
      }

      setGeneratedBlueprint(data.blueprint)
      setGeneratedStats(data.stats)

      toast({
        title: 'IR Generated',
        description: 'AppBlueprint (IR) generated successfully',
        variant: 'success',
      })
    },
    onError: (err) => {
      toast({
        title: 'Failed to generate IR',
        description: getErrorMessage(err),
        variant: 'error',
      })
    },
  })

  const canGenerate = !!sessionId && !!domain && !!appName.trim() && selectedFeatures.length > 0 && !!scale

  const blueprintText = useMemo(() => {
    if (!generatedBlueprint) return ''
    return JSON.stringify(generatedBlueprint, null, 2)
  }, [generatedBlueprint])

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Vietnamese IR Onboarding</h1>
          <p className="text-muted-foreground mt-1">
            Minimal flow to generate a schema-valid AppBlueprint for Vietnamese SME domains.
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Start Session</CardTitle>
            <CardDescription>
              Creates an onboarding session and loads available domains, features, and scale tiers.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex items-center gap-3">
            <Button onClick={() => startMutation.mutate()} disabled={startMutation.isPending}>
              {startMutation.isPending ? 'Starting…' : 'Start Vietnamese Onboarding'}
            </Button>
            {sessionId && (
              <div className="text-sm text-muted-foreground">
                Session: <span className="font-mono text-xs">{sessionId}</span>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Questionnaire</CardTitle>
            <CardDescription>
              Provide domain + app name + features + scale, then generate IR.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Domain */}
            <div className="space-y-2">
              <Label>Domain</Label>
              <Select
                value={domain}
                onValueChange={(v) => {
                  setDomain(v)
                  setSelectedFeatures([])
                }}
                disabled={!sessionId || domainsQuery.isLoading}
              >
                <SelectTrigger>
                  <SelectValue placeholder={!sessionId ? 'Start session first' : 'Select a domain'} />
                </SelectTrigger>
                <SelectContent>
                  {domainOptions.map((d) => (
                    <SelectItem key={d.key} value={d.key}>
                      {d.icon} {d.name} ({d.name_en})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {selectedDomainMeta && (
                <p className="text-sm text-muted-foreground">{selectedDomainMeta.description}</p>
              )}
            </div>

            {/* App Name */}
            <div className="space-y-2">
              <Label>App name (Vietnamese OK)</Label>
              <Input
                value={appName}
                onChange={(e) => setAppName(e.target.value)}
                placeholder={!sessionId ? 'Start session first' : 'e.g., Quán Phở Ngon'}
                disabled={!sessionId}
              />
            </div>

            {/* Features */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>Features</Label>
                {sessionId && domain && featureOptions.length > 0 && (
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setSelectedFeatures(featureOptions.map(f => f.key))}
                      disabled={selectedFeatures.length === featureOptions.length}
                    >
                      Chọn tất cả
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setSelectedFeatures([])}
                      disabled={selectedFeatures.length === 0}
                    >
                      Bỏ chọn
                    </Button>
                  </div>
                )}
              </div>
              <Card className="border">
                <CardContent className="p-3">
                  {!sessionId ? (
                    <p className="text-sm text-muted-foreground">Start session first.</p>
                  ) : !domain ? (
                    <p className="text-sm text-muted-foreground">Select a domain to see features.</p>
                  ) : featuresQuery.isLoading ? (
                    <p className="text-sm text-muted-foreground">Loading features…</p>
                  ) : featureOptions.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No features found for this domain.</p>
                  ) : (
                    <ScrollArea className="h-40">
                      <div className="space-y-2 pr-3">
                        {featureOptions.map((f) => {
                          const checked = selectedFeatures.includes(f.key)
                          return (
                            <div key={f.key} className="flex items-start gap-3 rounded-md p-2 hover:bg-muted">
                              <Checkbox
                                checked={checked}
                                onCheckedChange={(nextChecked) => {
                                  const isChecked = nextChecked === true
                                  setSelectedFeatures((prev) => {
                                    if (isChecked) return prev.includes(f.key) ? prev : [...prev, f.key]
                                    return prev.filter((x) => x !== f.key)
                                  })
                                }}
                                aria-label={f.name}
                              />
                              <div className="space-y-0.5">
                                <div className="text-sm font-medium">{f.name}</div>
                                <div className="text-xs text-muted-foreground">{f.description}</div>
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    </ScrollArea>
                  )}
                </CardContent>
              </Card>
              {selectedFeatures.length > 0 && (
                <p className="text-sm text-muted-foreground">
                  Selected: <span className="font-mono text-xs">{selectedFeatures.join(', ')}</span>
                </p>
              )}
            </div>

            {/* Scale */}
            <div className="space-y-2">
              <Label>Company scale</Label>
              <Select value={scale} onValueChange={setScale} disabled={!sessionId || scalesQuery.isLoading}>
                <SelectTrigger>
                  <SelectValue placeholder={!sessionId ? 'Start session first' : 'Select a scale'} />
                </SelectTrigger>
                <SelectContent>
                  {scaleOptions.map((s) => (
                    <SelectItem key={s.key} value={s.key}>
                      {s.label} ({s.employee_min}-{s.employee_max} employees) • {s.cgf_tier}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center gap-3">
              <Button onClick={() => generateMutation.mutate()} disabled={!canGenerate || generateMutation.isPending}>
                {generateMutation.isPending ? 'Generating…' : 'Generate AppBlueprint (IR)'}
              </Button>
              {!sessionId && <span className="text-sm text-muted-foreground">Start a session to begin.</span>}
            </div>
          </CardContent>
        </Card>

        {/* Generated Blueprint with Copy Button */}
        {generatedBlueprint ? (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Generated IR (AppBlueprint)</CardTitle>
                  <CardDescription>Blueprint đã sẵn sàng cho quá trình tạo code.</CardDescription>
                </div>
                <Button
                  onClick={() => navigate('/code-generation', {
                    state: {
                      blueprint: generatedBlueprint,
                      stats: generatedStats,
                    },
                  })}
                  className="gap-2"
                >
                  Tiếp tục tạo Code
                  <span aria-hidden="true">&rarr;</span>
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <BlueprintJsonViewer blueprint={generatedBlueprint as any} />
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardHeader>
              <CardTitle>Generated IR (AppBlueprint)</CardTitle>
              <CardDescription>Copy/export this IR to use with backend IR generation endpoints.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Textarea
                value={blueprintText}
                readOnly
                placeholder="IR will appear here after generation"
                className="min-h-[280px] font-mono text-xs"
              />
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  )
}
