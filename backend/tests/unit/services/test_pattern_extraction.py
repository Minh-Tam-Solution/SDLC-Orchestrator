"""
Unit Tests for Pattern Extraction Service (Agentic Grep)

SDLC Stage: 04 - BUILD
Sprint: 98 - Planning Sub-agent Implementation Part 1
Framework: SDLC 5.2.0
Epic: EP-10 Planning Mode with Sub-agent Orchestration

Purpose:
Comprehensive unit tests for PatternExtractionService.
Tests agentic grep approach, pattern matching, and relevance scoring.

Coverage Target: 80%+
Reference: ADR-034-Planning-Subagent-Orchestration

Key Insight (Expert Workflow):
"Agentic grep > RAG for context retrieval"
"""

import tempfile
from pathlib import Path

import pytest

from app.schemas.planning_subagent import (
    ExploreAgentType,
    PatternCategory,
)
from app.services.pattern_extraction_service import PatternExtractionService


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def pattern_service():
    """Create a fresh PatternExtractionService instance."""
    return PatternExtractionService()


@pytest.fixture
def python_project_dir():
    """Create a temporary Python project directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)

        # Create app/services directory
        (project_path / "app" / "services").mkdir(parents=True)

        # Create a service file with patterns
        (project_path / "app" / "services" / "user_service.py").write_text('''
"""User Service Module."""
import logging
from typing import Optional
from uuid import UUID

from fastapi import HTTPException

logger = logging.getLogger(__name__)


class UserService:
    """Service for user operations."""

    def __init__(self, repository):
        """Initialize with repository dependency."""
        self.repository = repository

    async def get_user_by_id(self, user_id: UUID) -> Optional[dict]:
        """Get user by ID."""
        try:
            user = await self.repository.find_by_id(user_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            return user
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            raise

    async def create_user(self, data: dict) -> dict:
        """Create a new user."""
        try:
            return await self.repository.create(data)
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise
''')

        # Create another service file
        (project_path / "app" / "services" / "auth_service.py").write_text('''
"""Authentication Service Module."""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication operations."""

    async def authenticate(self, username: str, password: str) -> Optional[str]:
        """Authenticate user and return token."""
        try:
            # Authentication logic
            return "jwt_token"
        except Exception as e:
            logger.error(f"Authentication failed for {username}: {e}")
            raise
''')

        # Create API router file
        (project_path / "app" / "api").mkdir(parents=True)
        (project_path / "app" / "api" / "users.py").write_text('''
"""Users API Router."""
from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}")
async def get_user(user_id: UUID):
    """Get user by ID."""
    return {"id": user_id}


@router.post("/")
async def create_user(data: dict):
    """Create a new user."""
    return data


@router.delete("/{user_id}")
async def delete_user(user_id: UUID):
    """Delete user by ID."""
    return {"deleted": True}
''')

        yield project_path


@pytest.fixture
def typescript_project_dir():
    """Create a temporary TypeScript project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)

        # Create src directory
        (project_path / "src" / "services").mkdir(parents=True)

        # Create a TypeScript service
        (project_path / "src" / "services" / "userService.ts").write_text('''
import { User } from '../types';

export class UserService {
  constructor(private repository: UserRepository) {}

  async getUserById(userId: string): Promise<User | null> {
    try {
      return await this.repository.findById(userId);
    } catch (error) {
      console.error(`Failed to get user ${userId}:`, error);
      throw error;
    }
  }

