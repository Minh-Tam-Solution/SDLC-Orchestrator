# KIẾN TRÚC MULTI-AGENT SYSTEM — SDLC-ALIGNED AUTONOMOUS DEVELOPMENT

**Date**: 2026-02-23 | **Author**: AI Architect | **Format**: TOON | **Version**: 1.0.0

---

## 1. SYSTEM OVERVIEW

### 1.1 Vision Statement

**Goal**: Tự động phát triển phần mềm từ BRD/PRD → Production-ready code với governance tích hợp

**Input**: Product description, BRD (Business Requirements Document)
**Output**: Deployed application + Full evidence trail (code, tests, docs, SAST reports)

**Differentiator**: KHÔNG phải AI coder thay thế con người, mà là **AI Team** làm việc DƯỚI sự giám sát của Quality Gates.

### 1.2 High-Level Architecture

```
┌────────────────────────────────────────────────────────────────┐
│  USER INPUT (BRD/PRD)                                           │
└──────────────────────┬─────────────────────────────────────────┘
                       ↓
┌────────────────────────────────────────────────────────────────┐
│  ASSISTANT AGENT (Router)                                       │
│  - Parse user intent                                            │
│  - Ask clarifying questions                                     │
│  - Route to appropriate workflow                                │
└──────────────────────┬─────────────────────────────────────────┘
                       ↓
┌────────────────────────────────────────────────────────────────┐
│  STAGE 00-01: DESIGN THINKING & REQUIREMENTS (G0 → G1)          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Researcher  │→│  PM Agent    │→│  PJM Agent   │         │
│  │  (Domain)    │  │  (BRD/PRD)   │  │  (Breakdown) │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                            ↓                                    │
│  [GATE G1: Design Ready — CPO Approval via OTT]                │
└──────────────────────┬─────────────────────────────────────────┘
                       ↓
┌────────────────────────────────────────────────────────────────┐
│  STAGE 02: ARCHITECTURE DESIGN (G1 → G2)                        │
│  ┌──────────────┐  ┌──────────────┐                            │
│  │  Architect   │→│  Reviewer    │ (Design Review)            │
│  │  (ERD, API)  │  │  (Audit)     │                            │
│  └──────────────┘  └──────────────┘                            │
│                            ↓                                    │
│  [GATE G2: Security + Architecture — CTO Approval via OTT]     │
└──────────────────────┬─────────────────────────────────────────┘
                       ↓
┌────────────────────────────────────────────────────────────────┐
│  STAGE 03-04: IMPLEMENTATION (G2 → G3)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Coder       │↔│  Reviewer    │  │  Tester      │         │
│  │  (Features)  │  │  (Code Rev)  │  │  (Tests)     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│           ↓              ↓                  ↓                   │
│  [EP-06 Codegen: 4-Gate Quality Pipeline]                      │
│  [SAST Scan: Semgrep + OWASP rules]                            │
│  [Test Execution: pytest + coverage report]                    │
│                            ↓                                    │
│  [GATE G3: Ship Ready — CTO Approval via OTT]                  │
└──────────────────────┬─────────────────────────────────────────┘
                       ↓
┌────────────────────────────────────────────────────────────────┐
│  STAGE 05: DEPLOYMENT (G3 → G4)                                 │
│  ┌──────────────┐  ┌──────────────┐                            │
│  │  DevOps      │→│  Tester      │ (Smoke tests)              │
│  │  (Deploy)    │  │  (Validate)  │                            │
│  └──────────────┘  └──────────────┘                            │
│                            ↓                                    │
│  [GATE G4: Production Validation — CEO Approval via OTT]       │
└────────────────────────────────────────────────────────────────┘

OBSERVABILITY LAYER (runs in parallel):
- Evidence Vault: Auto-capture all artifacts (correlation_id)
- Budget Guard: Token cost tracking + circuit breaker
- Security Guard: Input sanitizer + Shell guard + Credential scrubber
```

---

## 2. AGENT ROLES & RESPONSIBILITIES

### 2.1 Router Layer (1 agent)

#### **Assistant Agent** (Router)

**Type**: LangChain Routing Agent (OpenAI Functions / LangGraph conditional edges)

**Responsibilities**:
1. Parse user input (BRD, PRD, or natural language description)
2. Ask clarifying questions (feature list, tech stack, constraints)
3. Route to appropriate SDLC stage workflow
4. Handle simple Q&A (project status, documentation lookup)

**Tools**:
- `parse_brd_tool` — Extract structured data from BRD/PRD
- `ask_question_tool` — Generate clarifying questions
- `search_knowledge_base_tool` — RAG over past projects
- `route_to_workflow_tool` — Select workflow (design → code → deploy)

