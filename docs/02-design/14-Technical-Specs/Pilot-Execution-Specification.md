# Pilot Execution Specification
## EP-06: Vietnam SME Founder Pilot | Sprint 49

**Status**: APPROVED
**Version**: 1.0.0
**Date**: December 23, 2025
**Author**: Product + Success Team
**Sprint**: Sprint 49 (Mar 3-14, 2026)
**Framework**: SDLC 6.1.0
**Dependency**: Sprint 48 (Quality Gates)

---

## 1. Overview

### 1.1 Purpose

This specification defines the pilot execution plan for validating EP-06 with 10 Vietnamese SME founders, measuring TTFV (Time to First Value) and satisfaction.

### 1.2 Strategic Context

**Founder Plan Validation**: Sprint 49 is the critical validation gate for EP-06.

| Outcome | Criteria | Next Step |
|---------|----------|-----------|
| **SUCCESS** | 10 pilots complete, 8/10 satisfaction, <30min TTFV | Proceed to GA |
| **PARTIAL** | 5-9 pilots, 6-7/10 satisfaction | Sprint 51-52 hardening |
| **FAIL** | <5 pilots, <6/10 satisfaction | Re-evaluate strategy |

---

## 2. Pilot Recruitment

### 2.1 Target Participants

| Domain | Target | Source | Incentive |
|--------|--------|--------|-----------|
| F&B (Nhà hàng) | 4 founders | NQH network, BFlow | Free 3 months |
| Hospitality (Khách sạn) | 3 founders | NQH network | Free 3 months |
| Retail (Cửa hàng) | 3 founders | Vietnam startup communities | Free 3 months |

### 2.2 Selection Criteria

```yaml
Must Have:
  - Vietnam-based SME owner (non-tech background preferred)
  - Active business (>6 months operation)
  - Basic smartphone/computer literacy
  - Willing to provide feedback (1-hour interview)
  - Available during pilot window (Mar 3-14)

Nice to Have:
  - Currently using manual processes (Excel, paper)
  - Expressed interest in digitalization
  - English optional (Vietnamese primary)
```

### 2.3 Recruitment Timeline

| Date | Milestone | Owner |
|------|-----------|-------|
| Feb 17-21 | Initial outreach (30 candidates) | Sales |
| Feb 24-28 | Screening calls, select 15 | Success |
| Mar 1-2 | Final selection, confirm 10 | Success |
| Mar 3 | Pilot kickoff | Product + Success |

---

## 3. Pilot Process

### 3.1 Pilot Journey

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PILOT JOURNEY (Per Founder)                       │
│                                                                      │
│  Day 1: Onboarding Session (60 min)                                  │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  1. Welcome + Consent (10 min)                               │    │
│  │  2. Domain Selection (5 min)                                 │    │
│  │  3. Questionnaire (15 min)                                   │    │
│  │  4. IR Preview + Confirmation (10 min)                       │    │
│  │  5. Code Generation (5 min) ← TTFV measured                  │    │
│  │  6. Demo Generated App (15 min)                              │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              ↓                                       │
│  Day 2-7: Self-Service Usage                                         │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  - Explore generated app                                     │    │
│  │  - Try modifications (via re-generation)                     │    │
│  │  - Report issues via WhatsApp/Zalo                           │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              ↓                                       │
│  Day 8-10: Feedback Session (45 min)                                │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  1. Usage Review (10 min)                                    │    │
│  │  2. Satisfaction Survey (15 min)                             │    │
│  │  3. Feature Requests (10 min)                                │    │
│  │  4. NPS + Testimonial (10 min)                               │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Support Model

| Channel | Purpose | Response Time |
|---------|---------|---------------|
| WhatsApp/Zalo Group | Quick questions | <2 hours |
| Video Call (Scheduled) | Complex issues | Within 24 hours |
| Email | Documentation, receipts | Within 48 hours |

---

## 4. Metrics Collection

### 4.1 Primary Metrics (Success Criteria)

| Metric | Target | Collection Method |
|--------|--------|-------------------|
| **TTFV (Time to First Value)** | <30 min (median) | System timestamp |
| **Completion Rate** | 10/10 complete onboarding | System tracking |
| **Satisfaction Score** | 8/10 average | Post-pilot survey |
| **NPS** | >50 | Survey question |

### 4.2 Secondary Metrics

