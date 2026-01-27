# ADR-039: App Builder Deterministic Scaffolder Integration

**Status:** Accepted  
**Date:** 2026-01-27  
**Sprint:** Sprint 106  
**Deciders:** CTO, Architecture Team  
**Related:** ADR-028 (EP-06 IR-Based Codegen), ADR-031 (Multi-Provider Fallback Chain)

---

## Context

SDLC Orchestrator currently has a production-ready EP-06 IR-Based Codegen system focused on Vietnamese SME domains (F&B, hospitality, retail). The system uses:

- **Multi-provider architecture**: Ollama → Claude → DeepCode fallback chain
- **IR-based generation**: AppBlueprint intermediate representation
- **4-Gate Quality Pipeline**: Syntax → Security → Context → Tests
- **Evidence Vault integration**: Tamper-evident audit trail
- **Streaming with SSE**: Real-time generation updates

The `.claude/skills/app-builder` skill provides 13 generic project templates (Next.js, FastAPI, React Native, etc.) with high-level orchestration. This creates an opportunity to expand from Vietnamese SME focus → Universal app scaffolding.

### Key Business Drivers

1. **Market expansion**: Vietnamese SME templates → Universal tech stacks
2. **Competitive parity**: Bolt.new, v0.dev, Cursor have instant scaffolding
3. **Customer demand**: Users need quick project initialization before governance kicks in
4. **Strategic moat**: Governance (our strength) applies AFTER scaffolding

### Strategic Clarification

**Core Product Identity:** SDLC Orchestrator is an **AI Dev Governance Platform**, not a code generator.

- **Primary moat**: Evidence Vault, quality gates, lifecycle-aware context, AGENTS.md enforcement
- **Secondary feature**: Code generation as input to governance pipeline

**App-builder's role**: Provide breadth (13 templates) while EP-06 provides depth (quality, evidence, governance).

---

## Decision

### Sprint 106 (MVP): Option A - Provider-Only Architecture

Implement app-builder as a **deterministic scaffolder provider** in the existing multi-provider registry:

```python
# backend/app/services/codegen/app_builder_provider.py
class AppBuilderProvider(CodegenProvider):
    """Deterministic template scaffolder (no AI calls, $0 cost)"""
    
    async def generate(self, spec: CodegenSpec) -> CodegenResult:
        # 1. Detect project type from spec
        template = self.select_template(spec)
        
        # 2. Generate TemplateBlueprint (IR)
        blueprint = await template.scaffold(spec)
        
        # 3. Return CodegenResult (participates in quality pipeline)
        return CodegenResult(
            files=blueprint.files,
            provider="app-builder",
            cost_usd=0.0,  # Deterministic, no AI calls
            metadata={"template": template.name}
        )
```

**Key architectural decisions:**

1. **Deterministic execution**: No runtime calls to Claude/Ollama. Templates are pure Python code.
2. **Zero cost**: app-builder does not consume AI credits (deterministic scaffolding).
3. **Quality pipeline participation**: All generated code passes through 4-Gate validation.
4. **Evidence Vault integration**: Automatic via existing CodegenResult → Evidence flow.

### Sprint 107 (Full): Option C - Hybrid with Planning Sub-Agent

Add Planning Orchestrator integration for high-risk projects:

```python
# backend/app/services/app_builder_agent.py
class AppBuilderSubAgent(SubAgent):
    async def explore(self, context: PlanningContext) -> ExploreResult:
        if context.intent == "NEW_SCAFFOLD":
            template = self.recommend_template(context)
            return ExploreResult(
                recommendations=[f"Use {template.name} template"],
                confidence=template.match_confidence,
                preview=template.generate_preview()
            )
```

**Deferred to Sprint 107:**
- Sub-agent integration
- CRP workflow for template selection approval
- Coordinator glue between planning → execution

---

## Consequences

### Positive

✅ **Minimal complexity**: Option A is 2-day implementation (vs 5-day hybrid)  
✅ **Automatic governance**: 4-Gate quality, Evidence Vault, streaming all work automatically  
✅ **Clear cost model**: $0 for app-builder, existing pricing for fallback providers  
✅ **Risk reduction**: No runtime Claude skill calls → no permission/security issues  
✅ **Incremental delivery**: Ship scaffolding in Sprint 106, orchestration in Sprint 107

