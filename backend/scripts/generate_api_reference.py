#!/usr/bin/env python3
"""
Generate human-readable API Reference from OpenAPI spec.

Purpose: Create COMPLETE-API-ENDPOINT-REFERENCE.md for Stage 03
Usage: python3 scripts/generate_api_reference.py
"""

import json
from pathlib import Path
from collections import defaultdict

def load_openapi():
    """Load OpenAPI specification."""
    spec_path = Path(__file__).parent.parent.parent / "docs/03-integrate/02-API-Specifications/openapi.json"
    with open(spec_path) as f:
        return json.load(f)

def generate_markdown(spec):
    """Generate markdown documentation from OpenAPI spec."""

    info = spec.get("info", {})
    paths = spec.get("paths", {})

    # Group endpoints by tag
    by_tag = defaultdict(list)

    for path, methods in sorted(paths.items()):
        for method, details in methods.items():
            if method in ["get", "post", "put", "delete", "patch"]:
                tags = details.get("tags", ["Uncategorized"])
                for tag in tags:
                    by_tag[tag].append({
                        "path": path,
                        "method": method.upper(),
                        "summary": details.get("summary", "No description"),
                        "description": details.get("description", ""),
                        "operationId": details.get("operationId", ""),
                    })

    # Generate markdown
    md = []
    md.append("# Complete API Endpoint Reference")
    md.append("")
    md.append(f"**API**: {info.get('title', 'Unknown')}")
    md.append(f"**Version**: {info.get('version', 'Unknown')}")
    md.append(f"**OpenAPI**: {spec.get('openapi', 'Unknown')}")
    md.append(f"**Description**: {info.get('description', 'No description')}")
    md.append("")
    md.append("---")
    md.append("")

    # Table of Contents
    md.append("## Table of Contents")
    md.append("")
    for tag in sorted(by_tag.keys()):
        anchor = tag.lower().replace(" ", "-").replace("/", "-")
        count = len(by_tag[tag])
        md.append(f"- [{tag}](#{anchor}) ({count} endpoints)")
    md.append("")
    md.append("---")
    md.append("")

    # Endpoints by tag
    for tag in sorted(by_tag.keys()):
        md.append(f"## {tag}")
        md.append("")

        for endpoint in by_tag[tag]:
            method = endpoint["method"]
            path = endpoint["path"]
            summary = endpoint["summary"]
            description = endpoint["description"]

            # Method badge
            method_badge = {
                "GET": "🔵 GET",
                "POST": "🟢 POST",
                "PUT": "🟡 PUT",
                "DELETE": "🔴 DELETE",
                "PATCH": "🟠 PATCH"
            }.get(method, method)

            md.append(f"### {method_badge} `{path}`")
            md.append("")
            md.append(f"**Summary**: {summary}")
            md.append("")

            if description and len(description) > 50:
                # Truncate long descriptions
                desc_lines = description.split("\n")
                if len(desc_lines) > 5:
                    md.append("<details>")
                    md.append("<summary>View full description</summary>")
                    md.append("")
                    for line in desc_lines[:30]:  # Limit to 30 lines
                        md.append(line)
                    if len(desc_lines) > 30:
                        md.append("")
                        md.append("*(truncated for brevity)*")
                    md.append("")
                    md.append("</details>")
                else:
                    md.append(f"**Description**: {description[:500]}")
                    if len(description) > 500:
                        md.append("*(truncated)*")
            md.append("")
            md.append("---")
            md.append("")

    # Summary statistics
    md.append("## Summary Statistics")
    md.append("")
    md.append(f"- **Total Categories**: {len(by_tag)}")
    md.append(f"- **Total Endpoints**: {sum(len(endpoints) for endpoints in by_tag.values())}")
    md.append("")
    md.append("### Endpoints by Category")
    md.append("")
    for tag in sorted(by_tag.keys()):
        count = len(by_tag[tag])
        md.append(f"- {tag}: {count} endpoints")
    md.append("")

    # Footer
    md.append("---")
    md.append("")
    md.append("**Document Status**: ✅ Auto-Generated from OpenAPI Specification")
    md.append(f"**Source**: `docs/03-integrate/02-API-Specifications/openapi.json`")
    md.append("**Generated**: Sprint 145+ - MCP Integration Phase 1")
    md.append("**Framework**: SDLC 6.0.5 (Stage 03 Integration)")
    md.append("**Date**: February 3, 2026")
    md.append("")

    return "\n".join(md)

def main():
    """Main function."""
    spec = load_openapi()
    markdown = generate_markdown(spec)

    output_path = Path(__file__).parent.parent.parent / "docs/03-integrate/02-API-Specifications/COMPLETE-API-ENDPOINT-REFERENCE.md"
    output_path.write_text(markdown)

    print(f"✅ Generated {output_path}")
    print(f"📊 Lines: {len(markdown.split(chr(10)))}")

if __name__ == "__main__":
    main()
