# SPRINT-58: Registration + VNPay Integration
## Marketing & Growth | User Acquisition & Payment

---

**Document Information**

| Field | Value |
|-------|-------|
| **Sprint ID** | SPRINT-58 |
| **Epic** | Marketing & Growth |
| **Duration** | 2 days (Dec 26-27, 2025) |
| **Status** | COMPLETE ✅ (Dec 27, 2025) |
| **Priority** | P0 Must Have |
| **Dependencies** | Sprint 57 complete |
| **Framework** | SDLC 5.1.2 Universal Framework |

---

## Sprint Goal

Implement user registration and VNPay payment integration for Founder Plan subscriptions.

---

## Features Delivered

### Backend

| Feature | File | Status |
|---------|------|--------|
| Registration API | `api/routes/auth.py` | ✅ Complete |
| VNPay Create Payment | `api/routes/payments.py` | ✅ Complete |
| VNPay Return Handler | `api/routes/payments.py` | ✅ Complete |
| VNPay IPN Webhook | `api/routes/payments.py` | ✅ Complete |
| Subscription Model | `models/subscription.py` | ✅ Complete |
| Payment History Model | `models/subscription.py` | ✅ Complete |
| VNPay Service | `services/vnpay_service.py` | ✅ Complete |

### Frontend

| Feature | File | Status |
|---------|------|--------|
| Registration Form | `app/register/page.tsx` | ✅ Complete |
| Login Form | `app/login/page.tsx` | ✅ Complete |
| Checkout Page | `app/checkout/page.tsx` | ✅ Complete |
| Success Page | `app/checkout/success/page.tsx` | ✅ Complete |
| Failed Page | `app/checkout/failed/page.tsx` | ✅ Complete |
| API Client | `lib/api.ts` | ✅ Complete |

### Database

| Table | Purpose | Status |
|-------|---------|--------|
| `subscriptions` | User subscription management | ✅ Migration created |
| `payment_history` | VNPay payment records with idempotency | ✅ Migration created |

---

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | User registration |
| POST | `/auth/login` | Email/password login |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/logout` | Revoke refresh token |
| GET | `/auth/me` | Get current user profile |

### Payments

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/payments/vnpay/create` | Create VNPay payment URL |
| GET | `/payments/vnpay/return` | User return from VNPay |
| POST | `/payments/vnpay/ipn` | VNPay IPN webhook |
| GET | `/payments/{vnp_txn_ref}` | Get payment status |
| GET | `/payments/subscriptions/me` | Get user subscription |

---

## VNPay Integration

### Security

- HMAC-SHA512 signature verification
- Sorted parameters for consistent signing
- Idempotent IPN handling (terminal state machine)
- State: pending → completed/failed (immutable)

### Payment Flow

1. User selects Founder Plan
2. Frontend calls POST `/payments/vnpay/create`
3. Backend generates VNPay payment URL with signature
4. User redirected to VNPay gateway
5. User completes payment on VNPay
6. VNPay sends IPN to `/payments/vnpay/ipn`
7. Backend verifies signature, updates payment status
8. User redirected to success/failed page

### Plan Pricing

| Plan | Monthly | Annual |
|------|---------|--------|
| Founder | 2,500,000 VND | 25,000,000 VND |

---

## Subscription Model

```python
class SubscriptionPlan(str, enum.Enum):
    FREE = "free"
    FOUNDER = "founder"
    STANDARD = "standard"
    ENTERPRISE = "enterprise"

class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"  # Terminal state
    FAILED = "failed"        # Terminal state
```

---

## Configuration

### Environment Variables

```env
# VNPay Configuration
VNPAY_TMN_CODE=your_terminal_code
VNPAY_HASH_SECRET=your_hash_secret
VNPAY_URL=https://sandbox.vnpayment.vn/paymentv2/vpcpay.html
VNPAY_RETURN_URL=http://localhost:3000/checkout/success
```

---

## Success Metrics

| Metric | Target | Status |
|--------|--------|--------|
| Registration flow | E2E working | ✅ |
| VNPay payment URL generation | Working | ✅ |
| IPN webhook handling | Idempotent | ✅ |
| Terminal state enforcement | Immutable | ✅ |

---

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Last Updated** | December 27, 2025 |
| **Owner** | Backend Lead |
| **Approved By** | CTO ✅ (Dec 27, 2025) |
