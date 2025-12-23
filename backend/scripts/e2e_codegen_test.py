#!/usr/bin/env python3
"""
E2E Test Script for Codegen Service.

Sprint 45: Multi-Provider Codegen Architecture (EP-06)
Tests the full code generation flow with real Ollama server.

Usage:
    # Test against production Ollama (api.nhatquangholding.com)
    python scripts/e2e_codegen_test.py

    # Test against local Ollama
    CODEGEN_OLLAMA_URL=http://localhost:11434 python scripts/e2e_codegen_test.py

    # Run specific test
    python scripts/e2e_codegen_test.py --test health
    python scripts/e2e_codegen_test.py --test generate
    python scripts/e2e_codegen_test.py --test validate

Author: Backend Lead
Date: December 23, 2025
"""

import asyncio
import argparse
import json
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.codegen import CodegenService, CodegenSpec
from app.services.codegen.demos.vietnamese_sme_demo import get_retail_store_blueprint


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print section header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")


async def test_health():
    """Test health check endpoint."""
    print_header("Test 1: Health Check")

    service = CodegenService()
    health = service.health_check()

    print(f"Status: {json.dumps(health, indent=2)}")

    if health["healthy"]:
        print_success(f"Service is healthy with {health['available_count']} available providers")
        return True
    else:
        print_warning("Service is degraded - no available providers")
        print_info("This is expected if Ollama server is not reachable")
        return False


async def test_list_providers():
    """Test listing providers."""
    print_header("Test 2: List Providers")

    service = CodegenService()
    providers = service.list_providers()

    print(f"Registered providers: {len(providers)}")
    for p in providers:
        status = "✓ Available" if p["available"] else "✗ Unavailable"
        primary = " (PRIMARY)" if p.get("primary") else ""
        print(f"  - {p['name']}: {status}{primary}")

    if providers:
        print_success(f"Found {len(providers)} registered providers")
        return True
    else:
        print_error("No providers registered")
        return False


async def test_cost_estimation():
    """Test cost estimation."""
    print_header("Test 3: Cost Estimation")

    service = CodegenService()

    # Simple blueprint for estimation
    spec = CodegenSpec(
        app_blueprint={
            "name": "TestApp",
            "description": "Test application",
            "modules": [
                {
                    "name": "users",
                    "entities": [
                        {
                            "name": "User",
                            "fields": [
                                {"name": "id", "type": "uuid"},
                                {"name": "email", "type": "string"},
                                {"name": "name", "type": "string"}
                            ]
                        }
                    ]
                }
            ]
        },
        language="python",
        framework="fastapi"
    )

    estimates = service.estimate_cost(spec)

    print("Cost estimates by provider:")
    for name, est in estimates.items():
        print(f"  - {name}:")
        print(f"      Tokens: {est.estimated_tokens}")
        print(f"      Cost: ${est.estimated_cost_usd:.6f}")
        print(f"      Confidence: {est.confidence:.0%}")

    # Get cheapest provider
    cheapest = service.get_cheapest_provider(spec)
    if cheapest:
        name, est = cheapest
        print_success(f"Cheapest provider: {name} at ${est.estimated_cost_usd:.6f}")
        return True
    else:
        print_warning("No available providers for cost comparison")
        return False


async def test_generate_minimal():
    """Test code generation with minimal blueprint."""
    print_header("Test 4: Generate Code (Minimal Blueprint)")

    service = CodegenService()

    # Check if any provider is available
    health = service.health_check()
    if not health["healthy"]:
        print_warning("Skipping generation test - no providers available")
        print_info("Start Ollama server or configure CODEGEN_OLLAMA_URL")
        return None

    spec = CodegenSpec(
        app_blueprint={
            "name": "MinimalApp",
            "description": "Minimal test app",
            "modules": [
                {
                    "name": "items",
                    "entities": [
                        {
                            "name": "Item",
                            "fields": [
                                {"name": "id", "type": "uuid", "primary": True},
                                {"name": "name", "type": "string", "max_length": 100}
                            ]
                        }
                    ]
                }
            ]
        },
        language="python",
        framework="fastapi"
    )

    print_info("Generating code... (this may take 30-60 seconds)")
    start_time = time.time()

    try:
        result = await service.generate(spec)
        elapsed = time.time() - start_time

        print(f"\nGeneration completed in {elapsed:.1f}s")
        print(f"Provider: {result.provider}")
        print(f"Tokens used: {result.tokens_used}")
        print(f"Files generated: {len(result.files)}")

        if result.files:
            print("\nGenerated files:")
            for path, content in result.files.items():
                lines = len(content.split('\n'))
                print(f"  - {path} ({lines} lines)")

            # Show first file preview
            first_file = list(result.files.keys())[0]
            first_content = result.files[first_file]
            preview_lines = first_content.split('\n')[:15]
            print(f"\n{Colors.CYAN}Preview of {first_file}:{Colors.RESET}")
            for line in preview_lines:
                print(f"  {line}")
            if len(first_content.split('\n')) > 15:
                print("  ...")

            print_success(f"Generated {len(result.files)} files successfully")
            return True
        else:
            print_warning("No files were parsed from generation output")
            print("Raw output preview:")
            print(result.code[:500] + "..." if len(result.code) > 500 else result.code)
            return False

    except Exception as e:
        print_error(f"Generation failed: {e}")
        return False


