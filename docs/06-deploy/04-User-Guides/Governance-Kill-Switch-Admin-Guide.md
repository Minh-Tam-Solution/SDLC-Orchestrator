# Kill Switch Admin Guide

**Version**: 1.0.0
**Date**: January 28, 2026
**Framework**: SDLC 6.1.0
**ADR Reference**: ADR-041
**Authorization**: CTO/CEO Only

---

## Overview

The Kill Switch Admin provides governance mode control and emergency bypass capabilities. This guide is for **CTO/CEO authorized personnel only**.

### Components

| Component | Purpose |
|-----------|---------|
| **Governance Mode Toggle** | Switch between OFF/WARNING/SOFT/FULL modes |
| **Kill Switch Dashboard** | Monitor rollback criteria and system health |
| **Mode History Timeline** | Audit trail of all mode changes |
| **Break Glass Button** | Emergency bypass for P0/P1 incidents |
| **Audit Log Table** | Comprehensive event logging with search |

---

## Governance Modes

### Mode Definitions

| Mode | Behavior | When to Use |
|------|----------|-------------|
| **OFF** | Governance disabled, all PRs pass | Initial deployment, major issues |
| **WARNING** | Log violations, don't block PRs | Dogfooding period, tuning rules |
| **SOFT** | Block critical violations only (Red PRs) | Gradual rollout |
| **FULL** | All violations block, only Green PRs merge | Production standard |

### Mode Transition Matrix

```
OFF → WARNING → SOFT → FULL (Normal progression)
FULL → SOFT → WARNING → OFF (Rollback if issues)
ANY → OFF (Break glass emergency)
```

### Recommended Rollout

1. **Week 1**: WARNING mode - Establish baseline, tune thresholds
2. **Week 2**: SOFT mode - Block critical issues, allow medium/low
3. **Week 3**: FULL mode - Full enforcement (if metrics pass)

---

## Mode Change Procedure

### Prerequisites

- CTO or CEO role assigned
- 2FA authentication enabled
- Valid reason for change (audit requirement)

### Steps

1. Navigate to **Kill Switch Admin** (`/app/governance/kill-switch`)
2. Click on target mode in the **Mode Toggle** grid
3. Confirmation dialog appears:
   - Current mode displayed
   - Target mode highlighted
   - Reason textarea (required, min 10 chars)
4. Enter reason for mode change
5. Click **Confirm Change**
6. Mode changes immediately
7. Audit log entry created
8. Slack notification sent to `#governance-alerts`

### Reason Examples

- "Enabling WARNING mode for Sprint 114 dogfooding"
- "Rollback to SOFT due to 15% false positive rate"
- "FULL enforcement after successful 2-week trial"

---

## Rollback Criteria Dashboard

### Metrics Monitored

| Metric | Threshold | Trigger |
|--------|-----------|---------|
| **Rejection Rate** | >5% | Too many PRs rejected |
| **Latency P95** | >100ms | Governance too slow |
| **False Positive Rate** | >10% | Blocking valid PRs |
| **Developer Complaints** | >3/day | Team friction |

### Reading the Gauges

Each metric displays:
- **Current Value**: Real-time measurement
- **Threshold Line**: Auto-rollback trigger point
- **Status Indicator**: Green (safe) / Red (breached)

### Auto-Rollback

When enabled, system automatically:
1. Detects threshold breach
2. Waits 5 minutes (debounce)
3. Rolls back to previous mode
4. Sends Slack alert
5. Creates audit log entry

**Enable/Disable**: Toggle in dashboard header

---

## Mode History Timeline

### Entry Information

Each timeline entry shows:
- **From Mode → To Mode**: Transition visualization
- **Timestamp**: When change occurred (relative + absolute)
- **Actor**: Who made the change (or "System" for auto)
- **Reason**: Why the change was made
- **Duration**: How long previous mode was active

### Auto-Rollback Indicators

Entries with red dot indicate auto-rollback:
- **Trigger Criteria**: Which metric(s) caused rollback
- **Values at Trigger**: Actual values when triggered

### Filtering

- Click **Load More** for older entries
- Default shows last 10 changes
- Audit retention: 2 years

---

## Break Glass Procedure

### When to Use

**ONLY for production emergencies:**
- P0: Complete service outage
- P1: Major functionality broken
- Hotfix: Critical security vulnerability

**DO NOT use for:**
- Regular deployments
- Feature releases
- Non-critical bugs

### Activation Steps

1. Click **Break Glass** button (bottom-right, red)
2. Confirmation modal appears with warning
3. Select **Incident Type**: P0, P1, or Hotfix
4. Enter **Reason** (min 50 chars, detailed explanation)
5. Complete **2FA verification** (required)
6. Click **Activate Emergency Bypass**

### What Happens

