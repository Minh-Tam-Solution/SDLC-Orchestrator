"""
Integration Tests for POST /projects/{id}/sync API Endpoint

Sprint 172 - Project Metadata Auto-Sync
Framework: SDLC 6.0.5

NOTE: These tests require a live PostgreSQL database (sdlc_orchestrator_test).
They will be SKIPPED when the database is unavailable.

For tests that run WITHOUT a database, see:
  tests/unit/api/routes/test_project_sync.py  (7 tests, ~0.08s)
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project, ProjectMember
from app.services import cache_service as cache_service_module


@pytest.mark.asyncio
async def test_sync_project_metadata_success(
    client,
    auth_headers,
    db_session: AsyncSession,
    monkeypatch,
):
    project_id = uuid4()
    owner_id = uuid4()

    project = Project(
        id=project_id,
        name="Old Name",
        slug="test-project",
        description="Old desc",
        owner_id=owner_id,
        is_active=True,
    )
    db_session.add(project)
    await db_session.flush()

    # Make the logged-in test_user a project member
    me = (await client.get("/api/v1/auth/me", headers=auth_headers)).json()
    member = ProjectMember(project_id=project_id, user_id=me["id"], role="member")
    db_session.add(member)
    await db_session.commit()

    class _FakeMetadata:
        name = "New Name"
        description = "New desc"
        tier = "professional"
        current_sprint = "Sprint 171"
        sprint_status = "✅ 90% COMPLETE"
        sprint_description = "Market Expansion"
        framework_version = "SDLC 6.0.5"
        gate_status = "Gate G3 APPROVED"
        last_commit_date = datetime.utcnow().isoformat()
        last_commit_sha = "deadbeef"

    async def _fake_sync_project_metadata(*, project_id, repo_path):
        return _FakeMetadata()

    # Avoid touching filesystem/git
    from app.api.routes import projects as projects_routes

    monkeypatch.setattr(
        projects_routes.project_metadata_service,
        "sync_project_metadata",
        _fake_sync_project_metadata,
    )

    # Ensure cache miss
    async def _cache_get(_key):
        return None

    async def _cache_set(_key, _value, ttl=0):
        return True

    monkeypatch.setattr(cache_service_module.cache_service, "get", _cache_get)
    monkeypatch.setattr(cache_service_module.cache_service, "set", _cache_set)

    resp = await client.post(f"/api/v1/projects/{project_id}/sync", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == str(project_id)
    assert body["name"] == "New Name"
    assert body["description"] == "New desc"
    assert body["metadata"]["framework_version"] == "SDLC 6.0.5"


@pytest.mark.asyncio
async def test_sync_project_metadata_cache_hit_returns_cached(
    client,
    auth_headers,
    db_session: AsyncSession,
    monkeypatch,
):
    project_id = uuid4()
    owner_id = uuid4()

    project = Project(
        id=project_id,
        name="Name",
        slug="test-project",
        description="Desc",
        owner_id=owner_id,
        is_active=True,
    )
    db_session.add(project)
    await db_session.flush()

    me = (await client.get("/api/v1/auth/me", headers=auth_headers)).json()
    db_session.add(ProjectMember(project_id=project_id, user_id=me["id"], role="member"))
    await db_session.commit()

    cached_payload = {"id": str(project_id), "name": "Cached", "slug": "test-project"}

    async def _cache_get(_key):
        return cached_payload

    monkeypatch.setattr(cache_service_module.cache_service, "get", _cache_get)

    # If service gets called, that's a bug on cache hit
    from app.api.routes import projects as projects_routes

    async def _boom(*args, **kwargs):
        raise AssertionError("service should not run on cache hit")

    monkeypatch.setattr(projects_routes.project_metadata_service, "sync_project_metadata", _boom)

    resp = await client.post(f"/api/v1/projects/{project_id}/sync", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == cached_payload


@pytest.mark.asyncio
async def test_sync_project_metadata_not_member_forbidden(
    client,
    auth_headers,
    db_session: AsyncSession,
):
    project_id = uuid4()
    owner_id = uuid4()

    project = Project(
        id=project_id,
        name="Name",
        slug="test-project",
        description="Desc",
        owner_id=owner_id,
        is_active=True,
    )
    db_session.add(project)
    await db_session.commit()

    resp = await client.post(f"/api/v1/projects/{project_id}/sync", headers=auth_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_sync_project_metadata_repo_not_found_maps_404(
    client,
    auth_headers,
    db_session: AsyncSession,
    monkeypatch,
):
    project_id = uuid4()
    owner_id = uuid4()

    project = Project(
        id=project_id,
        name="Name",
        slug="missing-repo",
        description="Desc",
        owner_id=owner_id,
        is_active=True,
    )
    db_session.add(project)
    await db_session.flush()

    me = (await client.get("/api/v1/auth/me", headers=auth_headers)).json()
    db_session.add(ProjectMember(project_id=project_id, user_id=me["id"], role="member"))
    await db_session.commit()

    from app.api.routes import projects as projects_routes

    async def _raise_not_found(*, project_id, repo_path):
        raise FileNotFoundError("no such repo")

    monkeypatch.setattr(
        projects_routes.project_metadata_service,
        "sync_project_metadata",
        _raise_not_found,
    )

    # Ensure cache miss
    async def _cache_get(_key):
        return None

    monkeypatch.setattr(cache_service_module.cache_service, "get", _cache_get)

    resp = await client.post(f"/api/v1/projects/{project_id}/sync", headers=auth_headers)
    assert resp.status_code == 404
    assert "Repository not found" in resp.json()["detail"]