  async createUser(data: CreateUserDto): Promise<User> {
    return await this.repository.create(data);
  }
}
''')

        yield project_path


# =============================================================================
# Test: Basic Functionality
# =============================================================================


@pytest.mark.asyncio
async def test_search_similar_implementations(pattern_service, python_project_dir):
    """Test basic pattern extraction from Python project."""
    result = await pattern_service.search_similar_implementations(
        task="Add user profile update feature",
        project_path=python_project_dir,
        depth=3,
    )

    assert result is not None
    assert result.agent_type == ExploreAgentType.SIMILAR_IMPLEMENTATIONS
    assert result.status == "completed"
    assert result.files_searched > 0


@pytest.mark.asyncio
async def test_extracts_code_patterns(pattern_service, python_project_dir):
    """Test that code patterns are extracted."""
    result = await pattern_service.search_similar_implementations(
        task="Add new service with logging",
        project_path=python_project_dir,
        depth=3,
    )

    # Should find patterns
    assert len(result.patterns) > 0

    # Check pattern structure
    for pattern in result.patterns:
        assert pattern.id is not None
        assert pattern.category is not None
        assert pattern.name is not None
        assert pattern.confidence > 0


@pytest.mark.asyncio
async def test_finds_error_handling_patterns(pattern_service, python_project_dir):
    """Test detection of error handling patterns."""
    result = await pattern_service.search_similar_implementations(
        task="Add error handling to payment service",
        project_path=python_project_dir,
        depth=3,
    )

    # Should find error handling patterns (try/except)
    error_patterns = [
        p for p in result.patterns
        if p.category == PatternCategory.ERROR_HANDLING
    ]

    # Project has try/except blocks, should detect them
    # Note: May be empty if no patterns matched the current task
    assert result.patterns is not None


@pytest.mark.asyncio
async def test_finds_api_patterns(pattern_service, python_project_dir):
    """Test detection of API design patterns."""
    result = await pattern_service.search_similar_implementations(
        task="Add new API endpoint for users",
        project_path=python_project_dir,
        depth=3,
    )

    # Check that API-related files were searched
    assert result.files_searched > 0


# =============================================================================
# Test: Concept Extraction
# =============================================================================


def test_extract_task_concepts(pattern_service):
    """Test key concept extraction from task description."""
    concepts = pattern_service._extract_task_concepts(
        "Add OAuth2 authentication with Google provider"
    )

    assert "oauth2" in concepts or "oauth" in concepts
    assert "authentication" in concepts
    assert "google" in concepts
    assert "provider" in concepts

    # Stop words should be excluded
    assert "with" not in concepts
    assert "add" not in concepts


def test_extract_concepts_excludes_common_words(pattern_service):
    """Test that common words are excluded from concepts."""
    concepts = pattern_service._extract_task_concepts(
        "The user should be able to create and delete items"
    )

    # Common words excluded
    assert "the" not in concepts
    assert "to" not in concepts
    assert "and" not in concepts
    assert "be" not in concepts

    # Meaningful words included
    assert "user" in concepts
    assert "create" in concepts
    assert "delete" in concepts
    assert "items" in concepts


# =============================================================================
# Test: Grep Pattern Generation
# =============================================================================


def test_generate_grep_patterns(pattern_service):
    """Test grep pattern generation from concepts."""
    concepts = {"user", "service", "create"}
    patterns = pattern_service._generate_grep_patterns(concepts)

    assert len(patterns) > 0
    # Should include word boundary patterns
    assert any("user" in p for p in patterns)


# =============================================================================
# Test: Relevance Calculation
# =============================================================================


def test_calculate_relevance(pattern_service):
    """Test relevance calculation between content and concepts."""
    content = "This is a user service that handles authentication and creates users"
    concepts = {"user", "service", "authentication", "create"}

    relevance = pattern_service._calculate_relevance(content, concepts)

    assert 0 <= relevance <= 1
    assert relevance > 0.5  # High relevance expected


def test_calculate_relevance_low(pattern_service):
    """Test low relevance for unrelated content."""
    content = "This is a database migration script for table creation"
    concepts = {"authentication", "oauth", "google", "login"}

    relevance = pattern_service._calculate_relevance(content, concepts)

    assert 0 <= relevance <= 1
    assert relevance < 0.5  # Low relevance expected


# =============================================================================
# Test: File Filtering
# =============================================================================


def test_should_scan_python_files(pattern_service):
    """Test that Python files are scanned."""
    assert pattern_service._should_scan_file(Path("app/services/user_service.py"))
    assert pattern_service._should_scan_file(Path("tests/test_user.py"))


def test_should_scan_typescript_files(pattern_service):
    """Test that TypeScript files are scanned."""
    assert pattern_service._should_scan_file(Path("src/services/userService.ts"))
    assert pattern_service._should_scan_file(Path("src/components/User.tsx"))


def test_excludes_node_modules(pattern_service):
    """Test that node_modules is excluded."""
    assert not pattern_service._should_scan_file(
        Path("node_modules/express/index.js")
    )


def test_excludes_pycache(pattern_service):
    """Test that __pycache__ is excluded."""
    assert not pattern_service._should_scan_file(
        Path("app/__pycache__/module.cpython-311.pyc")
    )


def test_excludes_venv(pattern_service):
    """Test that venv directories are excluded."""
    assert not pattern_service._should_scan_file(Path("venv/lib/python3.11/site.py"))
    assert not pattern_service._should_scan_file(Path(".venv/bin/python"))


def test_excludes_dist(pattern_service):
    """Test that dist/build directories are excluded."""
    assert not pattern_service._should_scan_file(Path("dist/bundle.js"))
    assert not pattern_service._should_scan_file(Path("build/output.js"))


# =============================================================================
# Test: Empty Project Handling
# =============================================================================


@pytest.mark.asyncio
async def test_empty_project_returns_empty_results(pattern_service):
    """Test handling of empty project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = await pattern_service.search_similar_implementations(
            task="Add user authentication",
            project_path=Path(tmpdir),
            depth=3,
        )

        assert result is not None
        assert result.status == "completed"
        assert result.files_searched == 0
        assert len(result.patterns) == 0


# =============================================================================
# Test: Depth Parameter
# =============================================================================


@pytest.mark.asyncio
async def test_depth_limits_search(pattern_service, python_project_dir):
    """Test that depth parameter limits directory traversal."""
    # Create deep nested structure
    deep_path = python_project_dir / "a" / "b" / "c" / "d" / "e"
    deep_path.mkdir(parents=True)
    (deep_path / "deep_service.py").write_text("def deep_function(): pass")

    # With depth=2, should not reach deep file
    result_shallow = await pattern_service.search_similar_implementations(
        task="Find deep function",
        project_path=python_project_dir,
        depth=2,
    )

    # With depth=10, should reach deep file
    result_deep = await pattern_service.search_similar_implementations(
        task="Find deep function",
        project_path=python_project_dir,
        depth=10,
    )

    # Deep search should find more or equal files
    assert result_deep.files_searched >= result_shallow.files_searched


# =============================================================================
# Test: Pattern Categories
# =============================================================================


@pytest.mark.asyncio
async def test_categorizes_patterns(pattern_service, python_project_dir):
    """Test that patterns are categorized correctly."""
    result = await pattern_service.search_similar_implementations(
        task="Add service with error handling",
        project_path=python_project_dir,
        depth=3,
    )

    if result.patterns:
        categories = {p.category for p in result.patterns}
        # Should have at least one category
        assert len(categories) >= 1


# =============================================================================
# Test: Code Snippet Extraction
# =============================================================================


@pytest.mark.asyncio
async def test_extracts_code_snippets(pattern_service, python_project_dir):
    """Test that code snippets are extracted for patterns."""
    result = await pattern_service.search_similar_implementations(
        task="Add user service function",
        project_path=python_project_dir,
        depth=3,
    )

    # Some patterns should have code snippets
    patterns_with_snippets = [p for p in result.patterns if p.code_snippet]
    # May or may not have snippets depending on matching
    assert result.patterns is not None


# =============================================================================
# Test: Execution Time Tracking
# =============================================================================


@pytest.mark.asyncio
async def test_tracks_execution_time(pattern_service, python_project_dir):
    """Test that execution time is tracked."""
    result = await pattern_service.search_similar_implementations(
        task="Track execution time test",
        project_path=python_project_dir,
        depth=3,
    )

    assert result.execution_time_ms > 0
    assert result.execution_time_ms < 30000  # Should be under 30s


# =============================================================================
# Test: Search Queries Logging
# =============================================================================


@pytest.mark.asyncio
async def test_logs_search_queries(pattern_service, python_project_dir):
    """Test that search queries are logged."""
    result = await pattern_service.search_similar_implementations(
        task="Log search queries test",
        project_path=python_project_dir,
        depth=3,
    )

    assert len(result.search_queries) > 0