1. Governance mode immediately set to **OFF**
2. **4-hour countdown** starts
3. Slack notification sent to `#governance-alerts` and `#incidents`
4. All stakeholders notified (CTO, CEO, Tech Leads)
5. Audit log entry with full details

### Auto-Revert

After 4 hours:
- Mode automatically reverts to previous setting
- Notification sent: "Break glass expired, governance restored"
- Post-incident review required within 24 hours

### Post-Incident

Within 24 hours:
1. Complete incident report
2. Review what was deployed during break glass
3. Validate all PRs merged during window
4. Document lessons learned

---

## Audit Log

### Event Types

| Event | Color | Description |
|-------|-------|-------------|
| **mode_change** | Blue | Manual mode transition |
| **auto_rollback** | Orange | System-triggered rollback |
| **break_glass** | Red | Emergency bypass activation |
| **override** | Yellow | Individual PR override |

### Search & Filter

- **Event Type**: Dropdown filter
- **Actor**: Search by username
- **Date Range**: Start/end date picker
- **Keyword**: Search in reason text

### Export

Click **Export CSV** to download filtered audit log for compliance reporting.

### Retention

- Audit logs retained for **2 years**
- Break glass events retained **indefinitely**
- Immutable (cannot be deleted or modified)

---

## Emergency Runbook

### P0 Incident (Complete Outage)

```
1. Assess: Confirm governance is causing outage
2. Break Glass: Activate with P0 type
3. Deploy: Push hotfix without governance checks
4. Monitor: Verify service restored
5. Review: Post-incident analysis within 4 hours
6. Restore: Governance auto-reverts after 4 hours
```

### P1 Incident (Major Issue)

```
1. Assess: Determine if governance-related
2. Option A: Use PR override for specific PR
3. Option B: Break glass if multiple PRs blocked
4. Deploy: Push fixes
5. Review: Document within 24 hours
```

### False Positive Spike

```
1. Check: Dashboard shows >10% false positive
2. Rollback: Change mode to WARNING (not OFF)
3. Analyze: Review rejected PRs in audit log
4. Tune: Adjust rules/thresholds
5. Re-enable: Gradually return to SOFT/FULL
```

---

## Slack Integration

### Channels

| Channel | Purpose |
|---------|---------|
| `#governance-alerts` | All mode changes, warnings |
| `#incidents` | Break glass activations only |
| `#cto-notifications` | CTO-specific alerts |

### Alert Format

```
🔔 Governance Mode Changed
From: FULL → To: SOFT
By: @cto.name
Reason: High false positive rate (12.3%)
Time: 2026-01-28 14:32:05 UTC
```

### Break Glass Alert

```
🚨 BREAK GLASS ACTIVATED
Type: P0 - Complete Outage
By: @cto.name
Reason: Database connection pool exhausted...
Auto-Revert: 4 hours (18:32 UTC)
Action Required: Deploy hotfix immediately
```

---

## Best Practices

### Mode Changes

1. **Document thoroughly** - Future audits depend on clear reasons
2. **Notify team** - Announce mode changes in team channel
3. **Monitor closely** - Watch dashboard after changes
4. **Gradual rollout** - WARNING → SOFT → FULL over weeks

### Break Glass

1. **Last resort only** - Try PR override first
2. **Document everything** - Every action during bypass
3. **Time-box deployments** - Don't leave break glass open
4. **Post-incident review** - Always, within 24 hours

### Audit Compliance

1. **Regular reviews** - Weekly audit log review
2. **Export reports** - Monthly compliance exports
3. **Trend analysis** - Track mode change frequency
4. **Stakeholder updates** - Quarterly governance reports

---

## Troubleshooting

### Mode Change Fails

**Problem**: "Unauthorized" error

**Solution**:
- Verify CTO/CEO role assigned
- Check 2FA is enabled
- Contact admin if role missing

### Dashboard Not Loading

**Problem**: Metrics show "Loading..."

**Solution**:
- Check network connectivity
- Verify backend services running
- Refresh page
- Contact DevOps if persistent

### Break Glass Not Working

**Problem**: Button disabled or error

**Solution**:
- Verify 2FA authentication
- Check role permissions
- If system error, manually set mode via database (last resort)

### Audit Log Missing Entries

**Problem**: Expected entries not visible

**Solution**:
- Check date range filter
- Clear all filters
- Verify event type selected
- Check audit service health

---

## Related Documentation

- [Auto-Generation User Guide](./Governance-Auto-Generation-Guide.md)
- [ADR-041: Stage Dependencies](../../02-design/03-ADRs/ADR-041-Stage-Dependencies.md)
- [Incident Response Runbook](../Runbooks/Incident-Response.md)
- [SDLC 6.1.0 Quality Assurance System](../../../SDLC-Enterprise-Framework/02-Core-Methodology/SDLC-Quality-Assurance-System.md)

---

*Kill Switch - Control governance without compromising safety.*