**LangChain Implementation**:
```python
from langchain.agents import create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate

assistant_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an AI Assistant for SDLC Orchestrator.
    Your job: understand user intent, ask clarifying questions, route to appropriate workflow.

    Available workflows:
    - design_thinking_workflow: For new projects (Stage 00-01)
    - requirements_workflow: For existing projects needing new features (Stage 01)
    - coding_workflow: For implementation tasks (Stage 03-04)
    - deployment_workflow: For deployment tasks (Stage 05)

    Always clarify:
    1. Project name & description
    2. Target users & use cases
    3. Tech stack preferences (if any)
    4. Constraints (budget, timeline, compliance)
    """),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])

assistant_agent = create_openai_functions_agent(
    llm=ollama_llm,  # qwen3:32b (Vietnamese excellent)
    tools=[parse_brd_tool, ask_question_tool, search_knowledge_base_tool, route_to_workflow_tool],
    prompt=assistant_prompt
)
```

---

### 2.2 SE4A Layer (Software Engineering for Agents) — 8 agents

#### **2.2.1 Researcher Agent**

**Stage**: 00 (WHY) — Design Thinking
**Gate Output**: Research findings → G0.1 (Foundation Ready)

**Responsibilities**:
1. Gather domain knowledge (web search, documentation)
2. Analyze similar systems (competitor analysis)
3. Identify technical challenges & solutions

**Tools**:
- `web_search_tool` — Tavily/Serper API
- `github_search_tool` — Search GitHub repos for similar projects
- `documentation_scraper_tool` — Extract content from docs sites
- `competitor_analysis_tool` — Compare features

**LangChain Implementation**:
```python
from langchain.agents import create_react_agent
from langchain_community.tools import TavilySearchResults

researcher_agent = create_react_agent(
    llm=ollama_llm,  # qwen3:32b
    tools=[
        TavilySearchResults(max_results=5),
        github_search_tool,
        documentation_scraper_tool,
        competitor_analysis_tool
    ],
    prompt=researcher_prompt
)
```

---

#### **2.2.2 PM Agent (Product Manager)**

**Stage**: 01 (WHAT) — Requirements
**Gate Output**: BRD/PRD → G1 (Design Ready, CPO approval)

**Responsibilities**:
1. Ask clarifying questions about features
2. Write structured BRD/PRD (markdown format)
3. Prioritize features (MoSCoW method)
4. Define acceptance criteria

**Tools**:
- `ask_stakeholder_tool` — Interactive Q&A with user
- `brd_template_tool` — Generate BRD from template
- `prd_template_tool` — Generate PRD from template
- `prioritization_tool` — MoSCoW matrix generator

**LangChain Implementation**:
```python
from langchain.agents import create_structured_chat_agent
from langchain.output_parsers import PydanticOutputParser

# Pydantic schema for structured BRD
class BRD(BaseModel):
    project_name: str
    business_objectives: List[str]
    target_users: List[str]
    features: List[Feature]  # Feature = {name, description, priority: MUST/SHOULD/COULD/WONT}
    constraints: List[str]  # budget, timeline, compliance

pm_agent = create_structured_chat_agent(
    llm=ollama_llm,  # qwen3:32b
    tools=[ask_stakeholder_tool, brd_template_tool, prd_template_tool],
    prompt=pm_prompt,
    output_parser=PydanticOutputParser(pydantic_object=BRD)
)
```

---

#### **2.2.3 PJM Agent (Project Manager)**

**Stage**: 01 (WHAT) — Requirements
**Gate Output**: Task breakdown → Sprint plan

**Responsibilities**:
1. Break down PRD into tasks (MUST features → tasks)
2. Estimate effort (T-shirt sizing: S/M/L)
3. Create sprint plan (5-10 day sprints)
4. Assign tasks to agents (Architect, Coder, Tester, DevOps)

**Tools**:
- `task_breakdown_tool` — Feature → subtasks
- `effort_estimation_tool` — T-shirt sizing
- `sprint_planning_tool` — Create sprint via SDLC Orchestrator API
- `agent_assignment_tool` — Assign tasks to agents

**LangChain Implementation**:
```python
from langchain.agents import create_plan_and_execute_agent
from langchain.chains import LLMChain

# Planner: Break down PRD into tasks
planner = LLMChain(
    llm=ollama_llm,
    prompt=task_breakdown_prompt,
    output_key="tasks"
)

# Executor: Execute tasks (delegate to other agents)
pjm_agent = create_plan_and_execute_agent(
    llm=ollama_llm,
    planner=planner,
    tools=[effort_estimation_tool, sprint_planning_tool, agent_assignment_tool]
)
```

---

#### **2.2.4 Architect Agent**

**Stage**: 02 (HOW) — Design
**Gate Output**: System design docs (ERD, API spec, architecture diagram) → G2 (Security + Architecture, CTO approval)

