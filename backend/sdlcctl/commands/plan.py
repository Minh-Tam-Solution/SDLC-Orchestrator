"""
=========================================================================
SDLC 5.2.0 Planning Mode CLI Command
SDLC Orchestrator - Sprint 98 (Planning Sub-agent Implementation Part 1)

Version: 1.0.0
Date: January 22, 2026
Status: ACTIVE - Sprint 98 Implementation
Authority: Backend Lead + CTO Approved
Reference: ADR-034-Planning-Subagent-Orchestration
Reference: SDLC 5.2.0 AI Agent Best Practices (Planning Mode)

Purpose:
- Execute planning mode with sub-agent orchestration
- Extract patterns from codebase, ADRs, tests before implementation
- Generate implementation plans for human approval
- Prevent architectural drift (MANDATORY for >15 LOC changes)

Key Insight (Expert Workflow):
- "Agentic grep > RAG for context retrieval"
- Direct codebase exploration finds real patterns
- Planning Mode spawns explore sub-agents → extract patterns → build on them

Commands:
    sdlcctl plan "Add OAuth2 authentication"
    sdlcctl plan "Refactor user service" --depth 5
    sdlcctl plan "Add unit tests" --no-adrs

Zero Mock Policy: 100% real implementation
=========================================================================
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax
from rich.table import Table
from rich.tree import Tree

console = Console()


def plan_command(
    task: str = typer.Argument(
        ...,
        help="Task description (e.g., 'Add OAuth2 authentication with Google provider')",
        min=10,
    ),
    path: Path = typer.Option(
        Path.cwd(),
        "--path",
        "-p",
        help="Project root path",
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    depth: int = typer.Option(
        3,
        "--depth",
        "-d",
        help="Search depth for pattern extraction (1-10)",
        min=1,
        max=10,
    ),
    include_tests: bool = typer.Option(
        True,
        "--tests/--no-tests",
        help="Include test pattern analysis",
    ),
    include_adrs: bool = typer.Option(
        True,
        "--adrs/--no-adrs",
        help="Include ADR analysis",
    ),
    auto_approve: bool = typer.Option(
        False,
        "--auto",
        "-a",
        help="Auto-approve plan without prompting",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Save plan to file (JSON format)",
    ),
    format: str = typer.Option(
        "cli",
        "--format",
        "-f",
        help="Output format: cli, json, markdown",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Minimal output (useful for scripts)",
    ),
) -> None:
    """
    Execute planning mode with sub-agent orchestration.

    Planning Mode is MANDATORY for changes >15 LOC (per ADR-034).
    This command spawns explore sub-agents to extract patterns from:
    - Codebase (similar implementations)
    - ADRs (architectural decisions)
    - Tests (testing patterns and conventions)

    Then generates an implementation plan for human approval.

    Examples:

        sdlcctl plan "Add OAuth2 authentication with Google provider"

        sdlcctl plan "Refactor user service to use repository pattern" --depth 5

        sdlcctl plan "Add unit tests for payment service" --no-adrs

        sdlcctl plan "Implement caching layer" --auto --output plan.json

        sdlcctl plan "Add logging middleware" --format json | jq .
    """
    # Run the async planning
    try:
        asyncio.run(
            _execute_planning(
                task=task,
                project_path=path,
                depth=depth,
                include_tests=include_tests,
                include_adrs=include_adrs,
                auto_approve=auto_approve,
                output=output,
                format=format,
                quiet=quiet,
            )
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Planning cancelled by user.[/yellow]")
        raise typer.Exit(code=130)
    except Exception as e:
        console.print(f"\n[bold red]Planning failed:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


async def _execute_planning(
    task: str,
    project_path: Path,
    depth: int,
    include_tests: bool,
    include_adrs: bool,
    auto_approve: bool,
    output: Optional[Path],
    format: str,
    quiet: bool,
) -> None:
    """
    Execute the planning workflow.

    Args:
        task: Task description
        project_path: Project root path
        depth: Search depth
        include_tests: Include test patterns
        include_adrs: Include ADR analysis
        auto_approve: Skip approval prompt
        output: Output file path
        format: Output format
        quiet: Minimal output
    """
    # Import service here to avoid import issues when CLI loads
    from app.schemas.planning_subagent import PlanningRequest
    from app.services.planning_orchestrator_service import (
        PlanningOrchestratorService,
    )

    # Show header (unless quiet)
    if not quiet:
        console.print()
        console.print(
            Panel(
                "[bold]Planning Mode - Sub-agent Orchestration[/bold]\n\n"
                "Spawning explore sub-agents to extract patterns...\n"
                "Key insight: 'Agentic grep > RAG for context retrieval'\n\n"
                f"[dim]Task: {task[:80]}{'...' if len(task) > 80 else ''}[/dim]",
                title="[bold blue]sdlcctl plan[/bold blue]",
                border_style="blue",
            )
        )

    # Create request
    request = PlanningRequest(
        task=task,
        project_path=str(project_path),
        depth=depth,
        include_tests=include_tests,
        include_adrs=include_adrs,
        auto_approve=auto_approve,
    )

    # Execute planning with progress
    orchestrator = PlanningOrchestratorService()

    if not quiet:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Step 1: Exploration
            exploration_task = progress.add_task(
                "Spawning explore sub-agents...", total=None
            )

            # Run planning
            result = await orchestrator.plan(request)

            progress.update(
                exploration_task,
                description=(
                    f"[green]✓[/green] Found {result.patterns.total_patterns_found} patterns "
                    f"from {result.patterns.total_files_scanned} files"
                ),
            )
    else:
        result = await orchestrator.plan(request)

    # Output based on format
    if format == "json":
        _output_json(result, output, quiet)
    elif format == "markdown":
        _output_markdown(result, output, quiet)
    else:
        _output_cli(result, quiet)

    # Approval flow (unless auto-approve or quiet)
    if not auto_approve and not quiet and format == "cli":
        console.print()
        approved = Confirm.ask(
            "[bold]Approve this plan?[/bold]",
            default=True,
        )

        if approved:
            await orchestrator.approve_plan(
                planning_id=result.id,
                approved=True,
                notes="Approved via CLI",
            )
            console.print()
            console.print("[bold green]✓ Plan approved![/bold green]")
            console.print()
            console.print("[bold]Next steps:[/bold]")
            console.print("  1. Begin implementation following the plan")
            console.print("  2. Run tests after each step")
            console.print("  3. Update documentation as needed")
            console.print()
        else:
            reason = Prompt.ask(
                "[dim]Rejection reason (optional)[/dim]",
                default="",
            )
            await orchestrator.approve_plan(
                planning_id=result.id,
                approved=False,
                notes=reason if reason else None,
            )
            console.print()
            console.print("[yellow]Plan rejected.[/yellow]")
            console.print("Run 'sdlcctl plan' again with refined task description.")
            console.print()

    # Save to file if requested
    if output:
        output_data = _result_to_dict(result)
        output.write_text(json.dumps(output_data, indent=2, default=str))
        if not quiet:
            console.print(f"[dim]Plan saved to: {output}[/dim]")


def _output_cli(result, quiet: bool) -> None:
    """Output result in CLI format."""
    if quiet:
        # Minimal output for scripts
        print(f"patterns:{result.patterns.total_patterns_found}")
        print(f"conformance:{result.conformance.score}")
        print(f"steps:{len(result.plan.steps)}")
        return

    console.print()

    # Pattern Summary
    pattern_table = Table(title="Extracted Patterns", show_header=True)
    pattern_table.add_column("Category", style="cyan", width=18)
    pattern_table.add_column("Count", justify="right", width=8)

    for category, count in result.patterns.categories.items():
        pattern_table.add_row(category.replace("_", " ").title(), str(count))

    console.print(pattern_table)

    # Top Patterns
    if result.patterns.top_patterns:
        console.print()
        console.print("[bold]Top Patterns Found:[/bold]")
        for i, pattern in enumerate(result.patterns.top_patterns[:5], 1):
            console.print(f"  {i}. {pattern}")

    # Conventions Detected
    if result.patterns.conventions_detected:
        console.print()
        console.print("[bold]Conventions Detected:[/bold]")
        for name, desc in result.patterns.conventions_detected.items():
            console.print(f"  • [cyan]{name}:[/cyan] {desc[:60]}...")

    # Implementation Plan
    console.print()
    console.print(
        Panel(
            result.plan.summary,
            title="[bold green]Implementation Plan[/bold green]",
            border_style="green",
        )
    )

    # Steps Tree
    console.print()
    tree = Tree("[bold]Implementation Steps[/bold]")
    for step in result.plan.steps:
        step_node = tree.add(
            f"[cyan]{step.order}.[/cyan] {step.title} "
            f"[dim]({step.estimated_hours:.1f}h, ~{step.estimated_loc} LOC)[/dim]"
        )
        if step.patterns_to_follow:
            step_node.add(f"[dim]Patterns: {', '.join(step.patterns_to_follow[:3])}[/dim]")
        if step.tests_required:
            step_node.add(f"[dim]Tests: {', '.join(step.tests_required)}[/dim]")

    console.print(tree)

    # Risks
    if result.plan.risks:
        console.print()
        console.print("[bold yellow]⚠️ Identified Risks:[/bold yellow]")
        for risk in result.plan.risks:
            console.print(f"  • {risk}")

    # Conformance Score
    console.print()
    score = result.conformance.score
    level = result.conformance.level.value

    if score >= 90:
        score_color = "green"
        score_icon = "✓"
    elif score >= 70:
        score_color = "yellow"
        score_icon = "○"
    else:
        score_color = "red"
        score_icon = "✗"

    console.print(
        Panel(
            f"[bold {score_color}]{score_icon} Score: {score}/100 ({level})[/bold {score_color}]\n\n"
            + (
                "[dim]Deviations:[/dim]\n"
                + "\n".join(f"  • {d.description}" for d in result.conformance.deviations[:3])
                if result.conformance.deviations
                else "[dim]No significant deviations detected.[/dim]"
            )
            + (
                f"\n\n[dim]Recommendations:[/dim]\n"
                + "\n".join(f"  • {r}" for r in result.conformance.recommendations[:3])
                if result.conformance.recommendations
                else ""
            ),
            title="[bold]Conformance Analysis[/bold]",
            border_style=score_color,
        )
    )

    # Execution time
    console.print()
    console.print(f"[dim]Planning completed in {result.execution_time_ms}ms[/dim]")


def _output_json(result, output: Optional[Path], quiet: bool) -> None:
    """Output result in JSON format."""
    data = _result_to_dict(result)

    if output:
        output.write_text(json.dumps(data, indent=2, default=str))
        if not quiet:
            console.print(f"[dim]Plan saved to: {output}[/dim]")
    else:
        # Print to stdout
        print(json.dumps(data, indent=2, default=str))


def _output_markdown(result, output: Optional[Path], quiet: bool) -> None:
    """Output result in Markdown format."""
    lines = []

    # Header
    lines.append(f"# Implementation Plan")
    lines.append("")
    lines.append(f"**Task:** {result.task}")
    lines.append(f"**Generated:** {datetime.now().isoformat()}")
    lines.append(f"**Conformance Score:** {result.conformance.score}/100")
    lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    lines.append(result.plan.summary)
    lines.append("")

    # Patterns
    lines.append("## Extracted Patterns")
    lines.append("")
    lines.append("| Category | Count |")
    lines.append("|----------|-------|")
    for category, count in result.patterns.categories.items():
        lines.append(f"| {category.replace('_', ' ').title()} | {count} |")
    lines.append("")

    # Top Patterns
    if result.patterns.top_patterns:
        lines.append("### Top Patterns")
        lines.append("")
        for pattern in result.patterns.top_patterns[:5]:
            lines.append(f"- {pattern}")
        lines.append("")

    # Implementation Steps
    lines.append("## Implementation Steps")
    lines.append("")
    for step in result.plan.steps:
        lines.append(f"### {step.order}. {step.title}")
        lines.append("")
        lines.append(step.description)
        lines.append("")
        lines.append(f"- **Estimated:** {step.estimated_hours:.1f}h, ~{step.estimated_loc} LOC")
        if step.patterns_to_follow:
            lines.append(f"- **Patterns:** {', '.join(step.patterns_to_follow)}")
        if step.files_to_create:
            lines.append(f"- **Create:** {', '.join(step.files_to_create)}")
        if step.files_to_modify:
            lines.append(f"- **Modify:** {', '.join(step.files_to_modify)}")
        if step.tests_required:
            lines.append(f"- **Tests:** {', '.join(step.tests_required)}")
        lines.append("")

    # Risks
    if result.plan.risks:
        lines.append("## Risks")
        lines.append("")
        for risk in result.plan.risks:
            lines.append(f"- ⚠️ {risk}")
        lines.append("")

    # Conformance
    lines.append("## Conformance Analysis")
    lines.append("")
    lines.append(f"- **Score:** {result.conformance.score}/100")
    lines.append(f"- **Level:** {result.conformance.level.value}")
    lines.append("")

    if result.conformance.deviations:
        lines.append("### Deviations")
        lines.append("")
        for d in result.conformance.deviations:
            lines.append(f"- **{d.pattern_name}:** {d.description}")
        lines.append("")

    if result.conformance.recommendations:
        lines.append("### Recommendations")
        lines.append("")
        for r in result.conformance.recommendations:
            lines.append(f"- {r}")
        lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append(f"_Generated by `sdlcctl plan` | {datetime.now().strftime('%Y-%m-%d %H:%M')} | Sprint 98_")

    content = "\n".join(lines)

    if output:
        output.write_text(content)
        if not quiet:
            console.print(f"[dim]Plan saved to: {output}[/dim]")
    else:
        console.print(Syntax(content, "markdown", theme="monokai"))


def _result_to_dict(result) -> dict:
    """Convert PlanningResult to dict for JSON serialization."""
    return {
        "id": str(result.id),
        "task": result.task,
        "status": result.status.value,
        "patterns": {
            "total_files_scanned": result.patterns.total_files_scanned,
            "total_patterns_found": result.patterns.total_patterns_found,
            "categories": result.patterns.categories,
            "top_patterns": result.patterns.top_patterns,
            "conventions_detected": result.patterns.conventions_detected,
        },
        "plan": {
            "id": str(result.plan.id),
            "summary": result.plan.summary,
            "steps": [
                {
                    "order": step.order,
                    "title": step.title,
                    "description": step.description,
                    "estimated_loc": step.estimated_loc,
                    "estimated_hours": step.estimated_hours,
                    "files_to_create": step.files_to_create,
                    "files_to_modify": step.files_to_modify,
                    "patterns_to_follow": step.patterns_to_follow,
                    "tests_required": step.tests_required,
                }
                for step in result.plan.steps
            ],
            "total_estimated_loc": result.plan.total_estimated_loc,
            "total_estimated_hours": result.plan.total_estimated_hours,
            "files_to_create": result.plan.files_to_create,
            "files_to_modify": result.plan.files_to_modify,
            "patterns_applied": result.plan.patterns_applied,
            "adrs_referenced": result.plan.adrs_referenced,
            "risks": result.plan.risks,
        },
        "conformance": {
            "score": result.conformance.score,
            "level": result.conformance.level.value,
            "deviations": [
                {
                    "pattern_name": d.pattern_name,
                    "description": d.description,
                    "severity": d.severity,
                    "suggestion": d.suggestion,
                }
                for d in result.conformance.deviations
            ],
            "recommendations": result.conformance.recommendations,
            "requires_adr": result.conformance.requires_adr,
        },
        "execution_time_ms": result.execution_time_ms,
        "requires_approval": result.requires_approval,
    }
