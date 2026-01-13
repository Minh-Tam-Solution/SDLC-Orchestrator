"""
=========================================================================
SOP Generator Service - AI-Assisted Standard Operating Procedure Generation
SDLC Orchestrator - Phase 2-Pilot (SE 3.0 Track 1)

Version: 1.0.0
Date: December 23, 2025
Status: ACTIVE - Phase 2-Pilot Week 1
Authority: CTO Approved (BRS-PILOT-001)
Foundation: SE 3.0 SASE Integration, Phase 1-Spec (v5.1.0-agentic-spec-alpha)
Framework: SDLC 5.1.0 Complete Lifecycle

Purpose:
- Generate SOPs from workflow descriptions using AI
- Support 5 SOP types: Deployment, Incident, Change, Backup, Security
- Produce MRP evidence for each generation
- Enable VCR approval workflow

BRS Reference: BRS-PILOT-001-NQH-Bot-SOP-Generator.yaml
Functional Requirements:
- FR1: Generate SOP from workflow description
- FR2: Include 5 mandatory sections
- FR3: Support 5 SOP types
- FR4: ISO 9001 compliance validation
- FR5: Evidence Vault storage with SHA256
- FR6: MRP generation with evidence
- FR7: VCR approval workflow

Non-Functional Requirements:
- NFR1: Generation time <30s (p95)
- NFR2: Quality rating ≥4/5
- NFR3: Cost <$50/month (Ollama)
- NFR4: Success rate ≥95%
- NFR5: No sensitive data leakage

Zero Mock Policy: 100% real implementation
=========================================================================
"""

import hashlib
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from app.core.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# SOP Types and Structures
# ============================================================================


class SOPType(str, Enum):
    """5 SOP types supported by the generator (FR3)."""

    DEPLOYMENT = "deployment"
    INCIDENT = "incident"
    CHANGE = "change"
    BACKUP = "backup"
    SECURITY = "security"


class SOPStatus(str, Enum):
    """SOP lifecycle status."""

    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUIRED = "revision_required"


@dataclass
class SOPSection:
    """Individual section of an SOP (FR2)."""

    title: str
    content: str
    order: int


@dataclass
class GeneratedSOP:
    """Complete generated SOP structure."""

    # Identification
    sop_id: str
    sop_type: SOPType
    version: str = "1.0.0"

    # Metadata
    title: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "AI Agent (Ollama)"
    status: SOPStatus = SOPStatus.DRAFT

    # Content (FR2: 5 mandatory sections)
    purpose: str = ""
    scope: str = ""
    procedure: str = ""
    roles: str = ""
    quality_criteria: str = ""

    # Full markdown content
    markdown_content: str = ""

    # Evidence (FR5, FR6)
    sha256_hash: str = ""
    generation_time_ms: float = 0.0
    ai_model: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "sop_id": self.sop_id,
            "sop_type": self.sop_type.value,
            "version": self.version,
            "title": self.title,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "status": self.status.value,
            "purpose": self.purpose,
            "scope": self.scope,
            "procedure": self.procedure,
            "roles": self.roles,
            "quality_criteria": self.quality_criteria,
            "markdown_content": self.markdown_content,
            "sha256_hash": self.sha256_hash,
            "generation_time_ms": self.generation_time_ms,
            "ai_model": self.ai_model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
        }


@dataclass
class SOPGenerationRequest:
    """Request to generate an SOP."""

    sop_type: SOPType
    workflow_description: str
    additional_context: Optional[str] = None
    requested_by: str = "PM/PO"
    project_id: Optional[str] = None


@dataclass
class MRPEvidence:
    """Merge-Readiness Pack evidence for SOP generation (FR6)."""

    mrp_id: str
    brs_id: str = "BRS-PILOT-001"
    sop_id: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)

    # SOP evidence
    sop_content: str = ""
    sop_type: str = ""
    template_used: str = ""

    # Generation metrics
    generation_time_ms: float = 0.0
    ai_model: str = ""
    ai_provider: str = "ollama"

    # Quality metrics
    sections_present: int = 0
    sections_required: int = 5
    completeness_score: float = 0.0

    # Integrity
    sha256_hash: str = ""

    # Status
    status: str = "pending_review"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "mrp_id": self.mrp_id,
            "brs_id": self.brs_id,
            "sop_id": self.sop_id,
            "created_at": self.created_at.isoformat(),
            "sop_content": self.sop_content,
            "sop_type": self.sop_type,
            "template_used": self.template_used,
            "generation_time_ms": self.generation_time_ms,
            "ai_model": self.ai_model,
            "ai_provider": self.ai_provider,
            "sections_present": self.sections_present,
            "sections_required": self.sections_required,
            "completeness_score": self.completeness_score,
            "sha256_hash": self.sha256_hash,
            "status": self.status,
        }


