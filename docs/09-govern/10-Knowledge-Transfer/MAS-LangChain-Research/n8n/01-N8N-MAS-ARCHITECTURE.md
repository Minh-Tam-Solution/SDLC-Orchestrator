# MULTI-AGENT SYSTEM VỚI N8N — SDLC ORCHESTRATOR INTEGRATION

**Date**: 2026-02-23 | **Author**: AI Architect | **Platform**: n8n | **Version**: 1.0.0

---

## 1. TẠI SAO N8N?

### 1.1 N8N vs LangChain

| Aspect | n8n | LangChain |
|--------|-----|-----------|
| **Paradigm** | Visual workflow (no-code/low-code) | Code-first (Python) |
| **Learning Curve** | Low (drag-and-drop) | Medium-High (coding required) |
| **Debugging** | Visual execution trace | Code debugging |
| **Integration** | 400+ built-in nodes | Manual API integration |
| **Deployment** | Docker, self-hosted, cloud | Custom deployment |
| **Cost** | Open-source (MIT) + n8n Cloud ($20-500/mo) | Open-source + hosting costs |
| **Best For** | **Business users, rapid prototyping, visual workflows** | **Developers, complex logic, custom agents** |

**Kết luận**: N8N phù hợp cho:
- ✅ Non-technical users (PM, PO, business analysts)
- ✅ Rapid prototyping (thiết kế workflow trong vài giờ)
- ✅ Visual debugging (xem execution step-by-step)
- ✅ Built-in integrations (SDLC API, OpenAI, Ollama, GitHub)
- ✅ Self-hosted (data privacy, cost control)

---

## 2. N8N CAPABILITIES

### 2.1 Core Features

```
- 400+ integrations: OpenAI, Anthropic, PostgreSQL, Redis, GitHub, Slack, Telegram
- AI nodes: AI Agent, AI Chain, Vector Store (Pinecone, Qdrant, Supabase)
- HTTP Request: Call any REST API (SDLC Orchestrator, Ollama, custom APIs)
- Code node: JavaScript/Python for custom logic
- Webhook: Trigger workflows via HTTP POST
- Schedule: Cron-based workflow execution
- Sub-workflow: Reusable workflow components
- Error handling: Retry, fallback, error webhook
```

### 2.2 AI Agent Node (n8n v1.20+)

```
Features:
- Multi-provider LLM support: OpenAI, Anthropic, Ollama, HuggingFace
- Tool calling: Execute sub-workflows, HTTP requests, code functions
- Memory: Conversation buffer, window memory
- System prompt: Custom instructions per agent
- Temperature, max tokens, streaming support
```

### 2.3 Vector Store Node

```
Providers:
- Pinecone (cloud vector DB)
- Qdrant (self-hosted)
- Supabase (PostgreSQL + pgvector)
- Weaviate (GraphQL)

Operations:
- Insert documents (chunking, embedding)
- Similarity search (top-k retrieval)
- Update/delete vectors
```

---

## 3. KIẾN TRÚC MAS VỚI N8N

### 3.1 High-Level Architecture

```
USER (BRD/PRD)
      ↓ (Webhook)
┌─────────────────────────────────────────────┐
│  WORKFLOW 1: Router (Assistant Agent)       │
│  ┌─────────┐  ┌─────────┐  ┌──────────┐    │
│  │ Webhook │→│ AI Agent │→│ Switch   │    │
│  │ Trigger │  │ (Router) │  │ (Route)  │    │
│  └─────────┘  └─────────┘  └──────────┘    │
└─────────────────┬────────────────────────────┘
                  ↓ (Conditional)
┌─────────────────────────────────────────────┐
│  WORKFLOW 2: Design Thinking (G0→G1)        │
│  ┌─────────┐  ┌─────────┐  ┌──────────┐    │
│  │Researcher│→│ PM Agent │→│ Gate G1  │    │
│  │  Agent   │  │ (BRD/PRD)│  │ (SDLC)   │    │
│  └─────────┘  └─────────┘  └──────────┘    │
│       ↓ (Human Approval via Telegram)       │
└─────────────────┬────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│  WORKFLOW 3: Architecture (G1→G2)           │
│  ┌─────────┐  ┌─────────┐  ┌──────────┐    │
│  │Architect │→│ Reviewer │→│ Gate G2  │    │
│  │  Agent   │  │  Agent   │  │ (SDLC)   │    │
│  └─────────┘  └─────────┘  └──────────┘    │
│       ↓ (Human Approval via Telegram)       │
└─────────────────┬────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│  WORKFLOW 4: Coding (G2→G3) — Reflection    │
│  ┌─────────┐  ┌─────────┐  ┌──────────┐    │
│  │  Coder  │↔│ Reviewer │→│ Gate G3  │    │
│  │  Agent  │  │  Agent   │  │ (SDLC)   │    │
│  └─────────┘  └─────────┘  └──────────┘    │
│  Loop: max 3 retries                        │
│       ↓ (Human Approval via Telegram)       │
└─────────────────┬────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│  WORKFLOW 5: Deployment (G3→G4)             │
│  ┌─────────┐  ┌─────────┐  ┌──────────┐    │
│  │ DevOps  │→│  Tester  │→│ Gate G4  │    │
│  │  Agent  │  │  Agent   │  │ (SDLC)   │    │
│  └─────────┘  └─────────┘  └──────────┘    │
│       ↓ (Human Approval via Telegram)       │
└─────────────────────────────────────────────┘
```

