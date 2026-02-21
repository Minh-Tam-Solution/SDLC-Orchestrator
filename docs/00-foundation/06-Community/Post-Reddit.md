# Reddit Posts — Multi-Subreddit Strategy

**Platform**: Reddit
**Timing**: Week 1 Wednesday (r/programming), Week 3 Tuesday (r/devops), Week 3 Thursday (r/softwarearchitecture)
**Important**: Spread across weeks to avoid Reddit link-spam detection. Never cross-post multiple subreddits the same day.
**Target**: Developer community, DevOps engineers, software architects

---

## Post 1: r/programming (Week 1)

### Title

```
We tested 5 multi-agent AI coding tools. They were fast — but without structure, speed just amplified our mistakes. So we built an agent orchestrator with SDLC role discipline.
```

### Body

My team builds enterprise software in Vietnam. Over the past 8 months, we tested five multi-agent tools for AI-assisted development: TinyClaw, OpenClaw, NanoBot, PicoClaw, and ZeroClaw.

They were incredibly fast. But we kept hitting the same wall:

- AI agents generated code with no audit trail
- No structured review — just "looks good, ship it"
- When things broke in production, we couldn't trace back to which agent made which decision
- One project (NQH-Bot — an AI-Powered WFM platform for Vietnamese F&B market) ended up with 679 mock implementations and 78% production failure rate

The root issue wasn't the AI tools. It was the lack of governance around them.

So we built **TinySDLC** — a minimal agent orchestrator that adds SDLC role discipline to AI coding.

**What TinySDLC is NOT:**
- Not a new AI model
- Not a replacement for Claude/Cursor/Copilot
- Not a CI/CD system or SAST scanner

**What TinySDLC is:**
- A role-constrained multi-agent protocol
- A local-first orchestrator with zero infrastructure
- A structural enforcement layer for AI workflows

It doesn't replace AI tools. It structures how they collaborate:

- 8 agent roles (researcher, pm, architect, coder, reviewer, tester, devops, pjm)
- Separation of duties (coder can't self-approve, reviewer can't be bypassed)
- Structured handoffs via `@agent: message` mentions
- Security hardening (credential scrubbing, env scrubbing, shell guards)
- Multi-channel (Discord, Telegram, WhatsApp, Zalo)
- File-based queue, zero external dependencies

Local-first. MIT licensed.

The governance methodology (Spec → Gate → Evidence → Approval) is documented separately in **MTS-SDLC-Lite** — pure documentation (templates, playbooks, processes) that works with any AI tool. TinySDLC provides the structure; MTS-SDLC-Lite defines what to govern. Both MIT.

This came from 12 iterations of our internal SDLC framework, tested across 5 production projects.

- TinySDLC (code): https://github.com/Minh-Tam-Solution/tinysdlc
- MTS-SDLC-Lite (methodology): https://github.com/Minh-Tam-Solution/MTS-SDLC-Lite

Happy to answer questions about what worked, what didn't, and where we think AI governance is heading.

---

## Post 2: r/devops (Week 2)

### Title

```
Built a minimal agent orchestrator for AI coding — 8 SDLC roles, separation of duties, security hardening. Here's the architecture.
```

### Body

If you're using AI coding assistants (Cursor, Claude Code, Copilot) in your team, you've probably noticed: they're great at generating code, terrible at governance.

No structure. No role separation. No traceability. When something breaks in production, good luck figuring out which agent made which decision.

We built **TinySDLC** — a minimal agent orchestrator that adds SDLC discipline to AI coding:

```
┌──────────────────────────────────────────────────────────┐
│               TinySDLC Agent Orchestrator                 │
│                                                           │
│  Researcher → Architect → Coder → Reviewer → Tester      │
│                                                           │
│  Role isolation · Structured handoffs · @mention routing  │
│  Credential scrubbing · Shell guards · Event logging      │
└──────────────────────────────────────────────────────────┘
```

It orchestrates 8 agent roles: researcher, pm, architect, coder, reviewer, tester, devops, pjm. Each role has defined tool permissions, system prompts, and scope constraints. Separation of duties is structural — the coder can't self-approve, the reviewer can't be bypassed.