# ============================================================================
# SOP Templates (5 types per FR3)
# ============================================================================

SOP_TEMPLATES: dict[SOPType, dict[str, Any]] = {
    SOPType.DEPLOYMENT: {
        "name": "Deployment SOP",
        "description": "Application deployment procedures",
        "typical_sections": [
            "Pre-deployment checklist",
            "Deployment steps",
            "Verification steps",
            "Rollback procedure",
        ],
        "prompt_context": """
You are generating a Deployment SOP for application releases.
Focus on:
- Pre-deployment requirements and checks
- Step-by-step deployment procedure
- Post-deployment verification
- Rollback procedure if issues occur
- Approval requirements
""",
    },
    SOPType.INCIDENT: {
        "name": "Incident Response SOP",
        "description": "Incident handling procedures",
        "typical_sections": [
            "Incident classification",
            "Initial response",
            "Escalation matrix",
            "Post-incident review",
        ],
        "prompt_context": """
You are generating an Incident Response SOP.
Focus on:
- Incident classification (P0/P1/P2/P3)
- Initial triage and response steps
- Escalation procedures and contacts
- Communication protocols
- Post-incident review process
""",
    },
    SOPType.CHANGE: {
        "name": "Change Management SOP",
        "description": "Change request procedures",
        "typical_sections": [
            "Change request form",
            "Impact assessment",
            "Approval workflow",
            "Implementation steps",
        ],
        "prompt_context": """
You are generating a Change Management SOP.
Focus on:
- Change request initiation process
- Impact and risk assessment
- Approval workflow (CAB if needed)
- Implementation and testing
- Documentation requirements
""",
    },
    SOPType.BACKUP: {
        "name": "Backup and Recovery SOP",
        "description": "Backup and recovery procedures",
        "typical_sections": [
            "Backup schedule",
            "Backup verification",
            "Recovery procedure",
            "Testing schedule",
        ],
        "prompt_context": """
You are generating a Backup and Recovery SOP.
Focus on:
- Backup schedules (daily, weekly, monthly)
- Data retention policies
- Backup verification procedures
- Recovery steps for different scenarios
- Regular testing requirements
""",
    },
    SOPType.SECURITY: {
        "name": "Security SOP",
        "description": "Security procedures",
        "typical_sections": [
            "Access control",
            "Incident reporting",
            "Vulnerability management",
            "Compliance checks",
        ],
        "prompt_context": """
You are generating a Security SOP.
Focus on:
- Access control and authentication
- Security incident reporting
- Vulnerability scanning and patching
- Compliance requirements (ISO 27001, SOC 2)
- Security awareness training
""",
    },
}


# ============================================================================
# SOP Generator Service
# ============================================================================


class SOPGeneratorService:
    """
    AI-Assisted SOP Generator Service.

    Generates Standard Operating Procedures using Ollama AI,
    following SASE Level 1 workflow (BRS → MRP → VCR).

    BRS Reference: BRS-PILOT-001
    """

    def __init__(
        self,
        ollama_base_url: str = "http://localhost:11434",
        ollama_model: str = "llama2:13b",
        timeout: int = 30,
    ):
        """
        Initialize SOP Generator Service.

        Args:
            ollama_base_url: Ollama API endpoint
            ollama_model: Model to use for generation
            timeout: Request timeout in seconds (NFR1: <30s)
        """
        self.ollama_base_url = ollama_base_url
        self.ollama_model = ollama_model
        self.timeout = timeout
        self._session = None

        logger.info(
            f"SOPGeneratorService initialized: model={ollama_model}, "
            f"timeout={timeout}s"
        )

    def _get_session(self):
        """Get or create HTTP session."""
        if self._session is None:
            import requests

            self._session = requests.Session()
        return self._session

    def _generate_sop_id(self, sop_type: SOPType) -> str:
        """Generate unique SOP ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        short_uuid = str(uuid4())[:8]
        return f"SOP-{sop_type.value.upper()}-{timestamp}-{short_uuid}"

    def _generate_mrp_id(self) -> str:
        """Generate unique MRP ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        short_uuid = str(uuid4())[:8]
        return f"MRP-PILOT-{timestamp}-{short_uuid}"

    def _compute_sha256(self, content: str) -> str:
        """Compute SHA256 hash of content (FR5)."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _build_prompt(
        self, sop_type: SOPType, workflow_description: str, additional_context: Optional[str] = None
    ) -> str:
        """
        Build the AI prompt for SOP generation.

        Args:
            sop_type: Type of SOP to generate
            workflow_description: User's workflow description
            additional_context: Optional additional context

        Returns:
            Complete prompt string
        """
        template = SOP_TEMPLATES[sop_type]

        prompt = f"""
{template["prompt_context"]}