### 3.2 Workflow Components (N8N Nodes)

#### Agent Node Structure

```
AI Agent Node:
  - Model: Ollama (qwen3:32b, qwen3-coder:30b, deepseek-r1:32b)
  - System Prompt: Role-specific instructions
  - Tools: Sub-workflows (create_gate, upload_evidence, generate_code, sast_scan)
  - Memory: Conversation buffer (last 50 messages)
  - Output: Text response + tool invocations

HTTP Request Node (SDLC API):
  - Method: POST/GET/PUT/DELETE
  - URL: http://sdlc-backend:8300/api/v1/{endpoint}
  - Authentication: Bearer Token (JWT)
  - Body: JSON payload
  - Output: API response

Code Node (JavaScript):
  - Purpose: Data transformation, validation, logic
  - Input: $json (previous node output)
  - Code: JavaScript ES6+
  - Output: Transformed data

Switch Node:
  - Purpose: Conditional routing
  - Conditions: if-else logic
  - Outputs: Multiple routes

Merge Node:
  - Purpose: Combine outputs from multiple branches
  - Mode: Wait for all, Keep only first, etc.
```

---

## 4. WORKFLOW DESIGNS

### 4.1 Workflow 1: Router (Assistant Agent)

**Purpose**: Parse user input, ask clarifying questions, route to appropriate workflow

**Trigger**: Webhook (POST /webhook/router)

**Nodes**:
1. **Webhook** — Receive user input (BRD/PRD or natural language)
2. **AI Agent (Router)** — Parse intent, generate clarifying questions
3. **Code Node** — Extract workflow route (design_thinking, requirements, coding, deployment)
4. **Switch Node** — Route to appropriate workflow
5. **HTTP Request (Trigger Sub-workflow)** — Call next workflow via webhook

**n8n JSON** (simplified):
```json
{
  "name": "Router Workflow",
  "nodes": [
    {
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "path": "router",
        "httpMethod": "POST"
      },
      "position": [250, 300]
    },
    {
      "name": "AI Agent (Router)",
      "type": "@n8n/n8n-nodes-langchain.agent",
      "parameters": {
        "model": "ollama",
        "modelName": "qwen3:32b",
        "systemPrompt": "You are a Router Agent. Parse user input and determine workflow: design_thinking, requirements, coding, or deployment.",
        "tools": []
      },
      "position": [450, 300]
    },
    {
      "name": "Extract Route",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "language": "javaScript",
        "jsCode": "const response = $json.output;\nconst route = response.match(/workflow: (\\w+)/)?.[1] || 'design_thinking';\nreturn { route };"
      },
      "position": [650, 300]
    },
    {
      "name": "Switch Route",
      "type": "n8n-nodes-base.switch",
      "parameters": {
        "rules": [
          {"value": "design_thinking"},
          {"value": "requirements"},
          {"value": "coding"},
          {"value": "deployment"}
        ]
      },
      "position": [850, 300]
    },
    {
      "name": "Trigger Design Thinking",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "http://n8n:5678/webhook/design-thinking",
        "body": {"input": "={{$json.input}}"}
      },
      "position": [1050, 200]
    }
  ],
  "connections": {
    "Webhook": {"main": [[{"node": "AI Agent (Router)"}]]},
    "AI Agent (Router)": {"main": [[{"node": "Extract Route"}]]},
    "Extract Route": {"main": [[{"node": "Switch Route"}]]},
    "Switch Route": {
      "main": [
        [{"node": "Trigger Design Thinking"}],
        [{"node": "Trigger Requirements"}],
        [{"node": "Trigger Coding"}],
        [{"node": "Trigger Deployment"}]
      ]
    }
  }
}
```

