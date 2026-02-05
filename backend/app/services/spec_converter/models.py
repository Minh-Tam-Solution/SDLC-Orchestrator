"""
Spec Converter Models
Sprint 154 - Spec Standard Completion

Intermediate Representation (IR) Schema for specifications.

Architecture: ADR-050 (3-Layer Architecture)
- Parser Layer → IR → Renderer Layer

SDLC 6.0.3 Section 8: YAML frontmatter + BDD requirements
"""

from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


class SpecFormat(str, Enum):
    """Supported specification formats."""

    BDD = "bdd"
    OPENSPEC = "openspec"
    USER_STORY = "user_story"
    NATURAL_LANGUAGE = "natural_language"


class AcceptanceCriterion(BaseModel):
    """
    Acceptance Criterion with BDD format.

    Maps to SDLC 6.0.3 acceptance criteria table format:
    | ID | Scenario | Tier | Testable |
    """

    id: str = Field(..., description="Unique criterion ID (e.g., AC-001)")
    scenario: str = Field(..., description="Scenario description")
    given: str = Field(default="", description="GIVEN clause - initial context")
    when: str = Field(default="", description="WHEN clause - action")
    then: str = Field(default="", description="THEN clause - expected outcome")
    tier: list[str] = Field(
        default_factory=lambda: ["ALL"],
        description="Applicable tiers (LITE, STANDARD, PROFESSIONAL, ENTERPRISE, ALL)",
    )
    testable: bool = Field(default=True, description="Whether criterion is testable")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "id": "AC-001",
                "scenario": "Successful login with valid credentials",
                "given": "a registered user",
                "when": "they enter valid credentials",
                "then": "they are redirected to the dashboard",
                "tier": ["ALL"],
                "testable": True,
            }
        }


class SpecRequirement(BaseModel):
    """
    Specification Requirement with BDD format.

    Maps to SDLC 6.0.3 functional requirement format:
    GIVEN [context]
    WHEN [action]
    THEN [outcome]
    """

    id: str = Field(..., description="Requirement ID (e.g., REQ-001)")
    title: str = Field(..., description="Requirement title")
    priority: Literal["P0", "P1", "P2", "P3"] = Field(
        default="P1", description="Priority (P0: critical, P3: nice-to-have)"
    )
    tier: list[str] = Field(
        default_factory=lambda: ["ALL"],
        description="Applicable tiers",
    )
    given: str = Field(..., description="GIVEN clause - precondition/context")
    when: str = Field(..., description="WHEN clause - action/trigger")
    then: str = Field(..., description="THEN clause - expected result")
    user_story: Optional[str] = Field(
        default=None,
        description="Original user story (As a... I want... So that...)",
    )
    acceptance_criteria: list[str] = Field(
        default_factory=list,
        description="Related acceptance criteria IDs",
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "id": "REQ-001",
                "title": "User Login",
                "priority": "P0",
                "tier": ["ALL"],
                "given": "a registered user with valid credentials",
                "when": "they submit the login form",
                "then": "they are authenticated and redirected to dashboard",
                "user_story": "As a user, I want to login so that I can access my account",
                "acceptance_criteria": ["AC-001", "AC-002"],
            }
        }


class SpecIR(BaseModel):
    """
    Specification Intermediate Representation.

    Central data model for spec conversion between formats.
    Maps to SDLC 6.0.3 Section 8 YAML frontmatter.

    Attributes map to SDLC spec template fields:
    - spec_id, title, version, status (required)
    - tier, owner, last_updated (required)
    - tags, related_adrs, related_specs (optional)
    - requirements, acceptance_criteria (content)
    """

    # Required YAML frontmatter fields
    spec_id: str = Field(..., description="Unique spec ID (e.g., SPEC-0001)")
    title: str = Field(..., description="Specification title")
    version: str = Field(default="1.0.0", description="Semantic version")
    status: Literal["DRAFT", "PROPOSED", "APPROVED", "DEPRECATED"] = Field(
        default="DRAFT", description="Specification status"
    )
    tier: list[str] = Field(
        default_factory=lambda: ["LITE", "STANDARD", "PROFESSIONAL", "ENTERPRISE"],
        description="Applicable tiers",
    )
    owner: str = Field(default="", description="Team/person responsible")
    last_updated: str = Field(..., description="Last update date (ISO format)")

    # Optional metadata fields
    tags: list[str] = Field(default_factory=list, description="Classification tags")
    related_adrs: list[str] = Field(
        default_factory=list, description="Related ADR references"
    )
    related_specs: list[str] = Field(
        default_factory=list, description="Related spec references"
    )

    # Content sections
    executive_summary: str = Field(default="", description="Brief summary")
    problem_statement: str = Field(default="", description="Problem being solved")
    requirements: list[SpecRequirement] = Field(
        default_factory=list, description="Functional requirements"
    )
    acceptance_criteria: list[AcceptanceCriterion] = Field(
        default_factory=list, description="Global acceptance criteria"
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "spec_id": "SPEC-0026",
                "title": "Spec Converter Technical Specification",
                "version": "1.0.0",
                "status": "DRAFT",
                "tier": ["STANDARD", "PROFESSIONAL", "ENTERPRISE"],
                "owner": "Backend Team",
                "last_updated": "2026-02-04",
                "tags": ["spec-converter", "bdd", "openspec"],
                "related_adrs": ["ADR-050"],
                "related_specs": ["SPEC-0002"],
                "executive_summary": "Defines spec conversion capabilities",
                "problem_statement": "Need to convert between spec formats",
                "requirements": [],
                "acceptance_criteria": [],
            }
        }

    @classmethod
    def create_empty(cls, spec_id: str, title: str) -> "SpecIR":
        """
        Create an empty SpecIR with minimal fields.

        Args:
            spec_id: Unique specification ID
            title: Specification title

        Returns:
            SpecIR with defaults populated
        """
        return cls(
            spec_id=spec_id,
            title=title,
            last_updated=datetime.utcnow().isoformat(),
        )

    def add_requirement(self, requirement: SpecRequirement) -> None:
        """Add a requirement to the specification."""
        self.requirements.append(requirement)

    def add_acceptance_criterion(self, criterion: AcceptanceCriterion) -> None:
        """Add an acceptance criterion to the specification."""
        self.acceptance_criteria.append(criterion)

    def to_frontmatter_dict(self) -> dict:
        """
        Convert to YAML frontmatter dict (metadata only).

        Returns:
            Dict suitable for YAML frontmatter serialization
        """
        return {
            "spec_id": self.spec_id,
            "title": self.title,
            "version": self.version,
            "status": self.status,
            "tier": self.tier,
            "owner": self.owner,
            "last_updated": self.last_updated,
            "tags": self.tags,
            "related_adrs": self.related_adrs,
            "related_specs": self.related_specs,
        }
