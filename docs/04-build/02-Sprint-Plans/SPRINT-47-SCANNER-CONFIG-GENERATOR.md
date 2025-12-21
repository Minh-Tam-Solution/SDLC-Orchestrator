# SPRINT-47: Scanner Engine & Config Generator
## EP-05: Enterprise SDLC Migration | Phase 1

---

**Document Information**

| Field | Value |
|-------|-------|
| **Sprint ID** | SPRINT-47 |
| **Epic** | EP-05: Enterprise SDLC Migration Engine |
| **Duration** | 2 weeks (Apr 7-18, 2026) |
| **Status** | PLANNED |
| **Team** | 3 Backend + 1 DevOps + 1 QA |
| **Story Points** | 26 SP |
| **Budget** | $15,000 |
| **Framework** | SDLC 5.1.1 + SASE Level 2 |
| **Reference** | ADR-020, Bflow tools (10,500 LOC) |

---

## Sprint Goals

### Primary Objectives

| # | Objective | Priority | Owner |
|---|-----------|----------|-------|
| 1 | Implement parallel file scanner (18x speedup) | P0 | Backend Lead |
| 2 | Build header metadata parser | P0 | Backend Dev 1 |
| 3 | Create `.sdlc-config.json` generator | P0 | Backend Dev 2 |
| 4 | Design migration plan generator | P1 | Backend Lead |
| 5 | Integrate with sdlcctl CLI | P0 | Backend Dev 1 |

### Success Criteria (from ADR-020)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Scanner accuracy | ≥98% | Test on Bflow 3,800 files |
| Scan performance (10K files) | <5 min | Benchmark |
| Config accuracy | 100% | Manual review |
| Header detection | ≥95% | Test dataset |

---

## Architecture (from ADR-020)

### Parallel Scanner Design

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  SDLC Version Migration Scanner (Bflow-Proven Algorithm)                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Input: docs/ folder                                                        │
│       ↓                                                                     │
│  ┌─────────────┐                                                            │
│  │ File Walker │  Walk all .md files                                        │
│  │ (async)     │  Chunk into 500-file batches                              │
│  └──────┬──────┘                                                            │
│         ↓                                                                   │
│  ┌─────────────────────────────────────────────────────────┐               │
│  │                   Thread Pool (8 workers)                │               │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │               │
│  │  │ Worker 1│ │ Worker 2│ │ Worker 3│ │ Worker 4│ ...   │               │
│  │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘       │               │
│  │       │           │           │           │             │               │
│  │       └───────────┴───────────┴───────────┘             │               │
│  │                         ↓                               │               │
│  │                   Merge Results                         │               │
│  └─────────────────────────────────────────────────────────┘               │
│         ↓                                                                   │
│  ┌─────────────┐                                                            │
│  │ Aggregator  │  Combine results                                          │
│  │             │  Generate report                                          │
│  └─────────────┘                                                            │
│         ↓                                                                   │
│  Output: ScanReport                                                         │
│  - files_scanned: int                                                       │
│  - sdlc_version_detected: str                                              │
│  - compliance_issues: List[Issue]                                          │
│  - migration_recommendations: List[Fix]                                    │
│                                                                             │
│  Performance: 18x faster than sequential (Bflow benchmark)                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Week 1: Scanner Engine (Apr 7-11)

### Day 1-2: Parallel File Scanner

**Task**: Port Bflow's battle-tested parallel scanner

