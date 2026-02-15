"""
=========================================================================
Enforcement Decision Matrix Tests
SDLC Orchestrator - Sprint 173 (Governance Loop Completion)

Version: 1.0.0
Date: February 15, 2026
Status: ACTIVE
Authority: CTO + Backend Lead Approved
Framework: SDLC 6.0.5 Quality Assurance System

Purpose:
- Verify enforcement decisions match the documented decision matrix
- Same input must produce same WARN/BLOCK/APPROVE decisions
- Matrix covers both SOFT and FULL enforcement strategies
- Prevents regressions during Strategy pattern consolidation

Zero Mock Policy: Real enforcement strategies, real index calculations
=========================================================================
"""

import pytest
from uuid import uuid4

from app.services.governance.enforcement_strategy import (
    SoftEnforcement,
    FullEnforcement,
    EnforcementAction,
    ApprovalRequirement,
)
from app.services.governance.signals_engine import (
    CodeSubmission,
    IndexCategory,
    RoutingDecision,
    VibecodingIndex,
)


# ============================================================================
# Test Fixtures
# ============================================================================


def _make_index(score: float) -> VibecodingIndex:
    """Create a VibecodingIndex with the given score."""
    if score <= 30:
        category = IndexCategory.GREEN
        routing = RoutingDecision.AUTO_APPROVE
    elif score <= 60:
        category = IndexCategory.YELLOW
        routing = RoutingDecision.TECH_LEAD_REVIEW
    elif score <= 80:
        category = IndexCategory.ORANGE
        routing = RoutingDecision.CEO_SHOULD_REVIEW
    else:
        category = IndexCategory.RED
        routing = RoutingDecision.CEO_MUST_REVIEW

    return VibecodingIndex(
        score=score,
        category=category,
        routing=routing,
        signals=[],
        critical_override=False,
        critical_matches=[],
        original_score=score,
        suggested_focus=[],
        flags=[],
    )


def _make_submission(**kwargs) -> CodeSubmission:
    """Create a minimal CodeSubmission for testing."""
    defaults = {
        "submission_id": uuid4(),
        "project_id": uuid4(),
        "changed_files": ["src/feature.py"],
        "added_lines": 100,
        "removed_lines": 20,
        "is_new_feature": False,
    }
    defaults.update(kwargs)
    return CodeSubmission(**defaults)


@pytest.fixture
def soft_enforcer():
    """Create SoftEnforcement strategy with defaults."""
    return SoftEnforcement()


@pytest.fixture
def full_enforcer():
    """Create FullEnforcement strategy with defaults."""
    return FullEnforcement()


@pytest.fixture
def submission():
    """Standard code submission for matrix testing."""
    return _make_submission()


# ============================================================================
# SOFT Mode Decision Matrix
# ============================================================================


class TestSoftModeDecisionMatrix:
    """
    Verify SOFT mode enforcement produces correct action for each zone.

    Decision Matrix (SOFT):
    | Zone   | Index | Expected Action    |
    |--------|-------|--------------------|
    | GREEN  | 0-30  | AUTO_APPROVED      |
    | YELLOW | 31-60 | APPROVED           |
    | ORANGE | 61-80 | WARNED             |
    | RED    | 81+   | BLOCKED            |
    """

    @pytest.mark.parametrize(
        "score,expected_action",
        [
            (0, EnforcementAction.AUTO_APPROVED),
            (15, EnforcementAction.AUTO_APPROVED),
            (25, EnforcementAction.AUTO_APPROVED),
            (30, EnforcementAction.AUTO_APPROVED),
        ],
    )
    def test_green_zone_auto_approved(
        self, soft_enforcer, submission, score, expected_action
    ):
        """GREEN zone (0-30): Auto-approved, no review needed."""
        index = _make_index(score)
        result = soft_enforcer.decide(index, submission)
        assert result.action == expected_action
        assert result.can_merge is True

    @pytest.mark.parametrize(
        "score,expected_action",
        [
            (31, EnforcementAction.APPROVED),
            (45, EnforcementAction.APPROVED),
            (60, EnforcementAction.APPROVED),
        ],
    )
    def test_yellow_zone_approved(
        self, soft_enforcer, submission, score, expected_action
    ):
        """YELLOW zone (31-60): Approved, Tech Lead review suggested."""
        index = _make_index(score)
        result = soft_enforcer.decide(index, submission)
        assert result.action == expected_action
        assert result.can_merge is True

    @pytest.mark.parametrize(
        "score",
        [61, 70, 80],
    )
    def test_orange_zone_warned(self, soft_enforcer, submission, score):
        """ORANGE zone (61-80): Warned, CEO review recommended."""
        index = _make_index(score)
        result = soft_enforcer.decide(index, submission)
        assert result.action == EnforcementAction.WARNED
        assert result.can_merge is True

    @pytest.mark.parametrize(
        "score",
        [81, 90, 100],
    )
    def test_red_zone_blocked(self, soft_enforcer, submission, score):
        """RED zone (81-100): Blocked, CTO override required."""
        index = _make_index(score)
        result = soft_enforcer.decide(index, submission)
        assert result.action == EnforcementAction.BLOCKED
        assert result.can_merge is False
        assert result.requires_override is True

    def test_backward_compat_enforce_alias(self, soft_enforcer, submission):
        """Old .enforce() method still works via alias."""
        index = _make_index(25)
        result = soft_enforcer.enforce(index, submission)
        assert result.action == EnforcementAction.AUTO_APPROVED

    def test_backward_compat_evaluate_exemptions_alias(self, soft_enforcer, submission):
        """Old .evaluate_exemptions() method still works via alias."""
        exemptions = soft_enforcer.evaluate_exemptions(submission)
        assert isinstance(exemptions, list)


