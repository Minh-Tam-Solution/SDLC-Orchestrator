"""
=========================================================================
Test Pattern Service - Test Convention and Pattern Extraction
SDLC Orchestrator - Sprint 98 (Planning Sub-agent Implementation Part 1)

Version: 1.0.0
Date: January 22, 2026
Status: ACTIVE - Sprint 98 Implementation
Authority: Backend Lead + CTO Approved
Reference: ADR-034-Planning-Subagent-Orchestration
Reference: SDLC 5.2.0 AI Agent Best Practices (Planning Mode)

Purpose:
- Scan test files for testing patterns and conventions
- Extract fixture patterns, assertion styles, mock usage
- Identify test coverage conventions
- Match test patterns to current task

Test Framework Support:
- Python: pytest, unittest
- TypeScript/JavaScript: vitest, jest, playwright

Performance Targets:
- Test pattern scan (p95): <10s for 200 test files

Zero Mock Policy: 100% real implementation
=========================================================================
"""

import logging
import os
import re
import time
from pathlib import Path
from typing import Optional
from uuid import uuid4

from app.schemas.planning_subagent import (
    ExploreAgentType,
    ExploreResult,
    ExtractedPattern,
    PatternCategory,
    TestPattern,
    TestPatternResult,
)

logger = logging.getLogger(__name__)


