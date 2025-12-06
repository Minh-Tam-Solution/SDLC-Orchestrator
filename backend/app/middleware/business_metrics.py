"""
=========================================================================
Business Metrics - Prometheus Metrics for SDLC Orchestrator Business Logic
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.0.0
Date: December 2, 2025
Status: ACTIVE - Sprint 22 Day 2 (Prometheus Metrics Integration)
Authority: Backend Lead + CTO Approved
Foundation: Sprint 22 Plan, Observability Architecture
Framework: SDLC 4.9.1 Complete Lifecycle

Purpose:
- Compliance scan metrics (duration, violations, scores)
- Notification metrics (sent, failed, by channel)
- Gate metrics (evaluations, pass/fail rates)
- Evidence metrics (uploads, storage size)
- AI recommendation metrics (requests, latency, costs)

Metrics Categories:
1. Compliance Metrics (compliance_*)
2. Notification Metrics (notification_*)
3. Gate Metrics (gate_*)
4. Evidence Metrics (evidence_*)
5. AI Metrics (ai_*)

Performance Targets:
- Compliance scan: <30s (p95)
- Notification delivery: <5s (p95)
- Gate evaluation: <100ms (p95)

Zero Mock Policy: 100% production-ready implementation
=========================================================================
"""

from prometheus_client import Counter, Gauge, Histogram, Summary

# ============================================================================
# COMPLIANCE SCAN METRICS
# ============================================================================

# Histogram: Compliance scan duration (buckets: 1s, 5s, 10s, 30s, 60s, 120s, 300s)
compliance_scan_duration_seconds = Histogram(
    "compliance_scan_duration_seconds",
    "Time taken to complete a compliance scan (seconds)",
    ["project_id", "scan_type"],
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
)

# Counter: Total compliance scans
compliance_scans_total = Counter(
    "compliance_scans_total",
    "Total number of compliance scans executed",
    ["project_id", "scan_type", "status"],  # status: completed, failed, cancelled
)

# Gauge: Current compliance score per project
compliance_score_current = Gauge(
    "compliance_score_current",
    "Current compliance score (0-100) per project",
    ["project_id"],
)

# Counter: Total violations detected
compliance_violations_total = Counter(
    "compliance_violations_total",
    "Total number of compliance violations detected",
    ["project_id", "severity", "policy_category"],
)

# Histogram: Violations per scan
compliance_violations_per_scan = Histogram(
    "compliance_violations_per_scan",
    "Number of violations detected per scan",
    ["project_id", "scan_type"],
    buckets=(0, 1, 5, 10, 20, 50, 100),
)

# Gauge: Scans currently in progress
compliance_scans_in_progress = Gauge(
    "compliance_scans_in_progress",
    "Number of compliance scans currently in progress",
)

# Counter: Policies evaluated
compliance_policies_evaluated_total = Counter(
    "compliance_policies_evaluated_total",
    "Total number of policy evaluations",
    ["project_id", "policy_id", "result"],  # result: pass, fail, error
)


# ============================================================================
# NOTIFICATION METRICS
# ============================================================================

# Counter: Notifications sent
notifications_sent_total = Counter(
    "notifications_sent_total",
    "Total number of notifications sent",
    ["channel", "notification_type", "status"],  # channel: email, slack, teams, in_app
)

# Histogram: Notification delivery time
notification_delivery_seconds = Histogram(
    "notification_delivery_seconds",
    "Time taken to deliver notification (seconds)",
    ["channel", "notification_type"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0),
)

# Counter: Notification failures by reason
notification_failures_total = Counter(
    "notification_failures_total",
    "Total number of failed notifications",
    ["channel", "notification_type", "failure_reason"],
)

# Gauge: Unread notifications per user (sampled)
notifications_unread_gauge = Gauge(
    "notifications_unread_total",
    "Total unread notifications across all users",
)

