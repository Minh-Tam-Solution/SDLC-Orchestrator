"""
GitHubAIDetectionService - Combined Detection Orchestrator

SDLC Stage: 04 - BUILD
Sprint: 42 - AI Detection & Validation Pipeline
Framework: SDLC 5.1.1
Epic: EP-02 AI Safety Layer v1

Purpose:
Orchestrate multiple AI detection strategies with weighted voting.
Combines metadata, commit, and pattern analysis for ≥85% accuracy.

Architecture:
- 3 detection strategies running in parallel
- Weighted voting: Metadata (40%), Commit (40%), Pattern (20%)
- Decision threshold: 0.50 confidence
- Async/await for performance

Performance Target: <600ms p95 latency
"""

import asyncio
import time
from typing import List, Tuple

from . import AIDetectionResult, AIDetectionService, DetectionMethod, DetectionResult
from .commit_detector import CommitDetector
from .metadata_detector import MetadataDetector
from .pattern_detector import PatternDetector


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

        # Run all detectors in parallel
        tasks = [
            detector.detect(pr_data, commits, diff) for detector, _ in self.detectors
        ]
        results = await asyncio.gather(*tasks)

        # Calculate weighted confidence
        total_confidence = sum(
            result.confidence * weight
            for result, (_, weight) in zip(results, self.detectors)
        )

        # Determine detected tool (highest confidence wins)
        detected_results = [r for r in results if r.detected]
        detected_tool = None
        detected_model = None

        if detected_results:
            best_result = max(detected_results, key=lambda x: x.confidence)
            detected_tool = best_result.tool
            # Try to extract model from metadata evidence
            if best_result.method == DetectionMethod.METADATA:
                detected_model = self._extract_model_from_evidence(
                    best_result.evidence
                )

        # Aggregate evidence from all detectors
        combined_evidence = {
            "metadata": results[0].evidence,
            "commit": results[1].evidence,
            "pattern": results[2].evidence,
            "weights": {"metadata": 0.4, "commit": 0.4, "pattern": 0.2},
            "individual_confidences": {
                "metadata": results[0].confidence,
                "commit": results[1].confidence,
                "pattern": results[2].confidence,
            },
        }

        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)

        return AIDetectionResult(
            is_ai_generated=total_confidence > 0.50,
            confidence=total_confidence,
            detected_tool=detected_tool,
            detected_model=detected_model,
            detected_model_version=None,
            detection_method=DetectionMethod.COMBINED,
            strategies_used=["metadata", "commit", "pattern"],
            detection_evidence=combined_evidence,
            detection_duration_ms=duration_ms,
        )

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
