#!/usr/bin/env python3
"""
Performance Benchmark Script for Codegen Service.

Sprint 45 Day 7: Multi-Provider Codegen Architecture (EP-06)
Measures p95 latency, token throughput, and generation metrics.

Usage:
    python scripts/benchmark_codegen.py
    python scripts/benchmark_codegen.py --runs 5

Author: Backend Lead
Date: December 23, 2025
"""

import asyncio
import argparse
import json
import statistics
import sys
import time
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.codegen import CodegenService, CodegenSpec
from app.services.codegen.demos.vietnamese_sme_demo import get_retail_store_blueprint, get_minimal_demo_blueprint


@dataclass
class BenchmarkResult:
    """Result of a single benchmark run."""
    run_id: int
    latency_ms: float
    tokens_used: int
    files_generated: int
    success: bool
    error: Optional[str] = None


@dataclass
class BenchmarkSummary:
    """Summary of all benchmark runs."""
    total_runs: int
    successful_runs: int
    failed_runs: int

    # Latency metrics (ms)
    latency_min: float
    latency_max: float
    latency_mean: float
    latency_median: float
    latency_p95: float
    latency_p99: float

    # Token metrics
    tokens_total: int
    tokens_mean: float
    tokens_per_second: float

    # File metrics
    files_total: int
    files_mean: float

    # Raw results
    results: List[BenchmarkResult] = field(default_factory=list)


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print section header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")


def print_metric(name: str, value: str, unit: str = ""):
    """Print a metric with formatting."""
    print(f"  {Colors.YELLOW}{name:25}{Colors.RESET}: {value} {unit}")


async def run_single_benchmark(
    service: CodegenService,
    spec: CodegenSpec,
    run_id: int
) -> BenchmarkResult:
    """Run a single benchmark iteration."""
    start_time = time.perf_counter()

    try:
        result = await service.generate(spec)
        latency_ms = (time.perf_counter() - start_time) * 1000

        return BenchmarkResult(
            run_id=run_id,
            latency_ms=latency_ms,
            tokens_used=result.tokens_used,
            files_generated=len(result.files),
            success=True
        )
    except Exception as e:
        latency_ms = (time.perf_counter() - start_time) * 1000
        return BenchmarkResult(
            run_id=run_id,
            latency_ms=latency_ms,
            tokens_used=0,
            files_generated=0,
            success=False,
            error=str(e)
        )


