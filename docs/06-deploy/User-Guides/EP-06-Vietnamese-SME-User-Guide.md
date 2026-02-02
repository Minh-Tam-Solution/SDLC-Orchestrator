# EP-06 Vietnamese SME User Guide
## Hướng dẫn sử dụng EP-06 Codegen cho Doanh nghiệp Việt Nam

---

**Document Information**

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Status** | ACTIVE |
| **Created** | December 24, 2025 |
| **Sprint** | Sprint 50 - EP-06 Productization |
| **Audience** | Vietnamese SME Founders, Non-tech users |
| **Language** | Vietnamese + English |

---

## Mục lục

1. [Giới thiệu](#1-giới-thiệu)
2. [Yêu cầu hệ thống](#2-yêu-cầu-hệ-thống)
3. [Quy trình Onboarding](#3-quy-trình-onboarding)
4. [Tạo ứng dụng đầu tiên](#4-tạo-ứng-dụng-đầu-tiên)
5. [Hiểu về TTFV](#5-hiểu-về-ttfv)
6. [Xử lý lỗi thường gặp](#6-xử-lý-lỗi-thường-gặp)
7. [FAQ](#7-faq)

---

## 1. Giới thiệu

### EP-06 là gì?

EP-06 (IR-Based Codegen Engine) là công cụ tạo code tự động dành cho doanh nghiệp vừa và nhỏ tại Việt Nam. Với EP-06, bạn có thể:

- **Tạo ứng dụng quản lý** cho F&B, Khách sạn, Bán lẻ
- **Không cần biết lập trình** - Chỉ cần mô tả yêu cầu
- **Thời gian nhanh** - Dưới 30 phút từ ý tưởng đến ứng dụng chạy được
- **Chi phí thấp** - Founder Plan $99/team/tháng (~2.5M VND)

### Các ngành được hỗ trợ

| Ngành | Domain | Ví dụ ứng dụng |
|-------|--------|----------------|
| **F&B** | fnb | Quản lý nhà hàng, quán cà phê, order online |
| **Hospitality** | hospitality | Quản lý khách sạn, homestay, booking |
| **Retail** | retail | Quản lý cửa hàng, kho, bán hàng |

---

## 2. Yêu cầu hệ thống

### Để sử dụng EP-06, bạn cần:

- **Tài khoản SDLC Orchestrator** - Đăng ký tại dashboard
- **Trình duyệt web** - Chrome, Firefox, Safari phiên bản mới nhất
- **Kết nối Internet** - Tối thiểu 5 Mbps

### Không cần cài đặt gì thêm!

Mọi thứ đều chạy trên cloud. Bạn chỉ cần trình duyệt web.

---

## 3. Quy trình Onboarding

### Bước 1: Đăng ký tài khoản

1. Truy cập dashboard: `https://sdlc.nhatquangholding.com`
2. Click **"Đăng ký"** hoặc **"Sign Up"**
3. Điền thông tin:
   - Email công ty
   - Tên doanh nghiệp
   - Ngành nghề (F&B / Hospitality / Retail)
   - Quy mô (Micro / Small / Medium)

### Bước 2: Xác nhận email

1. Kiểm tra email inbox (và spam folder)
2. Click link xác nhận
3. Đăng nhập vào dashboard

### Bước 3: Tham gia Pilot Program

1. Sau khi đăng nhập, bạn sẽ thấy **"EP-06 Pilot Program"**
2. Click **"Tham gia ngay"**
3. Điền thông tin bổ sung:
   - Tên công ty
   - Quy mô nhân viên
   - Nguồn giới thiệu (nếu có)

---

## 4. Tạo ứng dụng đầu tiên

### Quy trình 5 bước (TTFV < 30 phút)

```
┌─────────────────────────────────────────────────────────────────────┐
│  BƯỚC 1          BƯỚC 2          BƯỚC 3          BƯỚC 4          BƯỚC 5   │
│  Chọn ngành  →  Đặt tên app  →  Chọn tính năng  →  Chờ tạo code  →  Xong!   │
│  (1 phút)       (1 phút)        (3 phút)          (5-15 phút)      (✓)     │
└─────────────────────────────────────────────────────────────────────┘
```

### Bước 1: Chọn ngành (Domain Selection)

Chọn một trong ba ngành:

| Ngành | Mô tả | Ví dụ tính năng |
|-------|-------|-----------------|
| **Nhà hàng (F&B)** | Quản lý order, menu, bàn | Đặt bàn, thanh toán, báo cáo |
| **Khách sạn (Hospitality)** | Quản lý phòng, khách, booking | Check-in, housekeeping, hóa đơn |
| **Cửa hàng (Retail)** | Quản lý sản phẩm, kho, bán hàng | POS, inventory, báo cáo doanh thu |

### Bước 2: Đặt tên ứng dụng (App Naming)

- Nhập tên ứng dụng (tiếng Việt có dấu OK)
- Ví dụ: "Quản lý Quán Cà Phê Thơm", "Hotel Đà Lạt Booking"

### Bước 3: Chọn tính năng (Feature Selection)

**F&B Features:**
- [ ] Quản lý menu
- [ ] Đặt bàn online
- [ ] Order tại bàn (QR code)
- [ ] Thanh toán (VNPay, Momo)
- [ ] Báo cáo doanh thu
- [ ] Quản lý nhân viên

**Hospitality Features:**
- [ ] Quản lý phòng
- [ ] Booking online
- [ ] Check-in / Check-out
- [ ] Housekeeping tracker
- [ ] Hóa đơn tự động
- [ ] Báo cáo occupancy

**Retail Features:**
- [ ] Quản lý sản phẩm
- [ ] Quản lý kho
- [ ] Bán hàng (POS)
- [ ] Barcode/QR scan
- [ ] Báo cáo tồn kho
- [ ] Quản lý nhân viên

### Bước 4: Chọn quy mô (Scale Selection)

| Quy mô | Mô tả | Phù hợp với |
|--------|-------|-------------|
| **Micro** | 1-5 nhân viên | Quán cà phê, tiệm tạp hóa |
| **Small** | 6-20 nhân viên | Nhà hàng vừa, khách sạn mini |
| **Medium** | 21-50 nhân viên | Chuỗi nhà hàng, khách sạn 3-4 sao |

### Bước 5: Chờ tạo code (Code Generation)

Sau khi click **"Tạo ứng dụng"**, hệ thống sẽ:

1. **Tạo Blueprint** (~30 giây)
   - Phân tích yêu cầu
   - Thiết kế cấu trúc database
   - Lên kế hoạch API

2. **Sinh code** (~5-10 phút)
   - Backend FastAPI (Python)
   - Database PostgreSQL
   - API documentation

3. **Kiểm tra chất lượng** (~2-5 phút)
   - Gate 1: Syntax check
   - Gate 2: Security scan
   - Gate 3: Context validation
   - Gate 4: Test execution

4. **Hoàn thành** ✓
   - Download source code
   - Hướng dẫn deploy

---

## 5. Hiểu về TTFV

### TTFV là gì?

**TTFV = Time To First Value** (Thời gian đến Giá trị đầu tiên)

Đây là thời gian từ khi bạn click "Tạo ứng dụng" đến khi nhận được code chạy được.

### Mục tiêu TTFV

| Metric | Target | Ý nghĩa |
|--------|--------|---------|
| **TTFV** | < 30 phút | Từ ý tưởng đến code chạy được |
| **Quality Gate** | > 95% pass | Code an toàn, không lỗi cơ bản |
| **Satisfaction** | > 8/10 | Hài lòng với kết quả |

### Theo dõi TTFV của bạn

Sau mỗi session, bạn có thể xem:

- **Thời gian tổng**: Từ start đến finish
- **Breakdown theo stage**: Mỗi bước mất bao lâu
- **So sánh với target**: Có đạt <30 phút không

---

## 6. Xử lý lỗi thường gặp

### Lỗi 1: "Generation timeout"

**Nguyên nhân**: Server đang bận hoặc yêu cầu quá phức tạp

**Cách xử lý**:
1. Đợi 2-3 phút và thử lại
2. Giảm số tính năng chọn
3. Chọn quy mô nhỏ hơn

### Lỗi 2: "Quality gate failed"

**Nguyên nhân**: Code sinh ra chưa đạt tiêu chuẩn

**Cách xử lý**:
1. Hệ thống sẽ tự động retry (tối đa 3 lần)
2. Nếu vẫn fail → escalate lên team hỗ trợ
3. Check email để nhận thông báo kết quả

### Lỗi 3: "Provider unavailable"

**Nguyên nhân**: AI model tạm thời không khả dụng

**Cách xử lý**:
1. Hệ thống tự động chuyển sang provider khác
2. Thời gian có thể lâu hơn một chút
3. Không cần làm gì - chờ tự động hoàn thành

---

## 7. FAQ

### Q: Tôi cần biết lập trình không?

**A**: Không cần! EP-06 được thiết kế cho người không biết code. Bạn chỉ cần mô tả yêu cầu, hệ thống sẽ tạo code cho bạn.

### Q: Code sinh ra có an toàn không?

**A**: Có! Mỗi code được kiểm tra qua 4 cổng chất lượng:
- Syntax check (không lỗi cú pháp)
- Security scan (không có lỗ hổng bảo mật)
- Context validation (phù hợp yêu cầu)
- Test execution (chạy được tests)

### Q: Tôi có thể customize code sau khi sinh không?

**A**: Có! Code sinh ra là source code đầy đủ, bạn có thể:
- Tự sửa nếu biết code
- Thuê dev để customize
- Liên hệ team hỗ trợ để yêu cầu thêm

### Q: Chi phí như thế nào?

**A**: Founder Plan $99/team/tháng (~2.5M VND), bao gồm:
- Unlimited code generation
- 10 dự án active
- Email support
- SDLC governance

### Q: Làm sao để deploy ứng dụng?

**A**: Sau khi sinh code xong, bạn sẽ nhận được:
- Source code (download ZIP)
- Docker files (cho deploy)
- Hướng dẫn deploy từng bước
- Option: Managed hosting ($50/tháng thêm)

---

## Liên hệ hỗ trợ

- **Email**: support@sdlc-orchestrator.com
- **Hotline**: 1900-xxxx (8AM-6PM, T2-T6)
- **Chat**: Dashboard → Help → Live Chat

---

**Document Control**

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | Dec 24, 2025 | Initial version - Sprint 50 |

---

*EP-06 - Từ ý tưởng đến ứng dụng trong 30 phút.*