**Responsibilities**:
1. Design database schema (ERD)
2. Design API specification (OpenAPI 3.0)
3. Create system architecture diagram (C4 model)
4. Select technology stack (FastAPI, PostgreSQL, React, etc.)

**Tools**:
- `erd_generator_tool` — Generate Mermaid ERD from schema
- `api_spec_generator_tool` — Generate OpenAPI spec
- `architecture_diagram_tool` — C4 model generator
- `tech_stack_selector_tool` — Recommend tech stack based on requirements

**LangChain Implementation**:
```python
from langchain.agents import create_react_agent

architect_agent = create_react_agent(
    llm=ollama_llm,  # qwen3-coder:30b (256K context for large specs)
    tools=[
        erd_generator_tool,
        api_spec_generator_tool,
        architecture_diagram_tool,
        tech_stack_selector_tool
    ],
    prompt=architect_prompt
)
```

---

#### **2.2.5 Coder Agent**

**Stage**: 03-04 (BUILD) — Implementation
**Gate Output**: Production-ready code → G3 (Ship Ready, CTO approval)

**Responsibilities**:
1. Generate code from PRD + Architecture spec
2. Follow coding standards (PEP 8, ESLint, etc.)
3. Integrate with SDLC Orchestrator EP-06 Codegen Pipeline
4. Upload code to Evidence Vault

**Tools**:
- `ep06_codegen_tool` — Generate code via EP-06 (4-Gate Quality Pipeline)
- `code_review_self_tool` — Self-review generated code
- `upload_evidence_tool` — Upload code to Evidence Vault
- `git_operations_tool` — Create branch, commit, push

**LangChain Implementation**:
```python
from langchain.agents import create_openai_tools_agent

coder_agent = create_openai_tools_agent(
    llm=ollama_llm,  # qwen3-coder:30b
    tools=[
        ep06_codegen_tool,
        code_review_self_tool,
        upload_evidence_tool,
        git_operations_tool
    ],
    prompt=coder_prompt
)

# EP-06 Integration
async def ep06_codegen_tool(spec: str, language: str = "python") -> dict:
    """Generate code via SDLC Orchestrator EP-06 Codegen Pipeline"""
    response = await sdlc_api.post("/api/v1/codegen/generate", json={
        "spec": spec,
        "language": language,
        "quality_mode": "production",  # SCAFFOLD or PRODUCTION
        "max_retries": 3
    })
    return response.json()  # {session_id, status, artifacts, quality_results}
```

---

#### **2.2.6 Reviewer Agent**

**Stage**: 03-04 (BUILD) — Code Review
**Gate Output**: Code review report + approval/reject decision

**Responsibilities**:
1. Review code against coding standards
2. Check for security vulnerabilities (complement SAST)
3. Verify test coverage (>90% target)
4. Suggest improvements

**Tools**:
- `static_analysis_tool` — Run ruff, mypy, ESLint
- `sast_tool` — Trigger Semgrep scan via SDLC API
- `test_coverage_tool` — Parse pytest coverage report
- `code_quality_scorer_tool` — Score code quality (0-100)

**LangChain Implementation**:
```python
from langchain.agents import create_react_agent

reviewer_agent = create_react_agent(
    llm=ollama_llm,  # deepseek-r1:32b (reasoning mode for thorough review)
    tools=[
        static_analysis_tool,
        sast_tool,
        test_coverage_tool,
        code_quality_scorer_tool
    ],
    prompt=reviewer_prompt
)
```

---

#### **2.2.7 Tester Agent**

**Stage**: 03-04 (BUILD) — Testing
**Gate Output**: Test suites (unit + integration + E2E) + test results

**Responsibilities**:
1. Generate test cases from requirements
2. Write unit tests (pytest, Jest)
3. Write integration tests (API contract tests)
4. Write E2E tests (Playwright)

**Tools**:
- `test_case_generator_tool` — Generate test cases from PRD
- `pytest_runner_tool` — Execute pytest suites
- `jest_runner_tool` — Execute Jest suites
- `playwright_runner_tool` — Execute E2E tests

**LangChain Implementation**:
```python
from langchain.agents import create_react_agent

tester_agent = create_react_agent(
    llm=ollama_llm,  # qwen3-coder:30b
    tools=[
        test_case_generator_tool,
        pytest_runner_tool,
        jest_runner_tool,
        playwright_runner_tool
    ],
    prompt=tester_prompt
)
```

---

#### **2.2.8 DevOps Agent**

**Stage**: 05 (DEPLOY) — Deployment
**Gate Output**: Deployed application + health check results → G4 (Production Validation, CEO approval)

