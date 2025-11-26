# SDLC ORCHESTRATOR – STAGE 00 & 01 REFRESH DELTAS (v1.2)

**Date:** 13/11/2025
**Context:** Đồng bộ **Stage 00** & **Stage 01** theo **BRD v1.2 (Bridge‑First)** và **Market & OSS Landscape**.

---

## A) STAGE 00 – PROJECT FOUNDATION (Delta v1.2)

### A.1 Bản chất & Định vị (thêm vào 0.A / Value Proposition)

* **Tagline:** “Project governance tool that enforces the SDLC Universal Framework.”
* **Định vị:** Lớp **governance** bao trùm công cụ hiện hữu, **Bridge‑First** (GitHub) ở MVP; có thể **thay thế** bằng **Native Board** ở v2.
* **Giá trị cốt lõi:** **Policy‑as‑Code (Gate Engine)**, **Evidence‑first (Vault)**, **AI theo stage**, **Operate‑ready**, **Traceability** Roadmap → Operate.

### A.2 Scope & Non‑Scope (cập nhật 0.4)

**In‑scope (MVP – Bridge‑First):**

* **Gate Engine + Stage Console**; **Evidence Vault v1** (Auto collect PR/Actions: test/coverage/lint/SAST + link Orchdocs).
* **Work Management (Bridge):** đọc/hiển thị GitHub Issues/Projects; Orchestrator là **enforcer** bên trên.
* **AI theo ngữ cảnh v1 (WHY/WHAT/HOW)** trong VS Code Ext v0; **Reporting v1**: DORA + Gate Status.
* **Developer‑first:** VS Code Ext v0 + CLI `sdlcctl` v0.

**Out‑of‑scope (MVP):** Native Board (v2); Billing/FinOps; License/Contract mgmt; HR performance.

### A.3 Integrations & OSS Alignment (thêm Section 8.A ở Stage 00)

* **Gate policy:** **OPA + Conftest** (YAML abstraction).
* **Evidence:** **Allure + S3/MinIO + Postgres (metadata)**; cân nhắc **ReportPortal** khi cần.
* **Collectors:** **GitHub Actions** (MVP), mở rộng **Argo/Tekton** (v2).
* **Operate:** **Prom + Grafana + OnCall + Alertmanager**; **Sentry** self‑host; status page **Cachet/cstate**; **RCA/Runbook**: docs‑as‑code.
* **Developer Hub:** **Backstage plugin** + **VS Code ext**.

### A.4 Objectives & KPI (cập nhật 0.3)

* DORA: ↓ Lead Time 30–50%, ↑ Deploy 2×, ↓ CFR 25%, ↓ MTTR 30%.
* ≥90% release có đủ evidence & RN; 100% incident có **RCA ≤ 5 ngày**.

### A.5 Constraints (cập nhật 0.10)

* **SSO OIDC**, RBAC, masking/anonymization & **egress control** (AI Gateway); **audit log bất biến**, **hash+timestamp** evidence.

### A.6 Roadmap hierarchy (cập nhật 0.11)

* Roadmap → Phase → Sprint → Backlog (bắt buộc tag stage/gate; Gate Pass/Fail đẩy về PR Check khi phù hợp).

---

## B) STAGE 01 – PLANNING & ANALYSIS (Delta v1.2)

### B.1 Decision Framework (Bridge vs Native)

* **MVP:** **Bridge‑First** (đọc Issues/Projects từ GitHub).
* **v2:** **Native Board** khi cần enforcement/compliance sâu.
* **Tiêu chí:** velocity, traceability depth, API limits, vận hành/chi phí, bảo mật & audit.

### B.2 Tiered Compliance mapping

* **Lite (≤5):** Gates: **G0.2 Solution Diversity**, **G1 Requirements Ready** (rút gọn). Evidence: BRD 1 trang, **Solution Gallery ≥30 ý tưởng / ≥5 theme / ≥2 concept**, Phase/Sprint skeleton.
* **Standard (6–20):** Solution Gallery ≥100 ý tưởng / ≥10 theme / ≥3 concept; **Scorecards**, ADR‑0x; Phase plan 4–12w; KPI (DORA + Tri‑layer); **Auto evidence 60–70%**.
* **Enterprise:** thêm **risk register**, **compliance checklist**, **stakeholder sign‑off**; **Evidence Vault auto ≥70%**.

### B.3 AI Guardrails & Evidence (WHAT‑stage)

* **Guardrails:** tag `ai-generated`, **human sign‑off**, secret scan/PII masking; egress control.
* **Evidence mẫu:** BRD, Problem Statement, Persona/Stakeholder Map, Journey/VSM, Solution Gallery, Scorecards, ADR‑0x, Phase/Sprint plan → **Evidence Vault** (hash/timestamp/owner).

### B.4 VS Code & CLI (WHAT‑stage)

* **VS Code:** scaffold BRD/ADR/Test; Sidebar **Gate Status**; attach evidence trong IDE.
* **CLI:** `validate-gate --stage WHAT`, `attach-evidence --doc BRD.md`, `open-stage 02` khi G1 pass.

### B.5 Reporting & KPI (WHAT‑stage)

* Theo dõi tiến độ **G0.2/G1**, readiness cho Stage 02; Heatmap rủi ro theo **concept**; Traceability Roadmap→Phase→Sprint.

---

**Hướng dẫn hợp nhất**

* Chèn các delta này **đúng mục tương ứng** trong Stage 00/01.
* Nếu muốn **overwrite** toàn văn Stage 00/01 theo bản đã đồng bộ BRD/OSS, mình sẽ phát hành **Stage 00 v1.2** và **Stage 01 v1.2** (full content) trong lần cập nhật kế tiếp.
