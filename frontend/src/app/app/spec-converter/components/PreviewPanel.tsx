/**
 * Preview Panel Component
 * Sprint 154 Day 4 - TDD Phase 2 (GREEN)
 *
 * Live preview of spec in selected format.
 * Architecture: ADR-050 Visual Editor
 */

"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Copy, Download, Eye, AlertCircle, Check } from "lucide-react";
import {
  useSpecConverter,
  type SpecIR,
  type SpecFormat,
} from "@/hooks/useSpecConverter";

interface PreviewPanelProps {
  specIR: SpecIR;
  format?: SpecFormat;
  onFormatChange?: (format: SpecFormat) => void;
}

const FORMAT_OPTIONS: { value: SpecFormat; label: string; extension: string }[] = [
  { value: "OPENSPEC", label: "OpenSpec YAML", extension: ".yaml" },
  { value: "BDD", label: "BDD (Gherkin)", extension: ".feature" },
  { value: "USER_STORY", label: "User Story", extension: ".md" },
];

export function PreviewPanel({
  specIR,
  format = "OPENSPEC",
  onFormatChange,
}: PreviewPanelProps) {
  const { renderAsync, isRendering, renderError, renderedContent } =
    useSpecConverter();
  const [copied, setCopied] = useState(false);
  const [currentFormat, setCurrentFormat] = useState<SpecFormat>(format);
  const [content, setContent] = useState<string>("");

  // Render when specIR or format changes
  useEffect(() => {
    const doRender = async () => {
      try {
        const result = await renderAsync({
          ir: specIR,
          target_format: currentFormat,
        });
        setContent(result.content);
      } catch (err) {
        console.error("Render error:", err);
      }
    };

    if (specIR.spec_id) {
      doRender();
    }
  }, [specIR, currentFormat, renderAsync]);

  const handleFormatChange = (newFormat: SpecFormat) => {
    setCurrentFormat(newFormat);
    onFormatChange?.(newFormat);
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  const handleDownload = () => {
    const formatOption = FORMAT_OPTIONS.find((f) => f.value === currentFormat);
    const extension = formatOption?.extension || ".txt";
    const filename = `${specIR.spec_id}${extension}`;

    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="flex items-center gap-2">
          <Eye className="h-5 w-5" />
          Preview
        </CardTitle>
        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={handleCopy}
            disabled={!content}
            aria-label="Copy"
          >
            {copied ? (
              <Check className="h-4 w-4 text-green-500" />
            ) : (
              <Copy className="h-4 w-4" />
            )}
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={handleDownload}
            disabled={!content}
            aria-label="Download"
          >
            <Download className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col space-y-4">
        {/* Format Selector */}
        <div className="space-y-2">
          <Label htmlFor="preview-format">Format</Label>
          <select
            id="preview-format"
            aria-label="Format"
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            value={currentFormat}
            onChange={(e) => handleFormatChange(e.target.value as SpecFormat)}
          >
            {FORMAT_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {/* Content Area */}
        <div className="flex-1 relative">
          {isRendering ? (
            <div className="absolute inset-0 flex flex-col gap-2 p-4 bg-muted rounded-lg">
              <p className="text-sm text-muted-foreground">Rendering...</p>
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-1/2" />
              <Skeleton className="h-4 w-2/3" />
              <Skeleton className="h-4 w-1/4" />
            </div>
          ) : renderError ? (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>
                Failed to render preview: {renderError.message}
              </AlertDescription>
            </Alert>
          ) : (
            <pre className="h-full overflow-auto p-4 bg-muted rounded-lg text-sm font-mono whitespace-pre-wrap">
              {content || "No content to preview"}
            </pre>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export default PreviewPanel;