```python
# backend/sdlcctl/migration/scanner.py

import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any
import re
import time

@dataclass
class ScanResult:
    """Result of scanning a single file"""
    file_path: Path
    sdlc_version: Optional[str] = None
    stage: Optional[str] = None
    header_fields: Dict[str, str] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)
    parse_time_ms: float = 0

@dataclass
class ScanReport:
    """Aggregated scan report"""
    total_files: int
    scanned_files: int
    sdlc_versions_found: Dict[str, int]  # version -> count
    stage_distribution: Dict[str, int]    # stage -> count
    compliance_issues: List[Dict]
    scan_time_seconds: float
    workers_used: int

class ParallelScanner:
    """
    Parallel SDLC version scanner
    
    Bflow-proven algorithm:
    - 8 workers (optimal for I/O-bound)
    - 500 files per chunk
    - 18x speedup over sequential
    """
    
    DEFAULT_WORKERS = 8
    CHUNK_SIZE = 500
    
    def __init__(
        self,
        docs_root: Path,
        workers: int = DEFAULT_WORKERS,
        chunk_size: int = CHUNK_SIZE
    ):
        self.docs_root = docs_root
        self.workers = workers
        self.chunk_size = chunk_size
        self.header_parser = HeaderMetadataParser()
    
    async def scan(self) -> ScanReport:
        """Scan all markdown files in parallel"""
        start_time = time.time()
        
        # Collect all markdown files
        all_files = list(self.docs_root.rglob("*.md"))
        total_files = len(all_files)
        
        if total_files == 0:
            return ScanReport(
                total_files=0,
                scanned_files=0,
                sdlc_versions_found={},
                stage_distribution={},
                compliance_issues=[],
                scan_time_seconds=0,
                workers_used=0
            )
        
        # Chunk files
        chunks = [
            all_files[i:i + self.chunk_size]
            for i in range(0, len(all_files), self.chunk_size)
        ]
        
        # Parallel scan
        results: List[ScanResult] = []
        
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = []
            for chunk in chunks:
                future = executor.submit(self._scan_chunk, chunk)
                futures.append(future)
            
            for future in as_completed(futures):
                chunk_results = future.result()
                results.extend(chunk_results)
        
        # Aggregate results
        report = self._aggregate_results(results)
        report.scan_time_seconds = time.time() - start_time
        report.workers_used = min(self.workers, len(chunks))
        
        return report
    
    def _scan_chunk(self, files: List[Path]) -> List[ScanResult]:
        """Scan a chunk of files (runs in thread)"""
        results = []
        for file_path in files:
            result = self._scan_file(file_path)
            results.append(result)
        return results
    
    def _scan_file(self, file_path: Path) -> ScanResult:
        """Scan a single file for SDLC metadata"""
        start = time.time()
        
        try:
            content = file_path.read_text(encoding="utf-8")
            
            # Parse header
            header = self.header_parser.parse(content)
            
            # Detect SDLC version
            version = header.get("SDLC Version") or header.get("Version")
            if version:
                # Normalize version (e.g., "5.1.0" -> "5.1")
                version = self._normalize_version(version)
            
            # Detect stage from path
            stage = self._detect_stage_from_path(file_path)
            
            # Check for issues
            issues = self._check_compliance(header, stage, file_path)
            
            return ScanResult(
                file_path=file_path,
                sdlc_version=version,
                stage=stage,
                header_fields=header,
                issues=issues,
                parse_time_ms=(time.time() - start) * 1000
            )
            
        except Exception as e:
            return ScanResult(
                file_path=file_path,
                issues=[f"Parse error: {str(e)}"],
                parse_time_ms=(time.time() - start) * 1000
            )
    
    def _normalize_version(self, version: str) -> str:
        """Normalize SDLC version string"""
        # Extract major.minor from various formats
        match = re.search(r"(\d+)\.(\d+)", version)
        if match:
            return f"{match.group(1)}.{match.group(2)}"
        return version
    
    def _detect_stage_from_path(self, file_path: Path) -> Optional[str]:
        """Detect SDLC stage from file path"""
        # Path-based detection (100% accuracy from Bflow)
        relative = file_path.relative_to(self.docs_root)
        parts = relative.parts
        
        if parts:
            first_folder = parts[0]
            match = re.match(r"^(\d{2})-(.+)$", first_folder)
            if match:
                return match.group(1)  # Return stage number
        
        return None
    
    def _check_compliance(
        self,
        header: Dict[str, str],
        stage: Optional[str],
        file_path: Path
    ) -> List[str]:
        """Check file for compliance issues"""
        issues = []
        
        # Missing required fields
        required = ["Version", "Date", "Stage", "Status"]
        for field in required:
            if field not in header:
                issues.append(f"Missing header field: {field}")
        
        # Stage mismatch
        header_stage = header.get("Stage", "").split("-")[0] if header.get("Stage") else None
        if stage and header_stage and stage != header_stage:
            issues.append(f"Stage mismatch: path={stage}, header={header_stage}")
        
        return issues
    
    def _aggregate_results(self, results: List[ScanResult]) -> ScanReport:
        """Aggregate scan results into report"""
        versions: Dict[str, int] = {}
        stages: Dict[str, int] = {}
        issues: List[Dict] = []
        
        for result in results:
            # Count versions
            if result.sdlc_version:
                versions[result.sdlc_version] = versions.get(result.sdlc_version, 0) + 1
            else:
                versions["unknown"] = versions.get("unknown", 0) + 1
            
            # Count stages
            if result.stage:
                stages[result.stage] = stages.get(result.stage, 0) + 1
            
            # Collect issues
            for issue in result.issues:
                issues.append({
                    "file": str(result.file_path),
                    "issue": issue,
                    "stage": result.stage
                })
        
        return ScanReport(
            total_files=len(results),
            scanned_files=len([r for r in results if not r.issues or "Parse error" not in r.issues[0]]),
            sdlc_versions_found=versions,
            stage_distribution=stages,
            compliance_issues=issues,
            scan_time_seconds=0,  # Set by caller
            workers_used=0        # Set by caller
        )
```

