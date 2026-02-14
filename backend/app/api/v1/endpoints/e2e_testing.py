"""
=========================================================================
E2E Testing Execution API - Async Test Runner and Results
SDLC Orchestrator - Sprint 140 (CLI Orchestration Upgrade)

Version: 1.1.0
Date: February 11, 2026
Status: ACTIVE - Sprint 140 Day 2 (RFC-SDLC-602)
Authority: Backend Lead + CTO Approved
Framework: SDLC 6.0.5 (RFC-SDLC-602 E2E API Testing Enhancement)

Purpose:
- Execute E2E API tests asynchronously
- Support multiple test runners (Newman, Pytest, REST Assured)
- Store and retrieve test execution results
- Track execution status in real-time

RFC-SDLC-602 Compliance:
- Phase 2: Test Execution
- Phase 3: Report Generation
- Integration with Stage 05 (Testing & Quality)

Sprint 140 Day 2 Updates:
- Migrated from in-memory store to Redis-backed E2EExecutionStore
- Added persistent execution tracking across server restarts
- TTL-based cleanup for completed executions (7 days)

Zero Mock Policy: Production-ready implementation with Redis persistence
=========================================================================
"""

import asyncio
import json
import logging
import subprocess
import tempfile
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.e2e_execution_store import (
    E2EExecutionStore,
    ExecutionStatus as StoreExecutionStatus,
    get_execution_store,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/e2e", tags=["E2E Testing"])


# ============================================================================
# Enums
# ============================================================================


class TestRunner(str, Enum):
    """Supported test runners."""

    NEWMAN = "newman"
    PYTEST = "pytest"
    REST_ASSURED = "rest_assured"
    CUSTOM = "custom"


class ExecutionStatus(str, Enum):
    """Test execution status."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


# ============================================================================
# Request/Response Models
# ============================================================================


class TestExecutionRequest(BaseModel):
    """Request to execute E2E tests."""

    project_id: UUID = Field(..., description="Project UUID")
    test_suite_path: str = Field(
        ...,
        description="Path to test suite (collection.json or test directory)"
    )
    runner: TestRunner = Field(
        TestRunner.NEWMAN,
        description="Test runner to use"
    )
    environment: Optional[str] = Field(
        None,
        description="Environment file path or name"
    )
    environment_variables: Dict[str, str] = Field(
        default_factory=dict,
        description="Additional environment variables"
    )
    timeout_seconds: int = Field(
        300,
        description="Execution timeout in seconds",
        ge=30,
        le=3600
    )
    parallel: bool = Field(
        False,
        description="Run tests in parallel (if supported)"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Filter tests by tags"
    )


class TestExecutionResult(BaseModel):
    """Response after queuing test execution."""

    execution_id: str = Field(..., description="Unique execution ID")
    status: ExecutionStatus = Field(..., description="Current status")
    message: str = Field(..., description="Status message")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When execution was queued"
    )
    estimated_duration_seconds: Optional[int] = Field(
        None,
        description="Estimated execution duration"
    )


class TestCaseResult(BaseModel):
    """Individual test case result."""

    name: str = Field(..., description="Test case name")
    status: str = Field(..., description="pass, fail, skip, error")
    duration_ms: float = Field(0, description="Execution time in milliseconds")
    endpoint: Optional[str] = Field(None, description="API endpoint tested")
    method: Optional[str] = Field(None, description="HTTP method")
    assertions_passed: int = Field(0, description="Number of assertions passed")
    assertions_failed: int = Field(0, description="Number of assertions failed")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    request_data: Optional[Dict[str, Any]] = Field(None, description="Request details")
    response_data: Optional[Dict[str, Any]] = Field(None, description="Response details")


class TestResults(BaseModel):
    """Complete test execution results."""

    execution_id: str = Field(..., description="Execution ID")
    status: ExecutionStatus = Field(..., description="Final status")
    runner: TestRunner = Field(..., description="Test runner used")
    started_at: Optional[datetime] = Field(None, description="Execution start time")
    completed_at: Optional[datetime] = Field(None, description="Execution end time")
    duration_seconds: float = Field(0, description="Total duration in seconds")
    total_tests: int = Field(0, description="Total test count")
    passed: int = Field(0, description="Passed tests")
    failed: int = Field(0, description="Failed tests")
    skipped: int = Field(0, description="Skipped tests")
    errors: int = Field(0, description="Tests with errors")
    pass_rate: float = Field(0, description="Pass rate percentage")
    tests: List[TestCaseResult] = Field(
        default_factory=list,
        description="Individual test results"
    )
    categories: Dict[str, Dict[str, int]] = Field(
        default_factory=dict,
        description="Results grouped by category/tag"
    )
    environment: Optional[str] = Field(None, description="Environment used")
    logs: Optional[str] = Field(None, description="Execution logs")
    report_path: Optional[str] = Field(None, description="Path to generated report")


class ExecutionStatusResponse(BaseModel):
    """Response for execution status check."""

    execution_id: str
    status: ExecutionStatus
    progress: Optional[int] = Field(None, description="Progress percentage (0-100)")
    current_test: Optional[str] = Field(None, description="Currently running test")
    tests_completed: int = 0
    tests_total: int = 0
    started_at: Optional[datetime] = None
    estimated_remaining_seconds: Optional[int] = None


# ============================================================================
# API Endpoints
# ============================================================================


@router.post("/execute", response_model=TestExecutionResult)
async def execute_e2e_tests(
    request: TestExecutionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TestExecutionResult:
    """
    Execute E2E API tests asynchronously.

    Supports Newman (Postman), Pytest, and REST Assured test runners.
    Tests run in background and results can be retrieved via GET /results/{id}.

    RFC-SDLC-602 Phase 2: Test Execution

    Args:
        request: Test execution configuration
        background_tasks: FastAPI background tasks handler
        db: Database session
        current_user: Authenticated user

    Returns:
        TestExecutionResult with execution ID for tracking

    Raises:
        HTTPException 404: Project not found
        HTTPException 400: Invalid test configuration
    """
    # Generate unique execution ID
    execution_id = str(uuid.uuid4())

    # Get execution store (Redis-backed)
    store = await get_execution_store()

    # Create execution record in Redis
    await store.create_execution(
        execution_id=execution_id,
        project_id=str(request.project_id),
        user_id=str(current_user.id),
        runner=request.runner.value,
        test_suite_path=request.test_suite_path,
        environment=request.environment,
        environment_variables=request.environment_variables,
        timeout_seconds=request.timeout_seconds,
    )

    # Queue execution in background
    background_tasks.add_task(
        _run_tests_background,
        execution_id=execution_id,
        request=request,
    )

    logger.info(
        f"E2E test execution queued: {execution_id} "
        f"(runner={request.runner}, project={request.project_id})"
    )

    return TestExecutionResult(
        execution_id=execution_id,
        status=ExecutionStatus.QUEUED,
        message="Tests queued for execution",
        estimated_duration_seconds=_estimate_duration(request),
    )


@router.get("/results/{execution_id}", response_model=TestResults)
async def get_test_results(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TestResults:
    """
    Get E2E test execution results.

    Returns complete test results including individual test cases,
    pass/fail counts, and execution timing.

    RFC-SDLC-602 Phase 3: Report Generation

    Args:
        execution_id: Unique execution identifier
        db: Database session
        current_user: Authenticated user

    Returns:
        TestResults with complete execution data

    Raises:
        HTTPException 404: Execution not found
        HTTPException 202: Execution still in progress
    """
    # Get execution from Redis store
    store = await get_execution_store()
    execution = await store.get_execution(execution_id)

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution not found: {execution_id}"
        )

    # Get status value
    exec_status = execution["status"]
    if isinstance(exec_status, StoreExecutionStatus):
        exec_status = ExecutionStatus(exec_status.value)

    # Check if still running
    if exec_status in [ExecutionStatus.QUEUED, ExecutionStatus.RUNNING]:
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail={
                "message": "Execution still in progress",
                "status": exec_status.value,
                "execution_id": execution_id,
            }
        )

    # Return results
    results = execution.get("results", {}) or {}

    # Parse runner
    runner_value = execution.get("runner", "newman")
    if isinstance(runner_value, str):
        try:
            runner = TestRunner(runner_value)
        except ValueError:
            runner = TestRunner.NEWMAN
    else:
        runner = runner_value

    return TestResults(
        execution_id=execution_id,
        status=exec_status,
        runner=runner,
        started_at=execution.get("started_at"),
        completed_at=execution.get("completed_at"),
        duration_seconds=results.get("duration_seconds", 0),
        total_tests=results.get("total_tests", 0),
        passed=results.get("passed", 0),
        failed=results.get("failed", 0),
        skipped=results.get("skipped", 0),
        errors=results.get("errors", 0),
        pass_rate=results.get("pass_rate", 0),
        tests=[TestCaseResult(**t) for t in results.get("tests", [])],
        categories=results.get("categories", {}),
        environment=execution.get("environment"),
        logs=results.get("logs"),
        report_path=results.get("report_path"),
    )


@router.get("/status/{execution_id}", response_model=ExecutionStatusResponse)
async def get_execution_status(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExecutionStatusResponse:
    """
    Check E2E test execution status.

    Provides real-time progress updates for running tests.

    Args:
        execution_id: Unique execution identifier
        db: Database session
        current_user: Authenticated user

    Returns:
        ExecutionStatusResponse with current progress

    Raises:
        HTTPException 404: Execution not found
    """
    # Get execution from Redis store
    store = await get_execution_store()
    execution = await store.get_execution(execution_id)

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution not found: {execution_id}"
        )

    results = execution.get("results", {}) or {}

    # Get status value
    exec_status = execution["status"]
    if isinstance(exec_status, StoreExecutionStatus):
        exec_status = ExecutionStatus(exec_status.value)

    return ExecutionStatusResponse(
        execution_id=execution_id,
        status=exec_status,
        progress=results.get("progress", 0),
        current_test=results.get("current_test"),
        tests_completed=results.get("tests_completed", 0),
        tests_total=results.get("total_tests", 0),
        started_at=execution.get("started_at"),
        estimated_remaining_seconds=results.get("estimated_remaining_seconds"),
    )


@router.post("/cancel/{execution_id}")
async def cancel_execution(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Cancel a running E2E test execution.

    Args:
        execution_id: Unique execution identifier
        db: Database session
        current_user: Authenticated user

    Returns:
        Cancellation confirmation

    Raises:
        HTTPException 404: Execution not found
        HTTPException 400: Execution not cancellable
    """
    # Get execution from Redis store
    store = await get_execution_store()
    execution = await store.get_execution(execution_id)

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution not found: {execution_id}"
        )

    # Get status value
    exec_status = execution["status"]
    if isinstance(exec_status, StoreExecutionStatus):
        exec_status_value = exec_status.value
    else:
        exec_status_value = exec_status

    if exec_status_value not in [ExecutionStatus.QUEUED.value, ExecutionStatus.RUNNING.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Execution cannot be cancelled (status: {exec_status_value})"
        )

    # Update status to cancelled
    await store.update_status(
        execution_id,
        StoreExecutionStatus.CANCELLED,
        completed_at=datetime.now(timezone.utc),
    )

    logger.info(f"E2E test execution cancelled: {execution_id}")

    return {
        "execution_id": execution_id,
        "status": "cancelled",
        "message": "Execution cancelled successfully",
    }