---

### 4.2 Workflow 2: Design Thinking (G0→G1)

**Purpose**: Research domain, write BRD/PRD, create Gate G1

**Trigger**: Webhook (POST /webhook/design-thinking)

**Nodes**:
1. **Webhook** — Receive input from Router
2. **AI Agent (Researcher)** — Web search, domain research
3. **Vector Store (Insert)** — Store research findings in ChromaDB
4. **AI Agent (PM)** — Write BRD/PRD based on research
5. **HTTP Request (Create Gate G1)** — POST /api/v1/gates
6. **HTTP Request (Upload Evidence)** — POST /api/v1/evidence/upload (attach BRD/PRD)
7. **Telegram (Send Approval Request)** — Notify CPO for approval
8. **Wait for Approval** — Webhook or polling for approval status
9. **Conditional** — If approved, trigger Architecture workflow

**Key Node: AI Agent (PM)**
```json
{
  "name": "AI Agent (PM)",
  "type": "@n8n/n8n-nodes-langchain.agent",
  "parameters": {
    "model": "ollama",
    "modelName": "qwen3:32b",
    "systemPrompt": "You are a PM Agent. Write a detailed PRD (Product Requirements Document) based on the BRD and research findings. Include: 1) Business objectives, 2) Target users, 3) Features (MoSCoW prioritization), 4) Acceptance criteria, 5) Constraints.",
    "tools": [],
    "memory": {
      "type": "bufferMemory",
      "maxMessages": 50
    },
    "temperature": 0.7
  }
}
```

**Key Node: HTTP Request (Create Gate G1)**
```json
{
  "name": "Create Gate G1",
  "type": "n8n-nodes-base.httpRequest",
  "parameters": {
    "method": "POST",
    "url": "http://sdlc-backend:8300/api/v1/gates",
    "authentication": "genericCredentialType",
    "genericAuthType": "httpHeaderAuth",
    "sendHeaders": true,
    "headerParameters": {
      "parameters": [
        {
          "name": "Authorization",
          "value": "Bearer {{$credentials.sdlcApiKey}}"
        }
      ]
    },
    "sendBody": true,
    "bodyParameters": {
      "parameters": [
        {
          "name": "project_id",
          "value": "={{$json.project_id}}"
        },
        {
          "name": "gate_type",
          "value": "G1_CONSULTATION"
        },
        {
          "name": "title",
          "value": "Design Ready - CPO Approval"
        },
        {
          "name": "description",
          "value": "PRD ready for CPO review"
        }
      ]
    },
    "options": {}
  }
}
```

---

### 4.3 Workflow 3: Architecture (G1→G2)

**Purpose**: Design system architecture (ERD, API spec), create Gate G2

**Nodes**:
1. **Webhook** — Receive PRD from previous workflow
2. **AI Agent (Architect)** — Generate ERD, API spec, architecture diagram
3. **Code Node (Validate Architecture)** — Check ERD syntax, API spec OpenAPI 3.0 compliance
4. **HTTP Request (Create Gate G2)** — POST /api/v1/gates
5. **HTTP Request (Upload Evidence)** — Attach architecture docs
6. **AI Agent (Reviewer)** — Review architecture for security, scalability
7. **Conditional** — If review passes, request CTO approval
8. **Telegram (CTO Approval)** — Notify CTO via Telegram
9. **Wait for Approval** — Polling or webhook
10. **Trigger Coding Workflow** — If approved

**Key Node: AI Agent (Architect)**
```json
{
  "name": "AI Agent (Architect)",
  "type": "@n8n/n8n-nodes-langchain.agent",
  "parameters": {
    "model": "ollama",
    "modelName": "qwen3-coder:30b",
    "systemPrompt": "You are an Architect Agent. Design system architecture including: 1) Database schema (ERD in Mermaid format), 2) API specification (OpenAPI 3.0 JSON), 3) Architecture diagram (C4 model), 4) Technology stack selection.",
    "tools": [
      {
        "name": "validate_erd",
        "description": "Validate ERD Mermaid syntax",
        "subWorkflow": "validate-erd"
      },
      {
        "name": "validate_openapi",
        "description": "Validate OpenAPI 3.0 spec",
        "subWorkflow": "validate-openapi"
      }
    ],
    "memory": {
      "type": "bufferMemory",
      "maxMessages": 50
    },
    "temperature": 0.3
  }
}
```