---

### Day 3-4: Header Metadata Parser

**Task**: Parse SDLC document headers with multiple formats

```python
# backend/sdlcctl/migration/header_parser.py

import re
from typing import Dict, Optional

class HeaderMetadataParser:
    """
    Parse SDLC document header metadata
    
    Supports formats:
    1. Table format: | Field | Value |
    2. YAML frontmatter: ---\nfield: value\n---
    3. Key-value: **Field**: Value
    """
    
    # Regex patterns for different formats
    TABLE_PATTERN = re.compile(
        r'\|\s*\**([^|*]+?)\**\s*\|\s*([^|]+?)\s*\|',
        re.MULTILINE
    )
    
    YAML_PATTERN = re.compile(
        r'^---\s*\n(.*?)\n---',
        re.MULTILINE | re.DOTALL
    )
    
    KV_PATTERN = re.compile(
        r'\*\*([^*]+)\*\*:\s*(.+?)(?:\n|$)',
        re.MULTILINE
    )
    
    def parse(self, content: str) -> Dict[str, str]:
        """Parse header metadata from document content"""
        
        # Try table format first (most common in SDLC)
        header = self._parse_table(content)
        if header:
            return header
        
        # Try YAML frontmatter
        header = self._parse_yaml(content)
        if header:
            return header
        
        # Try key-value format
        header = self._parse_kv(content)
        if header:
            return header
        
        return {}
    
    def _parse_table(self, content: str) -> Optional[Dict[str, str]]:
        """Parse markdown table header format"""
        # Find header table (first table in document)
        lines = content.split('\n')[:50]  # Only check first 50 lines
        table_content = '\n'.join(lines)
        
        matches = self.TABLE_PATTERN.findall(table_content)
        if not matches:
            return None
        
        header = {}
        for field, value in matches:
            field = field.strip()
            value = value.strip()
            
            # Skip table header row
            if field.lower() in ['field', 'property', 'attribute']:
                continue
            if value.lower() in ['value', 'description']:
                continue
            if '---' in field or '---' in value:
                continue
            
            header[field] = value
        
        return header if header else None
    
    def _parse_yaml(self, content: str) -> Optional[Dict[str, str]]:
        """Parse YAML frontmatter format"""
        match = self.YAML_PATTERN.match(content)
        if not match:
            return None
        
        yaml_content = match.group(1)
        header = {}
        
        for line in yaml_content.split('\n'):
            if ':' in line:
                key, _, value = line.partition(':')
                header[key.strip()] = value.strip().strip('"\'')
        
        return header if header else None
    
    def _parse_kv(self, content: str) -> Optional[Dict[str, str]]:
        """Parse key-value format (**Key**: Value)"""
        lines = content.split('\n')[:30]  # Only check first 30 lines
        kv_content = '\n'.join(lines)
        
        matches = self.KV_PATTERN.findall(kv_content)
        if not matches:
            return None
        
        header = {field.strip(): value.strip() for field, value in matches}
        return header if header else None
```