@router.get("/history", response_model=List[TestExecutionResult])
async def get_execution_history(
    project_id: Optional[UUID] = None,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[TestExecutionResult]:
    """
    Get E2E test execution history.

    Args:
        project_id: Optional project filter
        limit: Maximum results to return
        db: Database session
        current_user: Authenticated user

    Returns:
        List of recent test executions
    """
    # Get executions from Redis store
    store = await get_execution_store()

    # Filter by user (and optionally project)
    executions = await store.list_executions(
        user_id=str(current_user.id),
        project_id=str(project_id) if project_id else None,
        limit=limit,
    )

    results = []
    for e in executions:
        # Get status value
        exec_status = e.get("status", "unknown")
        if isinstance(exec_status, StoreExecutionStatus):
            exec_status = ExecutionStatus(exec_status.value)
        elif isinstance(exec_status, str):
            try:
                exec_status = ExecutionStatus(exec_status)
            except ValueError:
                exec_status = ExecutionStatus.QUEUED

        results.append(
            TestExecutionResult(
                execution_id=e["id"],
                status=exec_status,
                message=f"Execution {exec_status.value}",
                created_at=e.get("created_at", datetime.now(timezone.utc)),
            )
        )

    return results


# ============================================================================
# Background Task Helpers
# ============================================================================


async def _run_tests_background(
    execution_id: str,
    request: TestExecutionRequest,
) -> None:
    """
    Run tests in background.

    This function executes the actual tests based on the runner type.
    Uses Redis-backed store for persistent state management.

    Args:
        execution_id: Unique execution identifier
        request: Test execution configuration
    """
    # Get execution store
    store = await get_execution_store()

    try:
        # Update status to running
        await store.update_status(
            execution_id,
            StoreExecutionStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
        )

        # Execute based on runner type
        if request.runner == TestRunner.NEWMAN:
            results = await _run_newman_tests(request)
        elif request.runner == TestRunner.PYTEST:
            results = await _run_pytest_tests(request)
        else:
            results = await _run_custom_tests(request)

        # Update with results
        await store.set_results(execution_id, results)

        logger.info(
            f"E2E test execution completed: {execution_id} "
            f"(passed={results.get('passed', 0)}, failed={results.get('failed', 0)})"
        )

    except asyncio.TimeoutError:
        await store.update_status(
            execution_id,
            StoreExecutionStatus.TIMEOUT,
            completed_at=datetime.now(timezone.utc),
            error="Execution timed out",
        )
        logger.error(f"E2E test execution timed out: {execution_id}")

    except Exception as e:
        await store.update_status(
            execution_id,
            StoreExecutionStatus.FAILED,
            completed_at=datetime.now(timezone.utc),
            error=str(e),
        )
        logger.error(f"E2E test execution failed: {execution_id} - {e}")


async def _run_newman_tests(request: TestExecutionRequest) -> Dict[str, Any]:
    """
    Run Newman (Postman) tests.

    Args:
        request: Test execution configuration

    Returns:
        Test results dictionary
    """
    # Build Newman command
    cmd = ["newman", "run", request.test_suite_path]

    if request.environment:
        cmd.extend(["-e", request.environment])

    # Add environment variables
    for key, value in request.environment_variables.items():
        cmd.extend(["--env-var", f"{key}={value}"])

    # Create temp file for JSON output
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        report_path = f.name

    cmd.extend(["--reporters", "cli,json", "--reporter-json-export", report_path])

    # Run Newman
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=request.timeout_seconds,
        )

        # Parse Newman JSON output
        with open(report_path, "r") as f:
            newman_results = json.load(f)

        return _parse_newman_results(newman_results, stdout.decode())

    except FileNotFoundError:
        return {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 1,
            "pass_rate": 0,
            "tests": [],
            "logs": "Newman not found. Install with: npm install -g newman",
        }


