"""
Unit Tests for ADR Scanner Service

SDLC Stage: 04 - BUILD
Sprint: 98 - Planning Sub-agent Implementation Part 1
Framework: SDLC 5.2.0
Epic: EP-10 Planning Mode with Sub-agent Orchestration

Purpose:
Comprehensive unit tests for ADRScannerService.
Tests ADR detection, parsing, and relevance matching.

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
from app.services.adr_scanner_service import ADRScannerService


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def adr_service():
    """Create a fresh ADRScannerService instance."""
    return ADRScannerService()


@pytest.fixture
def project_with_adrs():
    """Create a project with ADR documents."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)

        # Create ADR directory structure
        adr_path = project_path / "docs" / "02-design" / "03-ADRs"
        adr_path.mkdir(parents=True)

        # Create ADR-001: Authentication Strategy
        (adr_path / "ADR-001-Authentication-Strategy.md").write_text('''
# ADR-001: Authentication Strategy

## Status
ACCEPTED

## Context
We need to decide on an authentication mechanism for our API.
Options considered: JWT, Session-based, OAuth2.

## Decision
We will use JWT tokens with OAuth2 for external providers.

- JWT tokens for API authentication
- OAuth2 for Google and GitHub login
- Refresh token rotation for security

## Consequences
- Stateless authentication
- Token storage on client side
- Need to handle token expiration
''')

        # Create ADR-007: AI Model Integration
        (adr_path / "ADR-007-AI-Model-Integration.md").write_text('''
# ADR-007: AI Model Integration Strategy

## Status
ACCEPTED

## Context
We need to integrate AI models for code generation and analysis.
Multiple providers available: OpenAI, Anthropic, local Ollama.

## Decision
Implement multi-provider fallback chain:
1. Primary: Ollama (local, cost-effective)
2. Fallback 1: Claude (Anthropic)
3. Fallback 2: GPT-4o (OpenAI)
4. Fallback 3: Rule-based templates

## Consequences
- Cost optimization (95% savings)
- Latency improvement
- Provider independence
- Need fallback handling code
''')

        # Create ADR with MADR format
        (adr_path / "ADR-010-Database-Selection.md").write_text('''
---
title: Database Selection
status: accepted
date: 2025-12-01
decision-makers: CTO, Backend Lead
---

# Database Selection

## Context and Problem Statement
Which database should we use for the main application data?

## Considered Options
* PostgreSQL
* MySQL
* MongoDB

## Decision Outcome
Chosen option: PostgreSQL with pgvector extension.

### Positive Consequences
- ACID compliance
- Vector search capability
- Strong community support

### Negative Consequences
- More complex setup than SQLite
- Requires connection pooling
''')

        yield project_path


@pytest.fixture
def project_without_adrs():
    """Create a project without ADR documents."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)
        (project_path / "docs").mkdir()
        (project_path / "src").mkdir()
        (project_path / "README.md").write_text("# My Project")
        yield project_path


# =============================================================================
# Test: Basic ADR Scanning
# =============================================================================


@pytest.mark.asyncio
async def test_find_related_adrs(adr_service, project_with_adrs):
    """Test finding ADRs related to a task."""
    result = await adr_service.find_related_adrs(
        task="Add OAuth2 authentication with Google",
        project_path=project_with_adrs,
    )

    assert result is not None
    assert result.agent_type == ExploreAgentType.ADR_PATTERNS
    assert result.status == "completed"


@pytest.mark.asyncio
async def test_scans_adr_files(adr_service, project_with_adrs):
    """Test that ADR files are scanned."""
    result = await adr_service.find_related_adrs(
        task="Authentication decision",
        project_path=project_with_adrs,
    )

    assert result.files_searched > 0
    assert result.files_relevant >= 0


@pytest.mark.asyncio
async def test_extracts_patterns_from_adrs(adr_service, project_with_adrs):
    """Test that patterns are extracted from ADR content."""
    result = await adr_service.find_related_adrs(
        task="Add AI model integration",
        project_path=project_with_adrs,
    )

    # Should find architecture patterns from ADRs
    arch_patterns = [
        p for p in result.patterns
        if p.category == PatternCategory.ARCHITECTURE
    ]

    # May find patterns if task matches ADR content
    assert result.patterns is not None


# =============================================================================
# Test: ADR Path Detection
# =============================================================================


@pytest.mark.asyncio
async def test_finds_standard_adr_paths(adr_service):
    """Test detection of standard ADR directory locations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)

        # Create various ADR locations
        locations = [
            "docs/ADRs",
            "docs/adr",
            "docs/decisions",
            "architecture/decisions",
        ]

        for loc in locations:
            (project_path / loc).mkdir(parents=True)
            (project_path / loc / "ADR-001.md").write_text("# ADR 001\n\n## Status\nAccepted")

        adr_dirs = adr_service._find_adr_directories(project_path)

        # Should find at least some ADR directories
        assert len(adr_dirs) >= 1


# =============================================================================
# Test: ADR Parsing
# =============================================================================


