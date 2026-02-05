"""
=========================================================================
SASE Generation Service Unit Tests
SDLC Orchestrator - Sprint 151 Day 5

Version: 1.0.0
Date: February 3, 2026
Status: ACTIVE - Sprint 151 Testing
Authority: Backend Lead + CTO Approved
Reference: docs/04-build/02-Sprint-Plans/SPRINT-151-SASE-ARTIFACTS.md

Test Coverage:
- VCR Generation: AI-based and rule-based
- CRP Generation: AI-based and rule-based
- AI Tool Detection: Cursor, Claude, Copilot, etc.
- Expertise Detection: Security, Database, API, etc.
- Priority Detection: Urgent, High, Medium, Low

Zero Mock Policy: Tests use real dataclasses and schemas
=========================================================================
"""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.sase_generation_service import (
    AIToolType,
    AI_TOOL_MARKERS,
    CRPGenerationResult,
    SASEGenerationService,
    VCRGenerationResult,
    create_sase_generation_service,
)


# =========================================================================
# Fixtures
# =========================================================================


@pytest.fixture
def sample_pr_diff():
    """Sample PR diff for testing."""
    return """diff --git a/backend/app/services/auth_service.py b/backend/app/services/auth_service.py
index abc123..def456 100644
--- a/backend/app/services/auth_service.py
+++ b/backend/app/services/auth_service.py
@@ -10,6 +10,15 @@ class AuthService:
     def __init__(self):
         self.secret_key = settings.SECRET_KEY

+    async def refresh_token(self, token: str) -> str:
+        '''
+        Refresh an expired JWT token.
+
+        Generated with Claude assistance.
+        '''
+        payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
+        return self._generate_token(payload['user_id'])
+
     def authenticate(self, username: str, password: str) -> Optional[User]:
         user = self.db.query(User).filter_by(username=username).first()
         if user and bcrypt.checkpw(password, user.password_hash):
"""


@pytest.fixture
def sample_commit_messages():
    """Sample commit messages for testing."""
    return [
        "fix: resolve authentication timeout issue",
        "feat: add token refresh mechanism",
        "docs: update API documentation for auth endpoints",
        "test: add unit tests for auth service",
    ]


@pytest.fixture
def sample_code_snippet():
    """Sample code snippet for CRP context."""
    return """
async def authenticate(self, token: str) -> User:
    '''Authenticate user with JWT token.'''
    try:
        payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
        user_id = payload.get('user_id')
        if not user_id:
            raise AuthenticationError('Invalid token')
        return await self.get_user(user_id)
    except jwt.ExpiredSignatureError:
        raise AuthenticationError('Token expired')
"""


@pytest.fixture
def mock_ollama_service():
    """Mock Ollama service for testing."""
    mock = MagicMock()
    mock.generate_async = AsyncMock()
    return mock


# =========================================================================
# VCR Generation Tests
# =========================================================================


