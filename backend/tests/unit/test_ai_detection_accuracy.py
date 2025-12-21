"""
AI Detection Accuracy Validation Tests - Sprint 42 Day 5

SDLC Stage: 04 - BUILD
Sprint: 42 - AI Detection & Validation Pipeline
Framework: SDLC 5.1.1
Day: 5 - Test Dataset Validation

Purpose:
Validate AI detection accuracy against 110-PR test dataset.
Target: ≥85% accuracy on true AI PRs, <20% false positive rate.

CTO P0 Fix: Added adversarial test cases for false positive protection.

Test Structure:
1. Overall accuracy validation
2. Per-category accuracy (Cursor, Copilot, Claude, etc.)
3. Confusion matrix analysis
4. False positive/negative analysis
5. Adversarial test validation (false positive protection)
6. Performance validation (<600ms p95)

Coverage Target: 95%+
"""

import asyncio
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional

import pytest

from app.services.ai_detection import AIToolType
from app.services.ai_detection.service import GitHubAIDetectionService
from tests.fixtures.ai_detection_test_dataset import (
    ADVERSARIAL_PRS,
    ALL_TEST_PRS,
    CHATGPT_PRS,
    CLAUDE_PRS,
    COPILOT_PRS,
    CURSOR_PRS,
    DATASET_SUMMARY,
    HUMAN_PRS,
    OTHER_AI_PRS,
    TestPR,
    WINDSURF_PRS,
)


# ============================================================================
# Result Tracking
# ============================================================================


@dataclass
class DetectionTestResult:
    """Result of a single detection test."""

    pr_id: str
    category: str
    expected_detected: bool
    expected_tool: Optional[AIToolType]
    actual_detected: bool
    actual_tool: Optional[AIToolType]
    confidence: float
    duration_ms: int
    correct_detection: bool
    correct_tool: bool


@dataclass
class AccuracyReport:
    """Summary of accuracy validation results."""

    total_tests: int
    correct_detections: int
    incorrect_detections: int
    detection_accuracy: float
    true_positives: int  # AI detected as AI
    true_negatives: int  # Human detected as Human
    false_positives: int  # Human detected as AI
    false_negatives: int  # AI detected as Human
    precision: float  # TP / (TP + FP)
    recall: float  # TP / (TP + FN)
    f1_score: float  # 2 * (precision * recall) / (precision + recall)
    per_category_accuracy: Dict[str, float]
    avg_duration_ms: float
    p95_duration_ms: float
    results: List[DetectionTestResult]


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def detection_service():
    """Create AI detection service instance."""
    return GitHubAIDetectionService()


@pytest.fixture
def all_test_prs():
    """Get all test PRs."""
    return ALL_TEST_PRS


# ============================================================================
# Helper Functions
# ============================================================================


async def run_detection_test(
    service: GitHubAIDetectionService, pr: TestPR
) -> DetectionTestResult:
    """
    Run detection on a single test PR and return results.

    Args:
        service: AI detection service
        pr: Test PR data

    Returns:
        DetectionTestResult with comparison
    """
    # Prepare PR data
    pr_data = {"title": pr.title, "body": pr.body}

    # Run detection
    result = await service.detect(pr_data, pr.commits, pr.diff)

    # Compare results
    correct_detection = result.is_ai_generated == pr.expected_detected
    correct_tool = (
        result.detected_tool == pr.expected_tool if pr.expected_detected else True
    )

    return DetectionTestResult(
        pr_id=pr.id,
        category=pr.category,
        expected_detected=pr.expected_detected,
        expected_tool=pr.expected_tool,
        actual_detected=result.is_ai_generated,
        actual_tool=result.detected_tool,
        confidence=result.confidence,
        duration_ms=result.detection_duration_ms,
        correct_detection=correct_detection,
        correct_tool=correct_tool,
    )


