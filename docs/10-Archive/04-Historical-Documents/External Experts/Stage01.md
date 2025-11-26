# SDLC ORCHESTRATOR – STAGE 01: PLANNING & ANALYSIS (SDLC 4.8)

**Version:** v1.2 (Bridge‑First, aligned BRD & Market/OSS)
**Ngày:** 13/11/2025
**Owner:** Product Lead / CTO
**Stakeholders:** PM/PO, Tech Lead/Architect, EM, QA Lead, SRE Lead, Customer Success

> **WHAT‑stage mục tiêu:** mở rộng không gian giải pháp → chọn **concept khả thi, đo lường được**, sẵn sàng chuyển **Stage 02 (HOW)**. Tuân thủ **Pillar 0–5** và tiến trình **WHY→WHAT→HOW→BUILD→TEST→DEPLOY(05)→OPERATE**.

---

## 1. Bối cảnh WHAT & Kết quả mong đợi

* **Vấn đề:** team thường “nhảy vào giải pháp/stack” quá sớm → rủi ro build sai.
* **Kết quả cần có:** 1) **Problem/Outcome rõ** (kế thừa Stage 00), 2) **Solution Gallery đa dạng** → **shortlist ≥3 concept** có **scorecards**, 3) **Phase plan (4–12w)**, **Sprint plan (2 sprint đầu)**, 4) **KPI mục tiêu** (Tri‑layer + DORA) & **risk register**.

---

## 2. Scope (WHAT) & Non‑Scope (MVP Bridge‑First)

**In‑scope (MVP):**

* **Decision Framework Bridge vs Native** (per‑product).
* **Solution Gallery & Concept Shortlist** với **scorecards** (feasibility/impact/risk/cost).
* **Phase/Sprint skeleton** + **KPI tiêu chuẩn**.
* **Stage‑aware AI (WHAT)** trong **VS Code Ext v0** + **CLI `sdlcctl`**.
* **Evidence mapping** vào **Evidence Vault** (hash/timestamp/owner/link).
* **Reporting WHAT**: tiến độ G0.2/G1, readiness chuyển HOW.

**Non‑scope (MVP):**

* Native Board thay Jira/Projects (đưa sang v2).
* Tự động hoá full **Test Validity** (để giai đoạn BUILD/TEST).

---

## 3. Decision Framework: Bridge vs Native (WHAT)

* **Bridge (khuyến nghị MVP):** dùng GitHub Issues/Projects; Orchestrator là **lớp enforcer** (Gate/Evidence/AI/Reporting).
* **Native (v2):** Issue/Epic/Sprint/Board nội bộ khi cần **enforcement/compliance sâu**.
* **Tiêu chí:** (1) velocity & đổi công cụ tối thiểu, (2) traceability depth & audit, (3) giới hạn API nền tảng ngoài, (4) chi phí vận hành, (5) bảo mật & data residency.

---

## 4. Tiered Compliance Mapping (WHAT)

* **Lite (≤5):** Gates: **G0.2 Solution Diversity**, **G1 Requirements Ready** (rút gọn).
  Evidence tối thiểu: **BRD 1 trang**, **Solution Gallery ≥30 ý tưởng / ≥5 theme / ≥2 concept**, Phase/Sprint skeleton.
* **Standard (6–20):** **Solution Gallery ≥100/≥10/≥3**, **Scorecards**, **ADR‑0x seed**, Phase plan 4–12w, Sprint plan 2 sprint; **KPI (Tri‑layer + DORA)**; **Auto‑evidence 60–70%**.
* **Enterprise:** thêm **risk register**, **compliance checklist**, **stakeholder sign‑off**; evidence auto vào **Vault ≥70%**.

---

## 5. WHAT Deliverables (artefacts & chuẩn hoá)

* **solution_gallery.csv** (ý tưởng & themes).
* **concept_scorecards.md** (chấm điểm & lý do chọn/bỏ).
* **shortlist.md** (≥3 concept).
* **phase_plan.md** (4–12 tuần, goals/gates/KPI).
* **sprint_plan.md** (2 sprint đầu: stories/outcomes/KPI).
* **risks_assumptions.md** & **validation_experiments.md** (cheap tests).
* (Optional) **requirements.md** (MoSCoW/Job stories/AC).
* Tất cả **được attach vào Evidence Vault** với metadata `{stage: WHAT, gate: G0.2|G1, artefact_type, hash, owner, link}`.

---

## 6. Gates & Evidence (WHAT → HOW)

**G0.2 – Solution Diversity**

* **Requires:** Solution Gallery, Themes, **Shortlist ≥3 concept**, **Scorecards**.
* **Approvals:** Product Lead, CTO.

**G1 – Requirements Ready** *(nếu áp dụng)*

