/**
 * Requirement Editor Component
 * Sprint 154 Day 4 - TDD Phase 2 (GREEN)
 *
 * Editable form for a single BDD requirement.
 * Architecture: ADR-050 Visual Editor
 */

"use client";

import { ChangeEvent, useState } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Card, CardContent } from "@/components/ui/card";
import { ChevronDown, ChevronRight, Trash2 } from "lucide-react";
import type { SpecRequirement, Priority } from "@/hooks/useSpecConverter";

interface RequirementEditorProps {
  requirement: SpecRequirement;
  onChange: (updated: SpecRequirement) => void;
  onRemove: () => void;
}

const PRIORITY_OPTIONS: Priority[] = ["P0", "P1", "P2", "P3"];
const TIER_OPTIONS = ["ALL", "LITE", "STANDARD", "PROFESSIONAL", "ENTERPRISE"];

export function RequirementEditor({
  requirement,
  onChange,
  onRemove,
}: RequirementEditorProps) {
  const [isOpen, setIsOpen] = useState(true);

  const handleFieldChange = (
    field: keyof SpecRequirement,
    value: string | string[]
  ) => {
    onChange({ ...requirement, [field]: value });
  };

  const handleTierToggle = (tier: string) => {
    const currentTiers = requirement.tier;
    const hasAll = currentTiers.includes("ALL");

    let newTiers: string[];
    if (tier === "ALL") {
      newTiers = ["ALL"];
    } else if (hasAll) {
      newTiers = [tier];
    } else if (currentTiers.includes(tier)) {
      newTiers = currentTiers.filter((t) => t !== tier);
      if (newTiers.length === 0) {
        newTiers = ["ALL"];
      }
    } else {
      newTiers = [...currentTiers, tier];
      if (newTiers.filter((t) => t !== "ALL").length === TIER_OPTIONS.length - 1) {
        newTiers = ["ALL"];
      }
    }

    onChange({ ...requirement, tier: newTiers });
  };

  const isTierSelected = (tier: string): boolean => {
    return requirement.tier.includes("ALL") || requirement.tier.includes(tier);
  };

  return (
    <Card className="border-l-4 border-l-primary">
      <Collapsible open={isOpen} onOpenChange={setIsOpen}>
        <div className="flex items-center justify-between p-4">
          <CollapsibleTrigger asChild>
            <button
              type="button"
              className="flex items-center gap-2 hover:text-primary"
            >
              {isOpen ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
              <span className="font-medium">
                {requirement.id}: {requirement.title || "Untitled Requirement"}
              </span>
            </button>
          </CollapsibleTrigger>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={onRemove}
            className="text-destructive hover:text-destructive"
            aria-label="Remove requirement"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>

        <CollapsibleContent>
          <CardContent className="pt-0 space-y-4">
            {/* ID and Title Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor={`req-${requirement.id}-id`}>ID</Label>
                <Input
                  id={`req-${requirement.id}-id`}
                  value={requirement.id}
                  onChange={(e: ChangeEvent<HTMLInputElement>) =>
                    handleFieldChange("id", e.target.value)
                  }
                  placeholder="REQ-001"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor={`req-${requirement.id}-title`}>Title</Label>
                <Input
                  id={`req-${requirement.id}-title`}
                  value={requirement.title}
                  onChange={(e: ChangeEvent<HTMLInputElement>) =>
                    handleFieldChange("title", e.target.value)
                  }
                  placeholder="Requirement title"
                />
              </div>
            </div>

            {/* Priority */}
            <div className="space-y-2">
              <Label htmlFor={`req-${requirement.id}-priority`}>Priority</Label>
              <select
                id={`req-${requirement.id}-priority`}
                aria-label="Priority"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                value={requirement.priority}
                onChange={(e) => handleFieldChange("priority", e.target.value)}
              >
                {PRIORITY_OPTIONS.map((priority) => (
                  <option key={priority} value={priority}>
                    {priority}
                  </option>
                ))}
              </select>
            </div>

            {/* Tier Selection */}
            <div className="space-y-2">
              <Label>Tier</Label>
              <div className="flex flex-wrap gap-4">
                {TIER_OPTIONS.map((tier) => (
                  <div key={tier} className="flex items-center space-x-2">
                    <Checkbox
                      id={`req-${requirement.id}-tier-${tier.toLowerCase()}`}
                      checked={isTierSelected(tier)}
                      onCheckedChange={() => handleTierToggle(tier)}
                    />
                    <Label
                      htmlFor={`req-${requirement.id}-tier-${tier.toLowerCase()}`}
                      className="text-sm"
                    >
                      {tier}
                    </Label>
                  </div>
                ))}
              </div>
            </div>

            {/* BDD Fields */}
            <div className="space-y-4 p-4 bg-muted/50 rounded-lg">
              <h4 className="font-medium text-sm text-muted-foreground">
                BDD Format (Given-When-Then)
              </h4>

              <div className="space-y-2">
                <Label htmlFor={`req-${requirement.id}-given`}>
                  <span className="font-bold text-green-600">GIVEN</span> (Precondition)
                </Label>
                <Textarea
                  id={`req-${requirement.id}-given`}
                  aria-label="Given"
                  value={requirement.given}
                  onChange={(e: ChangeEvent<HTMLTextAreaElement>) =>
                    handleFieldChange("given", e.target.value)
                  }
                  placeholder="the initial context or state..."
                  rows={2}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor={`req-${requirement.id}-when`}>
                  <span className="font-bold text-blue-600">WHEN</span> (Action)
                </Label>
                <Textarea
                  id={`req-${requirement.id}-when`}
                  aria-label="When"
                  value={requirement.when}
                  onChange={(e: ChangeEvent<HTMLTextAreaElement>) =>
                    handleFieldChange("when", e.target.value)
                  }
                  placeholder="the action or trigger occurs..."
                  rows={2}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor={`req-${requirement.id}-then`}>
                  <span className="font-bold text-purple-600">THEN</span> (Expected Result)
                </Label>
                <Textarea
                  id={`req-${requirement.id}-then`}
                  aria-label="Then"
                  value={requirement.then}
                  onChange={(e: ChangeEvent<HTMLTextAreaElement>) =>
                    handleFieldChange("then", e.target.value)
                  }
                  placeholder="the expected outcome..."
                  rows={2}
                />
              </div>
            </div>

            {/* User Story (Optional) */}
            <div className="space-y-2">
              <Label htmlFor={`req-${requirement.id}-userstory`}>
                User Story (Optional)
              </Label>
              <Textarea
                id={`req-${requirement.id}-userstory`}
                value={requirement.user_story || ""}
                onChange={(e: ChangeEvent<HTMLTextAreaElement>) =>
                  handleFieldChange("user_story", e.target.value)
                }
                placeholder="As a [role], I want [feature] so that [benefit]..."
                rows={2}
              />
            </div>
          </CardContent>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
}

export default RequirementEditor;
