/**
 * Requirements Editor Component
 * Sprint 154 Day 4 - TDD Phase 2 (GREEN)
 *
 * List manager for BDD requirements with add/remove.
 * Architecture: ADR-050 Visual Editor
 */

"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Plus, FileText } from "lucide-react";
import { RequirementEditor } from "./RequirementEditor";
import {
  createEmptyRequirement,
  type SpecRequirement,
} from "@/hooks/useSpecConverter";

interface RequirementsEditorProps {
  requirements: SpecRequirement[];
  onChange: (updated: SpecRequirement[]) => void;
}

export function RequirementsEditor({
  requirements,
  onChange,
}: RequirementsEditorProps) {
  const handleAddRequirement = () => {
    const newId = `REQ-${String(requirements.length + 1).padStart(3, "0")}`;
    const newRequirement = createEmptyRequirement(newId);
    onChange([...requirements, newRequirement]);
  };

  const handleUpdateRequirement = (index: number, updated: SpecRequirement) => {
    const newRequirements = [...requirements];
    newRequirements[index] = updated;
    onChange(newRequirements);
  };

  const handleRemoveRequirement = (index: number) => {
    const newRequirements = requirements.filter((_, i) => i !== index);
    onChange(newRequirements);
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          Requirements
        </CardTitle>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={handleAddRequirement}
        >
          <Plus className="h-4 w-4 mr-2" />
          Add Requirement
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        {requirements.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No requirements yet.</p>
            <p className="text-sm">Click "Add Requirement" to create your first one.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {requirements.map((req, index) => (
              <RequirementEditor
                key={req.id}
                requirement={req}
                onChange={(updated) => handleUpdateRequirement(index, updated)}
                onRemove={() => handleRemoveRequirement(index)}
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default RequirementsEditor;
