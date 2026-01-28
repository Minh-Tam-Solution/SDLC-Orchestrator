# Error Message Templates
# SDLC Orchestrator - Framework 6.0 Governance System
# Sprint 115 - Soft Enforcement

"""
User-friendly error messages with actionable fix suggestions.
Used when governance checks block PRs in SOFT or FULL mode.
"""

# ============================================================================
# Template Structure
# ============================================================================
# Each template includes:
# - title: Short error title (shown in PR comment header)
# - message: Detailed explanation (markdown supported)
# - severity: critical, high, medium, low
# - suggested_fixes: List of actionable steps
# - documentation_link: Link to docs
# - example: Code example if applicable
# ============================================================================

ERROR_TEMPLATES = {
    
    # ==========================================================================
    # OWNERSHIP ERRORS
    # ==========================================================================
    
    "ownership_missing": {
        "title": "🔒 Missing File Ownership",
        "severity": "medium",
        "message": """
### Files Without Ownership

Your PR modifies **{unowned_count} files** that don't have clear ownership defined in `CODEOWNERS`.

**Why this matters:**
- Ownership ensures the right people review changes
- Helps with future maintenance and bug triage
- Required for CEO auto-routing decisions

**Files missing ownership:**
{unowned_files_list}
""",
        "suggested_fixes": [
            {
                "step": 1,
                "action": "Update CODEOWNERS file",
                "command": "# Add to .github/CODEOWNERS\n{file_pattern} @{suggested_owner}",
                "explanation": "We analyzed git blame and suggest these owners based on commit history"
            },
            {
                "step": 2,
                "action": "Or assign PR reviewers manually",
                "command": "gh pr edit {pr_number} --add-reviewer {suggested_owner}",
                "explanation": "This PR will route to the assigned reviewers"
            },
            {
                "step": 3,
                "action": "Request CTO override if urgent",
                "command": "Add label 'governance-override-needed' to this PR",
                "explanation": "CTO can manually approve if ownership unclear"
            }
        ],
        "auto_suggestions": {
            "enabled": true,
            "display": "**💡 Auto-Generated Suggestions:**\n{ownership_suggestions_markdown}"
        },
        "documentation_link": "https://docs.sdlc-orchestrator.dev/governance/ownership",
        "estimated_fix_time": "2-5 minutes",
        "bypass_options": [
            "Add label 'governance-exempt' (requires CTO approval)",
            "Use CTO manual override button",
            "Activate break glass for P0 incidents"
        ]
    },
    
    "ownership_stale": {
        "title": "⚠️ Stale Ownership Information",
        "severity": "low",
        "message": """
### CODEOWNERS File Out of Date

Your `CODEOWNERS` file hasn't been updated in **{days_since_update} days**.

**Why this matters:**
- Team members may have changed roles
- New components may lack ownership
- Stale owners slow down PR review routing

**Last updated:** {last_update_date} by {last_updater}
""",
        "suggested_fixes": [
            {
                "step": 1,
                "action": "Review and update CODEOWNERS",
                "command": "git diff HEAD~10 .github/CODEOWNERS",
                "explanation": "Check if ownership matches current team structure"
            },
            {
                "step": 2,
                "action": "Run ownership audit script",
                "command": "python scripts/audit_ownership.py",
                "explanation": "Identifies files with invalid or missing owners"
            }
        ],
        "documentation_link": "https://docs.sdlc-orchestrator.dev/governance/ownership#maintenance",
        "estimated_fix_time": "10-15 minutes",
        "bypass_options": [
            "This is a warning only, PR can proceed"
        ]
    },
    
    # ==========================================================================
    # INTENT ERRORS
    # ==========================================================================
    
    "intent_missing": {
        "title": "📝 Missing Intent Statement",
        "severity": "high",
        "message": """
### PR Needs Clear Intent

Your PR description is missing a clear intent statement explaining **WHY** this change is needed.

**Why this matters:**
- CEO needs context to make informed approval decisions
- Future developers need to understand the reasoning
- Required for governance auto-routing

**Current PR description:**
```
{current_description}
```

**What we're looking for:**
- **WHY:** Business reason or problem being solved
- **WHAT:** What changes are being made
- **HOW:** Technical approach (optional but helpful)
""",
        "suggested_fixes": [
            {
                "step": 1,
                "action": "Use AI to generate intent skeleton",
                "command": "Click 'Generate Intent' button in governance dashboard",
                "explanation": "AI will analyze your code and suggest an intent based on changes"
            },
            {
                "step": 2,
                "action": "Or manually add intent to PR description",
                "template": """
## Intent

### WHY (Business Reason)
[Explain the problem or opportunity]

### WHAT (Changes Made)
- [List key changes]
- [Architectural decisions]

### HOW (Technical Approach - Optional)
[Brief technical explanation if complex]

### References
- ADR-XXX: [Link to relevant ADR]
- Issue #XXX: [Link to ticket]
""",
                "explanation": "Copy this template and fill in the sections"
            }
        ],
        "auto_suggestions": {
            "enabled": true,
            "display": "**💡 AI-Generated Intent Suggestion:**\n{intent_skeleton_markdown}"
        },
        "documentation_link": "https://docs.sdlc-orchestrator.dev/governance/intent",
        "estimated_fix_time": "3-5 minutes",
        "examples": [
            {
                "title": "Good Intent Example",
                "content": """
## Intent

### WHY
CEO spends 40h/week reviewing PRs. We need to reduce this to <20h by auto-approving simple PRs.

### WHAT
- Add Vibecoding Index calculation (0-100 score)
- Auto-approve PRs with index <30 (Green)
- Route medium/high complexity PRs to CEO

### References
- ADR-041: Framework 6.0 Governance System
- Sprint 113: Governance UI implementation
"""
            }
        ],
        "bypass_options": [
            "Add label 'documentation-only' if this is pure docs",
            "Add label 'dependency-update' if automated update",
            "Request CTO override if intent truly unclear"
        ]
    },
    
    "intent_vague": {
        "title": "🤔 Vague Intent Statement",
        "severity": "medium",
        "message": """
### PR Intent Needs More Detail

Your intent statement is too vague. The CEO needs more context to understand the **business reason** for this change.

**Current intent:**
```
{current_intent}
```

**Issues identified:**
- {vagueness_issues}

**What's missing:**
- {missing_elements}
""",
        "suggested_fixes": [
            {
                "step": 1,
                "action": "Add business context",
                "explanation": "Explain the problem from a business perspective (customer impact, revenue, efficiency, etc.)"
            },
            {
                "step": 2,
                "action": "Link to supporting documents",
                "explanation": "Reference ADRs, specs, or issues that provide additional context"
            }
        ],
        "documentation_link": "https://docs.sdlc-orchestrator.dev/governance/intent#good-intent",
        "estimated_fix_time": "2-3 minutes"
    },
    
    # ==========================================================================
    # CONTEXT ERRORS
    # ==========================================================================
    
    "context_missing": {
        "title": "📚 Missing Design Context",
        "severity": "medium",
        "message": """
### PR Lacks Design Context

Your PR makes architectural changes but doesn't reference relevant design documents (ADRs, specs, design docs).

**Why this matters:**
- CEO needs context to evaluate architectural decisions
- Future developers need to understand design rationale
- Helps identify if existing ADRs need updates

**Detected changes:**
{architectural_changes_summary}
""",
        "suggested_fixes": [
            {
                "step": 1,
                "action": "Use AI to auto-attach context",
                "command": "Click 'Auto-Attach Context' in governance dashboard",
                "explanation": "AI will find relevant ADRs/specs based on your file changes"
            },
            {
                "step": 2,
                "action": "Or manually link design docs in PR description",
                "template": """
## Design Context

### Relevant ADRs
- [ADR-041](docs/02-design/03-ADRs/ADR-041-...) - Framework 6.0 Governance

### Technical Specs
- [Governance Implementation Spec](docs/02-design/14-Technical-Specs/...)

### Related PRs
- #123 - Previous work in this area
""",
                "explanation": "Add this section to your PR description"
            },
            {
                "step": 3,
                "action": "Create new ADR if this introduces new architecture",
                "command": "python sdlcctl create adr \"Your Decision Title\"",
                "explanation": "Use sdlcctl CLI to generate ADR template"
            }
        ],
        "auto_suggestions": {
            "enabled": true,
            "display": "**💡 AI-Found Context:**\n{context_suggestions_markdown}"
        },
        "documentation_link": "https://docs.sdlc-orchestrator.dev/governance/context",
        "estimated_fix_time": "5-10 minutes"
    },
    
    "agents_md_missing": {
        "title": "🤖 Missing AI Session Documentation",
        "severity": "medium",
        "message": """
### AGENTS.md Not Updated

We detected AI-generated code in this PR, but `AGENTS.md` wasn't updated.

**Why this matters:**
- Tracks AI usage for compliance and audit
- Documents which AI models were used
- Provides context for future code reviews

**AI usage detected:**
{ai_detection_summary}
""",
        "suggested_fixes": [
            {
                "step": 1,
                "action": "Use AI attestation form to auto-fill",
                "command": "Click 'Fill Attestation' in governance dashboard",
                "explanation": "Form pre-fills with AI session metadata (model, tokens, timestamp)"
            },
            {
                "step": 2,
                "action": "Or manually update AGENTS.md",
                "template": """
## Session {session_id}
**Date:** {date}
**Model:** {model_name}
**Tokens:** {token_count}
**Purpose:** {purpose}
**Files Modified:** {files_list}
**Review Status:** ✅ Reviewed by {reviewer}
""",
                "explanation": "Add this entry to AGENTS.md"
            }
        ],
        "documentation_link": "https://docs.sdlc-orchestrator.dev/governance/ai-attestation",
        "estimated_fix_time": "1-2 minutes",
        "bypass_options": [
            "Add label 'no-ai-used' if this is false positive"
        ]
    },
    
    # ==========================================================================
    # COMPLEXITY ERRORS
    # ==========================================================================
    
    "complexity_too_high": {
        "title": "🚨 PR Too Complex (Vibecoding Index: {index})",
        "severity": "high",
        "message": """
### PR Complexity Exceeds Threshold

Your PR has a **Vibecoding Index of {index}/100** (Red zone: >80).

**Why this matters:**
- CEO would need >{expected_ceo_time} minutes to review
- High complexity PRs have higher defect rates
- Breaking into smaller PRs improves review quality

**Complexity factors:**
- **Files changed:** {files_changed} (target: <15)
- **Lines of code:** {loc_changed} (target: <500)
- **Missing ownership:** {unowned_files} files
- **Test coverage:** {test_coverage}% (target: >80%)
- **Security findings:** {security_issues} issues

**Index breakdown:**
{index_breakdown_chart}
""",
        "suggested_fixes": [
            {
                "step": 1,
                "action": "Break PR into smaller chunks",
                "explanation": "Aim for <500 LOC per PR. Create a PR chain if needed.",
                "example": """
# PR Chain Example:
1. PR #1: Types + API functions (500 LOC)
2. PR #2: React components (400 LOC) - depends on PR #1
3. PR #3: E2E tests (300 LOC) - depends on PR #2
"""
            },
            {
                "step": 2,
                "action": "Address ownership gaps",
                "command": "Click 'Accept Ownership Suggestions' in dashboard",
                "explanation": "Adding ownership reduces index by ~15 points"
            },
            {
                "step": 3,
                "action": "Increase test coverage",
                "command": "npm run test:coverage",
                "explanation": "Adding tests reduces index by ~10 points"
            },
            {
                "step": 4,
                "action": "Request CTO review for exception",
                "explanation": "If PR truly cannot be broken down, CTO can override"
            }
        ],
        "documentation_link": "https://docs.sdlc-orchestrator.dev/governance/vibecoding-index",
        "estimated_fix_time": "30-60 minutes (refactoring required)"
    },
    
    "complexity_medium": {
        "title": "⚠️ Medium Complexity PR (Index: {index})",
        "severity": "low",
        "message": """
### PR Complexity Is Medium (Orange Zone: 61-80)

Your PR will require detailed CEO review ({expected_ceo_time} minutes).

**Consider simplifying if possible:**
- Current index: **{index}/100**
- Target: <60 for standard review

**Quick wins to reduce complexity:**
{quick_wins_list}
""",
        "suggested_fixes": [
            {
                "step": 1,
                "action": "Review complexity factors above",
                "explanation": "Focus on quick wins (ownership, context, tests)"
            }
        ],
        "documentation_link": "https://docs.sdlc-orchestrator.dev/governance/vibecoding-index#optimization",
        "estimated_fix_time": "5-10 minutes",
        "bypass_options": [
            "This is a warning only, PR can proceed"
        ]
    },
    
    # ==========================================================================
    # SECURITY ERRORS
    # ==========================================================================
    
    "security_scan_failed": {
        "title": "🔐 Security Scan Failed",
        "severity": "critical",
        "message": """
### Critical Security Issues Found

Your PR has **{issue_count} high-severity security findings** that must be fixed before proceeding.

**Findings:**
{findings_table}

**Why this blocks:**
- Security issues can lead to data breaches
- Must be fixed before code reaches production
- CTO override required for exceptions
""",
        "suggested_fixes": [
            {
                "step": 1,
                "action": "Fix critical issues immediately",
                "explanation": "See details below for each finding"
            },
            {
                "step": 2,
                "action": "Re-run security scans",
                "command": "make security-audit",
                "explanation": "Verify all issues are resolved"
            },
            {
                "step": 3,
                "action": "Request CTO review if false positive",
                "explanation": "CTO can mark findings as false positives"
            }
        ],
        "findings_details": "{detailed_findings_markdown}",
        "documentation_link": "https://docs.sdlc-orchestrator.dev/governance/security",
        "estimated_fix_time": "15-60 minutes (depends on severity)",
        "bypass_options": [
            "CTO manual override (requires 2FA)",
            "Break glass for P0 hotfix"
        ]
    },
    
    # ==========================================================================
    # STAGE GATING ERRORS
    # ==========================================================================
    
    "stage_gate_failed": {
        "title": "🚪 Stage Gate Requirements Not Met",
        "severity": "medium",
        "message": """
### SDLC Stage: {stage_name}

Your PR is in **{current_stage}** but is missing required artifacts.

**Missing artifacts:**
{missing_artifacts_list}

**Why this matters:**
- Each SDLC stage has quality gates
- Ensures proper design before implementation
- Reduces rework and defects
""",
        "suggested_fixes": [
            {
                "step": 1,
                "action": "Complete missing artifacts",
                "explanation": "See checklist below for each artifact"
            },
            {
                "step": 2,
                "action": "Use sdlcctl CLI for templates",
                "command": "python sdlcctl create {artifact_type} \"{title}\"",
                "explanation": "Auto-generates properly structured documents"
            }
        ],
        "checklist": "{stage_checklist_markdown}",
        "documentation_link": "https://docs.sdlc-orchestrator.dev/stages/{stage_slug}",
        "estimated_fix_time": "20-40 minutes"
    },
    
    # ==========================================================================
    # TEST COVERAGE ERRORS
    # ==========================================================================
    
    "test_coverage_low": {
        "title": "🧪 Test Coverage Below Threshold",
        "severity": "low",
        "message": """
### Test Coverage: {coverage}% (Target: 80%)

Your PR reduces test coverage below the recommended threshold.

**Files with low coverage:**
{low_coverage_files}

**Why this matters:**
- Untested code is more likely to have bugs
- Makes refactoring harder
- Increases maintenance cost
""",
        "suggested_fixes": [
            {
                "step": 1,
                "action": "Add unit tests for new code",
                "command": "npm run test:watch",
                "explanation": "Focus on critical paths first"
            },
            {
                "step": 2,
                "action": "Check coverage report",
                "command": "npm run test:coverage",
                "explanation": "Identifies specific lines needing tests"
            }
        ],
        "documentation_link": "https://docs.sdlc-orchestrator.dev/testing/coverage",
        "estimated_fix_time": "15-30 minutes",
        "bypass_options": [
            "This is a warning only, PR can proceed"
        ]
    },
    
    # ==========================================================================
    # GENERIC ERRORS
    # ==========================================================================
    
    "governance_check_timeout": {
        "title": "⏱️ Governance Check Timeout",
        "severity": "medium",
        "message": """
### Governance Check Exceeded Time Limit

The governance check took >{timeout_ms}ms (limit: 100ms).

**Why this happened:**
- Large PR size (>{files_count} files)
- External API timeout (GitHub, security scanners)
- Infrastructure issue

**What to do:**
- PR is temporarily blocked for your safety
- Automatic retry in 5 minutes
- Or request CTO manual review
""",
        "suggested_fixes": [
            {
                "step": 1,
                "action": "Wait for automatic retry",
                "explanation": "System will retry in 5 minutes"
            },
            {
                "step": 2,
                "action": "Or request CTO override",
                "explanation": "CTO can manually review if urgent"
            }
        ],
        "documentation_link": "https://docs.sdlc-orchestrator.dev/governance/troubleshooting",
        "estimated_fix_time": "5-10 minutes"
    },
    
    "governance_service_unavailable": {
        "title": "🚫 Governance Service Unavailable",
        "severity": "critical",
        "message": """
### Governance System Error

The governance service is temporarily unavailable.

**Status:** {service_status}  
**Incident:** #{incident_id}

**What to do:**
- Check status page: https://status.sdlc-orchestrator.dev
- Automatic fallback to WARNING mode in 2 minutes
- Or use break glass for urgent PRs
""",
        "suggested_fixes": [
            {
                "step": 1,
                "action": "Wait for service recovery",
                "explanation": "Ops team is investigating"
            },
            {
                "step": 2,
                "action": "Use break glass for P0 incidents",
                "explanation": "Emergency bypass available for CTO/CEO"
            }
        ],
        "documentation_link": "https://docs.sdlc-orchestrator.dev/governance/incidents",
        "estimated_fix_time": "Depends on incident severity"
    }
}

