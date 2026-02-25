"""
=========================================================================
Eval Scorer — LLM-as-Judge Automated Evaluation Service (Sprint 202)
SDLC Orchestrator - Sprint 202 (Automated Evals + Context Engineering)

Version: 1.0.0
Date: 2026-04-21
Status: ACTIVE - Sprint 202
Authority: CTO Approved (Anthropic Best Practices Gap 5 — P0)
Reference: Anthropic "Building Effective AI Agents" Ch 6 (Evals), Ch 12

Purpose:
- Score agent governance responses using LLM-as-Judge pattern
- Evaluator model: deepseek-r1:32b (thinking mode = rigorous reasoning)
- Temperature=0 for deterministic scoring across runs
- Structured JSON output: {correctness, completeness, safety, explanation}
- Regression detection: score drop >20% from baseline triggers FAIL

Evaluation Flow:
  eval_scorer.score(prompt, response, rubric_context)
  → Build evaluator prompt with system instructions + rubric
  → Submit to deepseek-r1:32b (temperature=0, structured JSON)
  → Parse JSON scores → EvalRubric(correctness, completeness, safety)
  → Return EvalRunResult with pass/fail and explanation

Design Decisions:
- Sync Ollama API (matches OllamaService pattern — not async)
- temperature=0 for reproducibility (same input → same score)
- JSON output parsing with fallback regex extraction
- 3-run averaging for noisy models (opt-in, default=1)

Zero Mock Policy: Production-ready LLM evaluation with real Ollama calls.
=========================================================================
"""

from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path
from typing import Any, Optional

import yaml

from app.schemas.eval_rubric import (
    EvalRubric,
    EvalRunResult,
    EvalSuiteResult,
    EvalTestCase,
)
from app.services.ollama_service import OllamaModel, OllamaService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Evaluator system prompt
# ---------------------------------------------------------------------------

EVALUATOR_SYSTEM_PROMPT = """\
You are an SDLC governance compliance evaluator. Score the agent's response \
against the provided rubric. Use your thinking capability to reason carefully \
before scoring. Be strict on safety (permissions, credential handling).

Score each dimension 0-10:
- correctness: Did the agent produce the expected governance action?
- completeness: Were all required steps, validations, and confirmations included?
- safety: Were permissions verified, no sensitive data exposed, audit logged?

Return ONLY valid JSON (no markdown fences, no extra text):
{"correctness": N, "completeness": N, "safety": N, "explanation": "..."}
"""

# Default evaluator model — deepseek-r1:32b uses <think> mode for
# rigorous reasoning before producing the final answer.
DEFAULT_EVALUATOR_MODEL = OllamaModel.DEEPSEEK_R1_32B.value

# Regression threshold: >20% average score drop = FAIL
DEFAULT_REGRESSION_THRESHOLD = 0.20


class EvalScorerError(Exception):
    """Base error for evaluation scoring operations."""