Key design decisions:
- **Local-first**: File-based queue, zero external dependencies (no Redis, no Postgres)
- **Multi-channel**: Discord, Telegram, WhatsApp, Zalo — agents work where your team works
- **Security hardening**: Credential scrubbing, env scrubbing, input sanitization, shell guards
- **Event logging**: Every agent action logged with correlation IDs for traceability

Background: We tested 5 different multi-agent tools internally. Speed was never the problem. Governance was. This emerged from 12 iterations of our SDLC framework across 5 production projects.

MIT licensed: https://github.com/Minh-Tam-Solution/tinysdlc
Methodology docs: https://github.com/Minh-Tam-Solution/MTS-SDLC-Lite

How are you handling AI governance in your DevOps pipeline?

---

## Post 3: r/softwarearchitecture (Week 2)

### Title

```
Architecture decision: How we structured a governance layer for multi-agent AI development
```

### Body

We needed to solve a specific architecture problem: how do you add structure to a workflow where multiple AI agents (coder, reviewer, tester) collaborate on code generation?

The constraints:
1. Must work with any AI coding tool (not locked to one vendor)
2. Must run locally with zero external dependencies (no Redis, no Postgres, no cloud)
3. Must log every agent action for traceability
4. Must enforce separation of duties (coder can't self-approve, reviewer can't be bypassed)

Our solution is **TinySDLC** — a minimal agent orchestrator with this architecture:

```
                    ┌──────────────────────┐
                    │   SDLC Role Engine    │
                    │  (8 roles, isolation, │
                    │   structured handoffs)│
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
        ┌─────┴─────┐   ┌─────┴─────┐   ┌─────┴─────┐
        │ Researcher │   │   Coder   │   │ Reviewer  │
        │   Agent    │   │   Agent   │   │   Agent   │
        └───────────┘   └───────────┘   └───────────┘
              │                │                │
              └────────────────┼────────────────┘
                               │
                    ┌──────────┴───────────┐
                    │   Any AI Provider    │
                    │  (Claude, GPT, etc.) │
                    └──────────────────────┘
```

Key architectural decisions:
- **Role-first, not tool-first**: 8 defined SDLC roles — each has scoped tool permissions, system prompts, and handoff rules. Roles are the contract; AI providers are swappable.
- **File-based queue**: Messages flow through `incoming/` → `processing/` → `outgoing/` directories. Zero external dependencies — no Redis, no database. Simple, inspectable, debuggable.
- **Security hardening**: Credential scrubbing (7 patterns), environment variable scrubbing, input sanitization (12 injection patterns), shell guards (8 deny patterns + path traversal). Learned from testing ZeroClaw.
- **Multi-channel routing**: Discord, Telegram, WhatsApp, Zalo — `@agent: message` mention parsing routes to the right role regardless of channel.

This emerged from extracting the minimal viable agent orchestration layer from a larger internal system into a standalone OSS tool. TinySDLC is a complete, self-contained tool — role discipline with zero infrastructure.

MIT licensed: https://github.com/Minh-Tam-Solution/tinysdlc

The methodology behind the architecture is documented separately in MTS-SDLC-Lite: https://github.com/Minh-Tam-Solution/MTS-SDLC-Lite

Would love feedback on the architecture choices, especially around the protocol-first approach vs. more flexible agent topologies.

---

## Reddit Rules Compliance

- [x] No self-promotional language ("we built" not "check out our amazing")
- [x] Leads with the problem, not the product
- [x] Includes genuine question to invite discussion
- [x] Technical depth appropriate for each subreddit
- [x] No link-only posts — substantial body text
- [x] Follows each subreddit's posting guidelines
- [x] Account should have prior engagement (not a fresh account posting links)

## Pre-Engagement Requirement (CRITICAL — Do NOT Skip)

Reddit will shadow-remove posts from accounts without prior engagement. Before posting to any subreddit:

1. **2-3 weeks before launch**: Comment genuinely on 3-4 threads about AI governance, multi-agent tools, or coding agents in each target subreddit
2. **1 week before**: Upvote and reply to existing discussions (build karma in the subreddit)
3. **After posting**: Reply to >10 comments within the first 6 hours. Reddit's algorithm rewards active discussion.

If the CEO account has no prior Reddit history, consider having a team member with established Reddit presence post instead (with CEO credited in the body text).
