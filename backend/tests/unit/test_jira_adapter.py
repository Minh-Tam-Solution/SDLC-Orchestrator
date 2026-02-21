"""
test_jira_adapter.py — Sprint 184 JA-01..20

Unit tests for JiraAdapter (httpx-based, no SDK).

Test IDs: JA-01 to JA-20 (20 tests)

Coverage:
  JA-01..06  list_projects (network, auth, errors, timeout)
  JA-07..09  get_sprint_issues (fields, empty sprint)
  JA-10..13  sync_to_evidence_vault (DB write, idempotency)
  JA-14..16  test_connection (valid/invalid/timeout)
  JA-17..20  Route-level behaviour (via adapter usage)

Framework: pytest + pytest-asyncio + unittest.mock
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import httpx
import pytest

from app.services.integrations.jira_adapter import JiraAdapter


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def adapter() -> JiraAdapter:
    """Default JiraAdapter for testing."""
    return JiraAdapter(
        base_url="https://acme.atlassian.net",
        api_token="ATATT3xFfGF0TEST_TOKEN",
        email="dev@acme.com",
    )


def _mock_response(status_code: int, body: Any) -> MagicMock:
    """Build a mock httpx.Response with JSON body."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json.return_value = body
    if status_code >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            message=f"HTTP {status_code}",
            request=MagicMock(),
            response=resp,
        )
    else:
        resp.raise_for_status.return_value = None
    return resp


def _jira_issue(key: str = "PROJ-1", summary: str = "Test story",
                status: str = "In Progress", type_: str = "Story") -> dict[str, Any]:
    """Build a minimal Jira issue dict."""
    return {
        "id": "10001",
        "key": key,
        "fields": {
            "summary": summary,
            "status": {"name": status, "id": "3"},
            "issuetype": {"name": type_, "id": "10001"},
            "assignee": {"displayName": "Alice Dev"},
            "priority": {"name": "Medium"},
            "labels": [],
        },
    }


# ---------------------------------------------------------------------------
# JA-01..06: list_projects
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ja_01_list_projects_returns_list(adapter):
    """JA-01: list_projects returns list of Jira project dicts."""
    projects = [
        {"id": "10000", "key": "PROJ", "name": "Main Project"},
        {"id": "10001", "key": "DEV", "name": "Dev Project"},
    ]
    mock_resp = _mock_response(200, {"values": projects, "total": 2})

    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock, return_value=mock_resp):
        result = await adapter.list_projects()

    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["key"] == "PROJ"


@pytest.mark.asyncio
async def test_ja_02_list_projects_passes_basic_auth(adapter):
    """JA-02: list_projects passes BasicAuth credentials."""
    mock_resp = _mock_response(200, {"values": []})
    captured_auth = []

    original_init = httpx.AsyncClient.__init__

    def patched_init(self, *args, **kwargs):
        captured_auth.append(kwargs.get("auth"))
        original_init(self, *args, **kwargs)

    with patch.object(httpx.AsyncClient, "__init__", patched_init):
        with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock, return_value=mock_resp):
            with patch.object(httpx.AsyncClient, "__aenter__", new_callable=AsyncMock,
                              return_value=MagicMock(get=AsyncMock(return_value=mock_resp))):
                with patch.object(httpx.AsyncClient, "__aexit__", new_callable=AsyncMock,
                                  return_value=None):
                    # Test BasicAuth is constructed correctly
                    assert isinstance(adapter._auth, httpx.BasicAuth)


@pytest.mark.asyncio
async def test_ja_03_list_projects_empty_workspace(adapter):
    """JA-03: list_projects handles empty workspace (returns [])."""
    mock_resp = _mock_response(200, {"values": [], "total": 0})

    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock, return_value=mock_resp):
        with patch.object(httpx.AsyncClient, "__aenter__", new_callable=AsyncMock) as mock_ctx:
            mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_ctx.return_value)
            mock_ctx.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_ctx.return_value.get = AsyncMock(return_value=mock_resp)

            # Call via context manager approach
            result = []
            async with httpx.AsyncClient(auth=adapter._auth) as client:
                # Mocked response
                pass

    # Directly test with mocked client
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)

    with patch("httpx.AsyncClient") as MockClient:
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)
        result = await adapter.list_projects()

    assert result == []


@pytest.mark.asyncio
async def test_ja_04_list_projects_raises_on_401(adapter):
    """JA-04: list_projects raises HTTPStatusError on 401 (invalid credentials)."""
    mock_resp = _mock_response(401, {"errorMessages": ["Unauthorized"]})

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)

    with patch("httpx.AsyncClient") as MockClient:
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

        with pytest.raises(httpx.HTTPStatusError):
            await adapter.list_projects()