---

### Day 5: Config Generator

**Task**: Generate `.sdlc-config.json` from scan results

```python
# backend/sdlcctl/migration/config_generator.py

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

@dataclass
class SDLCConfig:
    """Generated .sdlc-config.json structure"""
    version: str = "1.0.0"
    sdlc_version: str = "5.1.0"
    project_name: str = "Unknown Project"
    tier: str = "STANDARD"
    docs_root: str = "docs"
    
    # Structure settings
    naming: str = "short"  # "short" or "long"
    stages: list = None
    legacy_folders: list = None
    
    # Validation settings
    strict_naming: bool = True
    require_headers: bool = True
    required_header_fields: list = None
    min_compliance_rate: int = 90
    
    # Enforcement settings
    pre_commit_hook: bool = True
    github_action: bool = True
    block_on_violation: bool = False
    
    def __post_init__(self):
        if self.stages is None:
            self.stages = ["00", "01", "02", "03", "04", "05", "06", "07", "08", "09"]
        if self.legacy_folders is None:
            self.legacy_folders = ["10-archive", "99-legacy"]
        if self.required_header_fields is None:
            self.required_header_fields = ["Version", "Date", "Stage", "Status"]

class ConfigGenerator:
    """
    Generate .sdlc-config.json from scan results
    
    Key insight from Bflow:
    - Replaces 700KB manual docs with 1KB config
    - Generated in 5 seconds vs 2 weeks manual
    """
    
    def __init__(self, scan_report: 'ScanReport'):
        self.report = scan_report
    
    def generate(self, project_name: Optional[str] = None) -> SDLCConfig:
        """Generate config from scan results"""
        
        # Detect dominant SDLC version
        versions = self.report.sdlc_versions_found
        if versions:
            dominant_version = max(versions.items(), key=lambda x: x[1])[0]
            if dominant_version == "unknown":
                dominant_version = "5.1.0"
        else:
            dominant_version = "5.1.0"
        
        # Detect project tier from file count
        tier = self._detect_tier(self.report.total_files)
        
        # Detect naming convention
        naming = self._detect_naming_convention()
        
        # Detect active stages
        stages = sorted(list(self.report.stage_distribution.keys()))
        
        return SDLCConfig(
            sdlc_version=dominant_version,
            project_name=project_name or "SDLC Project",
            tier=tier,
            naming=naming,
            stages=stages if stages else None,
            min_compliance_rate=self._calculate_compliance_target()
        )
    
    def _detect_tier(self, file_count: int) -> str:
        """Detect project tier from file count"""
        if file_count < 50:
            return "LITE"
        elif file_count < 200:
            return "STANDARD"
        elif file_count < 1000:
            return "PROFESSIONAL"
        else:
            return "ENTERPRISE"
    
    def _detect_naming_convention(self) -> str:
        """Detect short vs long folder naming"""
        # Check stage distribution for naming patterns
        stages = self.report.stage_distribution
        
        # If using long names like "00-Project-Foundation" -> "long"
        # If using short names like "00-foundation" -> "short"
        # Default to "short" (SDLC 5.1 standard)
        return "short"
    
    def _calculate_compliance_target(self) -> int:
        """Calculate realistic compliance target"""
        total = self.report.total_files
        issues = len(self.report.compliance_issues)
        
        if total == 0:
            return 90
        
        current_rate = ((total - issues) / total) * 100
        
        # Target 10% above current, max 95%
        target = min(95, int(current_rate + 10))
        return max(70, target)  # Minimum 70%
    
    def to_json(self, config: SDLCConfig) -> str:
        """Serialize config to JSON"""
        return json.dumps({
            "$schema": "https://sdlc-orchestrator.io/schemas/sdlc-config-v1.json",
            "version": config.version,
            "sdlc_version": config.sdlc_version,
            "generated_at": datetime.now().isoformat(),
            
            "project": {
                "name": config.project_name,
                "tier": config.tier,
            },
            
            "structure": {
                "docs_root": config.docs_root,
                "stages": config.stages,
                "naming": config.naming,
                "legacy_folders": config.legacy_folders,
            },
            
            "validation": {
                "strict_naming": config.strict_naming,
                "require_headers": config.require_headers,
                "required_header_fields": config.required_header_fields,
                "min_compliance_rate": config.min_compliance_rate,
            },
            
            "enforcement": {
                "pre_commit_hook": config.pre_commit_hook,
                "github_action": config.github_action,
                "block_on_violation": config.block_on_violation,
            }
        }, indent=2)
    
    def save(self, config: SDLCConfig, output_path: Path) -> Path:
        """Save config to file"""
        config_path = output_path / ".sdlc-config.json"
        config_path.write_text(self.to_json(config))
        return config_path
```