# Counter: Notifications by priority
notifications_by_priority_total = Counter(
    "notifications_by_priority_total",
    "Notifications sent by priority level",
    ["priority"],  # critical, high, medium, low
)


# ============================================================================
# GATE METRICS
# ============================================================================

# Counter: Gate evaluations
gate_evaluations_total = Counter(
    "gate_evaluations_total",
    "Total number of gate evaluations",
    ["project_id", "gate_type", "result"],  # result: pass, fail, blocked
)

# Histogram: Gate evaluation duration
gate_evaluation_duration_seconds = Histogram(
    "gate_evaluation_duration_seconds",
    "Time taken to evaluate a gate (seconds)",
    ["gate_type"],
    buckets=(0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0),
)

# Gauge: Gates pending approval
gates_pending_approval = Gauge(
    "gates_pending_approval",
    "Number of gates currently pending approval",
    ["project_id", "gate_type"],
)

# Counter: Gate approvals
gate_approvals_total = Counter(
    "gate_approvals_total",
    "Total number of gate approvals",
    ["project_id", "gate_type", "approver_role"],
)

# Counter: Gate rejections
gate_rejections_total = Counter(
    "gate_rejections_total",
    "Total number of gate rejections",
    ["project_id", "gate_type", "rejection_reason"],
)


# ============================================================================
# EVIDENCE METRICS
# ============================================================================

# Counter: Evidence uploads
evidence_uploads_total = Counter(
    "evidence_uploads_total",
    "Total number of evidence files uploaded",
    ["project_id", "evidence_type", "status"],  # status: success, failed
)

# Histogram: Evidence upload size (bytes)
evidence_upload_size_bytes = Histogram(
    "evidence_upload_size_bytes",
    "Size of uploaded evidence files (bytes)",
    ["project_id", "evidence_type"],
    buckets=(1024, 10240, 102400, 1048576, 10485760, 104857600),  # 1KB to 100MB
)

# Histogram: Evidence upload duration
evidence_upload_duration_seconds = Histogram(
    "evidence_upload_duration_seconds",
    "Time taken to upload evidence (seconds)",
    ["evidence_type"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0),
)

# Gauge: Total evidence storage size (bytes) per project
evidence_storage_bytes = Gauge(
    "evidence_storage_bytes",
    "Total evidence storage size in bytes",
    ["project_id"],
)


# ============================================================================
# AI RECOMMENDATION METRICS
# ============================================================================

# Counter: AI recommendation requests
ai_requests_total = Counter(
    "ai_requests_total",
    "Total number of AI recommendation requests",
    ["provider", "request_type", "status"],  # provider: ollama, anthropic, openai
)