def calculate_accuracy_report(results: List[DetectionTestResult]) -> AccuracyReport:
    """
    Calculate comprehensive accuracy report from test results.

    Args:
        results: List of detection test results

    Returns:
        AccuracyReport with all metrics
    """
    total = len(results)
    correct = sum(1 for r in results if r.correct_detection)
    incorrect = total - correct

    # Binary classification metrics
    tp = sum(1 for r in results if r.expected_detected and r.actual_detected)
    tn = sum(1 for r in results if not r.expected_detected and not r.actual_detected)
    fp = sum(1 for r in results if not r.expected_detected and r.actual_detected)
    fn = sum(1 for r in results if r.expected_detected and not r.actual_detected)

    # Precision, Recall, F1
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (
        2 * (precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    # Per-category accuracy
    category_results: Dict[str, List[DetectionTestResult]] = defaultdict(list)
    for r in results:
        category_results[r.category].append(r)

    per_category_accuracy = {}
    for category, cat_results in category_results.items():
        cat_correct = sum(1 for r in cat_results if r.correct_detection)
        per_category_accuracy[category] = cat_correct / len(cat_results)

    # Duration stats
    durations = [r.duration_ms for r in results]
    avg_duration = sum(durations) / len(durations) if durations else 0.0
    sorted_durations = sorted(durations)
    p95_index = int(len(sorted_durations) * 0.95)
    p95_duration = sorted_durations[p95_index] if sorted_durations else 0.0

    return AccuracyReport(
        total_tests=total,
        correct_detections=correct,
        incorrect_detections=incorrect,
        detection_accuracy=correct / total if total > 0 else 0.0,
        true_positives=tp,
        true_negatives=tn,
        false_positives=fp,
        false_negatives=fn,
        precision=precision,
        recall=recall,
        f1_score=f1,
        per_category_accuracy=per_category_accuracy,
        avg_duration_ms=avg_duration,
        p95_duration_ms=p95_duration,
        results=results,
    )


# ============================================================================
# Main Accuracy Validation Tests
# ============================================================================


@pytest.mark.asyncio
async def test_overall_accuracy_meets_target(detection_service, all_test_prs):
    """
    CRITICAL TEST: Validate ≥85% overall accuracy.

    This is the primary acceptance criterion for Sprint 42.
    Runs detection against all 100 test PRs and validates accuracy.
    """
    results = []

    for pr in all_test_prs:
        result = await run_detection_test(detection_service, pr)
        results.append(result)

    report = calculate_accuracy_report(results)

    # Print detailed report for debugging
    print(f"\n{'='*60}")
    print("AI DETECTION ACCURACY REPORT")
    print(f"{'='*60}")
    print(f"Total Tests: {report.total_tests}")
    print(f"Correct: {report.correct_detections}")
    print(f"Incorrect: {report.incorrect_detections}")
    print(f"Accuracy: {report.detection_accuracy:.1%}")
    print(f"\nConfusion Matrix:")
    print(f"  True Positives (AI→AI): {report.true_positives}")
    print(f"  True Negatives (Human→Human): {report.true_negatives}")
    print(f"  False Positives (Human→AI): {report.false_positives}")
    print(f"  False Negatives (AI→Human): {report.false_negatives}")
    print(f"\nClassification Metrics:")
    print(f"  Precision: {report.precision:.3f}")
    print(f"  Recall: {report.recall:.3f}")
    print(f"  F1 Score: {report.f1_score:.3f}")
    print(f"\nPer-Category Accuracy:")
    for category, accuracy in sorted(report.per_category_accuracy.items()):
        print(f"  {category}: {accuracy:.1%}")
    print(f"\nPerformance:")
    print(f"  Avg Duration: {report.avg_duration_ms:.1f}ms")
    print(f"  P95 Duration: {report.p95_duration_ms:.1f}ms")

    # List failures for debugging
    failures = [r for r in results if not r.correct_detection]
    if failures:
        print(f"\nMisclassified PRs ({len(failures)}):")
        for f in failures[:10]:  # Show first 10
            print(
                f"  {f.pr_id}: expected={f.expected_detected}, "
                f"actual={f.actual_detected} (conf={f.confidence:.2f})"
            )

    print(f"{'='*60}\n")

    # CRITICAL ASSERTION: ≥85% accuracy
    assert (
        report.detection_accuracy >= 0.85
    ), f"Accuracy {report.detection_accuracy:.1%} below 85% target"


@pytest.mark.asyncio
async def test_cursor_detection_accuracy(detection_service):
    """Test accuracy for Cursor-generated PRs."""
    results = []
    for pr in CURSOR_PRS:
        result = await run_detection_test(detection_service, pr)
        results.append(result)

    report = calculate_accuracy_report(results)

    print(f"\nCursor Detection: {report.detection_accuracy:.1%} ({report.correct_detections}/{report.total_tests})")

    # Cursor should have high detection rate (explicit patterns)
    assert report.detection_accuracy >= 0.80, f"Cursor accuracy {report.detection_accuracy:.1%} below 80%"


@pytest.mark.asyncio
async def test_copilot_detection_accuracy(detection_service):
    """Test accuracy for GitHub Copilot-generated PRs."""
    results = []
    for pr in COPILOT_PRS:
        result = await run_detection_test(detection_service, pr)
        results.append(result)

    report = calculate_accuracy_report(results)

    print(f"\nCopilot Detection: {report.detection_accuracy:.1%} ({report.correct_detections}/{report.total_tests})")

    # Copilot has strong patterns (co-authored-by, 🤖 emoji)
    assert report.detection_accuracy >= 0.80, f"Copilot accuracy {report.detection_accuracy:.1%} below 80%"


@pytest.mark.asyncio
async def test_claude_detection_accuracy(detection_service):
    """Test accuracy for Claude-generated PRs."""
    results = []
    for pr in CLAUDE_PRS:
        result = await run_detection_test(detection_service, pr)
        results.append(result)

    report = calculate_accuracy_report(results)

    print(f"\nClaude Detection: {report.detection_accuracy:.1%} ({report.correct_detections}/{report.total_tests})")

    # Claude has explicit patterns (Generated with Claude Code)
    assert report.detection_accuracy >= 0.80, f"Claude accuracy {report.detection_accuracy:.1%} below 80%"


@pytest.mark.asyncio
async def test_chatgpt_detection_accuracy(detection_service):
    """Test accuracy for ChatGPT-generated PRs."""
    results = []
    for pr in CHATGPT_PRS:
        result = await run_detection_test(detection_service, pr)
        results.append(result)

    report = calculate_accuracy_report(results)

    print(f"\nChatGPT Detection: {report.detection_accuracy:.1%} ({report.correct_detections}/{report.total_tests})")

    # ChatGPT has explicit patterns
    assert report.detection_accuracy >= 0.70, f"ChatGPT accuracy {report.detection_accuracy:.1%} below 70%"


@pytest.mark.asyncio
async def test_windsurf_detection_accuracy(detection_service):
    """Test accuracy for Windsurf-generated PRs."""
    results = []
    for pr in WINDSURF_PRS:
        result = await run_detection_test(detection_service, pr)
        results.append(result)

    report = calculate_accuracy_report(results)

    print(f"\nWindsurf Detection: {report.detection_accuracy:.1%} ({report.correct_detections}/{report.total_tests})")

    # Windsurf is newer, may have lower detection
    assert report.detection_accuracy >= 0.60, f"Windsurf accuracy {report.detection_accuracy:.1%} below 60%"


@pytest.mark.asyncio
async def test_other_ai_detection_accuracy(detection_service):
    """Test accuracy for other AI tools (Cody, Tabnine)."""
    results = []
    for pr in OTHER_AI_PRS:
        result = await run_detection_test(detection_service, pr)
        results.append(result)

    report = calculate_accuracy_report(results)

    print(f"\nOther AI Detection: {report.detection_accuracy:.1%} ({report.correct_detections}/{report.total_tests})")

    # Other tools should be detected at reasonable rate
    assert report.detection_accuracy >= 0.60, f"Other AI accuracy {report.detection_accuracy:.1%} below 60%"


@pytest.mark.asyncio
async def test_human_false_positive_rate(detection_service):
    """Test that human PRs are NOT falsely detected as AI."""
    results = []
    for pr in HUMAN_PRS:
        result = await run_detection_test(detection_service, pr)
        results.append(result)

    report = calculate_accuracy_report(results)

    # False positive rate
    false_positives = sum(1 for r in results if r.actual_detected)
    fp_rate = false_positives / len(results)

    print(f"\nHuman PRs: {report.detection_accuracy:.1%} correct ({false_positives} false positives)")
    print(f"False Positive Rate: {fp_rate:.1%}")

    # CRITICAL: Low false positive rate (<20%)
    assert fp_rate <= 0.20, f"False positive rate {fp_rate:.1%} exceeds 20% threshold"


@pytest.mark.asyncio
async def test_adversarial_false_positive_protection(detection_service):
    """
    CTO P0 CRITICAL TEST: Adversarial false positive protection.

    These PRs contain words like "cursor", "pilot", "claude" in non-AI contexts.
    They should NOT be detected as AI-generated.
    """
    results = []
    for pr in ADVERSARIAL_PRS:
        result = await run_detection_test(detection_service, pr)
        results.append(result)

    report = calculate_accuracy_report(results)

    # False positive rate on adversarial cases
    false_positives = sum(1 for r in results if r.actual_detected)
    fp_rate = false_positives / len(results)

    print(f"\n{'='*60}")
    print("ADVERSARIAL TEST - False Positive Protection")
    print(f"{'='*60}")
    print(f"Total Adversarial PRs: {len(results)}")
    print(f"False Positives: {false_positives}")
    print(f"False Positive Rate: {fp_rate:.1%}")

    # List any failures
    failures = [r for r in results if r.actual_detected]
    if failures:
        print(f"\nFalse Positive Details:")
        for f in failures:
            print(f"  {f.pr_id}: detected as {f.actual_tool} (conf={f.confidence:.2f})")

    print(f"{'='*60}\n")

    # CTO P0 CRITICAL: <30% false positive rate on adversarial cases
    # (these are harder cases than typical human PRs)
    assert fp_rate <= 0.30, f"Adversarial FP rate {fp_rate:.1%} exceeds 30% threshold"


# ============================================================================
# Performance Validation Tests
# ============================================================================


@pytest.mark.asyncio
async def test_detection_latency_p95(detection_service, all_test_prs):
    """Test that p95 latency is <600ms."""
    durations = []

    for pr in all_test_prs:
        pr_data = {"title": pr.title, "body": pr.body}
        result = await detection_service.detect(pr_data, pr.commits, pr.diff)
        durations.append(result.detection_duration_ms)

    sorted_durations = sorted(durations)
    p95_index = int(len(sorted_durations) * 0.95)
    p95_latency = sorted_durations[p95_index]
    avg_latency = sum(durations) / len(durations)

    print(f"\nLatency: avg={avg_latency:.1f}ms, p95={p95_latency:.1f}ms")

    # p95 should be <600ms
    assert p95_latency < 600, f"p95 latency {p95_latency}ms exceeds 600ms target"


@pytest.mark.asyncio
async def test_detection_latency_average(detection_service, all_test_prs):
    """Test that average latency is <100ms."""
    durations = []

    for pr in all_test_prs[:20]:  # Sample for speed
        pr_data = {"title": pr.title, "body": pr.body}
        result = await detection_service.detect(pr_data, pr.commits, pr.diff)
        durations.append(result.detection_duration_ms)

    avg_latency = sum(durations) / len(durations)

    print(f"\nAverage Latency: {avg_latency:.1f}ms")

    # Average should be <100ms
    assert avg_latency < 100, f"Average latency {avg_latency}ms exceeds 100ms target"


# ============================================================================
# Classification Metrics Tests
# ============================================================================


@pytest.mark.asyncio
async def test_precision_meets_target(detection_service, all_test_prs):
    """Test that precision (TP / (TP + FP)) is ≥80%."""
    results = []
    for pr in all_test_prs:
        result = await run_detection_test(detection_service, pr)
        results.append(result)

    report = calculate_accuracy_report(results)

    print(f"\nPrecision: {report.precision:.1%}")

    # Precision should be ≥80% (most detections are correct)
    assert report.precision >= 0.80, f"Precision {report.precision:.1%} below 80% target"


@pytest.mark.asyncio
async def test_recall_meets_target(detection_service, all_test_prs):
    """Test that recall (TP / (TP + FN)) is ≥85%."""
    results = []
    for pr in all_test_prs:
        result = await run_detection_test(detection_service, pr)
        results.append(result)

    report = calculate_accuracy_report(results)

    print(f"\nRecall: {report.recall:.1%}")

    # Recall should be ≥85% (most AI code is detected)
    assert report.recall >= 0.85, f"Recall {report.recall:.1%} below 85% target"


@pytest.mark.asyncio
async def test_f1_score_meets_target(detection_service, all_test_prs):
    """Test that F1 score is ≥80%."""
    results = []
    for pr in all_test_prs:
        result = await run_detection_test(detection_service, pr)
        results.append(result)

    report = calculate_accuracy_report(results)

    print(f"\nF1 Score: {report.f1_score:.1%}")

    # F1 should be ≥80% (balanced precision/recall)
    assert report.f1_score >= 0.80, f"F1 score {report.f1_score:.1%} below 80% target"


# ============================================================================
# Edge Case Tests
# ============================================================================


@pytest.mark.asyncio
async def test_empty_pr_body(detection_service):
    """Test detection with empty PR body."""
    pr_data = {"title": "feat: add feature [Cursor]", "body": ""}
    commits = [{"commit": {"message": "[cursor] add feature"}}]

    result = await detection_service.detect(pr_data, commits, "diff")

    # Should still detect from title and commits
    assert result.is_ai_generated is True


@pytest.mark.asyncio
async def test_empty_commits(detection_service):
    """Test detection with no commits."""
    pr_data = {
        "title": "feat: implement with Copilot",
        "body": "Generated by GitHub Copilot",
    }
    commits = []

    result = await detection_service.detect(pr_data, commits, "diff")

    # Should still detect from title and body
    assert result.is_ai_generated is True


@pytest.mark.asyncio
async def test_minimal_signals(detection_service):
    """Test detection with minimal AI signals."""
    pr_data = {"title": "fix: typo", "body": "Fixed typo"}
    commits = [{"commit": {"message": "fix typo"}}]

    result = await detection_service.detect(pr_data, commits, "def func(): pass")

    # Should NOT detect (no AI signals)
    assert result.is_ai_generated is False
    assert result.confidence < 0.50


@pytest.mark.asyncio
async def test_mixed_signals(detection_service):
    """Test detection with mixed AI and human signals."""
    pr_data = {
        "title": "feat: add feature",
        "body": "Implemented manually but used Copilot for autocomplete",
    }
    commits = [{"commit": {"message": "add feature"}}]

    result = await detection_service.detect(pr_data, commits, "")

    # Should detect (explicit mention of Copilot)
    assert result.is_ai_generated is True


# ============================================================================
# Dataset Integrity Tests
# ============================================================================


def test_dataset_size():
    """Verify test dataset has exactly 100 PRs."""
    assert len(ALL_TEST_PRS) == 100
    assert DATASET_SUMMARY["total"] == 100


def test_dataset_distribution():
    """Verify test dataset distribution matches specification."""
    assert len(CURSOR_PRS) == 25
    assert len(COPILOT_PRS) == 25
    assert len(CLAUDE_PRS) == 15
    assert len(CHATGPT_PRS) == 10
    assert len(WINDSURF_PRS) == 5
    assert len(OTHER_AI_PRS) == 5
    assert len(HUMAN_PRS) == 15

    # Verify summary matches
    assert DATASET_SUMMARY["cursor"] == 25
    assert DATASET_SUMMARY["copilot"] == 25
    assert DATASET_SUMMARY["claude"] == 15
    assert DATASET_SUMMARY["chatgpt"] == 10
    assert DATASET_SUMMARY["windsurf"] == 5
    assert DATASET_SUMMARY["other"] == 5
    assert DATASET_SUMMARY["human"] == 15


def test_ai_vs_human_distribution():
    """Verify AI vs human PR distribution."""
    ai_prs = [pr for pr in ALL_TEST_PRS if pr.expected_detected]
    human_prs = [pr for pr in ALL_TEST_PRS if not pr.expected_detected]

    assert len(ai_prs) == 85
    assert len(human_prs) == 15
    assert DATASET_SUMMARY["ai_generated"] == 85
    assert DATASET_SUMMARY["human_written"] == 15


def test_all_prs_have_expected_values():
    """Verify all PRs have required fields."""
    for pr in ALL_TEST_PRS:
        assert pr.id is not None
        assert pr.title is not None
        assert pr.body is not None
        assert isinstance(pr.commits, list)
        assert pr.diff is not None
        assert isinstance(pr.expected_detected, bool)
        assert pr.category in [
            "cursor",
            "copilot",
            "claude",
            "chatgpt",
            "windsurf",
            "other",
            "human",
        ]


def test_human_prs_have_no_expected_tool():
    """Verify human PRs have expected_tool=None."""
    for pr in HUMAN_PRS:
        assert pr.expected_tool is None
        assert pr.expected_detected is False


def test_ai_prs_have_expected_tool():
    """Verify AI PRs have appropriate expected_tool."""
    for pr in CURSOR_PRS:
        assert pr.expected_tool == AIToolType.CURSOR

    for pr in COPILOT_PRS:
        assert pr.expected_tool == AIToolType.COPILOT

    for pr in CLAUDE_PRS:
        assert pr.expected_tool == AIToolType.CLAUDE_CODE

    for pr in CHATGPT_PRS:
        assert pr.expected_tool == AIToolType.CHATGPT

    for pr in WINDSURF_PRS:
        assert pr.expected_tool == AIToolType.WINDSURF