---

## Week 2: CLI Integration & Testing (Apr 14-18)

### Day 6-7: CLI Commands

**Task**: Add `sdlcctl scan` and `sdlcctl init` commands

```python
# backend/sdlcctl/commands/scan.py

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path
import asyncio

from ..migration.scanner import ParallelScanner
from ..migration.config_generator import ConfigGenerator

app = typer.Typer()
console = Console()

@app.command()
def scan(
    path: Path = typer.Argument(
        Path("."),
        help="Path to docs folder or project root"
    ),
    output: str = typer.Option(
        "table",
        "--output", "-o",
        help="Output format: table, json, summary"
    ),
    generate_config: bool = typer.Option(
        False,
        "--generate-config",
        help="Generate .sdlc-config.json from scan"
    ),
    project_name: str = typer.Option(
        None,
        "--project", "-p",
        help="Project name for config generation"
    ),
):
    """
    Scan project for SDLC version and compliance status.
    
    Examples:
        sdlcctl scan
        sdlcctl scan docs/
        sdlcctl scan --generate-config --project "My Project"
    """
    # Find docs folder
    docs_path = _find_docs_folder(path)
    if not docs_path:
        console.print("[red]❌ Could not find docs/ folder[/red]")
        raise typer.Exit(1)
    
    # Run scan with progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Scanning files...", total=None)
        
        scanner = ParallelScanner(docs_path)
        report = asyncio.run(scanner.scan())
        
        progress.update(task, description="Scan complete!")
    
    # Output results
    if output == "table":
        _print_scan_table(report)
    elif output == "json":
        _print_scan_json(report)
    elif output == "summary":
        _print_scan_summary(report)
    
    # Generate config if requested
    if generate_config:
        console.print("\n[cyan]📝 Generating .sdlc-config.json...[/cyan]")
        
        generator = ConfigGenerator(report)
        config = generator.generate(project_name)
        config_path = generator.save(config, path)
        
        console.print(f"[green]✅ Config saved: {config_path}[/green]")

def _print_scan_table(report: 'ScanReport'):
    """Print scan results as table"""
    # Summary table
    summary = Table(title="SDLC Scan Results")
    summary.add_column("Metric", style="bold")
    summary.add_column("Value")
    
    summary.add_row("Total Files", str(report.total_files))
    summary.add_row("Scanned Files", str(report.scanned_files))
    summary.add_row("Scan Time", f"{report.scan_time_seconds:.2f}s")
    summary.add_row("Workers Used", str(report.workers_used))
    summary.add_row("Compliance Issues", str(len(report.compliance_issues)))
    
    console.print(summary)
    
    # Version distribution
    if report.sdlc_versions_found:
        version_table = Table(title="SDLC Versions Found")
        version_table.add_column("Version")
        version_table.add_column("Count")
        version_table.add_column("Percentage")
        
        total = sum(report.sdlc_versions_found.values())
        for version, count in sorted(report.sdlc_versions_found.items()):
            pct = (count / total) * 100
            version_table.add_row(version, str(count), f"{pct:.1f}%")
        
        console.print(version_table)
    
    # Stage distribution
    if report.stage_distribution:
        stage_table = Table(title="Stage Distribution")
        stage_table.add_column("Stage")
        stage_table.add_column("Files")
        
        for stage, count in sorted(report.stage_distribution.items()):
            stage_table.add_row(f"{stage}-*", str(count))
        
        console.print(stage_table)

@app.command()
def init(
    path: Path = typer.Argument(Path(".")),
    project: str = typer.Option(
        None,
        "--project", "-p",
        help="Project name"
    ),
    tier: str = typer.Option(
        "STANDARD",
        "--tier", "-t",
        help="Project tier: LITE, STANDARD, PROFESSIONAL, ENTERPRISE"
    ),
    version: str = typer.Option(
        "5.1.0",
        "--version", "-v",
        help="Target SDLC version"
    ),
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="Overwrite existing config"
    ),
):
    """
    Initialize .sdlc-config.json for a project.
    
    Examples:
        sdlcctl init
        sdlcctl init --project "My Project" --tier PROFESSIONAL
        sdlcctl init --version 5.1.0
    """
    config_path = path / ".sdlc-config.json"
    
    if config_path.exists() and not force:
        console.print(f"[yellow]⚠️ Config already exists: {config_path}[/yellow]")
        console.print("Use --force to overwrite")
        raise typer.Exit(1)
    
    # Create config
    from ..migration.config_generator import SDLCConfig
    
    config = SDLCConfig(
        project_name=project or path.name,
        tier=tier,
        sdlc_version=version,
    )
    
    # Save
    generator = ConfigGenerator(None)
    saved_path = generator.save(config, path)
    
    console.print(f"[green]✅ Config created: {saved_path}[/green]")
    console.print("\nNext steps:")
    console.print("  1. Review and edit .sdlc-config.json")
    console.print("  2. Run 'sdlcctl scan' to check compliance")
    console.print("  3. Run 'sdlcctl validate' to validate structure")
```