| Metric | Target | Collection Method |
|--------|--------|-------------------|
| Quality gate pass rate | ≥95% | System logs |
| Support tickets per user | <3 | Support system |
| Re-generation attempts | <2 per user | System logs |
| Session duration | <60 min total | System tracking |

### 4.3 Data Model

```python
# backend/app/models/pilot_metrics.py

from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, TimestampMixin
import uuid

class PilotParticipant(Base, TimestampMixin):
    """Pilot participant information."""
    __tablename__ = "pilot_participants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    business_name = Column(String(255))
    domain = Column(String(50))  # restaurant, hotel, retail
    phone = Column(String(20))
    email = Column(String(255))
    source = Column(String(100))  # nqh_network, bflow, startup_community
    status = Column(String(50))  # invited, confirmed, active, completed, dropped

class PilotSession(Base, TimestampMixin):
    """Individual pilot session data."""
    __tablename__ = "pilot_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    participant_id = Column(UUID(as_uuid=True), ForeignKey("pilot_participants.id"))
    session_type = Column(String(50))  # onboarding, usage, feedback
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime)
    duration_minutes = Column(Integer)
    notes = Column(JSON)

class PilotMetric(Base, TimestampMixin):
    """Collected metrics per participant."""
    __tablename__ = "pilot_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    participant_id = Column(UUID(as_uuid=True), ForeignKey("pilot_participants.id"))
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float)
    metric_unit = Column(String(50))
    collected_at = Column(DateTime, nullable=False)
    notes = Column(String(500))

class PilotFeedback(Base, TimestampMixin):
    """Feedback responses."""
    __tablename__ = "pilot_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    participant_id = Column(UUID(as_uuid=True), ForeignKey("pilot_participants.id"))
    satisfaction_score = Column(Integer)  # 1-10
    nps_score = Column(Integer)  # 0-10
    would_recommend = Column(String(10))  # yes, no, maybe
    most_valuable_feature = Column(String(500))
    biggest_pain_point = Column(String(500))
    feature_requests = Column(JSON)
    testimonial = Column(String(1000))
    consent_to_publish = Column(String(10))  # yes, no
```

---

## 5. Survey Instruments

### 5.1 Satisfaction Survey (Vietnamese)

```yaml
survey_id: pilot_satisfaction_v1
language: vi

questions:
  - id: overall_satisfaction
    text: "Bạn hài lòng với SDLC Orchestrator ở mức nào? (1-10)"
    type: scale
    min: 1
    max: 10
    required: true

  - id: ease_of_use
    text: "Công cụ dễ sử dụng không? (1-10)"
    type: scale
    min: 1
    max: 10
    required: true

  - id: time_saving
    text: "Công cụ giúp bạn tiết kiệm thời gian không?"
    type: select
    options:
      - value: "yes_significant"
        label: "Có, tiết kiệm rất nhiều"
      - value: "yes_some"
        label: "Có, tiết kiệm một ít"
      - value: "neutral"
        label: "Không rõ ràng"
      - value: "no"
        label: "Không"

  - id: valuable_feature
    text: "Tính năng nào bạn thấy có giá trị nhất?"
    type: text
    required: true

  - id: pain_point
    text: "Điều gì khó khăn nhất khi sử dụng?"
    type: text
    required: true

  - id: nps
    text: "Bạn có giới thiệu công cụ này cho người khác không? (0-10)"
    type: scale
    min: 0
    max: 10
    required: true
    nps: true

  - id: feature_requests
    text: "Bạn muốn có thêm tính năng gì?"
    type: text
    required: false

  - id: testimonial
    text: "Nếu hài lòng, bạn có thể chia sẻ vài câu về trải nghiệm?"
    type: text
    required: false

  - id: consent
    text: "Chúng tôi có thể sử dụng nhận xét của bạn cho mục đích marketing?"
    type: boolean
    required: true
```

### 5.2 Onboarding Checklist

```yaml
checklist_id: pilot_onboarding_v1

steps:
  - id: consent
    text: "Đã ký consent form"
    required: true

  - id: domain_selected
    text: "Đã chọn ngành (F&B/Hotel/Retail)"
    timestamp: true

  - id: questionnaire_started
    text: "Bắt đầu trả lời câu hỏi"
    timestamp: true

  - id: questionnaire_completed
    text: "Hoàn thành câu hỏi"
    timestamp: true

  - id: ir_generated
    text: "IR được tạo thành công"
    timestamp: true

  - id: ir_confirmed
    text: "Founder xác nhận IR"
    timestamp: true

  - id: generation_started
    text: "Bắt đầu tạo code"
    timestamp: true

  - id: generation_completed
    text: "Code được tạo thành công"
    timestamp: true
    ttfv_end: true

  - id: demo_completed
    text: "Demo app hoàn thành"
    timestamp: true
```

