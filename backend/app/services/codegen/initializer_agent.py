"""
=========================================================================
Initializer Agent Service - ADR-055 Phase 1
SDLC Orchestrator - Sprint 176 (Autonomous Codegen)

Version: 1.0.0
Date: 2026-02-18
Status: ACTIVE - Sprint 176
Authority: CTO Approved (ADR-055)
Reference: ADR-055-Autonomous-Codegen-Pipeline.md

Purpose:
- Parse YAML/JSON blueprint specifications
- Extract features with dependency graph resolution
- Estimate feature complexity (simple/medium/complex)
- Generate feature_list.json for Coding Agent consumption
- Validate spec completeness for Gate G1 readiness

Two-Agent Pattern (ADR-055):
  1. Initializer Agent (this) — spec → feature_list.json
  2. Coding Agent (Sprint 177) — feature_list.json → code per feature

Interface:
  async def initialize(spec, project_id, mode) → InitializationResult
  async def validate_spec(spec) → SpecValidationResult

Complexity Estimation:
  SIMPLE:  ≤3 files (CRUD entity, no relations)
  MEDIUM:  4-8 files (entity + relations + business logic)
  COMPLEX: >8 files (multi-entity feature with workflows)

Zero Mock Policy: Production-ready service
=========================================================================
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.services.codegen.schemas.app_blueprint import (
    AppBlueprint,
    ModuleSpec,
    EntitySpec,
)

logger = logging.getLogger(__name__)


# =========================================================================
# Data Models
# =========================================================================


class FeatureComplexity(str, Enum):
    """Feature complexity classification."""

    SIMPLE = "simple"      # ≤3 files: CRUD entity, no relations
    MEDIUM = "medium"      # 4-8 files: entity + relations + business logic
    COMPLEX = "complex"    # >8 files: multi-entity + workflows


class FeatureStatus(str, Enum):
    """Feature processing status in the pipeline."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ExtractedFeature(BaseModel):
    """A feature extracted from the spec with metadata."""

    id: str = Field(..., description="Feature ID (e.g., 'feat-001')")
    name: str = Field(..., description="Feature name (e.g., 'User Authentication')")
    module: str = Field(..., description="Parent module name")
    description: str = Field(..., description="Feature description")
    complexity: FeatureComplexity = Field(..., description="Estimated complexity")
    dependencies: list[str] = Field(default_factory=list, description="Feature IDs this depends on")
    priority: int = Field(..., ge=0, description="Priority order (0 = cross-cutting first, 1+ = feature order)")
    estimated_files: int = Field(..., ge=1, description="Estimated number of files to generate")
    entities: list[str] = Field(default_factory=list, description="Entity names in this feature")
    status: FeatureStatus = Field(default=FeatureStatus.PENDING)


class DependencyEdge(BaseModel):
    """Edge in the dependency graph."""

    source: str = Field(..., description="Source feature ID")
    target: str = Field(..., description="Target feature ID (dependency)")
    reason: str = Field(..., description="Why this dependency exists")


class SpecValidationResult(BaseModel):
    """Result of spec validation for Gate G1 readiness."""

    spec_complete: bool = Field(..., description="Whether spec has all required fields")
    errors: list[str] = Field(default_factory=list, description="Blocking errors")
    warnings: list[str] = Field(default_factory=list, description="Non-blocking warnings")
    gate_g1_ready: bool = Field(..., description="Whether spec is ready for Gate G1")
    checked_at: datetime = Field(default_factory=datetime.utcnow)


class InitializationResult(BaseModel):
    """Output of the Initializer Agent — the feature_list.json structure."""

    project_id: UUID
    spec_version: str = "1.0"
    mode: str
    blueprint_name: str
    total_features: int
    features: list[ExtractedFeature]
    dependency_graph: list[DependencyEdge]
    validation: SpecValidationResult
    initialized_at: datetime = Field(default_factory=datetime.utcnow)
    initialized_by: str = "initializer-agent-v1"


# =========================================================================
# Initializer Agent Service
# =========================================================================