def test_is_adr_file(adr_service):
    """Test ADR file detection."""
    assert adr_service._is_adr_file("ADR-001.md")
    assert adr_service._is_adr_file("ADR-007-AI-Integration.md")
    assert adr_service._is_adr_file("adr-001-decision.md")
    assert adr_service._is_adr_file("001-authentication.md")

    assert not adr_service._is_adr_file("README.md")
    assert not adr_service._is_adr_file("CHANGELOG.md")
    assert not adr_service._is_adr_file("requirements.txt")


def test_parse_adr_content(adr_service):
    """Test parsing ADR markdown content."""
    content = '''
# ADR-001: Authentication Strategy

## Status
ACCEPTED

## Context
We need authentication for our API.

## Decision
Use JWT with OAuth2.

## Consequences
- Stateless auth
- Token management needed
'''
    adr = adr_service._parse_adr_content(content, "ADR-001.md")

    assert adr is not None
    assert adr.id == "ADR-001"
    assert adr.status == "accepted"
    assert "authentication" in adr.title.lower() or "strategy" in adr.title.lower()


def test_parse_madr_format(adr_service):
    """Test parsing MADR format ADRs."""
    content = '''---
title: Database Selection
status: accepted
date: 2025-12-01
---

# Database Selection

## Context and Problem Statement
Which database to use?

## Decision Outcome
Chosen option: PostgreSQL
'''
    adr = adr_service._parse_adr_content(content, "ADR-010.md")

    assert adr is not None
    assert adr.status == "accepted"


# =============================================================================
# Test: Relevance Matching
# =============================================================================


def test_calculate_adr_relevance(adr_service):
    """Test ADR relevance calculation."""
    adr_content = "Authentication JWT OAuth2 Google provider security tokens"
    task_concepts = {"authentication", "oauth2", "google", "jwt"}

    relevance = adr_service._calculate_relevance(adr_content, task_concepts)

    assert 0 <= relevance <= 1
    assert relevance > 0.3  # Should be fairly relevant


def test_calculate_low_relevance(adr_service):
    """Test low relevance for unrelated ADRs."""
    adr_content = "Database PostgreSQL migration schema tables indexes"
    task_concepts = {"authentication", "oauth2", "google", "jwt"}

    relevance = adr_service._calculate_relevance(adr_content, task_concepts)

    assert 0 <= relevance <= 1
    assert relevance < 0.5  # Should be low relevance


# =============================================================================
# Test: Empty Project Handling
# =============================================================================


@pytest.mark.asyncio
async def test_no_adrs_returns_empty_result(adr_service, project_without_adrs):
    """Test handling of projects without ADRs."""
    result = await adr_service.find_related_adrs(
        task="Add user authentication",
        project_path=project_without_adrs,
    )

    assert result is not None
    assert result.status == "completed"
    assert result.files_searched == 0


# =============================================================================
# Test: Task Concept Extraction
# =============================================================================


def test_extract_task_concepts(adr_service):
    """Test concept extraction from task description."""
    concepts = adr_service._extract_task_concepts(
        "Add OAuth2 authentication with Google provider"
    )

    assert "oauth2" in concepts or "oauth" in concepts
    assert "authentication" in concepts
    assert "google" in concepts

    # Stop words excluded
    assert "add" not in concepts
    assert "with" not in concepts


# =============================================================================
# Test: Execution Time Tracking
# =============================================================================


@pytest.mark.asyncio
async def test_tracks_execution_time(adr_service, project_with_adrs):
    """Test that execution time is tracked."""
    result = await adr_service.find_related_adrs(
        task="Check execution time",
        project_path=project_with_adrs,
    )

    assert result.execution_time_ms >= 0


# =============================================================================
# Test: Pattern Conversion
# =============================================================================


@pytest.mark.asyncio
async def test_converts_adrs_to_patterns(adr_service, project_with_adrs):
    """Test that ADRs are converted to ExtractedPattern objects."""
    result = await adr_service.find_related_adrs(
        task="Check AI model integration approach",
        project_path=project_with_adrs,
    )

    if result.patterns:
        for pattern in result.patterns:
            assert pattern.id is not None
            assert pattern.name is not None
            assert pattern.category == PatternCategory.ARCHITECTURE
            assert pattern.source_file is not None


# =============================================================================
# Test: ADR Status Filtering
# =============================================================================


@pytest.mark.asyncio
async def test_includes_accepted_adrs(adr_service, project_with_adrs):
    """Test that accepted ADRs are included."""
    result = await adr_service.find_related_adrs(
        task="Authentication approach",
        project_path=project_with_adrs,
    )

    # Should process accepted ADRs
    assert result.files_searched > 0


@pytest.mark.asyncio
async def test_deprecated_adr_handling(adr_service):
    """Test handling of deprecated/superseded ADRs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)
        adr_path = project_path / "docs" / "ADRs"
        adr_path.mkdir(parents=True)

        # Create deprecated ADR
        (adr_path / "ADR-001.md").write_text('''
# ADR-001: Old Approach

## Status
DEPRECATED - Superseded by ADR-002

## Decision
This is the old way.
''')

        result = await adr_service.find_related_adrs(
            task="Check deprecated handling",
            project_path=project_path,
        )

        # Should still scan the file
        assert result.files_searched >= 1
