# SPRINT-43: Policy Guards & Evidence UI
## SDLC 5.1.3 Complete Lifecycle - BUILD Phase | AI Safety First (Q1 2026)

---

**Document Information**

| Field | Value |
|-------|-------|
| **Sprint ID** | SPRINT-43 |
| **Epic** | EP-02: AI Safety Layer v1 + EP-01: Idea Flow |
| **Duration** | 2 weeks (Feb 3-14, 2026) |
| **Status** | PLANNED |
| **Team** | 3 Backend + 2 Frontend + 1 DevOps + 1 QA |
| **Framework** | SDLC 5.1.3 + SASE Level 2 |
| **Prerequisites** | Sprint 42 Complete |

---

## SASE Artifact Linkage

| Artifact | Status | Location |
|----------|--------|----------|
| **BriefingScript** | ✅ Approved | [BRS-2026-003](../../05-SASE-Artifacts/BRS-2026-003-POLICY-GUARDS.yaml) |
| **MentorScript** | ✅ Active | [MTS-AI-SAFETY](../../05-SASE-Artifacts/MTS-AI-SAFETY.md) |
| **LoopScript** | ⏳ Agent generates | Per task |
| **MRP** | ⏳ Per PR | Evidence Vault |
| **VCR** | ⏳ Per approval | Evidence Vault |

---

## Executive Summary

Sprint 43 hoàn thiện AI Safety Layer v1 với Policy Guards (OPA integration) và Evidence Timeline UI. Đây là sprint cuối của core AI Safety feature trước M1 milestone (Mar 2026).

**Dependencies từ Sprint 42**:
- ✅ AI Detection Service live
- ✅ Validation Pipeline operational
- ✅ 3 core validators working
- ✅ 2-3 Design Partners onboarded
- ✅ PR Comment integration live

---

## Sprint Goals

### Primary Objectives

| # | Objective | Epic | Priority |
|---|-----------|------|----------|
| 1 | Implement Policy Guards (OPA-based) | EP-02 | P0 |
| 2 | Create Evidence Timeline UI | EP-02 | P0 |
| 3 | Add SAST validator (Semgrep) | EP-02 | P0 |
| 4 | Implement VCR override flow | EP-02 | P1 |
| 5 | Begin "Ý tưởng mới" flow UI | EP-01 | P1 |
| 6 | Onboard remaining partners (6 total) | EP-03 | P1 |

### Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Policy Guards blocking | 100% of policy fails block merge | E2E tests |
| Evidence Timeline | Viewable for all AI events | UI test |
| SAST validator | ≥5 security rules | Semgrep config |
| VCR override rate | <5% of blocked PRs | Analytics |
| Partners active | ≥6 total | CRM |
| Idea flow UI | v0.1 prototype | Demo |

---

## Week 1: Policy Guards & SAST (Feb 3-7)

### Day 1-2: Policy Guards (OPA Integration)

**BriefingScript Reference**: BRS-2026-003-TASK-01

**Objective**: Implement policy-as-code enforcement using OPA engine.

**Tasks**:

1. **Policy Pack Schema Extension**
   ```python
   # backend/app/schemas/policy_pack.py
   from pydantic import BaseModel
   from typing import List, Optional
   
   class ValidatorConfig(BaseModel):
       name: str
       enabled: bool = True
       blocking: bool = True
       config: dict = {}
   
   class PolicyRule(BaseModel):
       id: str
       name: str
       description: str
       rego_policy: str  # OPA Rego policy
       severity: str  # "critical", "high", "medium", "low"
       blocking: bool = True
       message_template: str
   
   class PolicyPackCreate(BaseModel):
       name: str
       description: str
       version: str
       tier: str  # "lite", "standard", "professional", "enterprise"
       
       # Validator configurations
       validators: List[ValidatorConfig]
       
       # Coverage thresholds
       coverage_threshold: int = 80
       coverage_blocking: bool = False
       
       # Custom OPA policies
       policies: List[PolicyRule] = []
       
       # Architecture rules
       forbidden_imports: List[str] = []
       required_patterns: List[str] = []
   ```

2. **OPA Policy Service**
   ```python
   # backend/app/services/opa_policy_service.py
   import httpx
   from typing import List
   
   class OPAPolicyService:
       def __init__(self, opa_url: str = "http://opa:8181"):
           self.opa_url = opa_url
       
       async def evaluate_policies(
           self,
           policies: List[PolicyRule],
           input_data: dict
       ) -> List[PolicyResult]:
           results = []
           
           for policy in policies:
               result = await self._evaluate_single(policy, input_data)
               results.append(result)
           
           return results
       
       async def _evaluate_single(
           self,
           policy: PolicyRule,
           input_data: dict
       ) -> PolicyResult:
           # Load policy to OPA
           await httpx.put(
               f"{self.opa_url}/v1/policies/{policy.id}",
               content=policy.rego_policy
           )
           
           # Evaluate
           response = await httpx.post(
               f"{self.opa_url}/v1/data/{policy.id}/allow",
               json={"input": input_data}
           )
           
           result_data = response.json()
           passed = result_data.get("result", False)
           
           return PolicyResult(
               policy_id=policy.id,
               policy_name=policy.name,
               passed=passed,
               severity=policy.severity,
               blocking=policy.blocking,
               message=policy.message_template if not passed else None
           )
   ```

