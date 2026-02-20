"""
Unit tests for ShellGuard.scrub_environment() — ADR-058 Pattern C.

Sprint 179 — ZeroClaw Security Hardening.
Test IDs: ES-01 to ES-06 (see FR-043 §3).

Coverage:
  ES-01  Only safe vars returned when full host env supplied
  ES-02  Secret env vars excluded (API_KEY, SECRET, DATABASE_URL, etc.)
  ES-03  LC_ALL included when set in host (Vietnamese UTF-8 locale)
  ES-04  Missing safe var is omitted — not set to empty string
  ES-05  PATH preserved with exact original value
  ES-06  Empty env returns empty dict
"""

from __future__ import annotations

import os
from typing import Generator
from unittest.mock import patch

import pytest

from app.services.agent_team.shell_guard import SAFE_ENV_VARS, ShellGuard


@pytest.fixture()
def guard() -> ShellGuard:
    return ShellGuard()


# ────────────────────────────────────────────────────────────────────────────
# ES-01: Only safe vars returned from full host env
# ────────────────────────────────────────────────────────────────────────────

class TestOnlySafeVarsReturned:
    def test_safe_vars_subset_of_allowlist(self, guard: ShellGuard) -> None:
        """ES-01a — every key in returned dict is in SAFE_ENV_VARS."""
        fake_env = {
            "PATH": "/usr/bin:/bin",
            "HOME": "/home/user",
            "LANG": "en_US.UTF-8",
            "ANTHROPIC_API_KEY": "sk-ant-SUPERSECRET",
            "DATABASE_URL": "postgresql://user:pass@host/db",
            "TERM": "xterm-256color",
            "SECRET_TOKEN": "topsecret",
        }
        with patch.dict(os.environ, fake_env, clear=True):
            result = ShellGuard.scrub_environment()

        for key in result:
            assert key in SAFE_ENV_VARS, (
                f"Non-allowlist var '{key}' appeared in scrubbed env"
            )

    def test_allowlist_covers_expected_9_vars(self) -> None:
        """ES-01b — SAFE_ENV_VARS contains exactly 9 variables."""
        expected = {"PATH", "HOME", "LANG", "LC_ALL", "TZ", "TERM", "USER", "SHELL", "TMPDIR"}
        assert set(SAFE_ENV_VARS) == expected


# ────────────────────────────────────────────────────────────────────────────
# ES-02: Secrets excluded from safe env
# ────────────────────────────────────────────────────────────────────────────

class TestSecretsExcluded:
    def test_api_key_excluded(self, guard: ShellGuard) -> None:
        """ES-02a — ANTHROPIC_API_KEY is excluded from scrubbed env."""
        with patch.dict(
            os.environ,
            {"ANTHROPIC_API_KEY": "sk-ant-SECRET", "PATH": "/usr/bin"},
            clear=True,
        ):
            result = ShellGuard.scrub_environment()

        assert "ANTHROPIC_API_KEY" not in result

    def test_database_url_excluded(self) -> None:
        """ES-02b — DATABASE_URL is excluded from scrubbed env."""
        with patch.dict(
            os.environ,
            {"DATABASE_URL": "postgresql://user:pass@localhost/db", "PATH": "/usr/bin"},
            clear=True,
        ):
            result = ShellGuard.scrub_environment()

        assert "DATABASE_URL" not in result

    def test_multiple_secrets_all_excluded(self) -> None:
        """ES-02c — Multiple secret vars all excluded."""
        secrets = {
            "AWS_ACCESS_KEY_ID": "AKIAXXX",
            "AWS_SECRET_ACCESS_KEY": "wJalrXUtnFEMI",
            "GITHUB_TOKEN": "ghp_abcdef",
            "REDIS_PASSWORD": "redis_secret",
            "JWT_SECRET_KEY": "jwt_secret",
            "PATH": "/usr/bin",  # safe — included
        }
        with patch.dict(os.environ, secrets, clear=True):
            result = ShellGuard.scrub_environment()

        for secret_key in secrets:
            if secret_key == "PATH":
                continue
            assert secret_key not in result, (
                f"Secret env var '{secret_key}' leaked into scrubbed env"
            )
        assert "PATH" in result


# ────────────────────────────────────────────────────────────────────────────
# ES-03: LC_ALL included when set (Vietnamese UTF-8 locale)
# ────────────────────────────────────────────────────────────────────────────

