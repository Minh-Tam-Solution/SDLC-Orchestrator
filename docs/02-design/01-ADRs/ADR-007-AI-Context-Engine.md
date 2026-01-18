# ADR-007: AI Context Engine Architecture

**Status**: APPROVED
**Date**: November 13, 2025
**Decision Makers**: CTO, CPO (joint review)
**Stage**: Stage 02 (HOW - Design & Architecture)
**Framework**: SDLC 5.1.3

---

## Context

SDLC Orchestrator requires AI capabilities for:
1. **Gate recommendations** based on team size and project type
2. **Policy generation** from natural language requirements
3. **Evidence analysis** for compliance verification
4. **Intelligent search** across documentation and evidence
5. **Automated suggestions** for gate approvals

We have access to:
- **Internal Infrastructure**: Ollama at `https://api.nhatquangholding.com/` (qwen2.5:14b with 96.4% Vietnamese accuracy)
- **AI-Platform Heritage**: Battle-tested from BFlow/NQH-Bot/MTEP (86% test coverage, Zero Mock Policy)
- **Cloud Providers**: OpenAI (GPT-4), Anthropic (Claude 3), Google (Gemini)

---

## Decision

We will implement a **Hybrid AI Architecture** with:

1. **Primary**: Internal Ollama API (api.nhatquangholding.com) for cost-effective, private processing
2. **Fallback**: Cloud providers (Claude → GPT-4 → Gemini) for advanced reasoning
3. **Orchestration**: Unified AI Gateway with provider abstraction
4. **Context Management**: Stage-aware prompting with evidence inclusion

---

## Rationale

### Why Hybrid Architecture?

**Cost Optimization**:
- Ollama (internal): ~$0.001 per 1K tokens (infrastructure cost only)
- Claude 3 Opus: $0.015/$0.075 per 1K tokens (input/output)
- GPT-4: $0.03/$0.06 per 1K tokens
- **Strategy**: 80% requests to Ollama, 20% to cloud (complex tasks)

**Data Privacy**:
- Sensitive data (PII, code, evidence) stays on-premise with Ollama
- Only sanitized prompts sent to cloud providers
- Compliance with GDPR, SOC 2, ISO 27001

**Performance**:
- Ollama: 2-6s response time (acceptable for most tasks)
- Cloud: 1-3s response time (for critical UX paths)
- Cache layer: <100ms for repeated queries

**Reliability**:
- Multi-provider fallback prevents single point of failure
- Ollama down → Claude → GPT-4 → Gemini → Error with graceful degradation

---

## Architecture Design

### 1. AI Gateway Service