### Negative

❌ **No upfront approval**: Users don't get CRP workflow for template selection (until Sprint 107)  
❌ **Limited customization**: Templates are fixed blueprints (not AI-customized)  
❌ **Maintenance burden**: 13 templates × framework updates = ongoing maintenance

### Neutral

⚪ **Two-phase delivery**: Scaffolding now, orchestration later (acceptable)  
⚪ **Template versioning**: Will need policy for deprecation (address in Sprint 108)

---

## Implementation Strategy

### Phase 1: Core Infrastructure (Day 1-2)

**1. Router with Intent Detection**

```python
# backend/app/services/codegen/provider_router.py
class ProviderRouter:
    def select_provider(self, spec: CodegenSpec) -> CodegenProvider:
        intent = self.detect_intent(spec)
        
        if intent == Intent.NEW_SCAFFOLD:
            confidence = app_builder.match_confidence(spec)
            if confidence >= 80:
                return app_builder_provider
            elif confidence >= 50:
                return hybrid_provider(app_builder, ollama)
        
        elif intent == Intent.MODIFY_EXISTING:
            return ep06_ir_provider  # Pattern-based modification
        
        elif intent == Intent.DOMAIN_SME:
            return ep06_domain_provider  # Vietnamese templates
        
        # Default fallback chain
        return multi_provider_chain
```

**Intent Detection Rules:**

| Intent | Triggers | Provider |
|--------|----------|----------|
| `NEW_SCAFFOLD` | "Create new", "initialize", empty repo | app-builder (if confidence ≥ 80) |
| `MODIFY_EXISTING` | Has repo context, "add feature", "refactor" | EP-06 IR / pattern-based |
| `DOMAIN_SME` | "restaurant", "hotel", "store", Vietnamese keywords | EP-06 Vietnamese templates |
| `FEATURE_ADD` | "implement auth", "add payment" | Ollama → Claude fallback |

**2. TemplateBlueprint Contract**

```python
# backend/app/schemas/codegen/template_blueprint.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class TemplateBlueprint(BaseModel):
    """Standardized output for template scaffolders.
    
    Subset of AppBlueprint (EP-06 IR) for template-based generation.
    """
    
    # Core metadata
    name: str = Field(..., description="Project name")
    template_id: str = Field(..., description="Template identifier (nextjs-fullstack, fastapi, etc.)")
    template_version: str = Field(default="1.0.0", description="Template version (for updates)")
    
    # Tech stack
    framework: str = Field(..., description="Primary framework (Next.js, FastAPI, React Native)")
    language: str = Field(..., description="Primary language (TypeScript, Python)")
    runtime: str = Field(..., description="Runtime (Node 20, Python 3.12)")
    
    # Project structure
    modules: List[str] = Field(default_factory=list, description="Top-level modules/packages")
    entry_points: Dict[str, str] = Field(..., description="Entry files (main.py, app.tsx)")
    
    # Security & config
    auth_strategy: Optional[str] = Field(None, description="Auth method (NextAuth, JWT, OAuth)")
    env_vars: List[str] = Field(default_factory=list, description="Required env variables")
    secrets: List[str] = Field(default_factory=list, description="Secret keys (API keys, tokens)")
    
    # Build artifacts
    files: List[GeneratedFile] = Field(..., description="Generated files")
    scripts: Dict[str, str] = Field(..., description="Package.json scripts or Makefile targets")
    dependencies: List[str] = Field(default_factory=list, description="Package dependencies")
    
    # Quality metadata (for evidence vault)
    quality_profile: str = Field(default="scaffold", description="scaffold | production")
    estimated_loc: int = Field(..., description="Total lines of code generated")


class GeneratedFile(BaseModel):
    path: str
    content: str
    language: str
    metadata: Optional[Dict] = None
```

**Adapter Interface:**

```python
# backend/app/services/codegen/templates/base_template.py
from abc import ABC, abstractmethod

class BaseTemplate(ABC):
    """Abstract base for all app-builder templates."""
    
    name: str
    framework: str
    language: str
    
    @abstractmethod
    def detect_match(self, spec: CodegenSpec) -> float:
        """Return confidence score 0-100 for matching spec."""
        pass
    
    @abstractmethod
    async def scaffold(self, spec: CodegenSpec) -> TemplateBlueprint:
        """Generate TemplateBlueprint with all files."""
        pass
    
    def get_secure_defaults(self) -> Dict:
        """Return secure defaults (auth, CSP, CORS, etc.)"""
        return {
            "csp": "default-src 'self'",
            "cors": ["http://localhost:3000"],
            "rate_limit": "100/hour"
        }
```

