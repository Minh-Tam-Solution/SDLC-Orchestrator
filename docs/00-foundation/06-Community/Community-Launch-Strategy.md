# Community Launch Strategy — TinySDLC & MTS-SDLC-Lite

**Version**: 1.0.0
**Date**: February 20, 2026
**Owner**: CEO (Tai Dang — CEO/Founder MTS & CEO Nhat Quang Holding) + CTO
**Status**: APPROVED — Ready to Execute
**Framework**: SDLC 6.1.0

---

## Executive Summary

Open-source launch of two MIT-licensed projects as the community gateway to the SDLC Orchestrator ecosystem:

- **TinySDLC** — Minimal governance layer for AI coding agents (code, tooling)
- **MTS-SDLC-Lite** — Community edition of the SDLC 6.1.0 methodology (docs, templates, processes)

**Core Message**: *"This is how we survived AI-driven development inside a real company."*

**Q2 2026 Target**: 1,000 GitHub stars across both repos.

---

## Product Positioning

### What Each Repo Is

| Project | What | License | Target | Relationship |
|---------|------|---------|--------|-------------|
| **TinySDLC** | Code — Minimal multi-agent governance engine | MIT | Developers using AI coding agents | The **tool** that enforces governance |
| **MTS-SDLC-Lite** | Docs — Community SDLC methodology & templates | MIT | Teams wanting structured dev process | The **methodology** that defines governance |
| **SDLC Orchestrator** | Platform — Enterprise governance control plane | Commercial | Enterprise teams 15-50+ engineers | The **platform** that scales governance |

### How They Relate

```
MTS-SDLC-Lite (methodology)    TinySDLC (tool)
       │                            │
       │  "What to govern"          │  "How to govern"
       │                            │
       └────────────┬───────────────┘
                    │
            SDLC 6.1.0 Framework
         (both are complete, standalone)
```

**Key narrative**: TinySDLC is the code. MTS-SDLC-Lite is the playbook. Together they give any team — from solo developer to 50-person engineering org — a governance foundation. Both are standalone, complete, and production-ready. SDLC Orchestrator is a separate commercial product — only mention it when directly asked.

**Launch positioning rule** (first 4 weeks): Do NOT position Orchestrator as "upgrade path." Earn community trust first. Frame: "TinySDLC is a minimal extract from a larger internal system." Orchestrator details only in response to direct questions.

---

## 3-Layer Distribution Strategy

### Layer 1: Core Developers (Week 1)

**Goal**: Get initial traction from developers who understand the pain of ungoverned AI coding.

| Date | Platform | Post File | Action |
|------|----------|-----------|--------|
| Feb 20 (Fri) | GitHub | `Post-GitHub-Announcement.md` | Pin repos, README polish, quickstart ≤5min |
| Feb 25 (Tue) | Hacker News | `Post-Hacker-News.md` | Show HN post — 9-11PM VN time (US morning) |
| Feb 26 (Wed) | Reddit | `Post-Reddit.md` | r/programming — problem-solving angle |
| Feb 27 (Thu) | LinkedIn | `Post-LinkedIn.md` | CEO personal narrative — Tet coding story |
| Feb 28 (Fri) | Facebook | `Post-Facebook.md` | CEO personal (Vietnamese-first) — VN tech community |

**Success Metrics (Week 1)**:
- 100+ GitHub stars
- 20+ HN points
- 5+ Reddit comments (engagement, not just upvotes)
- 50+ LinkedIn reactions
- 100+ Facebook reactions + 20+ shares

### Layer 2: Tech Leadership (Week 2)

**Goal**: Reach CTOs, VPs of Engineering, and tech leads with deeper technical content.

| Day | Platform | Post File | Action |
|-----|----------|-----------|--------|
| Mon | Dev.to | `Post-DevTo.md` | Long-form technical breakdown (2000 words) |
| Tue | Vietnam CTO Community | — | CTO Summit Slack, VietGlobal Founders |
| Wed | X (Twitter) | `Post-X-Thread.md` | Thread 10-15 tweets — "679 mocks. 78% failure. Here's what we built." |
| Thu | LinkedIn | — | Follow-up post: technical architecture deep-dive |
| Fri | — | — | Cross-compile engagement data, plan Week 3 |

**Success Metrics (Week 2)**:
- 300+ cumulative GitHub stars
- Dev.to: 2,000+ views, 50+ reactions
- 3+ inbound "how do I use this?" messages
- 1+ external blog mention or repost

### Layer 3: Amplification (Week 3)

**Goal**: Convert early interest into sustained community engagement.

| Day | Action | Details |
|-----|--------|---------|
| Mon | OSS contributor onboarding | Label `good-first-issue` on 10+ issues across both repos |
| Tue | Reddit r/devops | `Post-Reddit.md` Post 2 — architecture-focused angle |
| Wed | GitHub Discussions AMA | "Ask the CEO who re-learned coding at 55" |
| Thu | Reddit r/softwarearchitecture | `Post-Reddit.md` Post 3 — protocol-first design discussion |
| Fri | Product Hunt prep | Only if ≥300 stars + 3 testimonials — DO NOT launch prematurely |

