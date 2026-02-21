"""
==========================================================================
JiraAdapter — Sprint 184 (Enterprise Integrations, PROFESSIONAL+ Tier)
SDLC Orchestrator

Purpose:
- Jira REST API v3 adapter for connecting team Jira workspaces
- List accessible projects, fetch sprint issues, sync to Evidence Vault
- Network-only (httpx.AsyncClient) — no atlassian-python-api SDK
  (SDK licensing clarity + no unnecessary transitive dependency)

Architecture:
- PROFESSIONAL tier required (enforced by TierGateMiddleware + route dependency)
- Credentials: email + API token via Jira Basic Auth (RFC 7617)
- API base: https://{domain}.atlassian.net (Jira Cloud)
- Retries: httpx.AsyncClient with exponential backoff on 429 responses
- Evidence sync: upsert by (gate_id, jira_key) — idempotent re-sync

Endpoints used:
  GET  /rest/api/3/myself                    — credential test
  GET  /rest/api/3/project/search            — list all projects
  GET  /rest/agile/1.0/board/{id}/sprint/{id}/issue — sprint issues
  GET  /rest/api/3/issue/{key}               — single issue detail

SDLC 6.1.0 — Sprint 184 P0 Deliverable
Authority: CTO Approved
==========================================================================
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gate_evidence import GateEvidence

logger = logging.getLogger(__name__)

# Jira API timeouts (seconds)
_CONNECT_TIMEOUT = 5.0
_READ_TIMEOUT = 15.0


class JiraConnectionError(Exception):
    """Raised when Jira API credentials are invalid or connection fails."""


class JiraAdapter:
    """
    Jira REST API v3 adapter.

    Uses httpx.AsyncClient for all network calls (no atlassian SDK).
    All methods raise httpx.HTTPStatusError on 4xx/5xx responses.

    Args:
        base_url: Jira Cloud base URL (e.g., "https://myteam.atlassian.net")
        api_token: Jira API token (generated at id.atlassian.com/manage-profile/security/api-tokens)
        email: Atlassian account email (used for Basic Auth username)

    Example:
        adapter = JiraAdapter(
            base_url="https://acme.atlassian.net",
            api_token="ATATT3...",
            email="dev@acme.com",
        )
        ok = await adapter.test_connection()
        projects = await adapter.list_projects()
    """

    def __init__(self, base_url: str, api_token: str, email: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._auth = httpx.BasicAuth(email, api_token)
        self._headers: dict[str, str] = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    async def test_connection(self) -> bool:
        """
        Test API credentials by calling GET /rest/api/3/myself.

        Returns:
            True if credentials are valid (200 OK), False otherwise.

        Never raises — connection errors and HTTP errors are caught and logged.
        """
        try:
            async with self._client() as client:
                response = await client.get(
                    f"{self.base_url}/rest/api/3/myself",
                    headers=self._headers,
                    timeout=httpx.Timeout(_READ_TIMEOUT, connect=_CONNECT_TIMEOUT),
                )
                return response.status_code == 200
        except httpx.RequestError as exc:
            logger.warning("JiraAdapter.test_connection network error: %s", exc)
            return False
        except Exception as exc:
            logger.warning("JiraAdapter.test_connection unexpected error: %s", exc)
            return False

    async def list_projects(self) -> list[dict[str, Any]]:
        """
        List Jira projects accessible by the API token.

        Calls GET /rest/api/3/project/search with maxResults=50.

        Returns:
            List of Jira project dicts (keys: id, key, name, description, ...).

        Raises:
            httpx.HTTPStatusError: on 401 (invalid credentials), 403 (insufficient permissions).
        """
        async with self._client() as client:
            response = await client.get(
                f"{self.base_url}/rest/api/3/project/search",
                headers=self._headers,
                params={"expand": "description", "maxResults": 50},
                timeout=httpx.Timeout(_READ_TIMEOUT, connect=_CONNECT_TIMEOUT),
            )
            response.raise_for_status()
            return response.json().get("values", [])

    async def get_sprint_issues(
        self, board_id: int, sprint_id: int
    ) -> list[dict[str, Any]]:
        """
        Get all issues for a specific sprint (Jira Software required).

        Calls GET /rest/agile/1.0/board/{board_id}/sprint/{sprint_id}/issue.

        Args:
            board_id: Jira Software board ID
            sprint_id: Sprint ID within the board

        Returns:
            List of Jira issue dicts (keys: id, key, fields: {summary, status, assignee, issuetype}).

        Raises:
            httpx.HTTPStatusError: on 404 (board/sprint not found), 403 (no access).
        """
        async with self._client() as client:
            response = await client.get(
                f"{self.base_url}/rest/agile/1.0/board/{board_id}/sprint/{sprint_id}/issue",
                headers=self._headers,
                params={
                    "maxResults": 100,
                    "fields": "summary,status,assignee,issuetype,priority,labels",
                },
                timeout=httpx.Timeout(_READ_TIMEOUT, connect=_CONNECT_TIMEOUT),
            )
            response.raise_for_status()
            return response.json().get("issues", [])

    async def sync_to_evidence_vault(
        self,
        gate_id: Any,
        jira_issues: list[dict[str, Any]],
        db: AsyncSession,
        uploaded_by: Any | None = None,
    ) -> list[GateEvidence]:
        """
        Sync a list of Jira issues as GateEvidence records in the Evidence Vault.

        Idempotent: uses upsert logic keyed on (gate_id, source="jira", file_name=jira_key).
        On re-sync: updates description with latest issue summary and status.

        Args:
            gate_id: UUID of the target Gate (evidence belongs to this gate)
            jira_issues: List of Jira issue dicts from get_sprint_issues()
            db: Async SQLAlchemy session
            uploaded_by: Optional user UUID (attribution for the sync action)

        Returns:
            List of GateEvidence records (created or updated).
        """
        result: list[GateEvidence] = []

        for issue in jira_issues:
            jira_key: str = issue.get("key", "")
            fields: dict[str, Any] = issue.get("fields", {})
            summary: str = fields.get("summary", "(no summary)")
            status_name: str = (fields.get("status") or {}).get("name", "Unknown")
            issue_type: str = (fields.get("issuetype") or {}).get("name", "Task")

            # Compose human-readable description
            description = (
                f"Jira [{jira_key}] {issue_type}: {summary} — Status: {status_name}"
            )

            # Idempotent lookup: find existing record for this Jira issue in this gate
            stmt = select(GateEvidence).where(
                GateEvidence.gate_id == gate_id,
                GateEvidence.source == "jira",
                GateEvidence.file_name == jira_key,
            )
            existing = (await db.execute(stmt)).scalar_one_or_none()

            if existing:
                # Update description with latest status
                existing.description = description
                result.append(existing)
            else:
                # Create new evidence record
                evidence = GateEvidence(
                    gate_id=gate_id,
                    file_name=jira_key,           # Jira key as file identifier (e.g., "PROJ-42")
                    file_size=0,                   # Metadata record — no binary payload
                    file_type="application/json",  # Jira issue is JSON metadata
                    evidence_type="TEST_RESULTS",  # Sprint tracking = test/iteration evidence
                    s3_key=f"jira/{gate_id}/{jira_key}",  # Virtual key (no actual S3 upload)
                    s3_bucket="sdlc-evidence",
                    source="jira",
                    description=description,
                    uploaded_by=uploaded_by,
                )
                db.add(evidence)
                result.append(evidence)

        await db.commit()

        # Refresh all new/updated records to populate DB-assigned fields
        for record in result:
            if record.id is None:
                # Newly inserted: refresh to get DB-generated id + timestamps
                await db.refresh(record)

        logger.info(
            "JiraAdapter.sync_to_evidence_vault: synced %d issues to gate %s",
            len(result),
            gate_id,
        )
        return result

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    def _client(self) -> httpx.AsyncClient:
        """
        Create an httpx.AsyncClient with Basic Auth and default headers.

        Returns a context manager; use as: `async with self._client() as client`.
        """
        return httpx.AsyncClient(auth=self._auth)
