# SDLC ORCHESTRATOR – STAGE 02: DESIGN & ARCHITECTURE (SDLC 4.8)

**Version:** v1.2 (Bridge‑First, aligned BRD & Market/OSS)
**Ngày:** 13/11/2025
**Owner:** Tech Lead / Architect
**Stakeholders:** PM/PO, Security Lead, QA Lead, SRE Lead, Data/ML, Infra/DevOps

> **HOW‑stage mục tiêu:** Chuyển **concept** (WHAT) thành **thiết kế khả thi, bảo mật, có thể vận hành**, đủ **bằng chứng** để pass **G2 – Design Ready**, sẵn sàng sang **BUILD**.

---

## 1. Bối cảnh HOW & Kết quả mong đợi

* **Chống “solution‑first/stack‑first”**: mọi quyết định kiến trúc phải bám **NFRs** & use case, có **ADR** kèm lý do chọn/bỏ.
* **Output bắt buộc:** 1) **ADR‑0x** cho quyết định then chốt, 2) **OpenAPI spec** (hoặc gRPC/GraphQL schema) đã **lint PASS**, 3) **DB ERD** & **schema migration strategy**, 4) **System TDD diagram(s)** (flow/sequence/state), 5) **Security baseline** theo **OWASP_BASELINE**, 6) **Operate preview** (runbook/metrics/alerts thô), 7) **Perf budget** ban đầu.

---

## 2. Scope (HOW) & Non‑Scope (MVP Bridge‑First)

**In‑scope:**

* Thiết kế logic & boundary (context map, module decomposition, integration contracts).
* API spec & hợp đồng: **OpenAPI** + rules (Spectral) / JSON Schema / AsyncAPI (nếu cần).
* Data design: **ERD**, migration policy (idempotent, backward‑compatible).
* Non‑functional: bảo mật, hiệu năng, khả dụng, mở rộng, quan sát (observability).
* **Evidence mapping** vào **Evidence Vault**.
* **Design Review** ritual + sign‑off: Tech Lead, Security Lead, SRE Lead.

**Non‑scope (MVP):**

* Xây full **Native Board**; CI/CD chuyên sâu ngoài phạm vi thiết kế (triển khai ở BUILD/TEST/DEPLOY).
* Tuning hiệu năng mức micro‑optim (thực hiện sau khi có benchmark ở BUILD/TEST).

---

## 3. Artefacts & Chuẩn hoá (WHAT → HOW)

* **ADR‑0x/**: mỗi quyết định 1 file (`ADR-01-database-choice.md`, `ADR-02-authn-model.md`…), cấu trúc: *Context → Decision → Status → Consequences → Alternatives*.
* **/api/openapi.yml**: contract chuẩn; bắt buộc **lint PASS (Spectral)**.
* **/design/db_erd.puml**: ERD & data dictionary; policy **migration idempotent, backward‑compatible**.
* **/design/system_tdd.puml**: diagram (sequence/activity/state) cho core flows; *test‑driven design*.
* **/security/baseline.md**: OWASP ASVS baseline + secrets policy + dependency policy (SBOM).
* **/operate/preview.md**: metrics/events/logs cần thu; **runbook sketch**, **alert hypothesis**; mapping tới **G5 Operate Ready**.
* **/perf/budget.md**: SLO/latency p95, throughput, cap CPU/RAM/IO, data volume.

> **Metadata Evidence Vault:** `{stage: HOW, gate: G2, type, hash, owner, link}`.

---

## 4. Gates & Evidence (G2 – Design Ready)

**G2 – Design Ready (HOW) – yêu cầu tối thiểu:**

* `adr_links: present`, `openapi_lint: PASS`, `db_erd_link: present`, `security_review: OWASP_BASELINE`, `tdd_diagram: present`, `perf_budget: present`, `operate_preview: present`.
* **Approvals:** `TechLead`, `SecurityLead` (bắt buộc); `SRE_Lead` (advisory hoặc bắt buộc với tier Enterprise).
* **Waiver:** cho phép tạm miễn 1–2 tiêu chí trong **Lite**, có thời hạn và lý do; tự động nhắc **expire**.

**YAML ví dụ (Policy Pack):**

```yaml
id: G2_DESIGN_READY
stage: HOW
requires:
  adr_links: present
  openapi_lint: PASS
  db_erd_link: present
  security_review: OWASP_BASELINE
  tdd_diagram: present
  perf_budget: present
  operate_preview: present
approvals: ["TechLead","SecurityLead"]
waiver:
  allowed: true
  max_items: 2
  expires_in_days: 21
```

---

## 5. Stage‑aware Prompts (HOW) & IDE/CLI Hooks

**Mục tiêu:** sinh **artefact HOW** nhất quán, đo lường được, gắn evidence.

**Prompt 1 – ADR Generator**

```
Role: Software Architect
Task: Viết ADR cho quyết định <topic> với Context/Decision/Consequences/Alternatives; nêu rõ trade‑offs và rủi ro.
Inputs: BRD.md, shortlist.md, NFRs, risk list
Output: ADR-0x-<topic>.md
Guardrails: Không pick vendor lock‑in khi chưa có lí do đo lường được.
```

