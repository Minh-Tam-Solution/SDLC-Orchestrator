# Code Generation Page Technical Specification
## EP-06: IR-Based Vietnamese SME Codegen Engine | Sprint 50+

**Status**: DRAFT → APPROVED
**Version**: 1.0.0
**Date**: December 24, 2025
**Author**: Frontend Lead + Backend Lead
**Sprint**: Sprint 50 - Productization Baseline
**Framework**: SDLC 5.1.1
**Depends On**: [Codegen-Service-Specification.md](./Codegen-Service-Specification.md)

---

## 1. Overview

### 1.1 Purpose

This specification defines the Code Generation Page - the UI component that allows Vietnamese SME founders to generate production-ready code from their AppBlueprint (IR).

### 1.2 Problem Statement

Current flow stops after AppBlueprint generation:
```
Onboarding Wizard → AppBlueprint (IR) → ??? (GAP)
```

Users see "Tiếp tục tạo code" button but no page handles the actual code generation.

### 1.3 Solution

Implement **CodeGenerationPage** component that:
1. Receives AppBlueprint from onboarding wizard
2. Allows configuration (language, framework)
3. Triggers code generation via API
4. Displays generated files with syntax highlighting
5. Enables download as ZIP

---

## 2. User Flow

### 2.1 Complete E2E Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│  EP-06 COMPLETE USER FLOW                                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  PHASE 1: ONBOARDING WIZARD (Existing - VietnameseOnboardingWizard) │
│  │                                                                    │   │
│  │  Step 1: Domain Selection (restaurant/hotel/retail)               │   │
│  │  Step 2: App Name (Vietnamese input supported)                    │   │
│  │  Step 3: Feature Selection (multi-select modules)                 │   │
│  │  Step 4: Scale Selection (micro/small/medium)                     │   │
│  │  Step 5: Confirm & Generate Blueprint                             │   │
│  │                        │                                          │   │
│  └────────────────────────┼──────────────────────────────────────────┘   │
│                           │ AppBlueprint (IR)                            │
│                           ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  PHASE 2: CODE GENERATION PAGE (New - CodeGenerationPage)        │   │
│  │                                                                    │   │
│  │  ┌─────────────────────────────────────────────────────────────┐ │   │
│  │  │  Blueprint Summary                                           │ │   │
│  │  │  • App: Quán Phở 24                                         │ │   │
│  │  │  • Domain: F&B (restaurant)                                 │ │   │
│  │  │  • Modules: 4 (menu, orders, tables, payments)              │ │   │
│  │  │  • Scale: Small (6-20 employees) → STANDARD tier            │ │   │
│  │  └─────────────────────────────────────────────────────────────┘ │   │
│  │                                                                    │   │
│  │  ┌─────────────────────────────────────────────────────────────┐ │   │
│  │  │  Generation Options                                          │ │   │
│  │  │  • Language: [Python ▼] [TypeScript]                        │ │   │
│  │  │  • Backend:  [FastAPI ▼] [Express] [NestJS]                 │ │   │
│  │  │  • Frontend: [React ▼] [Vue] [None]                         │ │   │
│  │  │  • Database: [PostgreSQL ▼] [MySQL] [SQLite]                │ │   │
│  │  └─────────────────────────────────────────────────────────────┘ │   │
│  │                                                                    │   │
│  │  [ 🚀 Generate Code ]                                             │   │
│  │                        │                                          │   │
│  └────────────────────────┼──────────────────────────────────────────┘   │
│                           │ POST /api/v1/codegen/generate                │
│                           ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  PHASE 3: QUALITY GATES (Backend - Automatic)                    │   │
│  │                                                                    │   │
│  │  Gate 1: Syntax Validation (ast.parse, ruff, tsc) ───── ✅ PASS  │   │
│  │  Gate 2: Security Scan (Semgrep OWASP rules) ────────── ✅ PASS  │   │
│  │  Gate 3: Context Validation (imports, deps) ─────────── ✅ PASS  │   │
│  │  Gate 4: Test Execution (pytest in Docker) ──────────── ✅ PASS  │   │
│  │                        │                                          │   │
│  └────────────────────────┼──────────────────────────────────────────┘   │
│                           │ GenerateResponse                             │
│                           ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  PHASE 4: RESULTS & DOWNLOAD (CodeGenerationPage - Results View) │   │
│  │                                                                    │   │
│  │  ┌─────────────────────────────────────────────────────────────┐ │   │
│  │  │  Generated Files (12 files, 2.4 KB)                         │ │   │
│  │  │                                                              │ │   │
│  │  │  📁 backend/                                                 │ │   │
│  │  │  ├── 📄 main.py                    [View] [Copy]            │ │   │
│  │  │  ├── 📁 models/                                             │ │   │
│  │  │  │   ├── 📄 menu.py                [View] [Copy]            │ │   │
│  │  │  │   ├── 📄 order.py               [View] [Copy]            │ │   │
│  │  │  │   └── 📄 table.py               [View] [Copy]            │ │   │
│  │  │  ├── 📁 routes/                                             │ │   │
│  │  │  │   ├── 📄 menu_routes.py         [View] [Copy]            │ │   │
│  │  │  │   └── 📄 order_routes.py        [View] [Copy]            │ │   │
│  │  │  └── 📄 requirements.txt           [View] [Copy]            │ │   │
│  │  └─────────────────────────────────────────────────────────────┘ │   │
│  │                                                                    │   │
│  │  [ 📥 Download ZIP ]  [ 🔗 Push to GitHub ]  [ ➕ Create Project ] │   │
│  │                                                                    │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 State Machine