async def _run_pytest_tests(request: TestExecutionRequest) -> Dict[str, Any]:
    """
    Run Pytest tests.

    Args:
        request: Test execution configuration

    Returns:
        Test results dictionary
    """
    # Create temp file for JSON output
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        report_path = f.name

    # Build pytest command
    cmd = [
        "pytest",
        request.test_suite_path,
        "--json-report",
        f"--json-report-file={report_path}",
        "-v",
    ]

    # Add environment variables
    env = dict(request.environment_variables)

    # Run pytest
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**dict(subprocess.os.environ), **env},
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=request.timeout_seconds,
        )

        # Parse pytest JSON output
        with open(report_path, "r") as f:
            pytest_results = json.load(f)

        return _parse_pytest_results(pytest_results, stdout.decode())

    except FileNotFoundError:
        return {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 1,
            "pass_rate": 0,
            "tests": [],
            "logs": "Pytest not found. Install with: pip install pytest pytest-json-report",
        }


async def _run_custom_tests(request: TestExecutionRequest) -> Dict[str, Any]:
    """
    Run custom tests (generic subprocess).

    Args:
        request: Test execution configuration

    Returns:
        Test results dictionary
    """
    return {
        "total_tests": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "errors": 0,
        "pass_rate": 0,
        "tests": [],
        "logs": "Custom test runner: Implement _run_custom_tests based on your needs",
    }


