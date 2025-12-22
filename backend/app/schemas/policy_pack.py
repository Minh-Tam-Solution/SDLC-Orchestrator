"""
Policy Pack Schemas - OPA Policy-as-Code

SDLC Stage: 04 - BUILD
Sprint: 43 - Policy Guards & Evidence UI
Framework: SDLC 5.1.1
Epic: EP-02 AI Safety Layer v1

Purpose:
Define Pydantic schemas for Policy Packs and Policy Rules.
Used for OPA integration and policy-as-code enforcement.

Reference:
- docs/02-design/14-Technical-Specs/Policy-Guards-Design.md
- docs/04-build/05-SASE-Artifacts/BRS-2026-003-POLICY-GUARDS.yaml
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class PolicySeverity(str, Enum):
    """Policy violation severity level."""

    CRITICAL = "critical"  # Must fix immediately, blocks merge
    HIGH = "high"  # Serious issue, blocks merge
    MEDIUM = "medium"  # Should fix, configurable blocking
    LOW = "low"  # Minor issue, advisory only
    INFO = "info"  # Informational, never blocks


class PolicyTier(str, Enum):
    """Policy pack tier aligned with SDLC 4-Tier Classification."""

    LITE = "lite"  # Teams 1-2, minimal policies
    STANDARD = "standard"  # Teams 3-10, recommended policies
    PROFESSIONAL = "professional"  # Teams 10-50, comprehensive
    ENTERPRISE = "enterprise"  # Teams 50+, full governance


# ==============================================================================
# Policy Rule Schemas
# ==============================================================================


class PolicyRuleBase(BaseModel):
    """Base schema for policy rule."""

    policy_id: str = Field(
        ...,
        min_length=3,
        max_length=100,
        pattern=r"^[a-z0-9-]+$",
        description="Unique policy identifier (kebab-case)",
        examples=["no-hardcoded-secrets", "architecture-boundaries"],
    )
    name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Human-readable policy name",
        examples=["No Hardcoded Secrets"],
    )
    description: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Policy purpose and what it checks",
    )
    severity: PolicySeverity = Field(
        default=PolicySeverity.MEDIUM,
        description="Violation severity level",
    )
    blocking: bool = Field(
        default=True,
        description="If true, violations block merge",
    )
    enabled: bool = Field(
        default=True,
        description="If false, policy is skipped",
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Categorization tags",
        examples=[["security", "secrets"], ["architecture", "layers"]],
    )


class PolicyRuleCreate(PolicyRuleBase):
    """Schema for creating a policy rule."""

    rego_policy: str = Field(
        ...,
        min_length=50,
        description="Rego policy source code",
    )
    message_template: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Message shown when policy fails. Use {file}, {line} placeholders.",
        examples=["Hardcoded secret detected in {file} at line {line}"],
    )

    @field_validator("rego_policy")
    @classmethod
    def validate_rego_syntax(cls, v: str) -> str:
        """Basic Rego syntax validation."""
        required_keywords = ["package", "allow"]
        for keyword in required_keywords:
            if keyword not in v:
                raise ValueError(f"Rego policy must contain '{keyword}' keyword")
        return v


class PolicyRuleUpdate(BaseModel):
    """Schema for updating a policy rule."""

    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, min_length=10, max_length=500)
    rego_policy: Optional[str] = Field(None, min_length=50)
    severity: Optional[PolicySeverity] = None
    blocking: Optional[bool] = None
    enabled: Optional[bool] = None
    message_template: Optional[str] = Field(None, min_length=10, max_length=500)
    tags: Optional[List[str]] = None


class PolicyRuleResponse(PolicyRuleBase):
    """Schema for policy rule response."""

    id: UUID
    policy_pack_id: UUID
    rego_policy: str
    message_template: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==============================================================================
# Validator Config Schema
# ==============================================================================


class ValidatorConfigSchema(BaseModel):
    """Configuration for a validator in the pipeline."""

    name: str = Field(
        ...,
        description="Validator name (lint, test, coverage, security, policy_guards)",
    )
    enabled: bool = Field(default=True)
    blocking: bool = Field(default=True)
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Validator-specific configuration",
    )


# ==============================================================================
# Policy Pack Schemas
# ==============================================================================


class PolicyPackBase(BaseModel):
    """Base schema for policy pack."""

    name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Policy pack name",
        examples=["AI Safety Standard Pack"],
    )
    description: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Policy pack purpose and scope",
    )
    version: str = Field(
        ...,
        pattern=r"^\d+\.\d+\.\d+$",
        description="Semantic version",
        examples=["1.0.0"],
    )
    tier: PolicyTier = Field(
        default=PolicyTier.STANDARD,
        description="SDLC 4-Tier Classification",
    )


class PolicyPackCreate(PolicyPackBase):
    """Schema for creating a policy pack."""

    # Validator configurations
    validators: List[ValidatorConfigSchema] = Field(
        default_factory=list,
        description="Validator pipeline configuration",
    )

    # Coverage settings
    coverage_threshold: int = Field(
        default=80,
        ge=0,
        le=100,
        description="Minimum test coverage percentage",
    )
    coverage_blocking: bool = Field(
        default=False,
        description="If true, coverage below threshold blocks merge",
    )

    # Architecture rules
    forbidden_imports: List[str] = Field(
        default_factory=list,
        description="Import patterns to forbid",
        examples=[["minio", "grafana_sdk"]],
    )
    required_patterns: List[str] = Field(
        default_factory=list,
        description="Required code patterns (regex)",
        examples=[["from app.core.logging import"]],
    )

    # Custom OPA policies (optional, can add later)
    policies: List[PolicyRuleCreate] = Field(
        default_factory=list,
        description="Custom OPA policies for this pack",
    )


class PolicyPackUpdate(BaseModel):
    """Schema for updating a policy pack."""

    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, min_length=10, max_length=1000)
    version: Optional[str] = Field(None, pattern=r"^\d+\.\d+\.\d+$")
    tier: Optional[PolicyTier] = None
    validators: Optional[List[ValidatorConfigSchema]] = None
    coverage_threshold: Optional[int] = Field(None, ge=0, le=100)
    coverage_blocking: Optional[bool] = None
    forbidden_imports: Optional[List[str]] = None
    required_patterns: Optional[List[str]] = None


class PolicyPackResponse(PolicyPackBase):
    """Schema for policy pack response."""

    id: UUID
    project_id: UUID
    validators: List[ValidatorConfigSchema]
    coverage_threshold: int
    coverage_blocking: bool
    forbidden_imports: List[str]
    required_patterns: List[str]
    policies_count: int
    validators_count: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None

    class Config:
        from_attributes = True


class PolicyPackWithRules(PolicyPackResponse):
    """Policy pack with all rules included."""

    policies: List[PolicyRuleResponse] = Field(default_factory=list)


# ==============================================================================
# Policy Evaluation Schemas
# ==============================================================================


class PolicyViolation(BaseModel):
    """Single policy violation detail."""

    file: str = Field(..., description="File path where violation occurred")
    line: Optional[int] = Field(None, description="Line number if available")
    message: str = Field(..., description="Violation description")
    pattern: Optional[str] = Field(None, description="Pattern that matched")


class PolicyResult(BaseModel):
    """Result of evaluating a single policy."""

    policy_id: str
    policy_name: str
    passed: bool
    severity: PolicySeverity
    blocking: bool
    message: Optional[str] = None
    violations: List[PolicyViolation] = Field(default_factory=list)
    evaluation_time_ms: int = Field(
        ...,
        ge=0,
        description="Time taken to evaluate this policy",
    )


class PolicyEvaluationRequest(BaseModel):
    """Request to evaluate policies against files."""

    files: List[Dict[str, Any]] = Field(
        ...,
        description="List of files with path and content",
    )
    diff: str = Field(
        default="",
        description="Unified diff of changes",
    )


class PolicyEvaluationResponse(BaseModel):
    """Response from policy evaluation."""

    project_id: UUID
    pr_number: int
    policy_pack_id: UUID

    # Results
    total_policies: int
    passed_count: int
    failed_count: int
    blocked: bool

    # Details
    results: List[PolicyResult]
    blocking_violations: List[PolicyResult] = Field(default_factory=list)
    warnings: List[PolicyResult] = Field(default_factory=list)

    # Timing
    started_at: datetime
    completed_at: datetime
    duration_ms: int


class PolicyEvaluationHistoryResponse(BaseModel):
    """Historical policy evaluation record."""

    id: UUID
    project_id: UUID
    pr_number: int
    policy_pack_id: Optional[UUID]
    total_policies: int
    passed_count: int
    failed_count: int
    blocked: bool
    duration_ms: int
    created_at: datetime

    class Config:
        from_attributes = True


# ==============================================================================
# Default Policy Templates
# ==============================================================================


def get_default_policies() -> List[PolicyRuleCreate]:
    """Get default AI safety policies."""
    return [
        PolicyRuleCreate(
            policy_id="no-hardcoded-secrets",
            name="No Hardcoded Secrets",
            description="Detects hardcoded passwords, API keys, tokens, and other secrets in code",
            rego_policy='''package ai_safety.no_hardcoded_secrets

import future.keywords.in

default allow = true

# Deny if hardcoded secrets detected
allow = false {
    count(violations) > 0
}

violations[violation] {
    some file in input.files
    some i, line in split(file.content, "\\n")
    contains_secret(line)
    violation := {
        "file": file.path,
        "line": i + 1,
        "pattern": "hardcoded secret",
    }
}

contains_secret(line) {
    patterns := [
        `password\\s*=\\s*["'][^"']+["']`,
        `api_key\\s*=\\s*["'][^"']+["']`,
        `secret\\s*=\\s*["'][^"']+["']`,
        `token\\s*=\\s*["'][A-Za-z0-9+/=]{20,}["']`,
        `AWS_ACCESS_KEY_ID\\s*=\\s*["'][A-Z0-9]{20}["']`,
        `AWS_SECRET_ACCESS_KEY\\s*=\\s*["'][A-Za-z0-9+/]{40}["']`,
    ]
    some pattern in patterns
    regex.match(pattern, line)
}

# Exclude test files and examples
allow = true {
    some file in input.files
    contains(file.path, "/tests/")
}

allow = true {
    some file in input.files
    endswith(file.path, ".example")
}''',
            severity=PolicySeverity.CRITICAL,
            blocking=True,
            message_template="Hardcoded secret detected in {file} at line {line}",
            tags=["security", "secrets"],
        ),
        PolicyRuleCreate(
            policy_id="architecture-boundaries",
            name="Architecture Boundaries",
            description="Enforces 4-layer architecture by preventing cross-layer imports",
            rego_policy='''package ai_safety.architecture_boundaries

import future.keywords.in

default allow = true

# Deny if layer violations detected
allow = false {
    count(violations) > 0
}

violations[violation] {
    some file in input.files
    file.layer == "presentation"
    some import_stmt in file.imports
    is_data_layer_import(import_stmt)
    violation := {
        "file": file.path,
        "import": import_stmt,
        "message": "Presentation layer cannot directly import from data layer",
    }
}

# Data layer imports
is_data_layer_import(import_stmt) {
    data_layer_packages := [
        "app.db",
        "app.repositories",
        "sqlalchemy",
        "databases",
    ]
    some pkg in data_layer_packages
    startswith(import_stmt, pkg)
}''',
            severity=PolicySeverity.HIGH,
            blocking=True,
            message_template="Architecture violation in {file}: {message}",
            tags=["architecture", "layers"],
        ),
        PolicyRuleCreate(
            policy_id="no-forbidden-imports",
            name="No Forbidden Imports",
            description="Prevents importing forbidden packages (AGPL libraries, deprecated modules)",
            rego_policy='''package ai_safety.no_forbidden_imports

import future.keywords.in

default allow = true

allow = false {
    count(violations) > 0
}

violations[violation] {
    some file in input.files
    some import_stmt in file.imports
    is_forbidden_import(import_stmt)
    violation := {
        "file": file.path,
        "import": import_stmt,
        "message": sprintf("Forbidden import: %s", [import_stmt]),
    }
}

is_forbidden_import(import_stmt) {
    some forbidden in input.config.forbidden_imports
    startswith(import_stmt, forbidden)
}''',
            severity=PolicySeverity.CRITICAL,
            blocking=True,
            message_template="Forbidden import '{import}' in {file}",
            tags=["architecture", "imports", "agpl"],
        ),
    ]
