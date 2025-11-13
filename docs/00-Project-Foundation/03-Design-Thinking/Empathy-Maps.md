# SDLC Orchestrator - Empathy Maps
## Understanding User Emotions & Motivations (Design Thinking: EMPATHIZE)

**Version**: 1.0.0
**Date**: November 13, 2025
**Status**: ACTIVE - VALIDATED WITH 10+ INTERVIEWS
**Authority**: CPO + PM + UX Lead Approved
**Foundation**: User Personas 1.0.0, Problem Statement 1.0.0
**Stage**: Stage 00 (WHY) - Design Thinking EMPATHIZE Phase

---

## 🎯 Document Purpose

**Empathy Maps** visualize what users:
- **THINK** (thoughts, beliefs)
- **FEEL** (emotions, fears)
- **SAY** (what they tell us)
- **DO** (actions, behaviors)

This deepens our understanding beyond demographics to **emotional** and **behavioral** insights.

---

## 👤 Empathy Map 1: Engineering Manager (Primary Persona)

### Context

**Scenario**: Monday morning sprint planning
- **User**: Alex Chen, Engineering Manager (30-person SaaS)
- **Team**: 15 engineers (3 teams of 5)
- **Situation**: PM presents 5 features for next 2-week sprint
- **Trigger**: PM says "Customers asked for Feature X" (no evidence)

---

### 🧠 THINK (Thoughts & Beliefs)

**Rational Thoughts**:
- *"Did PM actually validate this with users?"*
- *"This feels like last quarter's commenting system disaster (2% adoption)"*
- *"If we build this and it fails, team morale will tank again"*
- *"I should ask for evidence, but I don't want to delay sprint planning"*
- *"CEO will ask why we're shipping so slowly, I'm stuck"*

**Beliefs**:
- *"60-70% of our features are wasted effort (I've seen the data)"*
- *"PM means well, but doesn't have systematic validation process"*
- *"Jira doesn't enforce validation, so PM skips it when busy"*
- *"My job is to prevent waste, but I don't have tools to enforce it"*
- *"If I challenge PM too much, they'll think I'm blocking progress"*

**Mental Model**:
- *"Good EM = protect team from wasted work"*
- *"Bad EM = blindly execute PM roadmap"*
- *"My career depends on showing business impact (feature adoption)"*

---

### 💔 FEEL (Emotions & Fears)

**Primary Emotions**:
- **Frustrated**: *"We've been here before, building unvalidated features"*
- **Anxious**: *"What if this wastes 2 sprints again?"*
- **Helpless**: *"I don't have power to block PM, only advise"*
- **Skeptical**: *"PM says 'customers want it' but where's the proof?"*
- **Worried**: *"Team already demoralized from last failed feature"*

**Fears**:
- **Fear #1**: *"Team builds Feature X → 2% adoption → engineers quit"*
- **Fear #2**: *"CEO asks 'Why so slow?' → I can't say '70% waste'"*
- **Fear #3**: *"I get passed over for VP Eng promotion (no business impact)"*
- **Fear #4**: *"PM-EM relationship deteriorates (constant friction)"*
- **Fear #5**: *"SOC 2 audit next quarter, we have zero evidence trail"*

**Stress Triggers**:
- PM says "Trust me" (no data)
- CEO adds feature to roadmap (HiPPO)
- Sprint retrospective: "Another unused feature"
- Quarterly performance review: "Show me business impact"

---

### 💬 SAY (What They Tell Us)

**In User Interviews** (direct quotes):
> "We built a commenting system. 3 sprints of work. Launched it. 2% of users used it. I had to tell my team we wasted 6 weeks. Morale tanked."

> "PM says 'Customers asked for this.' I ask 'Which customers? Show me emails.' PM says 'I don't remember.' We build it anyway. 5% adoption. Same story every quarter."

> "If you can stop my team from wasting 60% of our effort on features users don't want, I'll pay $500/month TODAY."

**In Sprint Planning**:
- *"Can we see evidence of user validation?"* (polite challenge)
- *"How confident are we this will get >30% adoption?"* (risk assessment)
- *"What's the rollback plan if adoption is low?"* (mitigation)

**To Their Team**:
- *"I know this feels like make-work, but let's ship it"* (forced positivity)
- *"Focus on quality, even if we're not sure users want it"* (defensive)

**To Their Boss (CTO)**:
- *"We're on track for this quarter"* (hide the waste problem)
- *"Team velocity is good"* (focus on output, not outcome)