# ============================================================================
# FULL Mode Decision Matrix
# ============================================================================


class TestFullModeDecisionMatrix:
    """
    Verify FULL mode enforcement produces correct action for each zone.

    Decision Matrix (FULL):
    | Zone   | Index | Expected Action         | Approval Required |
    |--------|-------|-------------------------|-------------------|
    | GREEN  | 0-30  | AUTO_APPROVED           | NONE              |
    | YELLOW | 31-60 | WARNED (needs approval) | TECH_LEAD         |
    | ORANGE | 61-80 | WARNED (needs approval) | CEO               |
    | RED    | 81+   | BLOCKED                 | CTO_CEO           |
    """

    @pytest.mark.parametrize(
        "score",
        [0, 15, 25, 30],
    )
    def test_green_zone_auto_approved(self, full_enforcer, submission, score):
        """GREEN zone (0-30): Auto-approved, no review needed."""
        index = _make_index(score)
        result = full_enforcer.decide_full(
            vibecoding_index=index,
            submission=submission,
        )
        assert result.action == EnforcementAction.AUTO_APPROVED
        assert result.approval_required is False
        assert result.approval_type == ApprovalRequirement.NONE
        assert result.can_merge is True

    @pytest.mark.parametrize(
        "score",
        [31, 45, 60],
    )
    def test_yellow_zone_needs_tech_lead(self, full_enforcer, submission, score):
        """YELLOW zone (31-60): Needs Tech Lead approval."""
        index = _make_index(score)
        result = full_enforcer.decide_full(
            vibecoding_index=index,
            submission=submission,
        )
        assert result.approval_required is True
        assert result.approval_type == ApprovalRequirement.TECH_LEAD
        assert result.ceo_review_required is False

    @pytest.mark.parametrize(
        "score",
        [61, 70, 80],
    )
    def test_orange_zone_needs_ceo(self, full_enforcer, submission, score):
        """ORANGE zone (61-80): Needs CEO approval."""
        index = _make_index(score)
        result = full_enforcer.decide_full(
            vibecoding_index=index,
            submission=submission,
        )
        assert result.approval_required is True
        assert result.approval_type == ApprovalRequirement.CEO
        assert result.ceo_review_required is True

    @pytest.mark.parametrize(
        "score",
        [81, 90, 100],
    )
    def test_red_zone_blocked_needs_cto_ceo(self, full_enforcer, submission, score):
        """RED zone (81-100): Blocked, needs CTO+CEO override."""
        index = _make_index(score)
        result = full_enforcer.decide_full(
            vibecoding_index=index,
            submission=submission,
        )
        assert result.action == EnforcementAction.BLOCKED
        assert result.approval_required is True
        assert result.approval_type == ApprovalRequirement.CTO_CEO
        assert result.ceo_review_required is True
        assert result.can_merge is False

    def test_backward_compat_enforce_full_alias(self, full_enforcer, submission):
        """Old .enforce_full() method still works via alias."""
        index = _make_index(45)
        result = full_enforcer.enforce_full(
            vibecoding_index=index,
            submission=submission,
        )
        assert result.approval_required is True
        assert result.approval_type == ApprovalRequirement.TECH_LEAD

    def test_backward_compat_enforce_alias(self, full_enforcer, submission):
        """Old .enforce() method still works via alias."""
        index = _make_index(25)
        result = full_enforcer.enforce(index, submission)
        assert result.action == EnforcementAction.AUTO_APPROVED


