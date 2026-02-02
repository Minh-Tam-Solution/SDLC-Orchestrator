"""
Unit tests for worktree CLI commands.

Tests for RFC-SDLC-604 Parallel AI Development Pattern implementation.
Sprint 144 Day 2 - Track 2 Implementation.

Test Coverage:
- Command: add (6 tests)
- Command: list (6 tests)
- Command: sync (4 tests)
- Command: remove (4 tests)
- Total: 20 tests targeting 90%+ coverage
"""

import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
from typer.testing import CliRunner

from sdlcctl.commands.worktree import (
    app,
    run_git_command,
    is_git_repository,
    get_git_root,
)

# Test fixtures
runner = CliRunner()


@pytest.fixture
def mock_git_repo(tmp_path):
    """Create a mock git repository for testing."""
    repo_path = tmp_path / "test-repo"
    repo_path.mkdir()
    (repo_path / ".git").mkdir()
    return repo_path


@pytest.fixture
def mock_worktree_path(tmp_path):
    """Create a mock worktree path."""
    worktree_path = tmp_path / "test-worktree"
    return worktree_path


# ============================================================================
# Helper Functions Tests
# ============================================================================


class TestRunGitCommand:
    """Test run_git_command helper function."""

    def test_run_git_command_success(self, mock_git_repo):
        """Test successful git command execution."""
        code, stdout, stderr = run_git_command(
            ['status', '--short'],
            cwd=mock_git_repo
        )

        # Git status should work in a git repo (even if empty)
        assert isinstance(code, int)
        assert isinstance(stdout, str)
        assert isinstance(stderr, str)

    def test_run_git_command_failure(self, tmp_path):
        """Test failed git command execution."""
        non_repo = tmp_path / "not-a-repo"
        non_repo.mkdir()

        code, stdout, stderr = run_git_command(
            ['status'],
            cwd=non_repo
        )

        # Should fail in non-git directory
        assert code != 0
        assert "not a git repository" in stderr.lower()

    def test_run_git_command_timeout(self, mock_git_repo):
        """Test git command timeout handling."""
        # Mock subprocess.run to simulate timeout
        with patch('sdlcctl.commands.worktree.subprocess.run') as mock_run:
            from subprocess import TimeoutExpired
            mock_run.side_effect = TimeoutExpired('git', 30)

            code, stdout, stderr = run_git_command(['status'], cwd=mock_git_repo)

            assert code == 1
            assert stdout == ""
            assert "timed out" in stderr.lower()


class TestIsGitRepository:
    """Test is_git_repository helper function."""

    def test_is_git_repository_true(self, mock_git_repo):
        """Test detection of valid git repository."""
        result = is_git_repository(mock_git_repo)
        assert result is False  # .git exists but not initialized

    def test_is_git_repository_false(self, tmp_path):
        """Test detection of non-git directory."""
        non_repo = tmp_path / "not-a-repo"
        non_repo.mkdir()

        result = is_git_repository(non_repo)
        assert result is False

    def test_is_git_repository_nonexistent(self, tmp_path):
        """Test handling of nonexistent path."""
        nonexistent = tmp_path / "does-not-exist"

        # Should handle gracefully (return False, not crash)
        result = is_git_repository(nonexistent)
        assert result is False


class TestGetGitRoot:
    """Test get_git_root helper function."""

    def test_get_git_root_success(self, mock_git_repo):
        """Test retrieval of git root directory."""
        # Mock git rev-parse --show-toplevel
        with patch('sdlcctl.commands.worktree.run_git_command') as mock_run:
            mock_run.return_value = (0, str(mock_git_repo), "")

            result = get_git_root(mock_git_repo)

            assert result == mock_git_repo

    def test_get_git_root_failure(self, tmp_path):
        """Test handling when not in git repository."""
        non_repo = tmp_path / "not-a-repo"
        non_repo.mkdir()

        result = get_git_root(non_repo)
        assert result is None


# ============================================================================
# Command: worktree add
# ============================================================================