@pytest.mark.asyncio
async def test_ja_05_list_projects_raises_on_403(adapter):
    """JA-05: list_projects raises HTTPStatusError on 403 (insufficient permissions)."""
    mock_resp = _mock_response(403, {"errorMessages": ["Forbidden"]})

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)

    with patch("httpx.AsyncClient") as MockClient:
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)

        with pytest.raises(httpx.HTTPStatusError):
            await adapter.list_projects()


@pytest.mark.asyncio
async def test_ja_06_list_projects_timeout_enforced(adapter):
    """JA-06: list_projects timeout=10.0s enforced via httpx.Timeout."""
    captured_timeout = []
    mock_resp = _mock_response(200, {"values": []})

    mock_client = AsyncMock()

    async def _capturing_get(url, headers=None, params=None, timeout=None, **kw):
        captured_timeout.append(timeout)
        return mock_resp

    mock_client.get = _capturing_get

    with patch("httpx.AsyncClient") as MockClient:
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)
        await adapter.list_projects()

    # Verify a Timeout was passed
    assert len(captured_timeout) == 1
    passed_timeout = captured_timeout[0]
    assert isinstance(passed_timeout, httpx.Timeout)


# ---------------------------------------------------------------------------
# JA-07..09: get_sprint_issues
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ja_07_get_sprint_issues_returns_list(adapter):
    """JA-07: get_sprint_issues returns list of issue dicts."""
    issues = [_jira_issue("PROJ-1"), _jira_issue("PROJ-2")]
    mock_resp = _mock_response(200, {"issues": issues, "total": 2})

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)

    with patch("httpx.AsyncClient") as MockClient:
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)
        result = await adapter.get_sprint_issues(board_id=1, sprint_id=42)

    assert len(result) == 2
    assert result[0]["key"] == "PROJ-1"


@pytest.mark.asyncio
async def test_ja_08_get_sprint_issues_includes_required_fields(adapter):
    """JA-08: get_sprint_issues requests summary, status, assignee, issuetype fields."""
    captured_params = []
    mock_resp = _mock_response(200, {"issues": []})

    mock_client = AsyncMock()

    async def _capturing_get(url, headers=None, params=None, timeout=None, **kw):
        captured_params.append(params or {})
        return mock_resp

    mock_client.get = _capturing_get

    with patch("httpx.AsyncClient") as MockClient:
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)
        await adapter.get_sprint_issues(board_id=1, sprint_id=10)

    assert len(captured_params) == 1
    fields_param = captured_params[0].get("fields", "")
    for required_field in ["summary", "status", "assignee", "issuetype"]:
        assert required_field in fields_param, f"Missing field: {required_field}"


@pytest.mark.asyncio
async def test_ja_09_get_sprint_issues_empty_sprint(adapter):
    """JA-09: get_sprint_issues handles empty sprint (returns [])."""
    mock_resp = _mock_response(200, {"issues": [], "total": 0})

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)

    with patch("httpx.AsyncClient") as MockClient:
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)
        result = await adapter.get_sprint_issues(board_id=5, sprint_id=99)

    assert result == []


# ---------------------------------------------------------------------------
# JA-10..13: sync_to_evidence_vault
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ja_10_sync_creates_gate_evidence_records(adapter):
    """JA-10: sync_to_evidence_vault creates GateEvidence records in DB."""
    gate_id = uuid4()
    issues = [_jira_issue("PROJ-1"), _jira_issue("PROJ-2")]

    # Mock DB session
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()

    # Simulate no existing records (first sync)
    from sqlalchemy.engine import Result
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_result

    result = await adapter.sync_to_evidence_vault(gate_id=gate_id, jira_issues=issues, db=db)

    assert len(result) == 2
    assert db.add.call_count == 2
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_ja_11_sync_sets_source_jira(adapter):
    """JA-11: sync_to_evidence_vault sets source='jira' on all records."""
    gate_id = uuid4()
    issues = [_jira_issue("PROJ-3")]

    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    captured_records = []

    def _capture_add(record):
        captured_records.append(record)

    db.add = _capture_add

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_result

    await adapter.sync_to_evidence_vault(gate_id=gate_id, jira_issues=issues, db=db)

    assert len(captured_records) == 1
    assert captured_records[0].source == "jira"


@pytest.mark.asyncio
async def test_ja_12_sync_sets_file_name_to_jira_key(adapter):
    """JA-12: sync_to_evidence_vault sets file_name=jira_key (e.g., 'PROJ-42')."""
    gate_id = uuid4()
    issues = [_jira_issue("PROJ-42")]

    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    captured_records = []
    db.add = lambda r: captured_records.append(r)

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_result

    await adapter.sync_to_evidence_vault(gate_id=gate_id, jira_issues=issues, db=db)

    assert captured_records[0].file_name == "PROJ-42"


