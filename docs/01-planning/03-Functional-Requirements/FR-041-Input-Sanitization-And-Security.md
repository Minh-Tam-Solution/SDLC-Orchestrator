---
sdlc_version: "6.1.0"
document_type: "Functional Requirement"
status: "PROPOSED"
sprint: "176"
spec_id: "FR-041"
tier: "PROFESSIONAL"
stage: "01 - Planning"
---

# FR-041: Input Sanitization and Security Guards

**Version**: 1.0.0
**Status**: PROPOSED
**Created**: February 2026
**Sprint**: 176-177
**Framework**: SDLC 6.1.0
**Epic**: EP-07 Multi-Agent Team Engine
**ADR**: ADR-056 (Non-Negotiable #4: Input Sanitizer, #5: Shell Guard)
**Owner**: Backend Team

---

## 1. Overview

### 1.1 Purpose

Protect agent execution from prompt injection, shell command injection, and workspace escape. Implements 12 input sanitization patterns (OpenClaw Pattern 9) and 8 shell deny patterns (Nanobot N6). All external input is wrapped in safety tags before entering agent context.

### 1.2 Business Value

- Prevents prompt injection attacks via OTT channels (CRITICAL threat T4)
- Prevents shell command injection (CRITICAL threat T9)
- Defense-in-depth: wrapping + pattern detection + path restriction
- Compliance: OWASP ASVS V5.1 Input Validation

---

## 2. Functional Requirements

### 2.1 Input Sanitization (Non-Negotiable #4)

**GIVEN** external input from OTT channels or user messages
**WHEN** the input is processed by `InputSanitizer`
**THEN** the system SHALL:
1. Check against 12 injection regex patterns:
   - system_prompt_override (`ignore previous|forget your instructions`)
   - role_injection (`you are now|act as|pretend to be`)
   - delimiter_escape (`<\|system\|>|<\|end\|>|\[INST\]`)
   - base64_payload (`execute.*base64|decode.*base64|base64.*eval`)
   - prompt_leak_attempt (`show.*system prompt|reveal.*instructions`)
   - instruction_override (`override.*instructions|new rules`)
   - jailbreak_prefix (`DAN mode|jailbreak|evil mode`)
   - xml_injection (`<system>|<assistant>|</user>`)
   - markdown_injection (`\[.*\]\(javascript:|!\[.*\]\(data:`)
   - unicode_escape (`\\u0000|\\x00|%00`)
   - repetition_attack (same char repeated 50+ times)
   - data_exfil_url (`fetch\(|XMLHttpRequest|navigator\.sendBeacon`)
2. Return list of violation names
3. Log violations for security audit trail

### 2.2 External Input Wrapping

**GIVEN** any external input that passes or fails sanitization
**WHEN** the input is prepared for agent context
**THEN** the system SHALL wrap it as: `[EXTERNAL_INPUT channel=ott]{content}[/EXTERNAL_INPUT]`

### 2.3 Reflect Step (Nanobot)

**GIVEN** a batch of tool results has been executed
**WHEN** `should_reflect()` returns true (error detected OR batch_index matches frequency)
**THEN** the system SHALL inject a reflection prompt into the conversation messages

**GIVEN** `reflect_frequency = 0` on the agent definition
**THEN** reflection SHALL be completely disabled (even on errors)

---

## 3. Test Coverage

| Test ID | Description | Non-Negotiable |
|---------|-------------|---------------|
| IS-01 to IS-10 | Input sanitizer pattern tests | #4 |
| RS-01 to RS-07 | Reflect step tests | — |

---

## 4. Dependencies

- `InputSanitizer` class (`input_sanitizer.py`)
- `ReflectStep` class (`reflect_step.py`)
- OpenClaw source: `src/security/external-content.ts` (12 patterns)
