---
sdlc_version: "6.1.1"
document_type: "Functional Requirement"
status: "PROPOSED"
sprint: "205"
spec_id: "FR-045"
tier: "PROFESSIONAL"
stage: "01 - Planning"
---

# FR-045: LangChain Provider Plugin

**Version**: 1.0.0
**Status**: PROPOSED
**Created**: February 2026
**Sprint**: 205
**Framework**: SDLC 6.1.1
**Epic**: EP-07 Multi-Agent Team Engine
**ADR**: ADR-066 (LangChain Multi-Agent Orchestration)
**Owner**: Backend Team
**Source**: CEO MAS Research (`mas/03-LANGCHAIN-IMPLEMENTATION.md`)

---

## 1. Overview

### 1.1 Purpose

Add LangChain as an optional provider in `agent_invoker.py._call_provider()` for multi-agent orchestration (EP-07). Enables structured output via `with_structured_output()`, unified tool calling via `StructuredTool`, and automatic token counting via callbacks.

### 1.2 Business Value

- Structured output eliminates regex parsing for agent responses (guaranteed JSON schema)
- Unified tool calling: 1 `StructuredTool` definition serves all providers (Ollama, Anthropic, OpenAI)
- Automatic token counting via `on_llm_end` callbacks (no manual parsing)
- Feature-flagged (`LANGCHAIN_ENABLED`) — zero disruption when disabled

### 1.3 Scope

LangChain is scoped to **multi-agent orchestration (EP-07, Layer 4)** only. Per ADR-066 Section 4, LangChain MUST NOT be used in:
- `chat_command_router.py` (ADR-064 scope)
- `ott_gateway.py` or any OTT channel processing
- Any Layer A component

---

## 2. Functional Requirements

### 2.1 Provider Branch

**GIVEN** an agent_definition with `provider="langchain"`
**WHEN** `AgentInvoker._call_provider()` is called
**THEN** the system SHALL dispatch to `_call_langchain()`
**AND** the result SHALL be an `InvocationResult` with the same schema as existing providers

### 2.2 Feature Flag Guard

**GIVEN** `LANGCHAIN_ENABLED=false` in config
**WHEN** an agent_definition with `provider="langchain"` is invoked
**THEN** the system SHALL raise `AgentInvokerError("LangChain provider is disabled")`
**AND** the failover classifier SHALL classify this as `format` reason (RETRY with different provider)

### 2.3 Optional Dependency Guard

**GIVEN** `langchain-anthropic` or `langchain-openai` is not installed
**WHEN** `langchain_provider.py` is imported
**THEN** the module SHALL NOT raise `ImportError`
**AND** a module-level `_LANGCHAIN_AVAILABLE = False` flag SHALL be set
**AND** calls to `LangChainProvider` SHALL raise `RuntimeError` with install instructions

### 2.4 ChatOllama Wrapper

**GIVEN** agent_definition with `provider="langchain"` and `model="qwen3-coder:30b"`
**WHEN** `LangChainProvider.invoke()` is called
**THEN** the system SHALL create a `ChatOllama` instance with:
  - `base_url` from `OLLAMA_BASE_URL` config
  - `model` from agent_definition
  - `temperature` from agent_definition
  - `num_predict` from agent_definition.max_tokens
**AND** the response SHALL be parsed into `InvocationResult`

### 2.5 ChatAnthropic Wrapper

**GIVEN** agent_definition with `provider="langchain"` and `model` containing "claude"
**WHEN** `LangChainProvider.invoke()` is called
**THEN** the system SHALL create a `ChatAnthropic` instance with:
  - `api_key` from `ANTHROPIC_API_KEY` config
  - `model` from agent_definition
  - `max_tokens` from agent_definition
**AND** the response SHALL be parsed into `InvocationResult`

### 2.6 Structured Output

**GIVEN** a Pydantic model class passed as `output_schema`
**WHEN** `LangChainProvider.invoke()` is called with `structured=True`
**THEN** the system SHALL call `model.with_structured_output(output_schema)`
**AND** the result SHALL be a validated Pydantic instance
**AND** invalid responses SHALL raise `AgentInvokerError("Structured output validation failed")`

### 2.7 Unified Tool Calling

**GIVEN** a list of `StructuredTool` definitions from `langchain_tool_registry.py`
**WHEN** `LangChainProvider.invoke()` is called with `tools=[...]`
**THEN** the system SHALL bind tools via `model.bind_tools(tools)`
**AND** tool calls SHALL be authorized via `authorize_tool_call()` before execution
**AND** unauthorized tool calls SHALL raise `PermissionDenied`

