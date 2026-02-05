"""
Spec Converter API Routes
Sprint 154 Day 3 - TDD Phase 2 (GREEN)

API endpoints for specification format conversion.

Endpoints:
- POST /parse - Parse content to IR
- POST /render - Render IR to format
- POST /convert - Convert between formats
- POST /detect - Detect format of content

Architecture: ADR-050 API Layer
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.spec_converter.models import SpecFormat, SpecIR, SpecRequirement, AcceptanceCriterion
from app.services.spec_converter.spec_converter_service import SpecConverterService
from app.services.spec_converter.import_service import (
    SpecImportService,
    ImportSource,
    ImportResult,
)


router = APIRouter(prefix="/spec-converter", tags=["spec-converter"])

# Initialize services
_service = SpecConverterService()
_import_service = SpecImportService()


# ============================================================================
# Request/Response Schemas
# ============================================================================


class ParseRequest(BaseModel):
    """Request to parse content to IR."""

    content: str = Field(..., description="Raw specification content")
    source_format: str = Field(..., description="Source format: BDD, OPENSPEC, USER_STORY")


class ParseResponse(BaseModel):
    """Parsed specification as IR."""

    spec_id: str
    title: str
    version: str
    status: str
    tier: List[str]
    owner: str
    last_updated: str
    tags: List[str]
    related_adrs: List[str]
    related_specs: List[str]
    requirements: List[Dict[str, Any]]
    acceptance_criteria: List[Dict[str, Any]]


class IRInput(BaseModel):
    """IR input for rendering."""

    spec_id: str
    title: str
    version: str = "1.0.0"
    status: str = "DRAFT"
    tier: List[str] = ["ALL"]
    owner: str = ""
    last_updated: str = ""
    tags: List[str] = []
    related_adrs: List[str] = []
    related_specs: List[str] = []
    requirements: List[Dict[str, Any]] = []
    acceptance_criteria: List[Dict[str, Any]] = []


class RenderRequest(BaseModel):
    """Request to render IR to format."""

    ir: IRInput = Field(..., description="Specification IR")
    target_format: str = Field(..., description="Target format: BDD, OPENSPEC")


class RenderResponse(BaseModel):
    """Rendered specification content."""

    content: str = Field(..., description="Rendered specification content")
    format: str = Field(..., description="Output format")


class ConvertRequest(BaseModel):
    """Request to convert between formats."""

    content: str = Field(..., description="Raw specification content")
    source_format: str = Field(..., description="Source format")
    target_format: str = Field(..., description="Target format")


class ConvertResponse(BaseModel):
    """Converted specification content."""

    content: str = Field(..., description="Converted content")
    source_format: str
    target_format: str


class DetectRequest(BaseModel):
    """Request to detect format."""

    content: str = Field(..., description="Content to analyze")


class DetectResponse(BaseModel):
    """Detected format result."""

    format: Optional[str] = Field(..., description="Detected format or null")
    confidence: float = Field(default=1.0, description="Detection confidence 0-1")


class ImportFromJiraRequest(BaseModel):
    """Request to import from Jira."""

    issue_key: str = Field(..., description="Jira issue key (e.g., PROJ-123)")
    jira_url: Optional[str] = Field(None, description="Jira instance URL")
    api_token: Optional[str] = Field(None, description="Jira API token")


class ImportFromLinearRequest(BaseModel):
    """Request to import from Linear."""

    issue_id: str = Field(..., description="Linear issue ID")
    api_key: Optional[str] = Field(None, description="Linear API key")


class ImportFromTextRequest(BaseModel):
    """Request to import from plain text."""

    content: str = Field(..., description="Text content to import")
    title: Optional[str] = Field(None, description="Optional title for the spec")


class ImportResponse(BaseModel):
    """Import operation result."""

    success: bool = Field(..., description="Whether import succeeded")
    spec_ir: Optional[Dict[str, Any]] = Field(None, description="Imported SpecIR")
    source: str = Field(..., description="Import source (jira, linear, text)")
    source_id: Optional[str] = Field(None, description="Source identifier")
    error: Optional[str] = Field(None, description="Error message if failed")
    warnings: List[str] = Field(default=[], description="Warning messages")


# ============================================================================
# Helper Functions
# ============================================================================


def _get_format_enum(format_str: str) -> SpecFormat:
    """Convert string to SpecFormat enum."""
    format_map = {
        "BDD": SpecFormat.BDD,
        "GHERKIN": SpecFormat.BDD,
        "OPENSPEC": SpecFormat.OPENSPEC,
        "YAML": SpecFormat.OPENSPEC,
        "USER_STORY": SpecFormat.USER_STORY,
        "USERSTORY": SpecFormat.USER_STORY,
        "NATURAL_LANGUAGE": SpecFormat.NATURAL_LANGUAGE,
    }
    upper_format = format_str.upper()
    if upper_format not in format_map:
        raise ValueError(f"Unsupported format: {format_str}")
    return format_map[upper_format]


def _ir_to_dict(ir: SpecIR) -> Dict[str, Any]:
    """Convert SpecIR to dictionary."""
    return {
        "spec_id": ir.spec_id,
        "title": ir.title,
        "version": ir.version,
        "status": ir.status,
        "tier": ir.tier,
        "owner": ir.owner,
        "last_updated": ir.last_updated,
        "tags": ir.tags,
        "related_adrs": ir.related_adrs,
        "related_specs": ir.related_specs,
        "requirements": [
            {
                "id": r.id,
                "title": r.title,
                "priority": r.priority,
                "tier": r.tier,
                "given": r.given,
                "when": r.when,
                "then": r.then,
                "user_story": r.user_story,
                "acceptance_criteria": r.acceptance_criteria,
            }
            for r in ir.requirements
        ],
        "acceptance_criteria": [
            {
                "id": ac.id,
                "scenario": ac.scenario,
                "given": ac.given,
                "when": ac.when,
                "then": ac.then,
                "tier": ac.tier,
                "testable": ac.testable,
            }
            for ac in ir.acceptance_criteria
        ],
    }


def _dict_to_ir(data: IRInput) -> SpecIR:
    """Convert dictionary to SpecIR."""
    requirements = []
    for r in data.requirements:
        requirements.append(
            SpecRequirement(
                id=r.get("id", "REQ-001"),
                title=r.get("title", "Untitled"),
                priority=r.get("priority", "P1"),
                tier=r.get("tier", ["ALL"]),
                given=r.get("given", ""),
                when=r.get("when", ""),
                then=r.get("then", ""),
                user_story=r.get("user_story"),
                acceptance_criteria=r.get("acceptance_criteria", []),
            )
        )

    acceptance_criteria = []
    for ac in data.acceptance_criteria:
        acceptance_criteria.append(
            AcceptanceCriterion(
                id=ac.get("id", "AC-001"),
                scenario=ac.get("scenario", ""),
                given=ac.get("given", ""),
                when=ac.get("when", ""),
                then=ac.get("then", ""),
                tier=ac.get("tier", ["ALL"]),
                testable=ac.get("testable", True),
            )
        )

    return SpecIR(
        spec_id=data.spec_id,
        title=data.title,
        version=data.version,
        status=data.status,
        tier=data.tier,
        owner=data.owner,
        last_updated=data.last_updated,
        tags=data.tags,
        related_adrs=data.related_adrs,
        related_specs=data.related_specs,
        requirements=requirements,
        acceptance_criteria=acceptance_criteria,
    )


# ============================================================================
# API Endpoints
# ============================================================================


@router.post("/parse", response_model=ParseResponse)
async def parse_specification(request: ParseRequest) -> Dict[str, Any]:
    """
    Parse specification content to Intermediate Representation.

    Supports:
    - BDD/Gherkin feature files
    - OpenSpec YAML specifications
    - User Stories

    Args:
        request: ParseRequest with content and source_format

    Returns:
        Parsed SpecIR as dictionary
    """
    # Validate content
    if not request.content or not request.content.strip():
        raise HTTPException(status_code=400, detail="Content cannot be empty")

    # Validate format
    try:
        source_format = _get_format_enum(request.source_format)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Parse content
    try:
        ir = await _service.parse(request.content, source_format)
        return _ir_to_dict(ir)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parse error: {str(e)}")


@router.post("/render", response_model=RenderResponse)
async def render_specification(request: RenderRequest) -> RenderResponse:
    """
    Render Intermediate Representation to target format.

    Supports:
    - BDD/Gherkin feature files
    - OpenSpec YAML specifications

    Args:
        request: RenderRequest with IR and target_format

    Returns:
        Rendered content string
    """
    # Validate format
    try:
        target_format = _get_format_enum(request.target_format)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Convert input to SpecIR
    ir = _dict_to_ir(request.ir)

    # Render using appropriate renderer
    from app.services.spec_converter.renderers import GherkinRenderer, OpenSpecRenderer

    try:
        if target_format == SpecFormat.BDD:
            renderer = GherkinRenderer()
            content = await renderer.render(ir)
        elif target_format == SpecFormat.OPENSPEC:
            renderer = OpenSpecRenderer()
            content = await renderer.render(ir)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Rendering to {request.target_format} not supported",
            )

        return RenderResponse(content=content, format=request.target_format)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Render error: {str(e)}")


@router.post("/convert", response_model=ConvertResponse)
async def convert_specification(request: ConvertRequest) -> ConvertResponse:
    """
    Convert specification from one format to another.

    Supports:
    - BDD → OpenSpec
    - OpenSpec → BDD
    - User Story → BDD
    - User Story → OpenSpec

    Args:
        request: ConvertRequest with content, source_format, target_format

    Returns:
        Converted content
    """
    # Validate content
    if not request.content or not request.content.strip():
        raise HTTPException(status_code=400, detail="Content cannot be empty")

    # Validate formats
    try:
        source_format = _get_format_enum(request.source_format)
        target_format = _get_format_enum(request.target_format)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        # Parse to IR
        ir = await _service.parse(request.content, source_format)

        # Render to target format
        from app.services.spec_converter.renderers import GherkinRenderer, OpenSpecRenderer

        if target_format == SpecFormat.BDD:
            renderer = GherkinRenderer()
            content = await renderer.render(ir)
        elif target_format == SpecFormat.OPENSPEC:
            renderer = OpenSpecRenderer()
            content = await renderer.render(ir)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Conversion to {request.target_format} not supported",
            )

        return ConvertResponse(
            content=content,
            source_format=request.source_format,
            target_format=request.target_format,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Conversion error: {str(e)}")


@router.post("/detect", response_model=DetectResponse)
async def detect_format(request: DetectRequest) -> DetectResponse:
    """
    Auto-detect specification format from content.

    Analyzes content structure to identify format:
    - BDD: Contains Feature/Scenario/Given/When/Then
    - OpenSpec: Starts with YAML frontmatter (---)
    - User Story: Contains "As a... I want... So that..."

    Args:
        request: DetectRequest with content

    Returns:
        Detected format or null if unknown
    """
    detected = await _service.detect_format(request.content)

    if detected is None:
        return DetectResponse(format=None, confidence=0.0)

    format_name = detected.value.upper()
    return DetectResponse(format=format_name, confidence=1.0)


# ============================================================================
# Import Endpoints
# ============================================================================


@router.post("/import/jira", response_model=ImportResponse)
async def import_from_jira(request: ImportFromJiraRequest) -> ImportResponse:
    """
    Import specification from Jira issue.

    Fetches a Jira issue and converts it to SpecIR format.
    Extracts:
    - Summary → Title
    - Description → Requirements
    - Acceptance Criteria → BDD format
    - Labels → Tags
    - Priority → Requirement priority

    Args:
        request: ImportFromJiraRequest with issue_key and optional credentials

    Returns:
        ImportResponse with parsed SpecIR or error
    """
    result = await _import_service.import_from_jira(
        issue_key=request.issue_key,
        jira_url=request.jira_url,
        api_token=request.api_token,
    )

    return ImportResponse(
        success=result.success,
        spec_ir=_ir_to_dict(result.spec_ir) if result.spec_ir else None,
        source=result.source.value,
        source_id=result.source_id,
        error=result.error,
        warnings=result.warnings,
    )


@router.post("/import/linear", response_model=ImportResponse)
async def import_from_linear(request: ImportFromLinearRequest) -> ImportResponse:
    """
    Import specification from Linear issue.

    Fetches a Linear issue and converts it to SpecIR format.
    Extracts:
    - Title → Title
    - Description → Requirements
    - Labels → Tags
    - Priority → Requirement priority
    - State → Status

    Args:
        request: ImportFromLinearRequest with issue_id and optional API key

    Returns:
        ImportResponse with parsed SpecIR or error
    """
    result = await _import_service.import_from_linear(
        issue_id=request.issue_id,
        api_key=request.api_key,
    )

    return ImportResponse(
        success=result.success,
        spec_ir=_ir_to_dict(result.spec_ir) if result.spec_ir else None,
        source=result.source.value,
        source_id=result.source_id,
        error=result.error,
        warnings=result.warnings,
    )


@router.post("/import/text", response_model=ImportResponse)
async def import_from_text(request: ImportFromTextRequest) -> ImportResponse:
    """
    Import specification from plain text or markdown.

    Automatically detects and parses:
    - User Stories: "As a... I want... So that..."
    - BDD/Gherkin: Feature/Scenario blocks
    - Plain text: Converts to basic requirement

    Args:
        request: ImportFromTextRequest with content and optional title

    Returns:
        ImportResponse with parsed SpecIR
    """
    if not request.content or not request.content.strip():
        return ImportResponse(
            success=False,
            spec_ir=None,
            source=ImportSource.TEXT.value,
            source_id=None,
            error="Content cannot be empty",
            warnings=[],
        )

    result = await _import_service.import_from_text(
        content=request.content,
        title=request.title,
    )

    return ImportResponse(
        success=result.success,
        spec_ir=_ir_to_dict(result.spec_ir) if result.spec_ir else None,
        source=result.source.value,
        source_id=result.source_id,
        error=result.error,
        warnings=result.warnings,
    )
