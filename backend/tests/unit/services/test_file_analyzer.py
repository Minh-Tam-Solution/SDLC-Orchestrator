"""
=========================================================================
Unit Tests - FileAnalyzer
SDLC Orchestrator - Sprint 80 (AGENTS.md Integration)

Version: 1.0.0
Date: January 19, 2026
Status: ACTIVE - Sprint 80 Implementation
Authority: QA Lead + Backend Lead Approved
Reference: TDS-080-001 AGENTS.md Technical Design

Purpose:
- Test project structure analysis
- Test framework detection
- Test Docker Compose parsing
- Test AGPL dependency detection

Coverage Target: 95%+
=========================================================================
"""

import pytest
import tempfile
import json
import os
from pathlib import Path
from uuid import uuid4

from app.services.file_analyzer import FileAnalyzer, ProjectAnalysis


class TestFileAnalyzer:
    """Test FileAnalyzer service."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def analyzer(self, temp_project):
        """Create FileAnalyzer instance."""
        return FileAnalyzer(str(temp_project))

    @pytest.fixture
    def project_id(self):
        """Generate a test project ID."""
        return uuid4()


class TestDockerAnalysis(TestFileAnalyzer):
    """Test Docker-related analysis."""

    @pytest.mark.asyncio
    async def test_detect_docker_compose_yml(self, temp_project, analyzer, project_id):
        """Test detection of docker-compose.yml."""
        # Create docker-compose.yml
        compose_content = """
version: '3.8'
services:
  backend:
    build: ./backend
  frontend:
    build: ./frontend
"""
        (temp_project / "docker-compose.yml").write_text(compose_content)

        result = await analyzer.analyze_project(project_id, str(temp_project))

        assert result.has_docker_compose
        assert "backend" in result.docker_services
        assert "frontend" in result.docker_services

    @pytest.mark.asyncio
    async def test_detect_docker_compose_yaml(self, temp_project, analyzer, project_id):
        """Test detection of docker-compose.yaml (alternative extension)."""
        compose_content = """
version: '3.8'
services:
  api:
    image: python:3.11
"""
        (temp_project / "docker-compose.yaml").write_text(compose_content)

        result = await analyzer.analyze_project(project_id, str(temp_project))

        assert result.has_docker_compose
        assert "api" in result.docker_services

    @pytest.mark.asyncio
    async def test_detect_dockerfile(self, temp_project, analyzer, project_id):
        """Test detection of Dockerfile."""
        (temp_project / "Dockerfile").write_text("FROM python:3.11")

        result = await analyzer.analyze_project(project_id, str(temp_project))

        assert result.has_dockerfile

    @pytest.mark.asyncio
    async def test_no_docker(self, temp_project, analyzer, project_id):
        """Test project without Docker."""
        (temp_project / "README.md").write_text("# Test Project")

        result = await analyzer.analyze_project(project_id, str(temp_project))

        assert not result.has_docker_compose
        assert not result.has_dockerfile


class TestDatabaseDetection(TestFileAnalyzer):
    """Test database detection from docker-compose."""

    @pytest.mark.asyncio
    async def test_detect_postgresql(self, temp_project, analyzer, project_id):
        """Test PostgreSQL detection."""
        compose_content = """
version: '3.8'
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: test
"""
        (temp_project / "docker-compose.yml").write_text(compose_content)

        result = await analyzer.analyze_project(project_id, str(temp_project))

        assert result.has_database
        assert result.database_type == "postgresql"

    @pytest.mark.asyncio
    async def test_detect_mysql(self, temp_project, analyzer, project_id):
        """Test MySQL detection."""
        compose_content = """
version: '3.8'
services:
  mysql:
    image: mysql:8.0
"""
        (temp_project / "docker-compose.yml").write_text(compose_content)

        result = await analyzer.analyze_project(project_id, str(temp_project))

        assert result.has_database
        assert result.database_type == "mysql"

    @pytest.mark.asyncio
    async def test_detect_mongodb(self, temp_project, analyzer, project_id):
        """Test MongoDB detection."""
        compose_content = """
version: '3.8'
services:
  mongo:
    image: mongo:6.0
