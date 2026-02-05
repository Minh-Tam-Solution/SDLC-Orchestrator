/**
 * Spec Converter Visual Editor Page
 * Sprint 154 Day 4 - TDD Phase 2 (GREEN)
 *
 * Main page integrating all Visual Editor components.
 * Architecture: ADR-050 Visual Editor
 */

"use client";

import { useState, useCallback, useEffect, ChangeEvent } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Save,
  Download,
  Upload,
  CheckCircle2,
  FileCode,
  AlertTriangle,
} from "lucide-react";
import {
  MetadataPanel,
  RequirementsEditor,
  AcceptanceCriteriaEditor,
  PreviewPanel,
  TemplateSelector,
} from "./components";
import {
  useSpecConverter,
  createEmptySpecIR,
  type SpecIR,
  type SpecFormat,
  type SpecRequirement,
  type AcceptanceCriterion,
} from "@/hooks/useSpecConverter";

interface ValidationError {
  field: string;
  message: string;
}

export default function SpecConverterPage() {
  const [specIR, setSpecIR] = useState<SpecIR>(createEmptySpecIR());
  const [previewFormat, setPreviewFormat] = useState<SpecFormat>("OPENSPEC");
  const [importContent, setImportContent] = useState("");
  const [importDialogOpen, setImportDialogOpen] = useState(false);
  const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);
  const [showValidation, setShowValidation] = useState(false);

  const { parseAsync, isParsing, renderAsync, isRendering } = useSpecConverter();

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "s") {
        e.preventDefault();
        handleSave();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [specIR]);

  const handleMetadataChange = useCallback((updated: SpecIR) => {
    setSpecIR(updated);
    setShowValidation(false);
  }, []);

  const handleRequirementsChange = useCallback(
    (requirements: SpecRequirement[]) => {
      setSpecIR((prev) => ({ ...prev, requirements }));
      setShowValidation(false);
    },
    []
  );

  const handleAcceptanceCriteriaChange = useCallback(
    (acceptance_criteria: AcceptanceCriterion[]) => {
      setSpecIR((prev) => ({ ...prev, acceptance_criteria }));
      setShowValidation(false);
    },
    []
  );

  const handleTemplateSelect = useCallback((template: SpecIR) => {
    setSpecIR(template);
    setShowValidation(false);
  }, []);

  const handleFormatChange = useCallback((format: SpecFormat) => {
    setPreviewFormat(format);
  }, []);

  const validateSpec = (): ValidationError[] => {
    const errors: ValidationError[] = [];

    if (!specIR.spec_id.trim()) {
      errors.push({ field: "spec_id", message: "Spec ID is required" });
    }

    if (!specIR.title.trim()) {
      errors.push({ field: "title", message: "Title is required" });
    }

    if (!specIR.owner.trim()) {
      errors.push({ field: "owner", message: "Owner is required" });
    }

    specIR.requirements.forEach((req, index) => {
      if (!req.title.trim()) {
        errors.push({
          field: `requirements[${index}].title`,
          message: `Requirement ${req.id}: Title is required`,
        });
      }
      if (!req.given.trim()) {
        errors.push({
          field: `requirements[${index}].given`,
          message: `Requirement ${req.id}: GIVEN is required`,
        });
      }
      if (!req.when.trim()) {
        errors.push({
          field: `requirements[${index}].when`,
          message: `Requirement ${req.id}: WHEN is required`,
        });
      }
      if (!req.then.trim()) {
        errors.push({
          field: `requirements[${index}].then`,
          message: `Requirement ${req.id}: THEN is required`,
        });
      }
    });

    return errors;
  };

  const handleValidate = () => {
    const errors = validateSpec();
    setValidationErrors(errors);
    setShowValidation(true);
    console.log("Validation result:", errors.length === 0 ? "passed" : "failed");
  };

  const handleSave = async () => {
    const errors = validateSpec();
    if (errors.length > 0) {
      setValidationErrors(errors);
      setShowValidation(true);
      console.log("save blocked - validation failed");
      return;
    }

    console.log("save", specIR);
    // In real implementation, would save to backend
  };

  const handleExport = async () => {
    try {
      const result = await renderAsync({
        ir: specIR,
        target_format: previewFormat,
      });

      const extension =
        previewFormat === "BDD"
          ? ".feature"
          : previewFormat === "OPENSPEC"
          ? ".yaml"
          : ".md";
      const filename = `${specIR.spec_id}${extension}`;

      const blob = new Blob([result.content], {
        type: "text/plain;charset=utf-8",
      });
      const url = URL.createObjectURL(blob);

      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Export error:", err);
    }
  };

  const handleImport = async () => {
    if (!importContent.trim()) return;

    try {
      // Try to detect format first
      let sourceFormat: SpecFormat = "BDD";
      if (importContent.includes("spec_id:") || importContent.startsWith("---")) {
        sourceFormat = "OPENSPEC";
      } else if (importContent.toLowerCase().includes("as a ")) {
        sourceFormat = "USER_STORY";
      }

      const result = await parseAsync({
        content: importContent,
        source_format: sourceFormat,
      });

      setSpecIR(result);
      setImportDialogOpen(false);
      setImportContent("");
    } catch (err) {
      console.error("Import error:", err);
    }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <FileCode className="h-8 w-8" />
            Spec Converter
          </h1>
          <p className="text-muted-foreground">
            Create and convert specifications in BDD, OpenSpec, and User Story formats
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          <Dialog open={importDialogOpen} onOpenChange={setImportDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="outline">
                <Upload className="h-4 w-4 mr-2" />
                Import
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-lg">
              <DialogHeader>
                <DialogTitle>Import Spec</DialogTitle>
                <DialogDescription>
                  Paste spec content in BDD, OpenSpec YAML, or User Story format
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="import-content">Paste content</Label>
                  <Textarea
                    id="import-content"
                    aria-label="Paste content"
                    value={importContent}
                    onChange={(e: ChangeEvent<HTMLTextAreaElement>) =>
                      setImportContent(e.target.value)
                    }
                    placeholder="Feature: User Login&#10;  Scenario: Valid credentials&#10;    Given a registered user&#10;    When they enter valid credentials&#10;    Then they see the dashboard"
                    rows={10}
                    className="font-mono"
                  />
                </div>
              </div>
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setImportDialogOpen(false)}
                >
                  Cancel
                </Button>
                <Button onClick={handleImport} disabled={isParsing}>
                  {isParsing ? "Importing..." : "Import"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          <Button variant="outline" onClick={handleValidate}>
            <CheckCircle2 className="h-4 w-4 mr-2" />
            Validate
          </Button>

          <Button variant="outline" onClick={handleExport} disabled={isRendering}>
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>

          <Button onClick={handleSave}>
            <Save className="h-4 w-4 mr-2" />
            Save
          </Button>
        </div>
      </div>

      {/* Validation Results */}
      {showValidation && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              {validationErrors.length === 0 ? (
                <>
                  <CheckCircle2 className="h-5 w-5 text-green-500" />
                  Validation Passed
                </>
              ) : (
                <>
                  <AlertTriangle className="h-5 w-5 text-destructive" />
                  Validation Failed ({validationErrors.length} errors)
                </>
              )}
            </CardTitle>
          </CardHeader>
          {validationErrors.length > 0 && (
            <CardContent className="pt-0">
              <ul className="space-y-1 text-sm">
                {validationErrors.map((error, index) => (
                  <li key={index} className="text-destructive">
                    {error.message}
                  </li>
                ))}
              </ul>
            </CardContent>
          )}
        </Card>
      )}

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Editor */}
        <div className="lg:col-span-2 space-y-6">
          <MetadataPanel specIR={specIR} onChange={handleMetadataChange} />

          <RequirementsEditor
            requirements={specIR.requirements}
            onChange={handleRequirementsChange}
          />

          <AcceptanceCriteriaEditor
            criteria={specIR.acceptance_criteria}
            onChange={handleAcceptanceCriteriaChange}
          />
        </div>

        {/* Right Column - Preview & Templates */}
        <div className="space-y-6">
          <PreviewPanel
            specIR={specIR}
            format={previewFormat}
            onFormatChange={handleFormatChange}
          />

          <TemplateSelector onSelect={handleTemplateSelect} />
        </div>
      </div>
    </div>
  );
}
