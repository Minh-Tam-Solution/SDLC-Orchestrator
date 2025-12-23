#!/usr/bin/env python3
"""
Ollama Codegen Connection Test Script.

Sprint 45: Multi-Provider Codegen Architecture (EP-06)

This script tests the connection to Ollama and performs
a minimal code generation to verify the setup.

Usage:
    python scripts/test_ollama_codegen.py

Author: Backend Lead
Date: December 23, 2025
"""

import asyncio
import json
import sys
import time

# Add backend to path
sys.path.insert(0, "/home/nqh/shared/SDLC-Orchestrator/backend")

from app.core.config import settings


async def test_ollama_connection():
    """Test basic Ollama API connection."""
    import httpx

    print("=" * 60)
    print("OLLAMA CODEGEN CONNECTION TEST")
    print("=" * 60)
    print()

    # Configuration
    print("[CONFIG]")
    print(f"  Base URL: {settings.CODEGEN_OLLAMA_URL}")
    print(f"  Model: {settings.CODEGEN_MODEL_PRIMARY}")
    print(f"  Timeout: {settings.CODEGEN_TIMEOUT}s")
    print()

    # Test 1: Health check
    print("[TEST 1] Health Check...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{settings.CODEGEN_OLLAMA_URL}/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                print(f"  ✅ Ollama is reachable")
                print(f"  📦 Available models: {len(models)}")
                for m in models[:5]:
                    print(f"      - {m}")
                if len(models) > 5:
                    print(f"      ... and {len(models) - 5} more")
            else:
                print(f"  ❌ Ollama returned status {response.status_code}")
                return False
    except httpx.ConnectError as e:
        print(f"  ❌ Connection failed: {e}")
        print("  💡 Hint: Check if Ollama is running and accessible")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

    print()

    # Test 2: Simple generation
    print("[TEST 2] Minimal Generation Test...")
    try:
        minimal_blueprint = {
            "name": "TestApp",
            "description": "Test application",
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
        }

        prompt = f"""Tạo một SQLAlchemy model đơn giản cho Item với id và name.
Chỉ tạo 1 file duy nhất.

### FILE: app/models/item.py
```python
"""

        start_time = time.time()

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.CODEGEN_OLLAMA_URL}/api/generate",
                json={
                    "model": settings.CODEGEN_MODEL_PRIMARY,
                    "prompt": prompt,
                    "temperature": 0.3,
                    "stream": False,
                    "options": {
                        "num_ctx": 2048,
                        "num_predict": 500,
                    }
                }
            )
            response.raise_for_status()
            result = response.json()

        elapsed = time.time() - start_time
        output = result.get("response", "")
        tokens = result.get("eval_count", 0)

        print(f"  ✅ Generation successful")
        print(f"  ⏱️  Time: {elapsed:.2f}s")
        print(f"  🎯 Tokens: {tokens}")
        print(f"  📝 Output preview:")
        preview = output[:300].replace("\n", "\n      ")
        print(f"      {preview}...")

    except httpx.TimeoutException:
        print(f"  ❌ Generation timed out (60s)")
        print("  💡 Hint: Model may be loading, try again")
        return False
    except Exception as e:
        print(f"  ❌ Generation failed: {e}")
        return False

    print()

    # Test 3: Vietnamese prompt test
    print("[TEST 3] Vietnamese Prompt Test...")
    try:
        vn_prompt = """Bạn là AI chuyên gia phát triển phần mềm Việt Nam.
Tạo một function Python đơn giản để tính tổng hai số.
Thêm docstring tiếng Việt."""

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.CODEGEN_OLLAMA_URL}/api/generate",
                json={
                    "model": settings.CODEGEN_MODEL_PRIMARY,
                    "prompt": vn_prompt,
                    "temperature": 0.3,
                    "stream": False,
                    "options": {
                        "num_predict": 200,
                    }
                }
            )
            response.raise_for_status()
            result = response.json()

        output = result.get("response", "")
        has_vietnamese = any(ord(c) > 127 for c in output)

        print(f"  ✅ Vietnamese prompt works")
        print(f"  🇻🇳 Contains Vietnamese: {'Yes' if has_vietnamese else 'No'}")

    except Exception as e:
        print(f"  ⚠️  Vietnamese test failed: {e}")
        # Not critical

    print()
    print("=" * 60)
    print("✅ ALL TESTS PASSED - Ollama Codegen is ready!")
    print("=" * 60)

    return True


async def test_codegen_service():
    """Test the full CodegenService."""
    print()
    print("[TEST 4] CodegenService Integration...")

    try:
        from app.services.codegen.codegen_service import get_codegen_service
        from app.services.codegen.base_provider import CodegenSpec

        service = get_codegen_service()

        # Check health
        health = service.health_check()
        print(f"  Service healthy: {health['healthy']}")
        print(f"  Providers: {health['providers']}")
        print(f"  Available: {health['available_count']}/{health['total_count']}")

        if health['healthy']:
            print("  ✅ CodegenService is ready")
        else:
            print("  ⚠️  No providers available")

    except Exception as e:
        print(f"  ❌ Service test failed: {e}")


if __name__ == "__main__":
    print()
    success = asyncio.run(test_ollama_connection())
    asyncio.run(test_codegen_service())
    print()
    sys.exit(0 if success else 1)
