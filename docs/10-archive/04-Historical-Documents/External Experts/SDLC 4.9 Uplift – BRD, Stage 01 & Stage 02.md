# SDLC 5.1.3 Uplift – BRD, Stage 01 & Stage 02 (Patch Pack v1.0)

**Date:** 16/11/2025
**Scope:** Đồng bộ BRD + Stage 01 + Stage 02 lên **SDLC 5.1.3** theo khuôn đã áp dụng cho **Stage 00** (Policy Pack, Evidence Schema, Deploy Readiness, PR Checks).
**How to use:** Mỗi khối dưới đây là **PATCH** (thêm/mở rộng) – copy vào đúng mục tương ứng trong canvas hiện tại.

---

## A) BRD – SDLC ORCHESTRATOR (4.9 uplift)

### A.1 Thay thế tiến trình SDLC

**Find:** `WHY→WHAT→HOW→BUILD→TEST→OPERATE`
**Replace:** `WHY→WHAT→HOW→BUILD→TEST→DEPLOY(05)→OPERATE`

### A.2 Thêm mục mới sau “8. Tích hợp (Integrations)”

**Heading:** `8.B SDLC 5.1.3 – Gate Map & PR Checks`

```
**G0.1 – Problem Defined (WHY):** problem_statement, success_metrics, ≥5 interviews; Approvals: Product Lead.  
**G0.2 – Solution Diversity (WHAT):** ≥100 ideas, ≥10 themes, ≥3 concepts + scorecards; Approvals: Product Lead, CTO.  
**G2 – Design Ready (HOW):** ADR, OpenAPI lint PASS, DB/ERD, TDD diagrams, OWASP baseline; Approvals: Tech Lead, Security Lead.  
**G3 – Ship Ready (BUILD/TEST):** tests_pass≥90% (critical), coverage≥80%, perf PASS, release notes draft; Approvals: QA Lead, PM.  
**G4 – Deploy Readiness (DEPLOY – Stage 05):** RELEASE_NOTES.md, SBOM (Syft/CycloneDX), cosign attestations, OpenAPI‑Diff (no‑breaking/waiver), rollback/flags/migration; Approvals: Release Manager, Tech Lead (+ Security khi cần).  
**G5 – Operate Ready (OPERATE):** runbook, on‑call, critical alerts, SLA declared; Approvals: SRE Lead.

**PR Checks contract:** `gate/G0.1`, `gate/G0.2`, `gate/G2`, `gate/G3`, `gate/G4`, `gate/G5` → PASS/FAIL + deep‑link Evidence.
```

### A.3 Thêm mục mới sau “10. Lộ trình MVP 90 ngày”

**Heading:** `10.A Policy Pack v0.9 (Tiered Compliance)`

```
- **Lite:** coverage≥70%, OWASP_BASELINE, perf: baseline, waiver.max=2, waiver.ttl≤21d.  
- **Standard:** coverage≥80%, SAST: PASS, OpenAPI‑Diff: no‑breaking, perf: target, evidence.auto≥60%.  
- **Enterprise:** + DAST, SBOM+attestations bắt buộc, operate.preview required, evidence.auto≥70%, SRE approval ở G2/G5.
```

### A.4 Thêm mục mới sau “14. Chế độ triển khai (Bridge vs Native)”

**Heading:** `17. Evidence Schema v0.9 (Vault)`

```
Metadata bắt buộc: {stage, gate, evidence_type, file_hash, owner, pr_id, run_id, timestamp, link}.
Lưu trữ: Orchdocs (docs) vs Artifacts/S3 (CI results). Immutability: hash+timestamp; audit log bất biến.
```

---

## B) STAGE 01 – Planning & Analysis (WHAT) – 4.9 uplift

### B.1 Thay thế tiến trình SDLC

**Find:** `WHY→WHAT→HOW→BUILD→TEST→OPERATE`
**Replace:** `WHY→WHAT→HOW→BUILD→TEST→DEPLOY(05)→OPERATE`