---

## 6. Pilot Dashboard

### 6.1 Real-time Metrics Display

```typescript
// frontend/web/src/components/pilot/PilotDashboard.tsx

interface PilotMetrics {
  totalParticipants: number;
  completedOnboarding: number;
  averageTTFV: number;  // minutes
  averageSatisfaction: number;  // 1-10
  nps: number;
  qualityGatePassRate: number;  // percentage
}

interface ParticipantStatus {
  id: string;
  name: string;
  domain: string;
  status: 'invited' | 'confirmed' | 'active' | 'completed' | 'dropped';
  ttfv: number | null;
  satisfaction: number | null;
  lastActivity: Date;
}

export function PilotDashboard() {
  // Real-time metrics display
  return (
    <div className="pilot-dashboard">
      <h1>EP-06 Pilot Dashboard</h1>

      {/* Summary Cards */}
      <div className="metrics-grid">
        <MetricCard
          title="Participants"
          value="10/10"
          target="10"
          status="on-track"
        />
        <MetricCard
          title="Median TTFV"
          value="22 min"
          target="<30 min"
          status="on-track"
        />
        <MetricCard
          title="Satisfaction"
          value="8.2/10"
          target="≥8/10"
          status="on-track"
        />
        <MetricCard
          title="NPS"
          value="62"
          target=">50"
          status="on-track"
        />
      </div>

      {/* Participant Table */}
      <ParticipantTable participants={participants} />

      {/* Timeline */}
      <PilotTimeline events={events} />
    </div>
  );
}
```

---

## 7. Risk Mitigation

### 7.1 Identified Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Insufficient pilot candidates | High | Medium | Start recruitment early, over-recruit by 50% |
| High drop-off rate | High | Medium | Daily check-ins, WhatsApp support |
| Poor satisfaction scores | High | Low | Pre-pilot testing, quick iterations |
| Technical issues during pilot | High | Medium | Dedicated support engineer, rollback plan |
| TTFV exceeds target | Medium | Medium | Optimize onboarding flow, pre-fill templates |

### 7.2 Contingency Plans

**If <5 complete by Day 5**:
- Extend pilot window by 1 week
- Add 5 more candidates from backup list
- Simplify onboarding flow

**If satisfaction <6/10 by Day 7**:
- Emergency feedback session
- Identify top 3 pain points
- Implement quick fixes

**If quality gate pass rate <90%**:
- Pause new onboardings
- Debug and fix failing gates
- Resume with fixed version

---

## 8. Success Criteria & Decision Gate

### 8.1 EP-06 Success Gate (End of Sprint 49)

| Criteria | Target | Weight |
|----------|--------|--------|
| Pilot completion | 10/10 founders complete | 25% |
| TTFV (median) | <30 minutes | 25% |
| Satisfaction score | ≥8/10 | 25% |
| NPS | >50 | 15% |
| Quality gate pass | ≥95% | 10% |

**Weighted Score Required**: ≥80% to proceed to GA

### 8.2 Decision Options

| Score | Decision | Next Action |
|-------|----------|-------------|
| ≥80% | **GO** | Proceed to Sprint 50 productization |
| 60-79% | **CONDITIONAL GO** | Address gaps in Sprint 50-51 |
| <60% | **NO GO** | Re-evaluate EP-06 strategy |

---

## 9. Sprint 49 Implementation Checklist

### Week 1 (Mar 3-7)

- [ ] Finalize 10 pilot participants
- [ ] Conduct onboarding sessions (2-3 per day)
- [ ] Collect TTFV metrics automatically
- [ ] Monitor quality gate pass rates
- [ ] Daily stand-up: address issues

### Week 2 (Mar 10-14)

- [ ] Continue self-service usage period
- [ ] Conduct feedback sessions
- [ ] Collect survey responses
- [ ] Calculate final metrics
- [ ] Prepare EP-06 Decision Gate report
- [ ] Present to CTO/CEO

---

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Date** | December 23, 2025 |
| **Author** | Product + Success Team |
| **Status** | APPROVED |
| **Sprint** | Sprint 49 (Mar 3-14, 2026) |
| **Dependency** | Sprint 48 |