**What They DON'T Say** (but think):
- *"PM is guessing, not validating"*
- *"I'm failing as an EM (can't prevent waste)"*
- *"I hate sprint planning (anxiety every Monday)"*

---

### 👟 DO (Actions & Behaviors)

**Before Sprint Planning**:
- ❌ Reviews Jira tickets (no validation evidence attached)
- ❌ Asks PM "Did you validate?" (PM says "Yes" verbally)
- ❌ Checks last sprint retrospective (notes: "Feature Y unused")
- ❌ Feels anxiety Sunday night (dreading Monday sprint planning)

**During Sprint Planning**:
- ✅ Asks for validation evidence (50% of time)
- ❌ Accepts PM's verbal assurance (50% of time, to avoid conflict)
- ❌ Commits team to 5 features (knowing 3 will likely fail)
- ❌ Mentally calculates: "2 weeks × $50K/sprint = $100K at risk"

**During Sprint**:
- ❌ Checks in with PM: "Any user feedback yet?" (too late, already building)
- ❌ Sees engineers working hard (feels guilty knowing likely waste)
- ❌ Prepares for retrospective: "How to say 'told you so' nicely?"

**After Feature Launch**:
- ✅ Checks analytics: Feature X = 5% adoption (predicted correctly)
- ❌ Leads retrospective: "What went wrong?" (knows answer: no validation)
- ❌ Updates resume (thinking about next role, frustrated)

**Workarounds** (current coping mechanisms):
- Manual validation checks (when remembers)
- Spreadsheet tracking (unmaintained after 2 weeks)
- Trusting PM's judgment (hope for best)
- Focusing on velocity (not outcome)

---

### 🎯 Pains & Gains

**Pains** (what frustrates them):
- 🔴 **No systematic validation**: PM skips when busy
- 🔴 **No evidence trail**: Can't prove validation happened
- 🔴 **No enforcement**: Jira doesn't block un-validated features
- 🔴 **Team demoralization**: Engineers hate building ignored features
- 🔴 **Career impact**: Can't show business results for promotion

**Gains** (what they want):
- 🟢 **Systematic gates**: Feature can't start without passing Gate G0.1
- 🟢 **Evidence vault**: Proof of validation (searchable, audit-ready)
- 🟢 **Real-time dashboard**: Feature adoption tracking
- 🟢 **Team happiness**: Build features users LOVE (70% adoption)
- 🟢 **Career advancement**: Show 30% → 70% adoption improvement

---

## 👤 Empathy Map 2: CTO (Secondary Persona)

### Context

**Scenario**: Quarterly board meeting
- **User**: Rebecca Taylor, CTO (200-person SaaS)
- **Situation**: Board asks "What projects are at risk?"
- **Trigger**: CTO doesn't know (has to ask 10 EMs, takes 2 days)

---

### 🧠 THINK

- *"I manage 10 teams, 30 projects. No idea which are on track."*
- *"Board expects real-time answers. I look incompetent."*
- *"Each team has their own 'process.' Chaos at scale."*
- *"SOC 2 audit costs $150K/year. This should be automated."*

### 💔 FEEL

**Primary Emotions**:
- **Embarrassed**: *"Board asks simple question, I can't answer"*
- **Overwhelmed**: *"10 teams, can't track manually"*
- **Anxious**: *"Board losing confidence in my leadership"*

**Fears**:
- *"Fired if can't show control over engineering org"*
- *"Audit failure (compliance breach = career-ending)"*
- *"Missed promotion to unicorn CTO role"*

### 💬 SAY

> "I manage 10 teams, 30 projects. Board asks 'What's at risk?' I don't know. I have to ask 10 EMs, consolidate manually. Takes 2 days."

> "We spend $150K/year on compliance: $50K auditor + 200 hours internal. SOC 2 + ISO 27001. Every year. Forever."

### 👟 DO

**Before Board Meeting**:
- ❌ Emails 10 EMs: "Send me project status by EOD" (manual consolidation)
- ❌ Spends 2 days consolidating 10 different formats
- ❌ Creates PowerPoint (stale data by presentation time)

**During Board Meeting**:
- ❌ Shows 2-day-old status (board asks "What changed since then?")
- ❌ Can't answer in real-time (looks unprepared)

**After Board Meeting**:
- ❌ Thinks about switching to competitor company (less chaos)

### 🎯 Pains & Gains

**Pains**:
- 🔴 No real-time visibility (2-day manual consolidation)
- 🔴 No standardization (10 teams = 10 processes)
- 🔴 Compliance burden ($150K/year)
- 🔴 Board frustration (looks incompetent)