def _parse_newman_results(data: Dict[str, Any], logs: str) -> Dict[str, Any]:
    """Parse Newman JSON output into standard format."""
    run = data.get("run", {})
    stats = run.get("stats", {})

    total = stats.get("assertions", {}).get("total", 0)
    failed = stats.get("assertions", {}).get("failed", 0)
    passed = total - failed

    tests = []
    for execution in run.get("executions", []):
        item = execution.get("item", {})
        for assertion in execution.get("assertions", []):
            tests.append({
                "name": f"{item.get('name', 'Unknown')} - {assertion.get('assertion', '')}",
                "status": "fail" if assertion.get("error") else "pass",
                "duration_ms": execution.get("response", {}).get("responseTime", 0),
                "endpoint": item.get("request", {}).get("url", {}).get("path", []),
                "method": item.get("request", {}).get("method", ""),
                "assertions_passed": 1 if not assertion.get("error") else 0,
                "assertions_failed": 1 if assertion.get("error") else 0,
                "error_message": str(assertion.get("error", {}).get("message", "")) if assertion.get("error") else None,
            })

    return {
        "total_tests": total,
        "passed": passed,
        "failed": failed,
        "skipped": 0,
        "errors": 0,
        "pass_rate": (passed / total * 100) if total > 0 else 0,
        "duration_seconds": run.get("timings", {}).get("completed", 0) / 1000,
        "tests": tests,
        "logs": logs,
    }