**Week 4 (Sustained)**:

| Day | Action | Details |
|-----|--------|---------|
| Mon | r/selfhosted, r/opensource | Cross-post with community-appropriate angle |
| Tue | Contributor spotlight | Thank and highlight first external contributors |
| Wed | Technical Deep Dive #1 | Follow-up Dev.to or blog post (architecture decisions) |
| Fri | Week 4 review | Compile all metrics, plan Q2 community roadmap |

**Success Metrics (Week 3)**:
- 500+ cumulative GitHub stars
- 5+ external contributors (PRs or issues)
- 10+ good-first-issue labels created
- Product Hunt launch criteria met (or deferred to Week 5)

---

## GitHub README Checklist (Pre-Launch)

Both repos need these before any post goes live:

- [ ] Clear 1-sentence description at top of README
- [ ] "What is this?" section (3-4 sentences max)
- [ ] "Why this exists / What problem it solves / What it does NOT solve" section
- [ ] "How it relates to [other repo]" section
- [ ] Quickstart (≤5 min to first governance loop for TinySDLC)
- [ ] Architecture diagram (text-based, no external images)
- [ ] Contributing guide (CONTRIBUTING.md)
- [ ] License file (MIT)
- [ ] Demo GIF or screenshot placeholder
- [ ] GitHub Topics/Tags set correctly
- [ ] Pinned repo on org profile

---

## Contributor Surface Area (P0 — Must Complete Before Week 2)

Without contributor mechanisms, the repo will flatline after initial interest. These are required to sustain momentum:

### C-01: Good First Issues (Owner: CTO/DevOps — 10+ issues before Week 2)

Label `good-first-issue` on at least 10 issues across both repos:
- TinySDLC: Add channel adapter, improve error messages, add tests, documentation gaps
- MTS-SDLC-Lite: Template improvements, case study additions, translation PRs

### C-02: Public Roadmap (Owner: CEO/CTO)

- [ ] Create `ROADMAP.md` in TinySDLC root (30-day + 90-day milestones)
- [ ] Pin as GitHub Discussion: "What should we build next?"
- [ ] Include "Community decides" items (not just internal roadmap)

### C-03: Community Ownership Narrative (Owner: CEO)

Every post and README must signal: **"This is yours now."**

- [ ] GitHub Discussion: "Why we open-sourced this" (pinned, CEO-authored)
- [ ] CONTRIBUTING.md includes "Why contribute?" section explaining community value
- [ ] README ends with: "Built by MTS. Maintained by the community. MIT — use it, fork it, improve it."

### C-04: "Why Contribute?" Section (in CONTRIBUTING.md)

```markdown
## Why Contribute?

TinySDLC is community-owned. We built it from internal pain — but its future
belongs to everyone building with AI coding agents.

What you get:
- Direct influence on the roadmap
- Credit in CONTRIBUTORS.md and release notes
- A governance tool shaped by real production experience, not theory

What we need:
- Channel adapters (Slack, MS Teams, etc.)
- Translations (especially CJK languages)
- Security audit from fresh eyes
- Templates and playbooks for different team sizes
```

---

## Content Assets

| # | File | Platform | Language | Audience |
|---|------|----------|----------|----------|
| 1 | `Community-Launch-Strategy.md` | Internal | EN | PM/CEO reference |
| 2 | `Post-GitHub-Announcement.md` | GitHub Discussions / README | EN+VI | Core devs |
| 3 | `Post-Hacker-News.md` | Hacker News (Show HN) | EN | Deep technical |
| 4 | `Post-Reddit.md` | r/programming, r/devops, r/opensource | EN | Dev community |
| 5 | `Post-LinkedIn.md` | LinkedIn personal | EN+VI | Tech leadership / CTO |
| 6 | `Post-DevTo.md` | Dev.to | EN | SEO long-form technical |
| 7 | `Post-Facebook.md` | Facebook personal | VI+EN | VN tech community / founders |
| 8 | `Post-X-Thread.md` | X (Twitter) | EN | AI dev ecosystem / OSS community |

---

## Key Numbers (Use in Posts)

These are verified, authentic numbers from the SDLC Orchestrator journey:

| Metric | Value | Source |
|--------|-------|--------|
| First commit | November 13, 2025 | Git log `2c43fac1` |
| Framework versions | 12+ iterations → SDLC 6.1.0 | CHANGELOG.md |
| NQH-Bot crisis mocks | 679 mock implementations → 78% prod failure | CLAUDE.md |
| API endpoints | 91 (FastAPI) | API-Specification.md v3.6.0 |
| Test coverage | 94% | CLAUDE.md |
| OPA policies | 110+ | Policy packs |
| Claw tools tested | TinyClaw, OpenClaw, NanoBot, PicoClaw, ZeroClaw | ADR-058 |
| CEO age | 55 | CEO bio |
| Years since last coding | 30 | CEO bio |
| Build duration | 3+ months (Nov 2025 → Feb 2026) | Sprint history |
| Products delivered on framework | Bflow (ERP+BPM Platform for Vietnamese SMEs, MTS — [bflow.vn](https://www.bflow.vn), launched Oct 2024) → Bflow 2.0 (ERP+BPM+AI, Conversation-First), NQH-Bot (AI-Powered WFM for F&B, Nhat Quang Holding), MTEP, SOP Generator, Orchestrator | Product history |

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| HN downvote spiral | No marketing language. Pure technical. Test title with 3 devs before posting. |
| Reddit self-promotion flag | Lead with the problem, not the product. Follow subreddit rules exactly. |
| "Vaporware" criticism | Repos must have real code + working quickstart before any post. |
| Premature Product Hunt launch | Gate: ≥300 stars + ≥3 testimonials. Otherwise defer. |
| Enterprise confusion | Every post clearly states: TinySDLC = free OSS. Orchestrator = separate commercial product. |
| Cultural misread (CEO story) | Tet coding story works on LinkedIn/GitHub. May not resonate on HN — keep it minimal there. |
| Feature conflation (TinySDLC vs Orchestrator) | All posts clearly distinguish: TinySDLC = agent orchestrator with role discipline. Orchestrator = automated gates, OPA policies, evidence vault. Never claim Orchestrator features for TinySDLC. |
| "Open core" funnel perception | HN/Reddit will downvote if they sense TinySDLC is marketing for Orchestrator. First 4 weeks: NEVER say "upgrade path." Only say "minimal extract from internal system." Orchestrator only in Q&A responses. |
| Repo flatline after Week 1 | Without contributor surface area, stars don't convert to community. Must have 10+ good-first-issues, public roadmap, and pinned "Why we open-sourced this" Discussion before Week 2. |

---

## Pre-Launch Action Items (P0 — Must Complete Before Feb 20)

### F-01: GitHub Repo Metadata (Owner: DevOps/CEO)

```bash
# TinySDLC repo
gh repo edit Minh-Tam-Solution/tinysdlc \
  --description "Minimal agent orchestrator for AI coding — 8 SDLC roles, separation of duties, security hardening, multi-channel (MIT)" \
  --add-topic ai,governance,sdlc,multi-agent,typescript,opensource,coding-agents \
  --enable-discussions

# MTS-SDLC-Lite repo
gh repo edit Minh-Tam-Solution/MTS-SDLC-Lite \
  --description "Community SDLC methodology — governance playbook for AI-assisted development (MIT)" \
  --add-topic sdlc,methodology,ai-governance,templates,playbooks,opensource \
  --enable-discussions
```

### F-05: MTS-SDLC-Lite Repo Verification (Owner: DevOps)

- [ ] Verify https://github.com/Minh-Tam-Solution/MTS-SDLC-Lite is publicly accessible
- [ ] Verify README has clear description + quickstart
- [ ] Verify LICENSE file (MIT) exists
- [ ] Test all links in posts resolve correctly (no 404s)

### F-04: Dev.to Cover Image (Owner: PM/Designer — Deadline: Mar 3)

- [ ] Create architecture diagram image for Dev.to cover
- [ ] Recommend: text-based diagram rendered as PNG (matches post style)
- [ ] Upload to GitHub or Dev.to CDN, update `cover_image:` in Post-DevTo.md

---

## Post-Launch Tracking

Weekly check-in (every Friday):

```markdown
## Week N Community Report
- GitHub Stars: TinySDLC [___] / MTS-SDLC-Lite [___]
- New Issues: [___] / New PRs: [___]
- Top referral source: [___]
- Community sentiment: [Positive/Neutral/Negative]
- Action items for next week: [___]
```

---

## Timeline

```
Feb 20 (Fri) ─── Week 1 Start ─── Core Devs
  └─ GitHub, HN, Reddit (r/programming only), LinkedIn, Facebook

Mar 3 (Mon)  ─── Week 2 Start ─── Tech Leadership
  └─ Dev.to, Vietnam CTO, X/Twitter thread

Mar 10 (Mon) ─── Week 3 Start ─── Amplification + Reddit Spread
  └─ r/devops (Tue), AMA (Wed), r/softwarearchitecture (Thu)

Mar 17 (Mon) ─── Week 4 ─── Sustained + Review
  └─ r/selfhosted, r/opensource, Deep Dive #1, Q2 plan
```

---

**Last Updated**: February 20, 2026
**SDLC 6.1.0 | Community Launch Strategy | Stage 00 (FOUNDATION)**