**Gains**:
- 🟢 Real-time dashboard (live board presentation)
- 🟢 Standardized SDLC (all teams follow SDLC 4.8)
- 🟢 Automated compliance (SOC 2 evidence auto-collected)
- 🟢 Board confidence (impress with real-time data)

---

## 👤 Empathy Map 3: Product Manager (Tertiary Persona)

### Context

**Scenario**: Engineer asks "Did you validate this feature?"
- **User**: Jordan Martinez, PM (40-person SaaS)
- **Situation**: Sprint planning, engineer challenges PM
- **Trigger**: PM can't find validation evidence (emails lost)

---

### 🧠 THINK

- *"I DID validate this (talked to 5 customers)"*
- *"But I can't find the emails (inbox search fails)"*
- *"Engineer thinks I'm making it up (losing trust)"*
- *"Next time I'll save evidence... (but I always forget)"*

### 💔 FEEL

**Primary Emotions**:
- **Defensive**: *"I DID do the work, just can't prove it"*
- **Frustrated**: *"Evidence is somewhere in 8 tools (Slack, email, Notion)"*
- **Embarrassed**: *"Engineer losing trust in my roadmap"*

**Fears**:
- *"Engineers stop trusting me → won't execute roadmap"*
- *"EM escalates to CEO → I look incompetent"*
- *"Feature fails (5% adoption) → 'I told you so'"*

### 💬 SAY

> "Engineer asks 'Did you validate?' I say 'Yes, talked to 5 customers.' Engineer: 'Show me notes.' I can't find them. They lose trust."

> "I WANT gates. They protect me from building features that'll fail. Career insurance."

### 👟 DO

**Before Sprint Planning**:
- ❌ Talks to 5 customers (verbally, no recording)
- ❌ Takes notes in Notion (not linked to Jira ticket)
- ❌ Forgets to save interview recording

**During Sprint Planning**:
- ❌ Says "I validated with 5 customers" (can't prove it)
- ❌ Engineer asks for evidence → scrambles to find emails
- ❌ Can't find evidence → engineer skeptical

**After Sprint**:
- ❌ Feature launches → 5% adoption
- ❌ Retrospective: "Why didn't we validate better?" (feels attacked)

### 🎯 Pains & Gains

**Pains**:
- 🔴 Can't prove validation (evidence lost)
- 🔴 Engineer-PM trust erosion
- 🔴 Manual evidence collection (always forgets)

**Gains**:
- 🟢 Evidence vault (auto-save interviews)
- 🟢 AI interview script (faster validation)
- 🟢 PM-engineer trust (proof of validation)

---

## ✅ Insights from Empathy Maps

### Key Emotional Insights

1. **Fear is Primary Driver** (not rational calculation):
   - EM fears: Team demoralization, career impact, PM relationship
   - CTO fears: Board embarrassment, audit failure, termination
   - PM fears: Engineer trust loss, career damage, public failure

2. **Powerlessness Creates Anxiety**:
   - EM: *"I can't block PM (only advise)"*
   - CTO: *"I can't force standardization (each team resists)"*
   - PM: *"I can't find evidence (8 tools, chaos)"*

3. **Shame Prevents Honesty**:
   - EM won't tell CTO: *"We're wasting 70% of effort"* (looks incompetent)
   - CTO won't tell Board: *"I don't know project status"* (looks unprepared)
   - PM won't admit: *"I guessed, didn't validate"* (career suicide)

### Design Implications

**Must Address Emotions** (not just features):
- ✅ Reduce fear: *"Gate failed? Here's how to fix (not punishment)"*
- ✅ Increase control: *"EM can block sprint if Gate G0.1 failed"*
- ✅ Build confidence: *"You validated with 5 users (here's proof)"*

**Must Be Non-Blaming**:
- ✅ *"Team didn't pass Gate G0.1"* (process failed, not people)
- ❌ *"PM failed to validate"* (personal attack)

**Must Save Face**:
- ✅ Private dashboard view (fix issues before public)
- ✅ Learning-focused retros (not blame)

---

**Document**: SDLC-Orchestrator-Empathy-Maps
**Framework**: SDLC 4.8 Stage 00 (WHY) - Design Thinking EMPATHIZE
**Component**: Emotional & Behavioral Understanding
**Review**: Quarterly (validate emotions remain accurate)

*"Understand what users feel, not just what they say"* 💚