### 2.8 Token Counting Callback

**GIVEN** a LangChain invocation completes
**WHEN** the `on_llm_end` callback fires
**THEN** the system SHALL extract `input_tokens` and `output_tokens` from the response metadata
**AND** update the `InvocationResult` with accurate token counts
**AND** fallback to `tiktoken` estimation if metadata is unavailable

### 2.9 Failover Integration

**GIVEN** a LangChain invocation raises an exception
**WHEN** `FailoverClassifier.classify()` is called
**THEN** the system SHALL map LangChain exceptions to existing 6 failover reasons:
  - `AuthenticationError` → `auth` (ABORT)
  - `RateLimitError` → `rate_limit` (FALLBACK)
  - `APITimeoutError` → `timeout` (FALLBACK)
  - `BadRequestError` → `format` (RETRY)
  - `APIError` → `unknown` (ABORT)
**AND** cooldown keys SHALL use the same `{provider}:{account}:{region}:{model_family}` format

### 2.10 Tool Authorization Guard

**GIVEN** a LangChain tool is invoked during agent execution
**WHEN** `authorize_tool_call(tool_name, agent_config)` is called
**THEN** the system SHALL check `allowed_tools` and `denied_tools` from the agent definition
**AND** denied tools SHALL return `PermissionDenied` without executing the tool
**AND** all authorization checks SHALL be logged with `correlation_id`

---

## 3. LangChain Tool Registry

### 3.1 Five SDLC StructuredTools

| # | Tool Name | Description | Output Schema |
|---|-----------|-------------|---------------|
| 1 | `gate_status` | Check gate status and available actions | `GateStatusResult` |
| 2 | `submit_evidence` | Submit evidence to a gate | `EvidenceSubmitResult` |
| 3 | `read_file` | Read project file contents | `FileReadResult` |
| 4 | `run_tests` | Execute test suite | `TestRunResult` |
| 5 | `code_review` | Request code review from reviewer agent | `CodeReviewResult` |

### 3.2 Authorization Integration

**GIVEN** any StructuredTool is invoked
**WHEN** the tool's `_run()` method executes
**THEN** `authorize_tool_call()` SHALL be called first
**AND** the tool SHALL receive the current `tool_context` (project_id, org_id, user permissions)

---

## 4. Test Coverage

| Test ID | Description | Reference |
|---------|-------------|-----------|
| LC-01 | LangChain provider dispatches from _call_provider | ADR-066 §2.2 |
| LC-02 | Feature flag disabled raises AgentInvokerError | FR-045 §2.2 |
| LC-03 | Optional dependency guard (import without langchain) | FR-045 §2.3 |
| LC-04 | ChatOllama wrapper produces InvocationResult | FR-045 §2.4 |
| LC-05 | ChatAnthropic wrapper produces InvocationResult | FR-045 §2.5 |
| LC-06 | Structured output returns validated Pydantic | FR-045 §2.6 |
| LC-07 | Tool binding and authorization | FR-045 §2.7 |
| LC-08 | Token counting via callback | FR-045 §2.8 |
| LC-09 | LangChain exceptions mapped to failover reasons | FR-045 §2.9 |
| LC-10 | Unauthorized tool call raises PermissionDenied | FR-045 §2.10 |
| LT-01 | gate_status tool returns GateStatusResult | FR-045 §3.1 |
| LT-02 | submit_evidence tool returns EvidenceSubmitResult | FR-045 §3.1 |
| LT-03 | read_file tool checks authorize_tool_call | FR-045 §3.2 |
| LT-04 | Tool without permission denied | FR-045 §3.2 |
| LT-05 | All 5 tools have output schema parity | FR-045 §3.1 |

---

## 5. Dependencies

- `langchain_provider.py` (new file, ~200 LOC)
- `langchain_tool_registry.py` (new file, ~200 LOC)
- `agent_invoker.py` (modified, ~40 LOC — `_call_langchain()` branch)
- `failover_classifier.py` (modified, ~25 LOC — LangChain exception mapping)
- `tool_context.py` (modified, ~30 LOC — `authorize_tool_call()` guard)
- `config.py` (modified, ~10 LOC — `LANGCHAIN_ENABLED`, `LANGCHAIN_DEFAULT_MODEL`)
- `enterprise.txt` (modified — `langchain-anthropic`, `langchain-openai`, `langchain-community`)