---

### 4.4 Workflow 4: Coding (G2→G3) — Reflection Loop

**Purpose**: Generate production code, review, iterate, create Gate G3

**Nodes**:
1. **Webhook** — Receive architecture from previous workflow
2. **Set Variable (retry_count = 0)** — Initialize retry counter
3. **AI Agent (Coder)** — Generate code via EP-06 Codegen
4. **HTTP Request (EP-06 Codegen)** — POST /api/v1/codegen/generate
5. **HTTP Request (Upload Evidence)** — Upload generated code
6. **AI Agent (Reviewer)** — Code review + SAST scan
7. **HTTP Request (SAST Scan)** — POST /api/v1/sast/scan
8. **Code Node (Check Review)** — Parse review result (PASS/FAIL)
9. **Conditional** — If FAIL and retry_count < 3, loop back to Coder with feedback
10. **Increment retry_count** — retry_count += 1
11. **If PASS** — Create Gate G3
12. **Telegram (CTO Approval)** — Notify CTO
13. **Trigger Deployment Workflow** — If approved

**Key Pattern: Reflection Loop**
```
Coder → Reviewer
  ↑         ↓ (FAIL)
  └─────────┘ (retry_count < 3)
         ↓ (PASS or retry_count >= 3)
      Gate G3
```

**Key Node: AI Agent (Coder)**
```json
{
  "name": "AI Agent (Coder)",
  "type": "@n8n/n8n-nodes-langchain.agent",
  "parameters": {
    "model": "ollama",
    "modelName": "qwen3-coder:30b",
    "systemPrompt": "You are a Coder Agent. Generate production-ready code based on PRD and architecture. Guidelines: 1) Zero Mock Policy (no TODOs), 2) OWASP ASVS Level 2 compliance, 3) PEP 8 (Python) / ESLint (JavaScript), 4) >90% test coverage. {{$json.feedback ? 'Previous feedback: ' + $json.feedback : ''}}",
    "tools": [
      {
        "name": "generate_code_ep06",
        "description": "Generate code via EP-06 Codegen Pipeline (4-Gate Quality)",
        "httpRequest": {
          "method": "POST",
          "url": "http://sdlc-backend:8300/api/v1/codegen/generate",
          "body": {
            "spec": "={{$json.spec}}",
            "language": "python",
            "quality_mode": "production"
          }
        }
      }
    ],
    "memory": {
      "type": "bufferMemory",
      "maxMessages": 50
    },
    "temperature": 0.2
  }
}
```

**Key Node: Conditional (Reflection Loop)**
```json
{
  "name": "Check Review Result",
  "type": "n8n-nodes-base.switch",
  "parameters": {
    "rules": [
      {
        "value": "={{$json.review_status === 'PASS'}}",
        "output": 0
      },
      {
        "value": "={{$json.review_status === 'FAIL' && $json.retry_count < 3}}",
        "output": 1
      },
      {
        "value": "={{$json.review_status === 'FAIL' && $json.retry_count >= 3}}",
        "output": 2
      }
    ]
  }
}
```

---

### 4.5 Workflow 5: Deployment (G3→G4)

**Purpose**: Deploy to production, run smoke tests, create Gate G4

**Nodes**:
1. **Webhook** — Receive code artifacts from previous workflow
2. **AI Agent (DevOps)** — Generate deployment scripts (Dockerfile, k8s manifests)
3. **Code Node (Build Docker Image)** — Execute `docker build`
4. **HTTP Request (Deploy to K8s)** — POST to Kubernetes API
5. **Wait (30s)** — Wait for deployment to stabilize
6. **AI Agent (Tester)** — Run smoke tests
7. **HTTP Request (Health Check)** — GET /health endpoint
8. **Code Node (Check Deployment Status)** — Parse health check result
9. **HTTP Request (Create Gate G4)** — POST /api/v1/gates
10. **Telegram (CEO Approval)** — Notify CEO
11. **Final Status** — Success or failure