def calculate_percentile(data: List[float], percentile: float) -> float:
    """Calculate percentile of a list of values."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    index = (percentile / 100) * (len(sorted_data) - 1)
    lower = int(index)
    upper = lower + 1
    if upper >= len(sorted_data):
        return sorted_data[-1]
    weight = index - lower
    return sorted_data[lower] * (1 - weight) + sorted_data[upper] * weight


def create_summary(results: List[BenchmarkResult]) -> BenchmarkSummary:
    """Create summary statistics from benchmark results."""
    successful = [r for r in results if r.success]

    if not successful:
        return BenchmarkSummary(
            total_runs=len(results),
            successful_runs=0,
            failed_runs=len(results),
            latency_min=0,
            latency_max=0,
            latency_mean=0,
            latency_median=0,
            latency_p95=0,
            latency_p99=0,
            tokens_total=0,
            tokens_mean=0,
            tokens_per_second=0,
            files_total=0,
            files_mean=0,
            results=results
        )

    latencies = [r.latency_ms for r in successful]
    tokens = [r.tokens_used for r in successful]
    files = [r.files_generated for r in successful]

    total_time_s = sum(latencies) / 1000
    total_tokens = sum(tokens)

    return BenchmarkSummary(
        total_runs=len(results),
        successful_runs=len(successful),
        failed_runs=len(results) - len(successful),
        latency_min=min(latencies),
        latency_max=max(latencies),
        latency_mean=statistics.mean(latencies),
        latency_median=statistics.median(latencies),
        latency_p95=calculate_percentile(latencies, 95),
        latency_p99=calculate_percentile(latencies, 99),
        tokens_total=total_tokens,
        tokens_mean=statistics.mean(tokens),
        tokens_per_second=total_tokens / total_time_s if total_time_s > 0 else 0,
        files_total=sum(files),
        files_mean=statistics.mean(files),
        results=results
    )


async def benchmark_minimal(service: CodegenService, runs: int) -> BenchmarkSummary:
    """Benchmark minimal app generation."""
    print_header("Benchmark: Minimal App Generation")

    blueprint = get_minimal_demo_blueprint()
    spec = CodegenSpec(
        app_blueprint=blueprint.model_dump(),
        language="python",
        framework="fastapi"
    )

    results = []
    for i in range(runs):
        print_info(f"Run {i+1}/{runs}...")
        result = await run_single_benchmark(service, spec, i+1)
        results.append(result)

        if result.success:
            print_success(f"Completed in {result.latency_ms:.0f}ms, {result.tokens_used} tokens, {result.files_generated} files")
        else:
            print_error(f"Failed: {result.error}")

    return create_summary(results)


async def benchmark_vietnamese(service: CodegenService, runs: int) -> BenchmarkSummary:
    """Benchmark Vietnamese SME module generation."""
    print_header("Benchmark: Vietnamese SME Module (san_pham)")

    blueprint = get_retail_store_blueprint()
    spec = CodegenSpec(
        app_blueprint=blueprint.model_dump(),
        language="python",
        framework="fastapi",
        target_module="san_pham"  # Single module for faster benchmark
    )

    results = []
    for i in range(runs):
        print_info(f"Run {i+1}/{runs}...")
        result = await run_single_benchmark(service, spec, i+1)
        results.append(result)

        if result.success:
            print_success(f"Completed in {result.latency_ms:.0f}ms, {result.tokens_used} tokens, {result.files_generated} files")
        else:
            print_error(f"Failed: {result.error}")

    return create_summary(results)


def print_summary(name: str, summary: BenchmarkSummary):
    """Print benchmark summary."""
    print_header(f"Summary: {name}")

    print(f"{Colors.BOLD}Run Statistics:{Colors.RESET}")
    print_metric("Total Runs", str(summary.total_runs))
    print_metric("Successful", f"{summary.successful_runs} ({summary.successful_runs/summary.total_runs*100:.0f}%)")
    print_metric("Failed", str(summary.failed_runs))

    if summary.successful_runs == 0:
        print_error("No successful runs to analyze")
        return

    print(f"\n{Colors.BOLD}Latency (ms):{Colors.RESET}")
    print_metric("Min", f"{summary.latency_min:.0f}", "ms")
    print_metric("Max", f"{summary.latency_max:.0f}", "ms")
    print_metric("Mean", f"{summary.latency_mean:.0f}", "ms")
    print_metric("Median", f"{summary.latency_median:.0f}", "ms")
    print_metric("p95", f"{Colors.CYAN}{summary.latency_p95:.0f}{Colors.RESET}", "ms")
    print_metric("p99", f"{summary.latency_p99:.0f}", "ms")

    print(f"\n{Colors.BOLD}Throughput:{Colors.RESET}")
    print_metric("Total Tokens", str(summary.tokens_total))
    print_metric("Mean Tokens/Request", f"{summary.tokens_mean:.0f}")
    print_metric("Tokens/Second", f"{Colors.CYAN}{summary.tokens_per_second:.1f}{Colors.RESET}")
    print_metric("Total Files", str(summary.files_total))
    print_metric("Mean Files/Request", f"{summary.files_mean:.1f}")


def export_results(summaries: dict, output_file: str):
    """Export benchmark results to JSON."""
    export_data = {}
    for name, summary in summaries.items():
        # Convert to dict without results list for cleaner output
        data = {
            "total_runs": summary.total_runs,
            "successful_runs": summary.successful_runs,
            "failed_runs": summary.failed_runs,
            "latency_ms": {
                "min": round(summary.latency_min, 2),
                "max": round(summary.latency_max, 2),
                "mean": round(summary.latency_mean, 2),
                "median": round(summary.latency_median, 2),
                "p95": round(summary.latency_p95, 2),
                "p99": round(summary.latency_p99, 2)
            },
            "tokens": {
                "total": summary.tokens_total,
                "mean": round(summary.tokens_mean, 2),
                "per_second": round(summary.tokens_per_second, 2)
            },
            "files": {
                "total": summary.files_total,
                "mean": round(summary.files_mean, 2)
            }
        }
        export_data[name] = data

    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2)

    print_success(f"Results exported to {output_file}")


async def main():
    parser = argparse.ArgumentParser(description="Codegen Performance Benchmark")
    parser.add_argument(
        "--runs",
        type=int,
        default=3,
        help="Number of runs per benchmark (default: 3)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="benchmark_results.json",
        help="Output file for results (default: benchmark_results.json)"
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=1,
        help="Number of warmup runs (default: 1)"
    )
    args = parser.parse_args()

    print_header("SDLC Orchestrator - Codegen Performance Benchmark")
    print(f"Sprint 45 Day 7: Multi-Provider Codegen Architecture (EP-06)")
    print(f"Runs per benchmark: {args.runs}")
    print(f"Warmup runs: {args.warmup}")

    service = CodegenService()

    # Check health
    health = service.health_check()
    if not health["healthy"]:
        print_error("No codegen providers available. Ensure Ollama is running.")
        print_info("Set CODEGEN_OLLAMA_URL=http://localhost:11434")
        sys.exit(1)

    print_success(f"Provider ready: {health['available_count']} available")

    # Warmup
    if args.warmup > 0:
        print_header("Warmup Phase")
        print_info(f"Running {args.warmup} warmup iteration(s)...")

        blueprint = get_minimal_demo_blueprint()
        spec = CodegenSpec(
            app_blueprint=blueprint.model_dump(),
            language="python",
            framework="fastapi"
        )

        for i in range(args.warmup):
            result = await run_single_benchmark(service, spec, i+1)
            if result.success:
                print_success(f"Warmup {i+1}: {result.latency_ms:.0f}ms")
            else:
                print_error(f"Warmup {i+1} failed: {result.error}")

    # Run benchmarks
    summaries = {}

    summaries["minimal_app"] = await benchmark_minimal(service, args.runs)
    summaries["vietnamese_sme"] = await benchmark_vietnamese(service, args.runs)

    # Print summaries
    for name, summary in summaries.items():
        print_summary(name, summary)

    # Export results
    export_results(summaries, args.output)

    # Overall summary
    print_header("Overall Benchmark Results")

    all_successful = all(s.failed_runs == 0 for s in summaries.values())

    if all_successful:
        print_success("All benchmarks completed successfully!")

        # Calculate weighted average p95
        total_runs = sum(s.successful_runs for s in summaries.values())
        weighted_p95 = sum(
            s.latency_p95 * s.successful_runs
            for s in summaries.values()
        ) / total_runs if total_runs > 0 else 0

        print(f"\n{Colors.BOLD}Key Metrics:{Colors.RESET}")
        print_metric("Weighted Average p95", f"{weighted_p95:.0f}", "ms")
        print_metric("Total Tokens Generated", str(sum(s.tokens_total for s in summaries.values())))
        print_metric("Total Files Generated", str(sum(s.files_total for s in summaries.values())))

        # Performance assessment
        if weighted_p95 < 60000:  # 60 seconds
            print_success(f"\n{Colors.GREEN}✓ Performance meets target (<60s p95){Colors.RESET}")
        else:
            print_error(f"\n{Colors.RED}✗ Performance below target (>60s p95){Colors.RESET}")
    else:
        failed_count = sum(s.failed_runs for s in summaries.values())
        print_error(f"Some benchmarks failed ({failed_count} failures)")

    sys.exit(0 if all_successful else 1)


if __name__ == "__main__":
    asyncio.run(main())
