---
sdlc_version: "6.1.0"
document_type: "Functional Requirement"
status: "PROPOSED"
sprint: "179"
spec_id: "FR-042"
tier: "PROFESSIONAL"
stage: "01 - Planning"
---

# FR-042: Output Credential Scrubbing

**Version**: 1.0.0
**Status**: PROPOSED
**Created**: February 2026
**Sprint**: 179
**Framework**: SDLC 6.1.0
**Epic**: EP-07 Multi-Agent Team Engine
**ADR**: ADR-058 (ZeroClaw Pattern A)
**Owner**: Backend Team
**Source**: ZeroClaw `src/agent/loop_.rs` -> `scrub_credentials()`

---

## 1. Overview

### 1.1 Purpose

Scrub credentials and secrets from agent tool output BEFORE the output is fed back into the LLM context or stored in the evidence vault. Prevents CWE-200 (Exposure of Sensitive Information) by regex-matching credential patterns and redacting them while preserving the first 4 characters for debugging.

### 1.2 Business Value

- Prevents secrets leaking into `agent_messages` table (agent runs `env` -> API keys stored in plaintext)
- Prevents secrets being fed back to LLM (credential echo amplification)
- Compliance: CWE-200 mitigation, OWASP ASVS V5.1
- Defense-in-depth: Complements `InputSanitizer` (inbound) with output scrubbing (outbound)

---

## 2. Functional Requirements

### 2.1 Credential Pattern Detection

**GIVEN** agent tool output (e.g., shell command result, file read result)
**WHEN** the output is processed by `OutputScrubber`
**THEN** the system SHALL:
1. Match against 6 credential regex patterns in key:value format:
   - `token` — matches `token=`, `token:`, `TOKEN=` etc.
   - `api_key` or `apikey` — matches `api_key=`, `API_KEY:` etc.
   - `password` or `passwd` — matches `password=`, `PASSWD:` etc.
   - `secret` — matches `secret=`, `SECRET_KEY:` etc.
   - `bearer` — matches `Authorization: Bearer ...`, `bearer ...` etc.
   - `credential` — matches `credential=`, `CREDENTIAL:` etc.
2. Redact matched values: preserve first 4 chars + `****[REDACTED]`
3. Return scrubbed text + list of scrubbed pattern names
4. Log scrub events for security audit trail

### 2.2 Dual Integration Points (CTO Amendment)

**GIVEN** agent invocation completes with `InvocationResult.content`
**WHEN** the result is returned from `AgentInvoker.invoke()`
**THEN** the system SHALL scrub credentials from `content` BEFORE returning to caller

**GIVEN** an agent message is captured as evidence
**WHEN** `EvidenceCollector.capture_message()` processes the message
**THEN** the system SHALL scrub credentials from `message.content` BEFORE computing SHA256 hash
**AND** the order SHALL be: scrub -> hash -> store

### 2.3 Non-Destructive Scrubbing

**GIVEN** output that contains no credential patterns
**WHEN** processed by `OutputScrubber`
**THEN** the output SHALL be returned unchanged (no false positives on normal text)

### 2.4 Short Value Handling

**GIVEN** a matched credential value with fewer than 4 characters
**WHEN** the value is redacted
**THEN** the entire value SHALL be preserved + `****[REDACTED]` appended

---

## 3. Test Coverage

| Test ID | Description | Reference |
|---------|-------------|-----------|
| CS-01 | Token pattern scrubbed | ADR-058 S1 |
| CS-02 | API key pattern scrubbed | ADR-058 S1 |
| CS-03 | Password pattern scrubbed | ADR-058 S1 |
| CS-04 | Bearer token scrubbed | ADR-058 S1 |
| CS-05 | Secret pattern scrubbed | ADR-058 S1 |
| CS-06 | Clean output unchanged | ADR-058 S1 |
| CS-07 | Multiple matches all scrubbed | ADR-058 S1 |
| CS-08 | Short value handling | ADR-058 S1 |
| CS-09 | Invoker integration (post-invocation scrub) | ADR-058 S1 |
| CS-10 | Evidence integration (scrub -> hash -> store) | ADR-058 S1 |

---

## 4. Dependencies

- `OutputScrubber` class (`output_scrubber.py`, new file)
- `AgentInvoker` class (`agent_invoker.py`, modified)
- `EvidenceCollector` class (`evidence_collector.py`, modified)
- ZeroClaw source: `src/agent/loop_.rs` -> `scrub_credentials()`