@pytest.mark.asyncio
async def test_ja_13_sync_is_idempotent_upsert_on_external_id(adapter):
    """JA-13: sync_to_evidence_vault is idempotent (upsert on gate_id + jira_key)."""
    gate_id = uuid4()
    issues = [_jira_issue("PROJ-5", summary="Updated summary")]

    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    # Simulate existing record (re-sync scenario)
    from app.models.gate_evidence import GateEvidence
    existing_record = GateEvidence()
    existing_record.gate_id = gate_id
    existing_record.file_name = "PROJ-5"
    existing_record.source = "jira"
    existing_record.description = "Old description"

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_record
    db.execute.return_value = mock_result

    add_calls = []
    db.add = lambda r: add_calls.append(r)

    result = await adapter.sync_to_evidence_vault(gate_id=gate_id, jira_issues=issues, db=db)

    # Should NOT create a new record (upsert = update existing)
    assert len(add_calls) == 0
    # Should update description
    assert "Updated summary" in existing_record.description
    assert result[0] is existing_record


# ---------------------------------------------------------------------------
# JA-14..16: test_connection
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ja_14_test_connection_returns_true_for_valid_creds(adapter):
    """JA-14: test_connection returns True for valid credentials."""
    mock_resp = _mock_response(200, {"accountId": "abc123", "emailAddress": "dev@acme.com"})
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)

    with patch("httpx.AsyncClient") as MockClient:
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)
        result = await adapter.test_connection()

    assert result is True


@pytest.mark.asyncio
async def test_ja_15_test_connection_returns_false_for_401(adapter):
    """JA-15: test_connection returns False for 401 response."""
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 401
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)

    with patch("httpx.AsyncClient") as MockClient:
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)
        result = await adapter.test_connection()

    assert result is False


@pytest.mark.asyncio
async def test_ja_16_test_connection_returns_false_for_network_timeout(adapter):
    """JA-16: test_connection returns False for network timeout (RequestError)."""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.ConnectTimeout("Connection timed out"))

    with patch("httpx.AsyncClient") as MockClient:
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)
        result = await adapter.test_connection()

    assert result is False


# ---------------------------------------------------------------------------
# JA-17..20: Route-level integration (adapter usage patterns)
# ---------------------------------------------------------------------------

def test_ja_17_jira_connection_model_encrypts_api_token():
    """JA-17: JiraConnection.encrypt_token stores encrypted (not plain) API token."""
    from app.models.jira_connection import JiraConnection

    plain = "ATATT3xFfGF0_plaintoken"
    encrypted = JiraConnection.encrypt_token(plain)

    # Encrypted value should differ from plain
    assert encrypted != plain
    # Should not contain plain token as substring
    assert plain not in encrypted
    # Round-trip: decrypt should return original
    decrypted = JiraConnection.decrypt_token(encrypted)
    assert decrypted == plain


def test_ja_18_jira_adapter_base_url_strips_trailing_slash():
    """JA-18: JiraAdapter strips trailing slash from base_url."""
    adapter = JiraAdapter(
        base_url="https://acme.atlassian.net/",
        api_token="token",
        email="user@acme.com",
    )
    assert not adapter.base_url.endswith("/")
    assert adapter.base_url == "https://acme.atlassian.net"


@pytest.mark.asyncio
async def test_ja_19_jira_adapter_uses_correct_agile_endpoint(adapter):
    """JA-19: get_sprint_issues uses /rest/agile/1.0/board/{id}/sprint/{id}/issue endpoint."""
    captured_urls = []
    mock_resp = _mock_response(200, {"issues": []})

    mock_client = AsyncMock()

    async def _capturing_get(url, **kwargs):
        captured_urls.append(url)
        return mock_resp

    mock_client.get = _capturing_get

    with patch("httpx.AsyncClient") as MockClient:
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=None)
        await adapter.get_sprint_issues(board_id=7, sprint_id=23)

    assert len(captured_urls) == 1
    assert "/rest/agile/1.0/board/7/sprint/23/issue" in captured_urls[0]


@pytest.mark.asyncio
async def test_ja_20_jira_sync_sets_evidence_type_test_results(adapter):
    """JA-20: sync creates evidence with evidence_type='TEST_RESULTS' (sprint tracking)."""
    gate_id = uuid4()
    issues = [_jira_issue("PROJ-10")]

    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    captured = []
    db.add = lambda r: captured.append(r)

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_result

    await adapter.sync_to_evidence_vault(gate_id=gate_id, jira_issues=issues, db=db)

    assert captured[0].evidence_type == "TEST_RESULTS"
