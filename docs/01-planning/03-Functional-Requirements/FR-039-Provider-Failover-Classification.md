---
sdlc_version: "6.1.0"
document_type: "Functional Requirement"
status: "PROPOSED"
sprint: "176"
spec_id: "FR-039"
tier: "PROFESSIONAL"
stage: "01 - Planning"
---

# FR-039: Provider Failover Classification

**Version**: 1.0.0
**Status**: PROPOSED
**Created**: February 2026
**Sprint**: 176-177
**Framework**: SDLC 6.1.0
**Epic**: EP-07 Multi-Agent Team Engine
**ADR**: ADR-056 (Decision 3: Provider Profile Key + Abort Matrix)
**Owner**: Backend Team

---

## 1. Overview

### 1.1 Purpose

Classify provider errors into 6 FailoverReasons and route to ABORT/FALLBACK/RETRY actions per the Abort Matrix. Implement provider profile key with Redis-based cooldown tracking. Enable LLM self-correction via error-as-string (Nanobot N3).

### 1.2 Business Value

- Reduces manual intervention on provider failures by 80%
- Enables automatic failover to backup providers (Ollama → Claude)
- Provider cooldowns prevent repeated expensive failed retries
- Error-as-string enables LLM self-correction without human involvement

---

## 2. Functional Requirements

### 2.1 HTTP Error Classification

**GIVEN** an HTTP error response from a provider
**WHEN** the status code is received
**THEN** the system SHALL classify as:

| HTTP Code | Reason | Action |
|-----------|--------|--------|
| 401, 403 | `auth` | ABORT |
| 402 | `billing` | ABORT |
| 429 | `rate_limit` | FALLBACK |
| 408, 504 | `timeout` | FALLBACK |
| 400 | `format` | RETRY |
| Other (500, 418, etc.) | `unknown` | ABORT |

### 2.2 Exception Classification

**GIVEN** a Python exception from a provider call
**WHEN** the error message contains:
- `timeout`, `timed out`, `ETIMEDOUT`, `ECONNRESET` → `timeout`
- `unauthorized`, `forbidden` → `auth`
- `rate limit`, `too many requests` → `rate_limit`
- `billing`, `payment` → `billing`
- `invalid`, `malformed` → `format`
- Other → `unknown`

**THEN** the system SHALL classify accordingly

### 2.3 Provider Profile Key (Decision 3)

**GIVEN** a provider configuration
**THEN** the system SHALL generate a key in format: `{provider}:{account}:{region}:{model_family}`

**GIVEN** a key string with != 4 colon-separated segments
**THEN** the system SHALL raise `ValueError`

### 2.4 Cooldown Tracking

**GIVEN** a provider failure classified as `rate_limit` or `timeout`
**THEN** the system SHALL:
1. Set Redis key `cooldown:{profile_key}` with TTL per reason
2. TTLs: rate_limit=60s, timeout=120s, auth=300s, billing=600s, format=0s, unknown=0s
3. Skip cooldown providers on next invocation

### 2.5 Error-as-String (Nanobot N3)

**GIVEN** a RETRY action from the abort matrix
**THEN** the system SHALL format error as: `Error [{reason}] (provider: {key}): {message}\nAction: retry`
**AND** feed this string back to the LLM as context for self-correction

---

## 3. Test Coverage

| Test ID | Description |
|---------|-------------|
| FC-01 to FC-09 | HTTP error classification (9 tests) |
| FC-10 to FC-16 | Exception classification (7 tests) |
| FC-17 to FC-19 | Error-as-string format (3 tests) |
| FC-20 to FC-23 | Provider profile key (4 tests) |
| MA-04 | Failover chain E2E |

---

## 4. Dependencies

- `FailoverClassifier` class (`failover_classifier.py`)
- `ProviderProfileKey` dataclass (`failover_classifier.py`)
- Redis 7.2 (cooldown key storage)