### B.2 Bổ sung “Gate Map WHAT → HOW” (sau mục 6. Gates & Evidence)

```
**G0.2 – Solution Diversity:** Evidence: Solution Gallery, Themes, Shortlist≥3, Scorecards; Approvals: Product Lead, CTO.
**G1 – Requirements Ready (optional by tier):** Evidence: requirements (MoSCoW/Job stories/AC), success metrics, Phase/Sprint skeleton; Approvals: PM/PO, Tech Lead.
**PR Checks:** `gate/G0.2`, `gate/G1` (nếu bật) → PASS/FAIL + deep‑link Evidence.
```

### B.3 Thêm mục “Policy Pack v0.9 – WHAT tiering” (sau mục 4. Tiered Compliance)

```
- **Lite:** Gallery ≥30/≥5/≥2; BRD 1‑page; Phase/Sprint skeleton; auto‑evidence≥40%.  
- **Standard:** Gallery ≥100/≥10/≥3; Scorecards; ADR‑seed; KPI (Tri‑layer + DORA); auto‑evidence≥60%.  
- **Enterprise:** + risk register, compliance checklist, stakeholder sign‑off; auto‑evidence≥70%.
```

### B.4 Thêm mục “Evidence Schema v0.9 (WHAT)” (trước mục 11. Ràng buộc & Tích hợp)

```
Metadata: {stage: WHAT, gate: G0.2|G1, artefact_type, hash, owner, link, pr_id?, run_id?, timestamp}.  
Lưu: Orchdocs cho docs; Artifacts/S3 cho export (csv/md) nếu qua CI; tất cả hash+timestamp.
```

---

## C) STAGE 02 – Design & Architecture (HOW) – 4.9 uplift

### C.1 Thay thế tiến trình SDLC

**Find:** `WHY→WHAT→HOW→BUILD→TEST→OPERATE`
**Replace:** `WHY→WHAT→HOW→BUILD→TEST→DEPLOY(05)→OPERATE`

### C.2 Bổ sung “Deploy Readiness hooks” (sau mục 4. Gates & Evidence)

```
**OpenAPI‑Diff** bắt buộc trong pipeline để phát hiện breaking changes trước G4.  
Xuất **SBOM** (Syft/CycloneDX) và ký **cosign attestations** khi tag RC.
```

### C.3 Thêm mục “Policy Pack v0.9 – HOW tiering” (sau mục 11. Tích hợp & OSS Alignment)

```
- **Lite:** OWASP_BASELINE, OpenAPI lint PASS, ERD+TDD diagrams, perf budget baseline, waiver.max=2 TTL≤21d.  
- **Standard:** + Semgrep SAST PASS, operate.preview required, evidence.auto≥60%.  
- **Enterprise:** + DAST (ZAP/Burp), threat model lite, SRE approval bắt buộc; evidence.auto≥70%.
```

### C.4 Thêm mục “Evidence Schema v0.9 (HOW)” (trước mục 14. Links tham chiếu)

```
Metadata: {stage: HOW, gate: G2, type, hash, owner, link, pr_id, run_id, timestamp}.  
Lưu: Orchdocs (ADR/baseline/diagrams) & Artifacts/S3 (lint reports, SBOM, attestations).  
PR Checks: `gate/G2` PASS/FAIL + deep‑link Evidence.
```

---

## D) PR Checks – Contract chung (đính kèm vào 3 canvas)

```
Github PR Checks:
- gate/G0.1, gate/G0.2, gate/G1 (optional), gate/G2, gate/G3, gate/G4, gate/G5  
- Nội dung: status PASS/FAIL, message ngắn, link tới Evidence Vault item(s)
- Tiêu chí pass/fail do Policy Pack v0.9 xác định theo tier
```

---

## E) Gợi ý tiếp theo

* Phát hành **Policy Pack YAML v0.9** & **Evidence Schema (JSON/MD)** theo đúng các mục trên.
* Cập nhật **VS Code Ext**: hiển thị **Gate timeline 00→06** + nút `Attach Evidence` + cảnh báo policy.