**3. Scaffold Quality Profile**

```python
# backend/app/services/codegen/quality_profiles.py
class ScaffoldQualityProfile:
    """Lenient profile for initial scaffolds."""
    
    gates = {
        "syntax": {
            "required": True,
            "fail_on_error": True,
            "description": "Code must compile without syntax errors"
        },
        "security": {
            "required": True,
            "fail_on_error": True,
            "description": "No OWASP Top 10 violations",
            "exemptions": [
                "Missing rate limiting (scaffold phase)",
                "Placeholder secrets (user must replace)"
            ]
        },
        "context": {
            "required": False,  # Soft fail
            "fail_on_error": False,
            "description": "Import consistency (may have placeholders)",
            "exemptions": [
                "Optional dependencies (user installs later)",
                "Placeholder components (to be implemented)"
            ]
        },
        "tests": {
            "required": False,  # N/A for scaffolds
            "fail_on_error": False,
            "description": "Unit tests (users add incrementally)"
        }
    }
```

**Gate 2 (Security) Tool Stack:**

- **TypeScript/Node**: `npm audit`, `eslint-plugin-security`
- **Python**: `bandit`, `safety`
- **React Native**: `react-native-community/eslint-config` with security rules

### Phase 2: MVP Templates (Day 3-4)

**Template 1: Next.js Fullstack**

```python
# backend/app/services/codegen/templates/nextjs_fullstack.py
class NextJsFullstackTemplate(BaseTemplate):
    name = "nextjs-fullstack"
    framework = "Next.js"
    language = "TypeScript"
    
    def detect_match(self, spec: CodegenSpec) -> float:
        keywords = ["next.js", "nextjs", "full-stack", "react", "ssr"]
        description_lower = spec.description.lower()
        
        matches = sum(1 for kw in keywords if kw in description_lower)
        confidence = min(100, matches * 25)
        
        return confidence
    
    async def scaffold(self, spec: CodegenSpec) -> TemplateBlueprint:
        files = [
            self._generate_app_layout(),
            self._generate_page_tsx(),
            self._generate_api_route(),
            self._generate_prisma_schema(),
            self._generate_package_json(),
            self._generate_env_example(),
            self._generate_tsconfig(),
            self._generate_next_config(),
        ]
        
        return TemplateBlueprint(
            name=spec.project_name,
            template_id=self.name,
            template_version="1.0.0",
            framework=self.framework,
            language=self.language,
            runtime="Node 20",
            modules=["app", "components", "lib", "prisma"],
            entry_points={"app": "app/layout.tsx"},
            auth_strategy="NextAuth.js",
            env_vars=["DATABASE_URL", "NEXTAUTH_SECRET", "NEXTAUTH_URL"],
            secrets=["NEXTAUTH_SECRET"],
            files=files,
            scripts={
                "dev": "next dev",
                "build": "next build",
                "start": "next start",
                "lint": "next lint",
                "db:push": "prisma db push"
            },
            dependencies=[
                "next@15.1.0",
                "react@19.0.0",
                "prisma@6.0.0",
                "next-auth@5.0.0",
                "zod@3.24.1"
            ],
            quality_profile="scaffold",
            estimated_loc=450
        )
    
    def _generate_app_layout(self) -> GeneratedFile:
        return GeneratedFile(
            path="app/layout.tsx",
            language="typescript",
            content='''import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'App',
  description: 'Generated by SDLC Orchestrator',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  )
}
'''
        )
    
    # ... (more file generators)
```

**Template 2: FastAPI**