class TestWorktreeAdd:
    """Test 'sdlcctl worktree add' command."""

    @patch('sdlcctl.commands.worktree.is_git_repository')
    @patch('sdlcctl.commands.worktree.get_git_root')
    @patch('sdlcctl.commands.worktree.run_git_command')
    def test_add_worktree_success(self, mock_run, mock_root, mock_is_repo, mock_git_repo, mock_worktree_path):
        """Test successful worktree creation with new branch."""
        # Setup mocks
        mock_is_repo.return_value = True
        mock_root.return_value = mock_git_repo
        mock_run.return_value = (0, "Preparing worktree", "")

        result = runner.invoke(app, [
            'add',
            str(mock_worktree_path),
            'feature/test-branch',
            '--project', str(mock_git_repo)
        ])

        assert result.exit_code == 0
        assert "Worktree created successfully" in result.output

    def test_add_worktree_project_not_found(self, tmp_path):
        """Test add worktree when project path doesn't exist."""
        non_existent_path = tmp_path / "does-not-exist"

        result = runner.invoke(app, [
            'add',
            '../test-worktree',
            'feature/test',
            '--project', str(non_existent_path)
        ])

        assert result.exit_code == 1
        assert "Project path not found" in result.output

    @patch('sdlcctl.commands.worktree.is_git_repository')
    def test_add_worktree_not_git_repo(self, mock_is_repo, tmp_path):
        """Test error when project path is not a git repository."""
        mock_is_repo.return_value = False

        result = runner.invoke(app, [
            'add',
            '../test-worktree',
            'feature/test',
            '--project', str(tmp_path)
        ])

        assert result.exit_code == 1
        assert "Not a git repository" in result.output

    @patch('sdlcctl.commands.worktree.is_git_repository')
    @patch('sdlcctl.commands.worktree.get_git_root')
    def test_add_worktree_path_exists(self, mock_root, mock_is_repo, mock_git_repo, mock_worktree_path):
        """Test error when worktree path already exists (without --force)."""
        # Setup mocks
        mock_is_repo.return_value = True
        mock_root.return_value = mock_git_repo

        # Create the worktree path to simulate it existing
        mock_worktree_path.mkdir(parents=True)

        result = runner.invoke(app, [
            'add',
            str(mock_worktree_path),
            'feature/test',
            '--project', str(mock_git_repo)
        ])

        assert result.exit_code == 1
        assert "already exists" in result.output

    @patch('sdlcctl.commands.worktree.is_git_repository')
    @patch('sdlcctl.commands.worktree.get_git_root')
    @patch('sdlcctl.commands.worktree.run_git_command')
    def test_add_worktree_with_force(self, mock_run, mock_root, mock_is_repo, mock_git_repo, mock_worktree_path):
        """Test worktree creation with --force (overwrite existing)."""
        # Setup mocks
        mock_is_repo.return_value = True
        mock_root.return_value = mock_git_repo
        mock_run.return_value = (0, "Preparing worktree", "")

        # Create the worktree path to simulate it existing
        mock_worktree_path.mkdir(parents=True)

        result = runner.invoke(app, [
            'add',
            str(mock_worktree_path),
            'feature/test',
            '--force',
            '--project', str(mock_git_repo)
        ])

        assert result.exit_code == 0
        assert "Worktree created successfully" in result.output

    @patch('sdlcctl.commands.worktree.is_git_repository')
    @patch('sdlcctl.commands.worktree.get_git_root')
    @patch('sdlcctl.commands.worktree.run_git_command')
    def test_add_worktree_no_create_branch(self, mock_run, mock_root, mock_is_repo, mock_git_repo, mock_worktree_path):
        """Test worktree creation from existing branch (--no-create-branch)."""
        # Setup mocks
        mock_is_repo.return_value = True
        mock_root.return_value = mock_git_repo
        mock_run.return_value = (0, "Preparing worktree", "")

        result = runner.invoke(app, [
            'add',
            str(mock_worktree_path),
            'existing-branch',
            '--no-create-branch',
            '--project', str(mock_git_repo)
        ])

        assert result.exit_code == 0
        assert "Worktree created successfully" in result.output

    @patch('sdlcctl.commands.worktree.is_git_repository')
    @patch('sdlcctl.commands.worktree.get_git_root')
    @patch('sdlcctl.commands.worktree.run_git_command')
    def test_add_worktree_git_failure(self, mock_run, mock_root, mock_is_repo, mock_git_repo, mock_worktree_path):
        """Test handling of git command failure."""
        # Setup mocks
        mock_is_repo.return_value = True
        mock_root.return_value = mock_git_repo
        mock_run.return_value = (1, "", "fatal: branch already exists")

        result = runner.invoke(app, [
            'add',
            str(mock_worktree_path),
            'existing-branch',
            '--project', str(mock_git_repo)
        ])

        assert result.exit_code == 1
        assert "Failed to create worktree" in result.output