```python
# ai_gateway.py - Unified AI interface
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

class AIProvider(ABC):
    @abstractmethod
    async def complete(self, prompt: str, context: Dict[str, Any]) -> str:
        pass

class OllamaProvider(AIProvider):
    """Internal Ollama at api.nhatquangholding.com"""

    def __init__(self):
        self.base_url = "https://api.nhatquangholding.com"
        self.model = "qwen2.5:14b"  # 96.4% Vietnamese accuracy

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def complete(self, prompt: str, context: Dict[str, Any]) -> str:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": self._build_prompt(prompt, context),
                    "temperature": 0.7,
                    "max_tokens": 2048
                }
            )
            response.raise_for_status()
            return response.json()["response"]

    def _build_prompt(self, prompt: str, context: Dict[str, Any]) -> str:
        """Build stage-aware prompt with context"""
        stage = context.get("stage", "unknown")
        evidence = context.get("evidence", [])

        return f"""
        You are an AI assistant for SDLC Orchestrator, a governance platform.
        Current SDLC Stage: {stage}
        Available Evidence: {', '.join(evidence)}

        User Request: {prompt}

        Provide specific, actionable guidance following SDLC 5.1.3 framework.
        """

class ClaudeProvider(AIProvider):
    """Anthropic Claude API fallback"""

    def __init__(self):
        self.api_key = os.environ["CLAUDE_API_KEY"]
        self.model = "claude-3-opus-20240229"

    async def complete(self, prompt: str, context: Dict[str, Any]) -> str:
        # Implementation for Claude API
        pass

class OpenAIProvider(AIProvider):
    """OpenAI GPT-4 fallback"""

    def __init__(self):
        self.api_key = os.environ["OPENAI_API_KEY"]
        self.model = "gpt-4-turbo-preview"

    async def complete(self, prompt: str, context: Dict[str, Any]) -> str:
        # Implementation for OpenAI API
        pass

class AIGateway:
    """Orchestrator with fallback chain"""

    def __init__(self):
        self.providers = [
            OllamaProvider(),     # Primary (internal)
            ClaudeProvider(),      # Fallback 1 (best reasoning)
            OpenAIProvider(),      # Fallback 2 (widely available)
            # GeminiProvider()     # Fallback 3 (future)
        ]
        self.cache = RedisCache()  # Response caching

    async def complete(
        self,
        prompt: str,
        context: Dict[str, Any],
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Execute with fallback chain"""

        # Check cache first
        if use_cache:
            cache_key = self._generate_cache_key(prompt, context)
            cached = await self.cache.get(cache_key)
            if cached:
                return {"response": cached, "provider": "cache", "latency_ms": 5}

        # Try each provider in order
        for i, provider in enumerate(self.providers):
            try:
                start = time.time()
                response = await provider.complete(prompt, context)
                latency = (time.time() - start) * 1000

                # Cache successful response
                if use_cache:
                    await self.cache.set(cache_key, response, ttl=3600)

                # Log metrics
                await self._log_metrics(
                    provider=provider.__class__.__name__,
                    latency_ms=latency,
                    prompt_tokens=len(prompt.split()),
                    success=True
                )

                return {
                    "response": response,
                    "provider": provider.__class__.__name__,
                    "latency_ms": latency,
                    "fallback_level": i
                }

            except Exception as e:
                logger.warning(f"Provider {provider.__class__.__name__} failed: {e}")
                continue

        # All providers failed
        raise AIServiceUnavailable("All AI providers are unavailable")
```

---

### 2. Stage-Aware Context Management

```python
# context_engine.py - SDLC stage-specific prompting
from enum import Enum
from typing import List, Dict, Any

class SDLCStage(Enum):
    """SDLC 5.1.1 stages (10 stages: 00-09 + Archive folder)"""
    STAGE_00 = "FOUNDATION - Strategic Discovery & Validation (WHY?)"
    STAGE_01 = "PLANNING - Requirements & User Stories (WHAT?)"
    STAGE_02 = "DESIGN - Architecture & Technical Design (HOW?)"
    STAGE_03 = "INTEGRATE - API Contracts & Third-party Setup"
    STAGE_04 = "BUILD - Development & Implementation"
    STAGE_05 = "TEST - Quality Assurance & Validation"
    STAGE_06 = "DEPLOY - Release & Deployment"
    STAGE_07 = "OPERATE - Production Operations & Monitoring"
    STAGE_08 = "COLLABORATE - Team Coordination & Knowledge"
    STAGE_09 = "GOVERN - Compliance & Strategic Oversight"
    STAGE_10 = "ARCHIVE - Project Archive (Legacy Docs)"

class ContextEngine:
    """Manages AI context per SDLC stage"""

    def __init__(self):
        self.stage_prompts = self._load_stage_prompts()
        self.evidence_vault = EvidenceVault()

    def _load_stage_prompts(self) -> Dict[SDLCStage, str]:
        """Load stage-specific prompt templates"""
        return {
            SDLCStage.STAGE_00: """
                Focus on problem validation and business case.
                Key questions: WHY are we building this? What problem does it solve?
                Evidence needed: User interviews, market research, competitor analysis.
            """,
            SDLCStage.STAGE_01: """
                Focus on requirements gathering and user stories.
                Key questions: WHAT are we building? Who are the users?
                Evidence needed: User stories, wireframes, API specifications.
            """,
            SDLCStage.STAGE_02: """
                Focus on technical design and architecture.
                Key questions: HOW will we build it? What technologies?
                Evidence needed: Architecture diagrams, ADRs, database schema.
            """,
            # ... other stages
        }

    async def build_context(
        self,
        project_id: str,
        stage: SDLCStage,
        include_evidence: bool = True
    ) -> Dict[str, Any]:
        """Build rich context for AI processing"""

        context = {
            "stage": stage.value,
            "stage_prompt": self.stage_prompts[stage],
            "project_id": project_id,
            "timestamp": datetime.utcnow().isoformat()
        }

        if include_evidence:
            # Fetch relevant evidence for this stage
            evidence = await self.evidence_vault.get_stage_evidence(
                project_id=project_id,
                stage=stage
            )

            # Include evidence metadata (not full content for token efficiency)
            context["evidence"] = [
                {
                    "id": e.id,
                    "title": e.title,
                    "type": e.type,
                    "summary": await self._summarize_evidence(e)
                }
                for e in evidence[:10]  # Limit to top 10 relevant
            ]

        # Add gate-specific context
        gates = await self._get_stage_gates(stage)
        context["gates"] = [
            {
                "id": g.id,
                "name": g.name,
                "status": g.status,
                "requirements": g.requirements
            }
            for g in gates
        ]

        return context

    async def _summarize_evidence(self, evidence: Evidence) -> str:
        """Generate concise summary for context inclusion"""
        if evidence.type == "document":
            # Extract first 500 chars or executive summary
            return evidence.content[:500] if evidence.content else "No summary"
        elif evidence.type == "test_report":
            # Extract pass/fail statistics
            return f"Tests: {evidence.tests_passed}/{evidence.tests_total} passed"
        # ... other evidence types
```