"""
        (temp_project / "docker-compose.yml").write_text(compose_content)

        result = await analyzer.analyze_project(project_id, str(temp_project))

        assert result.has_database
        assert result.database_type == "mongodb"


class TestBackendDetection(TestFileAnalyzer):
    """Test backend framework detection."""

    @pytest.mark.asyncio
    async def test_detect_python_requirements(self, temp_project, analyzer, project_id):
        """Test Python project with requirements.txt."""
        backend_dir = temp_project / "backend"
        backend_dir.mkdir()
        (backend_dir / "requirements.txt").write_text("fastapi\nuvicorn")

        result = await analyzer.analyze_project(project_id, str(temp_project))

        assert result.backend_type == "python"
        assert result.has_requirements
        assert result.backend_path == "backend"

    @pytest.mark.asyncio
    async def test_detect_python_poetry(self, temp_project, analyzer, project_id):
        """Test Python project with poetry."""
        (temp_project / "pyproject.toml").write_text("[tool.poetry]\nname = 'test'")
        (temp_project / "poetry.lock").write_text("# lock file")

        result = await analyzer.analyze_project(project_id, str(temp_project))

        assert result.backend_type == "python"
        assert result.has_poetry

    @pytest.mark.asyncio
    async def test_detect_node_backend(self, temp_project, analyzer, project_id):
        """Test Node.js backend detection."""
        backend_dir = temp_project / "api"
        backend_dir.mkdir()
        (backend_dir / "package.json").write_text('{"name": "api"}')

        result = await analyzer.analyze_project(project_id, str(temp_project))

        assert result.backend_type == "node"


class TestFrontendDetection(TestFileAnalyzer):
    """Test frontend framework detection."""

    @pytest.mark.asyncio
    async def test_detect_react(self, temp_project, analyzer, project_id):
        """Test React frontend detection."""
        frontend_dir = temp_project / "frontend"
        frontend_dir.mkdir()
        package = {
            "name": "frontend",
            "dependencies": {
                "react": "^18.0.0",
                "react-dom": "^18.0.0",
            },
        }
        (frontend_dir / "package.json").write_text(json.dumps(package))

        result = await analyzer.analyze_project(project_id, str(temp_project))

        assert result.frontend_type == "react"
        assert result.frontend_path == "frontend"

    @pytest.mark.asyncio
    async def test_detect_vue(self, temp_project, analyzer, project_id):
        """Test Vue.js frontend detection."""
        frontend_dir = temp_project / "frontend" / "web"
        frontend_dir.mkdir(parents=True)
        package = {
            "name": "web",
            "dependencies": {
                "vue": "^3.0.0",
            },
        }
        (frontend_dir / "package.json").write_text(json.dumps(package))

        result = await analyzer.analyze_project(project_id, str(temp_project))

        assert result.frontend_type == "vue"

    @pytest.mark.asyncio
    async def test_detect_angular(self, temp_project, analyzer, project_id):
        """Test Angular frontend detection."""
        frontend_dir = temp_project / "client"
        frontend_dir.mkdir()
        package = {
            "name": "client",
            "dependencies": {
                "@angular/core": "^17.0.0",
            },
        }
        (frontend_dir / "package.json").write_text(json.dumps(package))

        result = await analyzer.analyze_project(project_id, str(temp_project))

        assert result.frontend_type == "angular"

    @pytest.mark.asyncio
    async def test_detect_nextjs(self, temp_project, analyzer, project_id):
        """Test Next.js detection."""
        package = {
            "name": "app",
            "dependencies": {
                "next": "^14.0.0",
                "react": "^18.0.0",
            },
        }
        (temp_project / "package.json").write_text(json.dumps(package))

        result = await analyzer.analyze_project(project_id, str(temp_project))

        assert result.frontend_type == "nextjs"


class TestConfigDetection(TestFileAnalyzer):
    """Test configuration file detection."""

    @pytest.mark.asyncio
    async def test_detect_tsconfig(self, temp_project, analyzer, project_id):
        """Test TypeScript config detection."""
        (temp_project / "tsconfig.json").write_text('{"compilerOptions": {}}')

        result = await analyzer.analyze_project(project_id, str(temp_project))

        assert result.has_tsconfig

    @pytest.mark.asyncio
    async def test_detect_ruff(self, temp_project, analyzer, project_id):
        """Test ruff config detection."""
        (temp_project / "ruff.toml").write_text("[tool.ruff]")

        result = await analyzer.analyze_project(project_id, str(temp_project))

        assert result.has_ruff

    @pytest.mark.asyncio
    async def test_detect_eslint(self, temp_project, analyzer, project_id):
        """Test ESLint config detection."""
        (temp_project / ".eslintrc.json").write_text('{"rules": {}}')

        result = await analyzer.analyze_project(project_id, str(temp_project))

        assert result.has_eslint

    @pytest.mark.asyncio
    async def test_detect_prettier(self, temp_project, analyzer, project_id):
        """Test Prettier config detection."""
        (temp_project / ".prettierrc").write_text('{"semi": true}')

        result = await analyzer.analyze_project(project_id, str(temp_project))

        assert result.has_prettier


class TestAGPLDetection(TestFileAnalyzer):
    """Test AGPL dependency detection."""

    @pytest.mark.asyncio
    async def test_detect_minio(self, temp_project, analyzer, project_id):
        """Test MinIO detection in docker-compose."""
        compose_content = """