**Key Node: Code Node (Build Docker Image)**
```json
{
  "name": "Build Docker Image",
  "type": "n8n-nodes-base.code",
  "parameters": {
    "language": "javaScript",
    "jsCode": "const { exec } = require('child_process');\nconst util = require('util');\nconst execPromise = util.promisify(exec);\n\nconst dockerfile = $json.dockerfile;\nconst imageName = $json.image_name;\n\n// Write Dockerfile\nawait fs.promises.writeFile('/tmp/Dockerfile', dockerfile);\n\n// Build image\nconst { stdout, stderr } = await execPromise(`docker build -t ${imageName} /tmp`);\n\nreturn { stdout, stderr, image_name: imageName };"
  }
}
```

---

## 5. TOOL INTEGRATION

### 5.1 SDLC Orchestrator API Tools (HTTP Request Nodes)

**Credential Setup** (n8n Credentials):
```json
{
  "name": "SDLC API Token",
  "type": "httpHeaderAuth",
  "data": {
    "name": "Authorization",
    "value": "Bearer your-jwt-token-here"
  }
}
```

**Reusable Sub-workflows**:

1. **create_gate.json** (Sub-workflow)
```json
{
  "name": "Create Gate",
  "nodes": [
    {
      "name": "HTTP Request",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "http://sdlc-backend:8300/api/v1/gates",
        "authentication": "predefinedCredentialType",
        "nodeCredentialType": "sdlcApiToken",
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {"name": "project_id", "value": "={{$json.project_id}}"},
            {"name": "gate_type", "value": "={{$json.gate_type}}"},
            {"name": "title", "value": "={{$json.title}}"},
            {"name": "description", "value": "={{$json.description}}"}
          ]
        }
      }
    }
  ]
}
```

2. **upload_evidence.json** (Sub-workflow)
```json
{
  "name": "Upload Evidence",
  "nodes": [
    {
      "name": "HTTP Request",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "http://sdlc-backend:8300/api/v1/evidence/upload",
        "authentication": "predefinedCredentialType",
        "nodeCredentialType": "sdlcApiToken",
        "sendBody": true,
        "bodyContentType": "multipart-form-data",
        "bodyParameters": {
          "parameters": [
            {"name": "file", "value": "={{$binary.data}}"},
            {"name": "gate_id", "value": "={{$json.gate_id}}"},
            {"name": "type", "value": "={{$json.evidence_type}}"}
          ]
        }
      }
    }
  ]
}
```

3. **generate_code_ep06.json** (Sub-workflow)
```json
{
  "name": "Generate Code (EP-06)",
  "nodes": [
    {
      "name": "HTTP Request",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "http://sdlc-backend:8300/api/v1/codegen/generate",
        "authentication": "predefinedCredentialType",
        "nodeCredentialType": "sdlcApiToken",
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {"name": "spec", "value": "={{$json.spec}}"},
            {"name": "language", "value": "={{$json.language || 'python'}}"},
            {"name": "quality_mode", "value": "production"},
            {"name": "max_retries", "value": 3}
          ]
        }
      }
    }
  ]
}
```

4. **sast_scan.json** (Sub-workflow)
```json
{
  "name": "SAST Scan",
  "nodes": [
    {
      "name": "HTTP Request",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "http://sdlc-backend:8300/api/v1/sast/scan",
        "authentication": "predefinedCredentialType",
        "nodeCredentialType": "sdlcApiToken",
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {"name": "file_paths", "value": "={{$json.file_paths}}"},
            {"name": "rules", "value": ["ai-security", "owasp-python"]}
          ]
        }
      }
    }
  ]
}
```

---

## 6. MEMORY STRATEGY

### 6.1 Short-Term Memory (Conversation Buffer)

**Implementation**: AI Agent node built-in memory

```json
{
  "memory": {
    "type": "bufferMemory",
    "maxMessages": 50,
    "sessionKey": "={{$json.conversation_id}}"
  }
}
```

### 6.2 Long-Term Memory (Vector Store RAG)

**Setup**: Pinecone/Qdrant/Supabase Vector Store