**Responsibilities**:
1. Build Docker images
2. Deploy to staging/production (Kubernetes)
3. Run smoke tests
4. Monitor health metrics

**Tools**:
- `docker_build_tool` — Build Docker images
- `kubectl_tool` — Deploy to Kubernetes
- `smoke_test_tool` — Run smoke tests
- `health_check_tool` — Check application health

**LangChain Implementation**:
```python
from langchain.agents import create_react_agent

devops_agent = create_react_agent(
    llm=ollama_llm,  # qwen3:14b (fast for simple ops)
    tools=[
        docker_build_tool,
        kubectl_tool,
        smoke_test_tool,
        health_check_tool
    ],
    prompt=devops_prompt
)
```

---

### 2.3 SE4H Layer (Software Engineering for Humans) — 3 agents

#### **Human Approval Agents** (CEO, CPO, CTO)

**Implementation**: NOT LangChain agents, but **human-in-the-loop** via OTT Gateway (Telegram/Zalo)

```python
async def request_human_approval(gate_id: str, approver_role: str, gate_type: str):
    """Send OTT notification for gate approval"""
    # Get gate details
    gate = await sdlc_api.get(f"/api/v1/gates/{gate_id}")

    # Prepare approval message
    message = f"""
🚪 Gate {gate_type} requires approval

**Project**: {gate['project_name']}
**Gate**: {gate['title']}
**Status**: {gate['status']}
**Evidence**: {len(gate['evidence'])} artifacts uploaded
**Review**: {gate['policy_result']['pass_rate']}% policies passed

**Actions**:
- Reply APPROVE to approve
- Reply REJECT <reason> to reject
- Reply DETAILS for more information

**Timeout**: 24 hours (will escalate to CEO if no response)
    """

    # Send via OTT Gateway
    await sdlc_api.post("/api/v1/ott/messages/send", json={
        "channel": "telegram",  # or "zalo"
        "recipient": approver_role,  # "cto", "cpo", "ceo"
        "text": message
    })

    # Wait for response (with timeout)
    response = await wait_for_ott_response(
        gate_id=gate_id,
        timeout=86400  # 24h
    )

    if response.action == "APPROVE":
        await sdlc_api.post(f"/api/v1/gates/{gate_id}/approve", json={
            "comments": f"Approved via OTT by {approver_role}"
        })
    elif response.action == "REJECT":
        await sdlc_api.post(f"/api/v1/gates/{gate_id}/reject", json={
            "reason": response.reason,
            "comments": f"Rejected via OTT by {approver_role}"
        })
```

---

## 3. ORCHESTRATION PATTERNS

### 3.1 Pattern 1: Sequential Pipeline (SDLC Stages)

**Use Case**: Linear workflow G0 → G1 → G2 → G3 → G4

**LangGraph Implementation**:

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

# Define state
class ProjectState(TypedDict):
    brd: str  # Business Requirements Document
    prd: str  # Product Requirements Document
    architecture: dict  # ERD, API spec, architecture diagram
    code: dict  # Generated code artifacts
    tests: dict  # Test suites
    deployment: dict  # Deployment results
    gate_g1_approved: bool
    gate_g2_approved: bool
    gate_g3_approved: bool
    gate_g4_approved: bool
    messages: Annotated[list, operator.add]  # Conversation history

# Define nodes (agents)
async def researcher_node(state: ProjectState) -> ProjectState:
    """G0: Research domain & similar systems"""
    research_results = await researcher_agent.ainvoke({
        "task": "Research domain for: " + state["brd"],
        "chat_history": state["messages"]
    })
    state["messages"].append(("researcher", research_results["output"]))
    return state

async def pm_node(state: ProjectState) -> ProjectState:
    """G1: Write PRD"""
    prd = await pm_agent.ainvoke({
        "brd": state["brd"],
        "research": state["messages"][-1][1],  # Last researcher output
        "chat_history": state["messages"]
    })
    state["prd"] = prd["output"]
    state["messages"].append(("pm", prd["output"]))

    # Create G1 gate
    gate_g1 = await create_gate_tool.ainvoke({
        "gate_type": "G1_CONSULTATION",
        "title": "Design Ready - CPO Approval",
        "description": "PRD ready for CPO review"
    })

    # Request CPO approval (human-in-the-loop)
    approval = await request_human_approval(
        gate_id=gate_g1["id"],
        approver_role="cpo",
        gate_type="G1"
    )
    state["gate_g1_approved"] = approval
    return state

