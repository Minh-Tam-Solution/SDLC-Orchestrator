"""
File: backend/app/api/routes/docs.py
Version: 1.0.0
Status: ACTIVE - STAGE 04 (BUILD)
Date: 2025-12-20
Authority: Backend Lead + CTO Approved
Foundation: SDLC 5.1.1 Complete Lifecycle

Description:
API endpoints for serving user documentation markdown files.
Serves files from docs/07-operate/03-User Support directory.

Security:
- Read-only access to documentation files
- Path traversal prevention
- Only serves .md files from approved directory
"""

from fastapi import APIRouter, HTTPException, Path
from fastapi.responses import PlainTextResponse
import os
from pathlib import Path as PathLib

router = APIRouter(prefix="/docs", tags=["Documentation"])

# Base directory for documentation
# In Docker: docs are mounted at /docs
# Local dev: navigate from backend/ to docs/
DOCS_BASE_DIR = PathLib("/docs") if PathLib("/docs").exists() else PathLib(__file__).parent.parent.parent.parent.parent / "docs"
DOCS_USER_SUPPORT = DOCS_BASE_DIR / "07-operate" / "03-User Support"

# Allowed documentation files
ALLOWED_DOCS = [
    "01-Getting-Started.md",
    "02-SDLC-Framework-Overview.md",
    "03-Platform-Features.md",
    "04-User-Roles-Permissions.md",
    "05-Common-Tasks.md",
    "06-Troubleshooting.md",
    "07-FAQ.md",
    "08-Best-Practices.md",
    "09-Support-Channels.md",
    "10-README.md",
]


@router.get("/user-support/{filename}", response_class=PlainTextResponse)
async def get_user_support_doc(
    filename: str = Path(..., description="Documentation filename (e.g., 01-Getting-Started.md)")
):
    """
    Get user support documentation file content.
    
    Args:
        filename: Name of the markdown file to retrieve
        
    Returns:
        PlainTextResponse: Markdown content of the documentation file
        
    Raises:
        HTTPException: 404 if file not found or not allowed
        HTTPException: 500 if error reading file
    """
    # Security: Only allow specific filenames (prevent path traversal)
    if filename not in ALLOWED_DOCS:
        raise HTTPException(
            status_code=404,
            detail=f"Documentation file '{filename}' not found"
        )
    
    # Construct safe file path
    file_path = DOCS_USER_SUPPORT / filename
    
    # Verify file exists and is within allowed directory
    try:
        # Resolve to absolute path and check it's within DOCS_USER_SUPPORT
        resolved_path = file_path.resolve()
        if not str(resolved_path).startswith(str(DOCS_USER_SUPPORT.resolve())):
            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )
        
        # Read and return file content
        if not resolved_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Documentation file '{filename}' not found"
            )
            
        with open(resolved_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        return PlainTextResponse(content=content, media_type="text/markdown; charset=utf-8")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading documentation file: {str(e)}"
        )


@router.get("/user-support", response_model=list[str])
async def list_user_support_docs():
    """
    List available user support documentation files.
    
    Returns:
        list[str]: List of available documentation filenames
    """
    return ALLOWED_DOCS
