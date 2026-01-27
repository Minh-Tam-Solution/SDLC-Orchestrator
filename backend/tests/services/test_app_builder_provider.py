"""
Unit Tests for App Builder Provider

SDLC Framework Compliance:
- Framework: SDLC 5.2.0 (7-Pillar + AI Governance Principles)
- Pillar 5: Test & Quality Assurance
- AI Governance Principle 6: Multi-Tier Quality Enforcement
- Methodology: Test-driven validation with 95%+ coverage target

Sprint: 106 - App Builder Integration (MVP)
Date: January 28, 2026
Owner: Backend Team
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from backend.app.services.codegen.app_builder_provider import AppBuilderProvider
from backend.app.schemas.codegen.codegen_spec import CodegenSpec
from backend.app.schemas.codegen.template_blueprint import (
    TemplateType,
    TemplateBlueprint,
    Entity,
    EntityField,
    APIRoute,
    Page
)


class TestAppBuilderProvider:
    """Test suite for AppBuilderProvider"""

    @pytest.fixture
    def provider(self):
        """Create AppBuilderProvider instance"""
        return AppBuilderProvider()

    @pytest.fixture
    def basic_spec(self):
        """Create basic CodegenSpec for testing"""
        return CodegenSpec(
            description="Create a blog app with Next.js",
            project_name="my-blog",
            language="typescript",
            framework="nextjs",
        )

    @pytest.fixture
    def saas_spec(self):
        """Create SaaS-specific CodegenSpec"""
        return CodegenSpec(
            description="Create SaaS app with Stripe subscriptions",
            project_name="my-saas",
            language="typescript",
            framework="nextjs",
            features=["auth", "payments", "subscriptions"],
        )

    @pytest.fixture
    def fastapi_spec(self):
        """Create FastAPI CodegenSpec"""
        return CodegenSpec(
            description="Build REST API with FastAPI",
            project_name="my-api",
            language="python",
            framework="fastapi",
        )

    @pytest.fixture
    def react_native_spec(self):
        """Create React Native CodegenSpec"""
        return CodegenSpec(
            description="Build mobile app with React Native",
            project_name="my-mobile-app",
            language="typescript",
            framework="react-native",
        )

    def test_provider_initialization(self, provider):
        """Test provider initializes with all templates"""
        assert provider.name == "app-builder"
        assert provider.display_name == "App Builder (Deterministic Scaffolding)"
        assert len(provider._templates) == 4

        # Verify all template types registered
        assert TemplateType.NEXTJS_FULLSTACK in provider._templates
        assert TemplateType.NEXTJS_SAAS in provider._templates
        assert TemplateType.FASTAPI in provider._templates
        assert TemplateType.REACT_NATIVE in provider._templates

    def test_detect_template_type_nextjs_fullstack(self, provider):
        """Test template detection for Next.js Fullstack"""
        spec = CodegenSpec(
            description="Create web app with Next.js",
            project_name="test-app",
            framework="nextjs",
        )

        template_type = provider._detect_template_type(spec)
        assert template_type == TemplateType.NEXTJS_FULLSTACK

    def test_detect_template_type_nextjs_saas(self, provider):
        """Test template detection for Next.js SaaS"""
        # Test with "saas" keyword
        spec1 = CodegenSpec(
            description="Create SaaS app with subscriptions",
            project_name="test-saas",
        )
        assert provider._detect_template_type(spec1) == TemplateType.NEXTJS_SAAS

        # Test with "stripe" keyword
        spec2 = CodegenSpec(
            description="Build app with Stripe payments",
            project_name="test-payments",
        )
        assert provider._detect_template_type(spec2) == TemplateType.NEXTJS_SAAS

        # Test with tech stack
        spec3 = CodegenSpec(
            description="Create web app",
            project_name="test-app",
            tech_stack=["nextjs", "stripe"],
        )
        assert provider._detect_template_type(spec3) == TemplateType.NEXTJS_SAAS

    def test_detect_template_type_fastapi(self, provider):
        """Test template detection for FastAPI"""
        # Test with framework
        spec1 = CodegenSpec(
            description="Build API",
            project_name="test-api",
            framework="fastapi",
        )
        assert provider._detect_template_type(spec1) == TemplateType.FASTAPI

        # Test with description keyword
        spec2 = CodegenSpec(
            description="Create REST API with FastAPI and PostgreSQL",
            project_name="test-api",
        )
        assert provider._detect_template_type(spec2) == TemplateType.FASTAPI

        # Test with tech stack
        spec3 = CodegenSpec(
            description="Build backend",
            project_name="test-backend",
            tech_stack=["sqlalchemy", "alembic"],
        )
        assert provider._detect_template_type(spec3) == TemplateType.FASTAPI

    def test_detect_template_type_react_native(self, provider):
        """Test template detection for React Native"""
        # Test with framework
        spec1 = CodegenSpec(
            description="Build app",
            project_name="test-app",
            framework="react-native",
        )
        assert provider._detect_template_type(spec1) == TemplateType.REACT_NATIVE

        # Test with "mobile" keyword
        spec2 = CodegenSpec(
            description="Create mobile app for iOS and Android",
            project_name="test-mobile",
        )
        assert provider._detect_template_type(spec2) == TemplateType.REACT_NATIVE

        # Test with tech stack
        spec3 = CodegenSpec(
            description="Build app",
            project_name="test-app",
            tech_stack=["expo", "zustand"],
        )
        assert provider._detect_template_type(spec3) == TemplateType.REACT_NATIVE

    def test_detect_template_type_fallback(self, provider):
        """Test template detection fallback to Next.js Fullstack"""
        spec = CodegenSpec(
            description="Create an app",  # Ambiguous
            project_name="test-app",
        )

        template_type = provider._detect_template_type(spec)
        assert template_type == TemplateType.NEXTJS_FULLSTACK

    @pytest.mark.asyncio
    async def test_create_blueprint_basic(self, provider, basic_spec):
        """Test blueprint creation from basic spec"""
        template_type = TemplateType.NEXTJS_FULLSTACK
        blueprint = await provider._create_blueprint(basic_spec, template_type)

        assert isinstance(blueprint, TemplateBlueprint)
        assert blueprint.project_name == "my-blog"
        assert blueprint.template_type == TemplateType.NEXTJS_FULLSTACK
        assert blueprint.quality_mode == "scaffold"
        assert blueprint.integrity_hash != ""

        # Verify default tech stack
        assert "nextjs" in blueprint.tech_stack
        assert "react" in blueprint.tech_stack
        assert "typescript" in blueprint.tech_stack

    @pytest.mark.asyncio
    async def test_create_blueprint_with_entities(self, provider):
        """Test blueprint creation with entities"""
        spec = CodegenSpec(
            description="Create blog with posts",
            project_name="blog",
            framework="nextjs",
            entities=[
                {
                    "name": "Post",
                    "fields": [
                        {"name": "title", "type": "string", "required": True},
                        {"name": "content", "type": "string", "required": True},
                        {"name": "published", "type": "boolean", "required": False},
                    ],
                    "auth_required": True,
                }
            ],
        )

        blueprint = await provider._create_blueprint(spec, TemplateType.NEXTJS_FULLSTACK)

        # Verify entities
        assert len(blueprint.entities) == 1
        assert blueprint.entities[0].name == "Post"
        assert len(blueprint.entities[0].fields) == 3

        # Verify auto-generated API routes
        assert len(blueprint.api_routes) == 2
        assert any(route.path == "/api/post" for route in blueprint.api_routes)
        assert any(route.path == "/api/post/[id]" for route in blueprint.api_routes)

        # Verify auto-generated pages
        assert len(blueprint.pages) == 1
        assert blueprint.pages[0].path == "/post"

    @pytest.mark.asyncio
    async def test_create_blueprint_with_custom_routes(self, provider):
        """Test blueprint creation with custom API routes"""
        spec = CodegenSpec(
            description="Create app",
            project_name="test-app",
            framework="nextjs",
            api_routes=[
                {
                    "path": "/api/custom",
                    "methods": ["GET", "POST"],
                    "auth_required": True,
                }
            ],
        )

        blueprint = await provider._create_blueprint(spec, TemplateType.NEXTJS_FULLSTACK)

        assert len(blueprint.api_routes) == 1
        assert blueprint.api_routes[0].path == "/api/custom"
        assert "GET" in blueprint.api_routes[0].methods

    @pytest.mark.asyncio
    async def test_create_blueprint_feature_detection(self, provider):
        """Test automatic feature detection from description"""
        spec = CodegenSpec(
            description="Create app with authentication, file upload, and search",
            project_name="test-app",
            framework="nextjs",
        )

        blueprint = await provider._create_blueprint(spec, TemplateType.NEXTJS_FULLSTACK)

        # Verify detected features
        assert "auth" in blueprint.features
        assert "upload" in blueprint.features
        assert "search" in blueprint.features

    @pytest.mark.asyncio
    async def test_create_blueprint_env_vars(self, provider):
        """Test blueprint includes template-specific env vars"""
        spec = CodegenSpec(
            description="Create SaaS app",
            project_name="test-saas",
            framework="nextjs",
        )

        blueprint = await provider._create_blueprint(spec, TemplateType.NEXTJS_SAAS)

        # Verify SaaS-specific env vars
        assert "STRIPE_SECRET_KEY" in blueprint.env_vars
        assert "STRIPE_PUBLISHABLE_KEY" in blueprint.env_vars
        assert "DATABASE_URL" in blueprint.env_vars

    @pytest.mark.asyncio
    async def test_generate_success_nextjs(self, provider, basic_spec):
        """Test successful code generation for Next.js"""
        result = await provider.generate(basic_spec)

        # Verify result structure
        assert result.provider == "app-builder"
        assert len(result.files) > 0
        assert result.generation_time_ms > 0

        # Verify metadata
        assert result.metadata["template"] == "nextjs-fullstack"
        assert result.metadata["blueprint_id"]
        assert result.metadata["integrity_hash"]

        # Verify cost breakdown
        assert result.cost_breakdown.execution_cost_usd == 0.00
        assert result.cost_breakdown.total_cost_usd < 0.10

        # Verify key files generated
        file_paths = [f.path for f in result.files]
        assert "package.json" in file_paths
        assert "tsconfig.json" in file_paths
        assert "README.md" in file_paths
        assert any("prisma" in path for path in file_paths)

    @pytest.mark.asyncio
    async def test_generate_success_fastapi(self, provider, fastapi_spec):
        """Test successful code generation for FastAPI"""
        result = await provider.generate(fastapi_spec)

        assert result.provider == "app-builder"
        assert result.metadata["template"] == "fastapi"

        # Verify FastAPI-specific files
        file_paths = [f.path for f in result.files]
        assert "requirements.txt" in file_paths
        assert "pyproject.toml" in file_paths
        assert any("main.py" in path for path in file_paths)
        assert any("alembic" in path for path in file_paths)

    @pytest.mark.asyncio
    async def test_generate_success_react_native(self, provider, react_native_spec):
        """Test successful code generation for React Native"""
        result = await provider.generate(react_native_spec)

        assert result.provider == "app-builder"
        assert result.metadata["template"] == "react-native"

        # Verify React Native-specific files
        file_paths = [f.path for f in result.files]
        assert "package.json" in file_paths
        assert "app.json" in file_paths
        assert "App.tsx" in file_paths

    @pytest.mark.asyncio
    async def test_generate_with_entities(self, provider):
        """Test code generation with entities"""
        spec = CodegenSpec(
            description="Create blog",
            project_name="blog",
            framework="nextjs",
            entities=[
                {
                    "name": "Post",
                    "fields": [
                        {"name": "title", "type": "string", "required": True},
                        {"name": "content", "type": "string", "required": True},
                    ],
                }
            ],
        )

        result = await provider.generate(spec)

        # Verify entity-related files generated
        file_paths = [f.path for f in result.files]

        # Should have Prisma schema with Post model
        prisma_files = [f for f in result.files if "prisma/schema.prisma" in f.path]
        assert len(prisma_files) > 0
        assert "Post" in prisma_files[0].content

        # Should have API routes for Post
        assert any("/api/post" in path for path in file_paths)

        # Verify metadata
        assert result.metadata["entities_count"] == 1
        assert result.metadata["routes_count"] == 2  # List + Detail routes

    @pytest.mark.asyncio
    async def test_estimate_cost(self, provider, basic_spec):
        """Test cost estimation"""
        cost = await provider.estimate_cost(basic_spec)

        # Verify cost structure
        assert cost["provider"] == "app-builder"
        assert cost["execution_cost_usd"] == 0.00  # Deterministic
        assert cost["total_cost_usd"] < 0.10  # Only planning cost
        assert cost["estimated_time_ms"] < 10000  # <10s

        # Verify breakdown
        assert cost["breakdown"]["is_deterministic"] is True
        assert cost["breakdown"]["execution_tokens"] == 0

    @pytest.mark.asyncio
    async def test_estimate_cost_with_entities(self, provider):
        """Test cost estimation scales with entities"""
        spec_simple = CodegenSpec(
            description="Create app",
            project_name="simple",
            framework="nextjs",
        )

        spec_complex = CodegenSpec(
            description="Create app",
            project_name="complex",
            framework="nextjs",
            entities=[
                {"name": f"Entity{i}", "fields": []} for i in range(5)
            ],
            api_routes=[
                {"path": f"/api/route{i}", "methods": ["GET"]} for i in range(10)
            ],
        )

        cost_simple = await provider.estimate_cost(spec_simple)
        cost_complex = await provider.estimate_cost(spec_complex)

        # Complex spec should cost more (more planning tokens)
        assert cost_complex["planning_cost_usd"] > cost_simple["planning_cost_usd"]
        assert cost_complex["breakdown"]["planning_tokens"] > cost_simple["breakdown"]["planning_tokens"]

    def test_supports_streaming(self, provider):
        """Test streaming support flag"""
        assert provider.supports_streaming() is True

    def test_get_capabilities(self, provider):
        """Test capabilities reporting"""
        caps = provider.get_capabilities()

        assert caps["name"] == "app-builder"
        assert caps["deterministic"] is True
        assert caps["cost_per_generation"] == 0.00
        assert len(caps["templates"]) == 4
        assert caps["supports_streaming"] is True

        # Verify template list
        assert "nextjs-fullstack" in caps["templates"]
        assert "nextjs-saas" in caps["templates"]
        assert "fastapi" in caps["templates"]
        assert "react-native" in caps["templates"]

    @pytest.mark.asyncio
    async def test_generate_error_handling(self, provider):
        """Test error handling during generation"""
        # Create spec that will cause template error
        spec = CodegenSpec(
            description="Create app",
            project_name="",  # Invalid: empty project name
            framework="nextjs",
        )

        with pytest.raises(RuntimeError) as exc_info:
            await provider.generate(spec)

        assert "App Builder scaffolding failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_blueprint_integrity_hash(self, provider, basic_spec):
        """Test blueprint integrity hash is computed"""
        template_type = TemplateType.NEXTJS_FULLSTACK
        blueprint = await provider._create_blueprint(basic_spec, template_type)

        # Verify hash exists and is valid
        assert blueprint.integrity_hash != ""
        assert len(blueprint.integrity_hash) == 64  # SHA256 hex digest

        # Verify hash is deterministic
        blueprint2 = await provider._create_blueprint(basic_spec, template_type)
        # Note: Hashes will differ due to blueprint_id being unique each time
        # But the verify_integrity() method should work
        assert blueprint.verify_integrity() is True
        assert blueprint2.verify_integrity() is True


class TestAppBuilderProviderIntegration:
    """Integration tests for AppBuilderProvider with real templates"""

    @pytest.fixture
    def provider(self):
        return AppBuilderProvider()

    @pytest.mark.asyncio
    async def test_full_nextjs_generation(self, provider):
        """Integration test: Generate complete Next.js app"""
        spec = CodegenSpec(
            description="Create Instagram clone with posts and likes",
            project_name="instapic",
            framework="nextjs",
            entities=[
                {
                    "name": "Post",
                    "fields": [
                        {"name": "image_url", "type": "string"},
                        {"name": "caption", "type": "string"},
                        {"name": "likes_count", "type": "integer"},
                    ],
                }
            ],
        )

        result = await provider.generate(spec)

        # Verify comprehensive file set
        file_paths = [f.path for f in result.files]

        # Config files
        assert "package.json" in file_paths
        assert "tsconfig.json" in file_paths
        assert "next.config.js" in file_paths
        assert "tailwind.config.ts" in file_paths

        # Database
        assert any("prisma/schema.prisma" in path for path in file_paths)

        # Source files
        assert any("src/app/layout.tsx" in path for path in file_paths)
        assert any("src/lib/prisma.ts" in path for path in file_paths)

        # Entity files
        assert any("/api/post" in path for path in file_paths)

        # Documentation
        assert "README.md" in file_paths
        assert ".gitignore" in file_paths

        # Verify total file count reasonable
        assert len(result.files) >= 10

    @pytest.mark.asyncio
    async def test_full_fastapi_generation(self, provider):
        """Integration test: Generate complete FastAPI app"""
        spec = CodegenSpec(
            description="Create REST API for blog",
            project_name="blog-api",
            framework="fastapi",
            entities=[
                {
                    "name": "Article",
                    "fields": [
                        {"name": "title", "type": "string"},
                        {"name": "body", "type": "string"},
                        {"name": "published", "type": "boolean"},
                    ],
                }
            ],
        )

        result = await provider.generate(spec)

        file_paths = [f.path for f in result.files]

        # Config files
        assert "requirements.txt" in file_paths
        assert "pyproject.toml" in file_paths
        assert "Dockerfile" in file_paths

        # Source files
        assert any("app/main.py" in path for path in file_paths)
        assert any("app/core/config.py" in path for path in file_paths)

        # Database
        assert any("alembic" in path for path in file_paths)

        # Entity files
        assert any("models/article.py" in path for path in file_paths)
        assert any("schemas/article.py" in path for path in file_paths)
        assert any("api/endpoints/article.py" in path for path in file_paths)

        assert len(result.files) >= 15

    @pytest.mark.asyncio
    async def test_performance_benchmark(self, provider):
        """Test generation performance meets <5s target"""
        spec = CodegenSpec(
            description="Create simple app",
            project_name="perf-test",
            framework="nextjs",
        )

        start = datetime.utcnow()
        result = await provider.generate(spec)
        elapsed_ms = (datetime.utcnow() - start).total_seconds() * 1000

        # Should complete in <5s for simple spec
        assert elapsed_ms < 5000

        # Result should also track generation time
        assert result.generation_time_ms < 5000
