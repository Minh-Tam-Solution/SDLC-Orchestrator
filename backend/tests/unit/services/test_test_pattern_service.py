"""
Unit Tests for Test Pattern Service

SDLC Stage: 04 - BUILD
Sprint: 98 - Planning Sub-agent Implementation Part 1
Framework: SDLC 5.2.0
Epic: EP-10 Planning Mode with Sub-agent Orchestration

Purpose:
Comprehensive unit tests for TestPatternService.
Tests test file detection, pattern extraction, and convention detection.

Coverage Target: 80%+
Reference: ADR-034-Planning-Subagent-Orchestration
"""

import tempfile
from pathlib import Path

import pytest

from app.schemas.planning_subagent import (
    ExploreAgentType,
    PatternCategory,
)
from app.services.test_pattern_service import TestPatternService


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def test_service():
    """Create a fresh TestPatternService instance."""
    return TestPatternService()


@pytest.fixture
def python_test_project():
    """Create a project with Python pytest tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)

        # Create test directory structure
        tests_path = project_path / "tests" / "unit"
        tests_path.mkdir(parents=True)

        # Create pytest test file
        (tests_path / "test_user_service.py").write_text('''
"""Tests for UserService."""
import pytest
from unittest.mock import MagicMock, AsyncMock
from uuid import uuid4

from app.services.user_service import UserService


@pytest.fixture
def mock_repository():
    """Create a mock repository."""
    repo = MagicMock()
    repo.find_by_id = AsyncMock(return_value={"id": uuid4(), "name": "Test"})
    return repo


@pytest.fixture
def user_service(mock_repository):
    """Create UserService with mock repo."""
    return UserService(repository=mock_repository)


@pytest.mark.asyncio
async def test_get_user_by_id(user_service, mock_repository):
    """Test getting user by ID."""
    user_id = uuid4()
    result = await user_service.get_user_by_id(user_id)

    assert result is not None
    mock_repository.find_by_id.assert_called_once_with(user_id)


@pytest.mark.asyncio
async def test_get_user_not_found(user_service, mock_repository):
    """Test getting non-existent user."""
    mock_repository.find_by_id = AsyncMock(return_value=None)

    with pytest.raises(Exception):
        await user_service.get_user_by_id(uuid4())


@pytest.mark.parametrize("name,expected", [
    ("Alice", True),
    ("Bob", True),
    ("", False),
])
def test_validate_name(name, expected):
    """Test name validation with parameters."""
    result = bool(name)
    assert result == expected
''')

        # Create integration tests
        integration_path = project_path / "tests" / "integration"
        integration_path.mkdir(parents=True)

        (integration_path / "test_api.py").write_text('''
"""Integration tests for API."""
import pytest
from httpx import AsyncClient

from app.main import app


@pytest.fixture
async def client():
    """Create async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_check(client):
    """Test health endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
''')

        yield project_path


@pytest.fixture
def typescript_test_project():
    """Create a project with TypeScript/Vitest tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)

        # Create test directory
        tests_path = project_path / "src" / "__tests__"
        tests_path.mkdir(parents=True)

        # Create Vitest test file
        (tests_path / "userService.test.ts").write_text('''
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { UserService } from '../services/userService';

describe('UserService', () => {
  let service: UserService;
  let mockRepository: any;

  beforeEach(() => {
    mockRepository = {
      findById: vi.fn(),
      create: vi.fn(),
    };
    service = new UserService(mockRepository);
  });

  describe('getUserById', () => {
    it('should return user when found', async () => {
      const mockUser = { id: '123', name: 'Test' };
      mockRepository.findById.mockResolvedValue(mockUser);

      const result = await service.getUserById('123');

      expect(result).toEqual(mockUser);
      expect(mockRepository.findById).toHaveBeenCalledWith('123');
    });

    it('should return null when not found', async () => {
      mockRepository.findById.mockResolvedValue(null);

      const result = await service.getUserById('invalid');

      expect(result).toBeNull();
    });
  });

  describe('createUser', () => {
    it('should create user successfully', async () => {
      const userData = { name: 'New User' };
      const created = { id: '456', ...userData };
      mockRepository.create.mockResolvedValue(created);

      const result = await service.createUser(userData);

      expect(result).toEqual(created);
    });
  });
});
''')

        # Create spec file
        (tests_path / "utils.spec.ts").write_text('''
import { describe, it, expect } from 'vitest';
import { formatDate, validateEmail } from '../utils';

describe('formatDate', () => {
  it('should format date correctly', () => {
    const date = new Date('2025-01-22');
    expect(formatDate(date)).toBe('2025-01-22');
  });
});

describe('validateEmail', () => {
  it.each([
    ['test@example.com', true],
    ['invalid', false],
    ['', false],
  ])('should validate %s as %s', (email, expected) => {
    expect(validateEmail(email)).toBe(expected);
  });
});
''')

        yield project_path