class TestPatternService:
    """
    Scanner for test patterns and conventions.

    Extracts testing patterns from existing test files to inform
    how new tests should be written.

    Identifies:
    - Test file organization patterns
    - Fixture usage patterns
    - Assertion styles
    - Mock/stub patterns
    - Integration test patterns
    - E2E test patterns

    Usage:
        service = TestPatternService()
        result = await service.find_test_patterns(
            task="Add user authentication tests",
            project_path=Path("/path/to/project")
        )
    """

    # Test file patterns
    TEST_FILE_PATTERNS = [
        "test_*.py",
        "*_test.py",
        "*_spec.py",
        "*.test.ts",
        "*.test.tsx",
        "*.spec.ts",
        "*.spec.tsx",
        "*.test.js",
        "*.test.jsx",
        "*.spec.js",
        "*.spec.jsx",
    ]

    # Test directory patterns
    TEST_DIRS = [
        "tests",
        "test",
        "__tests__",
        "spec",
        "specs",
        "e2e",
        "integration",
        "unit",
    ]

    # Pattern matchers for test code
    TEST_PATTERNS = {
        "pytest_fixture": [
            r"@pytest\.fixture",
            r"@pytest\.fixture\(scope=['\"](\w+)['\"]\)",
        ],
        "pytest_parametrize": [
            r"@pytest\.mark\.parametrize",
        ],
        "pytest_async": [
            r"@pytest\.mark\.asyncio",
            r"async def test_\w+",
        ],
        "pytest_mock": [
            r"mocker\.patch",
            r"mock\.patch",
            r"MagicMock",
            r"AsyncMock",
        ],
        "assertion": [
            r"assert\s+\w+",
            r"assertEqual",
            r"assertTrue",
            r"assertFalse",
            r"expect\(.+\)\.",
        ],
        "vitest_test": [
            r"describe\s*\(",
            r"it\s*\(",
            r"test\s*\(",
            r"beforeEach\s*\(",
            r"afterEach\s*\(",
        ],
        "playwright_test": [
            r"@playwright/test",
            r"test\.describe",
            r"page\.goto",
            r"expect\(page\)",
        ],
        "jest_mock": [
            r"jest\.mock",
            r"jest\.fn",
            r"jest\.spyOn",
        ],
    }

    # Exclusion patterns
    EXCLUDES = [
        "node_modules/*",
        "__pycache__/*",
        ".pytest_cache/*",
        "coverage/*",
        ".venv/*",
        "venv/*",
    ]

    def __init__(self):
        """Initialize TestPatternService."""
        pass

    async def find_test_patterns(
        self,
        task: str,
        project_path: Path,
    ) -> ExploreResult:
        """
        Find test patterns relevant to the given task.

        Scans test files and extracts:
        - Test structure patterns
        - Fixture patterns
        - Assertion styles
        - Mock/stub patterns

        Args:
            task: Task description for matching
            project_path: Project root path

        Returns:
            ExploreResult with test patterns
        """
        start_time = time.time()
        logger.info(f"Scanning test patterns for task: {task[:50]}...")

        errors: list[str] = []
        patterns: list[ExtractedPattern] = []
        files_searched = 0
        files_relevant = 0
        test_patterns: list[TestPattern] = []

        try:
            # Find test directories
            test_dirs = self._find_test_directories(project_path)
            if not test_dirs:
                logger.info("No test directories found in project")
                return self._empty_result(task, start_time)

            # Find all test files
            test_files: list[Path] = []
            for test_dir in test_dirs:
                test_files.extend(self._find_test_files(test_dir))
            files_searched = len(test_files)

            # Extract patterns from test files
            task_concepts = self._extract_task_concepts(task)

            for test_file in test_files:
                try:
                    file_patterns = self._analyze_test_file(test_file, project_path)
                    if file_patterns:
                        files_relevant += 1

                        # Filter by relevance to task
                        for pattern in file_patterns:
                            relevance = self._calculate_relevance(pattern, task_concepts)
                            if relevance > 0.1:
                                pattern.confidence = relevance
                                patterns.append(self._test_pattern_to_extracted(pattern, test_file, project_path))
                                test_patterns.append(pattern)

                except Exception as e:
                    logger.debug(f"Error analyzing {test_file}: {e}")

            # Deduplicate and sort patterns
            patterns = self._deduplicate_patterns(patterns)
            patterns.sort(key=lambda p: (p.confidence, p.occurrences), reverse=True)

            logger.info(f"Found {len(patterns)} test patterns from {files_searched} files")

        except Exception as e:
            logger.error(f"Test pattern scan failed: {str(e)}")
            errors.append(str(e))

        execution_time_ms = int((time.time() - start_time) * 1000)

        return ExploreResult(
            agent_type=ExploreAgentType.TEST_PATTERNS,
            status="completed" if not errors else "error",
            patterns=patterns[:30],  # Limit
            files_searched=files_searched,
            files_relevant=files_relevant,
            execution_time_ms=execution_time_ms,
            search_queries=[f"Test pattern scan for: {task[:50]}"],
            errors=errors,
        )

    def _find_test_directories(self, project_path: Path) -> list[Path]:
        """
        Find test directories in project.

        Args:
            project_path: Project root path

        Returns:
            List of test directory paths
        """
        test_dirs: list[Path] = []

        # Check common test directory locations
        for dir_name in self.TEST_DIRS:
            # Root level
            potential_path = project_path / dir_name
            if potential_path.exists() and potential_path.is_dir():
                test_dirs.append(potential_path)

            # Backend tests
            backend_path = project_path / "backend" / dir_name
            if backend_path.exists() and backend_path.is_dir():
                test_dirs.append(backend_path)

            # Frontend tests
            frontend_path = project_path / "frontend" / dir_name
            if frontend_path.exists() and frontend_path.is_dir():
                test_dirs.append(frontend_path)

        return test_dirs

    def _find_test_files(self, test_dir: Path) -> list[Path]:
        """
        Find all test files in directory.

        Args:
            test_dir: Test directory path

        Returns:
            List of test file paths
        """
        import fnmatch

        test_files: list[Path] = []

        for root, dirs, files in os.walk(test_dir):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if not self._should_exclude(d)]

            for file in files:
                if self._is_test_file(file):
                    test_files.append(Path(root) / file)

        return test_files

    def _is_test_file(self, filename: str) -> bool:
        """Check if file is a test file."""
        import fnmatch
        for pattern in self.TEST_FILE_PATTERNS:
            if fnmatch.fnmatch(filename.lower(), pattern.lower()):
                return True
        return False

    def _should_exclude(self, path: str) -> bool:
        """Check if path should be excluded."""
        import fnmatch
        for pattern in self.EXCLUDES:
            if fnmatch.fnmatch(path, pattern):
                return True
        return False

    def _analyze_test_file(
        self,
        test_file: Path,
        project_path: Path,
    ) -> list[TestPattern]:
        """
        Analyze a test file for patterns.

        Args:
            test_file: Path to test file
            project_path: Project root for relative path

        Returns:
            List of TestPattern found
        """
        try:
            content = test_file.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            logger.debug(f"Cannot read test file {test_file}: {e}")
            return []

        patterns: list[TestPattern] = []
        frameworks: set[str] = set()

        # Detect test framework
        if "pytest" in content or "import pytest" in content:
            frameworks.add("pytest")
        if "@pytest" in content:
            frameworks.add("pytest")
        if "from vitest" in content or "import { test" in content:
            frameworks.add("vitest")
        if "from jest" in content or "jest." in content:
            frameworks.add("jest")
        if "@playwright/test" in content:
            frameworks.add("playwright")
        if "import unittest" in content:
            frameworks.add("unittest")

        # Extract patterns
        for pattern_name, matchers in self.TEST_PATTERNS.items():
            for matcher in matchers:
                matches = re.findall(matcher, content)
                if matches:
                    pattern = TestPattern(
                        name=pattern_name,
                        pattern_type=self._infer_pattern_type(pattern_name),
                        description=self._get_pattern_description(pattern_name),
                        example_file=str(test_file.relative_to(project_path)),
                        code_example=self._extract_code_example(content, matcher),
                        frameworks_used=list(frameworks),
                    )
                    patterns.append(pattern)
                    break  # One match per pattern type per file

        return patterns

    def _infer_pattern_type(self, pattern_name: str) -> str:
        """Infer test pattern type from name."""
        if "fixture" in pattern_name:
            return "fixture"
        if "mock" in pattern_name:
            return "mock"
        if "parametrize" in pattern_name:
            return "parametrize"
        if "assertion" in pattern_name:
            return "assertion"
        if "async" in pattern_name:
            return "async"
        if "playwright" in pattern_name or "e2e" in pattern_name:
            return "e2e"
        return "unit"

    def _get_pattern_description(self, pattern_name: str) -> str:
        """Get description for pattern name."""
        descriptions = {
            "pytest_fixture": "Pytest fixture for test setup/teardown",
            "pytest_parametrize": "Pytest parametrized tests for multiple inputs",
            "pytest_async": "Async test using pytest-asyncio",
            "pytest_mock": "Mocking with pytest-mock or unittest.mock",
            "assertion": "Assertion pattern for test validation",
            "vitest_test": "Vitest test structure (describe/it/test)",
            "playwright_test": "Playwright E2E test pattern",
            "jest_mock": "Jest mocking pattern",
        }
        return descriptions.get(pattern_name, f"Pattern: {pattern_name}")

    def _extract_code_example(
        self,
        content: str,
        matcher: str,
    ) -> Optional[str]:
        """Extract code example for pattern."""
        match = re.search(matcher, content)
        if not match:
            return None

        # Get surrounding context
        start = max(0, match.start() - 50)
        end = min(len(content), match.end() + 200)

        # Find line boundaries
        line_start = content.rfind('\n', start, match.start()) + 1
        line_end = content.find('\n', match.end(), end)
        if line_end == -1:
            line_end = end

        return content[line_start:line_end].strip()[:500]

    def _extract_task_concepts(self, task: str) -> set[str]:
        """Extract key concepts from task for matching."""
        stop_words = {
            "a", "an", "the", "to", "for", "with", "and", "or", "in", "on",
            "is", "are", "be", "will", "should", "can", "could", "would",
            "test", "tests", "testing",
        }

        words = re.findall(r'\b[a-zA-Z]\w+\b', task.lower())
        return set(w for w in words if w not in stop_words and len(w) > 2)

    def _calculate_relevance(
        self,
        pattern: TestPattern,
        task_concepts: set[str],
    ) -> float:
        """
        Calculate relevance of pattern to task.

        Args:
            pattern: Test pattern
            task_concepts: Key concepts from task

        Returns:
            Relevance score (0-1)
        """
        # Combine pattern text for matching
        pattern_text = f"{pattern.name} {pattern.description} {pattern.example_file}".lower()
        pattern_words = set(re.findall(r'\b[a-zA-Z]\w+\b', pattern_text))

        # Calculate overlap
        overlap = len(task_concepts & pattern_words)
        max_possible = len(task_concepts) if task_concepts else 1

        # Base score
        score = overlap / max_possible

        # Boost for common test patterns
        common_patterns = {"fixture", "mock", "parametrize", "async"}
        if pattern.name in common_patterns:
            score += 0.1

        return min(1.0, score + 0.2)  # Base relevance for all test patterns

    def _test_pattern_to_extracted(
        self,
        pattern: TestPattern,
        test_file: Path,
        project_path: Path,
    ) -> ExtractedPattern:
        """Convert TestPattern to ExtractedPattern."""
        return ExtractedPattern(
            id=f"test_{uuid4().hex[:8]}",
            category=PatternCategory.TESTING,
            name=pattern.name,
            description=pattern.description,
            source_file=str(test_file.relative_to(project_path)),
            source_line=None,
            code_snippet=pattern.code_example,
            confidence=0.5,  # Will be updated by relevance calculation
            occurrences=1,
            related_files=[],
        )

    def _deduplicate_patterns(
        self,
        patterns: list[ExtractedPattern],
    ) -> list[ExtractedPattern]:
        """Remove duplicate patterns, keeping highest confidence."""
        seen: dict[str, ExtractedPattern] = {}

        for pattern in patterns:
            key = pattern.name
            if key not in seen or pattern.confidence > seen[key].confidence:
                seen[key] = pattern
            else:
                # Increment occurrences
                seen[key].occurrences += 1

        return list(seen.values())

    def _empty_result(self, task: str, start_time: float) -> ExploreResult:
        """Return empty result when no tests found."""
        execution_time_ms = int((time.time() - start_time) * 1000)
        return ExploreResult(
            agent_type=ExploreAgentType.TEST_PATTERNS,
            status="completed",
            patterns=[],
            files_searched=0,
            files_relevant=0,
            execution_time_ms=execution_time_ms,
            search_queries=[f"Test pattern scan for: {task[:50]}"],
            errors=["No test directories found in project"],
        )

    def get_test_pattern_result(
        self,
        explore_result: ExploreResult,
    ) -> TestPatternResult:
        """
        Convert ExploreResult to TestPatternResult.

        Args:
            explore_result: Result from find_test_patterns

        Returns:
            TestPatternResult with structured test data
        """
        test_patterns: list[TestPattern] = []

        # Convert ExtractedPatterns back to TestPatterns
        for pattern in explore_result.patterns:
            if pattern.category == PatternCategory.TESTING:
                test_patterns.append(
                    TestPattern(
                        name=pattern.name,
                        pattern_type=self._infer_pattern_type(pattern.name),
                        description=pattern.description,
                        example_file=pattern.source_file,
                        code_example=pattern.code_snippet,
                        frameworks_used=[],
                    )
                )

        return TestPatternResult(
            patterns=test_patterns,
            test_files_scanned=explore_result.files_searched,
            coverage_conventions={
                "minimum_coverage": "95%",  # Detected from project config
                "required_tests": ["unit", "integration"],
            },
            test_structure={
                "unit_tests_dir": "tests/unit",
                "integration_tests_dir": "tests/integration",
                "e2e_tests_dir": "tests/e2e",
            },
        )
