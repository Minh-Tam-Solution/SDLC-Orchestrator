# Sprint 115: Soft Enforcement Specification

**Version**: 1.0.0
**Date**: January 28, 2026
**Status**: DRAFT - Awaiting CTO Approval
**Sprint**: 115 - Soft Enforcement Mode
**Dependencies**: Sprint 114 Metrics Pass (Go Decision)
**Framework**: SDLC 6.1.0

---

## Executive Summary

Sprint 115 enables SOFT enforcement mode where critical violations block PR merge while medium violations generate warnings. This document specifies the enforcement rules, error message templates, and developer experience for the first enforcement phase.

**Goal**: Block critical issues while maintaining developer productivity.

---

## 1. Enforcement Mode Definition

### 1.1 Mode Comparison

| Mode | Critical Violations | Medium Violations | Low Violations |
|------|--------------------|--------------------|----------------|
| **OFF** | Allow | Allow | Allow |
| **WARNING** | Log only | Log only | Log only |
| **SOFT** | **BLOCK** | Warn | Allow |
| **FULL** | **BLOCK** | **BLOCK** | Warn |

### 1.2 Violation Classification

```yaml
# backend/app/config/governance_violations.yaml

violation_classification:
  version: "1.0.0"
  effective_date: "2026-02-10"  # Sprint 115 start

  critical:
    description: "Violations that MUST block in SOFT mode"
    rationale: "These represent fundamental governance failures"

    violations:
      - id: CRIT-001
        name: missing_ownership
        description: "No @owner header in modified files"
        check: "file_header_contains(@owner)"
        severity: error

      - id: CRIT-002
        name: missing_intent
        description: "No intent document for PR"
        check: "intent_document_exists(pr.task_id)"
        severity: error

      - id: CRIT-003
        name: vibecoding_red_zone
        description: "Vibecoding index >= 80"
        check: "vibecoding_index < 80"
        severity: error

      - id: CRIT-004
        name: security_scan_fail
        description: "Semgrep security scan found critical issues"
        check: "semgrep_critical_count == 0"
        severity: error

      - id: CRIT-005
        name: stage_violation
        description: "File changes not allowed in current stage"
        check: "stage_gating_pass(pr.files, project.stage)"
        severity: error

      - id: CRIT-006
        name: missing_ai_attestation
        description: "AI-generated code without attestation"
        check: "ai_attestation_exists_if_ai_generated"
        severity: error

  medium:
    description: "Violations that WARN in SOFT mode"
    rationale: "These are important but not blocking"

    violations:
      - id: MED-001
        name: stale_agents_md
        description: "AGENTS.md not updated in >7 days"
        check: "agents_md_age_days < 7"
        severity: warning

      - id: MED-002
        name: missing_adr_linkage
        description: "Module has no linked ADR"
        check: "adr_linkage_exists(module)"
        severity: warning

      - id: MED-003
        name: vibecoding_orange_zone
        description: "Vibecoding index 60-79"
        check: "vibecoding_index < 60"
        severity: warning

      - id: MED-004
        name: missing_tests
        description: "Code changes without corresponding tests"
        check: "test_coverage_delta >= 0"
        severity: warning

      - id: MED-005
        name: missing_design_doc
        description: "New feature without design document"
        check: "design_doc_exists_if_new_feature"
        severity: warning

      - id: MED-006
        name: high_ai_dependency
        description: "AI-generated code ratio >80%"
        check: "ai_dependency_ratio < 0.8"
        severity: warning

  low:
    description: "Violations that are allowed in SOFT mode"
    rationale: "Best practices but not enforced yet"

    violations:
      - id: LOW-001
        name: vibecoding_yellow_zone
        description: "Vibecoding index 30-59"
        check: "vibecoding_index < 30"
        severity: info

      - id: LOW-002
        name: missing_inline_comments
        description: "Complex logic without comments"
        check: "complexity_has_comments"
        severity: info

      - id: LOW-003
        name: large_pr_size
        description: "PR touches >10 files"
        check: "file_count <= 10"
        severity: info
```

---

## 2. Enforcement Rules YAML

### 2.1 Complete Rules Configuration

