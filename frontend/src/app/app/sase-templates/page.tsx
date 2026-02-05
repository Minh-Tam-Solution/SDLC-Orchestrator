/**
 * SASE Templates Page - SDLC Orchestrator Dashboard
 *
 * @module frontend/src/app/app/sase-templates/page
 * @description SASE artifact templates viewer and generator
 * @sdlc SDLC 6.0.3 Universal Framework - SASE Integration
 * @status Sprint 151 - SASE Artifacts Enhancement
 */

"use client";

import { useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";

// SVG Icons
function DocumentIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
      className={className}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"
      />
    </svg>
  );
}

function ClipboardIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
      className={className}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M15.666 3.888A2.25 2.25 0 0013.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 01-.75.75H9a.75.75 0 01-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 01-2.25 2.25H6.75A2.25 2.25 0 014.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 011.927-.184"
      />
    </svg>
  );
}

function ChatBubbleIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
      className={className}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z"
      />
    </svg>
  );
}

function CheckCircleIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
      className={className}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
  );
}

function CodeBracketIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
      className={className}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5"
      />
    </svg>
  );
}

function ArrowDownTrayIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
      className={className}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3"
      />
    </svg>
  );
}

// SASE Template definitions
const SASE_TEMPLATES = [
  {
    id: "agents-md",
    name: "AGENTS.md",
    description: "Industry-standard AI guidance file for project context",
    createdBy: "SE4H (Human)",
    purpose: "Configure AI agent behavior and project conventions",
    badge: "Foundation",
    badgeVariant: "default" as const,
    icon: CodeBracketIcon,
    template: `# AGENTS.md

## Project Context
<!-- Describe what you're building and why it matters -->
Project Name: [Your Project Name]
Description: [Brief description of the project]
Business Context: [Why this project exists and what problem it solves]

## Architecture
<!-- Describe your tech stack and key patterns -->
- **Framework**: [e.g., FastAPI, React, Django]
- **Database**: [e.g., PostgreSQL, MongoDB]
- **Key Patterns**: [e.g., Clean Architecture, CQRS]

## Code Standards
<!-- Define coding conventions and best practices -->
- **Language**: [e.g., Python 3.11+, TypeScript 5.0+]
- **Style Guide**: [Link to style guide or inline rules]
- **Testing**: [Required coverage, testing patterns]

## Current Sprint
<!-- What the team is working on now -->
Sprint Goal: [Sprint objective]
Key Tasks:
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

## Critical Rules
<!-- Non-negotiable rules for AI agents -->
1. [Rule 1 - e.g., Never modify database schema without approval]
2. [Rule 2 - e.g., All API changes require OpenAPI spec update]
3. [Rule 3 - e.g., Security-sensitive code requires CRP]
`,
  },
  {
    id: "crp",
    name: "CRP - Consultation Request Protocol",
    description: "Escalate uncertainty to human for high-risk decisions",
    createdBy: "SE4A (Agent)",
    purpose: "Request human consultation when AI is uncertain",
    badge: "Governance",
    badgeVariant: "destructive" as const,
    icon: ChatBubbleIcon,
    template: `# Consultation Request Protocol (CRP)

## Request Information
- **Request ID**: CRP-[AUTO-GENERATED]
- **Created By**: [Agent Name/ID]
- **Created At**: [Timestamp]
- **Priority**: [Low | Medium | High | Urgent]
- **Required Expertise**: [Security | Database | API | Architecture | Concurrency | General]

## Question
<!-- What specific decision needs human input? -->
[Clearly state the question that requires human decision]

## Context
<!-- Background information the reviewer needs -->
### Current Situation
[Describe what's happening and why this question arose]

### Relevant Files
- \`path/to/file1.py\` - [Brief description]
- \`path/to/file2.ts\` - [Brief description]

### Risk Analysis
- **Impact**: [High | Medium | Low]
- **Reversibility**: [Easy | Moderate | Difficult]
- **Affected Systems**: [List systems/components]

## Options Considered
### Option A: [Name]
- **Description**: [What this option entails]
- **Pros**: [Benefits of this approach]
- **Cons**: [Drawbacks or risks]
- **Effort**: [Estimated effort]

### Option B: [Name]
- **Description**: [What this option entails]
- **Pros**: [Benefits of this approach]
- **Cons**: [Drawbacks or risks]
- **Effort**: [Estimated effort]

## Agent Recommendation
**Recommended Option**: [Option A | Option B | Need More Input]

**Rationale**: [Why the agent recommends this option]

## Impact Assessment
- **If Option A**: [Consequences]
- **If Option B**: [Consequences]
- **If No Decision**: [What happens if we don't decide]

---
## Resolution (To be filled by reviewer)
- **Decision**: [Pending]
- **Selected Option**: [TBD]
- **Reviewer Notes**: [TBD]
- **Resolved At**: [TBD]
`,
  },
  {
    id: "mrp",
    name: "MRP - Merge-Readiness Pack",
    description: "5-point evidence package for code review",
    createdBy: "SE4A (Agent)",
    purpose: "Structured evidence for merge decision",
    badge: "Evidence",
    badgeVariant: "secondary" as const,
    icon: ClipboardIcon,
    template: `# Merge-Readiness Pack (MRP)

## MRP Information
- **MRP ID**: MRP-[AUTO-GENERATED]
- **PR/MR Number**: #[PR_NUMBER]
- **Created By**: [Agent Name/ID]
- **Created At**: [Timestamp]

---

## 1. What Changed
<!-- Summary of code changes -->
### Files Modified
| File | Change Type | LOC |
|------|-------------|-----|
| \`path/to/file1.py\` | Modified | +50/-10 |
| \`path/to/file2.ts\` | Added | +120/0 |

### Change Summary
[High-level description of what was changed]

### Key Modifications
- [Modification 1]
- [Modification 2]
- [Modification 3]

---

## 2. Why Changed
<!-- Alignment with requirements -->
### Requirement Reference
- **Issue/Ticket**: #[ISSUE_NUMBER]
- **User Story**: [As a X, I want Y, so that Z]

### Business Alignment
[How these changes align with business requirements]

### Acceptance Criteria Met
- [x] Criteria 1
- [x] Criteria 2
- [x] Criteria 3

---

## 3. How Tested
<!-- Test results and coverage -->
### Test Summary
| Test Type | Total | Passed | Failed | Coverage |
|-----------|-------|--------|--------|----------|
| Unit | [X] | [X] | 0 | [X]% |
| Integration | [X] | [X] | 0 | [X]% |
| E2E | [X] | [X] | 0 | N/A |

### Test Evidence
\`\`\`
[Test output or summary]
\`\`\`

### Manual Testing
- [ ] Tested locally
- [ ] Tested in staging
- [ ] Reviewed with stakeholder

---

## 4. Risk Assessment
<!-- Potential issues identified -->
### Risk Matrix
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| [Risk 1] | Low | Medium | [Mitigation] |
| [Risk 2] | Medium | Low | [Mitigation] |

### Security Considerations
- [ ] SAST scan passed
- [ ] No hardcoded secrets
- [ ] Input validation implemented

### Performance Impact
[Expected performance impact, if any]

---

## 5. Rollback Plan
<!-- How to revert if needed -->
### Rollback Steps
1. [Step 1 - e.g., Revert commit]
2. [Step 2 - e.g., Run database rollback]
3. [Step 3 - e.g., Clear cache]

### Rollback Time Estimate
[Estimated time to complete rollback]

### Data Recovery
[Steps to recover any data if needed]

---

## Agent Confidence
- **Overall Confidence**: [High | Medium | Low]
- **Recommended Action**: [Ready to Merge | Needs Review | Needs Changes]
`,
  },
  {
    id: "vcr",
    name: "VCR - Version Controlled Resolution",
    description: "Approval record with audit trail",
    createdBy: "SE4H (Human)",
    purpose: "Record human approval decisions",
    badge: "Audit",
    badgeVariant: "outline" as const,
    icon: CheckCircleIcon,
    template: `# Version Controlled Resolution (VCR)

## VCR Information
- **VCR ID**: VCR-[AUTO-GENERATED]
- **Related MRP**: MRP-[ID]
- **Related PR/MR**: #[PR_NUMBER]
- **Project**: [Project Name]
- **Created At**: [Timestamp]

---

## Decision
**Status**: [ ] APPROVED | [ ] REJECTED | [ ] NEEDS_CHANGES

---

## MRP Review Summary
<!-- Summary of the Merge-Readiness Pack review -->

### What Changed
[Brief summary of changes from MRP]

### Test Results
- Unit Tests: [PASS/FAIL]
- Integration Tests: [PASS/FAIL]
- Coverage: [X]%

### Risk Assessment
[Summary of identified risks]

---

## Review Findings
<!-- Detailed review feedback -->

### Code Quality
- [ ] Follows project conventions
- [ ] No obvious bugs
- [ ] Properly documented
- [ ] No security vulnerabilities

### Business Alignment
- [ ] Meets acceptance criteria
- [ ] Aligns with user story
- [ ] No scope creep

### Additional Observations
[Any other observations from the review]

---

## Conditions for Approval
<!-- Any conditions that must be met -->
- [ ] [Condition 1 - e.g., Fix failing test]
- [ ] [Condition 2 - e.g., Update documentation]
- [ ] [Condition 3 - e.g., Add error handling]

---

## Approval Chain
<!-- For sensitive changes, may require multiple approvals -->

### Primary Approver
- **Name**: [Approver Name]
- **Role**: [Tech Lead | Senior Dev | CTO]
- **Decision**: [Approved | Rejected | Abstain]
- **Timestamp**: [When decision was made]
- **Signature**: [Digital signature or approval token]

### Secondary Approver (if required)
- **Name**: [Approver Name]
- **Role**: [Role]
- **Decision**: [Pending]
- **Timestamp**: [TBD]

---

## Resolution Notes
<!-- Additional context for the decision -->
[Why this decision was made, any concerns, follow-up items]

---

## Audit Trail
| Timestamp | Action | Actor | Details |
|-----------|--------|-------|---------|
| [Timestamp] | VCR Created | [Name] | Initial creation |
| [Timestamp] | Review Started | [Name] | MRP review began |
| [Timestamp] | Decision Made | [Name] | [Decision details] |

---

**Document Status**: [DRAFT | PENDING_APPROVAL | APPROVED | REJECTED]
**Last Modified**: [Timestamp]
`,
  },
];