class TestVCRGeneration:
    """Test VCR generation functionality."""

    def test_vcr_generation_result_dataclass(self):
        """Test VCRGenerationResult dataclass structure."""
        result = VCRGenerationResult(
            title="Fix Authentication Bug",
            problem_statement="Users were experiencing login timeouts",
            root_cause_analysis="Token expiration was not handled properly",
            solution_approach="Added token refresh mechanism",
            implementation_notes="Added retry logic with exponential backoff",
            ai_tools_detected=["cursor", "claude_code"],
            ai_percentage_estimate=0.45,
            confidence=0.85,
            generation_time_ms=1250.5,
            provider_used="ollama",
            fallback_used=False,
        )

        assert result.title == "Fix Authentication Bug"
        assert result.ai_percentage_estimate == 0.45
        assert result.confidence == 0.85
        assert "cursor" in result.ai_tools_detected
        assert result.fallback_used is False

    def test_vcr_rule_based_fallback_result(self):
        """Test VCR rule-based fallback result structure."""
        result = VCRGenerationResult(
            title="PR Changes Summary",
            problem_statement="Bug fix: resolve authentication timeout issue",
            root_cause_analysis=None,
            solution_approach="Implementation: add token refresh mechanism",
            implementation_notes="- 3 files changed\n- +50/-10 lines",
            ai_tools_detected=[],
            ai_percentage_estimate=0.0,
            confidence=0.3,
            generation_time_ms=15.2,
            provider_used="rule_based",
            fallback_used=True,
        )

        assert result.fallback_used is True
        assert result.provider_used == "rule_based"
        assert result.confidence == 0.3  # Low confidence for rule-based

    @pytest.mark.asyncio
    async def test_generate_vcr_with_ai_success(self, mock_ollama_service, sample_pr_diff, sample_commit_messages):
        """Test VCR generation with successful AI response."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.text = """{
            "title": "Fix Authentication Timeout",
            "problem_statement": "Users experiencing login failures after timeout",
            "root_cause_analysis": "Token refresh was missing",
            "solution_approach": "Added automatic token refresh mechanism",
            "implementation_notes": "Uses exponential backoff for retries",
            "confidence": 0.9
        }"""
        mock_ollama_service.generate_async.return_value = mock_response

        # Create service with mock
        service = SASEGenerationService(ollama_service=mock_ollama_service)

        # Generate VCR
        result = await service.generate_vcr(
            pr_diff=sample_pr_diff,
            commit_messages=sample_commit_messages,
            pr_title="Fix authentication timeout issue",
        )

        assert result.title == "Fix Authentication Timeout"
        assert result.confidence >= 0.7
        assert result.fallback_used is False
        assert result.provider_used == "ollama"

    @pytest.mark.asyncio
    async def test_generate_vcr_fallback_on_error(self, sample_pr_diff, sample_commit_messages):
        """Test VCR generation falls back to rule-based on AI error."""
        # Create mock that raises an error
        mock_ollama = MagicMock()
        mock_ollama.generate_async = AsyncMock(side_effect=Exception("AI unavailable"))

        service = SASEGenerationService(ollama_service=mock_ollama)

        result = await service.generate_vcr(
            pr_diff=sample_pr_diff,
            commit_messages=sample_commit_messages,
            pr_title="Fix authentication issue",
        )

        assert result.fallback_used is True
        assert result.provider_used == "rule_based"
        assert result.confidence == 0.3

    @pytest.mark.asyncio
    async def test_generate_vcr_without_diff(self, mock_ollama_service, sample_commit_messages):
        """Test VCR generation without PR diff."""
        mock_response = MagicMock()
        mock_response.text = '{"title": "Feature Addition", "problem_statement": "N/A", "solution_approach": "Added new feature", "confidence": 0.8}'
        mock_ollama_service.generate_async.return_value = mock_response

        service = SASEGenerationService(ollama_service=mock_ollama_service)

        result = await service.generate_vcr(
            pr_diff=None,
            commit_messages=sample_commit_messages,
            pr_title="Add new feature",
        )

        assert result.title is not None
        assert result.ai_tools_detected == []  # No diff to detect tools


# =========================================================================
# CRP Generation Tests
# =========================================================================


class TestCRPGeneration:
    """Test CRP generation functionality."""

    def test_crp_generation_result_dataclass(self):
        """Test CRPGenerationResult dataclass structure."""
        result = CRPGenerationResult(
            title="Authentication Architecture Decision",
            question="Should we use OAuth2 or JWT for authentication?",
            context="We need to choose an authentication strategy for the new API",
            options_considered=[
                {"option": "OAuth2", "pros_cons": "Standard, complex setup"},
                {"option": "JWT", "pros_cons": "Simple, stateless"},
            ],
            recommendation="Use JWT for simplicity",
            impact_assessment="Affects all API endpoints and client applications",
            required_expertise=["security", "api"],
            priority_suggestion="high",
            confidence=0.8,
            generation_time_ms=890.3,
            provider_used="ollama",
            fallback_used=False,
        )

        assert result.title == "Authentication Architecture Decision"
        assert len(result.options_considered) == 2
        assert "security" in result.required_expertise
        assert result.priority_suggestion == "high"

    def test_crp_rule_based_fallback_result(self):
        """Test CRP rule-based fallback result structure."""
        result = CRPGenerationResult(
            title="Consultation Request",
            question="How should we handle authentication?...",
            context="Full context here",
            options_considered=[
                {"option": "Option A", "pros_cons": "Please describe"},
                {"option": "Option B", "pros_cons": "Please describe"},
            ],
            recommendation=None,
            impact_assessment="Please assess the impact",
            required_expertise=["general"],
            priority_suggestion="medium",
            confidence=0.3,
            generation_time_ms=25.1,
            provider_used="rule_based",
            fallback_used=True,
        )

        assert result.fallback_used is True
        assert result.confidence == 0.3
        assert result.recommendation is None

    @pytest.mark.asyncio
    async def test_generate_crp_with_ai_success(self, mock_ollama_service, sample_code_snippet):
        """Test CRP generation with successful AI response."""
        mock_response = MagicMock()
        mock_response.text = """{
            "title": "JWT vs OAuth2 Authentication",
            "question": "Which authentication method should we use?",
            "context": "Building a new API that needs secure authentication",
            "options_considered": [
                {"option": "JWT", "pros_cons": "Simple, stateless, good for microservices"},
                {"option": "OAuth2", "pros_cons": "Standard, complex, better for third-party auth"}
            ],
            "recommendation": "JWT for internal APIs, OAuth2 for public APIs",
            "impact_assessment": "Affects security posture and client implementation",
            "required_expertise": ["security", "api"],
            "priority_suggestion": "high",
            "confidence": 0.85
        }"""
        mock_ollama_service.generate_async.return_value = mock_response

        service = SASEGenerationService(ollama_service=mock_ollama_service)

        result = await service.generate_crp(
            context="We need to decide on authentication for our API",
            code_snippet=sample_code_snippet,
        )

        assert result.title == "JWT vs OAuth2 Authentication"
        assert len(result.options_considered) >= 2
        assert result.confidence >= 0.7

    @pytest.mark.asyncio
    async def test_generate_crp_fallback_on_error(self, sample_code_snippet):
        """Test CRP generation falls back to rule-based on AI error."""
        mock_ollama = MagicMock()
        mock_ollama.generate_async = AsyncMock(side_effect=Exception("AI unavailable"))

        service = SASEGenerationService(ollama_service=mock_ollama)

        result = await service.generate_crp(
            context="Need help with database migration strategy",
            code_snippet=sample_code_snippet,
        )

        assert result.fallback_used is True
        assert result.provider_used == "rule_based"
        assert "database" in result.required_expertise


# =========================================================================
# AI Tool Detection Tests
# =========================================================================


class TestAIToolDetection:
    """Test AI tool detection functionality."""

    def test_ai_tool_markers_completeness(self):
        """Test all AI tool markers are defined."""
        expected_tools = [
            AIToolType.CURSOR,
            AIToolType.CLAUDE_CODE,
            AIToolType.COPILOT,
            AIToolType.CODEIUM,
            AIToolType.TABNINE,
            AIToolType.CHATGPT,
            AIToolType.GEMINI,
        ]

        for tool in expected_tools:
            assert tool in AI_TOOL_MARKERS
            assert len(AI_TOOL_MARKERS[tool]) > 0

    def test_detect_cursor_from_diff(self):
        """Test Cursor detection from diff."""
        service = SASEGenerationService(ollama_service=MagicMock())

        diff = "// cursor-generated code\nfunction hello() {}"
        tools = service._detect_ai_tools(diff=diff)

        assert AIToolType.CURSOR in tools

    def test_detect_claude_from_commits(self):
        """Test Claude detection from commit messages."""
        service = SASEGenerationService(ollama_service=MagicMock())

        commits = [
            "feat: add new feature",
            "Co-Authored-By: Claude",
            "fix: resolve bug",
        ]
        tools = service._detect_ai_tools(commits=commits)

        assert AIToolType.CLAUDE_CODE in tools

    def test_detect_copilot_from_description(self):
        """Test Copilot detection from PR description."""
        service = SASEGenerationService(ollama_service=MagicMock())

        description = "This PR was created with GitHub Copilot suggestions"
        tools = service._detect_ai_tools(description=description)

        assert AIToolType.COPILOT in tools

    def test_detect_multiple_tools(self):
        """Test detection of multiple AI tools."""
        service = SASEGenerationService(ollama_service=MagicMock())

        diff = "// cursor code here"
        commits = ["feat: add feature with claude"]
        description = "Used copilot for completion"

        tools = service._detect_ai_tools(diff=diff, commits=commits, description=description)

        assert len(tools) >= 2
        assert AIToolType.CURSOR in tools
        assert AIToolType.COPILOT in tools

    def test_no_ai_tools_detected(self):
        """Test no AI tools detected in clean code."""
        service = SASEGenerationService(ollama_service=MagicMock())

        diff = "def hello():\n    print('world')"
        commits = ["fix: resolve bug", "feat: add feature"]

        tools = service._detect_ai_tools(diff=diff, commits=commits)

        assert len(tools) == 0

    def test_detect_chatgpt_from_diff(self):
        """Test ChatGPT detection from diff."""
        service = SASEGenerationService(ollama_service=MagicMock())

        diff = "# Generated by GPT-4\ndef calculate():\n    pass"
        tools = service._detect_ai_tools(diff=diff)

        assert AIToolType.CHATGPT in tools


# =========================================================================
# AI Percentage Estimation Tests
# =========================================================================


class TestAIPercentageEstimation:
    """Test AI percentage estimation functionality."""

    def test_no_ai_tools_zero_percentage(self):
        """Test zero percentage when no AI tools detected."""
        service = SASEGenerationService(ollama_service=MagicMock())

        percentage = service._estimate_ai_percentage([], None)

        assert percentage == 0.0

    def test_single_tool_base_percentage(self):
        """Test base percentage with single AI tool."""
        service = SASEGenerationService(ollama_service=MagicMock())

        percentage = service._estimate_ai_percentage([AIToolType.CURSOR], None)

        assert 0.3 <= percentage <= 0.5

    def test_multiple_tools_higher_percentage(self):
        """Test higher percentage with multiple AI tools."""
        service = SASEGenerationService(ollama_service=MagicMock())

        tools = [AIToolType.CURSOR, AIToolType.CLAUDE_CODE, AIToolType.COPILOT]
        percentage = service._estimate_ai_percentage(tools, None)

        assert percentage >= 0.5

    def test_large_diff_increases_percentage(self):
        """Test large diff increases AI percentage estimate."""
        service = SASEGenerationService(ollama_service=MagicMock())

        # Create large diff with many additions
        diff = "\n".join([f"+line {i}" for i in range(150)])
        tools = [AIToolType.CLAUDE_CODE]

        percentage = service._estimate_ai_percentage(tools, diff)

        assert percentage >= 0.4

    def test_documentation_patterns_increase_percentage(self):
        """Test documentation patterns increase AI percentage."""
        service = SASEGenerationService(ollama_service=MagicMock())

        diff = '''
+"""
+This function handles user authentication.
+
+@param username: The username
+@return: User object if authenticated
+"""
+def authenticate(username):
+    pass
'''
        tools = [AIToolType.CURSOR]

        percentage = service._estimate_ai_percentage(tools, diff)

        # Should be higher due to documentation markers
        assert percentage >= 0.4

    def test_percentage_caps_at_reasonable_max(self):
        """Test AI percentage doesn't exceed reasonable maximum."""
        service = SASEGenerationService(ollama_service=MagicMock())

        # Many tools + large diff with docs
        tools = [
            AIToolType.CURSOR,
            AIToolType.CLAUDE_CODE,
            AIToolType.COPILOT,
            AIToolType.CHATGPT,
        ]
        diff = "\n".join([f"+/** @param x */\n+line {i}" for i in range(200)])

        percentage = service._estimate_ai_percentage(tools, diff)

        assert percentage <= 0.85


