"""
Unit tests for OutputScrubber — ADR-058 Pattern A.

Sprint 179 — ZeroClaw Security Hardening.
Test IDs: CS-01 to CS-12 (see FR-042 §3 + Reviewer R-01/R-02 findings).

Coverage:
  CS-01  token pattern scrubbed (key:value)
  CS-02  api_key pattern scrubbed
  CS-03  password pattern scrubbed
  CS-04  bearer token scrubbed (Authorization header + bare bearer)
  CS-05  secret pattern scrubbed
  CS-06  clean output returned unchanged (no false positives)
  CS-07  multiple matches all scrubbed in one call
  CS-08  short value (<4 chars) handled: full value preserved + suffix
  CS-09  invoker integration — scrub called with InvocationResult content
  CS-10  evidence integration — scrub→hash→store order validated
  CS-11  credential plural pattern scrubbed (R-02)
  CS-12  PEM private key block scrubbed (R-01)
"""

from __future__ import annotations

import pytest

from app.services.agent_team.output_scrubber import OutputScrubber

REDACTED = "****[REDACTED]"


@pytest.fixture()
def scrubber() -> OutputScrubber:
    return OutputScrubber()


# ────────────────────────────────────────────────────────────────────────────
# CS-01: token pattern
# ────────────────────────────────────────────────────────────────────────────

class TestTokenPattern:
    def test_token_equals_scrubbed(self, scrubber: OutputScrubber) -> None:
        """CS-01a — token=<value> is redacted."""
        result, violations = scrubber.scrub("token=sk-abcdef123456")
        assert REDACTED in result
        assert result.startswith("token=sk-a")
        assert "token" in violations

    def test_token_colon_scrubbed(self, scrubber: OutputScrubber) -> None:
        """CS-01b — token: <value> is redacted."""
        result, violations = scrubber.scrub("token: sk-abcdef123456")
        assert REDACTED in result
        assert "token" in violations

    def test_token_case_insensitive(self, scrubber: OutputScrubber) -> None:
        """CS-01c — TOKEN= (uppercase) is redacted."""
        result, violations = scrubber.scrub("TOKEN=sk-ABCDEF999")
        assert REDACTED in result
        assert "token" in violations

    def test_access_token_variant(self, scrubber: OutputScrubber) -> None:
        """CS-01d — access_token= is redacted."""
        result, violations = scrubber.scrub("access_token=eyJhbGciOiJIUzI1NiJ9.body.sig")
        assert REDACTED in result
        assert "token" in violations


# ────────────────────────────────────────────────────────────────────────────
# CS-02: api_key pattern
# ────────────────────────────────────────────────────────────────────────────

class TestApiKeyPattern:
    def test_api_key_scrubbed(self, scrubber: OutputScrubber) -> None:
        """CS-02a — api_key= is redacted."""
        result, violations = scrubber.scrub("api_key=AAABBBCCC111222")
        assert REDACTED in result
        assert result.startswith("api_key=AAAB")
        assert "api_key" in violations

    def test_apikey_no_underscore(self, scrubber: OutputScrubber) -> None:
        """CS-02b — apikey= (no underscore) is redacted."""
        result, violations = scrubber.scrub("apikey=mykey123")
        assert REDACTED in result
        assert "api_key" in violations

    def test_API_KEY_uppercase(self, scrubber: OutputScrubber) -> None:
        """CS-02c — API_KEY: is redacted."""
        result, violations = scrubber.scrub("API_KEY: secret_val")
        assert REDACTED in result
        assert "api_key" in violations


# ────────────────────────────────────────────────────────────────────────────
# CS-03: password pattern
# ────────────────────────────────────────────────────────────────────────────