```
┌─────────────┐     blueprint     ┌─────────────┐
│   INITIAL   │ ────────────────▶ │  CONFIGURE  │
└─────────────┘                   └──────┬──────┘
                                         │ generate()
                                         ▼
                                  ┌─────────────┐
                                  │ GENERATING  │
                                  │  (loading)  │
                                  └──────┬──────┘
                                         │
                           ┌─────────────┼─────────────┐
                           │             │             │
                           ▼             ▼             ▼
                    ┌──────────┐  ┌──────────┐  ┌──────────┐
                    │ SUCCESS  │  │  ERROR   │  │ TIMEOUT  │
                    │ (files)  │  │ (retry)  │  │ (retry)  │
                    └──────────┘  └──────────┘  └──────────┘
```

---

## 3. Component Design

### 3.1 Component Hierarchy

```
CodeGenerationPage/
├── index.tsx                    # Main page component
├── BlueprintSummary.tsx         # Display blueprint info
├── GenerationOptions.tsx        # Language/framework selection
├── GenerationProgress.tsx       # Loading state with progress
├── GeneratedFilesView.tsx       # File tree + preview
├── FilePreview.tsx              # Syntax-highlighted code view
└── DownloadActions.tsx          # Download/export buttons
```

### 3.2 Props & State

```typescript
// Page props (from router)
interface CodeGenerationPageProps {
  blueprint: AppBlueprint;        // From onboarding wizard
  sessionId?: string;             // Onboarding session ID
}

// Component state
interface CodeGenerationState {
  status: 'configure' | 'generating' | 'success' | 'error';
  options: GenerationOptions;
  result: GenerateResponse | null;
  error: string | null;
  selectedFile: string | null;    // Currently previewed file
}

// Generation options
interface GenerationOptions {
  language: 'python' | 'typescript';
  backend_framework: 'fastapi' | 'express' | 'nestjs';
  frontend_framework: 'react' | 'vue' | 'none';
  database: 'postgresql' | 'mysql' | 'sqlite';
  include_tests: boolean;
  include_docker: boolean;
}
```

### 3.3 API Integration