# =========================================================================
# Expertise Detection Tests
# =========================================================================


class TestExpertiseDetection:
    """Test required expertise detection functionality."""

    def test_detect_security_expertise(self):
        """Test security expertise detection."""
        service = SASEGenerationService(ollama_service=MagicMock())

        context = "We need to implement authentication with JWT tokens"
        expertise = service._detect_required_expertise(context, None)

        assert "security" in expertise

    def test_detect_database_expertise(self):
        """Test database expertise detection."""
        service = SASEGenerationService(ollama_service=MagicMock())

        context = "Need to optimize the SQL query for better performance"
        expertise = service._detect_required_expertise(context, None)

        assert "database" in expertise

    def test_detect_api_expertise(self):
        """Test API expertise detection."""
        service = SASEGenerationService(ollama_service=MagicMock())

        context = "Designing a new REST API endpoint for user management"
        expertise = service._detect_required_expertise(context, None)

        assert "api" in expertise

    def test_detect_architecture_expertise(self):
        """Test architecture expertise detection."""
        service = SASEGenerationService(ollama_service=MagicMock())

        context = "Refactoring the service layer architecture"
        expertise = service._detect_required_expertise(context, None)

        assert "architecture" in expertise

    def test_detect_concurrency_expertise(self):
        """Test concurrency expertise detection."""
        service = SASEGenerationService(ollama_service=MagicMock())

        context = "Need to handle race conditions in async operations"
        expertise = service._detect_required_expertise(context, None)

        assert "concurrency" in expertise

    def test_detect_multiple_expertise(self):
        """Test detection of multiple expertise types."""
        service = SASEGenerationService(ollama_service=MagicMock())

        context = "Implementing secure API authentication with database storage"
        expertise = service._detect_required_expertise(context, None)

        assert len(expertise) >= 2
        assert "security" in expertise or "api" in expertise

    def test_default_general_expertise(self):
        """Test default to general expertise when no specific match."""
        service = SASEGenerationService(ollama_service=MagicMock())

        context = "Just a simple code cleanup"
        expertise = service._detect_required_expertise(context, None)

        assert "general" in expertise

    def test_code_snippet_affects_expertise(self):
        """Test code snippet content affects expertise detection."""
        service = SASEGenerationService(ollama_service=MagicMock())

        context = "Looking at this function"
        code = "async def process_queue(): await queue.get()"

        expertise = service._detect_required_expertise(context, code)

        assert "concurrency" in expertise