**Workflow: Store Project Artifact**
```json
{
  "name": "Store in Vector DB",
  "nodes": [
    {
      "name": "Vector Store Insert",
      "type": "@n8n/n8n-nodes-langchain.vectorStorePinecone",
      "parameters": {
        "operation": "insert",
        "index": "sdlc-knowledge",
        "namespace": "={{$json.project_id}}",
        "documents": "={{$json.documents}}",
        "embedding": {
          "model": "ollama",
          "modelName": "bge-m3:latest"
        }
      }
    }
  ]
}
```

**Workflow: Retrieve Similar Projects**
```json
{
  "name": "RAG Retrieval",
  "nodes": [
    {
      "name": "Vector Store Search",
      "type": "@n8n/n8n-nodes-langchain.vectorStorePinecone",
      "parameters": {
        "operation": "search",
        "index": "sdlc-knowledge",
        "query": "={{$json.query}}",
        "topK": 3,
        "filter": {
          "artifact_type": "prd"
        }
      }
    }
  ]
}
```

### 6.3 History Compaction (ZeroClaw Pattern)

**Workflow: Compact History at 80% Capacity**
```json
{
  "name": "Compact History",
  "nodes": [
    {
      "name": "Check Message Count",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "jsCode": "const messages = $json.chat_history;\nconst threshold = 50 * 0.8;  // 80% of 50\nif (messages.length >= threshold) {\n  return { shouldCompact: true, messages };\n}\nreturn { shouldCompact: false };"
      }
    },
    {
      "name": "AI Agent (Summarize)",
      "type": "@n8n/n8n-nodes-langchain.agent",
      "parameters": {
        "model": "ollama",
        "modelName": "qwen3:8b",
        "systemPrompt": "Summarize the following conversation in 3-5 sentences.",
        "input": "={{$json.messages.slice(0, 20).join('\\n')}}"
      }
    },
    {
      "name": "Replace with Summary",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "jsCode": "const summary = $json.output;\nconst remaining = $input.all()[0].json.messages.slice(20);\nreturn { chat_history: [{ role: 'system', content: `[Summary: ${summary}]` }, ...remaining] };"
      }
    }
  ]
}
```

---

## 7. ERROR HANDLING & FAULT TOLERANCE

### 7.1 Multi-Provider Failover

**Workflow Pattern**:
```
Try Ollama
  ↓ (Error)
Try Claude
  ↓ (Error)
Try Rule-based
  ↓ (Error)
Send Alert
```

**Implementation**:
```json
{
  "name": "Multi-Provider Chain",
  "nodes": [
    {
      "name": "Try Ollama",
      "type": "@n8n/n8n-nodes-langchain.agent",
      "parameters": {
        "model": "ollama",
        "modelName": "qwen3:32b"
      },
      "onError": "continueErrorOutput"
    },
    {
      "name": "Check Ollama Error",
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "boolean": [
            {
              "value1": "={{$json.error}}",
              "value2": true
            }
          ]
        }
      }
    },
    {
      "name": "Try Claude",
      "type": "@n8n/n8n-nodes-langchain.agent",
      "parameters": {
        "model": "openAI",
        "modelName": "claude-sonnet-4-5"
      },
      "onError": "continueErrorOutput"
    },
    {
      "name": "Try Rule-based",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "jsCode": "// Deterministic rule-based fallback\nconst input = $json.input;\n// ... template matching logic\nreturn { output: templateResponse };"
      }
    }
  ]
}
```

### 7.2 Budget Guard (Circuit Breaker)

**Workflow: Check Budget Before LLM Call**
```json
{
  "name": "Budget Guard",
  "nodes": [
    {
      "name": "Get Current Budget",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "GET",
        "url": "http://sdlc-backend:8300/api/v1/agent-team/conversations/{{$json.conversation_id}}/cost"
      }
    },
    {
      "name": "Check Budget",
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "number": [
            {
              "value1": "={{$json.spent_cents}}",
              "operation": "smaller",
              "value2": "={{$json.max_budget_cents}}"
            }
          ]
        }
      }
    },
    {
      "name": "Budget Exceeded Alert",
      "type": "n8n-nodes-base.telegram",
      "parameters": {
        "chatId": "admin_chat_id",
        "text": "Budget exceeded for conversation {{$json.conversation_id}}: ${{$json.spent_cents/100}} / ${{$json.max_budget_cents/100}}"
      }
    }
  ]
}
```

---

## 8. OBSERVABILITY & LOGGING

### 8.1 Structured Logging