```typescript
// POST /api/v1/codegen/generate
interface GenerateRequest {
  app_blueprint: AppBlueprint;
  language: string;
  framework: string;
  target_module?: string;
  preferred_provider?: string;
}

// Response
interface GenerateResponse {
  success: boolean;
  provider: string;
  files: GeneratedFile[];
  tokens_used: number;
  generation_time_ms: number;
  metadata: {
    quality_gates_passed: boolean;
    gates_results: GateResult[];
  };
}

interface GeneratedFile {
  path: string;           // e.g., "backend/models/menu.py"
  content: string;        // File content
  language: string;       // For syntax highlighting
  size_bytes: number;
}
```

---

## 4. UI/UX Design

### 4.1 Wireframe - Configure State

```
┌─────────────────────────────────────────────────────────────────────┐
│  🚀 Tạo Code từ Blueprint                                    [X]    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ 📋 Tóm tắt Blueprint                                            ││
│  │                                                                  ││
│  │ Tên ứng dụng:    Quán Phở 24                                    ││
│  │ Ngành:           🍜 F&B / Nhà hàng                               ││
│  │ Modules:         4 (menu, orders, tables, payments)              ││
│  │ Quy mô:          Nhỏ (6-20 NV) • STANDARD tier                  ││
│  │ Entities:        8 database tables                               ││
│  │ Endpoints:       24 API routes                                   ││
│  │                                                                  ││
│  │ [ 👁 Xem Blueprint JSON ]  [ 📋 Copy ]                           ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ ⚙️ Cấu hình Code Generation                                      ││
│  │                                                                  ││
│  │ Ngôn ngữ Backend:                                               ││
│  │ ┌─────────────────┐  ┌─────────────────┐                        ││
│  │ │ ● Python        │  │ ○ TypeScript    │                        ││
│  │ │   FastAPI       │  │   NestJS        │                        ││
│  │ └─────────────────┘  └─────────────────┘                        ││
│  │                                                                  ││
│  │ Database:         [PostgreSQL ▼]                                ││
│  │                                                                  ││
│  │ ☑ Bao gồm unit tests                                            ││
│  │ ☑ Bao gồm Dockerfile                                            ││
│  │ ☐ Bao gồm CI/CD (GitHub Actions)                                ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ 💰 Ước tính                                                      ││
│  │                                                                  ││
│  │ Provider:         Ollama (qwen3-coder:30b)                       ││
│  │ Tokens:           ~8,000 tokens                                 ││
│  │ Thời gian:        ~15-20 giây                                   ││
│  │ Chi phí:          $0.00 (local)                                 ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
│         ┌────────────────────────────────────────────────┐          │
│         │     🚀  Bắt đầu tạo code                       │          │
│         └────────────────────────────────────────────────┘          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Wireframe - Blueprint JSON Viewer (Modal/Expandable)

When user clicks "Xem Blueprint JSON", show expandable code block with copy button:

```
┌─────────────────────────────────────────────────────────────────────┐
│  📋 AppBlueprint (IR)                                    [ 📋 Copy ]│
├─────────────────────────────────────────────────────────────────────┤
│ ```json                                                              │
│ {                                                                    │
│   "name": "QuanPho24",                                              │
│   "name_display": "Quán Phở 24",                                    │
│   "domain": "fnb",                                                  │
│   "domain_template": "restaurant",                                  │
│   "features": [                                                     │
│     "menu_management",                                              │
│     "order_management",                                             │
│     "table_reservation",                                            │
│     "payment_integration"                                           │
│   ],                                                                │
│   "scale": "small",                                                 │
│   "cgf_tier": "STANDARD",                                           │
│   "modules": [                                                      │
│     {                                                               │
│       "name": "menu",                                               │
│       "entities": ["MenuItem", "Category", "MenuVariant"],          │
│       "endpoints": [                                                │
│         "GET /menu",                                                │
│         "POST /menu",                                               │
│         "GET /menu/{id}",                                           │
│         "PUT /menu/{id}",                                           │
│         "DELETE /menu/{id}"                                         │
│       ]                                                             │
│     },                                                              │
│     ...                                                             │
│   ]                                                                 │
│ }                                                                   │
│ ```                                                                 │
│                                                                      │
│  ┌─────────────────┐                                                │
│  │  ✓ Đã copy!     │  ← Toast notification after copy               │
│  └─────────────────┘                                                │
└─────────────────────────────────────────────────────────────────────┘
```

**Copy Button Behavior:**
- Icon: 📋 (clipboard) → ✓ (check) after copy
- Text: "Copy" → "Đã copy!" for 2 seconds
- Uses `navigator.clipboard.writeText()`
- Toast notification on success

**Code Block Styling (ChatGPT/IDE style):**
```css
.blueprint-code-block {
  position: relative;
  background: #1e1e1e;           /* Dark theme */
  border-radius: 8px;
  padding: 16px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  line-height: 1.5;
  overflow-x: auto;
  max-height: 400px;
  overflow-y: auto;
}