3. **Default AI Safety Policies**
   ```rego
   # policy-packs/rego/ai-safety/no-hardcoded-secrets.rego
   package ai_safety.no_hardcoded_secrets
   
   import future.keywords.in
   
   default allow = true
   
   # Deny if hardcoded secrets detected
   allow = false {
       some file in input.files
       some line in file.content
       contains_secret(line)
   }
   
   contains_secret(line) {
       patterns := [
           "password\\s*=\\s*['\"][^'\"]+['\"]",
           "api_key\\s*=\\s*['\"][^'\"]+['\"]",
           "secret\\s*=\\s*['\"][^'\"]+['\"]",
       ]
       some pattern in patterns
       regex.match(pattern, line)
   }
   ```
   
   ```rego
   # policy-packs/rego/ai-safety/no-legacy-imports.rego
   package ai_safety.no_legacy_imports
   
   default allow = true
   
   # Configurable forbidden imports
   forbidden := input.config.forbidden_imports
   
   allow = false {
       some file in input.files
       some import_stmt in file.imports
       some forbidden_import in forbidden
       startswith(import_stmt, forbidden_import)
   }
   ```
   
   ```rego
   # policy-packs/rego/ai-safety/architecture-boundaries.rego
   package ai_safety.architecture_boundaries
   
   default allow = true
   
   # Check layer violations
   allow = false {
       some file in input.files
       file.layer == "presentation"
       some import_stmt in file.imports
       layer_of_import(import_stmt) == "data"
   }
   
   layer_of_import(import_stmt) = "data" {
       startswith(import_stmt, "app.db")
   }
   
   layer_of_import(import_stmt) = "data" {
       startswith(import_stmt, "app.repositories")
   }
   ```

4. **Policy Guard Validator**
   ```python
   # backend/app/services/validators/policy_guard_validator.py
   class PolicyGuardValidator(BaseValidator):
       name = "policy_guards"
       blocking = True
       
       def __init__(self, opa_service: OPAPolicyService):
           self.opa_service = opa_service
       
       async def validate(
           self, project_id, pr_number, files, diff
       ) -> ValidatorResult:
           start = time.time()
           
           # Get project's policy pack
           policy_pack = await get_project_policy_pack(project_id)
           
           if not policy_pack.policies:
               return ValidatorResult(
                   validator_name=self.name,
                   status=ValidatorStatus.SKIPPED,
                   message="No custom policies configured",
                   details={},
                   duration_ms=0,
                   blocking=False
               )
           
           # Prepare input for OPA
           input_data = await self._prepare_input(files, diff, policy_pack)
           
           # Evaluate all policies
           results = await self.opa_service.evaluate_policies(
               policy_pack.policies, input_data
           )
           
           # Check for blocking failures
           failures = [r for r in results if not r.passed]
           blocking_failures = [r for r in failures if r.blocking]
           
           duration = int((time.time() - start) * 1000)
           
           return ValidatorResult(
               validator_name=self.name,
               status=(
                   ValidatorStatus.PASSED if not blocking_failures
                   else ValidatorStatus.FAILED
               ),
               message=f"{len(failures)} policy violations" if failures else "All policies passed",
               details={
                   "total_policies": len(results),
                   "passed": len([r for r in results if r.passed]),
                   "failed": len(failures),
                   "blocking_failures": [f.policy_name for f in blocking_failures],
                   "violations": [
                       {"policy": f.policy_name, "message": f.message}
                       for f in failures
                   ]
               },
               duration_ms=duration,
               blocking=bool(blocking_failures)
           )
   ```

**Deliverables**:
- [ ] PolicyPack schema extended
- [ ] OPAPolicyService implemented
- [ ] 3 default AI safety policies
- [ ] PolicyGuardValidator implemented
- [ ] Integration tests with OPA

**Assignee**: Backend Lead + Backend Dev 1
**Estimated**: 2 days

---

### Day 3-4: SAST Validator (Semgrep)

**BriefingScript Reference**: BRS-2026-003-TASK-02

**Objective**: Add security static analysis using Semgrep.

**Tasks**:

1. **Semgrep Integration Service**
   ```python
   # backend/app/services/semgrep_service.py
   import subprocess
   import json
   from pathlib import Path
   
   class SemgrepService:
       def __init__(self, config_path: str = "semgrep.yaml"):
           self.config_path = config_path
       
       async def scan(
           self,
           target_path: str,
           rules: List[str] = None
       ) -> SemgrepResult:
           cmd = [
               "semgrep",
               "--json",
               "--config", self.config_path,
               target_path
           ]
           
           if rules:
               for rule in rules:
                   cmd.extend(["--config", rule])
           
           result = subprocess.run(
               cmd,
               capture_output=True,
               text=True,
               timeout=300  # 5 minute timeout
           )
           
           output = json.loads(result.stdout)
           
           return SemgrepResult(
               findings=self._parse_findings(output),
               errors=output.get("errors", []),
               stats=output.get("stats", {})
           )
       
       def _parse_findings(self, output: dict) -> List[Finding]:
           findings = []
           for result in output.get("results", []):
               findings.append(Finding(
                   rule_id=result["check_id"],
                   severity=result["extra"]["severity"],
                   message=result["extra"]["message"],
                   file=result["path"],
                   line=result["start"]["line"],
                   code=result["extra"].get("lines", "")
               ))
           return findings
   ```

2. **Semgrep Rules Configuration**
   ```yaml
   # semgrep.yaml
   rules:
     # SQL Injection
     - id: python-sql-injection
       pattern: |
         cursor.execute($QUERY % ...)
       message: "Possible SQL injection via string formatting"
       severity: ERROR
       languages: [python]
   
     # Command Injection
     - id: python-command-injection
       patterns:
         - pattern: os.system($CMD)
         - pattern: subprocess.call($CMD, shell=True)
       message: "Possible command injection"
       severity: ERROR
       languages: [python]
   
     # Hardcoded Secrets
     - id: hardcoded-password
       pattern-regex: '(password|passwd|pwd)\s*=\s*["\'][^"\']+["\']'
       message: "Hardcoded password detected"
       severity: WARNING
       languages: [python, javascript, typescript]
   
     # Insecure Random
     - id: insecure-random
       pattern: random.random()
       message: "Use secrets module for security-sensitive randomness"
       severity: WARNING
       languages: [python]
   
     # Debug Endpoints
     - id: debug-endpoint
       patterns:
         - pattern: '@app.route("/debug/...")'
         - pattern: 'DEBUG = True'
       message: "Debug code detected"
       severity: WARNING
       languages: [python]
   ```

3. **SAST Validator**
   ```python
   # backend/app/services/validators/sast_validator.py
   class SASTValidator(BaseValidator):
       name = "sast"
       blocking = True  # Critical/Error findings block
       
       def __init__(self, semgrep_service: SemgrepService):
           self.semgrep_service = semgrep_service
       
       async def validate(
           self, project_id, pr_number, files, diff
       ) -> ValidatorResult:
           start = time.time()
           
           # Get policy pack SAST config
           policy_pack = await get_project_policy_pack(project_id)
           sast_config = policy_pack.validators_config.get("sast", {})
           
           # Determine files to scan
           scannable_files = [
               f for f in files
               if f.endswith((".py", ".js", ".ts", ".tsx"))
           ]
           
           if not scannable_files:
               return ValidatorResult(
                   validator_name=self.name,
                   status=ValidatorStatus.SKIPPED,
                   message="No scannable files",
                   details={},
                   duration_ms=0,
                   blocking=False
               )
           
           # Run Semgrep
           result = await self.semgrep_service.scan(
               target_path=await self._prepare_files(scannable_files),
               rules=sast_config.get("rules", [])
           )
           
           # Categorize findings
           critical = [f for f in result.findings if f.severity == "ERROR"]
           warnings = [f for f in result.findings if f.severity == "WARNING"]
           
           # Determine blocking
           block_on_critical = sast_config.get("block_on_critical", True)
           block_on_warning = sast_config.get("block_on_warning", False)
           
           should_block = (
               (block_on_critical and critical) or
               (block_on_warning and warnings)
           )
           
           duration = int((time.time() - start) * 1000)
           
           return ValidatorResult(
               validator_name=self.name,
               status=(
                   ValidatorStatus.FAILED if should_block
                   else ValidatorStatus.PASSED
               ),
               message=f"{len(critical)} critical, {len(warnings)} warnings",
               details={
                   "critical_count": len(critical),
                   "warning_count": len(warnings),
                   "findings": [
                       {
                           "rule": f.rule_id,
                           "severity": f.severity,
                           "file": f.file,
                           "line": f.line,
                           "message": f.message
                       }
                       for f in result.findings[:20]  # Limit
                   ]
               },
               duration_ms=duration,
               blocking=should_block
           )
   ```