// Maturity levels
const MATURITY_LEVELS = [
  {
    level: "L0",
    name: "Tool-Assisted",
    description: "Ad-hoc prompts, no structured artifacts",
    artifacts: [],
  },
  {
    level: "L1",
    name: "Agent-Assisted",
    description: "Basic agent collaboration with minimal governance",
    artifacts: ["AGENTS.md", "MRP", "VCR"],
  },
  {
    level: "L2",
    name: "Structured Agentic",
    description: "Full SASE workflow with consultation protocol",
    artifacts: ["AGENTS.md", "CRP", "MRP", "VCR"],
  },
  {
    level: "L3",
    name: "Lifecycle Agentic",
    description: "Advanced with Planning Mode and Dynamic Context",
    artifacts: ["All + Planning Mode + Dynamic Context"],
  },
];

export default function SASETemplatesPage() {
  const [selectedTemplate, setSelectedTemplate] = useState<(typeof SASE_TEMPLATES)[0] | null>(null);
  const [showCopyModal, setShowCopyModal] = useState(false);
  const [editedTemplate, setEditedTemplate] = useState("");
  const [copiedMessage, setCopiedMessage] = useState<string | null>(null);

  const showCopiedMessage = (message: string) => {
    setCopiedMessage(message);
    setTimeout(() => setCopiedMessage(null), 2000);
  };

  const handleViewTemplate = (template: (typeof SASE_TEMPLATES)[0]) => {
    setSelectedTemplate(template);
    setEditedTemplate(template.template);
    setShowCopyModal(true);
  };

  const handleCopyToClipboard = () => {
    navigator.clipboard.writeText(editedTemplate);
    showCopiedMessage(`${selectedTemplate?.name} template copied to clipboard!`);
  };

  const handleDownload = () => {
    if (!selectedTemplate) return;
    const blob = new Blob([editedTemplate], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${selectedTemplate.id}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showCopiedMessage(`${selectedTemplate.name} template downloaded!`);
  };

  return (
    <div className="container mx-auto py-6 space-y-8">
      {/* Copied Message Notification */}
      {copiedMessage && (
        <div className="fixed top-4 right-4 z-50 bg-green-600 text-white px-4 py-2 rounded-lg shadow-lg animate-pulse">
          {copiedMessage}
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">SASE Templates</h1>
          <p className="text-muted-foreground mt-1">
            Software Agentic Software Engineering artifact templates for human-agent collaboration
          </p>
        </div>
        <Badge variant="secondary" className="text-sm">
          SDLC 6.0.3
        </Badge>
      </div>

      {/* Info Banner */}
      <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950/20 dark:to-indigo-950/20 border-blue-200 dark:border-blue-800">
        <CardContent className="py-4">
          <div className="flex items-start gap-4">
            <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
              <DocumentIcon className="h-6 w-6 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <h3 className="font-semibold text-blue-900 dark:text-blue-100">
                SASE Framework Overview
              </h3>
              <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                SASE (Software Agentic Software Engineering) defines structured artifacts for
                AI-human collaboration. Use AGENTS.md for AI guidance, CRP for escalations, MRP for
                merge evidence, and VCR for approvals.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Content */}
      <Tabs defaultValue="templates" className="space-y-6">
        <TabsList>
          <TabsTrigger value="templates">Templates</TabsTrigger>
          <TabsTrigger value="maturity">Maturity Levels</TabsTrigger>
          <TabsTrigger value="workflow">Workflow</TabsTrigger>
        </TabsList>

        {/* Templates Tab */}
        <TabsContent value="templates" className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2">
            {SASE_TEMPLATES.map((template) => {
              const IconComponent = template.icon;
              return (
                <Card key={template.id} className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-muted rounded-lg">
                          <IconComponent className="h-5 w-5" />
                        </div>
                        <div>
                          <CardTitle className="text-lg">{template.name}</CardTitle>
                          <Badge variant={template.badgeVariant} className="mt-1">
                            {template.badge}
                          </Badge>
                        </div>
                      </div>
                    </div>
                    <CardDescription className="mt-2">{template.description}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex items-center gap-2 text-sm">
                        <span className="text-muted-foreground">Created by:</span>
                        <span className="font-medium">{template.createdBy}</span>
                      </div>
                      <div className="text-sm text-muted-foreground">{template.purpose}</div>
                      <div className="flex gap-2 pt-2">
                        <Button
                          variant="default"
                          size="sm"
                          onClick={() => handleViewTemplate(template)}
                        >
                          <DocumentIcon className="h-4 w-4 mr-2" />
                          View Template
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            navigator.clipboard.writeText(template.template);
                            showCopiedMessage(`${template.name} template copied!`);
                          }}
                        >
                          <ClipboardIcon className="h-4 w-4 mr-2" />
                          Quick Copy
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </TabsContent>

        {/* Maturity Levels Tab */}
        <TabsContent value="maturity" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Agentic Maturity Levels</CardTitle>
              <CardDescription>
                Progress through maturity levels to maximize AI-human collaboration effectiveness
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {MATURITY_LEVELS.map((level, index) => (
                  <div
                    key={level.level}
                    className={`p-4 rounded-lg border ${
                      index === 2
                        ? "border-primary bg-primary/5"
                        : "border-border"
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <Badge variant={index === 2 ? "default" : "outline"}>
                            {level.level}
                          </Badge>
                          <h3 className="font-semibold">{level.name}</h3>
                          {index === 2 && (
                            <Badge variant="secondary" className="text-xs">
                              Recommended
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground mt-1">
                          {level.description}
                        </p>
                      </div>
                    </div>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {level.artifacts.length > 0 ? (
                        level.artifacts.map((artifact) => (
                          <Badge key={artifact} variant="secondary" className="text-xs">
                            {artifact}
                          </Badge>
                        ))
                      ) : (
                        <span className="text-xs text-muted-foreground">
                          No structured artifacts
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Workflow Tab */}
        <TabsContent value="workflow" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>SASE Workflow</CardTitle>
              <CardDescription>
                Standard workflow for AI-human collaboration using SASE artifacts
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Workflow Diagram */}
                <div className="p-6 bg-muted rounded-lg">
                  <pre className="text-sm overflow-x-auto">
                    {`
┌─────────────────────────────────────────────────────────────────────┐
│               SASE WORKFLOW (SDLC 6.0.3)                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Human                          Agent                               │
│    │                              │                                 │
│    │─── AGENTS.md (repo) ────────▶│  (AI reads conventions)        │
│    │                              │                                 │
│    │─── GitHub Issue/Task ───────▶│  (Task specification)          │
│    │                              │                                 │
│    │◀── Dynamic Overlay ─────────│  (Context via PR comment)       │
│    │                              │                                 │
│    │                    [Execute Task]                              │
│    │                              │                                 │
│    │◀── CRP (if uncertain) ──────│  (Escalate to human)           │
│    │                              │                                 │
│    │─── Answer CRP ──────────────▶│                                │
│    │                              │                                 │
│    │                    [Complete]                                  │
│    │                              │                                 │
│    │◀── MRP (5-point evidence) ──│  (Merge readiness)             │
│    │                              │                                 │
│    │─── VCR (Approve/Reject) ────▶│  (Human decision)              │
│    │                              │                                 │
│    ├── GitHub Check ─────────────▶│  (Enforcement)                 │
│    │                              │                                 │
└─────────────────────────────────────────────────────────────────────┘`}
                  </pre>
                </div>

                {/* Step by Step */}
                <div className="space-y-4">
                  <h3 className="font-semibold">Step-by-Step Process</h3>
                  <div className="grid gap-4">
                    {[
                      {
                        step: 1,
                        title: "Setup AGENTS.md",
                        description:
                          "Create AGENTS.md in your repository with project context, architecture, and coding standards. This guides all AI agents working on your project.",
                      },
                      {
                        step: 2,
                        title: "Assign Task",
                        description:
                          "Create a GitHub issue or task. The AI agent reads AGENTS.md and task context to understand requirements.",
                      },
                      {
                        step: 3,
                        title: "CRP (If Needed)",
                        description:
                          "If the agent encounters uncertainty or high-risk decisions, it creates a CRP to escalate to humans for consultation.",
                      },
                      {
                        step: 4,
                        title: "Execute & Generate MRP",
                        description:
                          "Agent completes the task and generates an MRP with 5-point evidence: What Changed, Why, How Tested, Risks, Rollback Plan.",
                      },
                      {
                        step: 5,
                        title: "Human Review & VCR",
                        description:
                          "Human reviews the MRP and creates a VCR with their approval decision. This creates an audit trail for all changes.",
                      },
                    ].map((item) => (
                      <div key={item.step} className="flex gap-4">
                        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                          {item.step}
                        </div>
                        <div>
                          <h4 className="font-medium">{item.title}</h4>
                          <p className="text-sm text-muted-foreground">{item.description}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Template View/Edit Modal */}
      <Dialog open={showCopyModal} onOpenChange={setShowCopyModal}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle>{selectedTemplate?.name} Template</DialogTitle>
            <DialogDescription>
              {selectedTemplate?.description}. Edit the template to customize for your project.
            </DialogDescription>
          </DialogHeader>
          <div className="flex-1 overflow-auto">
            <Textarea
              value={editedTemplate}
              onChange={(e) => setEditedTemplate(e.target.value)}
              className="min-h-[400px] font-mono text-sm"
            />
          </div>
          <DialogFooter className="flex gap-2">
            <Button variant="outline" onClick={handleDownload}>
              <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
              Download
            </Button>
            <Button onClick={handleCopyToClipboard}>
              <ClipboardIcon className="h-4 w-4 mr-2" />
              Copy to Clipboard
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