```yaml
# backend/app/config/governance_rules.yaml

governance_rules:
  version: "2.0.0"
  mode: "${GOVERNANCE_MODE}"  # OFF, WARNING, SOFT, FULL

  # =========================================================================
  # SOFT ENFORCEMENT RULES (Sprint 115)
  # =========================================================================
  soft_enforcement:
    enabled_when: "${GOVERNANCE_MODE} == 'SOFT'"

    # BLOCK: Critical violations that stop PR merge
    block:
      missing_ownership:
        rule: "All modified files MUST have @owner header"
        check: |
          for file in pr.modified_files:
            if not has_owner_header(file):
              return BLOCK
          return PASS
        message_template: "ownership_missing"
        fix_command: "sdlcctl add-ownership --file {file}"

      missing_intent:
        rule: "All PRs MUST have linked intent document"
        check: |
          if not intent_exists(pr.task_id):
            return BLOCK
          return PASS
        message_template: "intent_missing"
        fix_command: "sdlcctl generate-intent --task {task_id}"

      vibecoding_red:
        rule: "Vibecoding index MUST be < 80"
        check: |
          if pr.vibecoding_index >= 80:
            return BLOCK
          return PASS
        message_template: "vibecoding_red"
        fix_suggestions:
          - "Break up large changes"
          - "Reduce AI dependency"
          - "Improve code structure"

      security_fail:
        rule: "Semgrep MUST not find critical/high severity issues"
        check: |
          if semgrep.critical_count > 0 or semgrep.high_count > 0:
            return BLOCK
          return PASS
        message_template: "security_fail"
        fix_command: "semgrep --config auto {file}"

      stage_violation:
        rule: "Files MUST be allowed in current project stage"
        check: |
          for file in pr.modified_files:
            if not stage_allows(file, project.stage):
              return BLOCK
          return PASS
        message_template: "stage_violation"
        fix_command: "sdlcctl stage advance --project {project_id}"

      ai_attestation_missing:
        rule: "AI-generated code MUST have attestation"
        check: |
          if pr.has_ai_code and not pr.has_attestation:
            return BLOCK
          return PASS
        message_template: "attestation_missing"
        fix_command: "sdlcctl generate-attestation --pr {pr_number}"

    # WARN: Medium violations that generate warnings
    warn:
      stale_agents_md:
        rule: "AGENTS.md SHOULD be updated within 7 days"
        check: |
          if agents_md_age_days > 7:
            return WARN
          return PASS
        message_template: "agents_stale"
        fix_command: "sdlcctl update-agents-md"

      missing_adr:
        rule: "Modules SHOULD link to at least one ADR"
        check: |
          for module in pr.affected_modules:
            if not has_adr_linkage(module):
              return WARN
          return PASS
        message_template: "adr_missing"
        fix_command: "sdlcctl link-adr --module {module}"

      vibecoding_orange:
        rule: "Vibecoding index SHOULD be < 60"
        check: |
          if pr.vibecoding_index >= 60:
            return WARN
          return PASS
        message_template: "vibecoding_orange"

      missing_tests:
        rule: "Code changes SHOULD include tests"
        check: |
          if pr.test_coverage_delta < 0:
            return WARN
          return PASS
        message_template: "tests_missing"

      high_ai_ratio:
        rule: "AI-generated code SHOULD be < 80%"
        check: |
          if pr.ai_dependency_ratio > 0.8:
            return WARN
          return PASS
        message_template: "ai_ratio_high"

    # ALLOW: Low violations that are informational only
    allow:
      - vibecoding_yellow_zone
      - missing_inline_comments
      - large_pr_size

  # =========================================================================
  # AUTO-APPROVAL RULES
  # =========================================================================
  auto_approval:
    enabled_when: "vibecoding_index < 30"
    conditions:
      - all_critical_pass
      - all_medium_pass
      - ownership_verified
      - intent_verified
    routing: "auto_merge_enabled"
    notification: false  # Silent approval

  # =========================================================================
  # ESCALATION RULES
  # =========================================================================
  escalation:
    tech_lead_review:
      when: "vibecoding_index >= 30 AND vibecoding_index < 60"
      timeout: "4 hours"
      fallback: "cto_review"

    cto_review:
      when: "vibecoding_index >= 60 AND vibecoding_index < 80"
      timeout: "8 hours"
      fallback: "reject"

    ceo_review:
      when: "vibecoding_index >= 80 OR override_requested"
      timeout: "24 hours"
      fallback: "reject"
```