async def architect_node(state: ProjectState) -> ProjectState:
    """G2: Design architecture"""
    architecture = await architect_agent.ainvoke({
        "prd": state["prd"],
        "chat_history": state["messages"]
    })
    state["architecture"] = architecture["output"]
    state["messages"].append(("architect", str(architecture["output"])))

    # Create G2 gate
    gate_g2 = await create_gate_tool.ainvoke({
        "gate_type": "G2_SECURITY_ARCHITECTURE",
        "title": "Security + Architecture - CTO Approval",
        "description": "Architecture ready for CTO review"
    })

    # Request CTO approval
    approval = await request_human_approval(
        gate_id=gate_g2["id"],
        approver_role="cto",
        gate_type="G2"
    )
    state["gate_g2_approved"] = approval
    return state

async def coder_node(state: ProjectState) -> ProjectState:
    """G3: Generate code"""
    code = await coder_agent.ainvoke({
        "prd": state["prd"],
        "architecture": state["architecture"],
        "chat_history": state["messages"]
    })
    state["code"] = code["output"]
    state["messages"].append(("coder", str(code["output"])))
    return state

async def reviewer_node(state: ProjectState) -> ProjectState:
    """G3: Review code"""
    review = await reviewer_agent.ainvoke({
        "code": state["code"],
        "prd": state["prd"],
        "chat_history": state["messages"]
    })
    state["messages"].append(("reviewer", review["output"]))

    # Check if review passed
    if review["output"]["status"] != "PASS":
        # Loop back to coder with feedback
        state["messages"].append(("system", "Code review failed, retrying coder..."))
        return state  # Will trigger coder_node again

    # Create G3 gate
    gate_g3 = await create_gate_tool.ainvoke({
        "gate_type": "G3_SHIP_READY",
        "title": "Ship Ready - CTO Approval",
        "description": "Code ready for deployment"
    })

    # Request CTO approval
    approval = await request_human_approval(
        gate_id=gate_g3["id"],
        approver_role="cto",
        gate_type="G3"
    )
    state["gate_g3_approved"] = approval
    return state

async def devops_node(state: ProjectState) -> ProjectState:
    """G4: Deploy"""
    deployment = await devops_agent.ainvoke({
        "code": state["code"],
        "chat_history": state["messages"]
    })
    state["deployment"] = deployment["output"]
    state["messages"].append(("devops", str(deployment["output"])))

    # Create G4 gate
    gate_g4 = await create_gate_tool.ainvoke({
        "gate_type": "G4_PRODUCTION_VALIDATION",
        "title": "Production Validation - CEO Approval",
        "description": "Application deployed and validated"
    })

    # Request CEO approval
    approval = await request_human_approval(
        gate_id=gate_g4["id"],
        approver_role="ceo",
        gate_type="G4"
    )
    state["gate_g4_approved"] = approval
    return state

# Build graph
workflow = StateGraph(ProjectState)

# Add nodes
workflow.add_node("researcher", researcher_node)
workflow.add_node("pm", pm_node)
workflow.add_node("architect", architect_node)
workflow.add_node("coder", coder_node)
workflow.add_node("reviewer", reviewer_node)
workflow.add_node("devops", devops_node)

# Add edges (conditional)
workflow.set_entry_point("researcher")
workflow.add_edge("researcher", "pm")
workflow.add_conditional_edges(
    "pm",
    lambda state: "architect" if state["gate_g1_approved"] else END
)
workflow.add_conditional_edges(
    "architect",
    lambda state: "coder" if state["gate_g2_approved"] else END
)
workflow.add_edge("coder", "reviewer")
workflow.add_conditional_edges(
    "reviewer",
    lambda state: "devops" if state["gate_g3_approved"] else "coder"  # Loop if review failed
)
workflow.add_conditional_edges(
    "devops",
    lambda state: END if state["gate_g4_approved"] else END
)

# Compile
app = workflow.compile()
```

---

### 3.2 Pattern 2: Reflection Loop (Coder ↔ Reviewer)

**Use Case**: Iterative code improvement với feedback loop

```python
from langgraph.graph import StateGraph

class CodeReviewState(TypedDict):
    spec: str
    code: str
    review_feedback: str
    retry_count: int
    max_retries: int
    status: str  # "in_progress", "pass", "fail"
    messages: list

async def coder_with_feedback(state: CodeReviewState) -> CodeReviewState:
    """Generate code (with optional feedback from previous iteration)"""
    prompt = f"Generate code for:\n{state['spec']}"
    if state["review_feedback"]:
        prompt += f"\n\nPrevious attempt feedback:\n{state['review_feedback']}"
        prompt += f"\n\nRetry {state['retry_count']}/{state['max_retries']}"

    code = await coder_agent.ainvoke({"prompt": prompt})
    state["code"] = code["output"]
    state["messages"].append(("coder", code["output"]))
    return state

