/**
 * System Settings Types - SDLC Orchestrator
 *
 * @module frontend/src/lib/types/system-settings
 * @description TypeScript interfaces for System Settings Admin UI
 * @sdlc SDLC 5.1.3 Framework - Sprint 86 Phase 2 (ADR-027)
 * @status Sprint 86 - System Settings Admin UI
 */

// =========================================================================
// System Setting Types
// =========================================================================

/**
 * System setting category enum
 */
export type SettingCategory =
  | "security"
  | "limits"
  | "features"
  | "notifications"
  | "general"
  | "ai";

/**
 * Individual system setting item
 */
export interface SystemSettingItem {
  key: string;
  value: unknown;
  version: number;
  category: SettingCategory;
  description: string | null;
  updated_at: string;
  updated_by: string | null;
}

/**
 * System settings grouped by category
 */
export interface SystemSettingsListResponse {
  security: SystemSettingItem[];
  limits: SystemSettingItem[];
  features: SystemSettingItem[];
  notifications: SystemSettingItem[];
  general: SystemSettingItem[];
  ai: SystemSettingItem[];
}

/**
 * Update setting request
 */
export interface SystemSettingUpdate {
  value: unknown;
}

/**
 * Rollback setting request
 */
export interface SystemSettingRollback {
  target_version: number;
}

// =========================================================================
// Security Settings Types (ADR-027 Phase 1)
// =========================================================================

/**
 * Security settings keys
 */
export type SecuritySettingKey =
  | "session_timeout_minutes"
  | "max_login_attempts"
  | "mfa_required"
  | "password_min_length";

/**
 * Typed security settings for form binding
 */
export interface SecuritySettings {
  session_timeout_minutes: number;
  max_login_attempts: number;
  mfa_required: boolean;
  password_min_length: number;
}

/**
 * Security setting metadata for UI
 */
export interface SecuritySettingMeta {
  key: SecuritySettingKey;
  label: string;
  description: string;
  type: "number" | "boolean";
  min?: number;
  max?: number;
  unit?: string;
  default: number | boolean;
}

/**
 * ADR-027 Phase 1 security settings metadata
 */
export const SECURITY_SETTINGS_META: SecuritySettingMeta[] = [
  {
    key: "session_timeout_minutes",
    label: "Session Timeout",
    description: "JWT token expiry duration. Users must re-authenticate after this period.",
    type: "number",
    min: 5,
    max: 1440, // 24 hours
    unit: "minutes",
    default: 30,
  },
  {
    key: "max_login_attempts",
    label: "Max Login Attempts",
    description: "Number of failed login attempts before account lockout (30-minute lock).",
    type: "number",
    min: 1,
    max: 20,
    default: 5,
  },
  {
    key: "mfa_required",
    label: "MFA Required",
    description: "Enforce multi-factor authentication for all users (7-day grace period for setup).",
    type: "boolean",
    default: false,
  },
  {
    key: "password_min_length",
    label: "Minimum Password Length",
    description: "Minimum number of characters required for user passwords.",
    type: "number",
    min: 8,
    max: 128,
    unit: "characters",
    default: 12,
  },
];

// =========================================================================
// Limits Settings Types
// =========================================================================

/**
 * Resource limit setting keys
 */
export type LimitsSettingKey =
  | "max_projects_per_team"
  | "max_evidence_upload_mb"
  | "max_api_requests_per_minute";

/**
 * Typed limits settings for form binding
 */
export interface LimitsSettings {
  max_projects_per_team: number;
  max_evidence_upload_mb: number;
  max_api_requests_per_minute: number;
}

/**
 * Limits setting metadata for UI
 */
export interface LimitsSettingMeta {
  key: LimitsSettingKey;
  label: string;
  description: string;
  type: "number";
  min: number;
  max: number;
  unit?: string;
  default: number;
}

/**
 * Resource limits settings metadata
 */
export const LIMITS_SETTINGS_META: LimitsSettingMeta[] = [
  {
    key: "max_projects_per_team",
    label: "Max Projects per Team",
    description: "Maximum number of projects a team can create.",
    type: "number",
    min: 1,
    max: 1000,
    default: 50,
  },
  {
    key: "max_evidence_upload_mb",
    label: "Max Evidence Upload Size",
    description: "Maximum file size for evidence uploads.",
    type: "number",
    min: 1,
    max: 500,
    unit: "MB",
    default: 50,
  },
  {
    key: "max_api_requests_per_minute",
    label: "API Rate Limit",
    description: "Maximum API requests per minute per user.",
    type: "number",
    min: 10,
    max: 10000,
    unit: "req/min",
    default: 100,
  },
];

// =========================================================================
// Feature Flags Types
// =========================================================================

/**
 * Feature flag setting keys
 */
export type FeatureSettingKey =
  | "github_integration_enabled"
  | "codegen_enabled"
  | "sast_enabled";

/**
 * Typed feature settings for form binding
 */
export interface FeatureSettings {
  github_integration_enabled: boolean;
  codegen_enabled: boolean;
  sast_enabled: boolean;
}

/**
 * Feature setting metadata for UI
 */
export interface FeatureSettingMeta {
  key: FeatureSettingKey;
  label: string;
  description: string;
  type: "boolean";
  default: boolean;
}

/**
 * Feature flags settings metadata
 */
