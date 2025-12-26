/**
 * File: frontend/web/src/components/onboarding/StageMapping.tsx
 * Version: 3.0.0
 * Status: ACTIVE - Sprint 49
 * Date: December 24, 2025
 * Authority: Frontend Lead + CTO Approved
 * Foundation: SDLC-Project-Structure-Standard.md (SDLC 5.1.2)
 *
 * Description:
 * Step 5: Stage Mapping - Map /docs folders to SDLC stages
 *
 * SDLC 5.1.2 Rules:
 * - Only /docs folders are stage-mapped (stages 00-09)
 * - Code folders (backend, frontend, tests) are NOT stage-mapped
 * - Structure validation shows code folders as read-only info
 * - Stage 10-archive is displayed separately
 *
 * Reference: SDLC-Enterprise-Framework/02-Core-Methodology/Documentation-Standards/SDLC-Project-Structure-Standard.md
 */

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { AlertCircle, CheckCircle2, FolderOpen, FileText, Info } from 'lucide-react'
import OnboardingLayout from './OnboardingLayout'
import OnboardingProgress from './OnboardingProgress'
import {
  SDLC_STAGES,
  type StageMappingItem,
  type StructureValidationResult,
  type GitHubAnalysisResult,
} from '@/types/api'

/**
 * Get stages for dropdown (00-09 only, exclude archive)
 */
const STAGE_OPTIONS = SDLC_STAGES.filter(s => s.code !== '10')

/**
 * Archive stage (displayed separately)
 */
const ARCHIVE_STAGE = SDLC_STAGES.find(s => s.code === '10')

/**
 * Tier badge colors
 */
const TIER_COLORS: Record<string, string> = {
  LITE: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200',
  STANDARD: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  PROFESSIONAL: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  ENTERPRISE: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200',
}

/**
 * Stage Mapping component (Step 5) - SDLC 5.1.2
 *
 * Features:
 * - Display /docs folder mappings from backend analysis
 * - Allow manual adjustment of stage assignments
 * - Show project structure validation (read-only)
 * - Separate archive folder display
 */