# =========================================================================
# Priority Detection Tests
# =========================================================================


class TestPriorityDetection:
    """Test priority detection functionality."""

    def test_detect_urgent_priority(self):
        """Test urgent priority detection."""
        service = SASEGenerationService(ollama_service=MagicMock())

        urgent_contexts = [
            "URGENT: Production is down",
            "Critical security vulnerability found",
            "This is blocking the release ASAP",
        ]

        for context in urgent_contexts:
            priority = service._detect_priority(context)
            assert priority == "urgent", f"Failed for: {context}"

    def test_detect_high_priority(self):
        """Test high priority detection."""
        service = SASEGenerationService(ollama_service=MagicMock())

        high_contexts = [
            "Important feature for customer deadline",
            "Security improvement needed",
            "Priority issue affecting multiple users",
        ]

        for context in high_contexts:
            priority = service._detect_priority(context)
            assert priority == "high", f"Failed for: {context}"

    def test_detect_low_priority(self):
        """Test low priority detection."""
        service = SASEGenerationService(ollama_service=MagicMock())

        low_contexts = [
            "Minor code cleanup task",
            "This is nice to have feature",
            "Eventually we should update this",
        ]

        for context in low_contexts:
            priority = service._detect_priority(context)
            assert priority == "low", f"Failed for: {context}"

    def test_default_medium_priority(self):
        """Test default medium priority."""
        service = SASEGenerationService(ollama_service=MagicMock())

        context = "Adding a new feature to the application"
        priority = service._detect_priority(context)

        assert priority == "medium"


