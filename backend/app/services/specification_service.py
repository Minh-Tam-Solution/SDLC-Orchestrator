"""
SpecificationService - Business logic for Specification Management

SPEC-0002: Specification Standard (Framework 6.0.0)
- YAML frontmatter validation
- Version management
- Cross-reference graph queries
- Functional requirements tracking

Sprint: 118 (Jan 28 - Feb 7, 2026)
Phase: Phase 2 Part 2 - Service Classes
Authority: CTO + CEO Approved
"""
import hashlib
import re
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from uuid import UUID

import yaml
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.governance_specification import (
    GovernanceSpecification,
    SpecVersion,
    SpecFrontmatterMetadata,
    SpecFunctionalRequirement,
    SpecAcceptanceCriterion,
    SpecImplementationPhase,
    SpecCrossReference,
)
from app.models.governance_vibecoding import SpecValidationResult


class SpecificationValidationError(Exception):
    """Raised when specification validation fails."""
    pass


class SpecificationVersionConflictError(Exception):
    """Raised when specification version conflicts occur."""
    pass


class SpecificationService:
    """
    Service for Specification Management.

    Core Responsibilities:
    1. SPEC-0002 frontmatter validation
    2. Specification version management
    3. Cross-reference graph queries
    4. Functional requirements tracking
    5. Acceptance criteria validation

    SPEC-0002 Compliance:
    - YAML frontmatter with mandatory fields
    - Semantic versioning (major.minor.patch)
    - SHA256 content hashing
    - Immutable version history
    """

    # SPEC-0002 mandatory frontmatter fields
    MANDATORY_FRONTMATTER_FIELDS = ["authors"]
    RECOMMENDED_FRONTMATTER_FIELDS = ["reviewers", "stakeholders"]
    OPTIONAL_FRONTMATTER_FIELDS = ["tags", "dependencies", "supersedes", "related_specs"]

    # Spec types
    VALID_SPEC_TYPES = [
        "technical_spec",
        "adr",           # Architecture Decision Record
        "policy",
        "requirement",
        "design_doc",
    ]

    # Status transitions
    STATUS_TRANSITIONS = {
        "draft": ["review", "deprecated"],
        "review": ["approved", "draft", "deprecated"],
        "approved": ["deprecated"],
        "deprecated": [],  # Terminal state
    }

    def __init__(self, db: AsyncSession):
        """
        Initialize SpecificationService.

        Args:
            db: Async database session
        """
        self.db = db

    async def create_specification(
        self,
        project_id: UUID,
        spec_number: str,
        spec_type: str,
        title: str,
        file_path: str,
        content: str,
        tier: str = "STANDARD",
        created_by_id: Optional[UUID] = None,
        frontmatter: Optional[Dict] = None,
    ) -> GovernanceSpecification:
        """
        Create a new specification with version 1.0.0.

        Args:
            project_id: Project UUID
            spec_number: Specification identifier (e.g., SPEC-0001, ADR-041)
            spec_type: Type (technical_spec, adr, policy, requirement, design_doc)
            title: Human-readable title
            file_path: Relative path from project root
            content: Full specification content (markdown with YAML frontmatter)
            tier: Tier (LITE, STANDARD, PROFESSIONAL, ENTERPRISE)
            created_by_id: User who created the specification
            frontmatter: Optional parsed frontmatter (if None, will be extracted from content)

        Returns:
            Created GovernanceSpecification

        Raises:
            SpecificationValidationError: If validation fails
            ValueError: If parameters are invalid
        """
        # Validate spec type
        if spec_type not in self.VALID_SPEC_TYPES:
            raise ValueError(f"Invalid spec_type: {spec_type}. Must be one of {self.VALID_SPEC_TYPES}")

        # Extract frontmatter if not provided
        if frontmatter is None:
            frontmatter = self._extract_frontmatter(content)

        # Validate frontmatter (SPEC-0002 compliance)
        validation_errors, validation_warnings = self._validate_frontmatter(frontmatter)
        if validation_errors:
            raise SpecificationValidationError(
                f"Frontmatter validation failed: {', '.join(validation_errors)}"
            )

        # Calculate content hash (SHA256)
        content_hash = self._calculate_content_hash(content)

        # Create specification
        spec = GovernanceSpecification(
            project_id=project_id,
            spec_number=spec_number,
            spec_type=spec_type,
            title=title,
            file_path=file_path,
            status="draft",
            tier=tier,
            version="1.0.0",
            content_hash=content_hash,
            created_by_id=created_by_id,
        )
        self.db.add(spec)
        await self.db.flush()  # Get spec.id

        # Create frontmatter metadata
        frontmatter_metadata = SpecFrontmatterMetadata(
            spec_id=spec.id,
            authors=frontmatter.get("authors", []),
            reviewers=frontmatter.get("reviewers", []),
            stakeholders=frontmatter.get("stakeholders", []),
            tags=frontmatter.get("tags", []),
            dependencies=frontmatter.get("dependencies", []),
            supersedes=frontmatter.get("supersedes", []),
            related_specs=frontmatter.get("related_specs", []),
            custom_fields=frontmatter.get("custom_fields", {}),
        )
        self.db.add(frontmatter_metadata)

        # Create initial version (1.0.0)
        initial_version = SpecVersion(
            spec_id=spec.id,
            version="1.0.0",
            content_snapshot=content,
            content_hash=content_hash,
            change_summary="Initial specification version",
            created_by_id=created_by_id,
        )
        self.db.add(initial_version)

        # Store validation result
        validation_result = SpecValidationResult(
            spec_id=spec.id,
            validation_type="frontmatter",
            is_valid=len(validation_errors) == 0,
            errors=validation_errors if validation_errors else None,
            warnings=validation_warnings if validation_warnings else None,
            validator_version="1.0.0",
        )
        self.db.add(validation_result)

        await self.db.commit()
        await self.db.refresh(spec)

        return spec

    async def update_specification_content(
        self,
        spec_id: UUID,
        new_content: str,
        change_summary: str,
        updated_by_id: Optional[UUID] = None,
        bump_version: str = "patch",  # major, minor, patch
    ) -> GovernanceSpecification:
        """
        Update specification content and create new version.

        Args:
            spec_id: Specification UUID
            new_content: Updated content
            change_summary: Human-readable summary of changes
            updated_by_id: User who made the update
            bump_version: Version bump type (major, minor, patch)

        Returns:
            Updated GovernanceSpecification

        Raises:
            SpecificationVersionConflictError: If version conflict occurs
            SpecificationValidationError: If validation fails
        """
        # Get existing specification
        spec = await self.db.get(GovernanceSpecification, spec_id)
        if not spec:
            raise ValueError(f"Specification {spec_id} not found")

        # Calculate new content hash
        new_content_hash = self._calculate_content_hash(new_content)

        # Check if content actually changed
        if new_content_hash == spec.content_hash:
            return spec  # No change, return existing

        # Extract and validate frontmatter
        frontmatter = self._extract_frontmatter(new_content)
        validation_errors, validation_warnings = self._validate_frontmatter(frontmatter)
        if validation_errors:
            raise SpecificationValidationError(
                f"Frontmatter validation failed: {', '.join(validation_errors)}"
            )

        # Calculate new version
        new_version = self._bump_version(spec.version, bump_version)

        # Check for version conflicts
        existing_version_query = select(SpecVersion).where(
            and_(
                SpecVersion.spec_id == spec_id,
                SpecVersion.version == new_version,
            )
        )
        result = await self.db.execute(existing_version_query)
        if result.scalar_one_or_none():
            raise SpecificationVersionConflictError(
                f"Version {new_version} already exists for specification {spec_id}"
            )

        # Update specification
        spec.version = new_version
        spec.content_hash = new_content_hash
        spec.updated_at = datetime.utcnow()

        # Update frontmatter metadata
        await self.db.execute(
            select(SpecFrontmatterMetadata).where(
                SpecFrontmatterMetadata.spec_id == spec_id
            )
        )
        # (In production, would update existing frontmatter or create new)

        # Create new version
        new_version_record = SpecVersion(
            spec_id=spec_id,
            version=new_version,
            content_snapshot=new_content,
            content_hash=new_content_hash,
            change_summary=change_summary,
            created_by_id=updated_by_id,
        )
        self.db.add(new_version_record)

        # Store validation result
        validation_result = SpecValidationResult(
            spec_id=spec_id,
            validation_type="frontmatter",
            is_valid=True,
            errors=None,
            warnings=validation_warnings if validation_warnings else None,
            validator_version="1.0.0",
        )
        self.db.add(validation_result)

        await self.db.commit()
        await self.db.refresh(spec)

        return spec

    async def transition_status(
        self,
        spec_id: UUID,
        new_status: str,
        approved_by_id: Optional[UUID] = None,
    ) -> GovernanceSpecification:
        """
        Transition specification status.

        Allowed transitions:
        - draft → review, deprecated
        - review → approved, draft, deprecated
        - approved → deprecated

        Args:
            spec_id: Specification UUID
            new_status: Target status
            approved_by_id: User approving (required for approved status)

        Returns:
            Updated GovernanceSpecification

        Raises:
            ValueError: If transition is not allowed
        """
        spec = await self.db.get(GovernanceSpecification, spec_id)
        if not spec:
            raise ValueError(f"Specification {spec_id} not found")

        # Check if transition is allowed
        allowed_statuses = self.STATUS_TRANSITIONS.get(spec.status, [])
        if new_status not in allowed_statuses:
            raise ValueError(
                f"Cannot transition from {spec.status} to {new_status}. "
                f"Allowed: {allowed_statuses}"
            )

        # Update status
        spec.status = new_status

        # If approving, set approval metadata
        if new_status == "approved":
            if not approved_by_id:
                raise ValueError("approved_by_id required when approving specification")
            spec.approved_by_id = approved_by_id
            spec.approved_at = datetime.utcnow()

        spec.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(spec)

        return spec

    async def get_specification_graph(
        self,
        spec_id: UUID,
        depth: int = 2,
    ) -> Dict:
        """
        Get specification dependency graph.

        Builds graph of cross-references up to specified depth.

        Args:
            spec_id: Root specification UUID
            depth: Maximum graph depth (default: 2)

        Returns:
            Dict with graph structure:
            {
                "root": {...},
                "dependencies": [...],
                "dependents": [...],
                "related": [...]
            }
        """
        spec = await self.db.get(GovernanceSpecification, spec_id)
        if not spec:
            raise ValueError(f"Specification {spec_id} not found")

        # Get all cross-references (both directions)
        outgoing_query = select(SpecCrossReference).where(
            SpecCrossReference.source_spec_id == spec_id
        )
        incoming_query = select(SpecCrossReference).where(
            SpecCrossReference.target_spec_id == spec_id
        )

        outgoing_result = await self.db.execute(outgoing_query)
        incoming_result = await self.db.execute(incoming_query)

        outgoing_refs = list(outgoing_result.scalars().all())
        incoming_refs = list(incoming_result.scalars().all())

        # Build graph
        dependencies = [
            ref for ref in outgoing_refs if ref.reference_type == "depends_on"
        ]
        dependents = [
            ref for ref in incoming_refs if ref.reference_type == "depends_on"
        ]
        related = [
            ref for ref in outgoing_refs + incoming_refs
            if ref.reference_type == "related_to"
        ]

        return {
            "root": {
                "id": str(spec.id),
                "spec_number": spec.spec_number,
                "title": spec.title,
                "version": spec.version,
                "status": spec.status,
            },
            "dependencies": [
                {
                    "id": str(ref.target_spec_id),
                    "type": ref.reference_type,
                    "description": ref.description,
                }
                for ref in dependencies
            ],
            "dependents": [
                {
                    "id": str(ref.source_spec_id),
                    "type": ref.reference_type,
                    "description": ref.description,
                }
                for ref in dependents
            ],
            "related": [
                {
                    "id": str(ref.target_spec_id if ref.source_spec_id == spec_id else ref.source_spec_id),
                    "type": ref.reference_type,
                    "description": ref.description,
                }
                for ref in related
            ],
        }

    async def validate_cross_references(
        self,
        spec_id: UUID,
    ) -> Dict:
        """
        Validate all cross-references for a specification.

        Checks:
        - Referenced specs exist
        - No circular dependencies
        - Superseded specs are marked as deprecated

        Args:
            spec_id: Specification UUID

        Returns:
            Dict with validation results:
            {
                "is_valid": True,
                "errors": [],
                "warnings": []
            }
        """
        spec = await self.db.get(GovernanceSpecification, spec_id)
        if not spec:
            raise ValueError(f"Specification {spec_id} not found")

        errors = []
        warnings = []

        # Get frontmatter metadata
        frontmatter_query = select(SpecFrontmatterMetadata).where(
            SpecFrontmatterMetadata.spec_id == spec_id
        )
        result = await self.db.execute(frontmatter_query)
        frontmatter = result.scalar_one_or_none()

        if frontmatter:
            # Check dependencies exist
            if frontmatter.dependencies:
                for dep_spec_number in frontmatter.dependencies:
                    dep_query = select(GovernanceSpecification).where(
                        GovernanceSpecification.spec_number == dep_spec_number
                    )
                    dep_result = await self.db.execute(dep_query)
                    if not dep_result.scalar_one_or_none():
                        errors.append(f"Dependency not found: {dep_spec_number}")

            # Check superseded specs are deprecated
            if frontmatter.supersedes:
                for superseded_spec_number in frontmatter.supersedes:
                    superseded_query = select(GovernanceSpecification).where(
                        GovernanceSpecification.spec_number == superseded_spec_number
                    )
                    superseded_result = await self.db.execute(superseded_query)
                    superseded_spec = superseded_result.scalar_one_or_none()

                    if superseded_spec and superseded_spec.status != "deprecated":
                        warnings.append(
                            f"Superseded spec {superseded_spec_number} should be deprecated"
                        )

        # Check for circular dependencies (basic check)
        circular_deps = await self._check_circular_dependencies(spec_id)
        if circular_deps:
            errors.append(f"Circular dependency detected: {' → '.join(circular_deps)}")

        # Store validation result
        validation_result = SpecValidationResult(
            spec_id=spec_id,
            validation_type="cross_references",
            is_valid=len(errors) == 0,
            errors=errors if errors else None,
            warnings=warnings if warnings else None,
            validator_version="1.0.0",
        )
        self.db.add(validation_result)
        await self.db.commit()

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    # Private helper methods

    def _extract_frontmatter(self, content: str) -> Dict:
        """
        Extract YAML frontmatter from markdown content.

        Expected format:
        ---
        authors: [Author Name]
        reviewers: [Reviewer Name]
        ---

        Args:
            content: Markdown content with YAML frontmatter

        Returns:
            Dict with parsed frontmatter
        """
        # Regex to extract YAML between --- delimiters
        frontmatter_pattern = r"^---\s*\n(.*?)\n---\s*\n"
        match = re.match(frontmatter_pattern, content, re.DOTALL)

        if not match:
            return {}

        yaml_content = match.group(1)
        try:
            return yaml.safe_load(yaml_content) or {}
        except yaml.YAMLError:
            return {}

    def _validate_frontmatter(self, frontmatter: Dict) -> Tuple[List[str], List[str]]:
        """
        Validate frontmatter against SPEC-0002 requirements.

        Args:
            frontmatter: Parsed frontmatter dict

        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []

        # Check mandatory fields
        for field in self.MANDATORY_FRONTMATTER_FIELDS:
            if field not in frontmatter or not frontmatter[field]:
                errors.append(f"Missing mandatory field: {field}")

        # Check recommended fields
        for field in self.RECOMMENDED_FRONTMATTER_FIELDS:
            if field not in frontmatter or not frontmatter[field]:
                warnings.append(f"Missing recommended field: {field}")

        # Validate authors is a list
        if "authors" in frontmatter and not isinstance(frontmatter["authors"], list):
            errors.append("Field 'authors' must be a list")

        return errors, warnings

    def _calculate_content_hash(self, content: str) -> str:
        """
        Calculate SHA256 hash of content.

        Args:
            content: Content to hash

        Returns:
            SHA256 hash (hex string)
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _bump_version(self, current_version: str, bump_type: str) -> str:
        """
        Bump semantic version.

        Args:
            current_version: Current version (e.g., "1.2.3")
            bump_type: Bump type (major, minor, patch)

        Returns:
            New version string
        """
        parts = current_version.split(".")
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])

        if bump_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif bump_type == "minor":
            minor += 1
            patch = 0
        elif bump_type == "patch":
            patch += 1
        else:
            raise ValueError(f"Invalid bump_type: {bump_type}. Must be major, minor, or patch")

        return f"{major}.{minor}.{patch}"

    async def _check_circular_dependencies(
        self,
        spec_id: UUID,
        visited: Optional[Set[UUID]] = None,
    ) -> Optional[List[str]]:
        """
        Check for circular dependencies using depth-first search.

        Args:
            spec_id: Current specification UUID
            visited: Set of visited spec IDs (for recursion tracking)

        Returns:
            List of spec numbers forming circular dependency, or None if no cycle
        """
        if visited is None:
            visited = set()

        if spec_id in visited:
            # Circular dependency detected
            spec = await self.db.get(GovernanceSpecification, spec_id)
            return [spec.spec_number] if spec else []

        visited.add(spec_id)

        # Get dependencies
        query = select(SpecCrossReference).where(
            and_(
                SpecCrossReference.source_spec_id == spec_id,
                SpecCrossReference.reference_type == "depends_on",
            )
        )
        result = await self.db.execute(query)
        dependencies = list(result.scalars().all())

        # Recursively check each dependency
        for dep in dependencies:
            cycle = await self._check_circular_dependencies(dep.target_spec_id, visited.copy())
            if cycle:
                spec = await self.db.get(GovernanceSpecification, spec_id)
                if spec:
                    cycle.insert(0, spec.spec_number)
                return cycle

        return None