---

## 3. Error Message Templates

### 3.1 Template System

```yaml
# backend/app/config/governance_messages.yaml

message_templates:
  version: "1.0.0"
  language: "en"

  # =========================================================================
  # BLOCK MESSAGE TEMPLATES (Critical Violations)
  # =========================================================================
  block:
    ownership_missing:
      title: "Missing Ownership Declaration"
      icon: "user-x"
      color: "red"
      summary: "File `{file_path}` has no @owner header"

      body: |
        ## What Failed
        The file `{file_path}` is missing an ownership declaration.
        Every file in the codebase MUST have an @owner header.

        ## Why This Matters
        - Unowned code = unmaintained code = technical debt
        - When bugs occur, we need to know who's responsible
        - Ownership enables accountability and faster issue resolution

        ## How to Fix

        ### Option 1: Auto-Generate (Recommended)
        ```bash
        sdlcctl add-ownership --file {file_path}
        ```

        ### Option 2: Manual
        Add this header to the top of `{file_path}`:
        ```python
        # @owner: @{suggested_owner}
        # @module: {suggested_module}
        # @created: {today}
        ```

        ## Reference
        - [Ownership Standards](https://docs.sdlc.dev/ownership)
        - [ADR-041 Section 2.1](https://docs.sdlc.dev/adr-041#ownership)

      actions:
        - label: "Auto-Fix"
          command: "sdlcctl add-ownership --file {file_path}"
          style: "primary"
        - label: "View Docs"
          url: "https://docs.sdlc.dev/ownership"
          style: "secondary"

    intent_missing:
      title: "Missing Intent Statement"
      icon: "file-question"
      color: "red"
      summary: "PR #{pr_number} has no linked intent document"

      body: |
        ## What Failed
        This PR is missing an intent statement.
        Task {task_id} does not have a documented intent.

        ## Why This Matters
        - Code without intent confuses future developers
        - Intent documents capture the "WHY" behind changes
        - This is required for compliance and audit trails

        ## How to Fix

        ### Option 1: Auto-Generate (Recommended)
        ```bash
        sdlcctl generate-intent --task {task_id} --pr {pr_number}
        ```
        This will create: `docs/intents/{task_id}-intent.md`

        ### Option 2: Manual
        Create `docs/intents/{task_id}-intent.md` with:
        - Why This Change?
        - What Problem Does It Solve?
        - Alternatives Considered

        Then link in PR description: `Intent: docs/intents/{task_id}-intent.md`

        ## Reference
        - [Intent Documentation Guide](https://docs.sdlc.dev/intent)

      actions:
        - label: "Generate Intent"
          command: "sdlcctl generate-intent --task {task_id} --pr {pr_number}"
          style: "primary"

    vibecoding_red:
      title: "Vibecoding Index Too High"
      icon: "alert-triangle"
      color: "red"
      summary: "Index: {vibecoding_index}/100 (threshold: 80)"

      body: |
        ## What Failed
        Your PR has a vibecoding index of **{vibecoding_index}**, which exceeds the threshold of 80.

        ## Top Contributing Signals

        | Signal | Score | Contribution |
        |--------|-------|--------------|
        | {signal_1_name} | {signal_1_score} | {signal_1_pct}% |
        | {signal_2_name} | {signal_2_score} | {signal_2_pct}% |
        | {signal_3_name} | {signal_3_score} | {signal_3_pct}% |

        ## Why This Matters
        - High vibecoding index indicates potential code quality issues
        - CEO review is required for all red zone PRs
        - This prevents "vibecoding" - unreviewed AI-generated code

        ## How to Fix

        ### 1. Reduce Change Surface Area
        - Break PR into smaller, focused changes
        - Submit incremental PRs instead of one large PR

        ### 2. Address Top Signal
        {signal_1_fix_suggestion}

        ### 3. Request CEO Override (If Necessary)
        ```bash
        sdlcctl request-override --pr {pr_number} --reason "..."
        ```

        ## Reference
        - [Vibecoding Index Explained](https://docs.sdlc.dev/vibecoding)
        - [How to Reduce Your Index](https://docs.sdlc.dev/reduce-vibecoding)

      actions:
        - label: "View Details"
          url: "/governance/pr/{pr_number}/analysis"
          style: "primary"
        - label: "Request Override"
          command: "sdlcctl request-override --pr {pr_number}"
          style: "secondary"

    security_fail:
      title: "Security Scan Failed"
      icon: "shield-x"
      color: "red"
      summary: "{critical_count} critical, {high_count} high severity issues"

      body: |
        ## What Failed
        Semgrep security scan found vulnerabilities:
        - **Critical**: {critical_count}
        - **High**: {high_count}

        ## Findings

        {findings_table}

        ## Why This Matters
        - Security vulnerabilities can lead to data breaches
        - Critical/high severity issues MUST be fixed before merge
        - This protects our users and our reputation

        ## How to Fix

        Run Semgrep locally to see detailed findings:
        ```bash
        semgrep --config auto {affected_files}
        ```

        ## Reference
        - [Security Scan Guide](https://docs.sdlc.dev/security-scan)
        - [Common Vulnerability Fixes](https://docs.sdlc.dev/vuln-fixes)

      actions:
        - label: "View Full Report"
          url: "/governance/pr/{pr_number}/security"
          style: "primary"

    stage_violation:
      title: "Stage Gating Violation"
      icon: "lock"
      color: "red"
      summary: "Files not allowed in {current_stage} stage"

      body: |
        ## What Failed
        You're modifying files that are not allowed in the current project stage.

        **Current Stage**: {current_stage}
        **Blocked Files**:
        {blocked_files_list}

        ## Why This Matters
        - Working ahead of design leads to rework
        - Stage gates ensure proper process is followed
        - Complete previous stages before modifying these files

        ## How to Fix

        ### Option 1: Advance the Stage
        If you've completed the prerequisites:
        ```bash
        sdlcctl stage advance --project {project_id}
        ```

        ### Option 2: Request Exception
        For emergency hotfixes:
        ```bash
        sdlcctl request-exception --type stage_bypass --pr {pr_number}
        ```

        ### Option 3: Move Files
        If files are in the wrong location, move them to allowed directories.

        ## Reference
        - [Stage Gating Guide](https://docs.sdlc.dev/stages)
        - [ADR-041 Stage Dependencies](https://docs.sdlc.dev/adr-041#stages)

      actions:
        - label: "View Stage Requirements"
          url: "/projects/{project_id}/stages"
          style: "primary"
        - label: "Request Exception"
          command: "sdlcctl request-exception --type stage_bypass --pr {pr_number}"
          style: "secondary"

    attestation_missing:
      title: "Missing AI Attestation"
      icon: "bot"
      color: "red"
      summary: "AI-generated code detected without attestation"

      body: |
        ## What Failed
        This PR contains AI-generated code but no attestation form has been submitted.

        **AI-Generated Files**:
        {ai_files_list}

        **AI Dependency Ratio**: {ai_ratio}%

        ## Why This Matters
        - AI code must be reviewed and understood by humans
        - Attestation ensures accountability for AI-generated code
        - This is required for compliance and audit trails

        ## How to Fix

        ### Option 1: Auto-Generate (Recommended)
        ```bash
        sdlcctl generate-attestation --pr {pr_number}
        ```

        ### Option 2: Submit via UI
        1. Go to /governance/attestation
        2. Select PR #{pr_number}
        3. Complete the attestation form
        4. Confirm review time met (minimum: {min_review_time})

        ## Reference
        - [AI Attestation Guide](https://docs.sdlc.dev/ai-attestation)
        - [Why Attestation Matters](https://docs.sdlc.dev/ai-governance)

      actions:
        - label: "Submit Attestation"
          url: "/governance/attestation?pr={pr_number}"
          style: "primary"

  # =========================================================================
  # WARNING MESSAGE TEMPLATES (Medium Violations)
  # =========================================================================
  warn:
    agents_stale:
      title: "AGENTS.md is Stale"
      icon: "clock"
      color: "yellow"
      summary: "Last updated {days_old} days ago"

      body: |
        ## What's Wrong
        The AGENTS.md file hasn't been updated in {days_old} days.

        ## Why This Matters
        - AI assistants use AGENTS.md for context
        - Stale context leads to incorrect suggestions
        - Regular updates improve AI assistance quality

        ## Recommendation
        Update AGENTS.md with recent changes:
        ```bash
        sdlcctl update-agents-md
        ```

    adr_missing:
      title: "Missing ADR Linkage"
      icon: "link"
      color: "yellow"
      summary: "Module `{module}` has no linked ADR"

      body: |
        ## What's Wrong
        The module `{module}` doesn't reference any Architecture Decision Record (ADR).

        ## Why This Matters
        - ADRs document architectural decisions
        - Modules should reference relevant ADRs
        - This helps future developers understand the "why"

        ## Recommendation
        Link an existing ADR or create a new one:
        ```bash
        sdlcctl link-adr --module {module} --adr ADR-XXX
        # OR
        sdlcctl create-adr --module {module}
        ```

    vibecoding_orange:
      title: "Vibecoding Index in Orange Zone"
      icon: "alert-circle"
      color: "orange"
      summary: "Index: {vibecoding_index}/100 (range: 60-79)"

      body: |
        ## Notice
        Your PR has a vibecoding index of **{vibecoding_index}**, which is in the orange zone.

        **Top Signal**: {top_signal_name} ({top_signal_score})

        ## Why This Matters
        - Orange zone PRs require Tech Lead review
        - Consider addressing the top signal before merge

        ## Recommendation
        Review the suggested focus area: `{suggested_focus_file}`

    tests_missing:
      title: "Test Coverage Decreased"
      icon: "test-tube"
      color: "yellow"
      summary: "Coverage delta: {coverage_delta}%"

      body: |
        ## What's Wrong
        Test coverage decreased by {coverage_delta}% with this PR.

        **Before**: {coverage_before}%
        **After**: {coverage_after}%

        ## Recommendation
        Add tests for the new code to maintain coverage.

    ai_ratio_high:
      title: "High AI Dependency"
      icon: "cpu"
      color: "yellow"
      summary: "AI-generated: {ai_ratio}% (threshold: 80%)"

      body: |
        ## Notice
        {ai_ratio}% of this PR is AI-generated code.

        ## Why This Matters
        - High AI dependency requires careful human review
        - Ensure you understand all generated code

        ## Recommendation
        - Review AI-generated sections carefully
        - Add inline comments for complex logic
        - Consider refactoring if code is unclear
```