# Histogram: AI request latency
ai_request_duration_seconds = Histogram(
    "ai_request_duration_seconds",
    "Time taken for AI recommendation request (seconds)",
    ["provider", "request_type"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
)

# Counter: AI tokens used (cost tracking)
ai_tokens_used_total = Counter(
    "ai_tokens_used_total",
    "Total tokens used for AI requests",
    ["provider", "token_type"],  # token_type: input, output
)

# Gauge: AI cost tracking (estimated USD)
ai_cost_usd = Gauge(
    "ai_cost_usd_total",
    "Estimated AI cost in USD",
    ["provider"],
)

# Counter: AI fallback events
ai_fallback_total = Counter(
    "ai_fallback_total",
    "Number of times AI fell back to alternative provider",
    ["from_provider", "to_provider", "reason"],
)


# ============================================================================
# HELPER FUNCTIONS FOR METRIC COLLECTION
# ============================================================================


class ComplianceMetrics:
    """Helper class for collecting compliance scan metrics."""

    @staticmethod
    def record_scan_start():
        """Record a scan has started."""
        compliance_scans_in_progress.inc()

    @staticmethod
    def record_scan_complete(
        project_id: str,
        scan_type: str,
        duration_seconds: float,
        violations_count: int,
        compliance_score: float,
        status: str = "completed",
    ):
        """
        Record completion of a compliance scan.

        Args:
            project_id: UUID of the project
            scan_type: Type of scan (manual, scheduled, webhook)
            duration_seconds: Time taken for scan
            violations_count: Number of violations found
            compliance_score: Final compliance score (0-100)
            status: Scan status (completed, failed, cancelled)
        """
        compliance_scans_in_progress.dec()
        compliance_scan_duration_seconds.labels(
            project_id=project_id, scan_type=scan_type
        ).observe(duration_seconds)
        compliance_scans_total.labels(
            project_id=project_id, scan_type=scan_type, status=status
        ).inc()
        compliance_score_current.labels(project_id=project_id).set(compliance_score)
        compliance_violations_per_scan.labels(
            project_id=project_id, scan_type=scan_type
        ).observe(violations_count)

    @staticmethod
    def record_violation(project_id: str, severity: str, policy_category: str):
        """
        Record a compliance violation.

        Args:
            project_id: UUID of the project
            severity: Violation severity (critical, high, medium, low)
            policy_category: Category of the policy violated
        """
        compliance_violations_total.labels(
            project_id=project_id, severity=severity, policy_category=policy_category
        ).inc()

    @staticmethod
    def record_policy_evaluation(
        project_id: str, policy_id: str, result: str
    ):
        """
        Record a policy evaluation result.

        Args:
            project_id: UUID of the project
            policy_id: ID of the policy evaluated
            result: Evaluation result (pass, fail, error)
        """
        compliance_policies_evaluated_total.labels(
            project_id=project_id, policy_id=policy_id, result=result
        ).inc()


class NotificationMetrics:
    """Helper class for collecting notification metrics."""

    @staticmethod
    def record_notification_sent(
        channel: str,
        notification_type: str,
        priority: str,
        delivery_seconds: float,
        status: str = "success",
    ):
        """
        Record a notification sent.

        Args:
            channel: Delivery channel (email, slack, teams, in_app)
            notification_type: Type of notification
            priority: Priority level (critical, high, medium, low)
            delivery_seconds: Time taken to deliver
            status: Delivery status (success, failed)
        """
        notifications_sent_total.labels(
            channel=channel, notification_type=notification_type, status=status
        ).inc()
        notification_delivery_seconds.labels(
            channel=channel, notification_type=notification_type
        ).observe(delivery_seconds)
        notifications_by_priority_total.labels(priority=priority).inc()

    @staticmethod
    def record_notification_failure(
        channel: str, notification_type: str, failure_reason: str
    ):
        """
        Record a notification failure.

        Args:
            channel: Delivery channel
            notification_type: Type of notification
            failure_reason: Reason for failure
        """
        notification_failures_total.labels(
            channel=channel,
            notification_type=notification_type,
            failure_reason=failure_reason,
        ).inc()

    @staticmethod
    def update_unread_count(total_unread: int):
        """Update the total unread notifications gauge."""
        notifications_unread_gauge.set(total_unread)


class GateMetrics:
    """Helper class for collecting gate metrics."""

    @staticmethod
    def record_gate_evaluation(
        project_id: str,
        gate_type: str,
        result: str,
        duration_seconds: float,
    ):
        """
        Record a gate evaluation.

        Args:
            project_id: UUID of the project
            gate_type: Type of gate (G0.1, G0.2, G1, etc.)
            result: Evaluation result (pass, fail, blocked)
            duration_seconds: Time taken for evaluation
        """
        gate_evaluations_total.labels(
            project_id=project_id, gate_type=gate_type, result=result
        ).inc()
        gate_evaluation_duration_seconds.labels(gate_type=gate_type).observe(
            duration_seconds
        )

    @staticmethod
    def update_pending_approvals(project_id: str, gate_type: str, count: int):
        """Update the pending approvals gauge."""
        gates_pending_approval.labels(
            project_id=project_id, gate_type=gate_type
        ).set(count)

    @staticmethod
    def record_approval(project_id: str, gate_type: str, approver_role: str):
        """Record a gate approval."""
        gate_approvals_total.labels(
            project_id=project_id, gate_type=gate_type, approver_role=approver_role
        ).inc()

    @staticmethod
    def record_rejection(
        project_id: str, gate_type: str, rejection_reason: str
    ):
        """Record a gate rejection."""
        gate_rejections_total.labels(
            project_id=project_id, gate_type=gate_type, rejection_reason=rejection_reason
        ).inc()


class EvidenceMetrics:
    """Helper class for collecting evidence metrics."""

    @staticmethod
    def record_upload(
        project_id: str,
        evidence_type: str,
        size_bytes: int,
        duration_seconds: float,
        status: str = "success",
    ):
        """
        Record an evidence upload.

        Args:
            project_id: UUID of the project
            evidence_type: Type of evidence
            size_bytes: File size in bytes
            duration_seconds: Upload duration
            status: Upload status (success, failed)
        """
        evidence_uploads_total.labels(
            project_id=project_id, evidence_type=evidence_type, status=status
        ).inc()
        evidence_upload_size_bytes.labels(
            project_id=project_id, evidence_type=evidence_type
        ).observe(size_bytes)
        evidence_upload_duration_seconds.labels(evidence_type=evidence_type).observe(
            duration_seconds
        )

    @staticmethod
    def update_storage_size(project_id: str, total_bytes: int):
        """Update the total storage size gauge for a project."""
        evidence_storage_bytes.labels(project_id=project_id).set(total_bytes)


class AIMetrics:
    """Helper class for collecting AI recommendation metrics."""

    @staticmethod
    def record_request(
        provider: str,
        request_type: str,
        duration_seconds: float,
        input_tokens: int,
        output_tokens: int,
        status: str = "success",
    ):
        """
        Record an AI request.

        Args:
            provider: AI provider (ollama, anthropic, openai)
            request_type: Type of request (recommendation, summary, etc.)
            duration_seconds: Request duration
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            status: Request status (success, failed)
        """
        ai_requests_total.labels(
            provider=provider, request_type=request_type, status=status
        ).inc()
        ai_request_duration_seconds.labels(
            provider=provider, request_type=request_type
        ).observe(duration_seconds)
        ai_tokens_used_total.labels(provider=provider, token_type="input").inc(
            input_tokens
        )
        ai_tokens_used_total.labels(provider=provider, token_type="output").inc(
            output_tokens
        )

    @staticmethod
    def record_fallback(from_provider: str, to_provider: str, reason: str):
        """
        Record an AI provider fallback event.

        Args:
            from_provider: Original provider that failed
            to_provider: Fallback provider used
            reason: Reason for fallback
        """
        ai_fallback_total.labels(
            from_provider=from_provider, to_provider=to_provider, reason=reason
        ).inc()

    @staticmethod
    def update_cost(provider: str, cost_usd: float):
        """Update the AI cost gauge for a provider."""
        ai_cost_usd.labels(provider=provider).set(cost_usd)


# ============================================================================
# AI COUNCIL METRICS (Sprint 26)
# ============================================================================

# Counter: Council deliberations
ai_council_deliberations_total = Counter(
    "ai_council_deliberations_total",
    "Total number of AI Council deliberation requests",
    ["mode", "status"],  # mode: single, council, auto; status: success, failed, fallback
)

# Histogram: Council deliberation duration
ai_council_duration_seconds = Histogram(
    "ai_council_duration_seconds",
    "Time taken for AI Council deliberation (seconds)",
    ["mode", "stage"],  # stage: stage1, stage2, stage3, total
    buckets=(0.5, 1.0, 2.0, 3.0, 5.0, 8.0, 10.0, 15.0, 30.0),
)

# Gauge: Council confidence scores
ai_council_confidence = Histogram(
    "ai_council_confidence_score",
    "Confidence scores from AI Council deliberations",
    ["mode"],
    buckets=(0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100),
)

# Counter: Council provider participation
ai_council_provider_used_total = Counter(
    "ai_council_provider_used_total",
    "Number of times each provider participated in council",
    ["provider", "stage"],  # stage: query, review, synthesis
)

# Counter: Council fallback events
ai_council_fallback_total = Counter(
    "ai_council_fallback_total",
    "Number of council fallback events",
    ["reason"],  # timeout, no_quorum, error
)

# Gauge: Council cost tracking
ai_council_cost_usd = Gauge(
    "ai_council_cost_usd_total",
    "Total cost of AI Council deliberations in USD",
    ["mode"],
)

# Summary: Peer review scores
ai_council_peer_review_score = Summary(
    "ai_council_peer_review_score",
    "Peer review scores given during Stage 2",
    ["reviewer", "reviewee"],
)


class AICouncilMetrics:
    """Helper class for collecting AI Council metrics."""

    @staticmethod
    def record_deliberation_start(mode: str):
        """Record start of a council deliberation."""
        pass  # Could track in-progress gauge if needed

    @staticmethod
    def record_deliberation_complete(
        mode: str,
        status: str,
        total_duration_seconds: float,
        stage1_duration_seconds: float,
        stage2_duration_seconds: float,
        stage3_duration_seconds: float,
        confidence_score: int,
        providers_used: list[str],
        total_cost_usd: float,
    ):
        """
        Record completion of a council deliberation.

        Args:
            mode: Council mode (single, council, auto)
            status: Final status (success, failed, fallback)
            total_duration_seconds: Total time for deliberation
            stage1_duration_seconds: Stage 1 duration
            stage2_duration_seconds: Stage 2 duration (0 if skipped)
            stage3_duration_seconds: Stage 3 duration (0 if skipped)
            confidence_score: Final confidence score (0-100)
            providers_used: List of providers that participated
            total_cost_usd: Total cost in USD
        """
        # Record deliberation count
        ai_council_deliberations_total.labels(mode=mode, status=status).inc()

        # Record durations
        ai_council_duration_seconds.labels(mode=mode, stage="total").observe(
            total_duration_seconds
        )
        ai_council_duration_seconds.labels(mode=mode, stage="stage1").observe(
            stage1_duration_seconds
        )
        if stage2_duration_seconds > 0:
            ai_council_duration_seconds.labels(mode=mode, stage="stage2").observe(
                stage2_duration_seconds
            )
        if stage3_duration_seconds > 0:
            ai_council_duration_seconds.labels(mode=mode, stage="stage3").observe(
                stage3_duration_seconds
            )

        # Record confidence
        ai_council_confidence.labels(mode=mode).observe(confidence_score)

        # Record provider participation
        for provider in providers_used:
            ai_council_provider_used_total.labels(
                provider=provider, stage="query"
            ).inc()

        # Update cost gauge
        ai_council_cost_usd.labels(mode=mode).inc(total_cost_usd)

    @staticmethod
    def record_stage1_complete(
        providers_queried: list[str],
        successful_count: int,
        duration_seconds: float,
        cost_usd: float,
    ):
        """Record completion of Stage 1 (parallel queries)."""
        for provider in providers_queried:
            ai_council_provider_used_total.labels(
                provider=provider, stage="query"
            ).inc()

    @staticmethod
    def record_stage2_complete(
        reviewers: list[str],
        duration_seconds: float,
        cost_usd: float,
    ):
        """Record completion of Stage 2 (peer review)."""
        for reviewer in reviewers:
            ai_council_provider_used_total.labels(
                provider=reviewer, stage="review"
            ).inc()

    @staticmethod
    def record_stage3_complete(
        chairman: str,
        duration_seconds: float,
        cost_usd: float,
    ):
        """Record completion of Stage 3 (synthesis)."""
        ai_council_provider_used_total.labels(
            provider=chairman, stage="synthesis"
        ).inc()

    @staticmethod
    def record_peer_review_score(reviewer: str, reviewee: str, score: float):
        """
        Record a peer review score.

        Args:
            reviewer: Provider giving the review
            reviewee: Provider being reviewed
            score: Score given (0-100)
        """
        ai_council_peer_review_score.labels(
            reviewer=reviewer, reviewee=reviewee
        ).observe(score)

    @staticmethod
    def record_fallback(reason: str):
        """
        Record a council fallback event.

        Args:
            reason: Reason for fallback (timeout, no_quorum, error)
        """
        ai_council_fallback_total.labels(reason=reason).inc()


# ============================================================================
# PROMETHEUS QUERIES (PromQL) FOR GRAFANA DASHBOARDS
# ============================================================================

"""
## Compliance Metrics

# Compliance scan duration (p95)
histogram_quantile(0.95, rate(compliance_scan_duration_seconds_bucket[5m]))

# Compliance score over time
compliance_score_current

# Violations per hour
rate(compliance_violations_total[1h]) * 60

# Scans completed per hour
rate(compliance_scans_total{status="completed"}[1h]) * 60

# Policy pass rate
rate(compliance_policies_evaluated_total{result="pass"}[1h]) /
rate(compliance_policies_evaluated_total[1h]) * 100


## Notification Metrics

# Notification delivery rate
rate(notifications_sent_total{status="success"}[5m])

# Notification failure rate
rate(notification_failures_total[5m])

# Notification delivery time (p95)
histogram_quantile(0.95, rate(notification_delivery_seconds_bucket[5m]))

# Notifications by channel
sum by (channel) (rate(notifications_sent_total[1h]))


## Gate Metrics

# Gate pass rate
rate(gate_evaluations_total{result="pass"}[1h]) /
rate(gate_evaluations_total[1h]) * 100

# Gates pending approval
sum(gates_pending_approval)

# Gate evaluation time (p95)
histogram_quantile(0.95, rate(gate_evaluation_duration_seconds_bucket[5m]))


## Evidence Metrics

# Evidence upload rate
rate(evidence_uploads_total{status="success"}[1h])

# Evidence storage growth
deriv(evidence_storage_bytes[1h])

# Upload duration (p95)
histogram_quantile(0.95, rate(evidence_upload_duration_seconds_bucket[5m]))


## AI Metrics

# AI request rate by provider
sum by (provider) (rate(ai_requests_total[5m]))

# AI latency by provider (p95)
histogram_quantile(0.95, rate(ai_request_duration_seconds_bucket[5m])) by (provider)

# AI cost per day
ai_cost_usd_total

# AI fallback rate
rate(ai_fallback_total[1h])

# Token usage rate
rate(ai_tokens_used_total[1h])


## AI Council Metrics (Sprint 26)

# Council deliberation rate by mode
rate(ai_council_deliberations_total[1h]) by (mode)

# Council success rate
rate(ai_council_deliberations_total{status="success"}[1h]) /
rate(ai_council_deliberations_total[1h]) * 100

# Council latency by stage (p95)
histogram_quantile(0.95, rate(ai_council_duration_seconds_bucket[5m])) by (stage)

# Council mode distribution
sum(ai_council_deliberations_total) by (mode)

# Average confidence score by mode
histogram_quantile(0.5, rate(ai_council_confidence_score_bucket[1h])) by (mode)

# Provider participation in council
sum(ai_council_provider_used_total) by (provider, stage)

# Council fallback rate by reason
rate(ai_council_fallback_total[1h]) by (reason)

# Council cost by mode
ai_council_cost_usd_total by (mode)

# Average peer review score
ai_council_peer_review_score_sum / ai_council_peer_review_score_count by (reviewer)

# Council performance target (<8s p95 for council mode)
histogram_quantile(0.95, rate(ai_council_duration_seconds_bucket{mode="council",stage="total"}[5m])) < 8
"""