class InitializerAgent:
    """
    Initializer Agent — ADR-055 Phase 1.

    Parses blueprint specifications and produces a structured feature list
    with dependency resolution and complexity estimation. The output
    (feature_list.json) feeds into the Coding Agent (Sprint 177).

    Usage:
        agent = InitializerAgent()
        result = await agent.initialize(blueprint, project_id, mode="scaffold")
        if result.validation.gate_g1_ready:
            # Proceed to coding
            ...
    """

    async def initialize(
        self,
        blueprint: AppBlueprint,
        project_id: UUID,
        mode: Literal["scaffold", "production"] = "scaffold",
    ) -> InitializationResult:
        """
        Initialize a codegen session from a blueprint specification.

        Args:
            blueprint: Parsed AppBlueprint IR specification
            project_id: UUID of the project
            mode: Generation mode — scaffold (lenient) or production (strict)

        Returns:
            InitializationResult with features, dependencies, and validation status
        """
        logger.info(
            "Initializing project %s from blueprint '%s' in %s mode",
            project_id,
            blueprint.name,
            mode,
        )

        # Step 1: Validate the spec
        validation = self.validate_spec(blueprint, mode)

        # Step 2: Extract features from modules
        features = self._extract_features(blueprint)

        # Step 3: Resolve dependency graph
        dependency_graph = self._resolve_dependencies(features, blueprint)

        # Step 4: Apply topological sort for priority ordering
        features = self._apply_priority_ordering(features, dependency_graph)

        result = InitializationResult(
            project_id=project_id,
            spec_version="1.0",
            mode=mode,
            blueprint_name=blueprint.name,
            total_features=len(features),
            features=features,
            dependency_graph=dependency_graph,
            validation=validation,
        )

        logger.info(
            "Initialization complete: %d features, %d dependencies, g1_ready=%s",
            result.total_features,
            len(dependency_graph),
            validation.gate_g1_ready,
        )

        return result

    def validate_spec(
        self,
        blueprint: AppBlueprint,
        mode: Literal["scaffold", "production"] = "scaffold",
    ) -> SpecValidationResult:
        """
        Validate blueprint completeness for Gate G1.

        Args:
            blueprint: The blueprint to validate
            mode: scaffold allows missing descriptions; production requires everything

        Returns:
            SpecValidationResult with errors, warnings, and gate readiness
        """
        errors: list[str] = []
        warnings: list[str] = []

        # Required: at least one module
        if not blueprint.modules:
            errors.append("Blueprint has no modules defined")

        # Required: each module has at least one entity
        for module in blueprint.modules:
            if not module.entities:
                if mode == "production":
                    errors.append(f"Module '{module.name}' has no entities")
                else:
                    warnings.append(f"Module '{module.name}' has no entities")

            # Required: each entity has at least one field
            for entity in module.entities:
                if not entity.fields:
                    errors.append(
                        f"Entity '{entity.name}' in module '{module.name}' has no fields"
                    )

                # Required: entity has a primary key field
                has_pk = any(f.primary for f in entity.fields)
                if not has_pk:
                    warnings.append(
                        f"Entity '{entity.name}' has no primary key field "
                        f"(will auto-generate UUID pk)"
                    )

        # Production mode: descriptions required
        if mode == "production":
            if not blueprint.description:
                errors.append("Blueprint description is required in production mode")
            for module in blueprint.modules:
                if not module.description:
                    warnings.append(
                        f"Module '{module.name}' missing description"
                    )

        # Check for circular references in relations
        circular = self._check_circular_relations(blueprint)
        if circular:
            errors.append(f"Circular entity references detected: {circular}")

        # Validate relation targets exist
        all_entity_names = {
            entity.name
            for module in blueprint.modules
            for entity in module.entities
        }
        for module in blueprint.modules:
            for entity in module.entities:
                for relation in entity.relations:
                    if relation.target_entity not in all_entity_names:
                        errors.append(
                            f"Entity '{entity.name}' references non-existent "
                            f"entity '{relation.target_entity}'"
                        )

        spec_complete = len(errors) == 0
        gate_g1_ready = spec_complete  # Gate G1 passes if no blocking errors

        return SpecValidationResult(
            spec_complete=spec_complete,
            errors=errors,
            warnings=warnings,
            gate_g1_ready=gate_g1_ready,
        )

    def _extract_features(self, blueprint: AppBlueprint) -> list[ExtractedFeature]:
        """
        Extract features from blueprint modules.

        Each module becomes a feature. Complexity is estimated based on
        entity count, field count, and relation complexity.
        """
        features: list[ExtractedFeature] = []
        feature_counter = 0

        for module in blueprint.modules:
            feature_counter += 1
            feature_id = f"feat-{feature_counter:03d}"

            # Estimate complexity
            complexity = self._estimate_complexity(module)
            estimated_files = self._estimate_file_count(module)
            entity_names = [e.name for e in module.entities]

            description = module.description or f"Module: {module.name}"
            if module.entities:
                entity_summary = ", ".join(entity_names[:3])
                if len(entity_names) > 3:
                    entity_summary += f" (+{len(entity_names) - 3} more)"
                description += f" — entities: {entity_summary}"

            features.append(
                ExtractedFeature(
                    id=feature_id,
                    name=self._humanize_name(module.name),
                    module=module.name,
                    description=description,
                    complexity=complexity,
                    dependencies=[],  # Resolved in _resolve_dependencies
                    priority=feature_counter,  # Re-sorted in _apply_priority_ordering
                    estimated_files=estimated_files,
                    entities=entity_names,
                )
            )

        # Add cross-cutting features from blueprint.features flags
        if blueprint.features.get("authentication"):
            feature_counter += 1
            features.append(
                ExtractedFeature(
                    id=f"feat-{feature_counter:03d}",
                    name="Authentication",
                    module="_auth",
                    description="JWT + OAuth authentication flow",
                    complexity=FeatureComplexity.MEDIUM,
                    dependencies=[],
                    priority=0,  # Auth is always first
                    estimated_files=5,
                    entities=["User", "Session"],
                )
            )

        if blueprint.features.get("authorization"):
            feature_counter += 1
            auth_dep = next(
                (f.id for f in features if f.module == "_auth"), None
            )
            features.append(
                ExtractedFeature(
                    id=f"feat-{feature_counter:03d}",
                    name="Authorization (RBAC)",
                    module="_authz",
                    description="Role-based access control",
                    complexity=FeatureComplexity.MEDIUM,
                    dependencies=[auth_dep] if auth_dep else [],
                    priority=1,
                    estimated_files=4,
                    entities=["Role", "Permission"],
                )
            )

        return features

    def _estimate_complexity(self, module: ModuleSpec) -> FeatureComplexity:
        """
        Estimate module complexity based on structural analysis.

        Rules:
        - SIMPLE: ≤2 entities, ≤10 fields total, no relations
        - MEDIUM: 3-5 entities OR has relations OR >10 fields
        - COMPLEX: >5 entities OR many-to-many relations OR >30 fields
        """
        entity_count = len(module.entities)
        total_fields = sum(len(e.fields) for e in module.entities)
        total_relations = sum(len(e.relations) for e in module.entities)
        has_m2m = any(
            r.type.value == "many_to_many"
            for e in module.entities
            for r in e.relations
        )

        if entity_count > 5 or total_fields > 30 or has_m2m:
            return FeatureComplexity.COMPLEX
        elif entity_count > 2 or total_relations > 0 or total_fields > 10:
            return FeatureComplexity.MEDIUM
        else:
            return FeatureComplexity.SIMPLE

    def _estimate_file_count(self, module: ModuleSpec) -> int:
        """
        Estimate the number of files that will be generated for a module.

        Per entity: model.py + schema.py + route.py + service.py + test.py = 5
        Per module: __init__.py = 1
        """
        entity_count = max(len(module.entities), 1)
        files_per_entity = 5  # model, schema, route, service, test
        module_overhead = 1   # __init__.py
        return entity_count * files_per_entity + module_overhead

    def _resolve_dependencies(
        self,
        features: list[ExtractedFeature],
        blueprint: AppBlueprint,
    ) -> list[DependencyEdge]:
        """
        Resolve inter-feature dependencies based on entity relations.

        If Entity A in Module X has a relation to Entity B in Module Y,
        then Feature X depends on Feature Y (Feature Y must be generated first).
        """
        edges: list[DependencyEdge] = []

        # Build entity → feature mapping
        entity_to_feature: dict[str, str] = {}
        for feature in features:
            for entity_name in feature.entities:
                entity_to_feature[entity_name] = feature.id

        # Scan relations to find cross-module dependencies
        for module in blueprint.modules:
            source_feature_id = next(
                (f.id for f in features if f.module == module.name), None
            )
            if not source_feature_id:
                continue

            for entity in module.entities:
                for relation in entity.relations:
                    target_feature_id = entity_to_feature.get(relation.target_entity)
                    if (
                        target_feature_id
                        and target_feature_id != source_feature_id
                    ):
                        edge = DependencyEdge(
                            source=source_feature_id,
                            target=target_feature_id,
                            reason=(
                                f"{entity.name}.{relation.name} → "
                                f"{relation.target_entity} ({relation.type.value})"
                            ),
                        )
                        # Avoid duplicate edges
                        if not any(
                            e.source == edge.source and e.target == edge.target
                            for e in edges
                        ):
                            edges.append(edge)

        # Update feature dependency lists
        for edge in edges:
            source_feat = next(
                (f for f in features if f.id == edge.source), None
            )
            if source_feat and edge.target not in source_feat.dependencies:
                source_feat.dependencies.append(edge.target)

        return edges

    def _apply_priority_ordering(
        self,
        features: list[ExtractedFeature],
        dependency_graph: list[DependencyEdge],
    ) -> list[ExtractedFeature]:
        """
        Topological sort: features with no dependencies come first.
        Within the same level, simpler features come first.
        """
        # Build adjacency for topological sort
        in_degree: dict[str, int] = {f.id: 0 for f in features}
        for edge in dependency_graph:
            if edge.source in in_degree:
                in_degree[edge.source] += 1

        # Kahn's algorithm for topological ordering
        queue = [fid for fid, deg in in_degree.items() if deg == 0]
        sorted_ids: list[str] = []
        adjacency: dict[str, list[str]] = {f.id: [] for f in features}
        for edge in dependency_graph:
            if edge.target in adjacency:
                adjacency[edge.target].append(edge.source)

        while queue:
            # Sort by complexity within the same level (simple first)
            complexity_order = {
                FeatureComplexity.SIMPLE: 0,
                FeatureComplexity.MEDIUM: 1,
                FeatureComplexity.COMPLEX: 2,
            }
            queue.sort(
                key=lambda fid: complexity_order.get(
                    next((f.complexity for f in features if f.id == fid), FeatureComplexity.MEDIUM),
                    1,
                )
            )
            current = queue.pop(0)
            sorted_ids.append(current)

            for neighbor in adjacency.get(current, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Add any remaining (circular dependency fallback)
        for f in features:
            if f.id not in sorted_ids:
                sorted_ids.append(f.id)

        # Re-assign priorities
        feature_map = {f.id: f for f in features}
        ordered_features = []
        for priority, fid in enumerate(sorted_ids, start=1):
            feat = feature_map[fid]
            feat.priority = priority
            ordered_features.append(feat)

        return ordered_features

    def _check_circular_relations(self, blueprint: AppBlueprint) -> str | None:
        """Detect circular entity references. Returns description or None."""
        # Build entity relation graph
        graph: dict[str, set[str]] = {}
        for module in blueprint.modules:
            for entity in module.entities:
                graph.setdefault(entity.name, set())
                for relation in entity.relations:
                    graph[entity.name].add(relation.target_entity)

        # DFS cycle detection
        visited: set[str] = set()
        rec_stack: set[str] = set()

        def _has_cycle(node: str) -> str | None:
            visited.add(node)
            rec_stack.add(node)
            for neighbor in graph.get(node, set()):
                if neighbor not in visited:
                    cycle = _has_cycle(neighbor)
                    if cycle:
                        return cycle
                elif neighbor in rec_stack:
                    return f"{node} → {neighbor}"
            rec_stack.discard(node)
            return None

        for entity_name in graph:
            if entity_name not in visited:
                cycle = _has_cycle(entity_name)
                if cycle:
                    return cycle

        return None

    @staticmethod
    def _humanize_name(snake_name: str) -> str:
        """Convert snake_case to Title Case for display."""
        return snake_name.replace("_", " ").title()