**Deliverables**:
- [ ] SemgrepService implemented
- [ ] 5+ Semgrep rules configured
- [ ] SASTValidator implemented
- [ ] Integration tests
- [ ] Performance validation (<2 min scan)

**Assignee**: Backend Dev 2 + Security Review
**Estimated**: 2 days

---

### Day 5: VCR Override Flow

**BriefingScript Reference**: BRS-2026-003-TASK-03

**Objective**: Implement Version Controlled Resolution (VCR) override flow.

**Tasks**:

1. **VCR API Endpoints**
   ```python
   # backend/app/api/routes/vcr.py
   from fastapi import APIRouter, Depends
   
   router = APIRouter(prefix="/vcr", tags=["VCR"])
   
   @router.post("/{event_id}/request")
   async def request_override(
       event_id: UUID,
       request: VCRRequest,
       db: Session = Depends(get_db),
       current_user: User = Depends(get_current_user)
   ):
       """Request a VCR override for blocked AI PR."""
       event = await db.get(AICodeEvent, event_id)
       
       if event.validation_status != ValidationStatus.FAILED:
           raise HTTPException(400, "Event is not in failed state")
       
       # Create VCR request
       vcr = VCRRequest(
           event_id=event_id,
           requested_by=current_user.id,
           reason=request.reason,
           risk_assessment=request.risk_assessment,
           mitigation_plan=request.mitigation_plan,
           status="pending"
       )
       db.add(vcr)
       await db.commit()
       
       # Notify approvers
       await notify_vcr_request(event, vcr)
       
       return vcr
   
   @router.post("/{event_id}/approve")
   async def approve_override(
       event_id: UUID,
       approval: VCRApproval,
       db: Session = Depends(get_db),
       current_user: User = Depends(require_vcr_approver)
   ):
       """Approve VCR override (requires approver role)."""
       event = await db.get(AICodeEvent, event_id)
       vcr = await get_pending_vcr(event_id)
       
       # Update VCR
       vcr.status = "approved"
       vcr.approved_by = current_user.id
       vcr.approved_at = datetime.utcnow()
       vcr.approver_comments = approval.comments
       
       # Update event
       event.override_approved = True
       event.override_reason = vcr.reason
       event.override_approved_by = current_user.id
       event.override_approved_at = datetime.utcnow()
       event.validation_status = ValidationStatus.OVERRIDDEN
       
       await db.commit()
       
       # Update GitHub PR status
       await github_service.update_check_status(
           event.project_id,
           event.pr_number,
           status="success",
           description="VCR override approved"
       )
       
       # Audit log
       await audit_service.log(
           action="vcr_approved",
           actor=current_user,
           target_type="ai_code_event",
           target_id=event_id,
           details={"reason": vcr.reason}
       )
       
       return {"status": "approved", "event": event}
   
   @router.post("/{event_id}/reject")
   async def reject_override(
       event_id: UUID,
       rejection: VCRRejection,
       db: Session = Depends(get_db),
       current_user: User = Depends(require_vcr_approver)
   ):
       """Reject VCR override."""
       vcr = await get_pending_vcr(event_id)
       
       vcr.status = "rejected"
       vcr.rejected_by = current_user.id
       vcr.rejected_at = datetime.utcnow()
       vcr.rejection_reason = rejection.reason
       
       await db.commit()
       
       # Notify requester
       await notify_vcr_rejection(vcr)
       
       return {"status": "rejected"}
   ```

2. **VCR Request Schema**
   ```python
   # backend/app/schemas/vcr.py
   from pydantic import BaseModel, Field
   
   class VCRRequest(BaseModel):
       reason: str = Field(..., min_length=20, max_length=2000)
       risk_assessment: str = Field(..., min_length=10)
       mitigation_plan: str = Field(..., min_length=10)
       urgency: str = Field(default="normal")  # "critical", "high", "normal"
   
   class VCRApproval(BaseModel):
       comments: str = Field(default="")
   
   class VCRRejection(BaseModel):
       reason: str = Field(..., min_length=10)
   ```

3. **VCR Audit Trail**
   ```python
   # Store full audit trail in Evidence Vault
   class VCRRecord(Base):
       __tablename__ = "vcr_records"
       
       id = Column(UUID, primary_key=True)
       event_id = Column(UUID, ForeignKey("ai_code_events.id"))
       
       # Request
       requested_by = Column(UUID, ForeignKey("users.id"))
       requested_at = Column(DateTime, default=datetime.utcnow)
       reason = Column(Text, nullable=False)
       risk_assessment = Column(Text)
       mitigation_plan = Column(Text)
       urgency = Column(String(20))
       
       # Resolution
       status = Column(String(20))  # pending, approved, rejected
       resolved_by = Column(UUID, ForeignKey("users.id"))
       resolved_at = Column(DateTime)
       resolution_comments = Column(Text)
       
       # Context snapshot
       blocking_policies = Column(JSONB)  # What was blocked
       pr_snapshot = Column(JSONB)  # PR state at request time
   ```