async def reviewer_with_criteria(state: CodeReviewState) -> CodeReviewState:
    """Review code against quality criteria"""
    review = await reviewer_agent.ainvoke({
        "code": state["code"],
        "criteria": ["syntax", "security", "test_coverage", "documentation"]
    })

    if review["output"]["status"] == "PASS":
        state["status"] = "pass"
    else:
        state["review_feedback"] = review["output"]["feedback"]
        state["retry_count"] += 1
        if state["retry_count"] >= state["max_retries"]:
            state["status"] = "fail"
        else:
            state["status"] = "in_progress"

    state["messages"].append(("reviewer", review["output"]))
    return state

# Reflection loop graph
reflection_workflow = StateGraph(CodeReviewState)
reflection_workflow.add_node("coder", coder_with_feedback)
reflection_workflow.add_node("reviewer", reviewer_with_criteria)

reflection_workflow.set_entry_point("coder")
reflection_workflow.add_edge("coder", "reviewer")
reflection_workflow.add_conditional_edges(
    "reviewer",
    lambda state: "coder" if state["status"] == "in_progress" else END
)

reflection_app = reflection_workflow.compile()
```

---

### 3.3 Pattern 3: Supervisor (Parallel Task Execution)

**Use Case**: PJM distributes tasks to multiple agents in parallel

```python
from langgraph.graph import StateGraph
import asyncio

class TaskDistributionState(TypedDict):
    tasks: List[dict]  # [{agent: "coder", task: "implement auth"}, ...]
    results: dict  # {agent: result}
    messages: list

async def distribute_tasks(state: TaskDistributionState) -> TaskDistributionState:
    """Distribute tasks to agents in parallel"""
    async def execute_task(task: dict):
        agent_name = task["agent"]
        task_description = task["task"]

        # Get agent by name
        agent_map = {
            "coder": coder_agent,
            "tester": tester_agent,
            "reviewer": reviewer_agent,
            "devops": devops_agent
        }
        agent = agent_map[agent_name]

        # Execute task
        result = await agent.ainvoke({"task": task_description})
        return {agent_name: result["output"]}

    # Execute all tasks in parallel
    results = await asyncio.gather(*[execute_task(task) for task in state["tasks"]])

    # Merge results
    for result in results:
        state["results"].update(result)

    state["messages"].append(("supervisor", f"Completed {len(results)} tasks"))
    return state

supervisor_workflow = StateGraph(TaskDistributionState)
supervisor_workflow.add_node("distribute", distribute_tasks)
supervisor_workflow.set_entry_point("distribute")
supervisor_workflow.add_edge("distribute", END)

supervisor_app = supervisor_workflow.compile()
```

---

## 4. MEMORY STRATEGY

### 4.1 Three-Tier Memory Architecture

```python
from langchain.memory import (
    ConversationBufferMemory,
    ConversationSummaryMemory,
    ConversationEntityMemory
)
from langchain.vectorstores import Chroma
from langchain.embeddings import OllamaEmbeddings

class MASMemoryManager:
    def __init__(self):
        # Tier 1: Short-term (conversation buffer)
        self.short_term = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            max_messages=50  # Last 50 messages
        )

        # Tier 2: Medium-term (conversation summary)
        self.medium_term = ConversationSummaryMemory(
            llm=ollama_llm,  # qwen3:8b (fast for summarization)
            memory_key="conversation_summary",
            return_messages=False
        )

        # Tier 3: Long-term (vector store RAG)
        self.long_term = Chroma(
            collection_name="project_knowledge",
            embedding_function=OllamaEmbeddings(model="bge-m3:latest"),
            persist_directory="./chroma_db"
        )

        # Entity memory (track features, technologies, constraints)
        self.entity_memory = ConversationEntityMemory(
            llm=ollama_llm,
            entity_extraction_prompt="""Extract entities:
            - Features: {feature_name, description, status}
            - Technologies: {name, version, purpose}
            - Constraints: {type, description, impact}
            """
        )

    async def store_project_artifact(self, artifact_type: str, content: str, metadata: dict):
        """Store project artifact in long-term memory"""
        await self.long_term.aadd_texts(
            texts=[content],
            metadatas=[{
                "artifact_type": artifact_type,
                "project_id": metadata["project_id"],
                "gate_type": metadata.get("gate_type"),
                "timestamp": metadata["timestamp"]
            }]
        )

    async def retrieve_similar_projects(self, query: str, k: int = 3):
        """RAG: Retrieve similar past projects"""
        results = await self.long_term.asimilarity_search(query, k=k)
        return results

    async def compact_history(self, threshold: float = 0.8):
        """Compact conversation history when reaching 80% capacity (ZeroClaw pattern)"""
        messages = self.short_term.chat_memory.messages
        if len(messages) >= 50 * threshold:
            # Summarize oldest 20 messages
            old_messages = messages[:20]
            summary = await self.medium_term.predict_new_summary(
                messages=old_messages,
                existing_summary=""
            )

            # Replace oldest messages with summary
            self.short_term.chat_memory.messages = [
                {"role": "system", "content": f"[Summary of previous conversation: {summary}]"}
            ] + messages[20:]