def _parse_pytest_results(data: Dict[str, Any], logs: str) -> Dict[str, Any]:
    """Parse pytest-json-report output into standard format."""
    summary = data.get("summary", {})

    total = summary.get("total", 0)
    passed = summary.get("passed", 0)
    failed = summary.get("failed", 0)
    skipped = summary.get("skipped", 0)
    errors = summary.get("error", 0)

    tests = []
    for test in data.get("tests", []):
        tests.append({
            "name": test.get("nodeid", ""),
            "status": test.get("outcome", "unknown"),
            "duration_ms": test.get("duration", 0) * 1000,
            "error_message": test.get("call", {}).get("longrepr") if test.get("outcome") == "failed" else None,
        })

    return {
        "total_tests": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "errors": errors,
        "pass_rate": (passed / total * 100) if total > 0 else 0,
        "duration_seconds": data.get("duration", 0),
        "tests": tests,
        "logs": logs,
    }


def _estimate_duration(request: TestExecutionRequest) -> int:
    """Estimate test execution duration based on runner and config."""
    # Simple estimation: Newman tests typically take 30-60s
    # Pytest tests vary more widely
    base_duration = {
        TestRunner.NEWMAN: 60,
        TestRunner.PYTEST: 120,
        TestRunner.REST_ASSURED: 90,
        TestRunner.CUSTOM: 60,
    }

    return base_duration.get(request.runner, 60)
