"""
GitHubAIDetectionService - Combined Detection Orchestrator

SDLC Stage: 04 - BUILD
Sprint: 42 - AI Detection & Validation Pipeline
Framework: SDLC 5.1.1
Epic: EP-02 AI Safety Layer v1
CTO Review: P0 Overfitting Fix Applied

Purpose:
Orchestrate multiple AI detection strategies with weighted voting.
Combines metadata, commit, and pattern analysis for ≥85% accuracy.

Architecture:
- 3 detection strategies running in parallel
- Weighted voting: Metadata (40%), Commit (40%), Pattern (20%)
- Configurable detection threshold (default: 0.50)
- Async/await for performance
- Prometheus metrics for observability

CTO P0 Fix (Sprint 42 Day 5):
- Reverted from OR-based to weighted voting (prevents overfitting)
- Added configurable threshold for precision/recall trade-off
- Production validation required before deployment

Performance Target: <600ms p95 latency
"""

import asyncio
import logging
import os
import time
from typing import List, Tuple

from . import AIDetectionResult, AIDetectionService, DetectionMethod, DetectionResult
from .commit_detector import CommitDetector
from .metadata_detector import MetadataDetector
from .pattern_detector import PatternDetector

# Structured logging (CTO P2)
logger = logging.getLogger(__name__)

# Configurable detection threshold (CTO P0 recommendation)
# Default: 0.50 (balanced precision/recall)
# Precision-focused: 0.65 (fewer false positives)
# Recall-focused: 0.35 (fewer false negatives)
DETECTION_THRESHOLD = float(os.getenv("AI_DETECTION_THRESHOLD", "0.50"))

# Import metrics (may fail in test environment)
try:
    from app.middleware.ai_detection_metrics import (
        record_detection_error,
        record_detection_request,
        record_detection_result,
        record_strategy_result,
    )

    METRICS_ENABLED = True
except ImportError:
    METRICS_ENABLED = False
    logger.warning("Prometheus metrics not available - running without metrics")