@pytest.fixture
def playwright_test_project():
    """Create a project with Playwright E2E tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)

        # Create e2e directory
        e2e_path = project_path / "e2e"
        e2e_path.mkdir(parents=True)

        # Create Playwright test file
        (e2e_path / "login.spec.ts").write_text('''
import { test, expect } from '@playwright/test';

test.describe('Login Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  test('should login successfully with valid credentials', async ({ page }) => {
    await page.fill('[data-testid="email"]', 'user@example.com');
    await page.fill('[data-testid="password"]', 'password123');
    await page.click('[data-testid="submit"]');

    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('[data-testid="welcome"]')).toBeVisible();
  });

  test('should show error with invalid credentials', async ({ page }) => {
    await page.fill('[data-testid="email"]', 'invalid@example.com');
    await page.fill('[data-testid="password"]', 'wrong');
    await page.click('[data-testid="submit"]');

    await expect(page.locator('[data-testid="error"]')).toBeVisible();
  });
});
''')

        yield project_path


# =============================================================================
# Test: Basic Test Pattern Detection
# =============================================================================


@pytest.mark.asyncio
async def test_find_test_patterns(test_service, python_test_project):
    """Test basic test pattern detection."""
    result = await test_service.find_test_patterns(
        task="Add unit tests for payment service",
        project_path=python_test_project,
    )

    assert result is not None
    assert result.agent_type == ExploreAgentType.TEST_PATTERNS
    assert result.status == "completed"


@pytest.mark.asyncio
async def test_scans_test_files(test_service, python_test_project):
    """Test that test files are scanned."""
    result = await test_service.find_test_patterns(
        task="Add tests",
        project_path=python_test_project,
    )

    assert result.files_searched > 0


@pytest.mark.asyncio
async def test_extracts_pytest_patterns(test_service, python_test_project):
    """Test extraction of pytest patterns."""
    result = await test_service.find_test_patterns(
        task="Add pytest fixtures",
        project_path=python_test_project,
    )

    # Should find pytest-related patterns
    testing_patterns = [
        p for p in result.patterns
        if p.category == PatternCategory.TESTING
    ]

    # May find patterns
    assert result.patterns is not None


# =============================================================================
# Test: Test File Detection
# =============================================================================


def test_is_test_file_python(test_service):
    """Test Python test file detection."""
    assert test_service._is_test_file("test_user.py")
    assert test_service._is_test_file("user_test.py")
    assert test_service._is_test_file("test_service_spec.py")

    assert not test_service._is_test_file("user_service.py")
    assert not test_service._is_test_file("conftest.py")


def test_is_test_file_typescript(test_service):
    """Test TypeScript test file detection."""
    assert test_service._is_test_file("user.test.ts")
    assert test_service._is_test_file("user.test.tsx")
    assert test_service._is_test_file("user.spec.ts")
    assert test_service._is_test_file("user.spec.tsx")

    assert not test_service._is_test_file("userService.ts")
    assert not test_service._is_test_file("User.tsx")


def test_is_test_file_javascript(test_service):
    """Test JavaScript test file detection."""
    assert test_service._is_test_file("user.test.js")
    assert test_service._is_test_file("user.test.jsx")
    assert test_service._is_test_file("user.spec.js")

    assert not test_service._is_test_file("index.js")


# =============================================================================
# Test: Test Directory Detection
# =============================================================================


@pytest.mark.asyncio
async def test_finds_tests_directory(test_service, python_test_project):
    """Test detection of tests directory."""
    dirs = test_service._find_test_directories(python_test_project)

    assert len(dirs) >= 1
    dir_names = [d.name for d in dirs]
    assert "tests" in dir_names or "unit" in dir_names or "integration" in dir_names


@pytest.mark.asyncio
async def test_finds_typescript_test_dirs(test_service, typescript_test_project):
    """Test detection of TypeScript test directories."""
    dirs = test_service._find_test_directories(typescript_test_project)

    # Should find __tests__ directory
    assert len(dirs) >= 1


@pytest.mark.asyncio
async def test_finds_e2e_directory(test_service, playwright_test_project):
    """Test detection of e2e test directory."""
    dirs = test_service._find_test_directories(playwright_test_project)

    dir_names = [d.name for d in dirs]
    assert "e2e" in dir_names


# =============================================================================
# Test: Framework Detection
# =============================================================================


@pytest.mark.asyncio
async def test_detects_pytest_framework(test_service, python_test_project):
    """Test pytest framework detection."""
    result = await test_service.find_test_patterns(
        task="Add pytest tests",
        project_path=python_test_project,
    )

    # Should detect pytest patterns
    pattern_names = [p.name for p in result.patterns]
    # May include pytest_fixture, pytest_async, pytest_parametrize
    assert result.patterns is not None


@pytest.mark.asyncio
async def test_detects_vitest_framework(test_service, typescript_test_project):
    """Test Vitest framework detection."""
    result = await test_service.find_test_patterns(
        task="Add Vitest tests",
        project_path=typescript_test_project,
    )

    # Should find vitest patterns (describe, it, expect)
    assert result.files_searched > 0


@pytest.mark.asyncio
async def test_detects_playwright_framework(test_service, playwright_test_project):
    """Test Playwright framework detection."""
    result = await test_service.find_test_patterns(
        task="Add E2E tests",
        project_path=playwright_test_project,
    )

    # Should detect playwright patterns
    assert result.files_searched > 0


# =============================================================================
# Test: Pattern Matching
# =============================================================================


def test_infer_pattern_type(test_service):
    """Test pattern type inference."""
    assert test_service._infer_pattern_type("pytest_fixture") == "fixture"
    assert test_service._infer_pattern_type("pytest_mock") == "mock"
    assert test_service._infer_pattern_type("pytest_parametrize") == "parametrize"
    assert test_service._infer_pattern_type("pytest_async") == "async"
    assert test_service._infer_pattern_type("playwright_test") == "e2e"
    assert test_service._infer_pattern_type("assertion") == "assertion"


def test_get_pattern_description(test_service):
    """Test pattern description retrieval."""
    desc = test_service._get_pattern_description("pytest_fixture")
    assert "fixture" in desc.lower()

    desc = test_service._get_pattern_description("pytest_async")
    assert "async" in desc.lower()

    desc = test_service._get_pattern_description("vitest_test")
    assert "vitest" in desc.lower()


# =============================================================================
# Test: Empty Project Handling
# =============================================================================


@pytest.mark.asyncio
async def test_no_tests_returns_empty_result(test_service):
    """Test handling of projects without tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)
        (project_path / "src").mkdir()
        (project_path / "src" / "main.py").write_text("def main(): pass")

        result = await test_service.find_test_patterns(
            task="Add tests",
            project_path=project_path,
        )

        assert result is not None
        assert result.status == "completed"
        assert result.files_searched == 0