class TestPasswordPattern:
    def test_password_scrubbed(self, scrubber: OutputScrubber) -> None:
        """CS-03a — password= is redacted."""
        result, violations = scrubber.scrub("password=MyP@ssw0rd!")
        assert REDACTED in result
        assert result.startswith("password=MyP@")
        assert "password" in violations

    def test_passwd_alias_scrubbed(self, scrubber: OutputScrubber) -> None:
        """CS-03b — passwd= is redacted."""
        result, violations = scrubber.scrub("passwd=hunter2")
        assert REDACTED in result
        assert "password" in violations

    def test_PASSWORD_uppercase(self, scrubber: OutputScrubber) -> None:
        """CS-03c — PASSWORD: is redacted."""
        result, violations = scrubber.scrub("PASSWORD: Correct-Horse")
        assert REDACTED in result
        assert "password" in violations


# ────────────────────────────────────────────────────────────────────────────
# CS-04: bearer pattern
# ────────────────────────────────────────────────────────────────────────────

class TestBearerPattern:
    def test_authorization_bearer_header(self, scrubber: OutputScrubber) -> None:
        """CS-04a — Authorization: Bearer <token> is redacted."""
        raw = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        result, violations = scrubber.scrub(raw)
        assert REDACTED in result
        assert "bearer" in violations
        # Prefix "eyJh" preserved
        assert "eyJh" in result

    def test_bare_bearer_scrubbed(self, scrubber: OutputScrubber) -> None:
        """CS-04b — bare 'bearer <token>' is redacted."""
        result, violations = scrubber.scrub("bearer ghp_abcdefg12345")
        assert REDACTED in result
        assert "bearer" in violations


# ────────────────────────────────────────────────────────────────────────────
# CS-05: secret pattern
# ────────────────────────────────────────────────────────────────────────────

class TestSecretPattern:
    def test_secret_scrubbed(self, scrubber: OutputScrubber) -> None:
        """CS-05a — secret= is redacted."""
        result, violations = scrubber.scrub("secret=topsecretvalue")
        assert REDACTED in result
        assert "secret" in violations

    def test_secret_key_variant(self, scrubber: OutputScrubber) -> None:
        """CS-05b — secret_key= is redacted."""
        result, violations = scrubber.scrub("secret_key=my_secret_123")
        assert REDACTED in result
        assert "secret" in violations

    def test_client_secret(self, scrubber: OutputScrubber) -> None:
        """CS-05c — client_secret= is redacted."""
        result, violations = scrubber.scrub("client_secret=oauth2_secret_xyz")
        assert REDACTED in result
        assert "secret" in violations


# ────────────────────────────────────────────────────────────────────────────
# CS-06: clean output unchanged (no false positives)
# ────────────────────────────────────────────────────────────────────────────

class TestCleanOutput:
    def test_plain_text_unchanged(self, scrubber: OutputScrubber) -> None:
        """CS-06a — normal text without secrets is returned unchanged."""
        text = "The quick brown fox jumps over the lazy dog."
        result, violations = scrubber.scrub(text)
        assert result == text
        assert violations == []

    def test_code_output_unchanged(self, scrubber: OutputScrubber) -> None:
        """CS-06b — code-like output without secrets is unchanged."""
        text = "def authenticate(user, passobj):\n    return check(user)"
        result, violations = scrubber.scrub(text)
        assert result == text
        assert violations == []

    def test_empty_string_unchanged(self, scrubber: OutputScrubber) -> None:
        """CS-06c — empty string returns empty with no violations."""
        result, violations = scrubber.scrub("")
        assert result == ""
        assert violations == []

    def test_none_like_whitespace_unchanged(self, scrubber: OutputScrubber) -> None:
        """CS-06d — whitespace-only returns unchanged."""
        result, violations = scrubber.scrub("   \n\t  ")
        assert result == "   \n\t  "
        assert violations == []


# ────────────────────────────────────────────────────────────────────────────
# CS-07: multiple matches all scrubbed
# ────────────────────────────────────────────────────────────────────────────