---

### 3. Use Case Implementations

#### 3.1 Gate Recommendation

```python
# use_cases/gate_recommendation.py
class GateRecommendationService:
    """AI-powered gate recommendations based on team/project context"""

    def __init__(self):
        self.ai_gateway = AIGateway()
        self.context_engine = ContextEngine()

    async def recommend_gates(
        self,
        team_size: int,
        project_type: str,
        compliance_requirements: List[str]
    ) -> Dict[str, Any]:
        """Recommend which gates to enforce"""

        prompt = f"""
        Based on the following project context, recommend which SDLC 5.1.3 gates to enforce:

        Team Size: {team_size} engineers
        Project Type: {project_type}
        Compliance: {', '.join(compliance_requirements)}

        For each recommended gate, explain:
        1. Why it's important for this project
        2. What evidence is required
        3. Who should approve (roles)
        4. Estimated effort to pass

        Format response as JSON with gates array.
        """

        context = {
            "stage": SDLCStage.STAGE_00,  # Planning phase
            "team_size": team_size,
            "project_type": project_type,
            "compliance": compliance_requirements
        }

        response = await self.ai_gateway.complete(prompt, context)

        # Parse and validate AI response
        recommendations = self._parse_recommendations(response["response"])

        # Apply business rules
        recommendations = self._apply_business_rules(recommendations, team_size)

        # Store for audit
        await self._audit_recommendation(
            input_params={
                "team_size": team_size,
                "project_type": project_type,
                "compliance": compliance_requirements
            },
            recommendations=recommendations,
            provider=response["provider"],
            latency=response["latency_ms"]
        )

        return recommendations

    def _apply_business_rules(
        self,
        recommendations: List[Dict],
        team_size: int
    ) -> List[Dict]:
        """Apply domain-specific rules to AI recommendations"""

        # Small teams (<10): Lite policy pack
        if team_size < 10:
            # Filter out enterprise-only gates
            recommendations = [
                r for r in recommendations
                if r["gate_id"] not in ["G7", "G8", "G9"]
            ]

        # Large teams (>50): Mandatory security gates
        elif team_size > 50:
            # Ensure security gates are included
            security_gates = ["G2", "G5"]
            for gate in security_gates:
                if not any(r["gate_id"] == gate for r in recommendations):
                    recommendations.append({
                        "gate_id": gate,
                        "reason": "Mandatory for large teams",
                        "required": True
                    })

        return recommendations
```

#### 3.2 Policy Generation