# ============================================================================
# Message Formatting Helpers
# ============================================================================

def format_error_message(template_key: str, **kwargs) -> dict:
    """
    Format error message with dynamic values
    
    Args:
        template_key: Key from ERROR_TEMPLATES dict
        **kwargs: Dynamic values to substitute in template
        
    Returns:
        Formatted error message dict
    """
    template = ERROR_TEMPLATES[template_key]
    
    # Substitute variables in message
    message = template["message"].format(**kwargs)
    
    # Format suggested fixes
    formatted_fixes = []
    for fix in template["suggested_fixes"]:
        formatted_fix = {
            "step": fix["step"],
            "action": fix["action"].format(**kwargs) if "command" in fix else fix["action"],
            "command": fix.get("command", "").format(**kwargs),
            "explanation": fix["explanation"].format(**kwargs)
        }
        formatted_fixes.append(formatted_fix)
    
    return {
        "title": template["title"].format(**kwargs),
        "severity": template["severity"],
        "message": message,
        "suggested_fixes": formatted_fixes,
        "documentation_link": template["documentation_link"],
        "estimated_fix_time": template["estimated_fix_time"],
        "bypass_options": template.get("bypass_options", []),
        "auto_suggestions": template.get("auto_suggestions", {}),
        "examples": template.get("examples", [])
    }