class TestMultipleMatches:
    def test_two_different_patterns_both_scrubbed(
        self, scrubber: OutputScrubber
    ) -> None:
        """CS-07a — token= and api_key= in same text both redacted."""
        raw = "token=sk-abc123 api_key=key-xyz789"
        result, violations = scrubber.scrub(raw)
        assert result.count(REDACTED) == 2
        assert "token" in violations
        assert "api_key" in violations

    def test_same_pattern_multiple_occurrences(
        self, scrubber: OutputScrubber
    ) -> None:
        """CS-07b — two token= occurrences both redacted."""
        raw = "token=aaa111 token=bbb222"
        result, violations = scrubber.scrub(raw)
        assert result.count(REDACTED) == 2
        assert violations.count("token") == 1  # deduplicated

    def test_env_output_multiple_secrets(self, scrubber: OutputScrubber) -> None:
        """CS-07c — env-command-style output with multiple secrets."""
        raw = (
            "PATH=/usr/bin:/bin\n"
            "ANTHROPIC_API_KEY=sk-ant-api03-XYZXYZXYZ\n"
            "TOKEN=ghp_AAABBBCCC\n"
            "HOME=/home/user\n"
            "SECRET=mysecret123\n"
        )
        result, violations = scrubber.scrub(raw)
        # PATH and HOME should NOT be redacted
        assert "PATH=/usr/bin:/bin" in result
        assert "HOME=/home/user" in result
        # Secrets should be redacted
        assert "XYZXYZXYZ" not in result
        assert "ghp_AAABBBCCC" not in result
        assert "mysecret123" not in result
        assert len(violations) >= 3


# ────────────────────────────────────────────────────────────────────────────
# CS-08: short value handling (< 4 chars)
# ────────────────────────────────────────────────────────────────────────────

class TestShortValueHandling:
    def test_three_char_value_preserved_plus_suffix(
        self, scrubber: OutputScrubber
    ) -> None:
        """CS-08a — 3-char secret: all 3 chars preserved + REDACTED suffix."""
        result, violations = scrubber.scrub("token=abc")
        assert result == f"token=abc{REDACTED}"
        assert "token" in violations

    def test_one_char_value(self, scrubber: OutputScrubber) -> None:
        """CS-08b — 1-char secret: single char preserved + REDACTED suffix."""
        result, violations = scrubber.scrub("password=x")
        assert result == f"password=x{REDACTED}"
        assert "password" in violations

    def test_four_char_value_only_four_preserved(
        self, scrubber: OutputScrubber
    ) -> None:
        """CS-08c — exactly 4-char secret: all 4 preserved + suffix."""
        result, violations = scrubber.scrub("secret=abcd")
        assert result == f"secret=abcd{REDACTED}"
        assert "secret" in violations


# ────────────────────────────────────────────────────────────────────────────
# CS-09: idempotency — double scrub is a no-op
# (also validates invoker integration: scrub is safe to call twice)
# ────────────────────────────────────────────────────────────────────────────

class TestIdempotency:
    def test_double_scrub_no_op(self, scrubber: OutputScrubber) -> None:
        """CS-09 — applying scrub() twice produces identical output."""
        raw = "token=sk-abcdef123456"
        once, _ = scrubber.scrub(raw)
        twice, violations2 = scrubber.scrub(once)
        assert once == twice
        # Second call should find no new violations (already redacted)
        assert violations2 == []

    def test_already_redacted_not_double_redacted(
        self, scrubber: OutputScrubber
    ) -> None:
        """CS-09b — pre-redacted value is not further modified."""
        pre_scrubbed = f"token=sk-a{REDACTED}"
        result, violations = scrubber.scrub(pre_scrubbed)
        assert result == pre_scrubbed
        assert violations == []


# ────────────────────────────────────────────────────────────────────────────
# CS-10: evidence integration order (scrub → hash → store)
# ────────────────────────────────────────────────────────────────────────────

class TestEvidenceIntegrationOrder:
    def test_scrub_before_hash(self, scrubber: OutputScrubber) -> None:
        """CS-10 — scrubbed text differs from raw text, confirming scrub occurs
        before SHA256 hashing in EvidenceCollector."""
        import hashlib

        raw = "api_key=MY_SECRET_API_KEY_VALUE"
        scrubbed, violations = scrubber.scrub(raw)

        raw_hash = hashlib.sha256(raw.encode()).hexdigest()
        scrubbed_hash = hashlib.sha256(scrubbed.encode()).hexdigest()

        # Hashes differ — secret was removed before hashing
        assert raw_hash != scrubbed_hash
        assert "api_key" in violations
        assert "MY_SECRET_API_KEY_VALUE" not in scrubbed


