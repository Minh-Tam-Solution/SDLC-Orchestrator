# Dev.to Long-Form Technical Post

**Platform**: Dev.to (dev.to)
**Format**: Long-form technical article (~2000 words)
**Timing**: Week 2 Monday
**Target**: Developers interested in AI tooling, DevOps, software architecture
**SEO keywords**: AI governance, multi-agent, coding agents, SDLC, software development lifecycle

---

## Dev.to Frontmatter

```yaml
---
title: "How We Built a Governance Loop for AI Coding Agents"
published: true
description: "AI coding agents are fast. Without governance, they produce technical debt just as fast. Here's how we built a governance layer after testing 5 multi-agent tools across 5 production projects."
tags: ai, opensource, devops, softwareengineering
cover_image: # ACTION REQUIRED: Add architecture diagram image URL before Mar 3 (Week 2 Monday)
canonical_url: # Optional: link to blog if cross-posting
---
```

---

## Article Body

# How We Built a Governance Loop for AI Coding Agents

AI coding agents are fast. Claude Code, Cursor, Copilot — they can generate hundreds of lines in seconds. But here's the uncomfortable truth we learned after testing five different multi-agent tools across five production projects:

**Without governance, speed just amplifies mistakes.**

This is the story of how we built [TinySDLC](https://github.com/Minh-Tam-Solution/tinysdlc) — a minimal, open-source agent orchestrator that adds SDLC role discipline to AI coding. 8 roles, structured handoffs, separation of duties, security hardening — all local, zero external dependencies.

---

## The Real Starting Point: A Skeptical Team and a Non-Coding CEO

Before we talk about architecture, let me be honest about where this started.

In May 2025, I had a problem. My development team at MTS was slow to adopt AI coding tools. They were skeptical — and frankly, they had a point. They thought AI-generated code was full of bugs. "More time fixing than coding," they said. They used ChatGPT and Gemini individually for quick prompts, but had no team-wide process.

I'm a CEO. Not a professional software developer — at least, not for the past 30 years. The last time I wrote code was 1994: Assembler and Borland C++ for my graduation thesis, a graphics application for designing electronic circuit boards. Object-oriented programming deeply shaped how I think about systems. Then I moved into management and never looked back. My team knew that. And when I pushed for AI adoption, they were polite but unconvinced: *the boss isn't a real software engineer.*

I brought in experts. Ran a Claude Code workshop. The team was still slow to change.

So I made a decision: I would learn it myself.

I started with Python. Then free tools — LM Studio, Ollama with Continue.dev. Then paid — GitHub Copilot, Cursor, Claude Code. Small apps first. Then I moved to real enterprise platforms: Bflow ([bflow.vn](https://www.bflow.vn) — an ERP+BPM Platform for Vietnamese SMEs, built by my MTS team, launched Oct 2024), then evolving it into Bflow 2.0 (ERP+BPM+AI — Conversation-First with AI as a core pillar), and NQH-Bot (an AI-Powered Workforce Management platform for Vietnamese F&B market, at Nhat Quang Holding — my second startup).

---

## The Crisis: 679 Mocks and 78% Failure

NQH-Bot was an AI-Powered Workforce Management platform for Vietnamese F&B market — auto-scheduling, multi-tenant SaaS, regional compliance — at Nhat Quang Holding, my second startup. We were using AI coding tools heavily. The speed was incredible.

Then we deployed to production.

- 679 out of ~900 implementations were mock code (placeholder `// TODO: implement` patterns)
- 78% of production endpoints failed on real traffic
- 6 weeks of debugging to untangle what the AI had generated vs. what was actually working

The AI tools weren't broken. Our process was. We had no gates, no evidence capture, no structured review. The agents generated code, we skimmed it, and we shipped it.

My team's skepticism was validated — but for the wrong reason. The problem wasn't AI. The problem was **ungoverned AI**.

That crisis gave birth to what we now call the **Zero Mock Policy** — and eventually, to a complete governance framework.

---

## What We Tried First: Five Multi-Agent Tools

Over the next months, we experimented with different multi-agent orchestration approaches:

| Tool | What It Did | Why It Wasn't Enough |
|------|------------|---------------------|
| TinyClaw | @mention-based agent routing | No governance loop, just routing |
| OpenClaw | Lane-based message queue + failover | Great infra, no quality gates |
| NanoBot | Tool-context isolation + shell guards | Security focused, not governance focused |
| PicoClaw | Lightweight single-agent wrapper | Too simple for team workflows |
| ZeroClaw | Output scrubbing + query classification | Post-hoc safety, not pre-hoc governance |

Each tool solved a piece of the puzzle. But none of them answered the fundamental question:

> **How do you ensure AI-generated code meets quality standards before it enters your codebase?**

---

## The Architecture: Role Discipline + Structured Handoffs

TinySDLC's architecture is built on two principles: **separation of duties** and **structured handoffs**.

The methodology (MTS-SDLC-Lite) defines the governance loop:

```
┌────────────┐     ┌────────────┐     ┌────────────┐     ┌────────────┐
│    Spec     │────>│    Gate     │────>│  Evidence   │────>│  Approval  │
│  (Define)   │     │ (Validate)  │     │ (Capture)   │     │ (Sign-off) │
└────────────┘     └────────────┘     └────────────┘     └────────────┘
       ↑                                                        │
       └──────────────────── Feedback loop ────────────────────┘
```

TinySDLC enforces this loop through **role constraints**, not automated gates:

**Role isolation**: Each agent has a defined workspace, tool permissions, and scope. The coder can't approve its own output. The reviewer can't skip the tester. Separation of duties is structural, not optional.

**Structured handoffs**: Agents communicate through `@agent: message` mentions. Work flows from researcher → architect → coder → reviewer → tester with explicit handoff points. No silent pass-through.

**Event logging**: Every agent action is logged as a JSON event with correlation IDs — which agent did what, when, in response to what request. This gives you traceability, not just chat history:

```json
{
  "event": "handoff",
  "from_role": "coder",
  "to_role": "reviewer",
  "correlation_id": "conv-a1b2c3",
  "action": "submit_for_review",
  "timestamp": "2026-02-18T14:32:01Z",
  "message": "@reviewer: Auth service implementation ready for review"
}
```

**Human checkpoints**: The methodology defines when a human should review. TinySDLC provides the structure; your team provides the judgment.

> **Important distinction**: TinySDLC is a minimal agent orchestrator extracted from a larger internal system. It provides structure and role discipline — real governance with zero infrastructure. It's a complete, standalone tool, not a crippled version of something else.

---

## The 8 Agent Roles

TinySDLC defines 8 specialized roles, each with scoped permissions and responsibilities:

```
┌──────────────────────────────────────────────────────────┐
│                    Governance Layer                        │
│                                                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │Researcher│ │    PM    │ │   PJM    │ │ Architect│   │
│  │ (Explore)│ │(Require) │ │ (Track)  │ │ (Design) │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
│                                                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │  Coder   │ │ Reviewer │ │  Tester  │ │  DevOps  │   │
│  │(Generate)│ │ (Review) │ │  (Test)  │ │ (Deploy) │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

Each role has:
- **Defined tool permissions** (what the agent can access — isolated workspaces)
- **System prompt** (what the agent's responsibilities are)
- **Scope constraints** (what the agent is NOT allowed to do — enforced separation of duties)
- **Handoff responsibilities** (which role receives its output next)

This isn't about restricting AI. It's about giving structure to a multi-agent workflow so that a reviewer can't be bypassed, a coder can't self-approve, and every handoff is explicit.

---

## Key Design Decisions

### 1. Local-first, zero external dependencies

TinySDLC runs on your machine. File-based queue (incoming → processing → outgoing), no Redis, no Postgres, no cloud services. Install and run in under 5 minutes.

### 2. Multi-channel from day one

Discord, Telegram, WhatsApp, Zalo — your team works where they already are. Agents respond in the same channel. No context switching.

### 3. Security hardening built in

This came directly from our ZeroClaw experiments:
- **Credential scrubbing**: Agent output is scanned for leaked API keys, tokens, passwords before it reaches the channel
- **Environment variable scrubbing**: `.env` contents never appear in agent responses
- **Input sanitization**: 12 injection patterns blocked for external channel content
- **Shell guards**: 8 deny patterns + path traversal detection for any shell operations

### 4. Role constraints that enforce discipline

A reviewer can't approve their own code. A coder can't skip the review step. A tester can't deploy. These aren't suggestions — they're structural constraints in the agent definitions. This was a hard lesson from the NQH-Bot crisis: when governance is optional, it gets skipped.

---

## The Methodology: MTS-SDLC-Lite

TinySDLC is the tool. But governance needs more than code — it needs a methodology.

[MTS-SDLC-Lite](https://github.com/Minh-Tam-Solution/MTS-SDLC-Lite) is the community edition of our SDLC 6.1.0 framework. It's pure documentation:

- **Core concepts**: Design Thinking, Systems Thinking, 10-Stage Lifecycle
- **Roles and teams**: 4 team archetypes for different project sizes
- **Playbooks**: Step-by-step guides for common workflows
- **Templates**: Spec templates, gate checklists, evidence formats
- **Case studies**: Real examples from our production projects

It's tool-agnostic. Use it with Claude, GPT, Copilot, Cursor, or pen and paper. The methodology works regardless of which AI tool you choose.

---

## What We Learned

After 12 iterations of the framework and 5 production projects, here are our key takeaways:

1. **Governance is not overhead — it's insurance**. The time spent on gates and evidence capture pays back 10x when something breaks in production and you need to trace the root cause.

2. **AI doesn't need fewer rules — it needs better rules**. The agents are eager to follow structure. Give them clear constraints and they produce better output than with vague "be careful" instructions.

3. **Methodology outlives tools**. We've switched AI providers three times. The SDLC framework hasn't changed. Invest in your process, not your tool vendor.

4. **Not being an expert can be an advantage**. Professional developers have ingrained habits — "this is how we've always done it." As a non-coding CEO, I had no muscle memory to override. No legacy patterns to defend. I was ready to learn whatever was new, because everything was new. Sometimes the beginner's mind sees what the expert's mind filters out. We are always programming in our lives — with AI today, anyone with design thinking, systems thinking, and domain knowledge can quickly experiment and turn ideas into products.

5. **Start minimal**. TinySDLC is deliberately small. You don't need a full enterprise platform to start governing AI output. You need a loop: Spec → Gate → Evidence → Approval.

---

## What TinySDLC Does NOT Solve

Transparency matters more than polish. Here's what TinySDLC intentionally does not do:

- **It does not guarantee code quality.** It structures the workflow — the quality of output still depends on your AI provider and your prompts.
- **It does not replace CI/CD or SAST.** No automated test execution, no static analysis. Those belong in your pipeline, not your orchestrator.
- **It does not eliminate bad architecture decisions.** If your spec is wrong, governed agents will build the wrong thing — just more traceably.
- **It adds structure, not intelligence.** The agents are still AI. TinySDLC constrains how they interact, not what they think.

Governance is a constraint system, not a magic layer. TinySDLC makes multi-agent workflows auditable and disciplined — nothing more, nothing less.

---

## Get Started

```bash
# The tool
git clone https://github.com/Minh-Tam-Solution/tinysdlc.git
cd tinysdlc && npm install && npm run build
./tinysdlc.sh start    # Interactive setup wizard

# The methodology
git clone https://github.com/Minh-Tam-Solution/MTS-SDLC-Lite.git
```

Both repos are MIT licensed. Use them, fork them, improve them.

If you're building with AI coding agents and want to talk about governance approaches, find me on [LinkedIn](https://www.linkedin.com/in/the-tai-dang-a81bb710/) or open an issue on GitHub.

AI is fast. Governance must be faster.

— **Tai Dang**, CEO/Founder MTS & CEO Nhat Quang Holding

---

## Dev.to Publishing Checklist

- [x] Title is specific and searchable ("How We Built..." not "Introducing...")
- [x] Tags: ai, opensource, devops, softwareengineering (max 4 on Dev.to)
- [x] Cover image placeholder noted
- [x] Code blocks use proper syntax highlighting
- [x] Architecture diagrams are text-based (no external image dependencies)
- [x] ~2000 words (Dev.to sweet spot for technical content)
- [x] Real numbers included (679 mocks, 78% failure, 12 versions, 5 projects)
- [x] CTA at bottom with git clone commands
- [x] No marketing language — pure technical narrative
- [x] Cross-linking between TinySDLC and MTS-SDLC-Lite explained clearly