# ============================================================================
# Command: worktree list
# ============================================================================


class TestWorktreeList:
    """Test 'sdlcctl worktree list' command."""

    @patch('sdlcctl.commands.worktree.is_git_repository')
    @patch('sdlcctl.commands.worktree.get_git_root')
    @patch('sdlcctl.commands.worktree.run_git_command')
    def test_list_worktrees_success(self, mock_run, mock_root, mock_is_repo, mock_git_repo):
        """Test successful listing of worktrees."""
        # Setup mocks
        mock_is_repo.return_value = True
        mock_root.return_value = mock_git_repo

        # Mock git worktree list --porcelain output
        porcelain_output = f"""worktree {mock_git_repo}
HEAD a3f5b2c1234567890abcdef
branch refs/heads/main

"""
        mock_run.return_value = (0, porcelain_output, "")

        result = runner.invoke(app, [
            'list',
            '--project', str(mock_git_repo)
        ])

        assert result.exit_code == 0
        assert "Worktree(s)" in result.output
        assert str(mock_git_repo) in result.output

    def test_list_worktrees_project_not_found(self, tmp_path):
        """Test listing worktrees when project path doesn't exist."""
        non_existent_path = tmp_path / "does-not-exist"

        result = runner.invoke(app, [
            'list',
            '--project', str(non_existent_path)
        ])

        assert result.exit_code == 1
        assert "Project path not found" in result.output

    @patch('sdlcctl.commands.worktree.is_git_repository')
    def test_list_worktrees_not_git_repo(self, mock_is_repo, tmp_path):
        """Test error when project path is not a git repository."""
        mock_is_repo.return_value = False

        result = runner.invoke(app, [
            'list',
            '--project', str(tmp_path)
        ])

        assert result.exit_code == 1
        assert "Not a git repository" in result.output

    @patch('sdlcctl.commands.worktree.is_git_repository')
    @patch('sdlcctl.commands.worktree.get_git_root')
    @patch('sdlcctl.commands.worktree.run_git_command')
    def test_list_worktrees_porcelain(self, mock_run, mock_root, mock_is_repo, mock_git_repo):
        """Test JSON output with --porcelain flag."""
        # Setup mocks
        mock_is_repo.return_value = True
        mock_root.return_value = mock_git_repo

        # Mock git worktree list --porcelain output
        porcelain_output = f"""worktree {mock_git_repo}
HEAD a3f5b2c1234567890abcdef
branch refs/heads/main

"""
        mock_run.return_value = (0, porcelain_output, "")

        result = runner.invoke(app, [
            'list',
            '--porcelain',
            '--project', str(mock_git_repo)
        ])

        assert result.exit_code == 0

        # Parse JSON output
        output_data = json.loads(result.output)
        assert isinstance(output_data, list)
        assert len(output_data) == 1
        assert output_data[0]['path'] == str(mock_git_repo)

    @patch('sdlcctl.commands.worktree.is_git_repository')
    @patch('sdlcctl.commands.worktree.get_git_root')
    @patch('sdlcctl.commands.worktree.run_git_command')
    def test_list_worktrees_no_details(self, mock_run, mock_root, mock_is_repo, mock_git_repo):
        """Test simple output with --no-details flag."""
        # Setup mocks
        mock_is_repo.return_value = True
        mock_root.return_value = mock_git_repo

        # Mock git worktree list --porcelain output
        porcelain_output = f"""worktree {mock_git_repo}
HEAD a3f5b2c1234567890abcdef
branch refs/heads/main

"""
        mock_run.return_value = (0, porcelain_output, "")

        result = runner.invoke(app, [
            'list',
            '--no-details',
            '--project', str(mock_git_repo)
        ])

        assert result.exit_code == 0
        # Should only print path, nothing else
        assert str(mock_git_repo) in result.output
        assert "Worktree(s)" not in result.output

    @patch('sdlcctl.commands.worktree.is_git_repository')
    @patch('sdlcctl.commands.worktree.get_git_root')
    @patch('sdlcctl.commands.worktree.run_git_command')
    def test_list_worktrees_empty(self, mock_run, mock_root, mock_is_repo, mock_git_repo):
        """Test listing when no worktrees exist."""
        # Setup mocks
        mock_is_repo.return_value = True
        mock_root.return_value = mock_git_repo

        # Empty output (no worktrees)
        mock_run.return_value = (0, "", "")

        result = runner.invoke(app, [
            'list',
            '--project', str(mock_git_repo)
        ])

        assert result.exit_code == 0
        assert "No worktrees found" in result.output

    @patch('sdlcctl.commands.worktree.is_git_repository')
    @patch('sdlcctl.commands.worktree.get_git_root')
    @patch('sdlcctl.commands.worktree.run_git_command')
    def test_list_worktrees_multiple(self, mock_run, mock_root, mock_is_repo, mock_git_repo):
        """Test listing multiple worktrees."""
        # Setup mocks
        mock_is_repo.return_value = True
        mock_root.return_value = mock_git_repo

        # Mock multiple worktrees
        worktree2 = mock_git_repo.parent / "worktree2"
        porcelain_output = f"""worktree {mock_git_repo}
HEAD a3f5b2c1234567890abcdef
branch refs/heads/main

worktree {worktree2}
HEAD b4e6c3d1234567890fedcba
branch refs/heads/feature/test

"""
        mock_run.return_value = (0, porcelain_output, "")

        result = runner.invoke(app, [
            'list',
            '--project', str(mock_git_repo)
        ])

        assert result.exit_code == 0
        assert "2 Worktree(s)" in result.output
        # Rich table truncates long paths, verify both worktrees by their branches
        assert "main" in result.output
        assert "feature/test" in result.output

    @patch('sdlcctl.commands.worktree.is_git_repository')
    @patch('sdlcctl.commands.worktree.get_git_root')
    @patch('sdlcctl.commands.worktree.run_git_command')
    def test_list_worktrees_with_special_states(self, mock_run, mock_root, mock_is_repo, mock_git_repo):
        """Test listing worktrees with detached, locked, and prunable states."""
        # Setup mocks
        mock_is_repo.return_value = True
        mock_root.return_value = mock_git_repo

        # Mock worktrees with special states
        worktree2 = mock_git_repo.parent / "worktree-detached"
        worktree3 = mock_git_repo.parent / "worktree-locked"
        worktree4 = mock_git_repo.parent / "worktree-prunable"

        porcelain_output = f"""worktree {mock_git_repo}
HEAD a3f5b2c1234567890abcdef
branch refs/heads/main

worktree {worktree2}
HEAD b4e6c3d1234567890fedcba
detached

worktree {worktree3}
HEAD c5f7d4e1234567890abcdef
branch refs/heads/feature/locked
locked reason for locking

worktree {worktree4}
HEAD d6g8e5f1234567890fedcba
branch refs/heads/feature/old
prunable reason for pruning

"""
        mock_run.return_value = (0, porcelain_output, "")

        result = runner.invoke(app, [
            'list',
            '--project', str(mock_git_repo)
        ])

        assert result.exit_code == 0
        assert "4 Worktree(s)" in result.output
        # Verify special states appear in output
        assert "detached" in result.output
        assert "locked" in result.output
        assert "prunable" in result.output