export default function StageMapping() {
  const navigate = useNavigate()
  const [stageMappings, setStageMappings] = useState<StageMappingItem[]>([])
  const [structureValidation, setStructureValidation] = useState<StructureValidationResult | null>(null)
  const [archiveMapping, setArchiveMapping] = useState<StageMappingItem | null>(null)
  const [recommendedTier, setRecommendedTier] = useState<string>('STANDARD')
  const [isLoading, setIsLoading] = useState(true)

  // Load analysis data from sessionStorage (set by AIAnalysis step)
  useEffect(() => {
    const analysisData = sessionStorage.getItem('onboarding_analysis')
    if (analysisData) {
      try {
        const analysis: GitHubAnalysisResult = JSON.parse(analysisData)

        // Separate archive from regular stage mappings
        const regularMappings: StageMappingItem[] = []
        let archiveItem: StageMappingItem | null = null

        for (const mapping of analysis.stage_mappings || []) {
          if (mapping.stage_code === '10') {
            archiveItem = mapping
          } else {
            regularMappings.push(mapping)
          }
        }

        setStageMappings(regularMappings)
        setArchiveMapping(archiveItem)
        setStructureValidation(analysis.structure_validation || null)
        setRecommendedTier(analysis.recommendations?.tier || 'STANDARD')
      } catch (e) {
        console.error('Failed to parse analysis data:', e)
        // Fallback to empty state - user can still proceed
      }
    }
    setIsLoading(false)
  }, [])

  const handleContinue = () => {
    // Combine regular mappings with archive for storage
    const allMappings = archiveMapping
      ? [...stageMappings, archiveMapping]
      : stageMappings

    sessionStorage.setItem('onboarding_stage_mappings', JSON.stringify(allMappings))
    navigate('/onboarding/first-gate')
  }

  const updateMapping = (index: number, stageCode: string) => {
    const stage = SDLC_STAGES.find(s => s.code === stageCode)
    if (!stage) return

    const updated = [...stageMappings]
    const item = updated[index]
    if (item) {
      item.stage_code = stageCode as StageMappingItem['stage_code']
      item.stage_name = stage.name as StageMappingItem['stage_name']
      item.is_auto_detected = false // User modified
      setStageMappings(updated)
    }
  }

  if (isLoading) {
    return (
      <OnboardingLayout
        step={5}
        title="Loading..."
        subtitle="Preparing stage mapping"
      >
        <div className="flex items-center justify-center h-48">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
        </div>
      </OnboardingLayout>
    )
  }

  return (
    <OnboardingLayout
      step={5}
      title="Map Your Documentation Structure"
      subtitle="Review and adjust folder-to-stage mappings for your /docs folders"
    >
      <div className="space-y-6">
        {/* Info Banner */}
        <div className="rounded-lg bg-blue-50 dark:bg-blue-950 p-4 text-sm">
          <div className="flex items-start gap-3">
            <Info className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
            <div className="text-blue-900 dark:text-blue-100">
              <p className="font-medium">SDLC 5.1.2 Stage Mapping</p>
              <p className="mt-1 text-blue-800 dark:text-blue-200">
                Only <code className="bg-blue-100 dark:bg-blue-900 px-1 rounded">/docs</code> folders
                are mapped to SDLC stages (00-09). Code folders are validated separately.
              </p>
            </div>
          </div>
        </div>

        {/* Stage Mappings - /docs folders only */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Documentation Stage Mapping
              </CardTitle>
              <Badge className={TIER_COLORS[recommendedTier] || TIER_COLORS['STANDARD']}>
                {recommendedTier} Tier
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            {stageMappings.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <FolderOpen className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p>No /docs folders detected in repository</p>
                <p className="text-sm mt-1">You can add documentation folders later</p>
              </div>
            ) : (
              <div className="space-y-3">
                {stageMappings.map((mapping, index) => (
                  <div
                    key={mapping.folder_path}
                    className="flex items-center gap-4 p-3 rounded-lg bg-muted/50"
                  >
                    <div className="flex-1">
                      <div className="font-mono text-sm">{mapping.folder_path}</div>
                      {mapping.confidence !== null && (
                        <div className="text-xs text-muted-foreground mt-1">
                          {mapping.is_auto_detected ? 'Auto-detected' : 'Manually set'}
                          {mapping.confidence && ` (${Math.round(mapping.confidence * 100)}% confidence)`}
                        </div>
                      )}
                    </div>
                    <div className="text-muted-foreground font-bold">→</div>
                    <Select
                      value={mapping.stage_code}
                      onValueChange={(value) => updateMapping(index, value)}
                    >
                      <SelectTrigger className="w-[320px]">
                        <SelectValue placeholder="Select stage" />
                      </SelectTrigger>
                      <SelectContent>
                        {STAGE_OPTIONS.map((stage) => (
                          <SelectItem key={stage.code} value={stage.code}>
                            <span className="font-mono">{stage.code}</span> - {stage.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                ))}
              </div>
            )}

            {/* Archive folder (if found) - displayed separately */}
            {archiveMapping && (
              <div className="mt-4 pt-4 border-t">
                <div className="flex items-center gap-4 p-3 rounded-lg bg-amber-50 dark:bg-amber-950">
                  <div className="flex-1">
                    <div className="font-mono text-sm">{archiveMapping.folder_path}</div>
                    <div className="text-xs text-amber-700 dark:text-amber-300 mt-1">
                      Archive folder (legacy documentation)
                    </div>
                  </div>
                  <div className="text-muted-foreground font-bold">→</div>
                  <Badge variant="outline" className="border-amber-500 text-amber-700 dark:text-amber-300">
                    {ARCHIVE_STAGE?.code} - {ARCHIVE_STAGE?.name}
                  </Badge>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Structure Validation - Code folders (read-only) */}
        {structureValidation && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">
                <FolderOpen className="h-5 w-5" />
                Project Structure Validation
                <span className="text-sm font-normal text-muted-foreground ml-2">
                  (Read-only)
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Code Folders */}
                <div>
                  <h4 className="text-sm font-medium mb-2">Code Folders</h4>
                  <div className="grid grid-cols-2 gap-2">
                    {Object.entries(structureValidation.code_folders).map(([folder, info]) => (
                      <div
                        key={folder}
                        className="flex items-center gap-2 p-2 rounded bg-muted/50"
                      >
                        {info.found ? (
                          <CheckCircle2 className="h-4 w-4 text-green-600" />
                        ) : (
                          <AlertCircle className="h-4 w-4 text-amber-500" />
                        )}
                        <span className="font-mono text-sm">{folder}/</span>
                        {!info.found && (
                          <Badge variant="outline" className="text-xs ml-auto">
                            {info.required_for}
                          </Badge>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Required Files */}
                <div>
                  <h4 className="text-sm font-medium mb-2">Required Files</h4>
                  <div className="grid grid-cols-2 gap-2">
                    {Object.entries(structureValidation.required_files).map(([file, info]) => (
                      <div
                        key={file}
                        className="flex items-center gap-2 p-2 rounded bg-muted/50"
                      >
                        {info.found ? (
                          <CheckCircle2 className="h-4 w-4 text-green-600" />
                        ) : (
                          <AlertCircle className="h-4 w-4 text-amber-500" />
                        )}
                        <span className="font-mono text-sm">{file}</span>
                        {!info.found && (
                          <Badge variant="outline" className="text-xs ml-auto">
                            {info.required_for}
                          </Badge>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Summary */}
                <div className="flex items-center justify-between pt-2 border-t text-sm">
                  <span className="text-muted-foreground">Structure Status</span>
                  <span>
                    <span className="text-green-600 font-medium">{structureValidation.breakdown.found}</span>
                    <span className="text-muted-foreground"> found / </span>
                    <span className="text-amber-600 font-medium">{structureValidation.breakdown.missing}</span>
                    <span className="text-muted-foreground"> missing</span>
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Navigation Buttons */}
        <div className="flex gap-2">
          <Button
            variant="outline"
            className="flex-1"
            onClick={() => navigate('/onboarding/policy-pack')}
          >
            Back
          </Button>
          <Button
            size="lg"
            className="flex-1"
            onClick={handleContinue}
          >
            Confirm Mapping
          </Button>
        </div>
      </div>

      <OnboardingProgress current={5} total={6} />
    </OnboardingLayout>
  )
}