**Deliverables**:
- [ ] VCR API endpoints (request, approve, reject)
- [ ] VCR schemas
- [ ] VCR audit trail model
- [ ] Notification integration
- [ ] GitHub status update

**Assignee**: Backend Lead
**Estimated**: 1 day

---

## Week 2: Evidence UI & Idea Flow (Feb 10-14)

### Day 6-7: Evidence Timeline UI

**BriefingScript Reference**: BRS-2026-003-TASK-04

**Objective**: Create visual timeline of AI code event lifecycle.

**Tasks**:

1. **Timeline Component**
   ```typescript
   // frontend/web/src/components/evidence/EvidenceTimeline.tsx
   import { Timeline, TimelineItem } from '@/components/ui/timeline';
   
   interface AICodeEventTimeline {
     event: AICodeEvent;
     validators: ValidatorResult[];
     policies: PolicyResult[];
     vcr?: VCRRecord;
   }
   
   export function EvidenceTimeline({ data }: { data: AICodeEventTimeline }) {
     const items = buildTimelineItems(data);
     
     return (
       <div className="space-y-4">
         <h2 className="text-xl font-bold">Evidence Timeline</h2>
         
         <Timeline>
           {items.map((item, i) => (
             <TimelineItem
               key={i}
               icon={getIcon(item.type)}
               title={item.title}
               timestamp={item.timestamp}
               status={item.status}
             >
               <TimelineContent item={item} />
             </TimelineItem>
           ))}
         </Timeline>
       </div>
     );
   }
   
   function buildTimelineItems(data: AICodeEventTimeline): TimelineItem[] {
     const items: TimelineItem[] = [];
     
     // 1. PR Created
     items.push({
       type: "pr_created",
       title: "Pull Request Opened",
       timestamp: data.event.created_at,
       status: "completed",
       details: {
         pr_number: data.event.pr_number,
         author: data.event.pr_author,
         title: data.event.pr_title
       }
     });
     
     // 2. AI Detection
     items.push({
       type: "ai_detected",
       title: `AI Tool Detected: ${data.event.ai_tool}`,
       timestamp: data.event.created_at,
       status: "completed",
       details: {
         tool: data.event.ai_tool,
         model: data.event.ai_model,
         confidence: data.event.detection_confidence,
         method: data.event.detection_method
       }
     });
     
     // 3. Validation Started
     items.push({
       type: "validation_started",
       title: "Validation Pipeline Started",
       timestamp: data.event.validation_started_at,
       status: "completed",
     });
     
     // 4. Each Validator
     data.validators.forEach(v => {
       items.push({
         type: "validator",
         title: `${v.validator_name}: ${v.status}`,
         timestamp: v.completed_at,
         status: v.status === "passed" ? "success" : v.status === "failed" ? "error" : "warning",
         details: v.details
       });
     });
     
     // 5. Policy Checks
     data.policies.forEach(p => {
       items.push({
         type: "policy",
         title: `Policy: ${p.policy_name}`,
         timestamp: p.evaluated_at,
         status: p.passed ? "success" : "error",
         details: { message: p.message }
       });
     });
     
     // 6. Validation Complete
     items.push({
       type: "validation_complete",
       title: `Validation ${data.event.validation_status}`,
       timestamp: data.event.validation_completed_at,
       status: data.event.validation_status === "passed" ? "success" : "error",
       details: {
         duration: data.event.validation_duration_ms
       }
     });
     
     // 7. VCR (if exists)
     if (data.vcr) {
       items.push({
         type: "vcr_requested",
         title: "Override Requested (VCR)",
         timestamp: data.vcr.requested_at,
         status: "pending",
         details: { reason: data.vcr.reason }
       });
       
       if (data.vcr.resolved_at) {
         items.push({
           type: data.vcr.status === "approved" ? "vcr_approved" : "vcr_rejected",
           title: `Override ${data.vcr.status}`,
           timestamp: data.vcr.resolved_at,
           status: data.vcr.status === "approved" ? "success" : "error",
           details: { comments: data.vcr.resolution_comments }
         });
       }
     }
     
     return items.sort((a, b) => 
       new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
     );
   }
   ```