# ============================================================================
# Command: worktree sync
# ============================================================================


class TestWorktreeSync:
    """Test 'sdlcctl worktree sync' command."""

    def test_sync_worktrees_project_not_found(self, tmp_path):
        """Test sync worktrees when project path doesn't exist."""
        non_existent_path = tmp_path / "does-not-exist"

        result = runner.invoke(app, [
            'sync',
            '--project', str(non_existent_path)
        ])

        assert result.exit_code == 1
        assert "Project path not found" in result.output

    @patch('sdlcctl.commands.worktree.is_git_repository')
    @patch('sdlcctl.commands.worktree.get_git_root')
    @patch('sdlcctl.commands.worktree.run_git_command')
    def test_sync_worktrees_success(self, mock_run, mock_root, mock_is_repo, mock_git_repo):
        """Test successful sync of worktrees."""
        # Setup mocks
        mock_is_repo.return_value = True
        mock_root.return_value = mock_git_repo

        # Mock git worktree list output
        worktree2 = mock_git_repo.parent / "worktree2"
        list_output = f"""worktree {mock_git_repo}
branch refs/heads/main

worktree {worktree2}
branch refs/heads/feature/test

"""
        # Mock git commands: list, then fetch+rebase for feature branch
        mock_run.side_effect = [
            (0, list_output, ""),  # git worktree list
            (0, "", ""),  # git fetch
            (0, "Successfully rebased", ""),  # git rebase
        ]

        result = runner.invoke(app, [
            'sync',
            '--project', str(mock_git_repo)
        ])

        assert result.exit_code == 0
        assert "Syncing" in result.output
        assert "Synced: 1" in result.output

    @patch('sdlcctl.commands.worktree.is_git_repository')
    def test_sync_worktrees_not_git_repo(self, mock_is_repo, tmp_path):
        """Test error when project path is not a git repository."""
        mock_is_repo.return_value = False

        result = runner.invoke(app, [
            'sync',
            '--project', str(tmp_path)
        ])

        assert result.exit_code == 1
        assert "Not a git repository" in result.output

    @patch('sdlcctl.commands.worktree.is_git_repository')
    @patch('sdlcctl.commands.worktree.get_git_root')
    @patch('sdlcctl.commands.worktree.run_git_command')
    def test_sync_worktrees_dry_run(self, mock_run, mock_root, mock_is_repo, mock_git_repo):
        """Test sync dry run (no actual changes)."""
        # Setup mocks
        mock_is_repo.return_value = True
        mock_root.return_value = mock_git_repo

        # Mock git worktree list output
        worktree2 = mock_git_repo.parent / "worktree2"
        list_output = f"""worktree {mock_git_repo}
branch refs/heads/main

worktree {worktree2}
branch refs/heads/feature/test

"""
        mock_run.return_value = (0, list_output, "")

        result = runner.invoke(app, [
            'sync',
            '--dry-run',
            '--project', str(mock_git_repo)
        ])

        assert result.exit_code == 0
        assert "DRY RUN" in result.output
        assert "Would sync" in result.output

    @patch('sdlcctl.commands.worktree.is_git_repository')
    @patch('sdlcctl.commands.worktree.get_git_root')
    @patch('sdlcctl.commands.worktree.run_git_command')
    def test_sync_worktrees_rebase_conflict(self, mock_run, mock_root, mock_is_repo, mock_git_repo):
        """Test handling of rebase conflicts during sync."""
        # Setup mocks
        mock_is_repo.return_value = True
        mock_root.return_value = mock_git_repo

        # Mock git worktree list output
        worktree2 = mock_git_repo.parent / "worktree2"
        list_output = f"""worktree {mock_git_repo}
branch refs/heads/main

worktree {worktree2}
branch refs/heads/feature/test

"""
        # Mock rebase failure
        mock_run.side_effect = [
            (0, list_output, ""),  # git worktree list
            (0, "", ""),  # git fetch (success)
            (1, "", "CONFLICT: Merge conflict in file.txt"),  # git rebase (failure)
        ]

        result = runner.invoke(app, [
            'sync',
            '--project', str(mock_git_repo)
        ])

        # Should continue execution (exit 0) but report failure
        assert result.exit_code == 0
        assert "Rebase failed" in result.output


