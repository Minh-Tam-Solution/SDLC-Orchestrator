# SDLC ORCHESTRATOR – MARKET & OSS LANDSCAPE (v1.0)

**Date:** 13/11/2025
**Owner:** Product/Architecture
**Purpose:** Khảo sát thị trường & open‑source để **tăng tốc** phát triển **SDLC Orchestrator (Bridge‑First, SDLC 4.8)** – chọn các khối “plug‑in” cho **Gate Engine, Evidence Vault, Reporting, Operate** và **VS Code**.

---

## 1) Executive Summary

* **Khoảng trống thị trường**: Nhiều nền tảng ALM/DevOps (Jira/Azure DevOps/GitLab) mạnh ở **tracking**, nhưng **thiếu “Gate Engine” policy‑as‑code** + **Evidence Vault** chuẩn hoá theo SDLC 4.8; phần **Operate/RCA** thường rời rạc.
* **Chiến lược tăng tốc**:

  * **Bridge‑First** vào GitHub (Issues/PR/Actions).
  * Dùng **OPA/Rego + Conftest** làm nhân **policy‑as‑code** cho Gate Engine (mở rộng rule bằng YAML),
  * **Argo/Tekton/GitHub Actions** làm “collectors” đẩy evidence,
  * **Allure/ReportPortal + MinIO/S3** làm Evidence Vault (metadata + hash + links),
  * **Grafana/Prom/OpenTelemetry + Grafana OnCall + Alertmanager** cho Operate + RCA,
  * **VS Code Extension** (scaffolding + gate status + attach evidence).
* **Khuyến nghị**: Không “xây lại toàn bộ ALM”, mà **bao trùm (governance layer)** + **cắm mở (adapters)**. Giữ **Native Board** sang v2; MVP tập trung Gate Engine/Evidence/AI/Operate lite.

---

## 2) Category Map (so sánh theo nhu cầu SDLC 4.8)

* **ALM / Work Management:** OpenProject, Taiga, Redmine, Tuleap, GitLab, GitHub Projects (SaaS), Jira (ref).
* **CI/CD & Orchestration:** GitHub Actions, GitLab CI, Jenkins, **Argo Workflows/Events**, **Tekton**.
* **Policy‑as‑Code / Governance:** **Open Policy Agent (OPA)**, **Conftest**, Kyverno (K8s), Checkov (IaC).
* **Quality & Security:** SonarQube (CE), Semgrep, OWASP ZAP, Trivy/Grype (container), Spectral (OpenAPI linter – OSS flavor).
* **Testing & Evidence:** **Allure Report**, **ReportPortal.io**, Testkube, Pact (contract testing), OpenAPI‑Diff.
* **Observability & Operate:** Prometheus, Grafana, OpenTelemetry, **Grafana OnCall**, Alertmanager, Sentry (self‑host).
* **Status/RCA/Knowledge:** Cachet, cstate (status page), MkDocs/Docusaurus (docs‑as‑code), adr‑tools (ADR).
* **Supply Chain/SBOM/Attestations:** Syft/Grype, CycloneDX/SPDX, **Sigstore/cosign**, SLSA/in‑toto.
* **Developer Portal:** **Backstage** (plugin architecture – good for hub UI & catalogs).

---

## 3) Quick Matrix – Khả năng đáp ứng theo khối (✓ = mạnh / △ = một phần / ✗ = thiếu)

| Sản phẩm                | Board/Backlog | Gate Policy‑as‑Code |         Evidence Vault | AI/IDE hooks |     Operate/Incident | License         |
| ----------------------- | ------------: | ------------------: | ---------------------: | -----------: | -------------------: | --------------- |
| **OpenProject**         |             ✓ |                   ✗ |      △ (artifact link) |            ✗ |                    ✗ | GPLv3           |
| **Taiga**               |             ✓ |                   ✗ |                      △ |            ✗ |                    ✗ | MPL             |
| **Redmine**             |             ✓ |                   ✗ |            △ (plugins) |            ✗ |                    ✗ | GPLv2           |
| **Tuleap**              |             ✓ |                   ✗ |                      △ |            ✗ |                    ✗ | GPLv2           |
| **GitLab (CE)**         |             ✓ |     △ (rules in CI) |      △ (job artifacts) |            △ |              △ (Ops) | MIT             |
| **GitHub Projects**     |             ✓ |  △ (Actions checks) |          △ (Artifacts) |  ✓ (VS Code) |     △ (Integrations) | SaaS            |
| **Backstage**           |   △ (plugins) |                   ✗ |        △ (via plugins) | △ (scaffold) |                    ✗ | Apache‑2.0      |
| **Argo/Tekton**         |             ✗ |  △ (policy via OPA) |          △ (artifacts) |            ✗ |                    ✗ | Apache‑2.0      |
| **OPA + Conftest**      |             ✗ |               **✓** |                      ✗ |            ✗ |                    ✗ | BSD/Apache      |
| **Allure/ReportPortal** |             ✗ |                   ✗ |  **✓ (test evidence)** |            ✗ |                    ✗ | Apache‑2.0/AGPL |
| **Grafana Stack**       |             ✗ |                   ✗ |       △ (metrics/logs) |            ✗ | **✓ (OnCall/Alert)** | AGPL/Apache     |
| **Sigstore/cosign**     |             ✗ |    ✓ (attestations) | △ (evidence integrity) |            ✗ |                    ✗ | Apache‑2.0      |