async def test_generate_vietnamese():
    """Test code generation with Vietnamese SME blueprint."""
    print_header("Test 5: Generate Code (Vietnamese SME Blueprint)")

    service = CodegenService()

    # Check if any provider is available
    health = service.health_check()
    if not health["healthy"]:
        print_warning("Skipping Vietnamese test - no providers available")
        return None

    # Get the full Vietnamese SME blueprint
    blueprint = get_retail_store_blueprint()
    blueprint_dict = blueprint.model_dump()

    # Only generate one module to save time
    spec = CodegenSpec(
        app_blueprint=blueprint_dict,
        language="python",
        framework="fastapi",
        target_module="san_pham"  # Only generate products module
    )

    print_info("Generating Vietnamese SME code... (products module only)")
    print_info(f"Blueprint: {blueprint_dict['name']} - {blueprint_dict['description']}")
    start_time = time.time()

    try:
        result = await service.generate(spec)
        elapsed = time.time() - start_time

        print(f"\nGeneration completed in {elapsed:.1f}s")
        print(f"Provider: {result.provider}")
        print(f"Tokens used: {result.tokens_used}")
        print(f"Files generated: {len(result.files)}")

        # Check for Vietnamese content
        has_vietnamese = False
        for content in result.files.values():
            if any(c for c in content if ord(c) > 127):
                has_vietnamese = True
                break

        if has_vietnamese:
            print_success("Vietnamese comments detected in generated code")
        else:
            print_warning("No Vietnamese content detected - check prompt templates")

        if result.files:
            print_success(f"Generated {len(result.files)} files for Vietnamese SME module")
            return True
        else:
            return False

    except Exception as e:
        print_error(f"Vietnamese generation failed: {e}")
        return False


async def test_validate():
    """Test code validation."""
    print_header("Test 6: Validate Code")

    service = CodegenService()

    # Check if any provider is available
    health = service.health_check()
    if not health["healthy"]:
        print_warning("Skipping validation test - no providers available")
        return None

    # Sample code to validate
    sample_code = '''
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float

@app.get("/items/{item_id}")
def get_item(item_id: int):
    # No error handling - potential issue
    return {"id": item_id}

@app.post("/items")
def create_item(item: Item):
    return item
'''

    print_info("Validating sample FastAPI code...")

    try:
        result = await service.validate(
            sample_code,
            {"language": "python", "framework": "fastapi"}
        )

        print(f"\nValidation result: {'VALID' if result.valid else 'INVALID'}")

        if result.errors:
            print(f"\nErrors ({len(result.errors)}):")
            for err in result.errors:
                print(f"  - {err}")

        if result.warnings:
            print(f"\nWarnings ({len(result.warnings)}):")
            for warn in result.warnings:
                print(f"  - {warn}")

        if result.suggestions:
            print(f"\nSuggestions ({len(result.suggestions)}):")
            for sug in result.suggestions:
                print(f"  - {sug}")

        print_success("Validation completed")
        return True

    except Exception as e:
        print_error(f"Validation failed: {e}")
        return False


async def run_all_tests():
    """Run all E2E tests."""
    print_header("SDLC Orchestrator - Codegen E2E Tests")
    print(f"Sprint 45: Multi-Provider Codegen Architecture (EP-06)")
    print(f"Testing against: {service_url()}")

    results = {}

    # Run tests
    results["health"] = await test_health()
    results["providers"] = await test_list_providers()
    results["cost"] = await test_cost_estimation()
    results["generate_minimal"] = await test_generate_minimal()
    results["generate_vietnamese"] = await test_generate_vietnamese()
    results["validate"] = await test_validate()

    # Summary
    print_header("Test Summary")

    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r is None)

    for name, result in results.items():
        if result is True:
            print_success(f"{name}: PASSED")
        elif result is False:
            print_error(f"{name}: FAILED")
        else:
            print_warning(f"{name}: SKIPPED")

    print(f"\n{Colors.BOLD}Total: {passed} passed, {failed} failed, {skipped} skipped{Colors.RESET}")

    return failed == 0


def service_url():
    """Get current service URL."""
    from app.core.config import settings
    return settings.CODEGEN_OLLAMA_URL


async def main():
    parser = argparse.ArgumentParser(description="Codegen E2E Tests")
    parser.add_argument(
        "--test",
        choices=["health", "providers", "cost", "generate", "vietnamese", "validate", "all"],
        default="all",
        help="Specific test to run (default: all)"
    )
    args = parser.parse_args()

    if args.test == "all":
        success = await run_all_tests()
    elif args.test == "health":
        success = await test_health()
    elif args.test == "providers":
        success = await test_list_providers()
    elif args.test == "cost":
        success = await test_cost_estimation()
    elif args.test == "generate":
        success = await test_generate_minimal()
    elif args.test == "vietnamese":
        success = await test_generate_vietnamese()
    elif args.test == "validate":
        success = await test_validate()
    else:
        success = False

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
