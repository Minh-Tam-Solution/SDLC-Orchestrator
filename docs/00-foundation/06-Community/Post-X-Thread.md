# X (Twitter) Thread — Technical Thread

**Platform**: X / Twitter
**Format**: Thread (13 tweets)
**Timing**: Week 2 Wednesday
**Target**: AI dev ecosystem, OSS community, coding agent users
**Language**: English

---

## Thread

### Tweet 1 (Hook)

```
679 mock implementations. 78% production failure.

We tested 5 multi-agent AI coding tools across 5 production projects.

They were fast. But without structure, speed just amplified our mistakes.

So we built an open-source governance layer. Here's the thread:

🧵
```

### Tweet 2 (The Problem)

```
The tools weren't broken. Our process was.

AI agents generated code with:
- No audit trail
- No structured review
- No separation of duties
- No traceability

When production broke, we couldn't trace which agent made which decision.
```

### Tweet 3 (What We Tried)

```
5 multi-agent tools tested in 8 months:

• TinyClaw — @mention routing
• OpenClaw — lane-based queue + failover
• NanoBot — tool isolation + shell guards
• PicoClaw — single-agent wrapper
• ZeroClaw — output scrubbing + classification

Each solved a piece. None solved governance.
```

### Tweet 4 (The Gap)

```
The fundamental question none of them answered:

How do you ensure AI-generated code meets quality standards BEFORE it enters your codebase?

Not after. Not during CI. During generation.

That's what we built.
```

### Tweet 5 (The Solution)

```
So we built TinySDLC — a minimal agent orchestrator with SDLC role discipline.

Not a new AI model.
Not a replacement for Claude/Cursor/Copilot.
Not a CI/CD system.

It's a structural enforcement layer for how AI agents collaborate.

MIT licensed. Zero external dependencies.
```

### Tweet 6 (Architecture)

```
8 agent roles, each with scoped permissions:

Researcher → PM → Architect → Coder → Reviewer → Tester → DevOps → PJM

Key constraint: Coder can't self-approve. Reviewer can't be bypassed.

Separation of duties is structural, not optional.
```

### Tweet 7 (How It Works)

```
How agents communicate:

@researcher: "Investigate auth patterns for multi-tenant SaaS"
@architect: "Design the authentication flow"
@coder: "Implement JWT + OAuth service"
@reviewer: "Review the auth implementation"

Structured handoffs. Explicit routing. No silent pass-through.
```

### Tweet 8 (Security)

```
Security hardening (from testing ZeroClaw):

• 7 credential scrubbing patterns
• Environment variable scrubbing
• 12 injection patterns blocked
• 8 shell deny patterns + path traversal

Output is scrubbed BEFORE it reaches the channel or LLM context.
```

### Tweet 9 (Design Decisions)

```
Key design decisions:

1. Local-first: File-based queue (incoming → processing → outgoing). No Redis. No Postgres.

2. Multi-channel: Discord, Telegram, WhatsApp, Zalo — agents work where your team works.

3. Protocol-first: Roles are contracts. AI providers are swappable.
```

### Tweet 10 (The Methodology)

```
TinySDLC is the tool. But governance needs a methodology.

MTS-SDLC-Lite is the playbook:

Spec → Gate → Evidence → Approval → Feedback loop

Templates, playbooks, processes. Tool-agnostic — works with any AI tool.

Also MIT.
```

### Tweet 11 (What It Doesn't Do)

```
What TinySDLC does NOT do:

• Does not guarantee code quality (that's on your prompts + provider)
• Does not replace CI/CD or SAST
• Does not eliminate bad architecture decisions
• Adds structure, not intelligence

Governance is a constraint system, not a magic layer.
```

### Tweet 12 (Backstory)

```
This came from a 55-year-old CEO who re-learned coding after 30 years.

Last coded 1994 (Assembler, Borland C++).

Wrote TinySDLC during Lunar New Year — using the AI tools he was learning to govern.

12 iterations. 5 production projects. Real pain, real patterns.
```

### Tweet 13 (CTA)

```
Both repos are MIT licensed:

TinySDLC (code):
github.com/Minh-Tam-Solution/tinysdlc

MTS-SDLC-Lite (methodology):
github.com/Minh-Tam-Solution/MTS-SDLC-Lite

AI is fast. Governance must be faster.

Feedback, criticism, and PRs welcome.
```

---

## X/Twitter Thread Best Practices

- [x] Tweet 1 is a standalone hook (works even if no one reads the thread)
- [x] Each tweet is under 280 characters
- [x] Thread numbered implicitly by reply chain (no "1/12" — X handles this)
- [x] Technical content first, backstory near the end
- [x] No marketing language — factual, direct
- [x] Real numbers (679 mocks, 78% failure, 12 versions, 5 projects, 7 patterns)
- [x] CTA is the final tweet with direct GitHub links
- [x] "What it is NOT" included for credibility (Tweet 4 + Tweet 10)
- [x] No Orchestrator commercial mention in thread body
- [x] Thread is self-contained — each tweet can be retweeted independently

## Timing Notes

- **Best posting time**: 8-10 AM US Eastern (9-11 PM Vietnam)
- **Best days**: Tuesday, Wednesday, Thursday
- **Thread publishing**: Use X thread composer or Typefully to schedule all tweets as a thread
- **Engagement**: Reply to comments within 2 hours (X algorithm rewards fast engagement)
- **Retweet strategy**: Quote-tweet Tweet 1 from company account after 4 hours

## Hashtag Strategy

Do NOT put hashtags in the thread body — it looks spammy on X.

After posting the thread, add a single reply at the end:

```
Tags for discoverability:

#OpenSource #AIGovernance #CodingAgents #SDLC #DevTools #MIT
```

## Expected Questions & Prepared Answers

**Q: "How is this different from AGENTS.md?"**
A: AGENTS.md tells agents what to do. TinySDLC enforces who can do what — role isolation, separation of duties, structured handoffs. Plus security hardening that static config files can't provide.

**Q: "Why not just use CI/CD gates?"**
A: CI/CD catches problems after code is written. TinySDLC structures the process during code generation — reviewer sees every handoff, tester is required before deploy. Role discipline in the AI workflow, not post-hoc validation.

**Q: "What's the enterprise version?"**
A: SDLC Orchestrator — automated gate enforcement, SHA256 evidence vault, OPA policies, SSO, multi-tenant. TinySDLC is the community starting point. MIT, no strings.
