"""
Unit Tests for POST /projects/{id}/sync API Endpoint

Sprint 172 - Project Metadata Auto-Sync
Framework: SDLC 6.0.5

Tests the sync endpoint behavior via FastAPI dependency overrides.
No PostgreSQL or Redis required — fully mocked at the dependency layer.

Test Coverage:
- 200 success (metadata service returns valid data)
- 200 cache hit (returns cached payload, skips service call)
- 403 non-member forbidden
- 404 project not found
- 404 repository not found (FileNotFoundError from service)
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.db.session import get_db
from app.api.dependencies import get_current_user
from app.models.project import Project, ProjectMember
from app.models.user import User
from app.services.project_metadata_service import ProjectMetadata


# =============================================================================
# Helpers
# =============================================================================


def _make_mock_user(*, user_id=None, is_superuser=False, is_platform_admin=False):
    """Create a mock User with the fields the endpoint inspects."""
    user = MagicMock(spec=User)
    user.id = user_id or uuid4()
    user.email = "dev@example.com"
    user.is_superuser = is_superuser
    user.is_platform_admin = is_platform_admin
    return user


def _make_mock_project(*, project_id=None, name="Test Project", slug="test-project"):
    """Create a mock Project with the fields the endpoint reads/writes."""
    project = MagicMock(spec=Project)
    project.id = project_id or uuid4()
    project.name = name
    project.slug = slug
    project.description = "Old description"
    project.owner_id = uuid4()
    project.is_active = True
    project.deleted_at = None
    project.created_at = datetime(2025, 12, 1)
    project.updated_at = datetime(2025, 12, 1)
    return project


def _make_fake_metadata(**overrides):
    """Build a ProjectMetadata with sensible defaults."""
    defaults = {
        "id": uuid4(),
        "name": "Synced Name",
        "tier": "professional",
        "current_sprint": "Sprint 171",
        "sprint_status": "90% COMPLETE",
        "sprint_description": "Market Expansion Foundation",
        "framework_version": "SDLC 6.0.5",
        "gate_status": "Gate G3 APPROVED - Ship Ready (98.2%)",
        "description": "Synced description from README",
        "last_commit_date": "2026-02-10T18:00:00",
        "last_commit_sha": "abc1234",
    }
    defaults.update(overrides)
    return ProjectMetadata(**defaults)


def _mock_db_session(project, member):
    """
    Build an AsyncMock db session whose .execute() returns
    the right scalar results for the two SELECT queries the endpoint runs:
      1st call → Project lookup
      2nd call → ProjectMember lookup
    """
    db = AsyncMock()

    project_result = MagicMock()
    project_result.scalar_one_or_none.return_value = project

    member_result = MagicMock()
    member_result.scalar_one_or_none.return_value = member

    db.execute = AsyncMock(side_effect=[project_result, member_result])
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    return db


# =============================================================================
# Tests
# =============================================================================


class TestSyncProjectMetadata:
    """Tests for POST /api/v1/projects/{id}/sync."""

    @pytest.mark.asyncio
    async def test_sync_success_returns_200_with_metadata(self):
        """Successful sync updates project and returns metadata payload."""
        project_id = uuid4()
        user = _make_mock_user()
        project = _make_mock_project(project_id=project_id)
        member = MagicMock(spec=ProjectMember)
        db = _mock_db_session(project, member)
        metadata = _make_fake_metadata()

        async def override_get_db():
            yield db

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = lambda: user

        try:
            with patch(
                "app.api.routes.projects.project_metadata_service"
            ) as mock_svc, patch(
                "app.api.routes.projects.cache_service"
            ) as mock_cache, patch(
                "app.api.routes.projects.invalidate_projects_cache",
                new_callable=AsyncMock,
            ):
                mock_svc.sync_project_metadata = AsyncMock(return_value=metadata)
                mock_cache._make_key = MagicMock(return_value="test:cache:key")
                mock_cache.get = AsyncMock(return_value=None)  # cache miss
                mock_cache.set = AsyncMock()

                transport = ASGITransport(app=app)
                async with AsyncClient(
                    transport=transport, base_url="http://testserver"
                ) as client:
                    resp = await client.post(
                        f"/api/v1/projects/{project_id}/sync"
                    )

                assert resp.status_code == 200
                body = resp.json()
                assert body["id"] == str(project_id)
                assert body["metadata"]["framework_version"] == "SDLC 6.0.5"
                assert body["metadata"]["current_sprint"] == "Sprint 171"
                assert body["metadata"]["tier"] == "professional"
                assert body["metadata"]["gate_status"] == "Gate G3 APPROVED - Ship Ready (98.2%)"

                # Verify service was called
                mock_svc.sync_project_metadata.assert_awaited_once()

                # Verify cache was set
                mock_cache.set.assert_awaited_once()
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_sync_cache_hit_skips_service(self):
        """When cache holds a recent result, return it without calling the service."""
        project_id = uuid4()
        user = _make_mock_user()
        project = _make_mock_project(project_id=project_id)
        member = MagicMock(spec=ProjectMember)
        db = _mock_db_session(project, member)

        cached_payload = {
            "id": str(project_id),
            "name": "Cached Name",
            "slug": "cached",
            "metadata": {"framework_version": "cached"},
        }

        async def override_get_db():
            yield db

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = lambda: user

        try:
            with patch(
                "app.api.routes.projects.project_metadata_service"
            ) as mock_svc, patch(
                "app.api.routes.projects.cache_service"
            ) as mock_cache:
                mock_cache._make_key = MagicMock(return_value="test:cache:key")
                mock_cache.get = AsyncMock(return_value=cached_payload)  # cache hit

                # Service should never be called
                mock_svc.sync_project_metadata = AsyncMock(
                    side_effect=AssertionError("service must not run on cache hit")
                )

                transport = ASGITransport(app=app)
                async with AsyncClient(
                    transport=transport, base_url="http://testserver"
                ) as client:
                    resp = await client.post(
                        f"/api/v1/projects/{project_id}/sync"
                    )

                assert resp.status_code == 200
                assert resp.json() == cached_payload
                mock_svc.sync_project_metadata.assert_not_awaited()
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_sync_non_member_returns_403(self):
        """Users who are not project members get 403 Forbidden."""
        project_id = uuid4()
        user = _make_mock_user()
        project = _make_mock_project(project_id=project_id)
        db = _mock_db_session(project, member=None)  # no membership

        async def override_get_db():
            yield db

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = lambda: user

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://testserver"
            ) as client:
                resp = await client.post(
                    f"/api/v1/projects/{project_id}/sync"
                )

            assert resp.status_code == 403
            assert "permission" in resp.json()["detail"].lower()
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_sync_project_not_found_returns_404(self):
        """Non-existent project_id returns 404."""
        project_id = uuid4()
        user = _make_mock_user()
        db = _mock_db_session(project=None, member=None)  # project not found

        async def override_get_db():
            yield db

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = lambda: user

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://testserver"
            ) as client:
                resp = await client.post(
                    f"/api/v1/projects/{project_id}/sync"
                )

            assert resp.status_code == 404
            assert "not found" in resp.json()["detail"].lower()
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_sync_repo_not_found_returns_404(self):
        """When service raises FileNotFoundError, endpoint returns 404."""
        project_id = uuid4()
        user = _make_mock_user()
        project = _make_mock_project(project_id=project_id)
        member = MagicMock(spec=ProjectMember)
        db = _mock_db_session(project, member)

        async def override_get_db():
            yield db

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = lambda: user

        try:
            with patch(
                "app.api.routes.projects.project_metadata_service"
            ) as mock_svc, patch(
                "app.api.routes.projects.cache_service"
            ) as mock_cache:
                mock_cache._make_key = MagicMock(return_value="test:cache:key")
                mock_cache.get = AsyncMock(return_value=None)  # cache miss
                mock_svc.sync_project_metadata = AsyncMock(
                    side_effect=FileNotFoundError("/home/nqh/shared/missing-repo")
                )

                transport = ASGITransport(app=app)
                async with AsyncClient(
                    transport=transport, base_url="http://testserver"
                ) as client:
                    resp = await client.post(
                        f"/api/v1/projects/{project_id}/sync"
                    )

                assert resp.status_code == 404
                assert "Repository not found" in resp.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_sync_regular_admin_bypasses_membership(self):
        """Regular admins (non-platform) can sync without being a member."""
        project_id = uuid4()
        user = _make_mock_user(is_superuser=True, is_platform_admin=False)
        project = _make_mock_project(project_id=project_id)
        db = _mock_db_session(project, member=None)  # not a member
        metadata = _make_fake_metadata()

        async def override_get_db():
            yield db

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = lambda: user

        try:
            with patch(
                "app.api.routes.projects.project_metadata_service"
            ) as mock_svc, patch(
                "app.api.routes.projects.cache_service"
            ) as mock_cache, patch(
                "app.api.routes.projects.invalidate_projects_cache",
                new_callable=AsyncMock,
            ):
                mock_svc.sync_project_metadata = AsyncMock(return_value=metadata)
                mock_cache._make_key = MagicMock(return_value="test:cache:key")
                mock_cache.get = AsyncMock(return_value=None)
                mock_cache.set = AsyncMock()

                transport = ASGITransport(app=app)
                async with AsyncClient(
                    transport=transport, base_url="http://testserver"
                ) as client:
                    resp = await client.post(
                        f"/api/v1/projects/{project_id}/sync"
                    )

                # Regular admin should succeed despite no membership
                assert resp.status_code == 200
                assert resp.json()["metadata"]["framework_version"] == "SDLC 6.0.5"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_sync_platform_admin_without_membership_returns_403(self):
        """Platform admins CANNOT bypass membership (Sprint 88 policy)."""
        project_id = uuid4()
        user = _make_mock_user(is_superuser=True, is_platform_admin=True)
        project = _make_mock_project(project_id=project_id)
        db = _mock_db_session(project, member=None)

        async def override_get_db():
            yield db

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = lambda: user

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(
                transport=transport, base_url="http://testserver"
            ) as client:
                resp = await client.post(
                    f"/api/v1/projects/{project_id}/sync"
                )

            assert resp.status_code == 403
        finally:
            app.dependency_overrides.clear()