**Workflow: Log Agent Action**
```json
{
  "name": "Log to PostgreSQL",
  "nodes": [
    {
      "name": "Insert Log",
      "type": "n8n-nodes-base.postgres",
      "parameters": {
        "operation": "insert",
        "table": "agent_logs",
        "columns": "agent_name, action, correlation_id, tokens_used, cost_cents, latency_ms, provider, model, status",
        "values": "={{$json.agent_name}}, ={{$json.action}}, ={{$json.correlation_id}}, ={{$json.tokens_used}}, ={{$json.cost_cents}}, ={{$json.latency_ms}}, ={{$json.provider}}, ={{$json.model}}, ={{$json.status}}"
      }
    }
  ]
}
```

### 8.2 Prometheus Metrics

**Workflow: Export Metrics**
```json
{
  "name": "Push to Prometheus",
  "nodes": [
    {
      "name": "HTTP Request",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "http://prometheus-pushgateway:9091/metrics/job/n8n-mas",
        "body": "agent_execution_duration_seconds{agent=\"{{$json.agent_name}}\"} {{$json.latency_ms/1000}}\nagent_cost_cents_total{agent=\"{{$json.agent_name}}\"} {{$json.cost_cents}}\n"
      }
    }
  ]
}
```

---

## 9. DEPLOYMENT

### 9.1 N8N Self-Hosted (Docker Compose)

**docker-compose.yml**:
```yaml
version: "3.9"

services:
  n8n:
    image: n8nio/n8n:latest
    container_name: n8n-mas
    restart: unless-stopped
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=changeme
      - N8N_HOST=0.0.0.0
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
      - NODE_ENV=production
      - WEBHOOK_URL=http://n8n:5678/
      - GENERIC_TIMEZONE=Asia/Ho_Chi_Minh
      - EXECUTIONS_MODE=queue  # Use queue mode for scalability
      - QUEUE_BULL_REDIS_HOST=redis
      - QUEUE_BULL_REDIS_PORT=6379
    volumes:
      - n8n_data:/home/node/.n8n
      - ./workflows:/home/node/.n8n/workflows:ro
    depends_on:
      - postgres
      - redis
    networks:
      - mas-network

  postgres:
    image: postgres:15
    container_name: n8n-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_USER=n8n
      - POSTGRES_PASSWORD=n8n_password
      - POSTGRES_DB=n8n
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - mas-network

  redis:
    image: redis:7-alpine
    container_name: n8n-redis
    restart: unless-stopped
    networks:
      - mas-network

volumes:
  n8n_data:
  postgres_data:

networks:
  mas-network:
    external: true
    name: sdlc-network
```

### 9.2 Start N8N

```bash
# Start services
docker compose up -d

# Access n8n UI
open http://localhost:5678

# Import workflows
# Go to Workflows → Import from File → Select .json files
```

---

## 10. COST COMPARISON

### N8N vs LangChain

| Aspect | N8N | LangChain |
|--------|-----|-----------|
| **Infrastructure** | Docker ($5/mo VPS) or n8n Cloud ($20-500/mo) | Custom server ($5-20/mo) |
| **LLM Costs** | Same (Ollama $50/mo, Claude $1K/mo) | Same |
| **Development Time** | **2-5 hours** (visual workflows) | 10-20 hours (coding) |
| **Maintenance** | Low (visual debugging) | Medium (code maintenance) |
| **Total 1st Month** | **$55-555** | $55-1020 |

**Recommendation**: N8N cho rapid prototyping, LangChain cho production với custom logic phức tạp.

---

## SUMMARY

**N8N MAS Architecture**:
- ✅ 5 main workflows: Router, Design Thinking, Architecture, Coding (reflection loop), Deployment
- ✅ 12 agents: Researcher, PM, PJM, Architect, Coder, Reviewer, Tester, DevOps + 3 human approvers + Router
- ✅ SDLC API integration: Gates, Evidence, Codegen, SAST
- ✅ Multi-provider failover: Ollama → Claude → Rule-based
- ✅ Memory strategy: Conversation buffer + Vector store RAG
- ✅ Observability: PostgreSQL logs + Prometheus metrics
- ✅ Cost: $55-555/mo (vs $5K+ with all Claude)

**Next**: See `02-N8N-WORKFLOW-EXAMPLES.md` for complete workflow JSON files

---

**Status**: ✅ N8N MAS Architecture Complete
**Documentation**: 1/3 (Architecture)
**Next**: Workflow JSON Examples