---

### Day 8-9: Integration Tests

**Task**: Test scanner on real Bflow-scale data

```python
# tests/integration/test_scanner_performance.py

import pytest
import tempfile
from pathlib import Path
import time

class TestScannerPerformance:
    """Performance tests matching Bflow benchmarks"""
    
    @pytest.fixture
    def large_docs_structure(self, tmp_path):
        """Create 10,000 file structure for testing"""
        docs = tmp_path / "docs"
        
        stages = ["00-foundation", "01-planning", "02-design", "03-integrate",
                  "04-build", "05-test", "06-deploy", "07-operate",
                  "08-collaborate", "09-govern"]
        
        file_count = 0
        for stage in stages:
            stage_path = docs / stage
            stage_path.mkdir(parents=True)
            
            # Create 1000 files per stage
            for i in range(1000):
                folder = stage_path / f"subfolder-{i // 100}"
                folder.mkdir(exist_ok=True)
                
                file_path = folder / f"DOC-{i:04d}.md"
                file_path.write_text(f"""# Document {i}

| Field | Value |
|-------|-------|
| **Version** | 5.1.0 |
| **Date** | 2026-04-01 |
| **Stage** | {stage.split('-')[0]} |
| **Status** | Active |

## Content

This is test document {i}.
""")
                file_count += 1
        
        return tmp_path, file_count
    
    def test_scan_10k_files_under_5_minutes(self, large_docs_structure):
        """Scanner should process 10K files in <5 minutes (ADR-020 target)"""
        tmp_path, file_count = large_docs_structure
        
        scanner = ParallelScanner(tmp_path / "docs")
        
        start = time.time()
        report = asyncio.run(scanner.scan())
        elapsed = time.time() - start
        
        assert report.total_files == file_count
        assert elapsed < 300  # 5 minutes
        
        # Performance metric
        files_per_second = file_count / elapsed
        print(f"\nPerformance: {files_per_second:.1f} files/second")
        print(f"Total time: {elapsed:.1f}s for {file_count} files")
    
    def test_parallel_vs_sequential_speedup(self, large_docs_structure):
        """Parallel should be 10x+ faster than sequential"""
        tmp_path, _ = large_docs_structure
        docs = tmp_path / "docs"
        
        # Parallel scan
        parallel_scanner = ParallelScanner(docs, workers=8)
        start = time.time()
        asyncio.run(parallel_scanner.scan())
        parallel_time = time.time() - start
        
        # Sequential scan (1 worker)
        sequential_scanner = ParallelScanner(docs, workers=1)
        start = time.time()
        asyncio.run(sequential_scanner.scan())
        sequential_time = time.time() - start
        
        speedup = sequential_time / parallel_time
        print(f"\nSpeedup: {speedup:.1f}x (parallel: {parallel_time:.1f}s, sequential: {sequential_time:.1f}s)")
        
        assert speedup >= 5  # At least 5x speedup (conservative)
    
    def test_scanner_accuracy_98_percent(self, large_docs_structure):
        """Scanner should have ≥98% accuracy on well-formed documents"""
        tmp_path, file_count = large_docs_structure
        
        scanner = ParallelScanner(tmp_path / "docs")
        report = asyncio.run(scanner.scan())
        
        # All files should be scanned
        assert report.scanned_files == file_count
        
        # Version detection accuracy
        versioned = sum(v for k, v in report.sdlc_versions_found.items() if k != "unknown")
        accuracy = versioned / file_count * 100
        
        assert accuracy >= 98, f"Accuracy {accuracy}% < 98%"
```