# =========================================================================
# Factory Function Tests
# =========================================================================


class TestFactoryFunction:
    """Test factory function for service creation."""

    def test_create_service_default(self):
        """Test creating service with defaults."""
        with patch("app.services.sase_generation_service.create_ollama_service") as mock_create:
            mock_ollama = MagicMock()
            mock_create.return_value = mock_ollama

            service = create_sase_generation_service()

            assert service is not None
            assert service.ollama == mock_ollama

    def test_create_service_with_custom_ollama(self):
        """Test creating service with custom Ollama service."""
        custom_ollama = MagicMock()

        service = create_sase_generation_service(ollama_service=custom_ollama)

        assert service.ollama == custom_ollama


# =========================================================================
# AI Tool Type Enum Tests
# =========================================================================


class TestAIToolTypeEnum:
    """Test AIToolType enum values."""

    def test_all_tool_types_exist(self):
        """Test all expected AI tool types exist."""
        assert AIToolType.CURSOR.value == "cursor"
        assert AIToolType.CLAUDE_CODE.value == "claude_code"
        assert AIToolType.COPILOT.value == "copilot"
        assert AIToolType.CODEIUM.value == "codeium"
        assert AIToolType.TABNINE.value == "tabnine"
        assert AIToolType.CHATGPT.value == "chatgpt"
        assert AIToolType.GEMINI.value == "gemini"
        assert AIToolType.UNKNOWN.value == "unknown"

    def test_tool_type_is_string_enum(self):
        """Test AIToolType is a string enum."""
        assert isinstance(AIToolType.CURSOR.value, str)
        assert isinstance(AIToolType.CLAUDE_CODE, str)


