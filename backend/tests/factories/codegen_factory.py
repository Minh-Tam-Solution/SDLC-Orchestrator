"""
Codegen Factory - Test Data Generation

SDLC 5.2.0 Compliance - Test-Driven Development
Framework: Test Strategy 2026

Purpose:
    Generate CodegenSpec, CodegenResult, and TemplateBlueprint for testing.

Principles:
    1. Sensible defaults (realistic codegen data)
    2. Override support (Partial[CodegenSpec])
    3. Valid IR specifications
    4. Multi-provider support (Ollama, Claude, app-builder)

Usage:
    # Get CodegenSpec instance
    spec = get_mock_codegen_spec()
    nextjs_spec = get_mock_codegen_spec({"framework": "nextjs"})

    # Get CodegenResult instance
    result = get_mock_codegen_result()
    failed_result = get_mock_codegen_result({"success": False})

    # Get TemplateBlueprint instance
    blueprint = get_mock_codegen_blueprint()

Reference:
    - CodegenSpec: backend/app/schemas/codegen/codegen_spec.py
    - CodegenResult: backend/app/schemas/codegen/codegen_result.py
    - TemplateBlueprint: backend/app/schemas/codegen/template_blueprint.py
    - Test Strategy: docs/05-test/00-TEST-STRATEGY-2026.md § 3.5
    - EP-06: docs/02-design/14-Technical-Specs/Quality-Gates-Codegen-Specification.md
"""

from datetime import datetime, UTC
from typing import Optional, Dict, Any, List
from uuid import uuid4