* **Requires:** Requirements tổng hợp (MoSCoW/Job stories/AC), success metrics, **Phase/Sprint skeleton**.
* **Approvals:** PM/PO, Tech Lead.

> **Rule:** Không được “Open Stage 02 (HOW)” nếu thiếu **G0.2**; **G1** có thể rút gọn tuỳ tier.

---

## 7. Stage‑aware Prompts (WHAT) & Evidence Hooks

**Mục tiêu:** Chuẩn hoá **prompt** để AI tạo **đúng artefact WHAT** + gắn **evidence**.

1. **Solution Gallery Builder**

```
Role: Product Analyst
Task: Tạo >=100 ý tưởng, nhóm >=10 themes; mỗi theme >=2 concept candidates.
Deliverables: solution_gallery.csv
Guardrails: Không chọn stack; nêu tiêu chí loại trừ.
```

2. **Concept Scoring & Shortlist**

```
Role: Strategy Analyst
Task: Chấm feasibility/impact/risk/cost; chọn >=3 concept; lý do chọn/bỏ.
Deliverables: concept_scorecards.md, shortlist.md
```

3. **Phase & Sprint Skeleton**

```
Role: Delivery Planner
Task: Phác phase 4–12w (goals/gates/KPI); 2 sprint đầu (stories/outcomes/KPI).
Deliverables: phase_plan.md, sprint_plan.md
```

4. **Risks & Assumptions**

```
Role: Risk Analyst
Task: Xác định rủi ro & giả định; đề xuất thí nghiệm kiểm chứng (cheap tests).
Deliverables: risks_assumptions.md, validation_experiments.md
```

**VS Code Ext / CLI:**

* Palette: `SDLC: Generate Solution Gallery / Scorecards / Phase Plan / Sprint Plan`.
* `sdlcctl validate-gate --stage WHAT`; `sdlcctl attach-evidence --doc <file>`.

**CI Hooks:**

* Kích hoạt **Gate check G0.2/G1** trong PR Checks (dựa trên file/evidence có mặt + chữ ký).

---

## 8. Reporting & KPI (WHAT)

* **Gate Progress:** % hoàn thành G0.2/G1, **first‑pass rate**.
* **Concept Readiness:** số concept vượt **threshold**.
* **Risk Heatmap:** theo concept (feasibility/cost/risk).
* **Traceability View:** Roadmap → Phase → Sprint (liên kết backlog GitHub Issues/Projects – Bridge Mode).

---

## 9. Quy trình WHAT (Swimlane)

1. **Kế thừa Stage 00**: BRD.md, success_metrics.md, risks.md.
2. **Ideation** → **Solution Gallery** (themes/concepts).
3. **Scoring** → **Shortlist ≥3**.
4. **Phase/Sprint skeleton** + **KPI**.
5. **(Optional) Requirements** rút gọn (MoSCoW/Job stories/AC).
6. **Gate Review**: G0.2 (bắt buộc), G1 (tuỳ tier).
7. **Open Stage 02** khi pass.

---

## 10. RACI (WHAT)

| Vai trò             | Nhiệm vụ                                     | Gate     |
| ------------------- | -------------------------------------------- | -------- |
| Product Lead        | Đảm bảo outcome & ưu tiên                    | G0.2, G1 |
| PM/PO               | Điều phối artefact WHAT, phase/sprint        | G1       |
| Tech Lead/Architect | Review khả thi & ràng buộc kỹ thuật          | G0.2, G1 |
| QA Lead             | Tham vấn Test Validity thô (không deep)      | G1       |
| SRE Lead            | Xem trước ràng buộc Operate (runbook/alerts) | advisory |

---

## 11. Ràng buộc & Tích hợp (WHAT)

* **Bridge‑First (MVP):** chỉ “đọc” GitHub Issues/Projects; Gate/Evidence/Reporting nằm ở Orchestrator.
* **Evidence Vault:** Allure/S3 + Postgres metadata; hash/timestamp/owner/link.
* **Policy‑as‑Code:** OPA/Conftest (YAML abstraction).
* **Operate preview:** mapping yêu cầu runbook/alerts/SLA ở mức high‑level cho Stage 02.

---

## 12. Câu hỏi mở (WHAT)

1. Ngưỡng **diversity** tối thiểu theo domain (Fintech/Edtech/F&B)?
2. Tỷ lệ tự động hoá evidence ở WHAT (target 60–70%)?
3. Chuẩn hoá format **scorecards** và **risk heatmap** (CSV/MD/YAML)?

---

## 13. Link tham chiếu

* **BRD v1.2** (Bridge‑First, Market/OSS alignment).
* **Stage 00 v1.2** (Prompt Library, Gate set).
* **Policy Pack** (YAML Gates – G0.2/G1).
* **Evidence Schema** (Vault metadata).