export const FEATURE_SETTINGS_META: FeatureSettingMeta[] = [
  {
    key: "github_integration_enabled",
    label: "GitHub Integration",
    description: "Enable GitHub OAuth and repository integration.",
    type: "boolean",
    default: true,
  },
  {
    key: "codegen_enabled",
    label: "Code Generation (EP-06)",
    description: "Enable IR-based code generation features.",
    type: "boolean",
    default: false,
  },
  {
    key: "sast_enabled",
    label: "SAST Integration",
    description: "Enable Semgrep static analysis security testing.",
    type: "boolean",
    default: true,
  },
];

// =========================================================================
// AI Settings Types
// =========================================================================

/**
 * AI provider setting keys
 */
export type AISettingKey =
  | "ai_primary_provider"
  | "ai_fallback_enabled"
  | "ai_max_tokens"
  | "ai_temperature";

/**
 * Typed AI settings for form binding
 */
export interface AISettings {
  ai_primary_provider: string;
  ai_fallback_enabled: boolean;
  ai_max_tokens: number;
  ai_temperature: number;
}

/**
 * AI setting metadata for UI
 */
export interface AISettingMeta {
  key: AISettingKey;
  label: string;
  description: string;
  type: "select" | "boolean" | "number";
  options?: { value: string; label: string }[];
  min?: number;
  max?: number;
  step?: number;
  default: string | boolean | number;
}

/**
 * AI provider settings metadata
 */
export const AI_SETTINGS_META: AISettingMeta[] = [
  {
    key: "ai_primary_provider",
    label: "Primary AI Provider",
    description: "Primary AI provider for code generation and analysis.",
    type: "select",
    options: [
      { value: "ollama", label: "Ollama (Self-hosted)" },
      { value: "claude", label: "Claude (Anthropic)" },
      { value: "openai", label: "OpenAI GPT-4" },
    ],
    default: "ollama",
  },
  {
    key: "ai_fallback_enabled",
    label: "Enable Fallback Chain",
    description: "Automatically fallback to secondary providers on failure.",
    type: "boolean",
    default: true,
  },
  {
    key: "ai_max_tokens",
    label: "Max Tokens",
    description: "Maximum tokens for AI responses.",
    type: "number",
    min: 256,
    max: 32768,
    default: 4096,
  },
  {
    key: "ai_temperature",
    label: "Temperature",
    description: "AI response creativity (0 = deterministic, 1 = creative).",
    type: "number",
    min: 0,
    max: 1,
    step: 0.1,
    default: 0.7,
  },
];

// =========================================================================
// Helper Functions
// =========================================================================

/**
 * Get setting value from list by key
 */
export function getSettingValue<T>(
  settings: SystemSettingItem[],
  key: string,
  defaultValue: T
): T {
  const setting = settings.find((s) => s.key === key);
  return setting ? (setting.value as T) : defaultValue;
}

/**
 * Get security settings as typed object
 */
export function getSecuritySettings(settings: SystemSettingItem[]): SecuritySettings {
  return {
    session_timeout_minutes: getSettingValue(settings, "session_timeout_minutes", 30),
    max_login_attempts: getSettingValue(settings, "max_login_attempts", 5),
    mfa_required: getSettingValue(settings, "mfa_required", false),
    password_min_length: getSettingValue(settings, "password_min_length", 12),
  };
}

/**
 * Get limits settings as typed object
 */
export function getLimitsSettings(settings: SystemSettingItem[]): LimitsSettings {
  return {
    max_projects_per_team: getSettingValue(settings, "max_projects_per_team", 50),
    max_evidence_upload_mb: getSettingValue(settings, "max_evidence_upload_mb", 50),
    max_api_requests_per_minute: getSettingValue(settings, "max_api_requests_per_minute", 100),
  };
}

/**
 * Get feature settings as typed object
 */
export function getFeatureSettings(settings: SystemSettingItem[]): FeatureSettings {
  return {
    github_integration_enabled: getSettingValue(settings, "github_integration_enabled", true),
    codegen_enabled: getSettingValue(settings, "codegen_enabled", false),
    sast_enabled: getSettingValue(settings, "sast_enabled", true),
  };
}

/**
 * Get AI settings as typed object
 */
export function getAISettings(settings: SystemSettingItem[]): AISettings {
  return {
    ai_primary_provider: getSettingValue(settings, "ai_primary_provider", "ollama"),
    ai_fallback_enabled: getSettingValue(settings, "ai_fallback_enabled", true),
    ai_max_tokens: getSettingValue(settings, "ai_max_tokens", 4096),
    ai_temperature: getSettingValue(settings, "ai_temperature", 0.7),
  };
}

/**
 * Format setting category for display
 */
export function formatCategoryName(category: SettingCategory): string {
  const names: Record<SettingCategory, string> = {
    security: "Security",
    limits: "Resource Limits",
    features: "Feature Flags",
    notifications: "Notifications",
    general: "General",
    ai: "AI Configuration",
  };
  return names[category] || category;
}

/**
 * Get category icon name (for Heroicons)
 */
export function getCategoryIcon(category: SettingCategory): string {
  const icons: Record<SettingCategory, string> = {
    security: "ShieldCheckIcon",
    limits: "AdjustmentsHorizontalIcon",
    features: "CubeIcon",
    notifications: "BellIcon",
    general: "CogIcon",
    ai: "SparklesIcon",
  };
  return icons[category] || "CogIcon";
}

/**
 * Get category description
 */
export function getCategoryDescription(category: SettingCategory): string {
  const descriptions: Record<SettingCategory, string> = {
    security: "Authentication, authorization, and access control settings",
    limits: "Resource quotas and usage limits",
    features: "Enable or disable platform features",
    notifications: "Email and in-app notification preferences",
    general: "General platform configuration",
    ai: "AI provider and model configuration",
  };
  return descriptions[category] || "";
}