---

### Day 10: Documentation & Review

**Task**: Complete Sprint 47 documentation

**Deliverables Checklist**:
- [ ] `ParallelScanner` class with 8-worker default
- [ ] `HeaderMetadataParser` with 3 format support
- [ ] `ConfigGenerator` for `.sdlc-config.json`
- [ ] `sdlcctl scan` command
- [ ] `sdlcctl init` command
- [ ] Performance tests (10K files < 5 min)
- [ ] Integration tests (≥98% accuracy)

---

## Deliverables

| # | Deliverable | Status |
|---|-------------|--------|
| 1 | `ParallelScanner` class | ⏳ |
| 2 | `HeaderMetadataParser` | ⏳ |
| 3 | `ConfigGenerator` | ⏳ |
| 4 | `sdlcctl scan` command | ⏳ |
| 5 | `sdlcctl init` command | ⏳ |
| 6 | Performance benchmarks | ⏳ |
| 7 | Integration tests | ⏳ |

---

## Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| Sprint 44-46 (EP-04) | ⏳ | Scanner base |
| sdlcctl CLI framework | ✅ | Existing |
| ThreadPoolExecutor | ✅ | stdlib |

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Performance miss target | Low | Medium | Tune workers/chunks |
| Header format not detected | Medium | Medium | Add format fallbacks |
| Memory issues (large repos) | Low | High | Streaming/chunking |

---

*Sprint planned: December 21, 2025*
*CTO Approval: Pending*