```python
# backend/app/services/codegen/templates/python_fastapi.py
class PythonFastAPITemplate(BaseTemplate):
    name = "python-fastapi"
    framework = "FastAPI"
    language = "Python"
    
    async def scaffold(self, spec: CodegenSpec) -> TemplateBlueprint:
        files = [
            self._generate_main_py(),
            self._generate_models_py(),
            self._generate_schemas_py(),
            self._generate_crud_py(),
            self._generate_database_py(),
            self._generate_requirements_txt(),
            self._generate_env_example(),
            self._generate_dockerfile(),
        ]
        
        return TemplateBlueprint(
            name=spec.project_name,
            template_id=self.name,
            template_version="1.0.0",
            framework=self.framework,
            language=self.language,
            runtime="Python 3.12",
            modules=["app", "app/models", "app/schemas", "app/api"],
            entry_points={"api": "app/main.py"},
            auth_strategy="JWT",
            env_vars=["DATABASE_URL", "SECRET_KEY"],
            secrets=["SECRET_KEY"],
            files=files,
            scripts={
                "dev": "uvicorn app.main:app --reload",
                "start": "uvicorn app.main:app --host 0.0.0.0 --port 8000",
                "test": "pytest",
                "lint": "ruff check ."
            },
            dependencies=[
                "fastapi==0.115.0",
                "uvicorn[standard]==0.32.0",
                "sqlalchemy==2.0.36",
                "pydantic==2.10.4",
                "python-jose[cryptography]==3.3.0",
                "passlib[bcrypt]==1.7.4"
            ],
            quality_profile="scaffold",
            estimated_loc=350
        )
```

**Template 3: Next.js SaaS**

```python
# Extends NextJsFullstackTemplate with Stripe integration
class NextJsSaaSTemplate(NextJsFullstackTemplate):
    name = "nextjs-saas"
    
    async def scaffold(self, spec: CodegenSpec) -> TemplateBlueprint:
        blueprint = await super().scaffold(spec)
        
        # Add Stripe-specific files
        blueprint.files.extend([
            self._generate_stripe_webhook(),
            self._generate_pricing_page(),
            self._generate_subscription_api(),
        ])
        
        blueprint.env_vars.extend([
            "STRIPE_SECRET_KEY",
            "STRIPE_WEBHOOK_SECRET",
            "STRIPE_PRICE_ID"
        ])
        
        blueprint.dependencies.append("stripe@17.5.0")
        
        return blueprint
```

**Template 4: React Native**

```python
# backend/app/services/codegen/templates/react_native_app.py
class ReactNativeAppTemplate(BaseTemplate):
    name = "react-native-app"
    framework = "React Native (Expo)"
    language = "TypeScript"
    
    async def scaffold(self, spec: CodegenSpec) -> TemplateBlueprint:
        files = [
            self._generate_app_tsx(),
            self._generate_navigation(),
            self._generate_screens(),
            self._generate_components(),
            self._generate_app_json(),
            self._generate_package_json(),
            self._generate_tsconfig(),
        ]
        
        return TemplateBlueprint(
            name=spec.project_name,
            template_id=self.name,
            template_version="1.0.0",
            framework=self.framework,
            language=self.language,
            runtime="Node 20 + Expo SDK 52",
            modules=["screens", "components", "navigation", "store"],
            entry_points={"app": "App.tsx"},
            auth_strategy="expo-auth-session",
            env_vars=["API_URL", "AUTH_CLIENT_ID"],
            secrets=["AUTH_CLIENT_ID"],
            files=files,
            scripts={
                "start": "expo start",
                "android": "expo start --android",
                "ios": "expo start --ios",
                "web": "expo start --web",
                "lint": "eslint ."
            },
            dependencies=[
                "expo@52.0.0",
                "react@18.3.1",
                "react-native@0.76.0",
                "@react-navigation/native@7.0.0",
                "zustand@5.0.2"
            ],
            quality_profile="scaffold",
            estimated_loc=400
        )
```

### Phase 3: Provider Implementation (Day 5)