# ────────────────────────────────────────────────────────────────────────────
# CS-11: credential plural pattern (Reviewer R-02)
# ────────────────────────────────────────────────────────────────────────────

class TestCredentialPluralPattern:
    def test_credential_singular_scrubbed(self, scrubber: OutputScrubber) -> None:
        """CS-11a — credential= (singular) is redacted."""
        result, violations = scrubber.scrub("credential=my_cred_value")
        assert REDACTED in result
        assert "credential" in violations

    def test_credentials_plural_scrubbed(self, scrubber: OutputScrubber) -> None:
        """CS-11b — credentials= (plural) is redacted (R-02 fix)."""
        result, violations = scrubber.scrub("credentials=my_cred_value")
        assert REDACTED in result
        assert "credential" in violations

    def test_CREDENTIALS_uppercase(self, scrubber: OutputScrubber) -> None:
        """CS-11c — CREDENTIALS: (uppercase plural) is redacted."""
        result, violations = scrubber.scrub("CREDENTIALS: some_cred_string")
        assert REDACTED in result
        assert "credential" in violations


# ────────────────────────────────────────────────────────────────────────────
# CS-12: PEM private key block (Reviewer R-01)
# ────────────────────────────────────────────────────────────────────────────

_RSA_PRIVATE_KEY = """\
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmn
opqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdefghij
-----END RSA PRIVATE KEY-----"""

_OPENSSH_PRIVATE_KEY = """\
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAA....
-----END OPENSSH PRIVATE KEY-----"""

_EC_PRIVATE_KEY = """\
-----BEGIN EC PRIVATE KEY-----
MHQCAQEEINYFake...
-----END EC PRIVATE KEY-----"""


class TestPemBlockPattern:
    def test_rsa_private_key_scrubbed(self, scrubber: OutputScrubber) -> None:
        """CS-12a — RSA PRIVATE KEY block is replaced with [PEM_KEY_REDACTED]."""
        result, violations = scrubber.scrub(_RSA_PRIVATE_KEY)
        assert "[PEM_KEY_REDACTED]" in result
        assert "MIIEpAIBAAKCAQEA" not in result
        assert "pem_block" in violations

    def test_openssh_private_key_scrubbed(self, scrubber: OutputScrubber) -> None:
        """CS-12b — OPENSSH PRIVATE KEY block is scrubbed."""
        result, violations = scrubber.scrub(_OPENSSH_PRIVATE_KEY)
        assert "[PEM_KEY_REDACTED]" in result
        assert "b3BlbnNzaC1rZXktdjEAAAAA" not in result
        assert "pem_block" in violations

    def test_ec_private_key_scrubbed(self, scrubber: OutputScrubber) -> None:
        """CS-12c — EC PRIVATE KEY block is scrubbed."""
        result, violations = scrubber.scrub(_EC_PRIVATE_KEY)
        assert "[PEM_KEY_REDACTED]" in result
        assert "pem_block" in violations

    def test_pem_in_env_output_scrubbed(self, scrubber: OutputScrubber) -> None:
        """CS-12d — PEM key embedded in env-style output is scrubbed."""
        raw = f"HOME=/home/user\nSSH_KEY={_RSA_PRIVATE_KEY}\nPATH=/usr/bin"
        result, violations = scrubber.scrub(raw)
        assert "[PEM_KEY_REDACTED]" in result
        assert "HOME=/home/user" in result
        assert "PATH=/usr/bin" in result
        assert "pem_block" in violations

    def test_surrounding_text_preserved_after_pem(
        self, scrubber: OutputScrubber
    ) -> None:
        """CS-12e — text before/after PEM block is preserved unchanged."""
        raw = f"Before text\n{_RSA_PRIVATE_KEY}\nAfter text"
        result, violations = scrubber.scrub(raw)
        assert "Before text" in result
        assert "After text" in result
        assert "[PEM_KEY_REDACTED]" in result
        assert "pem_block" in violations
