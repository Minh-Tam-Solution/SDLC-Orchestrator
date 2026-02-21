# Hacker News — Show HN Post

**Platform**: Hacker News (news.ycombinator.com)
**Format**: Show HN (strict conventions — no marketing)
**Timing**: Week 1 Tuesday, 9-11PM VN time (8-10AM US Eastern)
**Target**: Deep technical audience, OSS enthusiasts

---

## Title

```
Show HN: TinySDLC – Agent orchestrator with SDLC role discipline for AI coding (MIT)
```

## Body

(Paste this into the HN text field — keep it short, HN penalizes long posts)

---

Problem: when multiple AI coding agents collaborate, there's no structure — no separation of duties, no handoff discipline, no traceability.

TinySDLC is a minimal agent orchestrator that adds SDLC role discipline to AI coding. 8 roles (researcher, architect, coder, reviewer, tester, etc.), each with isolated workspaces, scoped tool permissions, and enforced separation of duties. Coder can't self-approve. Reviewer can't be bypassed.

Design constraints: file-based queue (zero external dependencies), multi-channel (Discord, Telegram, WhatsApp, Zalo), security hardening (7 credential scrubbing patterns, 12 injection patterns blocked, 8 shell deny patterns).

Protocol-first: roles are contracts, AI providers are swappable.

Companion repo MTS-SDLC-Lite contains the governance methodology (Spec → Gate → Evidence → Approval) — templates, playbooks, processes. Both MIT.

Result of 12 iterations across 5 production projects.

GitHub: https://github.com/Minh-Tam-Solution/tinysdlc

Methodology docs: https://github.com/Minh-Tam-Solution/MTS-SDLC-Lite

Both MIT licensed. Feedback and criticism welcome.

---

## HN Rules Compliance Checklist

- [x] Title starts with "Show HN:"
- [x] Title ~84 chars (HN allows up to 256)
- [x] No exclamation marks or superlatives
- [x] Body is factual, not promotional
- [x] Describes what it does, why it exists
- [x] Includes direct GitHub link
- [x] No "revolutionary" / "game-changing" / "disrupting" language
- [x] Invites criticism ("Feedback and criticism welcome")
- [x] Under 200 words (HN sweet spot)

## Timing Notes

- **Best posting time**: 8-10 AM US Eastern (9-11 PM Vietnam)
- **Best days**: Tuesday, Wednesday, Thursday
- **Avoid**: Weekends, US holidays, major tech news days
- CEO should be available for 2-3 hours after posting to respond to comments
- HN comments are often critical — respond factually, never defensively

## Expected Questions & Prepared Answers

**Q: "How is this different from just using AGENTS.md?"**
A: AGENTS.md tells agents what to do. TinySDLC enforces who can do what — role isolation, separation of duties, structured handoffs. Plus security hardening (credential scrubbing, env scrubbing, shell guards) that AGENTS.md can't provide.

**Q: "Why not just use CI/CD gates?"**
A: CI/CD catches problems after code is written. TinySDLC structures the process during code generation — the reviewer role sees every handoff, the tester role is required before deployment. It's about role discipline in the AI workflow, not post-hoc validation.

**Q: "Is this just a chat router with agent labels?"**
A: It's an orchestrator with real constraints. Roles have isolated workspaces, scoped tool permissions, and enforced separation of duties. Security hardening (credential scrubbing, input sanitization, shell guards) came from testing 5 multi-agent tools in production. It's not just routing — it's discipline.

**Q: "What's the enterprise version?"**
A: SDLC Orchestrator is a separate commercial product with automated gate enforcement (OPA policies), SHA256 evidence vault, Semgrep SAST integration, multi-tenant, SSO. TinySDLC is the community starting point — role discipline with zero infrastructure, MIT, no strings.