class GitHubAIDetectionService(AIDetectionService):
    """
    Orchestrate multiple detection strategies for GitHub PRs.

    Combines metadata analysis, commit patterns, and code patterns
    with weighted voting to achieve ≥85% accuracy.

    Weighting Strategy:
    - MetadataDetector: 40% (PR title/body, explicit mentions)
    - CommitDetector: 40% (commit message patterns, high confidence)
    - PatternDetector: 20% (code heuristics, supplementary signal)

    Decision Rule:
    - is_ai_generated = weighted_confidence > 0.50
    - detected_tool = highest confidence detector's tool
    """

    def __init__(self):
        """Initialize all detection strategies."""
        self.detectors: List[Tuple[DetectionResult, float]] = [
            (MetadataDetector(), 0.4),  # 40% weight (explicit signals)
            (CommitDetector(), 0.4),  # 40% weight (commit patterns)
            (PatternDetector(), 0.2),  # 20% weight (code heuristics)
        ]

    async def detect(
        self,
        pr_data: dict,
        commits: List[dict],
        diff: str,
    ) -> AIDetectionResult:
        """
        Detect AI-generated code in GitHub PR using combined strategies.

        Process:
        1. Run all 3 detectors in parallel (asyncio.gather)
        2. Calculate weighted confidence score
        3. Determine detected tool (highest confidence wins)
        4. Aggregate evidence from all detectors
        5. Record Prometheus metrics (CTO P1)

        Args:
            pr_data: GitHub PR object (title, body, labels, etc.)
            commits: List of commit objects with messages
            diff: Unified diff of all file changes

        Returns:
            AIDetectionResult with aggregated confidence and evidence

        Performance:
        - Target: <600ms p95 latency
        - Parallel execution of all detectors
        - No external API calls (local pattern matching only)
        """
        start_time = time.time()

        # Record detection request (CTO P1)
        if METRICS_ENABLED:
            record_detection_request()

        # Structured logging (CTO P2)
        logger.info(
            "Starting AI detection",
            extra={
                "pr_title": pr_data.get("title", "")[:50],
                "commit_count": len(commits),
                "diff_size": len(diff),
            },
        )

        try:
            # Run all detectors in parallel with timing
            strategy_times = {}
            tasks = []
            for detector, _ in self.detectors:
                tasks.append(self._run_detector_with_timing(detector, pr_data, commits, diff, strategy_times))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Handle exceptions from individual detectors
            processed_results = []
            strategy_names = ["metadata", "commit", "pattern"]
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(
                        f"Detector {strategy_names[i]} failed: {result}",
                        exc_info=True,
                    )
                    if METRICS_ENABLED:
                        record_detection_error(strategy_names[i], type(result).__name__)
                    # Use empty result on error
                    processed_results.append(DetectionResult(
                        detected=False,
                        confidence=0.0,
                        tool=None,
                        method=DetectionMethod.METADATA,
                        evidence={"error": str(result)},
                    ))
                else:
                    processed_results.append(result)
                    # Record strategy metrics (CTO P1)
                    if METRICS_ENABLED:
                        record_strategy_result(
                            strategy=strategy_names[i],
                            confidence=result.confidence,
                            duration_seconds=strategy_times.get(strategy_names[i], 0),
                        )

            # Detection Logic (CTO P0 Fix - Reverted to Weighted Voting)
            #
            # Strategy: Weighted voting with configurable threshold
            # - Calculate weighted average of all detector confidences
            # - Compare against configurable threshold (default 0.50)
            # - This prevents overfitting to synthetic test data
            #
            # CTO Rationale: OR-based detection led to 100% accuracy on
            # synthetic data but risks high false positive rate in production.
            # Weighted voting is more robust and production-ready.

            # Calculate weighted confidence (primary decision metric)
            weighted_confidence = sum(
                result.confidence * weight
                for result, (_, weight) in zip(processed_results, self.detectors)
            )

            # Also track max confidence for reporting
            max_confidence = max(r.confidence for r in processed_results)

            # Decision: Use weighted confidence against threshold
            # Threshold is configurable via AI_DETECTION_THRESHOLD env var
            is_ai_detected = weighted_confidence > DETECTION_THRESHOLD

            # Determine detected tool (highest confidence wins)
            detected_results = [r for r in processed_results if r.detected]
            detected_tool = None
            detected_model = None

            if detected_results and is_ai_detected:
                best_result = max(detected_results, key=lambda x: x.confidence)
                detected_tool = best_result.tool
                # Try to extract model from metadata evidence
                if best_result.method == DetectionMethod.METADATA:
                    detected_model = self._extract_model_from_evidence(
                        best_result.evidence
                    )

            # Final confidence for reporting
            final_confidence = weighted_confidence

            # Aggregate evidence from all detectors
            combined_evidence = {
                "metadata": processed_results[0].evidence,
                "commit": processed_results[1].evidence,
                "pattern": processed_results[2].evidence,
                "weights": {"metadata": 0.4, "commit": 0.4, "pattern": 0.2},
                "individual_confidences": {
                    "metadata": processed_results[0].confidence,
                    "commit": processed_results[1].confidence,
                    "pattern": processed_results[2].confidence,
                },
                "weighted_confidence": weighted_confidence,
                "max_confidence": max_confidence,
                "detection_threshold": DETECTION_THRESHOLD,
                "strategy_durations_ms": {
                    k: int(v * 1000) for k, v in strategy_times.items()
                },
            }

            # Calculate duration
            duration_seconds = time.time() - start_time
            duration_ms = int(duration_seconds * 1000)

            # Record detection result metrics (CTO P1)
            if METRICS_ENABLED:
                record_detection_result(
                    detected=is_ai_detected,
                    tool=detected_tool,
                    method=DetectionMethod.COMBINED,
                    confidence=final_confidence,
                    duration_seconds=duration_seconds,
                )

            # Structured logging (CTO P2)
            logger.info(
                "AI detection completed",
                extra={
                    "is_ai_generated": is_ai_detected,
                    "confidence": round(final_confidence, 3),
                    "detected_tool": detected_tool.value if detected_tool else None,
                    "duration_ms": duration_ms,
                },
            )

            return AIDetectionResult(
                is_ai_generated=is_ai_detected,
                confidence=final_confidence,
                detected_tool=detected_tool,
                detected_model=detected_model,
                detected_model_version=None,
                detection_method=DetectionMethod.COMBINED,
                strategies_used=["metadata", "commit", "pattern"],
                detection_evidence=combined_evidence,
                detection_duration_ms=duration_ms,
            )

        except Exception as e:
            logger.error(f"AI detection failed: {e}", exc_info=True)
            if METRICS_ENABLED:
                record_detection_error("combined", type(e).__name__)
            raise

    async def _run_detector_with_timing(
        self,
        detector,
        pr_data: dict,
        commits: List[dict],
        diff: str,
        timing_dict: dict,
    ) -> DetectionResult:
        """Run a detector and record its execution time."""
        start = time.time()
        result = await detector.detect(pr_data, commits, diff)
        timing_dict[detector.get_strategy_name()] = time.time() - start
        return result

    def _extract_model_from_evidence(self, evidence: dict) -> str | None:
        """
        Extract AI model name from evidence.

        Looks for common model names in matched text:
        - gpt-4-turbo, gpt-4, gpt-3.5-turbo
        - claude-3-opus, claude-3-sonnet, claude-3-haiku
        - gemini-pro, gemini-ultra

        Args:
            evidence: Evidence dict from detector

        Returns:
            Model name string or None
        """
        # Check for matched text in metadata evidence
        matched_in = evidence.get("matched_in", [])
        if not matched_in:
            return None

        # Common model name patterns
        model_names = [
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
            "claude-3-opus",
            "claude-3-sonnet",
            "claude-3-haiku",
            "gemini-pro",
            "gemini-ultra",
        ]

        # Search in evidence for model names
        evidence_str = str(evidence).lower()
        for model in model_names:
            if model in evidence_str:
                return model

        return None


# Singleton instance
ai_detection_service = GitHubAIDetectionService()