Generate a complete Standard Operating Procedure (SOP) in Markdown format.

WORKFLOW DESCRIPTION:
{workflow_description}

{"ADDITIONAL CONTEXT:" + chr(10) + additional_context if additional_context else ""}

REQUIRED SOP STRUCTURE (ISO 9001 compliant):

# SOP: [Title based on workflow]

## Document Control
- **Document ID:** SOP-{sop_type.value.upper()}-[NUMBER]
- **Version:** 1.0.0
- **Effective Date:** [Today's Date]
- **Owner:** [Appropriate Role]
- **Approver:** [Appropriate Role]

## 1. Purpose
[2-3 sentences explaining what this SOP covers and why it's important]

## 2. Scope
- [What systems/processes are covered]
- [What is explicitly excluded]

## 3. Procedure
[Numbered step-by-step instructions with clear, actionable language]

## 4. Roles and Responsibilities
| Role | Responsibility | RACI |
|------|----------------|------|
| [Role] | [Description] | R/A/C/I |

## 5. Quality Criteria
- [ ] [Checklist item 1]
- [ ] [Checklist item 2]
- [ ] [How to verify procedure was followed correctly]

## Revision History
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | [Date] | AI Agent | Initial version |

Generate a complete, professional SOP following this exact structure.
Ensure all sections are filled with relevant, specific content.
Do not use placeholder text like "[TBD]" or "[TODO]".
"""
        return prompt

    def _call_ollama(self, prompt: str) -> tuple[str, dict[str, Any]]:
        """
        Call Ollama API for SOP generation.

        Args:
            prompt: The prompt to send to Ollama

        Returns:
            Tuple of (generated_text, metrics)

        Raises:
            Exception: If Ollama call fails
        """
        import requests

        url = f"{self.ollama_base_url}/api/generate"

        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": 2000,
            },
        }

        start_time = time.time()

        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()

            result = response.json()
            generation_time = (time.time() - start_time) * 1000  # ms

            metrics = {
                "generation_time_ms": generation_time,
                "model": result.get("model", self.ollama_model),
                "prompt_tokens": result.get("prompt_eval_count", 0),
                "completion_tokens": result.get("eval_count", 0),
                "total_duration_ns": result.get("total_duration", 0),
            }

            generated_text = result.get("response", "")

            logger.info(
                f"Ollama generation complete: {metrics['generation_time_ms']:.0f}ms, "
                f"tokens={metrics['completion_tokens']}"
            )

            return generated_text, metrics

        except requests.exceptions.Timeout:
            logger.error(f"Ollama timeout after {self.timeout}s")
            raise Exception(f"SOP generation timeout (>{self.timeout}s)")

        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to Ollama at {self.ollama_base_url}")
            raise Exception(f"Cannot connect to Ollama at {self.ollama_base_url}")

        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise

    def _parse_sop_sections(self, markdown_content: str) -> dict[str, str]:
        """
        Parse SOP markdown to extract sections (FR2 validation).

        Args:
            markdown_content: Generated markdown content

        Returns:
            Dictionary of section names to content
        """
        sections = {
            "purpose": "",
            "scope": "",
            "procedure": "",
            "roles": "",
            "quality_criteria": "",
        }

        # Simple section extraction based on headers
        current_section = None
        current_content = []

        for line in markdown_content.split("\n"):
            line_lower = line.lower()

            if "## 1. purpose" in line_lower or "## purpose" in line_lower:
                if current_section and current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = "purpose"
                current_content = []
            elif "## 2. scope" in line_lower or "## scope" in line_lower:
                if current_section and current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = "scope"
                current_content = []
            elif "## 3. procedure" in line_lower or "## procedure" in line_lower:
                if current_section and current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = "procedure"
                current_content = []
            elif "## 4. roles" in line_lower or "## roles" in line_lower:
                if current_section and current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = "roles"
                current_content = []
            elif "## 5. quality" in line_lower or "## quality" in line_lower:
                if current_section and current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = "quality_criteria"
                current_content = []
            elif line.startswith("## ") and current_section:
                # New section starts, save current
                if current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = None
                current_content = []
            elif current_section:
                current_content.append(line)

        # Save last section
        if current_section and current_content:
            sections[current_section] = "\n".join(current_content).strip()

        return sections

    def _calculate_completeness(self, sections: dict[str, str]) -> tuple[int, float]:
        """
        Calculate section completeness (FR2 validation).

        Args:
            sections: Dictionary of section content

        Returns:
            Tuple of (sections_present, completeness_score)
        """
        required_sections = ["purpose", "scope", "procedure", "roles", "quality_criteria"]
        present = sum(1 for s in required_sections if sections.get(s, "").strip())
        score = (present / len(required_sections)) * 100

        return present, score

    async def generate_sop(
        self, request: SOPGenerationRequest
    ) -> tuple[GeneratedSOP, MRPEvidence]:
        """
        Generate an SOP from workflow description (FR1).

        This is the main entry point for SOP generation.
        Returns both the generated SOP and MRP evidence (FR6).

        Args:
            request: SOP generation request

        Returns:
            Tuple of (GeneratedSOP, MRPEvidence)

        Raises:
            Exception: If generation fails
        """
        logger.info(
            f"Generating SOP: type={request.sop_type.value}, "
            f"description_length={len(request.workflow_description)}"
        )

        # Generate IDs
        sop_id = self._generate_sop_id(request.sop_type)
        mrp_id = self._generate_mrp_id()

        # Build prompt
        prompt = self._build_prompt(
            request.sop_type,
            request.workflow_description,
            request.additional_context,
        )

        # Call Ollama for generation
        try:
            generated_text, metrics = self._call_ollama(prompt)
        except Exception as e:
            logger.error(f"SOP generation failed: {e}")
            raise

        # Parse sections
        sections = self._parse_sop_sections(generated_text)
        sections_present, completeness_score = self._calculate_completeness(sections)

        # Compute hash (FR5)
        sha256_hash = self._compute_sha256(generated_text)

        # Extract title from generated content
        title = f"{SOP_TEMPLATES[request.sop_type]['name']}"
        for line in generated_text.split("\n"):
            if line.startswith("# SOP:"):
                title = line.replace("# SOP:", "").strip()
                break
            elif line.startswith("# ") and not line.startswith("# SOP"):
                title = line.replace("#", "").strip()
                break

        # Create GeneratedSOP
        sop = GeneratedSOP(
            sop_id=sop_id,
            sop_type=request.sop_type,
            title=title,
            purpose=sections.get("purpose", ""),
            scope=sections.get("scope", ""),
            procedure=sections.get("procedure", ""),
            roles=sections.get("roles", ""),
            quality_criteria=sections.get("quality_criteria", ""),
            markdown_content=generated_text,
            sha256_hash=sha256_hash,
            generation_time_ms=metrics["generation_time_ms"],
            ai_model=metrics["model"],
            prompt_tokens=metrics["prompt_tokens"],
            completion_tokens=metrics["completion_tokens"],
        )

        # Create MRP evidence (FR6)
        mrp = MRPEvidence(
            mrp_id=mrp_id,
            sop_id=sop_id,
            sop_content=generated_text,
            sop_type=request.sop_type.value,
            template_used=SOP_TEMPLATES[request.sop_type]["name"],
            generation_time_ms=metrics["generation_time_ms"],
            ai_model=metrics["model"],
            sections_present=sections_present,
            completeness_score=completeness_score,
            sha256_hash=sha256_hash,
        )

        logger.info(
            f"SOP generated: id={sop_id}, completeness={completeness_score:.1f}%, "
            f"time={metrics['generation_time_ms']:.0f}ms"
        )

        return sop, mrp

    def get_supported_types(self) -> list[dict[str, Any]]:
        """
        Get list of supported SOP types (FR3).

        Returns:
            List of SOP type information
        """
        return [
            {
                "type": sop_type.value,
                "name": template["name"],
                "description": template["description"],
                "typical_sections": template["typical_sections"],
            }
            for sop_type, template in SOP_TEMPLATES.items()
        ]


# ============================================================================
# Service Factory
# ============================================================================


def get_sop_generator_service() -> SOPGeneratorService:
    """
    Factory function to create SOP Generator Service.

    Uses settings from app configuration.

    Returns:
        Configured SOPGeneratorService instance
    """
    # NOTE:
    # - Ollama service runs on same host, accessible via localhost:11434
    # - requests requires a fully-qualified URL with scheme.
    # - Default to localhost for pilot, but allow overriding via env (e.g., for production AI-Platform).
    ollama_url = (getattr(settings, "OLLAMA_URL", "") or "").strip()
    if not ollama_url:
        ollama_url = "http://localhost:11434"
    elif not (ollama_url.startswith("http://") or ollama_url.startswith("https://")):
        ollama_url = f"http://{ollama_url}"

    ollama_model = (getattr(settings, "OLLAMA_MODEL", "qwen3:14b") or "qwen3:14b").strip()

    return SOPGeneratorService(
        ollama_base_url=ollama_url,
        ollama_model=ollama_model,
        timeout=30,  # NFR1: <30s
    )