version: '3.8'
services:
  minio:
    image: minio/minio:latest
    ports:
      - "9000:9000"
"""
        (temp_project / "docker-compose.yml").write_text(compose_content)

        result = await analyzer.analyze_project(project_id, str(temp_project))

        assert result.has_minio
        assert result.has_agpl_deps

    @pytest.mark.asyncio
    async def test_detect_grafana(self, temp_project, analyzer, project_id):
        """Test Grafana detection in docker-compose."""
        compose_content = """
version: '3.8'
services:
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
"""
        (temp_project / "docker-compose.yml").write_text(compose_content)

        result = await analyzer.analyze_project(project_id, str(temp_project))

        assert result.has_grafana
        assert result.has_agpl_deps

    @pytest.mark.asyncio
    async def test_no_agpl_deps(self, temp_project, analyzer, project_id):
        """Test project without AGPL dependencies."""
        compose_content = """
version: '3.8'
services:
  redis:
    image: redis:7
"""
        (temp_project / "docker-compose.yml").write_text(compose_content)

        result = await analyzer.analyze_project(project_id, str(temp_project))

        assert not result.has_minio
        assert not result.has_grafana
        assert not result.has_agpl_deps


class TestCICDDetection(TestFileAnalyzer):
    """Test CI/CD configuration detection."""

    @pytest.mark.asyncio
    async def test_detect_github_actions(self, temp_project, analyzer, project_id):
        """Test GitHub Actions detection."""
        workflows_dir = temp_project / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        (workflows_dir / "ci.yml").write_text("name: CI")

        result = await analyzer.analyze_project(project_id, str(temp_project))

        assert result.has_github_actions

    @pytest.mark.asyncio
    async def test_detect_gitlab_ci(self, temp_project, analyzer, project_id):
        """Test GitLab CI detection."""
        (temp_project / ".gitlab-ci.yml").write_text("stages: [build]")

        result = await analyzer.analyze_project(project_id, str(temp_project))

        assert result.has_gitlab_ci


class TestDocumentation(TestFileAnalyzer):
    """Test documentation detection."""

    @pytest.mark.asyncio
    async def test_detect_docs_folder(self, temp_project, analyzer, project_id):
        """Test docs folder detection."""
        (temp_project / "docs").mkdir()
        (temp_project / "docs" / "index.md").write_text("# Docs")

        result = await analyzer.analyze_project(project_id, str(temp_project))

        assert result.has_docs_folder

    @pytest.mark.asyncio
    async def test_detect_readme(self, temp_project, analyzer, project_id):
        """Test README detection."""
        (temp_project / "README.md").write_text("# Project")

        result = await analyzer.analyze_project(project_id, str(temp_project))

        assert result.has_readme


class TestProjectAnalysisModel:
    """Test ProjectAnalysis dataclass."""

    def test_to_dict(self):
        """Test to_dict serialization."""
        analysis = ProjectAnalysis(
            project_id=uuid4(),
            project_path="/test",
            analyzed_at="2026-01-19T00:00:00",
            has_docker_compose=True,
            docker_services=["backend", "db"],
            backend_type="python",
        )

        result = analysis.to_dict()

        assert result["has_docker_compose"] is True
        assert result["docker_services"] == ["backend", "db"]
        assert result["backend_type"] == "python"


class TestPathSecurity(TestFileAnalyzer):
    """Test path traversal security."""

    @pytest.mark.asyncio
    async def test_path_traversal_blocked(self, temp_project, analyzer, project_id):
        """Test that path traversal is blocked."""
        with pytest.raises(ValueError, match="traversal"):
            await analyzer.read(project_id, "../../../etc/passwd")

    @pytest.mark.asyncio
    async def test_file_not_found(self, temp_project, analyzer, project_id):
        """Test FileNotFoundError for missing files."""
        with pytest.raises(FileNotFoundError):
            await analyzer.read(project_id, "nonexistent.txt")
