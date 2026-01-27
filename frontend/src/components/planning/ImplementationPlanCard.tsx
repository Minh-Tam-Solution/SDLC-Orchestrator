/**
 * Implementation Plan Card - SDLC Orchestrator
 *
 * @module frontend/src/components/planning/ImplementationPlanCard
 * @description Card component for displaying implementation plan steps
 * @sdlc SDLC 5.2.0 Framework - Sprint 99 (Planning Sub-agent Part 2)
 */

import { useState } from "react";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import type { ImplementationPlan, ImplementationStep } from "@/lib/types/planning-subagent";

interface ImplementationPlanCardProps {
  plan: ImplementationPlan;
  expandedSteps?: boolean;
  className?: string;
}

interface StepCardProps {
  step: ImplementationStep;
  defaultExpanded?: boolean;
}

function StepCard({ step, defaultExpanded = false }: StepCardProps) {
  const [isOpen, setIsOpen] = useState(defaultExpanded);

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <div className="border rounded-lg overflow-hidden">
        <CollapsibleTrigger asChild>
          <button className="w-full p-4 text-left hover:bg-muted/50 transition-colors">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground font-bold text-sm">
                  {step.order}
                </span>
                <div>
                  <h4 className="font-medium">{step.title}</h4>
                  <p className="text-sm text-muted-foreground">
                    ~{step.estimated_loc} LOC | {step.estimated_hours.toFixed(1)}h
                  </p>
                </div>
              </div>
              <span className="text-muted-foreground">
                {isOpen ? "▼" : "▶"}
              </span>
            </div>
          </button>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <div className="px-4 pb-4 pt-2 border-t bg-muted/20 space-y-4">
            {/* Description */}
            <p className="text-sm">{step.description}</p>

            {/* Files to Create */}
            {step.files_to_create.length > 0 && (
              <div>
                <h5 className="text-xs font-medium text-muted-foreground mb-2">
                  Files to Create
                </h5>
                <div className="flex flex-wrap gap-1">
                  {step.files_to_create.map((file) => (
                    <Badge key={file} variant="outline" className="font-mono text-xs">
                      + {file}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Files to Modify */}
            {step.files_to_modify.length > 0 && (
              <div>
                <h5 className="text-xs font-medium text-muted-foreground mb-2">
                  Files to Modify
                </h5>
                <div className="flex flex-wrap gap-1">
                  {step.files_to_modify.map((file) => (
                    <Badge key={file} variant="secondary" className="font-mono text-xs">
                      ~ {file}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Patterns to Follow */}
            {step.patterns_to_follow.length > 0 && (
              <div>
                <h5 className="text-xs font-medium text-muted-foreground mb-2">
                  Patterns to Follow
                </h5>
                <ul className="list-disc list-inside text-sm space-y-1">
                  {step.patterns_to_follow.map((pattern, idx) => (
                    <li key={idx}>{pattern}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Tests Required */}
            {step.tests_required.length > 0 && (
              <div>
                <h5 className="text-xs font-medium text-muted-foreground mb-2">
                  Tests Required
                </h5>
                <div className="flex flex-wrap gap-1">
                  {step.tests_required.map((test) => (
                    <Badge key={test} className="bg-green-100 text-green-800 text-xs">
                      {test}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        </CollapsibleContent>
      </div>
    </Collapsible>
  );
}

export function ImplementationPlanCard({
  plan,
  expandedSteps = false,
  className,
}: ImplementationPlanCardProps) {
  return (
    <Card className={cn("", className)}>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Implementation Plan</span>
          <div className="flex items-center gap-2">
            <Badge variant="secondary">
              ~{plan.total_estimated_loc} LOC
            </Badge>
            <Badge variant="outline">
              ~{plan.total_estimated_hours.toFixed(1)} hours
            </Badge>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Summary */}
        <div className="p-4 bg-muted rounded-lg">
          <p className="text-sm">{plan.summary}</p>
        </div>

        {/* Steps */}
        <div>
          <h4 className="text-sm font-medium text-muted-foreground mb-3">
            Implementation Steps ({plan.steps.length})
          </h4>
          <div className="space-y-3">
            {plan.steps.map((step) => (
              <StepCard
                key={step.order}
                step={step}
                defaultExpanded={expandedSteps}
              />
            ))}
          </div>
        </div>

        {/* Risks */}
        {plan.risks.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-muted-foreground mb-3">
              Identified Risks
            </h4>
            <ul className="space-y-2">
              {plan.risks.map((risk, index) => (
                <li key={index} className="flex items-start gap-2 text-sm">
                  <span className="text-yellow-500">⚠</span>
                  <span>{risk}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* ADRs Referenced */}
        {plan.adrs_referenced.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-muted-foreground mb-3">
              ADRs Referenced
            </h4>
            <div className="flex flex-wrap gap-2">
              {plan.adrs_referenced.map((adr) => (
                <Badge key={adr} variant="outline" className="font-mono">
                  {adr}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default ImplementationPlanCard;