### 3.2 Message Renderer Service

```python
# backend/app/services/governance/message_renderer.py

from typing import Any
import yaml
from jinja2 import Template

from app.config import get_settings


class GovernanceMessageRenderer:
    """
    Render governance violation messages from templates.

    Supports:
    - Variable interpolation
    - Markdown formatting
    - Multi-format output (CLI, Web, Slack)
    """

    def __init__(self):
        self.templates = self._load_templates()

    def _load_templates(self) -> dict:
        """Load message templates from YAML."""
        settings = get_settings()
        template_path = settings.governance_messages_path

        with open(template_path) as f:
            return yaml.safe_load(f)

    def render_block_message(
        self,
        template_key: str,
        context: dict[str, Any],
        format: str = "markdown",  # markdown, plain, html, slack
    ) -> str:
        """
        Render a block message for critical violations.

        Args:
            template_key: Template identifier (e.g., "ownership_missing")
            context: Variables for template interpolation
            format: Output format

        Returns:
            Rendered message string
        """
        template_data = self.templates["block"].get(template_key)
        if not template_data:
            return f"Unknown violation: {template_key}"

        # Render title and summary
        title = Template(template_data["title"]).render(context)
        summary = Template(template_data["summary"]).render(context)
        body = Template(template_data["body"]).render(context)

        if format == "markdown":
            return self._format_markdown(title, summary, body, template_data)
        elif format == "plain":
            return self._format_plain(title, summary, body)
        elif format == "slack":
            return self._format_slack(title, summary, body, template_data)
        elif format == "html":
            return self._format_html(title, summary, body, template_data)

        return body

    def render_warn_message(
        self,
        template_key: str,
        context: dict[str, Any],
        format: str = "markdown",
    ) -> str:
        """Render a warning message for medium violations."""
        template_data = self.templates["warn"].get(template_key)
        if not template_data:
            return f"Unknown warning: {template_key}"

        title = Template(template_data["title"]).render(context)
        summary = Template(template_data["summary"]).render(context)
        body = Template(template_data["body"]).render(context)

        return self._format_markdown(title, summary, body, template_data)

    def _format_markdown(
        self,
        title: str,
        summary: str,
        body: str,
        template_data: dict,
    ) -> str:
        """Format message as Markdown."""
        color_emoji = {
            "red": "x",
            "orange": "warning",
            "yellow": "warning",
        }.get(template_data.get("color", "red"), "x")

        actions_md = ""
        if "actions" in template_data:
            actions_md = "\n## Quick Actions\n"
            for action in template_data["actions"]:
                if "command" in action:
                    actions_md += f"- `{action['command']}`\n"
                elif "url" in action:
                    actions_md += f"- [{action['label']}]({action['url']})\n"

        return f"""# :{color_emoji}: {title}

**{summary}**

{body}
{actions_md}"""

    def _format_plain(self, title: str, summary: str, body: str) -> str:
        """Format message as plain text."""
        # Strip markdown
        import re
        plain_body = re.sub(r'[#*`]', '', body)
        plain_body = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', plain_body)

        return f"""
{title}
{'=' * len(title)}

{summary}

{plain_body}
"""

    def _format_slack(
        self,
        title: str,
        summary: str,
        body: str,
        template_data: dict,
    ) -> dict:
        """Format message as Slack blocks."""
        color = template_data.get("color", "danger")
        color_map = {"red": "danger", "orange": "warning", "yellow": "warning"}

        return {
            "attachments": [
                {
                    "color": color_map.get(color, "danger"),
                    "blocks": [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": title,
                            },
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": summary,
                            },
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": body[:2900],  # Slack limit
                            },
                        },
                    ],
                },
            ],
        }

    def _format_html(
        self,
        title: str,
        summary: str,
        body: str,
        template_data: dict,
    ) -> str:
        """Format message as HTML."""
        import markdown

        color = template_data.get("color", "red")
        color_class = f"border-{color}-500 bg-{color}-50"

        html_body = markdown.markdown(body, extensions=["tables", "fenced_code"])

        return f"""
<div class="governance-message {color_class} p-4 rounded-lg border-l-4">
    <h2 class="text-lg font-bold text-{color}-700">{title}</h2>
    <p class="text-sm text-{color}-600 mt-1">{summary}</p>
    <div class="mt-4 prose prose-sm">
        {html_body}
    </div>
</div>
"""
```

---

## 4. Enforcement Decision Flowchart

### 4.1 SOFT Mode Decision Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SOFT ENFORCEMENT FLOW                                 │
│                        (Sprint 115)                                          │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌───────────────┐
                              │   PR Created  │
                              └───────┬───────┘
                                      │
                              ┌───────▼───────┐
                              │ Auto-Generate │
                              │   Artifacts   │
                              └───────┬───────┘
                                      │
                              ┌───────▼───────┐
                              │   Evaluate    │
                              │  Governance   │
                              └───────┬───────┘
                                      │
               ┌──────────────────────┼──────────────────────┐
               │                      │                      │
        ┌──────▼──────┐        ┌──────▼──────┐        ┌──────▼──────┐
        │  CRITICAL   │        │   MEDIUM    │        │    LOW      │
        │ Violations? │        │ Violations? │        │ Violations? │
        └──────┬──────┘        └──────┬──────┘        └──────┬──────┘
               │                      │                      │
        ┌──────▼──────┐        ┌──────▼──────┐        ┌──────▼──────┐
        │    YES      │        │    YES      │        │     ANY     │
        └──────┬──────┘        └──────┬──────┘        └──────┬──────┘
               │                      │                      │
        ┌──────▼──────┐        ┌──────▼──────┐        ┌──────▼──────┐
        │   BLOCK     │        │    WARN     │        │   ALLOW     │
        │   MERGE     │        │  (Continue) │        │  (Continue) │
        └──────┬──────┘        └──────┬──────┘        └──────┬──────┘
               │                      │                      │
               │                      └──────────┬───────────┘
               │                                 │
               │                      ┌──────────▼──────────┐
               │                      │  Vibecoding Index   │
               │                      │     Routing         │
               │                      └──────────┬──────────┘
               │                                 │
               │        ┌────────────┬───────────┼───────────┬────────────┐
               │        │            │           │           │            │
               │  ┌─────▼─────┐┌─────▼─────┐┌────▼────┐┌─────▼─────┐     │
               │  │  GREEN    ││  YELLOW   ││ ORANGE  ││   RED     │     │
               │  │   <30     ││  30-59    ││  60-79  ││   80+     │     │
               │  └─────┬─────┘└─────┬─────┘└────┬────┘└─────┬─────┘     │
               │        │            │           │           │            │
               │  ┌─────▼─────┐┌─────▼─────┐┌────▼────┐┌─────▼─────┐     │
               │  │   AUTO    ││ TECH LEAD ││   CTO   ││   CEO     │     │
               │  │  APPROVE  ││  REVIEW   ││ REVIEW  ││  REVIEW   │     │
               │  └─────┬─────┘└─────┬─────┘└────┬────┘└─────┬─────┘     │
               │        │            │           │           │            │
               │        └────────────┴───────────┴───────────┘            │
               │                                 │                        │
               │                      ┌──────────▼──────────┐            │
               │                      │   Review Decision   │            │
               │                      └──────────┬──────────┘            │
               │                                 │                        │
               │               ┌─────────────────┼─────────────────┐     │
               │               │                 │                 │     │
               │        ┌──────▼──────┐   ┌──────▼──────┐   ┌──────▼──────┐
               │        │   APPROVE   │   │   REJECT    │   │  OVERRIDE   │
               │        │             │   │             │   │   REQUEST   │
               │        └──────┬──────┘   └──────┬──────┘   └──────┬──────┘
               │               │                 │                 │
               │               │                 │          ┌──────▼──────┐
               │               │                 │          │   CEO/CTO   │
               │               │                 │          │   DECIDES   │
               │               │                 │          └──────┬──────┘
               │               │                 │                 │
               │               │                 │      ┌──────────┴──────────┐
               │               │                 │      │                     │
               └───────────────┴─────────────────┴──────┴─────────────────────┘
                               │                 │      │                     │
                        ┌──────▼─────────────────▼──────▼─────────────────────▼──────┐
                        │                                                             │
                        │                    ┌─────────────┐                          │
                        │                    │ MERGE / NO  │                          │
                        │                    │   MERGE     │                          │
                        │                    └─────────────┘                          │
                        │                                                             │
                        └─────────────────────────────────────────────────────────────┘
```

