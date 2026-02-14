"""
Template Blueprint Schema - IR for App Builder Integration

SDLC Framework Compliance:
- Framework: SDLC 6.0.5 (7-Pillar + Section 8 Unified Specification Standard)
- Pillar 2: Design Phase - Architecture & Technical Specifications
- AI Governance Principle 4: Deterministic Intermediate Representations
- Methodology: Contract-first design pattern for AI-assisted codegen
- OpenSpec Integration: SDLC Specification Standard v6.0 compatible

Purpose:
This is the Intermediate Representation (IR) contract between:
- Planning Sub-Agent (exploration phase) → creates blueprint
- App Builder Provider (execution phase) → consumes blueprint

Ensures deterministic, auditable, and tamper-proof scaffolding workflow.
Now includes OpenSpec/SDLC Specification Standard fields for governance compliance.

Sprint: 106 - App Builder Integration (MVP)
Date: January 28, 2026
Owner: Backend Team
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional
from enum import Enum
from datetime import datetime
import hashlib
import json
import uuid


class TemplateType(str, Enum):
    """Supported template types for MVP (Sprint 106)"""
    NEXTJS_FULLSTACK = "nextjs-fullstack"
    NEXTJS_SAAS = "nextjs-saas"
    FASTAPI = "fastapi"
    REACT_NATIVE = "react-native"


class ProjectTier(str, Enum):
    """
    Project tier classification per SDLC Specification Standard v6.0.

    Determines requirement granularity and governance strictness.
    """
    LITE = "LITE"               # Small projects, minimal requirements
    STANDARD = "STANDARD"       # Typical projects, standard requirements
    PROFESSIONAL = "PROFESSIONAL"  # Regulated industries, enhanced requirements
    ENTERPRISE = "ENTERPRISE"   # Mission-critical systems, full requirements


class SpecCategory(str, Enum):
    """
    Specification category per SDLC Specification Standard v6.0.
    """
    FUNCTIONAL = "functional"
    TECHNICAL = "technical"
    SECURITY = "security"
    PERFORMANCE = "performance"
    INTEGRATION = "integration"


class EntityField(BaseModel):
    """Database field definition for entities"""
    name: str = Field(..., description="Field name (e.g., 'email', 'created_at')")
    type: str = Field(..., description="Field type: string, integer, boolean, date, relation")
    required: bool = Field(default=True, description="Whether field is required")
    unique: bool = Field(default=False, description="Whether field must be unique")
    relation_to: Optional[str] = Field(default=None, description="Foreign key relation (e.g., 'User')")
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v: str) -> str:
        valid_types = ['string', 'integer', 'boolean', 'date', 'datetime', 'relation', 'json']
        if v not in valid_types:
            raise ValueError(f"Field type must be one of: {', '.join(valid_types)}")
        return v


class Entity(BaseModel):
    """Database entity (table) definition"""
    name: str = Field(..., description="Entity name (singular, PascalCase: 'Post', 'User')")
    fields: List[EntityField] = Field(default_factory=list, description="Entity fields")
    auth_required: bool = Field(default=True, description="Whether entity requires authentication")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v[0].isupper():
            raise ValueError("Entity name must be PascalCase (e.g., 'User', not 'user')")
        return v


class APIRoute(BaseModel):
    """API endpoint definition"""
    path: str = Field(..., description="Route path (e.g., '/api/posts', '/api/users/[id]')")
    methods: List[str] = Field(..., description="HTTP methods: GET, POST, PUT, DELETE, PATCH")
    auth_required: bool = Field(default=True, description="Whether route requires authentication")
    entity: Optional[str] = Field(default=None, description="Related entity name (e.g., 'Post')")
    
    @field_validator('methods')
    @classmethod
    def validate_methods(cls, v: List[str]) -> List[str]:
        valid_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
        for method in v:
            if method not in valid_methods:
                raise ValueError(f"Method must be one of: {', '.join(valid_methods)}")
        return v


class Page(BaseModel):
    """Frontend page definition"""
    path: str = Field(..., description="Page route (e.g., '/dashboard', '/profile')")
    name: str = Field(..., description="Page display name (e.g., 'Dashboard', 'User Profile')")
    auth_required: bool = Field(default=True, description="Whether page requires authentication")
    entities_used: List[str] = Field(default_factory=list, description="Entities displayed on page")


class TemplateBlueprint(BaseModel):
    """
    Template Blueprint - IR for App Scaffolding
    
    This is the contract between Planning Sub-Agent (creates) and 
    App Builder Provider (consumes).
    
    Integrity Verification:
    - SHA256 hash computed from all fields (except blueprint_id, integrity_hash)
    - Hash verified before execution to detect tampering
    - Stored in Evidence Vault with DRAFT → APPROVED → COMPLETED lifecycle
    
    Example:
        blueprint = TemplateBlueprint(
            template_type=TemplateType.NEXTJS_SAAS,
            project_name="instagram-clone",
            tech_stack=["nextjs", "prisma", "cloudinary", "clerk"],
            entities=[
                Entity(
                    name="Post",
                    fields=[
                        EntityField(name="image_url", type="string"),
                        EntityField(name="caption", type="string"),
                        EntityField(name="created_at", type="datetime"),
                    ]
                ),
            ],
            api_routes=[
                APIRoute(path="/api/posts", methods=["GET", "POST"], entity="Post"),
            ],
            pages=[
                Page(path="/feed", name="Feed", entities_used=["Post"]),
            ],
            features=["auth", "upload", "likes"],
        ).finalize()  # Compute integrity hash
    """
    
    # Identity
    blueprint_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique blueprint identifier"
    )
    template_type: TemplateType = Field(..., description="Template to use for scaffolding")
    project_name: str = Field(..., description="Project name (lowercase, hyphen-separated)")

    # OpenSpec/SDLC Specification Standard v6.0 Fields (Section 8)
    spec_id: str = Field(
        default_factory=lambda: f"SPEC-{uuid.uuid4().hex[:8].upper()}",
        description="Unique specification identifier (OpenSpec format: SPEC-XXXX)"
    )
    tier: ProjectTier = Field(
        default=ProjectTier.STANDARD,
        description="Project tier: LITE, STANDARD, PROFESSIONAL, ENTERPRISE"
    )
    sdlc_stage: str = Field(
        default="03",
        description="Current SDLC stage (00-10). Default 03 = BUILD stage"
    )
    spec_category: SpecCategory = Field(
        default=SpecCategory.TECHNICAL,
        description="Specification category for classification"
    )
    owner: str = Field(
        default="Backend Team",
        description="Specification owner (team or person)"
    )
    description: str = Field(
        default="",
        description="Project description for specification document"
    )

    # Tech Stack
    tech_stack: List[str] = Field(
        default_factory=list,
        description="Technologies used (e.g., ['nextjs', 'prisma', 'tailwind'])"
    )
    tech_stack_overrides: Dict[str, str] = Field(
        default_factory=dict,
        description="Override default tech choices (e.g., {'orm': 'drizzle'})"
    )
    
    # Structure
    entities: List[Entity] = Field(
        default_factory=list,
        description="Database entities (tables)"
    )
    api_routes: List[APIRoute] = Field(
        default_factory=list,
        description="API endpoints to generate"
    )
    pages: List[Page] = Field(
        default_factory=list,
        description="Frontend pages to generate"
    )
    
    # Features
    features: List[str] = Field(
        default_factory=list,
        description="Features to include (e.g., ['auth', 'crud', 'upload', 'payments'])"
    )
    
    # Environment
    env_vars: List[str] = Field(
        default_factory=list,
        description="Required environment variables (e.g., ['DATABASE_URL', 'JWT_SECRET'])"
    )
    scripts: Dict[str, str] = Field(
        default_factory=dict,
        description="Package.json scripts or Makefile targets"
    )
    
    # Quality
    quality_mode: str = Field(
        default="scaffold",
        description="Quality mode: 'scaffold' (lenient) or 'production' (strict)"
    )
    
    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Blueprint creation timestamp"
    )
    created_by: Optional[str] = Field(
        default=None,
        description="User or agent that created blueprint"
    )
    
    # Integrity (Expert 3's recommendation)
    integrity_hash: str = Field(
        default="",
        description="SHA256 hash for tamper detection"
    )
    
    @field_validator('project_name')
    @classmethod
    def validate_project_name(cls, v: str) -> str:
        """Ensure project name is lowercase, hyphen-separated"""
        if not v.islower() or ' ' in v:
            raise ValueError("Project name must be lowercase with hyphens (e.g., 'my-app')")
        return v
    
    @field_validator('quality_mode')
    @classmethod
    def validate_quality_mode(cls, v: str) -> str:
        """Validate quality mode"""
        if v not in ['scaffold', 'production']:
            raise ValueError("Quality mode must be 'scaffold' or 'production'")
        return v
    
    def compute_hash(self) -> str:
        """
        Compute SHA256 hash of blueprint content

        Excludes:
        - blueprint_id (changes on each creation)
        - integrity_hash (circular dependency)
        - created_at (timestamp varies)

        Returns:
            str: Hexadecimal SHA256 hash
        """
        # Get dict excluding volatile fields, then serialize with sorted keys
        # Pydantic v2: model_dump_json doesn't support sort_keys, use json.dumps
        data = self.model_dump(
            exclude={
                'blueprint_id',
                'integrity_hash',
                'created_at',
                'created_by'
            },
            mode='json'  # Ensure JSON-serializable output
        )
        content = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def verify_integrity(self) -> bool:
        """
        Verify blueprint has not been tampered with
        
        Returns:
            bool: True if hash matches, False if tampered
        """
        if not self.integrity_hash:
            return False
        return self.integrity_hash == self.compute_hash()
    
    def finalize(self) -> "TemplateBlueprint":
        """
        Compute and set integrity hash before serialization
        
        Call this after creating/modifying blueprint and before:
        - Storing in Evidence Vault
        - Passing to App Builder Provider
        - Sending to CRP for approval
        
        Returns:
            TemplateBlueprint: Self (for method chaining)
        """
        self.integrity_hash = self.compute_hash()
        return self
    
    def get_summary(self) -> Dict[str, any]:
        """
        Get human-readable summary for CRP review

        Returns:
            Dict with counts and key details
        """
        return {
            'template': self.template_type.value,
            'project': self.project_name,
            'tech_stack': ', '.join(self.tech_stack),
            'entities': len(self.entities),
            'api_routes': len(self.api_routes),
            'pages': len(self.pages),
            'features': ', '.join(self.features),
            'quality_mode': self.quality_mode,
            # OpenSpec fields
            'spec_id': self.spec_id,
            'tier': self.tier.value,
            'sdlc_stage': self.sdlc_stage,
            'owner': self.owner,
        }

    def get_openspec_frontmatter(self) -> str:
        """
        Generate YAML frontmatter for SDLC Specification Standard v6.0.

        Returns OpenSpec-compliant YAML frontmatter for the generated spec document.
        """
        today = datetime.utcnow().strftime("%Y-%m-%d")
        features_str = ", ".join(self.features) if self.features else "scaffolding"

        return f"""---
# SDLC Specification Standard v6.0 - Generated by App Builder
spec_id: {self.spec_id}
spec_name: "{self.project_name} Application Specification"
spec_version: "1.0.0"
status: draft

# Classification
tier: {self.tier.value}
stage: "{self.sdlc_stage}"
category: {self.spec_category.value}

# Ownership
owner: "{self.owner}"
reviewers: []
approver: null

# Timestamps
created: {today}
last_updated: {today}
approved_date: null

# Relationships
related_adrs: ["ADR-040"]
related_specs: []
parent_spec: null
supersedes: null

# Tags
tags: [{', '.join([f'"{t}"' for t in self.tech_stack[:5]])}]
priority: P2
effort: M
---
"""


# Type alias for clarity
AppBuilderBlueprint = TemplateBlueprint