# ============================================================================
# GitHub PR Comment Formatter
# ============================================================================

def create_pr_comment(error_key: str, **kwargs) -> str:
    """
    Create GitHub PR comment with error message
    
    Returns markdown-formatted comment
    """
    error = format_error_message(error_key, **kwargs)
    
    comment = f"""
## {error['title']}

**Severity:** `{error['severity'].upper()}`  
**Estimated Fix Time:** {error['estimated_fix_time']}

{error['message']}

---

### 🔧 How to Fix

"""
    
    for fix in error['suggested_fixes']:
        comment += f"\n**Step {fix['step']}: {fix['action']}**\n"
        if fix['command']:
            comment += f"```bash\n{fix['command']}\n```\n"
        comment += f"_{fix['explanation']}_\n"
    
    if error.get('auto_suggestions', {}).get('enabled'):
        comment += f"\n---\n\n{error['auto_suggestions']['display']}\n"
    
    if error.get('examples'):
        comment += "\n---\n\n### 📖 Examples\n\n"
        for example in error['examples']:
            comment += f"**{example['title']}**\n```\n{example['content']}\n```\n"
    
    if error.get('bypass_options'):
        comment += "\n---\n\n### ⚡ Bypass Options\n\n"
        for option in error['bypass_options']:
            comment += f"- {option}\n"
    
    comment += f"\n---\n\n📚 [Full Documentation]({error['documentation_link']})\n"
    comment += "\n_Posted by SDLC Orchestrator Governance System_\n"
    
    return comment