---

## 5. API Endpoints

### 5.1 Enforcement API

```python
# backend/app/api/v1/endpoints/enforcement.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.schemas.enforcement import (
    EnforcementResultResponse,
    OverrideRequest,
    OverrideResponse,
)
from app.services.governance.enforcement_service import EnforcementService

router = APIRouter(prefix="/enforcement", tags=["enforcement"])


@router.post("/evaluate/{pr_number}", response_model=EnforcementResultResponse)
async def evaluate_pr_enforcement(
    pr_number: int,
    repo_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Evaluate a PR against enforcement rules.

    Returns:
        - blocked: True if critical violations found
        - warnings: List of medium violations
        - violations: Detailed violation info
        - message: Rendered error message (if blocked)
    """
    service = EnforcementService(db)
    return await service.evaluate_enforcement(pr_number, repo_id)


@router.post("/override", response_model=OverrideResponse)
async def request_override(
    request: OverrideRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Request an override for a blocked PR.

    Requires approval from CTO or CEO based on vibecoding index.
    """
    service = EnforcementService(db)
    return await service.request_override(current_user.id, request)


@router.post("/override/{override_id}/approve")
async def approve_override(
    override_id: str,
    notes: str = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Approve an override request.

    Requires: CTO or CEO role
    """
    if current_user.role not in ["cto", "ceo"]:
        raise HTTPException(status_code=403, detail="CTO/CEO approval required")

    service = EnforcementService(db)
    return await service.approve_override(override_id, current_user.id, notes)


@router.post("/override/{override_id}/reject")
async def reject_override(
    override_id: str,
    reason: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Reject an override request.

    Requires: CTO or CEO role
    """
    if current_user.role not in ["cto", "ceo"]:
        raise HTTPException(status_code=403, detail="CTO/CEO rejection required")

    service = EnforcementService(db)
    return await service.reject_override(override_id, current_user.id, reason)
```