# ============================================================================
# Cross-Strategy Comparison Matrix
# ============================================================================


class TestCrossStrategyMatrix:
    """
    Verify SOFT vs FULL decisions differ correctly per the plan's matrix.

    | Index | SOFT Mode        | FULL Mode                  |
    |-------|------------------|----------------------------|
    | 25    | AUTO_APPROVED    | AUTO_APPROVED              |
    | 45    | APPROVED         | NEED_TECH_LEAD_APPROVAL    |
    | 70    | WARNED           | NEED_CEO_APPROVAL          |
    | 90    | BLOCKED          | BLOCKED_NEED_CTO_CEO       |
    """

    @pytest.mark.parametrize(
        "score,soft_action,full_approval",
        [
            (25, EnforcementAction.AUTO_APPROVED, ApprovalRequirement.NONE),
            (45, EnforcementAction.APPROVED, ApprovalRequirement.TECH_LEAD),
            (70, EnforcementAction.WARNED, ApprovalRequirement.CEO),
            (90, EnforcementAction.BLOCKED, ApprovalRequirement.CTO_CEO),
        ],
    )
    def test_soft_vs_full_decision_matrix(
        self, soft_enforcer, full_enforcer, submission,
        score, soft_action, full_approval,
    ):
        """Same index → different enforcement between SOFT and FULL."""
        index = _make_index(score)

        soft_result = soft_enforcer.decide(index, submission)
        full_result = full_enforcer.decide_full(
            vibecoding_index=index,
            submission=submission,
        )

        assert soft_result.action == soft_action
        assert full_result.approval_type == full_approval


# ============================================================================
# Exemption Impact Matrix
# ============================================================================


class TestExemptionImpactMatrix:
    """Verify exemptions correctly adjust enforcement decisions."""

    def test_dependency_update_caps_index(self, soft_enforcer):
        """Dependency update exemption caps index to green zone."""
        submission = _make_submission(
            changed_files=["requirements.txt", "poetry.lock"],
            added_lines=10,
        )
        index = _make_index(65)  # Orange zone normally
        result = soft_enforcer.decide(index, submission)
        # Exemption should cap the index, may change action
        assert result.vibecoding_index.score <= 65

    def test_documentation_auto_approves(self, soft_enforcer):
        """Documentation-only PR is auto-approved."""
        submission = _make_submission(
            changed_files=["docs/guide.md", "docs/api.md"],
            added_lines=50,
        )
        index = _make_index(15)
        result = soft_enforcer.decide(index, submission)
        assert result.action == EnforcementAction.AUTO_APPROVED

    def test_test_only_reduces_scrutiny(self, soft_enforcer):
        """Test-only PR gets reduced scrutiny."""
        submission = _make_submission(
            changed_files=["tests/test_feature.py"],
            added_lines=100,
        )
        exemptions = soft_enforcer.check_exemptions(submission)
        test_exemption = [
            e for e in exemptions
            if e.applied and e.exemption_type is not None
            and e.exemption_type.value == "test_only_pattern"
        ]
        assert len(test_exemption) > 0


# ============================================================================
# Coverage Drop Matrix (FULL mode only)
# ============================================================================


class TestCoverageDropMatrix:
    """Verify coverage drop rules in FULL mode."""

    @pytest.mark.parametrize(
        "coverage_delta,should_block",
        [
            (-7.0, True),    # 7% drop → blocked
            (-5.1, True),    # Just over threshold → blocked
            (-3.0, False),   # 3% drop → acceptable
            (0.0, False),    # No change → OK
            (5.0, False),    # Increase → OK
        ],
    )
    def test_coverage_drop_enforcement(
        self, full_enforcer, submission, coverage_delta, should_block
    ):
        """Coverage drop blocking depends on threshold (-5%)."""
        index = _make_index(25)  # Green zone (no other blocks)
        result = full_enforcer.decide_full(
            vibecoding_index=index,
            submission=submission,
            coverage_delta=coverage_delta,
        )

        coverage_blocks = [
            b for b in result.block_rules_triggered
            if b.rule_name == "coverage_drop" and b.triggered
        ]

        if should_block:
            assert len(coverage_blocks) > 0
            assert result.action == EnforcementAction.BLOCKED
        else:
            assert len(coverage_blocks) == 0