class TestLCAllIncluded:
    def test_lc_all_included_when_set(self) -> None:
        """ES-03a — LC_ALL is included when present in host env."""
        with patch.dict(
            os.environ,
            {"LC_ALL": "vi_VN.UTF-8", "PATH": "/usr/bin"},
            clear=True,
        ):
            result = ShellGuard.scrub_environment()

        assert "LC_ALL" in result
        assert result["LC_ALL"] == "vi_VN.UTF-8"

    def test_lc_all_value_preserved_exactly(self) -> None:
        """ES-03b — LC_ALL value is not modified."""
        with patch.dict(
            os.environ,
            {"LC_ALL": "en_US.UTF-8", "PATH": "/usr/bin"},
            clear=True,
        ):
            result = ShellGuard.scrub_environment()

        assert result.get("LC_ALL") == "en_US.UTF-8"


# ────────────────────────────────────────────────────────────────────────────
# ES-04: Missing safe var is omitted (not set to empty string)
# ────────────────────────────────────────────────────────────────────────────

class TestMissingVarOmitted:
    def test_missing_tmpdir_omitted(self) -> None:
        """ES-04a — TMPDIR absent from host env → absent in scrubbed env."""
        env_without_tmpdir = {
            "PATH": "/usr/bin",
            "HOME": "/home/user",
        }
        with patch.dict(os.environ, env_without_tmpdir, clear=True):
            result = ShellGuard.scrub_environment()

        assert "TMPDIR" not in result

    def test_missing_var_not_empty_string(self) -> None:
        """ES-04b — missing var is omitted, NOT set to ''."""
        env_without_tz = {"PATH": "/usr/bin"}
        with patch.dict(os.environ, env_without_tz, clear=True):
            result = ShellGuard.scrub_environment()

        assert "TZ" not in result
        # Confirm we aren't setting empty strings for missing vars
        for value in result.values():
            assert value != "", (
                "scrub_environment() must not set empty-string values"
            )

    def test_result_is_dict_of_strings(self) -> None:
        """ES-04c — result is always Dict[str, str], never None values."""
        with patch.dict(os.environ, {"PATH": "/usr/bin"}, clear=True):
            result = ShellGuard.scrub_environment()

        assert isinstance(result, dict)
        for k, v in result.items():
            assert isinstance(k, str)
            assert isinstance(v, str)


# ────────────────────────────────────────────────────────────────────────────
# ES-05: PATH preserved with exact original value
# ────────────────────────────────────────────────────────────────────────────

class TestPathPreserved:
    def test_path_value_preserved_exactly(self) -> None:
        """ES-05a — PATH value is identical to host PATH."""
        custom_path = "/usr/local/bin:/usr/bin:/bin:/custom/tool"
        with patch.dict(os.environ, {"PATH": custom_path}, clear=True):
            result = ShellGuard.scrub_environment()

        assert result.get("PATH") == custom_path

    def test_path_not_modified_or_trimmed(self) -> None:
        """ES-05b — PATH with trailing colon is preserved as-is."""
        path_with_trailing = "/usr/bin:/bin:"
        with patch.dict(os.environ, {"PATH": path_with_trailing}, clear=True):
            result = ShellGuard.scrub_environment()

        assert result.get("PATH") == path_with_trailing


# ────────────────────────────────────────────────────────────────────────────
# ES-06: Empty env returns empty dict
# ────────────────────────────────────────────────────────────────────────────

class TestEmptyEnv:
    def test_empty_host_env_returns_empty_dict(self) -> None:
        """ES-06a — empty host env → empty scrubbed env."""
        with patch.dict(os.environ, {}, clear=True):
            result = ShellGuard.scrub_environment()

        assert result == {}

    def test_env_with_only_secrets_returns_empty_dict(self) -> None:
        """ES-06b — env with only secret vars → empty scrubbed env."""
        only_secrets = {
            "ANTHROPIC_API_KEY": "sk-ant-SECRET",
            "AWS_SECRET_ACCESS_KEY": "aws_secret",
            "DATABASE_URL": "postgres://user:pass@host/db",
        }
        with patch.dict(os.environ, only_secrets, clear=True):
            result = ShellGuard.scrub_environment()

        assert result == {}