2. **Event Detail Page**
   ```typescript
   // frontend/web/src/pages/AICodeEventPage.tsx
   import { useParams } from 'react-router-dom';
   import { EvidenceTimeline } from '@/components/evidence/EvidenceTimeline';
   
   export function AICodeEventPage() {
     const { eventId } = useParams();
     const { data: event, isLoading } = useAICodeEvent(eventId);
     
     if (isLoading) return <Spinner />;
     
     return (
       <div className="container mx-auto py-8 space-y-8">
         {/* Header */}
         <div className="flex justify-between items-center">
           <div>
             <h1 className="text-2xl font-bold">AI Code Event</h1>
             <p className="text-muted-foreground">
               PR #{event.pr_number}: {event.pr_title}
             </p>
           </div>
           <StatusBadge status={event.validation_status} />
         </div>
         
         {/* Summary Cards */}
         <div className="grid grid-cols-4 gap-4">
           <SummaryCard 
             title="AI Tool" 
             value={event.ai_tool} 
             icon={<BotIcon />} 
           />
           <SummaryCard 
             title="Confidence" 
             value={`${(event.detection_confidence * 100).toFixed(0)}%`} 
             icon={<TargetIcon />} 
           />
           <SummaryCard 
             title="Duration" 
             value={formatDuration(event.validation_duration_ms)} 
             icon={<ClockIcon />} 
           />
           <SummaryCard 
             title="Files Changed" 
             value={event.files_changed?.length || 0} 
             icon={<FileIcon />} 
           />
         </div>
         
         {/* Timeline */}
         <EvidenceTimeline data={event} />
         
         {/* Actions */}
         {event.validation_status === "failed" && !event.override_approved && (
           <VCRRequestForm eventId={eventId} />
         )}
         
         {/* Raw Data (collapsible) */}
         <Collapsible title="Raw Event Data">
           <pre className="bg-muted p-4 rounded text-sm">
             {JSON.stringify(event, null, 2)}
           </pre>
         </Collapsible>
       </div>
     );
   }
   ```

3. **Event List with Filters**
   ```typescript
   // frontend/web/src/pages/AICodeEventsPage.tsx
   export function AICodeEventsPage() {
     const [filters, setFilters] = useState<EventFilters>({
       status: null,
       ai_tool: null,
       date_range: "7d"
     });
     
     const { data: events } = useAICodeEvents(filters);
     
     return (
       <div className="space-y-6">
         <h1 className="text-2xl font-bold">AI Code Events</h1>
         
         {/* Filters */}
         <div className="flex gap-4">
           <Select 
             value={filters.status} 
             onValueChange={(v) => setFilters({...filters, status: v})}
           >
             <SelectItem value={null}>All Status</SelectItem>
             <SelectItem value="passed">Passed</SelectItem>
             <SelectItem value="failed">Failed</SelectItem>
             <SelectItem value="overridden">Overridden</SelectItem>
           </Select>
           
           <Select 
             value={filters.ai_tool}
             onValueChange={(v) => setFilters({...filters, ai_tool: v})}
           >
             <SelectItem value={null}>All Tools</SelectItem>
             <SelectItem value="cursor">Cursor</SelectItem>
             <SelectItem value="copilot">Copilot</SelectItem>
             <SelectItem value="claude_code">Claude Code</SelectItem>
           </Select>
           
           <DateRangePicker 
             value={filters.date_range}
             onChange={(v) => setFilters({...filters, date_range: v})}
           />
         </div>
         
         {/* Table */}
         <DataTable columns={eventColumns} data={events} />
       </div>
     );
   }
   ```

**Deliverables**:
- [ ] EvidenceTimeline component
- [ ] AICodeEventPage
- [ ] AICodeEventsPage with filters
- [ ] VCRRequestForm component
- [ ] API integration hooks

**Assignee**: Frontend Dev 1 + Frontend Dev 2
**Estimated**: 2 days

---

### Day 8-9: "Ý tưởng mới" Flow UI (Prototype)

**BriefingScript Reference**: BRS-2026-003-TASK-05

**Objective**: Begin EP-01 "New Idea" flow UI prototype.

**Tasks**:

1. **Idea Input Form**
   ```typescript
   // frontend/web/src/pages/NewIdeaPage.tsx
   import { useState } from 'react';
   import { Textarea } from '@/components/ui/textarea';
   
   export function NewIdeaPage() {
     const [idea, setIdea] = useState("");
     const [isAnalyzing, setIsAnalyzing] = useState(false);
     const [analysis, setAnalysis] = useState<IdeaAnalysis | null>(null);
     
     const handleAnalyze = async () => {
       setIsAnalyzing(true);
       try {
         const result = await analyzeIdea(idea);
         setAnalysis(result);
       } finally {
         setIsAnalyzing(false);
       }
     };
     
     return (
       <div className="container mx-auto py-8 max-w-3xl">
         <h1 className="text-3xl font-bold mb-8">💡 Ý tưởng mới</h1>
         
         {/* Input Section */}
         <div className="space-y-4">
           <label className="text-lg font-medium">
             Mô tả ý tưởng của bạn (VN/EN)
           </label>
           <Textarea
             value={idea}
             onChange={(e) => setIdea(e.target.value)}
             placeholder="Ví dụ: Tôi muốn xây dựng một API để quản lý inventory cho kho hàng, hỗ trợ real-time updates và báo cáo..."
             className="min-h-[200px] text-lg"
           />
           <Button 
             onClick={handleAnalyze} 
             disabled={idea.length < 20 || isAnalyzing}
             className="w-full"
           >
             {isAnalyzing ? (
               <>
                 <Spinner className="mr-2" />
                 Đang phân tích...
               </>
             ) : (
               "🔍 Phân tích ý tưởng"
             )}
           </Button>
         </div>
         
         {/* Analysis Result */}
         {analysis && (
           <IdeaAnalysisResult analysis={analysis} />
         )}
       </div>
     );
   }
   ```

2. **Idea Analysis Result Component**
   ```typescript
   // frontend/web/src/components/idea/IdeaAnalysisResult.tsx
   interface IdeaAnalysis {
     classification: "epic" | "feature" | "experiment";
     risk_tier: "low" | "medium" | "high";
     effort_estimate: string;  // "S", "M", "L", "XL"
     recommended_path: string[];  // SDLC stages
     suggested_policy_pack: PolicyPack;
     next_steps: string[];
     recommendation: "build" | "explore" | "park";
   }
   
   export function IdeaAnalysisResult({ analysis }: { analysis: IdeaAnalysis }) {
     return (
       <div className="mt-8 space-y-6">
         {/* Classification Card */}
         <Card>
           <CardHeader>
             <CardTitle>📊 Phân loại ý tưởng</CardTitle>
           </CardHeader>
           <CardContent className="grid grid-cols-3 gap-4">
             <div>
               <p className="text-sm text-muted-foreground">Loại</p>
               <Badge variant="outline">{analysis.classification}</Badge>
             </div>
             <div>
               <p className="text-sm text-muted-foreground">Rủi ro</p>
               <Badge variant={getRiskVariant(analysis.risk_tier)}>
                 {analysis.risk_tier}
               </Badge>
             </div>
             <div>
               <p className="text-sm text-muted-foreground">Effort</p>
               <Badge>{analysis.effort_estimate}</Badge>
             </div>
           </CardContent>
         </Card>
         
         {/* Recommendation */}
         <Card className={getRecommendationStyle(analysis.recommendation)}>
           <CardHeader>
             <CardTitle>
               {analysis.recommendation === "build" && "✅ Khuyến nghị: XÂY DỰNG"}
               {analysis.recommendation === "explore" && "🔍 Khuyến nghị: KHÁM PHÁ THÊM"}
               {analysis.recommendation === "park" && "⏸️ Khuyến nghị: TẠM DỪNG"}
             </CardTitle>
           </CardHeader>
           <CardContent>
             <ul className="list-disc list-inside space-y-2">
               {analysis.next_steps.map((step, i) => (
                 <li key={i}>{step}</li>
               ))}
             </ul>
           </CardContent>
         </Card>
         
         {/* SDLC Path */}
         <Card>
           <CardHeader>
             <CardTitle>🛤️ Lộ trình SDLC đề xuất</CardTitle>
           </CardHeader>
           <CardContent>
             <div className="flex gap-2">
               {analysis.recommended_path.map((stage, i) => (
                 <Badge key={i} variant="secondary">
                   {stage}
                 </Badge>
               ))}
             </div>
           </CardContent>
         </Card>
         
         {/* Policy Pack */}
         <Card>
           <CardHeader>
             <CardTitle>📋 Policy Pack đề xuất</CardTitle>
           </CardHeader>
           <CardContent>
             <PolicyPackPreview pack={analysis.suggested_policy_pack} />
           </CardContent>
           <CardFooter>
             <Button>Áp dụng Policy Pack này</Button>
           </CardFooter>
         </Card>
       </div>
     );
   }
   ```

3. **Idea Analysis API (Stub)**
   ```python
   # backend/app/api/routes/ideas.py
   @router.post("/analyze")
   async def analyze_idea(
       request: IdeaAnalysisRequest,
       db: Session = Depends(get_db),
       current_user: User = Depends(get_current_user)
   ):
       """Analyze a new idea using AI Council."""
       # Use AI Council service for analysis
       analysis = await ai_council_service.analyze_idea(
           idea_text=request.idea_text,
           language=request.language or "auto"
       )
       
       # Track event
       await analytics.track_event(
           user_id=str(current_user.id),
           event_name="idea_submitted",
           properties={"classification": analysis.classification}
       )
       
       return analysis
   ```