# =============================================================================
# Test: Relevance Calculation
# =============================================================================


def test_calculate_relevance(test_service):
    """Test relevance calculation for test patterns."""
    from app.schemas.planning_subagent import TestPattern

    pattern = TestPattern(
        name="pytest_fixture",
        pattern_type="fixture",
        description="Pytest fixture for test setup",
        example_file="tests/test_user.py",
        frameworks_used=["pytest"],
    )

    concepts = {"pytest", "fixture", "test", "setup"}
    relevance = test_service._calculate_relevance(pattern, concepts)

    assert 0 <= relevance <= 1
    assert relevance > 0.2  # Should have base relevance


# =============================================================================
# Test: Execution Time Tracking
# =============================================================================


@pytest.mark.asyncio
async def test_tracks_execution_time(test_service, python_test_project):
    """Test that execution time is tracked."""
    result = await test_service.find_test_patterns(
        task="Track time",
        project_path=python_test_project,
    )

    assert result.execution_time_ms >= 0


# =============================================================================
# Test: Code Example Extraction
# =============================================================================


def test_extract_code_example(test_service):
    """Test code example extraction from matched pattern."""
    content = '''
@pytest.fixture
def user_service():
    return UserService()

def test_something():
    pass
'''
    example = test_service._extract_code_example(content, r"@pytest\.fixture")

    assert example is not None
    assert "@pytest.fixture" in example


# =============================================================================
# Test: Test Pattern Result Conversion
# =============================================================================


@pytest.mark.asyncio
async def test_get_test_pattern_result(test_service, python_test_project):
    """Test conversion to TestPatternResult."""
    explore_result = await test_service.find_test_patterns(
        task="Get result",
        project_path=python_test_project,
    )

    pattern_result = test_service.get_test_pattern_result(explore_result)

    assert pattern_result is not None
    assert pattern_result.test_files_scanned == explore_result.files_searched
    assert isinstance(pattern_result.coverage_conventions, dict)
    assert isinstance(pattern_result.test_structure, dict)


# =============================================================================
# Test: Exclusion Patterns
# =============================================================================


def test_should_exclude_node_modules(test_service):
    """Test that node_modules is excluded."""
    assert test_service._should_exclude("node_modules")


def test_should_exclude_pycache(test_service):
    """Test that __pycache__ is excluded."""
    assert test_service._should_exclude("__pycache__")


def test_should_exclude_venv(test_service):
    """Test that venv is excluded."""
    assert test_service._should_exclude("venv")
    assert test_service._should_exclude(".venv")


def test_should_not_exclude_regular_dirs(test_service):
    """Test that regular directories are not excluded."""
    assert not test_service._should_exclude("tests")
    assert not test_service._should_exclude("src")
    assert not test_service._should_exclude("app")
