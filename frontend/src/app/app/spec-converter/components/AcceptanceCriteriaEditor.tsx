/**
 * Acceptance Criteria Editor Component
 * Sprint 154 Day 4 - TDD Phase 2 (GREEN)
 *
 * List manager for acceptance criteria.
 * Architecture: ADR-050 Visual Editor
 */

"use client";

import { ChangeEvent, useState } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Plus, Trash2, ChevronDown, ChevronRight, CheckSquare } from "lucide-react";
import {
  createEmptyAcceptanceCriterion,
  type AcceptanceCriterion,
} from "@/hooks/useSpecConverter";

interface AcceptanceCriteriaEditorProps {
  criteria: AcceptanceCriterion[];
  onChange: (updated: AcceptanceCriterion[]) => void;
}

interface CriterionEditorProps {
  criterion: AcceptanceCriterion;
  onChange: (updated: AcceptanceCriterion) => void;
  onRemove: () => void;
}

function CriterionEditor({ criterion, onChange, onRemove }: CriterionEditorProps) {
  const [isOpen, setIsOpen] = useState(true);

  const handleFieldChange = (
    field: keyof AcceptanceCriterion,
    value: string | boolean | string[]
  ) => {
    onChange({ ...criterion, [field]: value });
  };

  return (
    <Card className="border-l-4 border-l-green-500">
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
                {criterion.id}: {criterion.scenario || "Untitled Scenario"}
              </span>
            </button>
          </CollapsibleTrigger>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={onRemove}
            className="text-destructive hover:text-destructive"
            aria-label="Remove criterion"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>

        <CollapsibleContent>
          <CardContent className="pt-0 space-y-4">
            {/* ID and Scenario */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor={`ac-${criterion.id}-id`}>ID</Label>
                <Input
                  id={`ac-${criterion.id}-id`}
                  value={criterion.id}
                  onChange={(e: ChangeEvent<HTMLInputElement>) =>
                    handleFieldChange("id", e.target.value)
                  }
                  placeholder="AC-001"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor={`ac-${criterion.id}-scenario`}>Scenario</Label>
                <Input
                  id={`ac-${criterion.id}-scenario`}
                  value={criterion.scenario}
                  onChange={(e: ChangeEvent<HTMLInputElement>) =>
                    handleFieldChange("scenario", e.target.value)
                  }
                  placeholder="Scenario name"
                />
              </div>
            </div>

            {/* BDD Fields */}
            <div className="space-y-4 p-4 bg-muted/50 rounded-lg">
              <h4 className="font-medium text-sm text-muted-foreground">
                BDD Format (Given-When-Then)
              </h4>

              <div className="space-y-2">
                <Label htmlFor={`ac-${criterion.id}-given`}>
                  <span className="font-bold text-green-600">GIVEN</span>
                </Label>
                <Textarea
                  id={`ac-${criterion.id}-given`}
                  value={criterion.given}
                  onChange={(e: ChangeEvent<HTMLTextAreaElement>) =>
                    handleFieldChange("given", e.target.value)
                  }
                  placeholder="the initial context..."
                  rows={2}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor={`ac-${criterion.id}-when`}>
                  <span className="font-bold text-blue-600">WHEN</span>
                </Label>
                <Textarea
                  id={`ac-${criterion.id}-when`}
                  value={criterion.when}
                  onChange={(e: ChangeEvent<HTMLTextAreaElement>) =>
                    handleFieldChange("when", e.target.value)
                  }
                  placeholder="the action occurs..."
                  rows={2}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor={`ac-${criterion.id}-then`}>
                  <span className="font-bold text-purple-600">THEN</span>
                </Label>
                <Textarea
                  id={`ac-${criterion.id}-then`}
                  value={criterion.then}
                  onChange={(e: ChangeEvent<HTMLTextAreaElement>) =>
                    handleFieldChange("then", e.target.value)
                  }
                  placeholder="the expected outcome..."
                  rows={2}
                />
              </div>
            </div>

            {/* Testable Checkbox */}
            <div className="flex items-center space-x-2">
              <Checkbox
                id={`ac-${criterion.id}-testable`}
                checked={criterion.testable}
                onCheckedChange={(checked) =>
                  handleFieldChange("testable", checked === true)
                }
                aria-label="Testable"
              />
              <Label htmlFor={`ac-${criterion.id}-testable`}>
                Testable (can be automated)
              </Label>
            </div>
          </CardContent>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
}

export function AcceptanceCriteriaEditor({
  criteria,
  onChange,
}: AcceptanceCriteriaEditorProps) {
  const handleAddCriterion = () => {
    const newId = `AC-${String(criteria.length + 1).padStart(3, "0")}`;
    const newCriterion = createEmptyAcceptanceCriterion(newId);
    onChange([...criteria, newCriterion]);
  };

  const handleUpdateCriterion = (index: number, updated: AcceptanceCriterion) => {
    const newCriteria = [...criteria];
    newCriteria[index] = updated;
    onChange(newCriteria);
  };

  const handleRemoveCriterion = (index: number) => {
    const newCriteria = criteria.filter((_, i) => i !== index);
    onChange(newCriteria);
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2">
          <CheckSquare className="h-5 w-5" />
          Acceptance Criteria
        </CardTitle>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={handleAddCriterion}
        >
          <Plus className="h-4 w-4 mr-2" />
          Add Criterion
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        {criteria.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <CheckSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No acceptance criteria yet.</p>
            <p className="text-sm">
              Click "Add Criterion" to define how success is measured.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {criteria.map((criterion, index) => (
              <CriterionEditor
                key={criterion.id}
                criterion={criterion}
                onChange={(updated) => handleUpdateCriterion(index, updated)}
                onRemove={() => handleRemoveCriterion(index)}
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default AcceptanceCriteriaEditor;
