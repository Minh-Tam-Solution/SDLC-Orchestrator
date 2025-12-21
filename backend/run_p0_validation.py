#!/usr/bin/env python3
"""
CTO P0 Validation Script - Sprint 42 Day 5 Fix

Purpose:
Validate the P0 fixes for overfitting:
1. Weighted voting (not OR-based)
2. Configurable threshold
3. Adversarial false positive protection

Usage:
    python3 run_p0_validation.py
"""

import asyncio
import sys
from collections import defaultdict
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.ai_detection import AIToolType
from app.services.ai_detection.service import GitHubAIDetectionService, DETECTION_THRESHOLD
from tests.fixtures.ai_detection_test_dataset import (
    ALL_TEST_PRS,
    ADVERSARIAL_PRS,
    DATASET_SUMMARY,
)


async def run_validation():
    """Run CTO P0 validation."""
    print("=" * 70)
    print("CTO P0 VALIDATION - Sprint 42 Day 5 Fixes")
    print("=" * 70)
    print()
    print(f"Detection Threshold: {DETECTION_THRESHOLD}")
    print(f"Total Test PRs: {len(ALL_TEST_PRS)}")
    print(f"Adversarial PRs: {len(ADVERSARIAL_PRS)}")
    print()

    service = GitHubAIDetectionService()

    # Run all tests
    results = []
    for pr in ALL_TEST_PRS:
        pr_data = {"title": pr.title, "body": pr.body}
        result = await service.detect(pr_data, pr.commits, pr.diff)
        results.append({
            "id": pr.id,
            "category": pr.category,
            "expected": pr.expected_detected,
            "actual": result.is_ai_generated,
            "confidence": result.confidence,
            "correct": result.is_ai_generated == pr.expected_detected,
        })

    # Calculate metrics
    total = len(results)
    correct = sum(1 for r in results if r["correct"])
    accuracy = correct / total

    # Confusion matrix
    tp = sum(1 for r in results if r["expected"] and r["actual"])
    tn = sum(1 for r in results if not r["expected"] and not r["actual"])
    fp = sum(1 for r in results if not r["expected"] and r["actual"])
    fn = sum(1 for r in results if r["expected"] and not r["actual"])

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    # Per-category accuracy
    category_results = defaultdict(list)
    for r in results:
        category_results[r["category"]].append(r)

    print("=" * 70)
    print("ACCURACY REPORT (with P0 fixes)")
    print("=" * 70)
    print()
    print(f"Total: {total}")
    print(f"Correct: {correct}")
    print(f"Accuracy: {accuracy:.1%}")
    print()
    print("Confusion Matrix:")
    print(f"  True Positives:  {tp}")
    print(f"  True Negatives:  {tn}")
    print(f"  False Positives: {fp}")
    print(f"  False Negatives: {fn}")
    print()
    print("Classification Metrics:")
    print(f"  Precision: {precision:.1%}")
    print(f"  Recall:    {recall:.1%}")
    print(f"  F1 Score:  {f1:.1%}")
    print()
    print("Per-Category Accuracy:")
    for category in ["cursor", "copilot", "claude", "chatgpt", "windsurf", "other", "human", "adversarial"]:
        if category in category_results:
            cat_correct = sum(1 for r in category_results[category] if r["correct"])
            cat_total = len(category_results[category])
            cat_acc = cat_correct / cat_total if cat_total > 0 else 0
            print(f"  {category:12}: {cat_acc:6.1%} ({cat_correct}/{cat_total})")

    # Adversarial analysis
    adversarial_results = [r for r in results if r["category"] == "adversarial"]
    adv_fp = sum(1 for r in adversarial_results if r["actual"])
    adv_fp_rate = adv_fp / len(adversarial_results) if adversarial_results else 0

    print()
    print("=" * 70)
    print("ADVERSARIAL FALSE POSITIVE ANALYSIS")
    print("=" * 70)
    print(f"Total Adversarial PRs: {len(adversarial_results)}")
    print(f"False Positives: {adv_fp}")
    print(f"FP Rate: {adv_fp_rate:.1%}")

    if adv_fp > 0:
        print("\nFalse Positive Details:")
        for r in adversarial_results:
            if r["actual"]:
                print(f"  {r['id']}: conf={r['confidence']:.2f}")

    print()
    print("=" * 70)
    print("VALIDATION RESULTS")
    print("=" * 70)

    # Check pass/fail criteria
    ai_prs = [r for r in results if r["expected"]]
    ai_recall = sum(1 for r in ai_prs if r["actual"]) / len(ai_prs)

    checks = [
        ("Accuracy >= 70%", accuracy >= 0.70, f"{accuracy:.1%}"),
        ("Recall >= 50%", recall >= 0.50, f"{recall:.1%}"),
        ("Adversarial FP <= 30%", adv_fp_rate <= 0.30, f"{adv_fp_rate:.1%}"),
        ("Precision >= 80%", precision >= 0.80, f"{precision:.1%}"),
    ]

    all_pass = True
    for name, passed, value in checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name} (actual: {value})")
        if not passed:
            all_pass = False

    print()
    if all_pass:
        print("✅ ALL P0 CHECKS PASSED")
    else:
        print("⚠️ SOME P0 CHECKS FAILED - Review detection logic")

    print("=" * 70)

    return all_pass


def main():
    try:
        success = asyncio.run(run_validation())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