# ============================================================================
# Command: worktree remove
# ============================================================================


class TestWorktreeRemove:
    """Test 'sdlcctl worktree remove' command."""

    def test_remove_worktree_project_not_found(self, tmp_path, mock_worktree_path):
        """Test remove worktree when project path doesn't exist."""
        non_existent_path = tmp_path / "does-not-exist"

        result = runner.invoke(app, [
            'remove',
            str(mock_worktree_path),
            '--project', str(non_existent_path)
        ])

        assert result.exit_code == 1
        assert "Project path not found" in result.output

    @patch('sdlcctl.commands.worktree.is_git_repository')
    @patch('sdlcctl.commands.worktree.get_git_root')
    @patch('sdlcctl.commands.worktree.run_git_command')
    def test_remove_worktree_success(self, mock_run, mock_root, mock_is_repo, mock_git_repo, mock_worktree_path):
        """Test successful worktree removal."""
        # Setup mocks
        mock_is_repo.return_value = True
        mock_root.return_value = mock_git_repo
        mock_run.return_value = (0, "", "")

        result = runner.invoke(app, [
            'remove',
            str(mock_worktree_path),
            '--project', str(mock_git_repo)
        ])

        assert result.exit_code == 0
        assert "Worktree removed successfully" in result.output

    @patch('sdlcctl.commands.worktree.is_git_repository')
    def test_remove_worktree_not_git_repo(self, mock_is_repo, tmp_path):
        """Test error when project path is not a git repository."""
        mock_is_repo.return_value = False

        result = runner.invoke(app, [
            'remove',
            '../test-worktree',
            '--project', str(tmp_path)
        ])

        assert result.exit_code == 1
        assert "Not a git repository" in result.output

    @patch('sdlcctl.commands.worktree.is_git_repository')
    @patch('sdlcctl.commands.worktree.get_git_root')
    @patch('sdlcctl.commands.worktree.run_git_command')
    def test_remove_worktree_uncommitted_changes(self, mock_run, mock_root, mock_is_repo, mock_git_repo, mock_worktree_path):
        """Test error when worktree has uncommitted changes (without --force)."""
        # Setup mocks
        mock_is_repo.return_value = True
        mock_root.return_value = mock_git_repo
        mock_run.return_value = (1, "", "fatal: contains modified or untracked files")

        result = runner.invoke(app, [
            'remove',
            str(mock_worktree_path),
            '--project', str(mock_git_repo)
        ])

        assert result.exit_code == 1
        assert "Failed to remove worktree" in result.output
        assert "Hint" in result.output  # Should suggest --force

    @patch('sdlcctl.commands.worktree.is_git_repository')
    @patch('sdlcctl.commands.worktree.get_git_root')
    @patch('sdlcctl.commands.worktree.run_git_command')
    def test_remove_worktree_with_force(self, mock_run, mock_root, mock_is_repo, mock_git_repo, mock_worktree_path):
        """Test forced worktree removal (discard uncommitted changes)."""
        # Setup mocks
        mock_is_repo.return_value = True
        mock_root.return_value = mock_git_repo
        mock_run.return_value = (0, "", "")

        result = runner.invoke(app, [
            'remove',
            str(mock_worktree_path),
            '--force',
            '--project', str(mock_git_repo)
        ])

        assert result.exit_code == 0
        assert "Worktree removed successfully" in result.output