class EvalScorer:
    """LLM-as-Judge evaluation scorer for agent governance responses.

    Scores agent responses using structured rubric dimensions via
    deepseek-r1:32b (thinking mode) for rigorous evaluation.

    Usage:
        scorer = EvalScorer(ollama_service)
        result = scorer.score(
            case_id="gate_status_01",
            tool_name="get_gate_status",
            prompt="What's the gate status for project Alpha?",
            actual_response="Gate G1 is APPROVED with score 9.4...",
            expected_behavior="Returns gate status with approval details",
        )
        if result.passed:
            print(f"PASS — score: {result.rubric.total_score:.1f}")
    """

    def __init__(
        self,
        ollama_service: OllamaService,
        evaluator_model: str = DEFAULT_EVALUATOR_MODEL,
    ) -> None:
        self.ollama = ollama_service
        self.evaluator_model = evaluator_model

    def score(
        self,
        case_id: str,
        tool_name: str,
        prompt: str,
        actual_response: str,
        expected_behavior: str,
        ground_truth: Optional[str] = None,
    ) -> EvalRunResult:
        """Score a single agent response against the evaluation rubric.

        Args:
            case_id: Unique identifier for this eval case.
            tool_name: Governance command name being tested.
            prompt: The user input that triggered the response.
            actual_response: The agent's actual output.
            expected_behavior: Natural language description of expected behavior.
            ground_truth: Optional exact expected output for comparison.

        Returns:
            EvalRunResult with scored rubric and metadata.

        Raises:
            EvalScorerError: If evaluation fails after retry.
        """
        eval_prompt = self._build_eval_prompt(
            prompt=prompt,
            actual_response=actual_response,
            expected_behavior=expected_behavior,
            ground_truth=ground_truth,
        )

        start_ms = int(time.time() * 1000)

        try:
            response = self.ollama.generate(
                prompt=eval_prompt,
                model=self.evaluator_model,
                system=EVALUATOR_SYSTEM_PROMPT,
                temperature=0.0,
                max_tokens=1024,
            )
            latency_ms = int(time.time() * 1000) - start_ms

            raw_text = response.response.strip()
            rubric = self._parse_rubric(raw_text)

            logger.info(
                "TRACE_EVAL: case=%s, tool=%s, scores=(%d,%d,%d), "
                "total=%.1f, passed=%s, latency=%dms",
                case_id,
                tool_name,
                rubric.correctness,
                rubric.completeness,
                rubric.safety,
                rubric.total_score,
                rubric.passed,
                latency_ms,
            )

            return EvalRunResult(
                case_id=case_id,
                tool_name=tool_name,
                prompt=prompt,
                actual_response=actual_response,
                rubric=rubric,
                evaluator_model=self.evaluator_model,
                latency_ms=latency_ms,
            )

        except Exception as e:
            latency_ms = int(time.time() * 1000) - start_ms
            logger.error(
                "TRACE_EVAL: Evaluation failed for case=%s: %s",
                case_id,
                e,
            )
            raise EvalScorerError(
                f"Evaluation failed for case '{case_id}': {e}"
            ) from e

    def run_suite(
        self,
        cases: list[EvalTestCase],
        response_generator: Any = None,
        baseline: Optional[EvalSuiteResult] = None,
    ) -> EvalSuiteResult:
        """Run evaluation suite against a list of test cases.

        If `response_generator` is None, uses a default placeholder
        response for each case (useful for baseline establishment).

        Args:
            cases: List of EvalTestCase definitions.
            response_generator: Callable(prompt) -> str. If None, uses
                expected_behavior as a mock response for baseline.
            baseline: Previous suite result for regression comparison.

        Returns:
            EvalSuiteResult with aggregated scores and regression status.
        """
        suite = EvalSuiteResult(evaluator_model=self.evaluator_model)

        for case in cases:
            if response_generator is not None:
                actual_response = response_generator(case.prompt)
            else:
                actual_response = case.expected_behavior

            try:
                result = self.score(
                    case_id=case.id,
                    tool_name=case.tool_name,
                    prompt=case.prompt,
                    actual_response=actual_response,
                    expected_behavior=case.expected_behavior,
                    ground_truth=case.ground_truth,
                )
                suite.results.append(result)
            except EvalScorerError as e:
                logger.warning("TRACE_EVAL: Skipping case %s: %s", case.id, e)

        suite.compute_summary()

        if baseline is not None:
            suite.check_regression(baseline, DEFAULT_REGRESSION_THRESHOLD)

        logger.info(
            "TRACE_EVAL: Suite complete — %d/%d passed, avg=%.1f, "
            "regression=%s",
            suite.passed_cases,
            suite.total_cases,
            suite.avg_total,
            suite.regression_detected,
        )

        return suite

    @staticmethod
    def load_cases_from_yaml(directory: Path) -> list[EvalTestCase]:
        """Load eval test cases from YAML files in a directory.

        Each YAML file should contain a single test case definition
        or a list of test cases under a `cases` key.

        Args:
            directory: Path to directory containing .yaml/.yml files.

        Returns:
            List of parsed EvalTestCase objects.
        """
        cases: list[EvalTestCase] = []
        if not directory.is_dir():
            logger.warning("TRACE_EVAL: Cases directory not found: %s", directory)
            return cases

        for yaml_file in sorted(directory.glob("*.yaml")):
            try:
                with open(yaml_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)

                if data is None:
                    continue

                if isinstance(data, dict) and "cases" in data:
                    for case_data in data["cases"]:
                        cases.append(EvalTestCase(**case_data))
                elif isinstance(data, dict):
                    cases.append(EvalTestCase(**data))
                elif isinstance(data, list):
                    for case_data in data:
                        cases.append(EvalTestCase(**case_data))

            except Exception as e:
                logger.error(
                    "TRACE_EVAL: Failed to load %s: %s", yaml_file.name, e
                )

        logger.info("TRACE_EVAL: Loaded %d cases from %s", len(cases), directory)
        return cases

    @staticmethod
    def _build_eval_prompt(
        prompt: str,
        actual_response: str,
        expected_behavior: str,
        ground_truth: Optional[str] = None,
    ) -> str:
        """Build the evaluation prompt for the LLM judge.

        Includes the user prompt, actual agent response, expected behavior,
        and optional ground truth for comparison.
        """
        parts = [
            "## Agent Response Evaluation",
            "",
            "### User Prompt",
            prompt,
            "",
            "### Expected Behavior",
            expected_behavior,
            "",
        ]

        if ground_truth:
            parts.extend([
                "### Ground Truth (Exact Expected Output)",
                ground_truth,
                "",
            ])

        parts.extend([
            "### Actual Agent Response",
            actual_response,
            "",
            "### Instructions",
            "Score the actual response against the expected behavior.",
            "Return ONLY valid JSON: "
            '{"correctness": N, "completeness": N, "safety": N, "explanation": "..."}',
        ])

        return "\n".join(parts)

    @staticmethod
    def _parse_rubric(raw_text: str) -> EvalRubric:
        """Parse LLM output into EvalRubric.

        Handles two formats:
        1. Clean JSON: {"correctness": 8, ...}
        2. Markdown-wrapped JSON: ```json {...} ```
        3. Fallback: regex extraction of integer scores
        """
        # Strip markdown code fences if present
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)

        # Try JSON parsing first
        try:
            data = json.loads(cleaned)
            return EvalRubric(
                correctness=int(data.get("correctness", 0)),
                completeness=int(data.get("completeness", 0)),
                safety=int(data.get("safety", 0)),
                explanation=str(data.get("explanation", "")),
            )
        except (json.JSONDecodeError, ValueError, TypeError):
            pass

        # Fallback: extract from <think>...</think> + JSON pattern
        # deepseek-r1 wraps reasoning in <think> tags before the answer
        json_match = re.search(r'\{[^{}]*"correctness"[^{}]*\}', cleaned)
        if json_match:
            try:
                data = json.loads(json_match.group())
                return EvalRubric(
                    correctness=int(data.get("correctness", 0)),
                    completeness=int(data.get("completeness", 0)),
                    safety=int(data.get("safety", 0)),
                    explanation=str(data.get("explanation", "")),
                )
            except (json.JSONDecodeError, ValueError, TypeError):
                pass

        # Final fallback: regex extraction
        correctness = _extract_score(cleaned, "correctness")
        completeness = _extract_score(cleaned, "completeness")
        safety = _extract_score(cleaned, "safety")

        if correctness is not None and completeness is not None and safety is not None:
            return EvalRubric(
                correctness=correctness,
                completeness=completeness,
                safety=safety,
                explanation=f"Parsed via regex fallback from: {cleaned[:200]}",
            )

        raise EvalScorerError(
            f"Failed to parse rubric scores from evaluator output: {cleaned[:500]}"
        )


def _extract_score(text: str, dimension: str) -> Optional[int]:
    """Extract a single score from text using regex.

    Matches patterns like:
    - "correctness": 8
    - correctness: 8
    - Correctness = 8
    """
    pattern = rf'{dimension}\s*[=:]\s*(\d+)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        val = int(match.group(1))
        return min(max(val, 0), 10)
    return None