---

## 6. Success Metrics

### 6.1 Sprint 115 Targets

| Metric | Target | Measurement | Alert Threshold |
|--------|--------|-------------|-----------------|
| First-Pass Rate | > 70% | PRs passing on first evaluation | < 50% |
| Blocked PR Rate | < 20% | PRs blocked by critical violations | > 30% |
| CEO Time Saved | 25%+ vs baseline | Review hours this week vs Sprint 114 | < 10% |
| Developer Friction | < 5 min | Time to resolve violations | > 10 min |
| Override Requests | < 10% of PRs | Override requests / Total PRs | > 20% |
| False Block Rate | < 5% | Wrongly blocked PRs / Total blocked | > 10% |

### 6.2 Kill Switch Triggers

```yaml
# If any of these thresholds are breached, auto-rollback to WARNING mode

kill_switch_triggers:
  blocked_rate_high:
    metric: "blocked_prs / total_prs"
    threshold: "> 0.40"
    action: "rollback_to_warning"
    cooldown: "30 minutes"

  override_rate_high:
    metric: "override_requests / total_prs"
    threshold: "> 0.25"
    action: "alert_cto"
    cooldown: "1 hour"

  latency_degraded:
    metric: "p95_latency_ms"
    threshold: "> 500"
    action: "rollback_to_warning"
    cooldown: "15 minutes"

  developer_complaints:
    metric: "complaints_per_day"
    threshold: "> 5"
    action: "alert_cto"
    cooldown: "4 hours"
```