```

---

## 5. TOOL INTEGRATION

### 5.1 SDLC Orchestrator API Tools

```python
from langchain.tools import StructuredTool
from pydantic import BaseModel, Field
import httpx

# Pydantic schemas for tool inputs
class GateCreateInput(BaseModel):
    gate_type: str = Field(..., description="Gate type: G1_CONSULTATION, G2_SECURITY_ARCHITECTURE, G3_SHIP_READY, G4_PRODUCTION_VALIDATION")
    title: str = Field(..., description="Gate title")
    description: str = Field(None, description="Gate description")
    project_id: str = Field(..., description="Project UUID")

class EvidenceUploadInput(BaseModel):
    file_path: str = Field(..., description="Path to evidence file")
    evidence_type: str = Field(..., description="Evidence type: DESIGN_DOCUMENT, TEST_RESULTS, CODE_REVIEW, etc")
    gate_id: str = Field(..., description="Gate UUID to attach evidence to")

class CodegenInput(BaseModel):
    spec: str = Field(..., description="Code specification (PRD, feature description)")
    language: str = Field("python", description="Programming language")
    quality_mode: str = Field("production", description="SCAFFOLD or PRODUCTION")

# SDLC API client
class SDLCAPIClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.client = httpx.AsyncClient(base_url=base_url, headers=self.headers)

    async def create_gate(self, input: GateCreateInput) -> dict:
        response = await self.client.post("/api/v1/gates", json=input.dict())
        response.raise_for_status()
        return response.json()

    async def upload_evidence(self, input: EvidenceUploadInput) -> dict:
        with open(input.file_path, "rb") as f:
            files = {"file": f}
            data = {
                "gate_id": input.gate_id,
                "type": input.evidence_type
            }
            response = await self.client.post("/api/v1/evidence/upload", files=files, data=data)
        response.raise_for_status()
        return response.json()

    async def generate_code(self, input: CodegenInput) -> dict:
        response = await self.client.post("/api/v1/codegen/generate", json=input.dict())
        response.raise_for_status()
        return response.json()

# Create LangChain tools
sdlc_client = SDLCAPIClient(
    base_url="http://localhost:8300",
    api_key="your-api-key"
)

create_gate_tool = StructuredTool.from_function(
    func=sdlc_client.create_gate,
    name="create_quality_gate",
    description="Create a quality gate (G1/G2/G3/G4) in SDLC Orchestrator",
    args_schema=GateCreateInput
)

upload_evidence_tool = StructuredTool.from_function(
    func=sdlc_client.upload_evidence,
    name="upload_evidence",
    description="Upload evidence (code, docs, tests) to Evidence Vault",
    args_schema=EvidenceUploadInput
)

codegen_tool = StructuredTool.from_function(
    func=sdlc_client.generate_code,
    name="generate_code",
    description="Generate production-ready code via EP-06 Codegen Pipeline",
    args_schema=CodegenInput
)
```

---

## 6. COST & LATENCY OPTIMIZATION

### 6.1 Budget Guard (Circuit Breaker)

```python
class BudgetGuard:
    """Per-conversation token budget circuit breaker (ADR-056 O3)"""

    def __init__(self, max_budget_cents: int):
        self.max_budget_cents = max_budget_cents
        self.spent_cents = 0
        self.usage_log = []

    def estimate_cost(self, prompt: str, model: str) -> int:
        """Estimate cost before execution"""
        tokens = len(prompt.split()) * 1.3  # Rough estimate (1 word ≈ 1.3 tokens)
        cost_per_1k_tokens = {
            "qwen3-coder:30b": 0,  # Ollama self-hosted
            "qwen3:32b": 0,
            "deepseek-r1:32b": 0,
            "claude-sonnet-4-5": 300,  # $3/1M input + $15/1M output (avg $9/1M)
            "gpt-4o": 1500  # $15/1M
        }
        cost_cents = int((tokens / 1000) * cost_per_1k_tokens.get(model, 0))
        return cost_cents

    def check_budget(self, estimated_cost_cents: int):
        """Check if budget allows this operation"""
        if self.spent_cents + estimated_cost_cents > self.max_budget_cents:
            raise BudgetExceededError(
                f"Budget exceeded: ${self.spent_cents/100:.2f} + ${estimated_cost_cents/100:.2f} > ${self.max_budget_cents/100:.2f}"
            )

    def record_usage(self, tokens_input: int, tokens_output: int, model: str, latency_ms: int):
        """Record actual usage"""
        cost_per_1k_tokens = {...}  # Same as above
        cost_cents = int(((tokens_input + tokens_output) / 1000) * cost_per_1k_tokens.get(model, 0))

        self.spent_cents += cost_cents
        self.usage_log.append({
            "timestamp": datetime.now(),
            "model": model,
            "tokens_input": tokens_input,
            "tokens_output": tokens_output,
            "cost_cents": cost_cents,
            "latency_ms": latency_ms
        })

        return cost_cents