**Deliverables**:
- [ ] NewIdeaPage component
- [ ] IdeaAnalysisResult component
- [ ] Idea analysis API endpoint (stub)
- [ ] Basic AI Council integration
- [ ] Analytics tracking

**Assignee**: Frontend Dev 1 + Backend Dev 1
**Estimated**: 2 days

---

### Day 10: Partner Onboarding & Sprint Retro

**Tasks**:

1. **Onboard Remaining Partners**
   - Target: 3 more partners (total 6)
   - Follow Sprint 42 onboarding checklist
   - Schedule bi-weekly feedback calls

2. **Sprint 43 Retrospective**
   ```yaml
   Metrics Review:
     Policy Guards:
       - Policies enforced: X
       - Blocking rate: X%
       - False positive rate: X%
     
     SAST:
       - Files scanned: X
       - Findings: X critical, X warning
       - Time per scan: X min
     
     VCR:
       - Requests: X
       - Approved: X
       - Rejected: X
       - Override rate: X%
     
     Evidence UI:
       - Page views: X
       - Time on page: X min
     
     Idea Flow:
       - Ideas analyzed: X
       - Build recommendations: X%
     
     Partners:
       - Total active: X/6
       - AI PRs processed: X
       - Feedback items: X
   ```

3. **M1 Milestone Check**
   ```yaml
   M1 Target (Mar 2026):
     - AI-Intent Flows live for internal teams: Partial (Idea flow in progress)
     - ≥70% internal adoption: TBD
     - AI Safety Layer v1 protecting AI PRs: ✅ Core complete
     
   Sprint 43 Status:
     - Detection: ✅ Live
     - Validators: ✅ 4 validators (Lint, Tests, Coverage, SAST)
     - Policy Guards: ✅ Live
     - Evidence Trail: ✅ Live
     - VCR Override: ✅ Live
     
   Remaining for M1:
     - Complete Idea Flow (EP-01)
     - Complete Stalled Project Flow (EP-01)
     - Internal adoption push
   ```

**Deliverables**:
- [ ] 3 more partners onboarded (6 total)
- [ ] Retro notes documented
- [ ] M1 gap analysis
- [ ] Sprint 44 planning complete

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| OPA policy complexity | Medium | Medium | Start with simple rules, iterate |
| SAST false positives | High | Medium | Tunable severity thresholds |
| VCR abuse (too many overrides) | High | Low | Audit reports, escalation rules |
| Evidence UI performance | Medium | Low | Pagination, lazy loading |
| Idea flow AI accuracy | Medium | Medium | Human review, feedback loop |

---

## Dependencies

| Dependency | Owner | Status | Impact if Delayed |
|------------|-------|--------|-------------------|
| Sprint 42 complete | Team | ⏳ | Block all tasks |
| OPA engine upgrade | DevOps | ⏳ | Block Policy Guards |
| Semgrep license | Security | ✅ Ready | - |
| Partner contracts (3 more) | Legal | ⏳ | Block onboarding |
| AI Council API stable | AI Team | ✅ Ready | - |

---

## Team Allocation

| Role | Name | Focus Areas | Capacity |
|------|------|-------------|----------|
| Backend Lead | TBD | Policy Guards, VCR | 100% |
| Backend Dev 1 | TBD | Idea API, Integration | 100% |
| Backend Dev 2 | TBD | SAST Validator | 100% |
| Frontend Dev 1 | TBD | Evidence UI, Idea UI | 100% |
| Frontend Dev 2 | TBD | Timeline, Components | 100% |
| DevOps | TBD | OPA, Infrastructure | 50% |
| Product | TBD | Partner Onboarding | 100% |
| QA | TBD | E2E Tests | 100% |

---

## Definition of Done (Sprint Level)

- [ ] All P0 tasks completed
- [ ] Policy Guards blocking 100%
- [ ] Evidence Timeline viewable
- [ ] SAST validator operational
- [ ] VCR flow working end-to-end
- [ ] Idea flow prototype demoable
- [ ] ≥6 partners onboarded
- [ ] Code reviewed (MRP for all PRs)
- [ ] No P0/P1 bugs

---

## Next Sprint Preview

**Sprint 44** (Feb 17 - Feb 28, 2026): Stalled Project Flow & M1 Polish
- Complete "Dự án dở dang" analysis flow
- Portfolio dashboard for CTO persona
- Performance optimization (<6 min p95)
- Internal adoption campaign
- M1 milestone preparation

---

*Document Version: 1.0.0 | Created: December 20, 2025 | Framework: SDLC 5.1.3*