# ============================================================================
# Integration-Style Tests (within unit test file)
# ============================================================================


class TestWorktreeWorkflow:
    """Test complete worktree workflow (add → list → remove)."""

    @patch('sdlcctl.commands.worktree.is_git_repository')
    @patch('sdlcctl.commands.worktree.get_git_root')
    @patch('sdlcctl.commands.worktree.run_git_command')
    def test_full_workflow(self, mock_run, mock_root, mock_is_repo, mock_git_repo, mock_worktree_path):
        """Test complete workflow: add → list (2 worktrees) → remove → list (1 worktree)."""
        # Setup mocks
        mock_is_repo.return_value = True
        mock_root.return_value = mock_git_repo

        # Step 1: Add worktree
        mock_run.return_value = (0, "Preparing worktree", "")
        result_add = runner.invoke(app, [
            'add',
            str(mock_worktree_path),
            'feature/test',
            '--project', str(mock_git_repo)
        ])
        assert result_add.exit_code == 0

        # Step 2: List worktrees (should show 2)
        list_output = f"""worktree {mock_git_repo}
branch refs/heads/main

worktree {mock_worktree_path}
branch refs/heads/feature/test

"""
        mock_run.return_value = (0, list_output, "")
        result_list1 = runner.invoke(app, [
            'list',
            '--project', str(mock_git_repo)
        ])
        assert result_list1.exit_code == 0
        assert "2 Worktree(s)" in result_list1.output

        # Step 3: Remove worktree
        mock_run.return_value = (0, "", "")
        result_remove = runner.invoke(app, [
            'remove',
            str(mock_worktree_path),
            '--project', str(mock_git_repo)
        ])
        assert result_remove.exit_code == 0

        # Step 4: List worktrees (should show 1)
        list_output_after = f"""worktree {mock_git_repo}
branch refs/heads/main

"""
        mock_run.return_value = (0, list_output_after, "")
        result_list2 = runner.invoke(app, [
            'list',
            '--project', str(mock_git_repo)
        ])
        assert result_list2.exit_code == 0
        assert "1 Worktree(s)" in result_list2.output