.copy-button {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(255,255,255,0.1);
  border: none;
  border-radius: 4px;
  padding: 4px 8px;
  color: #fff;
  cursor: pointer;
  transition: background 0.2s;
}

.copy-button:hover {
  background: rgba(255,255,255,0.2);
}

.copy-button.copied {
  background: #22c55e;           /* Green success */
}
```

### 4.3 Wireframe - Generating State

```
┌─────────────────────────────────────────────────────────────────────┐
│  🚀 Đang tạo code...                                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│                                                                      │
│                         ┌────────────────┐                          │
│                         │    ◐◓◑◒        │                          │
│                         │   Generating   │                          │
│                         └────────────────┘                          │
│                                                                      │
│                    Đang tạo code với Ollama...                      │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ Progress                                                         ││
│  │ ████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  35%             ││
│  │                                                                  ││
│  │ ✅ Connecting to provider...                                     ││
│  │ ✅ Sending blueprint...                                          ││
│  │ ⏳ Generating models...                                          ││
│  │ ○ Generating routes...                                           ││
│  │ ○ Running quality gates...                                       ││
│  │ ○ Packaging files...                                             ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
│                   Thời gian: 8.2s / ~15-20s                         │
│                                                                      │
│                        [ Hủy ]                                       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.3 Wireframe - Success State

```
┌─────────────────────────────────────────────────────────────────────┐
│  ✅ Tạo code thành công!                                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────┬──────────────────────────────────────┐│
│  │ 📁 Files (12)            │ 📄 backend/models/menu.py            ││
│  │                          │                                       ││
│  │ ▼ backend/               │ ```python                             ││
│  │   ├── main.py            │ from sqlalchemy import Column, ...    ││
│  │   ├── ▼ models/          │ from app.database import Base         ││
│  │   │   ├── menu.py    ←   │                                       ││
│  │   │   ├── order.py       │ class MenuItem(Base):                 ││
│  │   │   └── table.py       │     __tablename__ = "menu_items"      ││
│  │   ├── ▼ routes/          │                                       ││
│  │   │   ├── menu.py        │     id = Column(Integer, ...)         ││
│  │   │   └── order.py       │     name = Column(String(100))        ││
│  │   ├── requirements.txt   │     price = Column(Numeric(10,2))     ││
│  │   └── Dockerfile         │     category = Column(String(50))     ││
│  │                          │     ...                               ││
│  │                          │ ```                                   ││
│  │                          │                                       ││
│  │                          │ [ Copy ]  [ Raw ]                     ││
│  └──────────────────────────┴──────────────────────────────────────┘│
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ 📊 Quality Gates                                                 ││
│  │ ✅ Syntax (0.3s)  ✅ Security (1.2s)  ✅ Context  ✅ Tests (4.1s)││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ 📈 Statistics                                                    ││
│  │ Provider: Ollama • Tokens: 7,842 • Time: 14.2s • Files: 12      ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │ 📥 Download  │  │ 🔗 GitHub    │  │ ➕ Tạo Project mới       │  │
│  │    ZIP       │  │    Push      │  │    trong Orchestrator   │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. Technical Implementation

### 5.1 File Structure

```
frontend/web/src/
├── pages/
│   └── codegen/
│       └── CodeGenerationPage.tsx      # Main page
├── components/
│   └── codegen/
│       ├── BlueprintSummary.tsx        # Blueprint info display
│       ├── BlueprintJsonViewer.tsx     # JSON viewer with copy button (NEW)
│       ├── CopyableCodeBlock.tsx       # Reusable code block with copy (NEW)
│       ├── GenerationOptions.tsx       # Config form
│       ├── GenerationProgress.tsx      # Loading with steps
│       ├── GeneratedFilesView.tsx      # File tree + preview
│       ├── FilePreview.tsx             # Syntax highlight
│       └── DownloadActions.tsx         # Export buttons
├── hooks/
│   ├── useCodeGeneration.ts            # API integration hook
│   └── useCopyToClipboard.ts           # Copy hook with feedback (NEW)
└── types/
    └── codegen.ts                      # TypeScript interfaces
