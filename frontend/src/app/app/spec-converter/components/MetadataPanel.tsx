/**
 * Metadata Panel Component
 * Sprint 154 Day 4 - TDD Phase 2 (GREEN)
 *
 * Editable panel for spec metadata fields.
 * Architecture: ADR-050 Visual Editor
 */

"use client";

import { ChangeEvent, KeyboardEvent, useState } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { X, Plus } from "lucide-react";
import type { SpecIR, SpecStatus, SpecTier } from "@/hooks/useSpecConverter";

interface MetadataPanelProps {
  specIR: SpecIR;
  onChange: (updated: SpecIR) => void;
}

const STATUS_OPTIONS: SpecStatus[] = ["DRAFT", "PROPOSED", "APPROVED", "DEPRECATED"];
const TIER_OPTIONS: SpecTier[] = ["LITE", "STANDARD", "PROFESSIONAL", "ENTERPRISE"];

export function MetadataPanel({ specIR, onChange }: MetadataPanelProps) {
  const [newTag, setNewTag] = useState("");
  const [newAdr, setNewAdr] = useState("");
  const [newSpec, setNewSpec] = useState("");

  const handleFieldChange = (field: keyof SpecIR, value: string) => {
    onChange({ ...specIR, [field]: value });
  };

  const handleTierToggle = (tier: SpecTier) => {
    const currentTiers = specIR.tier as unknown as string[];
    const hasAll = currentTiers.includes("ALL");

    let newTiers: string[];
    if (hasAll) {
      // Switch from ALL to specific tier
      newTiers = [tier];
    } else if (currentTiers.includes(tier)) {
      // Remove tier
      newTiers = currentTiers.filter((t) => t !== tier);
      if (newTiers.length === 0) {
        newTiers = ["ALL"];
      }
    } else {
      // Add tier
      newTiers = [...currentTiers, tier];
      if (newTiers.length === TIER_OPTIONS.length) {
        newTiers = ["ALL"];
      }
    }

    onChange({ ...specIR, tier: newTiers as unknown as SpecTier[] });
  };

  const isTierSelected = (tier: SpecTier): boolean => {
    const currentTiers = specIR.tier as unknown as string[];
    return currentTiers.includes("ALL") || currentTiers.includes(tier);
  };

  const handleAddTag = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && newTag.trim()) {
      e.preventDefault();
      if (!specIR.tags.includes(newTag.trim())) {
        onChange({ ...specIR, tags: [...specIR.tags, newTag.trim()] });
      }
      setNewTag("");
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    onChange({ ...specIR, tags: specIR.tags.filter((t) => t !== tagToRemove) });
  };

  const handleAddAdr = () => {
    if (newAdr.trim() && !specIR.related_adrs.includes(newAdr.trim())) {
      onChange({ ...specIR, related_adrs: [...specIR.related_adrs, newAdr.trim()] });
      setNewAdr("");
    }
  };

  const handleRemoveAdr = (adr: string) => {
    onChange({
      ...specIR,
      related_adrs: specIR.related_adrs.filter((a) => a !== adr),
    });
  };

  const handleAddSpec = () => {
    if (newSpec.trim() && !specIR.related_specs.includes(newSpec.trim())) {
      onChange({
        ...specIR,
        related_specs: [...specIR.related_specs, newSpec.trim()],
      });
      setNewSpec("");
    }
  };

  const handleRemoveSpec = (spec: string) => {
    onChange({
      ...specIR,
      related_specs: specIR.related_specs.filter((s) => s !== spec),
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Metadata</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Spec ID */}
        <div className="space-y-2">
          <Label htmlFor="spec-id">Spec ID</Label>
          <Input
            id="spec-id"
            value={specIR.spec_id}
            onChange={(e: ChangeEvent<HTMLInputElement>) =>
              handleFieldChange("spec_id", e.target.value)
            }
            placeholder="SPEC-0001"
          />
        </div>

        {/* Title */}
        <div className="space-y-2">
          <Label htmlFor="title">Title</Label>
          <Input
            id="title"
            value={specIR.title}
            onChange={(e: ChangeEvent<HTMLInputElement>) =>
              handleFieldChange("title", e.target.value)
            }
            placeholder="Feature title"
          />
        </div>

        {/* Version */}
        <div className="space-y-2">
          <Label htmlFor="version">Version</Label>
          <Input
            id="version"
            value={specIR.version}
            onChange={(e: ChangeEvent<HTMLInputElement>) =>
              handleFieldChange("version", e.target.value)
            }
            placeholder="1.0.0"
          />
        </div>

        {/* Status */}
        <div className="space-y-2">
          <Label htmlFor="status">Status</Label>
          <select
            id="status"
            aria-label="Status"
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            value={specIR.status}
            onChange={(e) => handleFieldChange("status", e.target.value)}
          >
            {STATUS_OPTIONS.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
        </div>

        {/* Owner */}
        <div className="space-y-2">
          <Label htmlFor="owner">Owner</Label>
          <Input
            id="owner"
            type="email"
            value={specIR.owner}
            onChange={(e: ChangeEvent<HTMLInputElement>) =>
              handleFieldChange("owner", e.target.value)
            }
            placeholder="owner@example.com"
          />
        </div>

        {/* Tier Selection */}
        <div className="space-y-2">
          <Label>Tier</Label>
          <div className="flex flex-wrap gap-4">
            {TIER_OPTIONS.map((tier) => (
              <div key={tier} className="flex items-center space-x-2">
                <Checkbox
                  id={`tier-${tier.toLowerCase()}`}
                  checked={isTierSelected(tier)}
                  onCheckedChange={() => handleTierToggle(tier)}
                  aria-label={tier}
                />
                <Label htmlFor={`tier-${tier.toLowerCase()}`} className="text-sm">
                  {tier}
                </Label>
              </div>
            ))}
          </div>
        </div>

        {/* Tags */}
        <div className="space-y-2">
          <Label htmlFor="tags">Tags</Label>
          <div className="flex flex-wrap gap-2 mb-2">
            {specIR.tags.map((tag) => (
              <Badge key={tag} variant="secondary" className="flex items-center gap-1">
                {tag}
                <button
                  type="button"
                  onClick={() => handleRemoveTag(tag)}
                  className="ml-1 hover:text-destructive"
                  aria-label={`Remove ${tag}`}
                >
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            ))}
          </div>
          <Input
            id="tags"
            value={newTag}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setNewTag(e.target.value)}
            onKeyDown={handleAddTag}
            placeholder="Add tag (press Enter)"
          />
        </div>

        {/* Related ADRs */}
        <div className="space-y-2">
          <Label>Related ADRs</Label>
          <div className="flex flex-wrap gap-2 mb-2">
            {specIR.related_adrs.map((adr) => (
              <Badge key={adr} variant="outline" className="flex items-center gap-1">
                {adr}
                <button
                  type="button"
                  onClick={() => handleRemoveAdr(adr)}
                  className="ml-1 hover:text-destructive"
                  aria-label={`Remove ${adr}`}
                >
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            ))}
          </div>
          <div className="flex gap-2">
            <Input
              value={newAdr}
              onChange={(e: ChangeEvent<HTMLInputElement>) => setNewAdr(e.target.value)}
              placeholder="ADR-XXX"
              className="flex-1"
            />
            <Button type="button" size="icon" variant="outline" onClick={handleAddAdr}>
              <Plus className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Related Specs */}
        <div className="space-y-2">
          <Label>Related Specs</Label>
          <div className="flex flex-wrap gap-2 mb-2">
            {specIR.related_specs.map((spec) => (
              <Badge key={spec} variant="outline" className="flex items-center gap-1">
                {spec}
                <button
                  type="button"
                  onClick={() => handleRemoveSpec(spec)}
                  className="ml-1 hover:text-destructive"
                  aria-label={`Remove ${spec}`}
                >
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            ))}
          </div>
          <div className="flex gap-2">
            <Input
              value={newSpec}
              onChange={(e: ChangeEvent<HTMLInputElement>) => setNewSpec(e.target.value)}
              placeholder="SPEC-XXX"
              className="flex-1"
            />
            <Button type="button" size="icon" variant="outline" onClick={handleAddSpec}>
              <Plus className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default MetadataPanel;