```python
# use_cases/policy_generation.py
class PolicyGenerationService:
    """Generate OPA policies from natural language"""

    async def generate_policy(
        self,
        requirement: str,
        examples: List[str] = None
    ) -> Dict[str, Any]:
        """Convert requirement to OPA Rego policy"""

        prompt = f"""
        Convert this requirement to an OPA (Open Policy Agent) Rego policy:

        Requirement: {requirement}

        Examples of similar policies:
        {chr(10).join(examples) if examples else "None provided"}

        Generate:
        1. Rego policy code (valid syntax)
        2. Test cases (at least 3)
        3. Documentation explaining the policy

        Follow OPA best practices and ensure the policy is production-ready.
        """

        context = {
            "stage": SDLCStage.STAGE_02,  # Design phase
            "policy_type": "gate_validation"
        }

        response = await self.ai_gateway.complete(prompt, context)

        # Validate Rego syntax
        policy_code = self._extract_rego_code(response["response"])
        validation_result = await self._validate_rego(policy_code)

        if not validation_result["valid"]:
            # Retry with error feedback
            prompt += f"\n\nPrevious attempt had error: {validation_result['error']}"
            response = await self.ai_gateway.complete(prompt, context)
            policy_code = self._extract_rego_code(response["response"])

        return {
            "policy_code": policy_code,
            "test_cases": self._extract_test_cases(response["response"]),
            "documentation": self._extract_documentation(response["response"]),
            "provider": response["provider"],
            "validated": True
        }
```

---

### 4. Safety & Ethics

```python
# safety/ai_safety.py
class AISafetyGuard:
    """Ensure AI outputs are safe and appropriate"""

    def __init__(self):
        self.prohibited_patterns = self._load_prohibited_patterns()
        self.pii_detector = PIIDetector()

    async def sanitize_input(self, text: str) -> str:
        """Remove sensitive data before sending to AI"""

        # Remove PII
        text = self.pii_detector.redact(text)

        # Remove credentials
        text = re.sub(r'(api[_-]?key|password|secret)[\s:=]+\S+', '[REDACTED]', text, flags=re.I)

        # Remove internal URLs
        text = re.sub(r'https?://[^\s]*\.(internal|local|dev)', '[INTERNAL_URL]', text)

        return text

    async def validate_output(self, text: str) -> Dict[str, Any]:
        """Check AI output for safety issues"""

        issues = []

        # Check for prohibited content
        for pattern in self.prohibited_patterns:
            if re.search(pattern, text, re.I):
                issues.append(f"Prohibited pattern detected: {pattern}")

        # Check for potential code injection
        if self._contains_code_injection(text):
            issues.append("Potential code injection detected")

        # Check for bias
        bias_score = await self._check_bias(text)
        if bias_score > 0.7:
            issues.append(f"High bias detected: {bias_score}")

        return {
            "safe": len(issues) == 0,
            "issues": issues,
            "sanitized_text": self._sanitize_output(text) if issues else text
        }

    def _contains_code_injection(self, text: str) -> bool:
        """Detect potential code injection attempts"""
        dangerous_patterns = [
            r'exec\s*\(',
            r'eval\s*\(',
            r'__import__',
            r'subprocess\.',
            r'os\.system',
            r'DROP\s+TABLE',
            r'DELETE\s+FROM',
            r'<script',
            r'javascript:'
        ]

        return any(re.search(p, text, re.I) for p in dangerous_patterns)
```

---

### 5. Cost Management

```python
# cost/ai_cost_manager.py
class AICostManager:
    """Track and optimize AI usage costs"""

    def __init__(self):
        self.cost_per_token = {
            "OllamaProvider": 0.000001,     # $0.001 per 1K tokens
            "ClaudeProvider": 0.000045,     # $0.045 per 1K tokens (avg in/out)
            "OpenAIProvider": 0.000045,     # $0.045 per 1K tokens
        }
        self.monthly_budget = 1000  # $1000/month
        self.usage_tracker = UsageTracker()

    async def check_budget(self, provider: str, estimated_tokens: int) -> bool:
        """Check if request fits within budget"""

        # Get current month usage
        current_usage = await self.usage_tracker.get_monthly_usage()

        # Calculate estimated cost
        estimated_cost = estimated_tokens * self.cost_per_token[provider]

        # Check if within budget
        if current_usage + estimated_cost > self.monthly_budget:
            # Try cheaper provider
            if provider != "OllamaProvider":
                return False  # Force fallback to Ollama
            else:
                # Budget exhausted
                raise BudgetExceededException(
                    f"Monthly budget exceeded: ${current_usage:.2f}/${self.monthly_budget}"
                )

        return True

    async def optimize_routing(
        self,
        task_complexity: str,
        urgency: str
    ) -> str:
        """Route to optimal provider based on task"""

        # Simple tasks → Ollama (cheap)
        if task_complexity == "simple":
            return "OllamaProvider"

        # Complex + urgent → Claude (best quality)
        if task_complexity == "complex" and urgency == "high":
            # Check budget allows premium provider
            if await self.check_budget("ClaudeProvider", 1000):
                return "ClaudeProvider"

        # Default to Ollama with fallback
        return "OllamaProvider"
```

