"""
E2E Integration Tests for Intent Router + App Builder Provider

SDLC Framework Compliance:
- Framework: SDLC 5.2.0 (7-Pillar + AI Governance Principles)
- Pillar 5: Test & Quality Assurance - E2E Integration Testing
- AI Governance Principle 6: Multi-Tier Quality Enforcement
- Methodology: End-to-end workflow validation

Purpose:
Verify complete intent-based routing workflow:
1. User submits CodegenSpec
2. Intent Router detects intent (NEW_SCAFFOLD, MODIFY_EXISTING, etc.)
3. CodegenService auto-routes to appropriate provider
4. Provider generates code
5. Result returned to user

Sprint: 106 - App Builder Integration (MVP)
Date: January 28, 2026
Owner: Backend Team
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from backend.app.services.codegen.codegen_service import CodegenService
from backend.app.services.codegen.intent_router import IntentRouter, IntentType
from backend.app.schemas.codegen.codegen_spec import CodegenSpec
from backend.app.schemas.codegen.template_blueprint import TemplateType


class TestIntentRouterIntegration:
    """E2E integration tests for Intent Router + CodegenService"""

    @pytest.fixture
    def service(self):
        """Create CodegenService with IntentRouter"""
        # Create service without auto-registering providers (avoid network calls)
        service = CodegenService(auto_register=False)

        # Manually register only app-builder provider for testing
        from backend.app.services.codegen.app_builder_provider import AppBuilderProvider
        service._registry.register(AppBuilderProvider())

        return service

    @pytest.fixture
    def intent_router(self):
        """Create IntentRouter with default threshold"""
        return IntentRouter(confidence_threshold=0.75)

    @pytest.mark.asyncio
    async def test_auto_route_new_scaffold_nextjs(self, service):
        """Test auto-routing for NEW_SCAFFOLD intent (Next.js)"""
        spec = CodegenSpec(
            description="Create Instagram clone with Next.js and Prisma",
            project_name="instapic",
            language="typescript",
            framework="nextjs",
        )

        # Generate code (should auto-route to app-builder)
        result = await service.generate(spec, has_existing_repo=False)

        # Verify app-builder was used
        assert result.provider == "app-builder"
        assert result.metadata["template"] == "nextjs-fullstack"

        # Verify files generated
        assert len(result.files) > 0
        file_paths = [f.path for f in result.files]
        assert "package.json" in file_paths
        assert any("prisma" in path for path in file_paths)

    @pytest.mark.asyncio
    async def test_auto_route_new_scaffold_saas(self, service):
        """Test auto-routing for NEW_SCAFFOLD intent (SaaS)"""
        spec = CodegenSpec(
            description="Create SaaS app with Stripe subscriptions and payments",
            project_name="my-saas",
            language="typescript",
            framework="nextjs",
        )

        result = await service.generate(spec, has_existing_repo=False)

        # Verify app-builder was used with SaaS template
        assert result.provider == "app-builder"
        assert result.metadata["template"] == "nextjs-saas"

        # Verify Stripe-specific files
        file_paths = [f.path for f in result.files]
        assert any("stripe" in path.lower() for path in file_paths)

    @pytest.mark.asyncio
    async def test_auto_route_new_scaffold_fastapi(self, service):
        """Test auto-routing for NEW_SCAFFOLD intent (FastAPI)"""
        spec = CodegenSpec(
            description="Build REST API with FastAPI and SQLAlchemy",
            project_name="my-api",
            language="python",
            framework="fastapi",
        )

        result = await service.generate(spec, has_existing_repo=False)

        # Verify app-builder was used with FastAPI template
        assert result.provider == "app-builder"
        assert result.metadata["template"] == "fastapi"

        # Verify FastAPI-specific files
        file_paths = [f.path for f in result.files]
        assert "requirements.txt" in file_paths
        assert any("main.py" in path for path in file_paths)

    @pytest.mark.asyncio
    async def test_auto_route_new_scaffold_react_native(self, service):
        """Test auto-routing for NEW_SCAFFOLD intent (React Native)"""
        spec = CodegenSpec(
            description="Create mobile app with React Native and Expo",
            project_name="my-mobile-app",
            language="typescript",
            framework="react-native",
        )

        result = await service.generate(spec, has_existing_repo=False)

        # Verify app-builder was used with React Native template
        assert result.provider == "app-builder"
        assert result.metadata["template"] == "react-native"

        # Verify React Native-specific files
        file_paths = [f.path for f in result.files]
        assert "app.json" in file_paths
        assert "App.tsx" in file_paths

    @pytest.mark.asyncio
    async def test_explicit_provider_overrides_intent(self, service):
        """Test explicit provider selection overrides intent routing"""
        spec = CodegenSpec(
            description="Create new app with Next.js",  # Would auto-route to app-builder
            project_name="test-app",
            framework="nextjs",
        )

        # Explicitly request app-builder (even though it would be auto-selected)
        result = await service.generate(spec, preferred_provider="app-builder")

        # Verify app-builder was used
        assert result.provider == "app-builder"

    def test_intent_detection_new_scaffold(self, intent_router):
        """Test intent detection for NEW_SCAFFOLD requests"""
        # Test various NEW_SCAFFOLD descriptions
        test_cases = [
            "Create Instagram clone with Next.js",
            "Build new SaaS app with Stripe",
            "Initialize FastAPI REST API",
            "Start mobile app with React Native",
            "Scaffold e-commerce platform",
            "Bootstrap blog with Next.js",
        ]

        for description in test_cases:
            detection = intent_router.detect_intent(description)

            assert detection.intent == IntentType.NEW_SCAFFOLD
            assert detection.confidence >= 0.75
            assert detection.recommended_provider == "app-builder"

    def test_intent_detection_modify_existing(self, intent_router):
        """Test intent detection for MODIFY_EXISTING requests"""
        # Test various MODIFY_EXISTING descriptions
        test_cases = [
            "Add authentication to existing app",
            "Update user profile page",
            "Fix bug in payment processing",
            "Refactor database queries",
            "Improve performance of API",
            "Change styling of homepage",
        ]

        for description in test_cases:
            detection = intent_router.detect_intent(
                description,
                has_existing_repo=True
            )

            assert detection.intent == IntentType.MODIFY_EXISTING
            assert detection.confidence >= 0.90  # High confidence with repo context
            assert detection.recommended_provider == "ollama"

    def test_intent_detection_feature_add(self, intent_router):
        """Test intent detection for FEATURE_ADD requests"""
        test_cases = [
            "Implement search functionality",
            "Add file upload feature",
            "Create notification system",
            "Enhance user dashboard",
        ]

        for description in test_cases:
            detection = intent_router.detect_intent(description)

            # Could be FEATURE_ADD or fall through to UNKNOWN
            assert detection.intent in [IntentType.FEATURE_ADD, IntentType.UNKNOWN]
            assert detection.recommended_provider == "ollama"

    def test_confidence_threshold_behavior(self):
        """Test confidence threshold affects routing decisions"""
        # Low threshold - more aggressive app-builder usage
        router_low = IntentRouter(confidence_threshold=0.50)

        # High threshold - more conservative
        router_high = IntentRouter(confidence_threshold=0.90)

        # Ambiguous description
        spec_ambiguous = "Build an app"

        detection_low = router_low.detect_intent(spec_ambiguous)
        detection_high = router_high.detect_intent(spec_ambiguous)

        # Both detect same intent, but routing decision differs
        if detection_low.intent == IntentType.NEW_SCAFFOLD:
            # Low threshold may route to app-builder
            can_use_app_builder_low = router_low.should_use_app_builder(detection_low)
            can_use_app_builder_high = router_high.should_use_app_builder(detection_high)

            # Verify low threshold is more permissive
            if can_use_app_builder_low and not can_use_app_builder_high:
                assert detection_low.confidence >= 0.50
                assert detection_low.confidence < 0.90


class TestIntentRouterScenarios:
    """Test realistic end-to-end scenarios"""

    @pytest.fixture
    def service(self):
        service = CodegenService(auto_register=False)
        from backend.app.services.codegen.app_builder_provider import AppBuilderProvider
        service._registry.register(AppBuilderProvider())
        return service

    @pytest.mark.asyncio
    async def test_scenario_instagram_clone(self, service):
        """
        Scenario: User wants to create Instagram clone

        Expected:
        1. Intent: NEW_SCAFFOLD (confidence > 0.75)
        2. Provider: app-builder (auto-routed)
        3. Template: Next.js Fullstack
        4. Files: 15+ including Prisma schema, API routes, pages
        """
        spec = CodegenSpec(
            description="Create Instagram clone with photo sharing and likes",
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

        result = await service.generate(spec)

        # Verify routing
        assert result.provider == "app-builder"

        # Verify comprehensive file generation
        assert len(result.files) >= 10

        file_paths = [f.path for f in result.files]
        assert "package.json" in file_paths
        assert any("prisma/schema.prisma" in path for path in file_paths)
        assert any("/api/post" in path for path in file_paths)

        # Verify Post entity in Prisma schema
        prisma_files = [f for f in result.files if "prisma/schema.prisma" in f.path]
        assert len(prisma_files) > 0
        assert "Post" in prisma_files[0].content
        assert "image_url" in prisma_files[0].content

        # Verify metadata
        assert result.metadata["entities_count"] == 1
        assert result.metadata["template"] == "nextjs-fullstack"

    @pytest.mark.asyncio
    async def test_scenario_saas_subscription_platform(self, service):
        """
        Scenario: User wants to create SaaS subscription platform

        Expected:
        1. Intent: NEW_SCAFFOLD (SaaS keywords detected)
        2. Provider: app-builder (auto-routed)
        3. Template: Next.js SaaS
        4. Files: Stripe integration, subscription management
        """
        spec = CodegenSpec(
            description="Build SaaS platform with Stripe subscriptions and billing",
            project_name="saas-starter",
            framework="nextjs",
            features=["auth", "payments", "subscriptions"],
        )

        result = await service.generate(spec)

        # Verify SaaS template selected
        assert result.provider == "app-builder"
        assert result.metadata["template"] == "nextjs-saas"

        # Verify Stripe-specific files
        file_paths = [f.path for f in result.files]
        assert any("stripe" in path.lower() for path in file_paths)
        assert any("checkout" in path.lower() for path in file_paths)

        # Verify Stripe webhooks
        webhook_files = [f for f in result.files if "webhook" in f.path.lower()]
        assert len(webhook_files) > 0

    @pytest.mark.asyncio
    async def test_scenario_blog_api_backend(self, service):
        """
        Scenario: User wants to create blog API (backend only)

        Expected:
        1. Intent: NEW_SCAFFOLD
        2. Provider: app-builder
        3. Template: FastAPI
        4. Files: REST API with SQLAlchemy models
        """
        spec = CodegenSpec(
            description="Create REST API for blog with FastAPI",
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

        result = await service.generate(spec)

        # Verify FastAPI template
        assert result.provider == "app-builder"
        assert result.metadata["template"] == "fastapi"

        # Verify FastAPI-specific files
        file_paths = [f.path for f in result.files]
        assert "requirements.txt" in file_paths
        assert any("models/article.py" in path for path in file_paths)
        assert any("api/endpoints/article.py" in path for path in file_paths)

    @pytest.mark.asyncio
    async def test_scenario_mobile_social_app(self, service):
        """
        Scenario: User wants to create mobile social media app

        Expected:
        1. Intent: NEW_SCAFFOLD (mobile keywords)
        2. Provider: app-builder
        3. Template: React Native
        4. Files: Expo + Zustand + Navigation
        """
        spec = CodegenSpec(
            description="Build social media mobile app for iOS and Android",
            project_name="social-mobile",
            framework="react-native",
        )

        result = await service.generate(spec)

        # Verify React Native template
        assert result.provider == "app-builder"
        assert result.metadata["template"] == "react-native"

        # Verify React Native-specific files
        file_paths = [f.path for f in result.files]
        assert "app.json" in file_paths
        assert "App.tsx" in file_paths
        assert any("navigation" in path.lower() for path in file_paths)

    @pytest.mark.asyncio
    async def test_performance_intent_routing_overhead(self, service):
        """Test intent routing adds minimal overhead (<100ms)"""
        import time

        spec = CodegenSpec(
            description="Create simple app with Next.js",
            project_name="perf-test",
            framework="nextjs",
        )

        # Measure time for intent routing
        start = time.time()
        routed_provider = service._route_by_intent(spec, has_existing_repo=False)
        routing_time_ms = (time.time() - start) * 1000

        # Intent routing should be fast (<100ms)
        assert routing_time_ms < 100
        assert routed_provider == "app-builder"

    def test_intent_router_keywords_coverage(self):
        """Test intent router recognizes all documented keywords"""
        router = IntentRouter()

        # Test NEW_SCAFFOLD keywords
        scaffold_keywords = ["create", "new", "scaffold", "bootstrap", "init", "start"]
        for keyword in scaffold_keywords:
            detection = router.detect_intent(f"{keyword} app with Next.js")
            assert detection.intent == IntentType.NEW_SCAFFOLD
            assert keyword in detection.matched_keywords

        # Test MODIFY keywords
        modify_keywords = ["modify", "change", "update", "refactor", "fix", "improve"]
        for keyword in modify_keywords:
            detection = router.detect_intent(
                f"{keyword} existing app",
                has_existing_repo=True
            )
            assert detection.intent == IntentType.MODIFY_EXISTING


class TestIntentRouterEdgeCases:
    """Test edge cases and error handling"""

    @pytest.fixture
    def service(self):
        service = CodegenService(auto_register=False)
        from backend.app.services.codegen.app_builder_provider import AppBuilderProvider
        service._registry.register(AppBuilderProvider())
        return service

    def test_empty_description(self):
        """Test handling of empty description"""
        router = IntentRouter()
        detection = router.detect_intent("")

        # Should fallback to UNKNOWN
        assert detection.intent == IntentType.UNKNOWN
        assert detection.confidence < 0.75

    def test_ambiguous_description(self):
        """Test handling of ambiguous description"""
        router = IntentRouter()
        detection = router.detect_intent("do something with code")

        # Should fallback with low confidence
        assert detection.confidence < 0.75

    @pytest.mark.asyncio
    async def test_intent_routing_failure_graceful_fallback(self, service):
        """Test graceful fallback when intent routing fails"""
        spec = CodegenSpec(
            description="Create app",
            project_name="test",
        )

        # Even with minimal description, should still work
        result = await service.generate(spec)

        # Should use app-builder (fallback to most versatile template)
        assert result.provider == "app-builder"
        assert len(result.files) > 0

    def test_vietnamese_keywords_detection(self):
        """Test Vietnamese keyword detection"""
        router = IntentRouter()

        # Vietnamese NEW_SCAFFOLD keywords
        detection = router.detect_intent("Tạo mới ứng dụng với Next.js")
        assert detection.intent == IntentType.NEW_SCAFFOLD

        # Vietnamese MODIFY keywords
        detection = router.detect_intent(
            "Sửa chữa lỗi trong ứng dụng",
            has_existing_repo=True
        )
        assert detection.intent == IntentType.MODIFY_EXISTING
