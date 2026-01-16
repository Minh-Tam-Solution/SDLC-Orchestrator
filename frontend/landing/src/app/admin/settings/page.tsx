"use client";

/**
 * System Settings Page - Next.js App Router
 * @route /admin/settings
 * @status Sprint 68 - Admin Section Migration
 * @description Database-backed system configuration with version control
 */

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  useSystemSettings,
  useUpdateSystemSetting,
  useRollbackSystemSetting,
} from "@/hooks/useAdmin";
import {
  SETTING_CATEGORY_META,
  formatSettingValue,
  type SettingCategory,
  type SystemSetting,
} from "@/lib/types/admin";
import { useToast } from "@/hooks/useToast";
import {
  ArrowLeft,
  ChevronDown,
  ChevronRight,
  Save,
  RotateCcw,
  Settings,
  Shield,
  Gauge,
  ToggleLeft,
  Bell,
  Sliders,
  Bot,
} from "lucide-react";

const CATEGORY_ICONS: Record<SettingCategory, React.ReactNode> = {
  security: <Shield className="h-5 w-5" />,
  limits: <Gauge className="h-5 w-5" />,
  features: <ToggleLeft className="h-5 w-5" />,
  notifications: <Bell className="h-5 w-5" />,
  general: <Sliders className="h-5 w-5" />,
  ai: <Bot className="h-5 w-5" />,
};

interface SettingRowProps {
  setting: SystemSetting;
  onSave: (key: string, value: unknown) => Promise<void>;
  onRollback: (key: string) => Promise<void>;
  isSaving: boolean;
  isRollingBack: boolean;
}