```

### 5.2 CopyableCodeBlock Component

```typescript
// components/codegen/CopyableCodeBlock.tsx

import { useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Check, Copy } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface CopyableCodeBlockProps {
  code: string;
  language?: string;
  title?: string;
  maxHeight?: string;
  className?: string;
}

export function CopyableCodeBlock({
  code,
  language = 'json',
  title,
  maxHeight = '400px',
  className,
}: CopyableCodeBlockProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={cn('relative rounded-lg overflow-hidden', className)}>
      {/* Header with title and copy button */}
      <div className="flex items-center justify-between px-4 py-2 bg-zinc-800 border-b border-zinc-700">
        <span className="text-sm text-zinc-400 font-mono">
          {title || language}
        </span>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleCopy}
          className={cn(
            'h-8 px-2 text-zinc-400 hover:text-white',
            copied && 'text-green-500 hover:text-green-500'
          )}
        >
          {copied ? (
            <>
              <Check className="h-4 w-4 mr-1" />
              Đã copy!
            </>
          ) : (
            <>
              <Copy className="h-4 w-4 mr-1" />
              Copy
            </>
          )}
        </Button>
      </div>

      {/* Code content */}
      <div style={{ maxHeight }} className="overflow-auto">
        <SyntaxHighlighter
          language={language}
          style={vscDarkPlus}
          customStyle={{
            margin: 0,
            padding: '16px',
            background: '#1e1e1e',
            fontSize: '13px',
          }}
        >
          {code}
        </SyntaxHighlighter>
      </div>
    </div>
  );
}
```

### 5.3 BlueprintJsonViewer Component

```typescript
// components/codegen/BlueprintJsonViewer.tsx

import { useState } from 'react';
import { ChevronDown, ChevronUp, Eye } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { CopyableCodeBlock } from './CopyableCodeBlock';
import type { AppBlueprint } from '@/types/codegen';

interface BlueprintJsonViewerProps {
  blueprint: AppBlueprint;
  defaultExpanded?: boolean;
}

export function BlueprintJsonViewer({
  blueprint,
  defaultExpanded = false,
}: BlueprintJsonViewerProps) {
  const [isOpen, setIsOpen] = useState(defaultExpanded);

  const formattedJson = JSON.stringify(blueprint, null, 2);

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <CollapsibleTrigger asChild>
        <Button variant="outline" className="w-full justify-between">
          <span className="flex items-center gap-2">
            <Eye className="h-4 w-4" />
            {isOpen ? 'Ẩn Blueprint JSON' : 'Xem Blueprint JSON'}
          </span>
          {isOpen ? (
            <ChevronUp className="h-4 w-4" />
          ) : (
            <ChevronDown className="h-4 w-4" />
          )}
        </Button>
      </CollapsibleTrigger>
      <CollapsibleContent className="mt-4">
        <CopyableCodeBlock
          code={formattedJson}
          language="json"
          title="AppBlueprint (IR)"
          maxHeight="400px"
        />
      </CollapsibleContent>
    </Collapsible>
  );
}
```

### 5.4 Route Configuration

```typescript
// src/App.tsx or routes.tsx
{
  path: '/codegen/generate',
  element: <CodeGenerationPage />,
  // Blueprint passed via location.state or URL params
}
```

### 5.3 Navigation Flow

```typescript
// From VietnameseOnboardingWizard.tsx
const handleComplete = (blueprint: AppBlueprint) => {
  navigate('/codegen/generate', {
    state: { blueprint, sessionId }
  });
};
```

---

## 6. Error Handling

### 6.1 Error States

| Error Type | User Message (VI) | Action |
|------------|-------------------|--------|
| **No Provider** | "Không có provider khả dụng. Vui lòng thử lại sau." | Retry button |
| **Generation Failed** | "Tạo code thất bại. Vui lòng thử lại." | Retry with same options |
| **Timeout** | "Quá thời gian chờ. Đang thử lại..." | Auto-retry once, then manual |
| **Quality Gate Failed** | "Code không vượt qua kiểm tra chất lượng." | Show gate details, retry |

### 6.2 Retry Logic

```typescript
const MAX_RETRIES = 2;
const RETRY_DELAY_MS = 2000;