---

## 7. Implementation Timeline

### 7.1 Sprint 115 Day-by-Day Plan

| Day | Tasks | Owner | Deliverables |
|-----|-------|-------|--------------|
| **Day 1** | Enable SOFT mode, deploy enforcement rules | DevOps + Backend | Mode active, rules loaded |
| **Day 2** | Monitor block rate, tune thresholds | CTO + Backend | First day metrics |
| **Day 3** | Handle override requests, fix false positives | Full team | Override flow working |
| **Day 4** | Measure CEO time saved, collect feedback | CTO + CEO | Time comparison report |
| **Day 5** | Go/No-Go decision for Full Enforcement | CTO + CEO | Decision documented |

---

## 8. Go/No-Go Decision for Sprint 116

### 8.1 Decision Criteria

```yaml
go_to_full_enforcement:
  mandatory:
    - first_pass_rate >= 70%
    - blocked_rate <= 20%
    - false_block_rate <= 5%
    - developer_friction < 5 minutes

  recommended:
    - ceo_time_saved >= 25%
    - override_rate < 10%
    - team_nps > 50

  approval:
    - CTO sign-off (technical readiness)
    - CEO sign-off (business impact confirmed)

extend_soft_mode:
  conditions:
    - any mandatory criterion fails
    - team feedback negative

  actions:
    - Tune enforcement thresholds
    - Improve error messages
    - Re-evaluate in 1 week
```

---

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Created** | January 28, 2026 |
| **Author** | Backend Lead |
| **Status** | DRAFT - Awaiting CTO Approval |
| **Sprint** | 115 |
| **Dependencies** | Sprint 114 Go Decision |

---

*SDLC Framework 6.0 - Quality Assurance System - Soft Enforcement Specification*