```python
# backend/app/services/codegen/app_builder_provider.py
from .base_provider import CodegenProvider
from .templates import (
    NextJsFullstackTemplate,
    PythonFastAPITemplate,
    NextJsSaaSTemplate,
    ReactNativeAppTemplate
)

class AppBuilderProvider(CodegenProvider):
    """Deterministic template scaffolder (no AI calls, $0 cost)."""
    
    name = "app-builder"
    display_name = "App Builder (Universal Templates)"
    
    def __init__(self):
        self.templates = [
            NextJsFullstackTemplate(),
            PythonFastAPITemplate(),
            NextJsSaaSTemplate(),
            ReactNativeAppTemplate(),
        ]
    
    def select_template(self, spec: CodegenSpec) -> BaseTemplate:
        """Select best matching template by confidence score."""
        scores = [(tmpl, tmpl.detect_match(spec)) for tmpl in self.templates]
        best_template, confidence = max(scores, key=lambda x: x[1])
        
        if confidence < 50:
            raise ValueError(f"No template match (best: {best_template.name} at {confidence}%)")
        
        return best_template
    
    async def generate(self, spec: CodegenSpec) -> CodegenResult:
        start_time = time.time()
        
        # 1. Select template
        template = self.select_template(spec)
        
        # 2. Generate blueprint
        blueprint = await template.scaffold(spec)
        
        # 3. Convert to CodegenResult (EP-06 format)
        result = CodegenResult(
            files=blueprint.files,
            provider="app-builder",
            generation_time_ms=int((time.time() - start_time) * 1000),
            metadata={
                "template": blueprint.template_id,
                "template_version": blueprint.template_version,
                "framework": blueprint.framework,
                "quality_profile": blueprint.quality_profile,
                "estimated_loc": blueprint.estimated_loc
            },
            cost_estimate=CostEstimate(
                provider="app-builder",
                estimated_cost_usd=0.0,  # Deterministic, no AI calls
                estimated_time_ms=1000
            )
        )
        
        return result
    
    async def estimate_cost(self, spec: CodegenSpec) -> CostEstimate:
        """App-builder is deterministic → $0 cost."""
        return CostEstimate(
            provider="app-builder",
            estimated_cost_usd=0.0,
            estimated_time_ms=1000,
            breakdown={
                "template_scaffolding": 0.0,
                "ai_calls": 0.0
            }
        )
```

**Provider Registration:**

```python
# backend/app/services/codegen/provider_registry.py
def register_providers():
    registry = ProviderRegistry()
    
    # App-builder (deterministic scaffolder)
    registry.register(AppBuilderProvider())
    
    # AI providers (fallback chain)
    registry.register(OllamaProvider())
    registry.register(ClaudeProvider())
    registry.register(DeepCodeProvider())
    
    return registry
```

### Phase 4: Testing & Documentation (Day 6)

**E2E Test Scenario (Simplified):**

```python
# backend/tests/e2e/test_app_builder_scaffold.py
async def test_nextjs_fullstack_scaffold():
    """Test: Generate Next.js fullstack app, validate quality gates."""
    
    # 1. Submit request
    spec = CodegenSpec(
        project_name="my-blog",
        description="Create a Next.js blog with Prisma and NextAuth",
        preferred_provider="app-builder"
    )
    
    # 2. Router selects app-builder
    router = ProviderRouter()
    provider = router.select_provider(spec)
    assert provider.name == "app-builder"
    
    # 3. Generate
    result = await provider.generate(spec)
    assert result.provider == "app-builder"
    assert result.cost_estimate.estimated_cost_usd == 0.0
    assert len(result.files) >= 8  # layout, page, api, prisma, config files
    
    # 4. Quality gates
    quality_result = await quality_pipeline.validate(result, profile="scaffold")
    assert quality_result.gate_1_syntax == "PASS"
    assert quality_result.gate_2_security == "PASS"
    assert quality_result.gate_3_context in ["PASS", "SOFT_FAIL"]  # Allowed
    assert quality_result.gate_4_tests in ["N/A", "SKIP"]  # Expected for scaffolds
    
    # 5. Evidence Vault
    evidence = await evidence_vault.store(result)
    assert evidence.state == "evidence_locked"
    assert evidence.provider == "app-builder"
    assert evidence.hash_sha256 is not None
    
    # 6. Build validation
    await write_files_to_temp(result.files, "/tmp/my-blog")
    build_result = await run_command("npm install && npm run build", cwd="/tmp/my-blog")
    assert build_result.exit_code == 0
```

---

## Success Metrics (Sprint 106)

| Metric | Target | Verification |
|--------|--------|--------------|
| **Templates implemented** | 4/4 | Unit tests pass for each template |
| **Provider registration** | app-builder in registry | `GET /codegen/providers` returns it |
| **Quality gates** | G1+G2 pass, G3 soft-fail | Generate sample app → gates pass |
| **Cost tracking** | $0.00 for app-builder | `GET /codegen/usage/report` shows $0 |
| **Streaming** | SSE updates work | Generate app → frontend shows real-time updates |
| **Evidence Vault** | Files stored with hash | Check `gate_evidence` table |
| **Router** | Intent detection works | NEW_SCAFFOLD → app-builder, MODIFY → EP-06 |
| **Build validation** | Generated code compiles | `npm run build` succeeds (Next.js), `uvicorn` starts (FastAPI) |