# Usage in agent
budget_guard = BudgetGuard(max_budget_cents=10000)  # $100 budget

async def coder_agent_with_budget(prompt: str):
    # Estimate cost before execution
    estimated_cost = budget_guard.estimate_cost(prompt, model="qwen3-coder:30b")
    budget_guard.check_budget(estimated_cost)

    # Execute
    start_time = time.time()
    result = await coder_agent.ainvoke(prompt)
    latency_ms = int((time.time() - start_time) * 1000)

    # Record actual usage
    budget_guard.record_usage(
        tokens_input=result["usage"]["input_tokens"],
        tokens_output=result["usage"]["output_tokens"],
        model="qwen3-coder:30b",
        latency_ms=latency_ms
    )

    return result
```

### 6.2 Provider Failover (6-Reason Classification)

```python
from enum import Enum

class FailoverReason(Enum):
    AUTH = "auth"  # Invalid API key
    FORMAT = "format"  # Malformed request
    RATE_LIMIT = "rate_limit"  # Quota exceeded
    BILLING = "billing"  # Payment failed
    TIMEOUT = "timeout"  # Latency >30s
    UNKNOWN = "unknown"  # Catch-all

class MultiProviderInvoker:
    """Multi-provider LLM invoker with automatic failover (ADR-056 D3)"""

    def __init__(self):
        self.providers = [
            {"name": "ollama", "llm": ollama_llm, "timeout": 15},
            {"name": "claude", "llm": claude_llm, "timeout": 25},
            {"name": "rule_based", "llm": rule_based_llm, "timeout": 1}
        ]
        self.cooldowns = {}  # {provider: cooldown_until_timestamp}

    def classify_error(self, error: Exception) -> FailoverReason:
        """Classify error into 6 failover reasons"""
        error_str = str(error).lower()
        if "auth" in error_str or "unauthorized" in error_str:
            return FailoverReason.AUTH
        elif "timeout" in error_str:
            return FailoverReason.TIMEOUT
        elif "rate limit" in error_str or "quota" in error_str:
            return FailoverReason.RATE_LIMIT
        elif "billing" in error_str or "payment" in error_str:
            return FailoverReason.BILLING
        elif "format" in error_str or "invalid" in error_str:
            return FailoverReason.FORMAT
        else:
            return FailoverReason.UNKNOWN

    async def invoke(self, prompt: str, **kwargs):
        """Invoke with automatic failover"""
        for provider in self.providers:
            # Check cooldown
            if provider["name"] in self.cooldowns:
                if time.time() < self.cooldowns[provider["name"]]:
                    logger.info(f"Provider {provider['name']} in cooldown, skipping...")
                    continue

            try:
                logger.info(f"Trying provider: {provider['name']}")
                result = await asyncio.wait_for(
                    provider["llm"].ainvoke(prompt, **kwargs),
                    timeout=provider["timeout"]
                )
                logger.info(f"Provider {provider['name']} succeeded")
                return result

            except Exception as e:
                reason = self.classify_error(e)
                logger.warning(f"Provider {provider['name']} failed: {reason.value} - {str(e)}")

                # Apply cooldown based on reason
                if reason == FailoverReason.RATE_LIMIT:
                    self.cooldowns[provider["name"]] = time.time() + 60  # 60s cooldown
                elif reason == FailoverReason.TIMEOUT:
                    continue  # Try next provider immediately
                elif reason == FailoverReason.AUTH:
                    self.cooldowns[provider["name"]] = time.time() + 3600  # 1h cooldown
                elif reason == FailoverReason.BILLING:
                    self.cooldowns[provider["name"]] = time.time() + 86400  # 24h cooldown

                # Continue to next provider
                continue

        # All providers failed
        raise AllProvidersFailed("All providers exhausted")

# Usage
invoker = MultiProviderInvoker()
result = await invoker.invoke("Generate code for user authentication")
```

---

## NEXT STEPS

1. **Implement sample code** — See `03-LANGCHAIN-IMPLEMENTATION.md`
2. **Deploy & test** — See `04-DEPLOYMENT-GUIDE.md`
3. **Monitor & evaluate** — See `05-OBSERVABILITY.md`

---

**Status**: ✅ MAS Architecture Design Complete
**Next**: LangChain Implementation Sample Code
