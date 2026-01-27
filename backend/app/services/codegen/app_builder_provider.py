"""
App Builder Provider - Deterministic app scaffolding provider

SDLC Framework Compliance:
- Framework: SDLC 5.2.0 (7-Pillar + AI Governance Principles)
- Pillar 3: Build Phase - Multi-Provider Orchestration
- AI Governance Principle 4: Deterministic Intermediate Representations
- Methodology: Template-based scaffolding with zero LLM cost

Purpose:
4th provider in multi-provider fallback chain:
- app-builder (NEW_SCAFFOLD, confidence ≥ 0.75) → THIS PROVIDER
- ollama (fallback for low confidence)
- claude (fallback for quota/timeout)
- deepcode (future Vietnamese-optimized)

Provides deterministic scaffolding for 4 template types:
1. Next.js Fullstack (Next.js 14 + Prisma + NextAuth)
2. Next.js SaaS (Next.js + Stripe + subscriptions)
3. FastAPI (FastAPI + SQLAlchemy + JWT)
4. React Native (Expo + Zustand + Navigation)

Cost: $0 execution (deterministic templates), minimal planning cost (LLM risk analysis)

Related ADRs:
- ADR-022: IR-Based Codegen with 4-Gate Quality Pipeline
- ADR-040: App Builder Integration - Competitive Necessity

Sprint: 106 - App Builder Integration (MVP)
Date: January 28, 2026
Owner: Backend Team
Status: ACTIVE
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
import re

from backend.app.schemas.codegen.codegen_spec import CodegenSpec
from backend.app.schemas.codegen.codegen_result import CodegenResult, GeneratedFile, CostBreakdown
from backend.app.schemas.codegen.template_blueprint import (
    TemplateBlueprint,
    TemplateType,
    Entity,
    EntityField,
    APIRoute,
    Page
)
from backend.app.services.codegen.base_provider import CodegenProvider
from backend.app.services.codegen.templates.base_template import BaseTemplate
from backend.app.services.codegen.templates.nextjs_fullstack_template import NextJSFullstackTemplate
from backend.app.services.codegen.templates.nextjs_saas_template import NextJSSaaSTemplate
from backend.app.services.codegen.templates.fastapi_template import FastAPITemplate
from backend.app.services.codegen.templates.react_native_template import ReactNativeTemplate

logger = logging.getLogger(__name__)


class AppBuilderProvider(CodegenProvider):
    """
    App Builder Provider - Deterministic app scaffolding.

    Routing Decision (Intent Router):
    - Intent: NEW_SCAFFOLD
    - Confidence: ≥ 0.75
    - Keywords: "create", "new", "scaffold", "bootstrap", "init", "start"
    - Anti-pattern: "modify", "change", "update", "fix" (routes to Ollama)

    Template Selection Logic:
    1. Keyword matching in description
    2. Tech stack detection (if provided)
    3. Domain-specific patterns (SaaS, mobile, API)
    4. Fallback: Next.js Fullstack (most versatile)

    Quality Gates:
    - Scaffold Mode: Gates 1-2 mandatory, 3-4 optional
    - Smoke test only (no full test suite)
    - Fast validation (<30s total)

    Cost Breakdown:
    - Planning: $0.01-0.05 (LLM risk analysis)
    - Execution: $0.00 (deterministic templates)
    - Total: $0.01-0.05 (95% cheaper than Ollama/Claude)

    Example:
        provider = AppBuilderProvider()

        spec = CodegenSpec(
            description="Create Instagram clone with Next.js",
            project_name="instapic",
            language="typescript",
            framework="nextjs"
        )

        result = await provider.generate(spec)
        # → 15+ files generated (pages, API routes, Prisma schema, etc.)
        # → Cost: $0.02 (planning only, execution free)
    """

    name = "app-builder"
    display_name = "App Builder (Deterministic Scaffolding)"
    version = "1.0.0"

    # Template instances (lazy-loaded)
    _templates: Dict[TemplateType, BaseTemplate] = {}

    def __init__(self):
        """Initialize App Builder Provider with template registry"""
        super().__init__()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Register templates
        self._templates = {
            TemplateType.NEXTJS_FULLSTACK: NextJSFullstackTemplate(),
            TemplateType.NEXTJS_SAAS: NextJSSaaSTemplate(),
            TemplateType.FASTAPI: FastAPITemplate(),
            TemplateType.REACT_NATIVE: ReactNativeTemplate(),
        }

        self.logger.info(f"Initialized {self.name} provider with {len(self._templates)} templates")

    async def generate(self, spec: CodegenSpec) -> CodegenResult:
        """
        Generate app scaffolding from spec.

        Workflow:
        1. Detect template type from spec description
        2. Create blueprint from spec (entities, routes, pages)
        3. Select template instance
        4. Generate files via template.scaffold(blueprint)
        5. Return CodegenResult with files + metadata

        Args:
            spec: Code generation specification

        Returns:
            CodegenResult with generated files and metadata

        Raises:
            ValueError: If template type cannot be detected
            RuntimeError: If scaffolding fails
        """
        start_time = datetime.utcnow()
        self.logger.info(f"Generating app scaffold for: {spec.project_name}")

        try:
            # Step 1: Detect template type
            template_type = self._detect_template_type(spec)
            self.logger.info(f"Detected template type: {template_type.value}")

            # Step 2: Create blueprint from spec
            blueprint = await self._create_blueprint(spec, template_type)
            self.logger.info(f"Created blueprint: {blueprint.blueprint_id}")

            # Step 3: Select template
            template = self._templates.get(template_type)
            if not template:
                raise ValueError(f"Template not found: {template_type}")

            # Step 4: Generate files
            self.logger.info(f"Scaffolding with {template.template_name}...")
            files = template.scaffold(blueprint)

            # Step 5: Compute metadata
            elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

            # Cost breakdown (planning estimated, execution always $0)
            planning_cost = 0.02  # Estimated LLM cost for risk analysis
            cost_breakdown = CostBreakdown(
                planning_provider="ollama",  # or claude, depends on planning phase
                planning_tokens=1500,  # estimated
                planning_cost_usd=planning_cost,
                execution_provider="app-builder",
                execution_cost_usd=0.00,  # deterministic = free
            )

            # Build result
            result = CodegenResult(
                files=files,
                provider=self.name,
                generation_time_ms=int(elapsed_ms),
                metadata={
                    "template": template_type.value,
                    "template_name": template.template_name,
                    "template_version": template.template_version,
                    "blueprint_id": blueprint.blueprint_id,
                    "integrity_hash": blueprint.integrity_hash,
                    "entities_count": len(blueprint.entities),
                    "routes_count": len(blueprint.api_routes),
                    "pages_count": len(blueprint.pages),
                },
                cost_breakdown=cost_breakdown,
            )

            self.logger.info(
                f"Scaffold complete: {len(files)} files, {elapsed_ms:.0f}ms, "
                f"cost=${cost_breakdown.total_cost_usd:.4f}"
            )

            return result

        except Exception as e:
            self.logger.error(f"Scaffold failed: {str(e)}", exc_info=True)
            raise RuntimeError(f"App Builder scaffolding failed: {str(e)}") from e

    async def estimate_cost(self, spec: CodegenSpec) -> Dict[str, Any]:
        """
        Estimate cost for app scaffolding.

        Planning Phase (LLM):
        - Risk analysis: 1000-2000 tokens
        - Blueprint generation: 500-1000 tokens
        - Cost: $0.01-0.05 (Ollama/Claude)

        Execution Phase (Deterministic):
        - Template scaffolding: deterministic
        - Cost: $0.00 (no LLM calls)

        Total: $0.01-0.05 (95% cheaper than full LLM generation)

        Args:
            spec: Code generation specification

        Returns:
            Cost estimate with breakdown
        """
        # Estimate planning tokens based on spec complexity
        base_tokens = 1000
        entity_tokens = len(spec.entities or []) * 200
        route_tokens = len(spec.api_routes or []) * 100
        page_tokens = len(spec.pages or []) * 150

        planning_tokens = base_tokens + entity_tokens + route_tokens + page_tokens
        planning_cost = planning_tokens * 0.00002  # $0.02 per 1K tokens (Ollama pricing)

        return {
            "provider": self.name,
            "planning_cost_usd": round(planning_cost, 4),
            "execution_cost_usd": 0.00,
            "total_cost_usd": round(planning_cost, 4),
            "estimated_time_ms": 5000,  # ~5s for scaffolding
            "breakdown": {
                "planning_tokens": planning_tokens,
                "execution_tokens": 0,
                "is_deterministic": True,
                "note": "Planning phase uses LLM for risk analysis, execution is deterministic",
            },
        }

    def _detect_template_type(self, spec: CodegenSpec) -> TemplateType:
        """
        Detect template type from spec description and tech stack.

        Priority Order:
        1. Explicit framework in spec.framework
        2. Tech stack keywords (spec.tech_stack)
        3. Description keyword matching
        4. Domain-specific patterns (SaaS, mobile, API)
        5. Fallback: NEXTJS_FULLSTACK (most versatile)

        Detection Rules:
        - Next.js SaaS: "saas", "subscription", "payment", "stripe", "billing"
        - Next.js Fullstack: "nextjs", "next.js", "full stack", "web app"
        - FastAPI: "fastapi", "python api", "rest api", "backend"
        - React Native: "react native", "mobile", "expo", "ios", "android"

        Args:
            spec: Code generation specification

        Returns:
            Detected template type

        Example:
            spec = CodegenSpec(description="Create SaaS app with Stripe")
            → TemplateType.NEXTJS_SAAS

            spec = CodegenSpec(description="Build FastAPI backend")
            → TemplateType.FASTAPI
        """
        description_lower = spec.description.lower()
        framework_lower = (spec.framework or "").lower()
        tech_stack_lower = [tech.lower() for tech in (spec.tech_stack or [])]

        # Rule 1: Explicit framework
        if "fastapi" in framework_lower or "fastapi" in tech_stack_lower:
            return TemplateType.FASTAPI

        if "react-native" in framework_lower or "expo" in tech_stack_lower:
            return TemplateType.REACT_NATIVE

        if "nextjs" in framework_lower or "next.js" in framework_lower:
            # Check if SaaS-specific keywords present
            saas_keywords = ["saas", "subscription", "payment", "stripe", "billing"]
            if any(kw in description_lower for kw in saas_keywords):
                return TemplateType.NEXTJS_SAAS
            return TemplateType.NEXTJS_FULLSTACK

        # Rule 2: Description keyword matching
        if any(kw in description_lower for kw in ["saas", "subscription", "payment", "stripe"]):
            return TemplateType.NEXTJS_SAAS

        if any(kw in description_lower for kw in ["mobile", "react native", "expo", "ios", "android"]):
            return TemplateType.REACT_NATIVE

        if any(kw in description_lower for kw in ["fastapi", "python api", "rest api", "backend only"]):
            return TemplateType.FASTAPI

        if any(kw in description_lower for kw in ["nextjs", "next.js", "full stack", "web app"]):
            return TemplateType.NEXTJS_FULLSTACK

        # Rule 3: Tech stack-based detection
        if "stripe" in tech_stack_lower or "payment" in tech_stack_lower:
            return TemplateType.NEXTJS_SAAS

        if "prisma" in tech_stack_lower or "nextauth" in tech_stack_lower:
            return TemplateType.NEXTJS_FULLSTACK

        if "sqlalchemy" in tech_stack_lower or "alembic" in tech_stack_lower:
            return TemplateType.FASTAPI

        if "zustand" in tech_stack_lower or "react-navigation" in tech_stack_lower:
            return TemplateType.REACT_NATIVE

        # Rule 4: Fallback to most versatile template
        self.logger.warning(
            f"Could not detect template type from spec, defaulting to NEXTJS_FULLSTACK. "
            f"Description: {spec.description[:100]}..."
        )
        return TemplateType.NEXTJS_FULLSTACK

    async def _create_blueprint(
        self,
        spec: CodegenSpec,
        template_type: TemplateType
    ) -> TemplateBlueprint:
        """
        Create TemplateBlueprint from CodegenSpec.

        Blueprint Creation Logic:
        1. Extract project metadata (name, tech stack)
        2. Parse entities from spec (if provided)
        3. Infer API routes from entities
        4. Infer pages from entities
        5. Detect features from description
        6. Set environment variables
        7. Compute integrity hash

        Args:
            spec: Code generation specification
            template_type: Detected template type

        Returns:
            Finalized TemplateBlueprint with integrity hash
        """
        # Parse entities from spec
        entities = []
        if spec.entities:
            for entity_spec in spec.entities:
                fields = [
                    EntityField(
                        name=field.get("name"),
                        type=field.get("type", "string"),
                        required=field.get("required", True),
                        unique=field.get("unique", False),
                        relation_to=field.get("relation_to"),
                    )
                    for field in entity_spec.get("fields", [])
                ]

                entity = Entity(
                    name=entity_spec.get("name"),
                    fields=fields,
                    auth_required=entity_spec.get("auth_required", True),
                )
                entities.append(entity)

        # Infer API routes from entities
        api_routes = []
        if spec.api_routes:
            for route_spec in spec.api_routes:
                route = APIRoute(
                    path=route_spec.get("path"),
                    methods=route_spec.get("methods", ["GET", "POST"]),
                    auth_required=route_spec.get("auth_required", True),
                    entity=route_spec.get("entity"),
                )
                api_routes.append(route)
        else:
            # Auto-generate CRUD routes for entities
            for entity in entities:
                api_routes.extend([
                    APIRoute(
                        path=f"/api/{entity.name.lower()}",
                        methods=["GET", "POST"],
                        auth_required=entity.auth_required,
                        entity=entity.name,
                    ),
                    APIRoute(
                        path=f"/api/{entity.name.lower()}/[id]",
                        methods=["GET", "PUT", "DELETE"],
                        auth_required=entity.auth_required,
                        entity=entity.name,
                    ),
                ])

        # Infer pages from entities
        pages = []
        if spec.pages:
            for page_spec in spec.pages:
                page = Page(
                    path=page_spec.get("path"),
                    name=page_spec.get("name"),
                    auth_required=page_spec.get("auth_required", True),
                    entities_used=page_spec.get("entities_used", []),
                )
                pages.append(page)
        else:
            # Auto-generate pages for entities
            for entity in entities:
                pages.append(Page(
                    path=f"/{entity.name.lower()}",
                    name=entity.name,
                    auth_required=entity.auth_required,
                    entities_used=[entity.name],
                ))

        # Detect features from description
        features = []
        description_lower = spec.description.lower()
        feature_keywords = {
            "auth": ["authentication", "login", "signin", "signup", "oauth"],
            "crud": ["create", "read", "update", "delete", "manage"],
            "upload": ["upload", "file", "image", "photo", "attachment"],
            "payments": ["payment", "stripe", "subscription", "billing"],
            "search": ["search", "filter", "query"],
            "notifications": ["notification", "email", "alert"],
        }

        for feature, keywords in feature_keywords.items():
            if any(kw in description_lower for kw in keywords):
                features.append(feature)

        # Set environment variables based on template
        env_vars = self._get_template_env_vars(template_type)

        # Get tech stack from template defaults + spec overrides
        template = self._templates[template_type]
        tech_stack = list(template.default_tech_stack)
        if spec.tech_stack:
            tech_stack.extend([tech for tech in spec.tech_stack if tech not in tech_stack])

        # Create and finalize blueprint
        blueprint = TemplateBlueprint(
            template_type=template_type,
            project_name=spec.project_name,
            tech_stack=tech_stack,
            entities=entities,
            api_routes=api_routes,
            pages=pages,
            features=features,
            env_vars=env_vars,
            quality_mode="scaffold",  # Always use scaffold mode for app-builder
        )

        return blueprint.finalize()

    def _get_template_env_vars(self, template_type: TemplateType) -> List[str]:
        """Get required environment variables for template type"""
        template = self._templates.get(template_type)
        return template.required_env_vars if template else []

    def supports_streaming(self) -> bool:
        """App Builder supports streaming (file-by-file generation)"""
        return True

    def get_capabilities(self) -> Dict[str, Any]:
        """Get provider capabilities"""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "version": self.version,
            "templates": [t.value for t in self._templates.keys()],
            "supports_streaming": True,
            "deterministic": True,
            "cost_per_generation": 0.00,  # Execution is free
            "features": [
                "Full app scaffolding",
                "Authentication setup",
                "Database schema generation",
                "API routes generation",
                "UI components generation",
                "Zero LLM cost execution",
            ],
        }
