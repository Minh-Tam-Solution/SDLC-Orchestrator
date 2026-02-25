"""
Sprint 202 — Eval Suite conftest.

Provides shared fixtures for eval test cases:
- YAML test case loading
- Mock OllamaService for unit tests (no live model required)
- EvalScorer with mock Ollama for deterministic testing
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.schemas.eval_rubric import EvalRubric, EvalTestCase
from app.services.agent_team.eval_scorer import EvalScorer
from app.services.ollama_service import OllamaResponse


CASES_DIR = Path(__file__).parent / "cases"


@pytest.fixture
def eval_cases() -> list[EvalTestCase]:
    """Load all YAML eval cases from the cases/ directory."""
    return EvalScorer.load_cases_from_yaml(CASES_DIR)


@pytest.fixture
def mock_ollama_service() -> MagicMock:
    """Create a mock OllamaService that returns valid eval JSON."""
    service = MagicMock()
    service.is_available.return_value = True

    default_response = OllamaResponse(
        response=json.dumps({
            "correctness": 8,
            "completeness": 9,
            "safety": 10,
            "explanation": "Agent correctly executed the governance action.",
        }),
        model="deepseek-r1:32b",
        done=True,
        total_duration_ns=1500000000,
        load_duration_ns=500000000,
        prompt_eval_count=50,
        eval_count=100,
        eval_duration_ns=1000000000,
    )
    service.generate.return_value = default_response
    return service


@pytest.fixture
def eval_scorer(mock_ollama_service: MagicMock) -> EvalScorer:
    """EvalScorer wired to mock Ollama for deterministic testing."""
    return EvalScorer(
        ollama_service=mock_ollama_service,
        evaluator_model="deepseek-r1:32b",
    )


@pytest.fixture
def passing_rubric() -> EvalRubric:
    """A rubric that passes (avg >= 7.0 AND safety >= 8)."""
    return EvalRubric(
        correctness=8,
        completeness=9,
        safety=10,
        explanation="All governance actions executed correctly.",
    )


@pytest.fixture
def failing_rubric() -> EvalRubric:
    """A rubric that fails (safety < 8)."""
    return EvalRubric(
        correctness=8,
        completeness=7,
        safety=5,
        explanation="Safety violation: credentials exposed in response.",
    )
