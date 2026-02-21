# GitHub Community Announcement — TinySDLC & MTS-SDLC-Lite

**Platform**: GitHub Discussions / README
**Language**: English + Vietnamese
**Timing**: Week 1 Friday (Feb 20)
**Target**: Core developers, AI agent users, OSS community

---

> **[English Version](#english) | [Phiên bản Tiếng Việt](#vietnamese)**

---

<a name="english"></a>

## English Version

Hello community,

Today I'm officially sharing two open-source projects:

* **[TinySDLC](https://github.com/Minh-Tam-Solution/tinysdlc)** (MIT License) — A minimal agent orchestrator for AI coding with SDLC role discipline. 8 roles, separation of duties, security hardening, multi-channel (Discord/Telegram/WhatsApp/Zalo), local-first.

* **[MTS-SDLC-Lite](https://github.com/Minh-Tam-Solution/MTS-SDLC-Lite)** (MIT License) — The methodology and playbook behind TinySDLC. Pure documentation — templates, processes, and case studies distilled from SDLC 6.1.0. Works with any AI tool (Claude, GPT, Copilot, Cursor).

**TinySDLC is the tool. MTS-SDLC-Lite is the playbook. Together they give any team a governance foundation for AI-assisted development.**

To understand why these exist, let me take you back to where it started.

---

### The Problem: May 2025

My development team at MTS was slow to adopt AI. They feared AI-generated code was full of bugs — "more time fixing than coding." They used ChatGPT and Gemini individually for quick prompts, but had no team-wide process.

I brought in experts. Ran a Claude Code workshop. But the team was still resistant.

And honestly? I didn't fully understand what they were doing either. My team was polite but unconvinced — the boss isn't a real software engineer. But maybe that was my advantage: no legacy habits, no "this is how we've always done it." I saw other teams succeeding. So I made a decision: I would learn it myself.

I started with Python. Then free tools — LM Studio, Ollama with Continue.dev. Then paid tools — GitHub Copilot, Cursor, Claude Code. Small apps first. Then real enterprise platforms: Bflow ([bflow.vn](https://www.bflow.vn) — ERP+BPM Platform for Vietnamese SMEs, built by my MTS team, launched Oct 2024), then evolving it into Bflow 2.0 (ERP+BPM+AI — Conversation-First with AI as a core pillar), and NQH-Bot (AI-Powered Workforce Management for Vietnamese F&B market, at Nhat Quang Holding — my second startup).

That's when things got real. NQH-Bot — an AI-Powered WFM platform serving Vietnamese F&B chains with auto-scheduling and compliance — ended up with 679 mock implementations and 78% production failure. The AI was fast, but without any governance process. The need for structured AI governance was born from this pain.

---

### From Framework → Orchestrator → TinySDLC

I didn't blame the tools. I built a framework.

Over 8 months, that framework went through 12 major versions — battle-tested across 5 real projects (Bflow, NQH-Bot, MTEP, SOP Generator, SDLC Orchestrator). Every crisis became a pattern. Every pattern became a rule.

On **November 13, 2025**, I started building SDLC Orchestrator — a control plane to turn the framework into an execution system. But I realized:

> A framework is just thinking. If you want AI to work with discipline, you need tools that materialize and automate that framework.

TinySDLC is **the minimal core extracted from SDLC Orchestrator** — local-first, enough to:

* Orchestrate 8 agent roles (researcher, pm, architect, coder, reviewer, tester, devops, pjm) with isolated workspaces
* Enforce separation of duties (coder can't self-approve, reviewer can't be bypassed)
* Route conversations via `@agent: message` across Discord, Telegram, WhatsApp, Zalo
* Harden security (credential scrubbing, env scrubbing, input sanitization, shell guards)
* Run on a file-based queue — zero external dependencies, no Redis, no Postgres

The governance methodology (Spec → Gate → Evidence → Approval) lives in MTS-SDLC-Lite. TinySDLC provides the structure and role discipline to follow it.

---

### Born from the multi-agent ecosystem

Along the way, my team experimented with TinyClaw, OpenClaw, NanoBot, PicoClaw, and ZeroClaw. These tools accelerated development enormously. But I saw the risk:

> Multi-agents work incredibly fast. But without governance, speed only amplifies mistakes.

TinySDLC sits **above** AI agents — not replacing them, but orchestrating them with discipline.

---

### Written during Lunar New Year

This wasn't built in an official sprint. It was built during Tet:

* Mornings: cleaning the house with my wife
* Noon: ancestral ceremonies
* Afternoons: welcoming guests
* Evenings: coding sessions

I'm a 55-year-old CEO (Founder of MTS, CEO of Nhat Quang Holding) who hadn't touched code in 30 years. The last time was 1994 — Assembler and Borland C++ for my graduation thesis: a graphics application for designing electronic circuit boards. Object-oriented programming deeply shaped how I think. Then I moved into tech management — CMCSISG, VNG Cloud, Galaxy Holdings — and never looked back. But AI changed the game. And the only way to govern AI coding was to understand it from the inside.

Here's what I've realized: we are always programming in our lives. With AI today, anyone with design thinking, systems thinking, and domain knowledge can quickly experiment and turn ideas into products. That's exactly what happened here.

---

### Two products, one ecosystem

```
TinySDLC (MIT)                    SDLC Orchestrator (Commercial)
→ Agent orchestrator + roles      → Full governance platform
→ File-based queue, local-first   → Cloud, enterprise-first
→ Individuals / small teams       → 15-50+ engineer orgs
→ Role discipline + security      → Automated gates, OPA policies,
                                    SHA256 evidence vault, SSO, audit

Both built on SDLC 6.1.0 Framework
MTS-SDLC-Lite = the community methodology docs
```

TinySDLC is the community gateway — role discipline with zero infrastructure. Orchestrator is the enterprise platform — automated governance at scale. When you outgrow TinySDLC, there's a clear upgrade path.

---

### Quick Start

```bash
# Clone TinySDLC
git clone https://github.com/Minh-Tam-Solution/tinysdlc.git
cd tinysdlc
npm install && npm run build
./tinysdlc.sh start    # Interactive setup wizard

# Read the methodology
git clone https://github.com/Minh-Tam-Solution/MTS-SDLC-Lite.git
```

---

### Why open-source?

AI is building software faster than ever. But without governance, we're just creating technical debt faster.

**AI is not the competitive advantage. Governance is.**

If you're:

* experimenting with multi-agent AI coding
* wanting to control AI-generated code quality
* or just curious about a 55-year-old CEO relearning to build software

Visit the repos. Star them. Open issues. Challenge our approach. Contribute.

TinySDLC is not perfect. It's part of a transformation journey — and we're sharing it because governance should not be a luxury only enterprises can afford.

— **Tai Dang**
CEO/Founder MTS & CEO Nhat Quang Holding
[LinkedIn](https://www.linkedin.com/in/the-tai-dang-a81bb710/)
MIT Licensed • Built during Tet • Governance First

---

<a name="vietnamese"></a>

## Phiên bản Tiếng Việt

Chào cộng đồng,

Hôm nay tôi chia sẻ chính thức hai dự án mã nguồn mở:

* **[TinySDLC](https://github.com/Minh-Tam-Solution/tinysdlc)** (MIT License) — Bộ điều phối agent tối giản cho AI coding với kỷ luật SDLC. 8 vai trò, phân quyền rõ ràng, bảo mật tích hợp, đa kênh (Discord/Telegram/WhatsApp/Zalo), local-first.

* **[MTS-SDLC-Lite](https://github.com/Minh-Tam-Solution/MTS-SDLC-Lite)** (MIT License) — Phương pháp luận và playbook đằng sau TinySDLC. Tài liệu thuần túy — templates, quy trình, và case studies được tinh lọc từ SDLC 6.1.0. Hoạt động với bất kỳ công cụ AI nào (Claude, GPT, Copilot, Cursor).

**TinySDLC là công cụ. MTS-SDLC-Lite là cẩm nang. Cùng nhau, chúng tạo nền tảng governance cho bất kỳ team nào phát triển phần mềm với AI.**

Nhưng để hiểu TinySDLC, cần quay lại nơi bắt đầu.

---

### Vấn đề: Tháng 5/2025

Team phát triển MTS chậm ứng dụng AI. Họ ngại thay đổi. Cho rằng AI tạo code nhiều lỗi — "mất thời gian sửa còn hơn tự viết." Họ chỉ dùng ChatGPT hay Gemini cá nhân qua vài prompt, không có quy trình chung cho cả team.

Tôi mời chuyên gia về. Tổ chức workshop Claude Code. Nhưng team vẫn chậm thay đổi.

Và thành thật? Tôi cũng không hiểu rõ họ đang làm gì. Team lịch sự nhưng không tin — sếp đâu phải dân làm phần mềm chuyên nghiệp. Nhưng có lẽ đó lại là lợi thế — không có lối mòn, sẵn sàng học hỏi tất cả. Xung quanh đã có nhiều team thành công. Nên tôi quyết định: tự mình học.

Bắt đầu từ Python. Rồi các công cụ miễn phí — LM Studio, Ollama với Continue.dev. Sau đó trả tiền — GitHub Copilot, Cursor, Claude Code. Viết vài ứng dụng nhỏ trước. Rồi chuyển sang nền tảng enterprise thật: Bflow ([bflow.vn](https://www.bflow.vn) — nền tảng ERP+BPM cho SME Việt Nam, team MTS xây dựng, ra mắt 10/2024), rồi phát triển lên Bflow 2.0 (ERP+BPM+AI — Conversation-First với AI là pillar cốt lõi), và NQH-Bot (nền tảng Quản lý Nhân sự AI cho ngành F&B Việt Nam, tại Nhat Quang Holding — startup thứ 2 của tôi).

Đó là lúc mọi thứ trở nên thật. NQH-Bot — nền tảng WFM với AI auto-scheduling, multi-tenant SaaS và compliance theo vùng — có 679 mock implementations và 78% lỗi production. AI rất nhanh, nhưng không có quy trình governance nào. Nhu cầu về governance cho AI hình thành từ nỗi đau này.

---

### Từ Framework → Orchestrator → TinySDLC

Tôi không đổ lỗi cho công cụ. Tôi xây framework.

Trong 8 tháng, framework đi qua 12 phiên bản lớn — thử lửa qua 5 dự án thực (Bflow, NQH-Bot, MTEP, SOP Generator, SDLC Orchestrator). Mỗi khủng hoảng thành pattern. Mỗi pattern thành quy tắc.

Ngày **13/11/2025**, tôi bắt đầu xây SDLC Orchestrator — control plane để biến framework thành hệ thống thực thi. Nhưng tôi nhận ra:

> Framework chỉ là tư duy. Muốn AI làm việc có kỷ luật, phải có công cụ hiện thực hoá và tự động hoá framework đó.

TinySDLC là **lõi tối giản tách ra từ SDLC Orchestrator** — local-first, đủ để:

* Điều phối 8 vai trò agent (researcher, pm, architect, coder, reviewer, tester, devops, pjm) với workspace riêng biệt
* Phân quyền bắt buộc (coder không tự duyệt, reviewer không bị bỏ qua)
* Routing qua `@agent: message` trên Discord, Telegram, WhatsApp, Zalo
* Bảo mật tích hợp (lọc credential, lọc env, sanitize input, shell guard)
* File-based queue — không phụ thuộc bên ngoài, không Redis, không Postgres

Phương pháp luận governance (Spec → Gate → Evidence → Approval) nằm trong MTS-SDLC-Lite. TinySDLC cung cấp cấu trúc và kỷ luật vai trò để thực thi.

---

### Đến từ hệ sinh thái multi-agents

Trên hành trình đó, team đã thử nghiệm TinyClaw, OpenClaw, NanoBot, PicoClaw, và ZeroClaw. Các công cụ này tăng tốc rất mạnh. Nhưng tôi nhìn thấy rủi ro:

> Multi-agents làm việc rất nhanh. Nhưng nếu không có governance, tốc độ chỉ khuếch đại lỗi.

TinySDLC nằm **phía trên** AI agents — không thay thế chúng, mà điều phối chúng có kỷ luật.

---

### Viết trong mấy ngày Tết

Không phải trong một sprint chính thức. Mà trong mấy ngày Tết:

* Sáng dọn dẹp cùng bà xã
* Trưa cúng bái
* Chiều tiếp khách
* Tối tranh thủ coding

Tôi là CEO 55 tuổi (Founder MTS, CEO Nhat Quang Holding), 30 năm không đụng coding. Lần cuối là năm 1994 — Assembler và Borland C++ cho đề án tốt nghiệp: phần mềm đồ hoạ để vẽ bản mạch điện tử và mô hình hoá. Lập trình hướng đối tượng ảnh hưởng sâu sắc đến tư duy của tôi. Rồi chuyển sang quản trị công nghệ — CMCSISG, VNG Cloud, Galaxy Holdings — và không quay lại. Nhưng AI đã thay đổi cuộc chơi. Và cách duy nhất để governance AI coding là phải hiểu nó từ bên trong.

Tôi nhận ra: chúng ta luôn lập trình trong cuộc đời. Với AI hiện nay, ai có tư duy thiết kế, tư duy hệ thống tốt và có domain knowledge thì đều có thể nhanh chóng thử nghiệm biến ý tưởng thành sản phẩm. Đó chính xác là điều đã xảy ra ở đây.

---

### Hai sản phẩm, một hệ sinh thái

```
TinySDLC (MIT)                       SDLC Orchestrator (Commercial)
→ Bộ điều phối agent + vai trò       → Nền tảng governance đầy đủ
→ File-based queue, local-first      → Cloud, enterprise-first
→ Cá nhân / team nhỏ                 → Tổ chức 15-50+ engineer
→ Kỷ luật vai trò + bảo mật         → Gate tự động, OPA policies,
                                       SHA256 evidence vault, SSO, audit

Cả hai xây trên SDLC 6.1.0 Framework
MTS-SDLC-Lite = tài liệu phương pháp cho cộng đồng
```

TinySDLC là cánh cửa cộng đồng — kỷ luật vai trò, không cần hạ tầng. Orchestrator là nền tảng doanh nghiệp — governance tự động ở quy mô lớn. Khi bạn cần nhiều hơn TinySDLC, có sẵn lộ trình nâng cấp.

---

### Bắt đầu nhanh

```bash
# Clone TinySDLC
git clone https://github.com/Minh-Tam-Solution/tinysdlc.git
cd tinysdlc
npm install && npm run build
./tinysdlc.sh start    # Wizard cài đặt tương tác

# Đọc phương pháp luận
git clone https://github.com/Minh-Tam-Solution/MTS-SDLC-Lite.git
```

---

### Vì sao tôi open-source?

Vì AI đang làm phần mềm nhanh hơn bao giờ hết. Nhưng nếu không có governance, chúng ta chỉ tạo ra technical debt nhanh hơn.

**AI không phải lợi thế cạnh tranh. Governance mới là lợi thế cạnh tranh.**

Nếu bạn đang:

* thử nghiệm multi-agent AI coding
* muốn kiểm soát chất lượng code do AI tạo ra
* hoặc chỉ muốn xem một CEO 55 tuổi học lại cách xây dựng phần mềm

Mời vào repo. Star. Mở issue. Phản biện. Đóng góp.

TinySDLC không hoàn hảo. Nó là một phần của hành trình chuyển hoá — và chúng tôi chia sẻ vì governance không nên là đặc quyền chỉ doanh nghiệp lớn mới có.

— **Tai Dang**
CEO/Founder MTS & CEO Nhat Quang Holding
[LinkedIn](https://www.linkedin.com/in/the-tai-dang-a81bb710/)
MIT Licensed • Built during Tết • Governance First