---

## Consequences

### Positive

1. **Cost Efficiency**: 80% requests to internal Ollama (~$50/month vs $1000/month cloud-only)
2. **Data Privacy**: Sensitive data stays on-premise
3. **Reliability**: Multi-provider fallback ensures 99.9% availability
4. **Flexibility**: Easy to add new providers or switch primary
5. **Performance**: Cache layer provides <100ms response for repeated queries
6. **Heritage**: Leverages battle-tested AI-Platform from BFlow (86% test coverage)

### Negative

1. **Complexity**: Managing multiple providers adds operational overhead
2. **Latency Variance**: Ollama (2-6s) vs Cloud (1-3s) creates inconsistent UX
3. **Feature Gaps**: Ollama may not support latest features (function calling, vision)
4. **Maintenance**: Need to maintain prompt compatibility across providers

### Risks

1. **Ollama Downtime**: Internal infrastructure dependency
   - **Mitigation**: Automatic fallback to cloud providers

2. **Token Limits**: Complex contexts may exceed model limits
   - **Mitigation**: Context compression, chunking strategies

3. **Cost Overrun**: Excessive cloud API usage
   - **Mitigation**: Budget controls, usage monitoring, alerts

---

## Implementation Plan

### Phase 1: Foundation (Week 1 BUILD)
- [ ] Setup AI Gateway with provider abstraction
- [ ] Implement Ollama provider with api.nhatquangholding.com
- [ ] Add Claude and OpenAI providers
- [ ] Create context engine with stage-aware prompting
- [ ] Add Redis caching layer

### Phase 2: Core Features (Week 2 BUILD)
- [ ] Gate recommendation service
- [ ] Policy generation from natural language
- [ ] Evidence analysis and summarization
- [ ] Intelligent search with semantic similarity

### Phase 3: Safety & Optimization (Week 3 BUILD)
- [ ] PII detection and redaction
- [ ] Output validation and safety checks
- [ ] Cost tracking and budget controls
- [ ] Performance monitoring and alerts

### Phase 4: Advanced Features (Week 4+ BUILD)
- [ ] Multi-turn conversations with context
- [ ] Batch processing for large analyses
- [ ] Fine-tuning Ollama for SDLC domain
- [ ] A/B testing different models

---

## Alternatives Considered

### Alternative 1: Cloud-Only (OpenAI/Claude)
- ❌ **Rejected**: Too expensive ($1000+/month), data privacy concerns

### Alternative 2: Ollama-Only (No Fallback)
- ❌ **Rejected**: Single point of failure, limited capabilities

### Alternative 3: Build Custom Model
- ❌ **Rejected**: 6-12 months effort, requires ML expertise

### Alternative 4: No AI Features
- ❌ **Rejected**: Competitive disadvantage, 20% of product moat

---

## Approval

| Role | Name | Decision | Date | Comment |
|------|------|----------|------|---------|
| **CTO** | [CTO Name] | ✅ APPROVED | Nov 13, 2025 | Excellent cost/privacy balance with Ollama |
| **CPO** | [CPO Name] | ✅ APPROVED | Nov 13, 2025 | AI = 20% of competitive moat, critical for UX |
| **Security Lead** | [Security Name] | ✅ APPROVED | Nov 13, 2025 | On-premise option addresses data concerns |

---

**Decision**: **APPROVED** - Hybrid AI Architecture with Ollama primary + cloud fallback

**Priority**: **CRITICAL** - Blocks 20% of product differentiation

**Timeline**: 4 weeks implementation in BUILD phase

**Success Metrics**:
- Cost per request <$0.01 average
- Response time <3s p95
- Availability >99.9%
- User satisfaction >4.0/5 for AI features

---

*"Leverage internal AI infrastructure (Ollama) while maintaining cloud flexibility"* 🤖