function SettingRow({
  setting,
  onSave,
  onRollback,
  isSaving,
  isRollingBack,
}: SettingRowProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState("");

  const handleEdit = () => {
    const valueStr =
      typeof setting.value === "object"
        ? JSON.stringify(setting.value, null, 2)
        : String(setting.value);
    setEditValue(valueStr);
    setIsEditing(true);
  };

  const handleSave = async () => {
    try {
      let parsedValue: unknown = editValue;

      // Try to parse as JSON first
      try {
        parsedValue = JSON.parse(editValue);
      } catch {
        // Keep as string if not valid JSON
      }

      await onSave(setting.key, parsedValue);
      setIsEditing(false);
    } catch {
      // Error handled by parent
    }
  };

  const handleCancel = () => {
    setIsEditing(false);
    setEditValue("");
  };

  return (
    <div className="flex items-start justify-between py-3 border-b last:border-0">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className="font-medium text-sm">{setting.key}</p>
          <Badge variant="outline" className="text-xs">
            v{setting.version}
          </Badge>
        </div>
        {setting.description && (
          <p className="text-sm text-muted-foreground mt-1">
            {setting.description}
          </p>
        )}
        {isEditing ? (
          <div className="mt-2 space-y-2">
            {typeof setting.value === "object" ? (
              <textarea
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                className="w-full h-32 p-2 text-sm font-mono bg-muted rounded border"
              />
            ) : (
              <Input
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                className="max-w-md"
              />
            )}
            <div className="flex gap-2">
              <Button size="sm" onClick={handleSave} disabled={isSaving}>
                <Save className="h-4 w-4 mr-1" />
                {isSaving ? "Saving..." : "Save"}
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={handleCancel}
                disabled={isSaving}
              >
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <div className="mt-1">
            <code className="text-sm bg-muted px-2 py-1 rounded">
              {formatSettingValue(setting.value)}
            </code>
          </div>
        )}
        {setting.updated_at && (
          <p className="text-xs text-muted-foreground mt-2">
            Last updated: {new Date(setting.updated_at).toLocaleString()}
            {setting.updated_by && ` by ${setting.updated_by}`}
          </p>
        )}
      </div>
      {!isEditing && (
        <div className="flex gap-2 ml-4">
          <Button variant="outline" size="sm" onClick={handleEdit}>
            Edit
          </Button>
          {setting.version > 1 && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onRollback(setting.key)}
              disabled={isRollingBack}
            >
              <RotateCcw className="h-4 w-4 mr-1" />
              {isRollingBack ? "..." : "Rollback"}
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

interface SettingsSectionProps {
  category: SettingCategory;
  settings: SystemSetting[];
  onSave: (key: string, value: unknown) => Promise<void>;
  onRollback: (key: string) => Promise<void>;
  isSaving: boolean;
  isRollingBack: boolean;
}

function SettingsSection({
  category,
  settings,
  onSave,
  onRollback,
  isSaving,
  isRollingBack,
}: SettingsSectionProps) {
  const [isOpen, setIsOpen] = useState(true);
  const meta = SETTING_CATEGORY_META[category];

  if (settings.length === 0) return null;

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <Card>
        <CollapsibleTrigger asChild>
          <CardHeader className="cursor-pointer hover:bg-muted/50 transition-colors">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="text-muted-foreground">
                  {CATEGORY_ICONS[category]}
                </div>
                <div>
                  <CardTitle className="flex items-center gap-2">
                    {meta.label}
                    <Badge variant="secondary" className="text-xs">
                      {settings.length}
                    </Badge>
                  </CardTitle>
                  <CardDescription>{meta.description}</CardDescription>
                </div>
              </div>
              {isOpen ? (
                <ChevronDown className="h-5 w-5 text-muted-foreground" />
              ) : (
                <ChevronRight className="h-5 w-5 text-muted-foreground" />
              )}
            </div>
          </CardHeader>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <CardContent>
            {settings.map((setting) => (
              <SettingRow
                key={setting.key}
                setting={setting}
                onSave={onSave}
                onRollback={onRollback}
                isSaving={isSaving}
                isRollingBack={isRollingBack}
              />
            ))}
          </CardContent>
        </CollapsibleContent>
      </Card>
    </Collapsible>
  );
}

export default function SystemSettingsPage() {
  const router = useRouter();
  const { toast } = useToast();

  const { data: settings, isLoading } = useSystemSettings();
  const updateMutation = useUpdateSystemSetting();
  const rollbackMutation = useRollbackSystemSetting();

  const handleSave = async (key: string, value: unknown) => {
    try {
      await updateMutation.mutateAsync({ key, data: { value } });
      toast({
        title: "Setting Updated",
        description: `${key} has been updated successfully`,
      });
    } catch (err) {
      toast({
        title: "Error",
        description: "Failed to update setting",
        variant: "destructive",
      });
      throw err;
    }
  };

  const handleRollback = async (key: string) => {
    try {
      await rollbackMutation.mutateAsync(key);
      toast({
        title: "Setting Rolled Back",
        description: `${key} has been rolled back to previous version`,
      });
    } catch {
      toast({
        title: "Error",
        description: "Failed to rollback setting",
        variant: "destructive",
      });
    }
  };

  const categories: SettingCategory[] = [
    "ai",
    "security",
    "limits",
    "features",
    "notifications",
    "general",
  ];

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.push("/admin")}
              className="h-8 w-8 p-0"
            >
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <h1 className="text-3xl font-bold tracking-tight">
              System Settings
            </h1>
          </div>
          <p className="text-muted-foreground">
            Configure system parameters with version control
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Settings className="h-5 w-5 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">
            Database-backed configuration
          </span>
        </div>
      </div>

      {/* Settings sections */}
      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <Card key={i}>
              <CardHeader>
                <div className="flex items-center gap-3">
                  <Skeleton className="h-5 w-5" />
                  <div>
                    <Skeleton className="h-6 w-32" />
                    <Skeleton className="h-4 w-64 mt-1" />
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {[1, 2, 3].map((j) => (
                    <Skeleton key={j} className="h-16 w-full" />
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : settings ? (
        <div className="space-y-4">
          {categories.map((category) => (
            <SettingsSection
              key={category}
              category={category}
              settings={settings[category] || []}
              onSave={handleSave}
              onRollback={handleRollback}
              isSaving={updateMutation.isPending}
              isRollingBack={rollbackMutation.isPending}
            />
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            No settings found
          </CardContent>
        </Card>
      )}
    </div>
  );
}