**Prompt 2 – API Contract (OpenAPI) + Lint**

```
Role: API Designer
Task: Sinh draft OpenAPI cho <resource>; áp rule Spectral; thêm examples, error model; versioning.
Output: /api/openapi.yml (lint PASS)
```

**Prompt 3 – ERD & Migration Policy**

```
Role: Data Architect
Task: Thiết kế ERD & mapping sang migration (idempotent, backward‑compatible); note index/partitioning.
Output: /design/db_erd.puml, /migrations/plan.md
```

**Prompt 4 – System TDD Diagrams**

```
Role: System Designer
Task: Sequence/state/activity cho flows chính; xác định test points & contract tests.
Output: /design/system_tdd.puml
```

**VS Code / CLI:**

* Palette: `SDLC: Generate ADR / OpenAPI / ERD / TDD Diagram / Security Baseline`.
* `sdlcctl validate-gate --stage HOW` → trả **Gate Status**;
* `sdlcctl attach-evidence --doc design/*`.

---

## 6. Security & Compliance (HOW)

* **OWASP_BASELINE** checklist; *threat modeling lite* (STRIDE / attack trees) cho luồng nhạy cảm.
* **Dependency policy**: SBOM (Syft/CycloneDX), **Semgrep** rules; secrets policy; **egress control**.
* **PII/Compliance**: phân loại dữ liệu (PII/PHI/PCI), **masking/anonymization**, log retention; **audit log bất biến**.

---

## 7. Operability Preview (Design for Operate)

* **SLI/SLO sơ bộ** (latency, error rate, saturation).
* **Metrics/events/logs** cần thu, *correlation ids*.
* **Runbook skeleton** & **alert hypothesis** (critical vs warning).
* **Capacity plan** thô (traffic, size growth, backups, DR pattern).
* Mapping sang **G5 – Operate Ready** để không bị “thiết kế mù vận hành”.

---

## 8. Performance & Scalability

* **Budget**: latency p95/99, throughput, resource caps.
* **Testability**: chuẩn bị kịch bản **baseline & stress** (dùng ở TEST stage).
* **Scale patterns**: cache, async queue, sharding, read replicas; **backpressure** & **timeout/circuit breaker**.

---

## 9. Review Workflow (Design Review)

1. **Self‑review** của Architect/Tech Lead (checklist chuẩn).
2. **Peer review** (cross‑team khi cần).
3. **Security review** (OWASP_BASELINE).
4. **SRE review** (operability & SLI/SLO).
5. **Gate vote** (approvals) → **pass/fail** + notes/waiver.

**Checklist rút gọn:** NFRs→ADR→API→ERD→TDD→Security→Operate→Perf Budget→Risk.

---

## 10. RACI (HOW)

| Vai trò             | Nhiệm vụ                     | Gate                           |
| ------------------- | ---------------------------- | ------------------------------ |
| Tech Lead/Architect | Chủ trì thiết kế, viết ADR   | G2                             |
| Security Lead       | Review bảo mật, policy       | G2                             |
| SRE Lead            | Review vận hành              | advisory/required (Enterprise) |
| PM/PO               | Bảo đảm scope & KPI          | advisory                       |
| QA Lead             | Tư vấn Test Validity cho TDD | advisory                       |

---

## 11. Tích hợp & OSS Alignment (HOW)

* **API lint:** **Spectral** (OpenAPI rules), **OpenAPI‑Diff** cho breaking changes.
* **Policy‑as‑Code:** **OPA + Conftest** để enforce rule design (vd: không public PII fields).
* **Evidence Vault:** Allure/S3 + Postgres metadata (hash/timestamp/owner/link).
* **Operate preview:** Prom/Grafana/Sentry schema sớm; mapping alert names.

---

## 12. NFRs Template (khuyến nghị)

* **Security:** authn/authz, data‑at‑rest/‑in‑transit, secret mgmt, exposure, threat model.
* **Reliability:** SLO, HA, DR, backup/restore, graceful degradation.
* **Performance:** latency/throughput budgets, resource caps.
* **Scalability:** scale‑up/out patterns; partition strategy.
* **Observability:** logs/metrics/traces; id chuẩn hoá.
* **Maintainability:** modularity, conventions, code ownership.
* **Portability:** lock‑in risk, abstraction.

---

## 13. Câu hỏi mở (HOW)

1. Chuẩn hoá **naming & versioning** API (semver, header vs path)?
2. Mức **threat modeling** bắt buộc cho mỗi tier?
3. Ngưỡng **perf budget** mặc định theo domain (F&B, ERP, chatbot)?
4. Chuẩn **runbook & alert** tối thiểu để pass G2 (Lite vs Standard vs Enterprise)?

---

## 14. Links tham chiếu

* **BRD v1.2** (Bridge‑First, Market/OSS).
* **Stage 00 v1.2** (Prompt Library, Gate set).
* **Stage 01 v1.2** (Deliverables & Gate G0.2/G1).
* **Policy Pack YAML** (G2).
* **Evidence Schema** (Vault metadata).