// Auto-retry on timeout
if (error.type === 'timeout' && retryCount < MAX_RETRIES) {
  await delay(RETRY_DELAY_MS);
  return generate(options, retryCount + 1);
}
```

---

## 7. Performance Requirements

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Time to Interactive** | < 1s | Lighthouse |
| **Generation Feedback** | < 500ms | First progress update |
| **File Preview Load** | < 200ms | Syntax highlighting complete |
| **Download ZIP** | < 2s | For typical 20-file project |

---

## 8. Dependencies

### 8.1 Frontend Dependencies

```json
{
  "react-syntax-highlighter": "^15.5.0",  // Code highlighting
  "jszip": "^3.10.1",                      // ZIP generation
  "file-saver": "^2.0.5"                   // Download trigger
}
```

### 8.2 Backend Dependencies

Existing - no new dependencies required.

---

## 9. Testing Strategy

### 9.1 Unit Tests

- BlueprintSummary renders correctly
- GenerationOptions form validation
- FilePreview syntax highlighting

### 9.2 Integration Tests

- Complete flow: Blueprint → Generate → Download
- Error handling: Provider unavailable
- Retry logic: Timeout scenario

### 9.3 E2E Tests (Playwright)

```typescript
test('complete code generation flow', async ({ page }) => {
  // Navigate to onboarding
  await page.goto('/codegen-onboarding');

  // Complete wizard
  await selectDomain('restaurant');
  await enterAppName('Quán Phở 24');
  await selectFeatures(['menu', 'orders']);
  await selectScale('small');
  await page.click('button:has-text("Tạo ứng dụng")');

  // Wait for code generation page
  await expect(page).toHaveURL('/codegen/generate');

  // Generate code
  await page.click('button:has-text("Bắt đầu tạo code")');

  // Wait for success
  await expect(page.locator('text=Tạo code thành công')).toBeVisible({ timeout: 30000 });

  // Download ZIP
  const [download] = await Promise.all([
    page.waitForEvent('download'),
    page.click('button:has-text("Download ZIP")')
  ]);

  expect(download.suggestedFilename()).toMatch(/quan-pho-24.*\.zip/);
});
```

---

## 10. Security Considerations

| Concern | Mitigation |
|---------|------------|
| **XSS in code preview** | Use react-syntax-highlighter (escapes HTML) |
| **Large file DoS** | Limit file size to 1MB per file |
| **ZIP bomb** | Limit total ZIP size to 10MB |
| **Rate limiting** | Backend enforces 10 req/min per user |

---

## 11. Internationalization

Primary language: Vietnamese (vi)
Secondary: English (en)

All user-facing text stored in translation files.

---

## 12. Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | Dec 24, 2025 | Frontend Lead | Initial specification |

---

## 13. Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Frontend Lead | | _____________ | ________ |
| Backend Lead | | _____________ | ________ |
| CTO | | _____________ | ________ |

---

*EP-06 Code Generation Page - Completing the Vietnamese SME code generation flow.*