**Kết luận:** Không có OSS đơn lẻ đáp ứng **Gate Engine + Evidence Vault + Operate** đầy đủ. Cần **compose**: **OPA/Conftest** (gate) + **Actions/Argo** (collect) + **Allure/ReportPortal + S3** (evidence) + **Grafana OnCall/Prom** (operate) + **Backstage plugin** (hub UI) + **VS Code ext** (dev‑first).

---

## 4) Shortlist – Thành phần đề xuất cho MVP (Bridge‑First)

**4.1 Gate Engine (policy‑as‑code)**

* **Open Policy Agent (OPA) + Conftest**: viết rule Rego, gọi bằng CLI/Action; bọc **YAML friendly** cho Product/QA dùng.
* **Spectral** (OpenAPI rules), **Semgrep** (code rules) làm “sub‑gate” chuyên biệt; unify kết quả về Gate Engine.

**4.2 Evidence Vault**

* **Allure Report** (test result) + **MinIO/S3** (artifact store) + **Postgres** (metadata index).
* **ReportPortal.io** nếu cần quản lý test campaign quy mô lớn.
* **Sigstore/cosign** để ký/attest evidence quan trọng (SBOM, test pack, release notes).
* **Syft/Grype/CycloneDX** cho SBOM + vuln scan (lưu manifest vào Vault).

**4.3 Collector & Bridge**

* **GitHub Actions** (trước mắt) + **Argo/Tekton** (sau) để thu và đẩy evidence.
* **DangerJS**/**MegaLinter**/**Super‑Linter** thêm check nhẹ.

**4.4 Operate (lite)**

* **Prometheus + Grafana + Grafana OnCall + Alertmanager**: alert → incident → on‑call rota;
* **Sentry** (self‑host) để gom exception + release correlation;
* Status page: **Cachet/cstate**; RCA & Runbook: **MkDocs/Docusaurus + adr‑tools** (docs‑as‑code, liên kết Evidence Vault).

**4.5 Developer Experience**

* **Backstage plugin** (Orchestrator hub: Stage/Gate/Evidence/Operate view).
* **VS Code Extension**: scaffold BRD/ADR/Test; `validate-gate`; `attach-evidence`; hiển thị Gate Status theo branch.

---

## 5) Reference Architectures (tích hợp các khối OSS)

1. **Gate‑First Pipeline**: PR → GH Action chạy **Conftest (Rego)** + Semgrep + Spectral + Tests → đẩy **results + artefacts** vào **Vault (S3 + Allure)** → cập nhật **Gate Status** ở PR Checks.
2. **Evidence Integrity**: khi tạo Release, sinh **SBOM (Syft/CycloneDX)** + ký **cosign attestations** + hash metadata; lưu vào Vault.
3. **Operate Lite**: App metrics/logs → **Prom/Otel → Grafana**; Alerts → **OnCall**; Incidents link về Orchestrator (RCA in docs‑as‑code); Gate **G5 Operate Ready** kiểm tra **runbook/on‑call/alerts/SLA**.

---

## 6) Gap Analysis vs BRD 1.2

* **Gate policy UI** (non‑Rego users) → cần **YAML abstraction** + UI editor.
* **Evidence Vault schema** → cần chuẩn hoá metadata (type, stage, gate, hash, owner, link).
* **Traceability graph** (Roadmap→Release→Operate) → cần service tổng hợp (Postgres + graph lib).
* **AI theo stage** → không có trong OSS; phải **tự build** VS Code ext + server API.
* **Bridge‑Only (MVP)** → không có 2‑way sync: design adapter đọc‑ghi từng phần theo roadmap v2.

---

## 7) Build‑vs‑Integrate (đề xuất)

* **Build**: Gate Engine adapter (YAML→Rego), Evidence Vault API & schema, Orchestrator UI (Next.js) + Backstage plugin, VS Code ext, Reporting (Tri‑layer/DORA), Operate glue (incidents/RCA links).
* **Integrate**: OPA/Conftest, Semgrep, Spectral, Allure/ReportPortal, MinIO/S3, Prom/Grafana/OnCall, Sentry, Sigstore/cosign, Syft/Grype.

---

## 8) Licensing & Viability Notes

* Ưu tiên **Apache‑2.0/MIT/BSD** (Backstage, Argo, Tekton, OPA, Sigstore, Syft/Grype).
* **AGPL/GPL** (Grafana CE/AGPL, ReportPortal AGPL, OpenProject GPL): cân nhắc khi đóng gói phân phối; tách **deploy profile** (self‑host nội bộ) vs **cloud multi‑tenant**.

---

## 9) 90‑Day Adoption Plan (khớp Roadmap MVP)

* **Weeks 1–2**: Gate Engine (OPA+Conftest) + Evidence Vault v1 (Allure+S3) + VS Code ext skeleton.
* **Weeks 3–4**: GitHub adapter (read Issues/PR/Actions) + PR Checks (Gate Status).
* **Weeks 5–6**: AI stage helpers (WHY/WHAT/HOW) + DORA v0.
* **Weeks 7–8**: Operate lite (Prom/Grafana/OnCall) + Tri‑layer dashboard v1.
* **Weeks 9–10**: Pilot 2 team (Lite & Standard) + hardening.

---

## 10) Next Steps

* Chuẩn hoá **Evidence schema** & **Gate YAML abstraction**.
* POC **Backstage plugin** (Gate/Evidence panel).
* Chốt **OSS stack** (license‑risk) theo môi trường deployment.
