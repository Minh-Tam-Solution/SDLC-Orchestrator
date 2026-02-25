"""
Sprint 202 — Automated Evals Framework + Context Engineering Depth
Test Suite: 50 tests across 10 test classes

Track A: Eval Framework (20 tests)
  - EvalRubric schema validation (6 tests)
  - EvalScorer scoring logic (6 tests)
  - YAML test case loading (4 tests)
  - EvalSuiteResult aggregation + regression (4 tests)

Track B: Context Engineering (16 tests)
  - AgentNote model schema (4 tests)
  - NoteService CRUD + UPSERT (8 tests)
  - Notes context injection (4 tests)

Track C: Integration (8 tests)
  - Command registry expansion (4 tests)
  - Evidence capture for eval reports (2 tests)
  - Tool context internal tools (2 tests)

Track D: Regression Guards (6 tests)
  - Sprint 201 regression guard (command count: 8→10)
  - Sprint 200 regression guard (OTT gateway)
  - Import checks for new modules
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

# ---------------------------------------------------------------------------
# Track A — Eval Framework Tests
# ---------------------------------------------------------------------------


class TestEvalRubricSchema:
    """A-02: EvalRubric dataclass validation — 6 tests."""

    def test_rubric_total_score_calculation(self):
        """Average of 3 dimensions."""
        from app.schemas.eval_rubric import EvalRubric

        rubric = EvalRubric(correctness=8, completeness=9, safety=10)
        assert rubric.total_score == pytest.approx(9.0)

    def test_rubric_passes_when_avg_ge_7_and_safety_ge_8(self):
        """Pass: avg >= 7.0 AND safety >= 8."""
        from app.schemas.eval_rubric import EvalRubric

        rubric = EvalRubric(correctness=7, completeness=7, safety=8)
        assert rubric.total_score == pytest.approx(7.33, abs=0.1)
        assert rubric.passed is True

    def test_rubric_fails_when_safety_below_8(self):
        """Fail: safety < 8 even if avg >= 7."""
        from app.schemas.eval_rubric import EvalRubric

        rubric = EvalRubric(correctness=9, completeness=9, safety=7)
        assert rubric.total_score == pytest.approx(8.33, abs=0.1)
        assert rubric.passed is False

    def test_rubric_fails_when_avg_below_7(self):
        """Fail: avg < 7.0 even if safety >= 8."""
        from app.schemas.eval_rubric import EvalRubric

        rubric = EvalRubric(correctness=3, completeness=4, safety=10)
        assert rubric.total_score == pytest.approx(5.67, abs=0.1)
        assert rubric.passed is False

    def test_rubric_with_explanation(self):
        """Explanation field preserved."""
        from app.schemas.eval_rubric import EvalRubric

        rubric = EvalRubric(
            correctness=8, completeness=9, safety=10,
            explanation="Correctly handled gate approval.",
        )
        assert "gate approval" in rubric.explanation

    def test_rubric_boundary_scores(self):
        """Edge case: all zeros."""
        from app.schemas.eval_rubric import EvalRubric

        rubric = EvalRubric(correctness=0, completeness=0, safety=0)
        assert rubric.total_score == 0.0
        assert rubric.passed is False


class TestEvalScorer:
    """A-01: EvalScorer scoring logic — 6 tests."""

    def test_score_returns_eval_run_result(self):
        """score() returns EvalRunResult with correct fields."""
        from app.schemas.eval_rubric import EvalRunResult
        from app.services.agent_team.eval_scorer import EvalScorer
        from app.services.ollama_service import OllamaResponse

        mock_ollama = MagicMock()
        mock_ollama.generate.return_value = OllamaResponse(
            response=json.dumps({
                "correctness": 8, "completeness": 9, "safety": 10,
                "explanation": "OK",
            }),
            model="deepseek-r1:32b",
            done=True,
            total_duration_ns=1000000000,
            load_duration_ns=0,
            prompt_eval_count=0,
            eval_count=50,
            eval_duration_ns=800000000,
        )

        scorer = EvalScorer(mock_ollama)
        result = scorer.score(
            case_id="test_01",
            tool_name="get_gate_status",
            prompt="What is gate status?",
            actual_response="Gate G1 is APPROVED.",
            expected_behavior="Returns gate status.",
        )

        assert isinstance(result, EvalRunResult)
        assert result.case_id == "test_01"
        assert result.rubric.correctness == 8
        assert result.rubric.safety == 10
        assert result.passed is True

    def test_score_handles_markdown_wrapped_json(self):
        """Handles ```json ... ``` wrapping."""
        from app.services.agent_team.eval_scorer import EvalScorer
        from app.services.ollama_service import OllamaResponse

        mock_ollama = MagicMock()
        mock_ollama.generate.return_value = OllamaResponse(
            response='```json\n{"correctness": 7, "completeness": 8, "safety": 9, "explanation": "OK"}\n```',
            model="deepseek-r1:32b",
            done=True,
            total_duration_ns=1000000000,
            load_duration_ns=0,
            prompt_eval_count=0,
            eval_count=50,
            eval_duration_ns=800000000,
        )

        scorer = EvalScorer(mock_ollama)
        result = scorer.score(
            case_id="test_02",
            tool_name="create_project",
            prompt="Create project",
            actual_response="Project created.",
            expected_behavior="Creates project.",
        )

        assert result.rubric.correctness == 7
        assert result.rubric.completeness == 8

    def test_score_handles_deepseek_think_tags(self):
        """deepseek-r1 wraps reasoning in <think> tags."""
        from app.services.agent_team.eval_scorer import EvalScorer
        from app.services.ollama_service import OllamaResponse

        mock_ollama = MagicMock()
        mock_ollama.generate.return_value = OllamaResponse(
            response=(
                '<think>\nLet me analyze this response...\n'
                'The agent correctly checked permissions.\n</think>\n\n'
                '{"correctness": 9, "completeness": 8, "safety": 10, '
                '"explanation": "Good governance action."}'
            ),
            model="deepseek-r1:32b",
            done=True,
            total_duration_ns=2000000000,
            load_duration_ns=0,
            prompt_eval_count=0,
            eval_count=80,
            eval_duration_ns=1500000000,
        )

        scorer = EvalScorer(mock_ollama)
        result = scorer.score(
            case_id="test_03",
            tool_name="request_approval",
            prompt="Approve gate",
            actual_response="Gate approved.",
            expected_behavior="Approves gate with permissions check.",
        )

        assert result.rubric.correctness == 9
        assert result.rubric.safety == 10

    def test_score_raises_on_unparseable_output(self):
        """Raises EvalScorerError if output cannot be parsed."""
        from app.services.agent_team.eval_scorer import EvalScorer, EvalScorerError
        from app.services.ollama_service import OllamaResponse

        mock_ollama = MagicMock()
        mock_ollama.generate.return_value = OllamaResponse(
            response="I cannot evaluate this. Sorry.",
            model="deepseek-r1:32b",
            done=True,
            total_duration_ns=500000000,
            load_duration_ns=0,
            prompt_eval_count=0,
            eval_count=20,
            eval_duration_ns=400000000,
        )

        scorer = EvalScorer(mock_ollama)
        with pytest.raises(EvalScorerError, match="Failed to parse rubric"):
            scorer.score(
                case_id="test_04",
                tool_name="export_audit",
                prompt="Export audit",
                actual_response="Here is the audit.",
                expected_behavior="Returns audit data.",
            )

    def test_score_uses_temperature_zero(self):
        """Verifies temperature=0 for deterministic scoring."""
        from app.services.agent_team.eval_scorer import EvalScorer
        from app.services.ollama_service import OllamaResponse

        mock_ollama = MagicMock()
        mock_ollama.generate.return_value = OllamaResponse(
            response='{"correctness": 8, "completeness": 8, "safety": 9, "explanation": "OK"}',
            model="deepseek-r1:32b",
            done=True,
            total_duration_ns=1000000000,
            load_duration_ns=0,
            prompt_eval_count=0,
            eval_count=50,
            eval_duration_ns=800000000,
        )

        scorer = EvalScorer(mock_ollama)
        scorer.score(
            case_id="test_05",
            tool_name="get_gate_status",
            prompt="Gate status?",
            actual_response="G1 APPROVED.",
            expected_behavior="Returns status.",
        )

        call_kwargs = mock_ollama.generate.call_args
        assert call_kwargs.kwargs.get("temperature") == 0.0 or call_kwargs[1].get("temperature") == 0.0

    def test_score_with_ground_truth(self):
        """Ground truth included in eval prompt when provided."""
        from app.services.agent_team.eval_scorer import EvalScorer
        from app.services.ollama_service import OllamaResponse

        mock_ollama = MagicMock()
        mock_ollama.generate.return_value = OllamaResponse(
            response='{"correctness": 10, "completeness": 10, "safety": 10, "explanation": "Exact match."}',
            model="deepseek-r1:32b",
            done=True,
            total_duration_ns=1000000000,
            load_duration_ns=0,
            prompt_eval_count=0,
            eval_count=50,
            eval_duration_ns=800000000,
        )

        scorer = EvalScorer(mock_ollama)
        result = scorer.score(
            case_id="test_06",
            tool_name="get_gate_status",
            prompt="Gate status?",
            actual_response="G1 APPROVED score 9.4",
            expected_behavior="Returns status.",
            ground_truth="G1 APPROVED score 9.4",
        )

        assert result.rubric.correctness == 10
        prompt_arg = mock_ollama.generate.call_args.kwargs.get("prompt") or mock_ollama.generate.call_args[0][0]
        assert "Ground Truth" in prompt_arg


class TestYamlCaseLoading:
    """A-03: YAML eval test case loading — 4 tests."""

    def test_load_cases_from_yaml_directory(self):
        """Loads all 5 YAML cases from the cases/ directory."""
        from app.services.agent_team.eval_scorer import EvalScorer

        cases_dir = Path(__file__).parent.parent / "evals" / "cases"
        cases = EvalScorer.load_cases_from_yaml(cases_dir)
        assert len(cases) == 5

    def test_yaml_case_has_required_fields(self):
        """Each case has id, tool_name, prompt, expected_behavior."""
        from app.services.agent_team.eval_scorer import EvalScorer

        cases_dir = Path(__file__).parent.parent / "evals" / "cases"
        cases = EvalScorer.load_cases_from_yaml(cases_dir)
        for case in cases:
            assert case.id, f"Case missing id"
            assert case.tool_name, f"Case {case.id} missing tool_name"
            assert case.prompt, f"Case {case.id} missing prompt"
            assert case.expected_behavior, f"Case {case.id} missing expected_behavior"

    def test_yaml_cases_cover_five_governance_tools(self):
        """5 cases cover 5 distinct governance tools."""
        from app.services.agent_team.eval_scorer import EvalScorer

        cases_dir = Path(__file__).parent.parent / "evals" / "cases"
        cases = EvalScorer.load_cases_from_yaml(cases_dir)
        tool_names = {c.tool_name for c in cases}
        expected = {"get_gate_status", "request_approval", "create_project",
                    "submit_evidence", "export_audit"}
        assert tool_names == expected

    def test_load_from_nonexistent_dir_returns_empty(self):
        """Returns empty list for nonexistent directory."""
        from app.services.agent_team.eval_scorer import EvalScorer

        cases = EvalScorer.load_cases_from_yaml(Path("/tmp/nonexistent_dir_xyz"))
        assert cases == []


class TestEvalSuiteResult:
    """A-07: Suite aggregation + regression detection — 4 tests."""

    def test_suite_compute_summary(self):
        """compute_summary calculates correct averages."""
        from app.schemas.eval_rubric import EvalRubric, EvalRunResult, EvalSuiteResult

        suite = EvalSuiteResult()
        suite.results = [
            EvalRunResult(
                case_id="c1", tool_name="t1", prompt="p", actual_response="r",
                rubric=EvalRubric(correctness=8, completeness=9, safety=10),
                evaluator_model="test",
            ),
            EvalRunResult(
                case_id="c2", tool_name="t2", prompt="p", actual_response="r",
                rubric=EvalRubric(correctness=6, completeness=7, safety=8),
                evaluator_model="test",
            ),
        ]
        suite.compute_summary()

        assert suite.total_cases == 2
        assert suite.passed_cases == 2  # c1 passes (avg=9.0, safety=10), c2 passes (avg=7.0, safety=8 — threshold met)
        assert suite.avg_correctness == pytest.approx(7.0)
        assert suite.avg_completeness == pytest.approx(8.0)
        assert suite.avg_safety == pytest.approx(9.0)

    def test_suite_regression_detected(self):
        """Regression flagged when score drops >20%."""
        from app.schemas.eval_rubric import EvalRubric, EvalRunResult, EvalSuiteResult

        baseline = EvalSuiteResult(avg_total=9.0)
        current = EvalSuiteResult(avg_total=6.0)  # 33% drop
        current.check_regression(baseline, threshold=0.20)

        assert current.regression_detected is True
        assert "33" in current.regression_details

    def test_suite_no_regression_within_threshold(self):
        """No regression when drop is within threshold."""
        from app.schemas.eval_rubric import EvalSuiteResult

        baseline = EvalSuiteResult(avg_total=9.0)
        current = EvalSuiteResult(avg_total=8.5)  # 5.6% drop
        current.check_regression(baseline, threshold=0.20)

        assert current.regression_detected is False

    def test_suite_empty_results(self):
        """Empty suite computes zero averages."""
        from app.schemas.eval_rubric import EvalSuiteResult

        suite = EvalSuiteResult()
        suite.compute_summary()

        assert suite.total_cases == 0
        assert suite.avg_total == 0.0


# ---------------------------------------------------------------------------
# Track B — Context Engineering Tests
# ---------------------------------------------------------------------------


class TestAgentNoteModel:
    """B-01: AgentNote model schema — 4 tests."""

    def test_agent_note_has_required_columns(self):
        """Model has all required columns."""
        from app.models.agent_note import AgentNote

        columns = {c.name for c in AgentNote.__table__.columns}
        required = {"id", "agent_id", "conversation_id", "key", "value",
                    "note_type", "created_at", "updated_at"}
        assert required.issubset(columns)

    def test_agent_note_tablename(self):
        """Table is named 'agent_notes'."""
        from app.models.agent_note import AgentNote

        assert AgentNote.__tablename__ == "agent_notes"

    def test_agent_note_unique_constraint(self):
        """UNIQUE(agent_id, key) constraint exists."""
        from app.models.agent_note import AgentNote

        constraints = [c.name for c in AgentNote.__table__.constraints
                       if hasattr(c, "name") and c.name]
        assert "uq_agent_notes_agent_key" in constraints

    def test_agent_note_indexes(self):
        """Required indexes exist."""
        from app.models.agent_note import AgentNote

        index_names = {idx.name for idx in AgentNote.__table__.indexes}
        assert "idx_agent_notes_agent_id" in index_names
        assert "idx_agent_notes_conversation" in index_names


class TestNoteServiceValidation:
    """B-02/B-03: NoteService validation — 8 tests."""

    def test_valid_note_types(self):
        """All 4 note types are recognized."""
        from app.services.agent_team.note_service import VALID_NOTE_TYPES

        assert VALID_NOTE_TYPES == {"decision", "commitment", "context", "preference"}

    def test_max_notes_per_agent(self):
        """MAX_NOTES_PER_AGENT is 50."""
        from app.services.agent_team.note_service import MAX_NOTES_PER_AGENT

        assert MAX_NOTES_PER_AGENT == 50

    def test_note_service_requires_db_session(self):
        """NoteService constructor accepts AsyncSession."""
        from app.services.agent_team.note_service import NoteService

        mock_db = AsyncMock()
        svc = NoteService(mock_db)
        assert svc.db is mock_db

    @pytest.mark.asyncio
    async def test_save_note_rejects_empty_key(self):
        """Empty key raises NoteServiceError."""
        from app.services.agent_team.note_service import NoteService, NoteServiceError

        svc = NoteService(AsyncMock())
        with pytest.raises(NoteServiceError, match="Key must be 1-100"):
            await svc.save_note(agent_id=uuid4(), key="", value="test")

    @pytest.mark.asyncio
    async def test_save_note_rejects_long_key(self):
        """Key > 100 chars raises NoteServiceError."""
        from app.services.agent_team.note_service import NoteService, NoteServiceError

        svc = NoteService(AsyncMock())
        with pytest.raises(NoteServiceError, match="Key must be 1-100"):
            await svc.save_note(agent_id=uuid4(), key="x" * 101, value="test")

    @pytest.mark.asyncio
    async def test_save_note_rejects_empty_value(self):
        """Empty value raises NoteServiceError."""
        from app.services.agent_team.note_service import NoteService, NoteServiceError

        svc = NoteService(AsyncMock())
        with pytest.raises(NoteServiceError, match="Value must be 1-500"):
            await svc.save_note(agent_id=uuid4(), key="test", value="")

    @pytest.mark.asyncio
    async def test_save_note_rejects_long_value(self):
        """Value > 500 chars raises NoteServiceError."""
        from app.services.agent_team.note_service import NoteService, NoteServiceError

        svc = NoteService(AsyncMock())
        with pytest.raises(NoteServiceError, match="Value must be 1-500"):
            await svc.save_note(agent_id=uuid4(), key="test", value="x" * 501)

    @pytest.mark.asyncio
    async def test_save_note_rejects_invalid_type(self):
        """Invalid note_type raises NoteServiceError."""
        from app.services.agent_team.note_service import NoteService, NoteServiceError

        svc = NoteService(AsyncMock())
        with pytest.raises(NoteServiceError, match="Invalid note_type"):
            await svc.save_note(
                agent_id=uuid4(), key="test", value="test",
                note_type="invalid_type",
            )


class TestNotesContextInjection:
    """B-04: Notes injection in _build_llm_context() — 4 tests."""

    def test_note_service_imported_in_orchestrator(self):
        """team_orchestrator imports NoteService."""
        from app.services.agent_team import team_orchestrator

        assert hasattr(team_orchestrator, "NoteService")

    def test_build_llm_context_method_exists(self):
        """_build_llm_context method exists on TeamOrchestrator."""
        from app.services.agent_team.team_orchestrator import TeamOrchestrator

        assert hasattr(TeamOrchestrator, "_build_llm_context")

    def test_format_notes_for_context_returns_none_for_empty(self):
        """format_notes_for_context returns None when no notes."""
        import asyncio
        from app.services.agent_team.note_service import NoteService

        mock_db = AsyncMock()
        mock_db.execute.return_value = MagicMock()
        mock_db.execute.return_value.scalars.return_value.all.return_value = []

        svc = NoteService(mock_db)
        result = asyncio.get_event_loop().run_until_complete(
            svc.format_notes_for_context(agent_id=uuid4())
        )
        assert result is None

    def test_note_tools_in_tool_context(self):
        """save_note and recall_note are in INTERNAL_TOOLS."""
        from app.services.agent_team.tool_context import INTERNAL_TOOLS, NOTE_TOOLS

        assert "save_note" in NOTE_TOOLS
        assert "recall_note" in NOTE_TOOLS
        assert NOTE_TOOLS.issubset(INTERNAL_TOOLS)


# ---------------------------------------------------------------------------
# Track C — Integration Tests
# ---------------------------------------------------------------------------


class TestCommandRegistryExpansion:
    """C-01/C-02: Command registry expansion 8→10 — 4 tests."""

    def test_registry_has_10_commands(self):
        """Registry expanded from 8 to 10 commands."""
        from app.services.agent_team.command_registry import GOVERNANCE_COMMANDS

        assert len(GOVERNANCE_COMMANDS) == 10

    def test_run_evals_command_registered(self):
        """run_evals command exists in registry."""
        from app.services.agent_team.command_registry import get_command

        cmd = get_command("run_evals")
        assert cmd is not None
        assert cmd.permission == "governance:read"
        assert "chạy đánh giá" in cmd.ott_aliases

    def test_list_notes_command_registered(self):
        """list_notes command exists in registry."""
        from app.services.agent_team.command_registry import get_command

        cmd = get_command("list_notes")
        assert cmd is not None
        assert cmd.permission == "governance:read"
        assert "xem ghi chú" in cmd.ott_aliases

    def test_registry_at_max_capacity(self):
        """Registry is at MAX_COMMANDS (10/10)."""
        from app.services.agent_team.command_registry import (
            GOVERNANCE_COMMANDS, MAX_COMMANDS,
        )

        assert len(GOVERNANCE_COMMANDS) == MAX_COMMANDS


class TestEvidenceEvalCapture:
    """C-05: Evidence capture for eval reports — 2 tests."""

    def test_evidence_collector_has_eval_report_method(self):
        """capture_eval_report method exists."""
        from app.services.agent_team.evidence_collector import EvidenceCollector

        assert hasattr(EvidenceCollector, "capture_eval_report")

    def test_eval_report_evidence_type_constant(self):
        """EVAL_REPORT is used as evidence type in capture method."""
        import inspect
        from app.services.agent_team.evidence_collector import EvidenceCollector

        source = inspect.getsource(EvidenceCollector.capture_eval_report)
        assert "EVAL_REPORT" in source


class TestToolContextInternalTools:
    """B-02/B-03: Tool context recognizes note tools — 2 tests."""

    def test_spawn_tools_constant_exists(self):
        """SPAWN_TOOLS frozenset exists."""
        from app.services.agent_team.tool_context import SPAWN_TOOLS

        assert "spawn_agent" in SPAWN_TOOLS
        assert "delegate" in SPAWN_TOOLS

    def test_note_tools_constant_exists(self):
        """NOTE_TOOLS frozenset exists."""
        from app.services.agent_team.tool_context import NOTE_TOOLS

        assert "save_note" in NOTE_TOOLS
        assert "recall_note" in NOTE_TOOLS


# ---------------------------------------------------------------------------
# Track D — Regression Guards
# ---------------------------------------------------------------------------


class TestRegressionGuards:
    """Sprint 201→202 regression guards — 6 tests."""

    def test_registry_expanded_from_8_to_10(self):
        """Sprint 201 had 8 commands, Sprint 202 has 10."""
        from app.services.agent_team.command_registry import GOVERNANCE_COMMANDS

        assert len(GOVERNANCE_COMMANDS) == 10

    def test_all_sprint_201_commands_preserved(self):
        """All 8 Sprint 201 commands still present."""
        from app.services.agent_team.command_registry import GOVERNANCE_COMMANDS

        names = {cmd.name for cmd in GOVERNANCE_COMMANDS}
        sprint_201_commands = {
            "create_project", "get_gate_status", "submit_evidence",
            "request_approval", "export_audit", "update_sprint",
            "close_sprint", "invite_member",
        }
        assert sprint_201_commands.issubset(names)

    def test_tool_name_enum_has_10_values(self):
        """ToolName enum has 10 members."""
        from app.services.agent_team.command_registry import ToolName

        assert len(ToolName) == 10

    def test_evidence_collector_captures_agent_output(self):
        """EvidenceCollector.capture_message still works for AGENT_OUTPUT."""
        from app.services.agent_team.evidence_collector import EvidenceCollector

        assert EvidenceCollector.EVIDENCE_TYPE == "AGENT_OUTPUT"

    def test_eval_rubric_import(self):
        """eval_rubric.py module importable."""
        from app.schemas.eval_rubric import (
            EvalRubric, EvalTestCase, EvalRunResult, EvalSuiteResult,
        )

        assert EvalRubric is not None
        assert EvalTestCase is not None

    def test_eval_scorer_import(self):
        """eval_scorer.py module importable."""
        from app.services.agent_team.eval_scorer import (
            EvalScorer, EvalScorerError, EVALUATOR_SYSTEM_PROMPT,
        )

        assert EvalScorer is not None
        assert "governance" in EVALUATOR_SYSTEM_PROMPT.lower()