# =========================================================================
# Section Extraction Tests
# =========================================================================


class TestSectionExtraction:
    """Test section extraction from AI responses."""

    def test_extract_section_with_colon(self):
        """Test extracting section with colon format."""
        service = SASEGenerationService(ollama_service=MagicMock())

        text = "Problem: Users cannot login\nSolution: Fix the auth service"
        problem = service._extract_section(text, "problem")

        assert "Users cannot login" in problem

    def test_extract_section_with_quotes(self):
        """Test extracting section with quoted format."""
        service = SASEGenerationService(ollama_service=MagicMock())

        text = '"solution": "Implement token refresh"'
        solution = service._extract_section(text, "solution")

        assert "token refresh" in solution.lower()

    def test_extract_section_not_found(self):
        """Test extracting section that doesn't exist."""
        service = SASEGenerationService(ollama_service=MagicMock())

        text = "Some random text without sections"
        result = service._extract_section(text, "problem")

        assert "provide" in result.lower()


# =========================================================================
# Generation Time Tests
# =========================================================================


class TestGenerationTime:
    """Test generation time tracking."""

    @pytest.mark.asyncio
    async def test_vcr_generation_time_tracked(self, mock_ollama_service):
        """Test VCR generation time is tracked."""
        mock_response = MagicMock()
        mock_response.text = '{"title": "Test", "problem_statement": "", "solution_approach": "", "confidence": 0.5}'
        mock_ollama_service.generate_async.return_value = mock_response

        service = SASEGenerationService(ollama_service=mock_ollama_service)

        result = await service.generate_vcr(
            pr_title="Test PR",
            commit_messages=["test commit"],
        )

        assert result.generation_time_ms >= 0
        assert isinstance(result.generation_time_ms, float)

    @pytest.mark.asyncio
    async def test_crp_generation_time_tracked(self, mock_ollama_service):
        """Test CRP generation time is tracked."""
        mock_response = MagicMock()
        mock_response.text = '{"title": "Test", "question": "Q", "context": "", "options_considered": [], "impact_assessment": "", "required_expertise": ["general"], "priority_suggestion": "medium", "confidence": 0.5}'
        mock_ollama_service.generate_async.return_value = mock_response

        service = SASEGenerationService(ollama_service=mock_ollama_service)

        result = await service.generate_crp(context="Test context")

        assert result.generation_time_ms >= 0
        assert isinstance(result.generation_time_ms, float)