---

## Template Lifecycle Policy

**Version Pinning:**
- All dependencies pinned to specific versions (e.g., `next@15.1.0`)
- Template version increments on any dependency update

**Security Scanning:**
- Monthly `npm audit` / `pip-audit` for all templates
- CVE notifications → template patch within 48 hours

**Usage-Based Retention:**
- Track template usage via Evidence Vault metadata
- Templates with < 5 uses in 6 months → **DEPRECATED**
- Deprecated templates remain available but no longer updated

**Update Schedule:**
- Major framework updates: Reviewed within 30 days, implemented within 60 days
- Minor updates: Batched quarterly
- Security patches: Immediate (48-hour SLA)

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Template drift** | High | Medium | Automated dependency scanning, 6-month review cycle |
| **Gate 2 (Security) false negatives** | Medium | High | Multi-tool validation (bandit + safety + npm audit) |
| **User expects AI customization** | Medium | Low | Clear UI messaging: "Scaffold → Customize → Govern" |
| **Maintenance burden (13 templates)** | High | Medium | Usage-based retention, deprecate low-traffic templates |
| **Conflict with EP-06 Vietnamese templates** | Low | Medium | Router intent detection, separate UI categories |

---

## Future Enhancements (Sprint 107+)

### Sprint 107: Planning Sub-Agent Integration

- Implement `AppBuilderSubAgent` in Planning Orchestrator
- CRP workflow for high-risk template selections (risk ≥ 70)
- Coordinator glue: planning blueprint → execution provider

### Sprint 108-110: Template Expansion

**Priority 2 Templates (Q1 2026):**
- Flutter app (cross-platform mobile)
- Express API (Node.js backend)
- Nuxt app (Vue full-stack)

**Priority 3 Templates (Q2 2026):**
- Electron desktop (desktop apps)
- Chrome extension (browser extensions)
- CLI tool (command-line apps)
- Monorepo (Turborepo)
- Next.js static (landing pages)

### Sprint 111+: Advanced Features

- **AI-assisted customization**: Use Ollama to customize template after scaffold
- **Multi-template composition**: Combine backend + frontend templates
- **User-defined templates**: Allow teams to create custom templates
- **Template marketplace**: Community-contributed templates

---

## References

- ADR-028: EP-06 IR-Based Codegen Architecture
- ADR-031: Multi-Provider Fallback Chain
- Sprint 45-50: EP-06 Implementation
- Sprint 101: Planning Orchestrator with CRP
- `.claude/skills/app-builder/SKILL.md`: Original skill specification

---

## Appendix: Router Decision Table

| Spec Characteristics | Intent | Selected Provider | Reasoning |
|---------------------|--------|-------------------|-----------|
| Empty repo + "Create Next.js app" | `NEW_SCAFFOLD` | app-builder (confidence 95) | Perfect template match |
| Empty repo + "Build blockchain DAO" | `NEW_SCAFFOLD` | ollama (confidence 10) | No template, need AI |
| Has repo + "Add auth to Express" | `MODIFY_EXISTING` | EP-06 IR + pattern extraction | Existing codebase |
| "Làm web nhà hàng Việt Nam" | `DOMAIN_SME` | EP-06 Vietnamese restaurant template | Vietnamese keywords |
| "Create CRUD for users" | `FEATURE_ADD` | ollama → claude fallback | Generic feature, AI-generated |
| "Init FastAPI with JWT" | `NEW_SCAFFOLD` | app-builder (confidence 90) | Template match |

---

## Decision Timeline

- **2026-01-25**: Initial plan proposed (Option C, 5 days)
- **2026-01-27**: CTO review → Approved with modifications
- **2026-01-27**: Revised to Option A MVP (Sprint 106), Option C full (Sprint 107)
- **2026-01-27**: ADR-039 drafted and accepted

---

**Status: ACCEPTED**  
**Next: Sprint 106 implementation begins 2026-01-28**