def get_mock_codegen_spec(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Factory for CodegenSpec data.

    Returns a dictionary representing a CodegenSpec with sensible defaults.
    Use this when you need a complete CodegenSpec object for testing.

    Args:
        overrides: Optional dict to override default values

    Returns:
        Dict with CodegenSpec fields

    Examples:
        # Basic spec (Next.js full-stack)
        spec = get_mock_codegen_spec()

        # SaaS platform spec
        saas_spec = get_mock_codegen_spec({
            "description": "Build SaaS platform with Stripe",
            "tech_stack": ["nextjs", "stripe", "prisma"],
        })

        # FastAPI backend spec
        api_spec = get_mock_codegen_spec({
            "framework": "fastapi",
            "description": "Create REST API backend",
        })
    """
    defaults = {
        "id": str(uuid4()),
        "project_name": "test_project",
        "description": "Create Instagram clone with Next.js",
        "framework": "nextjs",
        "tech_stack": ["nextjs", "prisma", "tailwind", "shadcn"],
        "entities": [
            {
                "name": "User",
                "fields": ["id", "email", "username", "avatar_url"],
            },
            {
                "name": "Post",
                "fields": ["id", "user_id", "image_url", "caption", "created_at"],
            },
        ],
        "features": ["authentication", "file_upload", "social_features"],
        "domain": "social_media",
        "quality_profile": "scaffold",
        "metadata": {
            "requested_by": str(uuid4()),
            "project_id": str(uuid4()),
        },
    }

    return {**defaults, **(overrides or {})}


def get_mock_codegen_result(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Factory for CodegenResult data.

    Returns a dictionary representing a CodegenResult with sensible defaults.
    Use this when you need a complete CodegenResult object for testing.

    Args:
        overrides: Optional dict to override default values

    Returns:
        Dict with CodegenResult fields

    Examples:
        # Successful generation
        result = get_mock_codegen_result()

        # Failed generation
        failed = get_mock_codegen_result({
            "success": False,
            "error_message": "Template not found",
        })

        # Generation with retries
        retry_result = get_mock_codegen_result({
            "validation_attempts": 2,
            "metadata": {"retries": 1},
        })
    """
    defaults = {
        "id": str(uuid4()),
        "spec_id": str(uuid4()),
        "provider": "app-builder",
        "success": True,
        "generated_files": {
            "package.json": "{ ... }",
            "app/layout.tsx": "export default function Layout() { ... }",
            "prisma/schema.prisma": "model User { ... }",
        },
        "validation_results": {
            "gate1_syntax": {"passed": True, "duration_ms": 450},
            "gate2_security": {"passed": True, "duration_ms": 1250},
            "gate3_context": {"passed": True, "duration_ms": 800},
            "gate4_tests": {"passed": True, "duration_ms": 35000},
        },
        "validation_attempts": 1,
        "quality_score": 95,
        "cost": {
            "planning_cost": 0.02,
            "execution_cost": 0.0,
            "total_cost": 0.02,
        },
        "duration_seconds": 8.5,
        "error_message": None,
        "metadata": {
            "template": "nextjs-fullstack",
            "blueprint_id": str(uuid4()),
        },
        "created_at": datetime.now(UTC),
    }

    return {**defaults, **(overrides or {})}


def get_mock_codegen_blueprint(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Factory for TemplateBlueprint data.

    Returns a dictionary representing a TemplateBlueprint with sensible defaults.
    Use this when you need a complete TemplateBlueprint object for testing.

    Args:
        overrides: Optional dict to override default values

    Returns:
        Dict with TemplateBlueprint fields

    Examples:
        # Basic blueprint (Next.js)
        blueprint = get_mock_codegen_blueprint()

        # SaaS blueprint with Stripe
        saas_blueprint = get_mock_codegen_blueprint({
            "template_type": "nextjs-saas",
            "features": ["authentication", "payment", "subscriptions"],
        })

        # API blueprint
        api_blueprint = get_mock_codegen_blueprint({
            "template_type": "fastapi",
            "project_name": "blog_api",
        })
    """
    defaults = {
        "blueprint_id": str(uuid4()),
        "template_type": "nextjs-fullstack",
        "project_name": "test_project",
        "tech_stack": ["nextjs", "prisma", "tailwind", "shadcn"],
        "entities": [
            {
                "name": "User",
                "fields": [
                    {"name": "id", "type": "String", "primary": True},
                    {"name": "email", "type": "String", "unique": True},
                    {"name": "username", "type": "String"},
                ],
            },
            {
                "name": "Post",
                "fields": [
                    {"name": "id", "type": "String", "primary": True},
                    {"name": "user_id", "type": "String", "foreign_key": "User.id"},
                    {"name": "content", "type": "String"},
                ],
            },
        ],
        "api_routes": [
            {"path": "/api/users", "method": "GET"},
            {"path": "/api/users", "method": "POST"},
            {"path": "/api/posts", "method": "GET"},
            {"path": "/api/posts", "method": "POST"},
        ],
        "pages": [
            {"path": "/", "name": "Home"},
            {"path": "/login", "name": "Login"},
            {"path": "/feed", "name": "Feed"},
        ],
        "features": ["authentication", "crud_operations"],
        "integrity_hash": "abc123def456...",
        "created_at": datetime.now(UTC).isoformat(),
    }

    return {**defaults, **(overrides or {})}


# ─────────────────────────────────────────────────────────────
# Template-Specific Factories
# ─────────────────────────────────────────────────────────────

def get_mock_nextjs_fullstack_spec(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Factory for Next.js full-stack project spec"""
    nextjs_defaults = {
        "framework": "nextjs",
        "description": "Create full-stack app with Next.js",
        "tech_stack": ["nextjs", "prisma", "tailwind", "shadcn"],
    }
    return get_mock_codegen_spec({**nextjs_defaults, **(overrides or {})})


def get_mock_nextjs_saas_spec(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Factory for Next.js SaaS platform spec"""
    saas_defaults = {
        "framework": "nextjs",
        "description": "Build SaaS platform with Stripe subscriptions",
        "tech_stack": ["nextjs", "stripe", "prisma", "tailwind"],
        "features": ["authentication", "payment", "subscriptions"],
        "domain": "saas",
    }
    return get_mock_codegen_spec({**saas_defaults, **(overrides or {})})


def get_mock_fastapi_spec(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Factory for FastAPI backend spec"""
    fastapi_defaults = {
        "framework": "fastapi",
        "description": "Create REST API backend with FastAPI",
        "tech_stack": ["fastapi", "sqlalchemy", "postgresql", "redis"],
        "domain": "backend",
    }
    return get_mock_codegen_spec({**fastapi_defaults, **(overrides or {})})


def get_mock_react_native_spec(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Factory for React Native mobile app spec"""
    rn_defaults = {
        "framework": "react-native",
        "description": "Create mobile app with React Native",
        "tech_stack": ["react-native", "expo", "zustand", "react-native-paper"],
        "features": ["authentication", "navigation", "offline_sync"],
        "domain": "mobile",
    }
    return get_mock_codegen_spec({**rn_defaults, **(overrides or {})})


# ─────────────────────────────────────────────────────────────
# Provider-Specific Factories
# ─────────────────────────────────────────────────────────────

def get_mock_ollama_codegen_result(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Factory for Ollama provider codegen result"""
    ollama_defaults = {
        "provider": "ollama",
        "cost": {
            "planning_cost": 0.0,
            "execution_cost": 0.0,
            "total_cost": 0.0,
        },
        "duration_seconds": 25.0,
        "metadata": {
            "model": "qwen3-coder:30b",
            "tokens_used": 15000,
        },
    }
    return get_mock_codegen_result({**ollama_defaults, **(overrides or {})})


def get_mock_claude_codegen_result(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Factory for Claude provider codegen result"""
    claude_defaults = {
        "provider": "claude",
        "cost": {
            "planning_cost": 0.50,
            "execution_cost": 1.50,
            "total_cost": 2.00,
        },
        "duration_seconds": 18.0,
        "metadata": {
            "model": "claude-sonnet-4-5-20250929",
            "tokens_used": 25000,
        },
    }
    return get_mock_codegen_result({**claude_defaults, **(overrides or {})})


def get_mock_app_builder_codegen_result(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Factory for app-builder provider codegen result"""
    app_builder_defaults = {
        "provider": "app-builder",
        "cost": {
            "planning_cost": 0.02,
            "execution_cost": 0.0,
            "total_cost": 0.02,
        },
        "duration_seconds": 8.5,
        "metadata": {
            "template": "nextjs-fullstack",
            "deterministic": True,
        },
    }
    return get_mock_codegen_result({**app_builder_defaults, **(overrides or {})})


# ─────────────────────────────────────────────────────────────
# Validation Result Factories
# ─────────────────────────────────────────────────────────────

def get_mock_validation_results(all_passed: bool = True) -> Dict[str, Any]:
    """
    Factory for 4-Gate quality pipeline validation results.

    Args:
        all_passed: If True, all gates pass. If False, generate failed gates.

    Returns:
        Dict with validation results for all 4 gates

    Examples:
        # All gates passed
        passed_results = get_mock_validation_results(True)

        # Some gates failed
        failed_results = get_mock_validation_results(False)
    """
    if all_passed:
        return {
            "gate1_syntax": {
                "passed": True,
                "duration_ms": 450,
                "errors": [],
            },
            "gate2_security": {
                "passed": True,
                "duration_ms": 1250,
                "errors": [],
            },
            "gate3_context": {
                "passed": True,
                "duration_ms": 800,
                "errors": [],
            },
            "gate4_tests": {
                "passed": True,
                "duration_ms": 35000,
                "errors": [],
            },
        }
    else:
        return {
            "gate1_syntax": {
                "passed": False,
                "duration_ms": 450,
                "errors": ["SyntaxError: Unexpected token on line 42"],
            },
            "gate2_security": {
                "passed": False,
                "duration_ms": 1250,
                "errors": ["SAST: SQL injection vulnerability detected"],
            },
            "gate3_context": {
                "passed": True,
                "duration_ms": 800,
                "errors": [],
            },
            "gate4_tests": {
                "passed": False,
                "duration_ms": 15000,
                "errors": ["3 unit tests failing"],
            },
        }
