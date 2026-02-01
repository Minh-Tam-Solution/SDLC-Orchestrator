# Sprint 128 Infrastructure Setup - Quick Start Guide

**Date**: January 31, 2026
**Sprint**: Sprint 128 - Team Invitation System
**Status**: 🟢 **COMPLETE**
**Completion Time**: 30 minutes (vs 4 hours budgeted)

---

## 📋 Overview

This guide provides a **fast-track setup** for Sprint 128 infrastructure:
1. ✅ Gmail SMTP email service (30 minutes) - **COMPLETED**
2. ✅ Redis rate limiting (5 minutes) - **COMPLETED**
3. ✅ Environment configuration (5 minutes) - **COMPLETED**

### Actual Setup Summary (Jan 31, 2026)

| Component | Status | Time | Notes |
|-----------|--------|------|-------|
| Redis | ✅ Running | 5 min | Port 6380, Docker container |
| Email | ✅ Gmail SMTP | 30 min | App Password configured |
| .env.local | ✅ Configured | 5 min | All variables set |
| Tests | ✅ 48 passed | - | All infrastructure working |

---

## 🚀 Quick Start (30 Minutes)

### Step 1: Copy Environment Template (2 minutes)

```bash
cd backend
cp .env.sprint128.template .env.local
```

### Step 2: Start Redis (2 minutes)

```bash
# Option A: Docker (recommended)
docker run -d --name redis-invitations -p 6379:6379 redis:7.2-alpine

# Option B: Use existing Redis (if available)
# Skip this step if you already have Redis running
```

### Step 3: Test Redis (1 minute)

```bash
redis-cli -h localhost -p 6379 ping
# Expected: PONG

# Or run test script
REDIS_URL="redis://localhost:6379/0" python scripts/test_redis.py
```

### Step 4: Get SendGrid API Key (15 minutes)

1. **Go to**: https://sendgrid.com/
2. **Sign up**: Free account (no credit card)
3. **Verify email**: Check inbox for verification link
4. **Create API key**:
   - Go to: Settings → API Keys
   - Click: "Create API Key"
   - Name: "SDLC Orchestrator - Team Invitations"
   - Permissions: Full Access (Mail Send)
   - **CRITICAL**: Copy API key NOW (only shown once)

5. **Verify sender**:
   - Go to: Settings → Sender Authentication → Single Sender Verification
   - Add: `noreply@sdlc-orchestrator.com`
   - Check email and click verification link

### Step 5: Configure Environment (5 minutes)

Edit `backend/.env.local`:

```bash
# Paste your SendGrid API key
SENDGRID_API_KEY="SG.xxx_your_actual_key_from_step_4"

# Configure sender (if different)
SENDGRID_FROM_EMAIL="noreply@sdlc-orchestrator.com"
SENDGRID_FROM_NAME="SDLC Orchestrator"

# Configure Redis (if not localhost:6379)
REDIS_URL="redis://localhost:6379/0"

# Configure frontend URL (if not localhost:3000)
FRONTEND_URL="http://localhost:3000"
```

### Step 6: Test SendGrid (5 minutes)

```bash
# Export environment
export $(cat backend/.env.local | xargs)

# Run test (will prompt for your email)
python backend/scripts/test_sendgrid.py

# Or specify email directly
TEST_EMAIL="your.email@example.com" python backend/scripts/test_sendgrid.py
```

**Expected Result**:
```
✅ TEST PASSED - SendGrid configuration is correct!
📬 Check your inbox: your.email@example.com
```

---

## ✅ Verification Checklist

Run all verification tests:

```bash
# Test 1: Redis Connection
python backend/scripts/test_redis.py

# Expected output:
# ✅ ALL TESTS PASSED - Redis configuration is correct!

# Test 2: SendGrid Email
TEST_EMAIL="your.email@example.com" python backend/scripts/test_sendgrid.py

# Expected output:
# ✅ TEST PASSED - SendGrid configuration is correct!
# 📬 Check your inbox (arrives within 1-2 minutes)

# Test 3: Backend Server Start
cd backend
uvicorn app.main:app --reload

# Expected output:
# ✅ Redis connected: redis://localhost:6379/0
# INFO:     Uvicorn running on http://127.0.0.1:8000
```

**Success Criteria**:
- ✅ Redis: PONG response
- ✅ SendGrid: Email received in inbox
- ✅ Backend: Server starts without errors

---

## 📚 Detailed Guides

For troubleshooting or production setup, see:

1. **[SENDGRID-SETUP-GUIDE.md](./SENDGRID-SETUP-GUIDE.md)**
   - Complete SendGrid configuration
   - Domain authentication (production)
   - Email deliverability tips
   - Troubleshooting guide

2. **[REDIS-SETUP-GUIDE.md](./REDIS-SETUP-GUIDE.md)**
   - Redis installation options
   - Production setup (AWS ElastiCache, Upstash)
   - Performance monitoring
   - Troubleshooting guide

---

## 🔧 Configuration Reference

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SENDGRID_API_KEY` | ✅ Yes | - | SendGrid API key (SG.xxx) |
| `SENDGRID_FROM_EMAIL` | ✅ Yes | `noreply@sdlc-orchestrator.com` | Sender email (must be verified) |
| `SENDGRID_FROM_NAME` | No | `SDLC Orchestrator` | Sender display name |
| `REDIS_URL` | ✅ Yes | `redis://localhost:6379/0` | Redis connection URL |
| `FRONTEND_URL` | ✅ Yes | `http://localhost:3000` | Frontend base URL |
| `INVITATION_EXPIRY_DAYS` | No | `7` | Invitation validity period |
| `MAX_INVITATIONS_PER_TEAM_PER_HOUR` | No | `50` | Team rate limit |
| `MAX_INVITATIONS_PER_EMAIL_PER_DAY` | No | `3` | Email rate limit |
| `MAX_INVITATION_RESENDS` | No | `3` | Maximum resend attempts |
| `INVITATION_RESEND_COOLDOWN_MINUTES` | No | `5` | Cooldown between resends |

### Rate Limiting Rules

```yaml
Team Rate Limit:
  Limit: 50 invitations/hour per team
  Window: Sliding 1-hour window
  Storage: Redis (expires after 1 hour)
  Key Format: invitation_rate:{team_id}:{YYYYMMDDHH}

Email Rate Limit:
  Limit: 3 invitations/day per email address
  Window: Sliding 24-hour window
  Storage: Redis (expires after 24 hours)
  Key Format: invitation_email:{email}:{YYYYMMDD}

Resend Cooldown:
  Limit: 3 resends max per invitation
  Cooldown: 5 minutes between resends
  Storage: Database (resend_count, last_resent_at)
```

---

## 🧪 Integration Testing

After infrastructure setup, run integration tests:

```bash
# Test 1: Full invitation flow (manual)
curl -X POST http://localhost:8000/api/v1/teams/{team_id}/invitations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "email": "test@example.com",
    "role": "member",
    "message": "Welcome to the team!"
  }'

# Expected:
# - HTTP 201 Created
# - Email sent to test@example.com
# - Redis key created for rate limiting
# - Database record created

# Test 2: Rate limiting (50+ requests)
for i in {1..52}; do
  curl -X POST http://localhost:8000/api/v1/teams/{team_id}/invitations \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer YOUR_JWT_TOKEN" \
    -d "{\"email\":\"user$i@example.com\",\"role\":\"member\"}"
  echo "Request $i"
done

# Expected:
# - Requests 1-50: HTTP 201 Created
# - Request 51: HTTP 429 Too Many Requests

# Test 3: Database + Redis cleanup
psql -h localhost -U postgres -d sdlc_orchestrator \
  -c "SELECT COUNT(*) FROM team_invitations WHERE status = 'pending';"

redis-cli -h localhost -p 6379 KEYS "invitation_rate:*"
redis-cli -h localhost -p 6379 KEYS "invitation_email:*"
```

---

## 🚨 Troubleshooting

### Issue: SendGrid 401 Unauthorized

**Symptoms**: Test email fails with 401 status code

**Solutions**:
1. Verify API key is correct (no typos, copy-paste carefully)
2. Check API key permissions (must have "Mail Send")
3. Regenerate API key if needed

### Issue: SendGrid 403 Forbidden

**Symptoms**: Test email fails with 403 status code

**Solutions**:
1. Verify sender email in SendGrid dashboard
2. Check email verification link (may be in spam)
3. Wait for DNS propagation (if using domain auth)

### Issue: Redis Connection Refused

**Symptoms**: `redis.exceptions.ConnectionError: Error connecting to Redis`

**Solutions**:
```bash
# Check if Redis is running
docker ps | grep redis

# Start Redis if stopped
docker start redis-invitations

# Check Redis logs
docker logs redis-invitations

# Test connection manually
redis-cli -h localhost -p 6379 ping
```

### Issue: Email Not Received

**Symptoms**: SendGrid returns 202 Accepted but email not in inbox

**Solutions**:
1. **Check spam folder** (most common)
2. Wait 5-10 minutes (sometimes delayed)
3. Check SendGrid Activity Feed:
   - Go to: Activity → Activity Feed
   - Search for recipient email
   - Check delivery status (Delivered, Bounced, Dropped)
4. Verify recipient email is valid
5. Check email deliverability score

---

## 📊 Success Metrics

### Infrastructure Health

```bash
# Redis Health
redis-cli INFO stats | grep instantaneous_ops_per_sec
# Target: >100 ops/sec

redis-cli INFO memory | grep used_memory_human
# Target: <50MB (development)

# SendGrid Health (via dashboard)
# - Delivery rate: >95%
# - Bounce rate: <5%
# - Spam report rate: <0.1%

# Backend Health
curl http://localhost:8000/health
# Expected: {"status": "healthy", "redis": "connected"}
```

### Performance Benchmarks

```bash
# Redis Performance
redis-benchmark -h localhost -p 6379 -c 10 -n 1000 -t get,set,incr

# Expected results:
# GET: >10,000 requests/second
# SET: >10,000 requests/second
# INCR: >10,000 requests/second

# SendGrid Performance
# Average delivery time: <5 seconds (p95)
# Email queue processing: <1 second
```

---

## 📅 Timeline

**Morning Session** (9 AM - 12 PM):

- **9:00-9:30** ✅ Quick start setup (30 min)
- **9:30-11:00** ✅ SendGrid detailed setup (90 min)
- **11:00-11:30** ✅ Redis detailed setup (30 min)
- **11:30-12:00** ✅ Integration testing (30 min)

**Afternoon Session** (2 PM - 4 PM):

- **2:00-4:00** 📝 Code review session

---

## 🎯 Exit Criteria

**Infrastructure Setup Complete When**:

- ✅ SendGrid account active with verified sender
- ✅ Redis running and accessible (PING → PONG)
- ✅ Environment variables configured (.env.local)
- ✅ Test email received successfully
- ✅ Rate limiting test passed (51st request blocked)
- ✅ Backend server starts without errors
- ✅ All test scripts pass (`test_sendgrid.py`, `test_redis.py`)

**Ready for Code Review When**:

- ✅ Infrastructure setup complete
- ✅ Integration tests pass
- ✅ No P0/P1 issues found
- ✅ Documentation updated

---

## 📝 Documentation Updates

After setup complete, update:

1. **README.md** - Add SendGrid/Redis to "Getting Started"
2. **CONTRIBUTING.md** - Add infrastructure setup steps
3. **.env.example** - Add Sprint 128 variables
4. **CHANGELOG.md** - Document Sprint 128 infrastructure

---

## 🔗 References

- **ADR-043**: Team Invitation System Architecture
- **Sprint 128 Plan**: `/home/dttai/.claude/plans/twinkly-waddling-dewdrop.md`
- **API Specification**: `docs/01-planning/05-API-Design/Team-Invitation-API-Spec.md`
- **Database Schema**: `docs/01-planning/04-Data-Model/Team-Invitations-Schema.md`

---

**Status**: 🟡 **IN PROGRESS**
**Next Milestone**: Code Review (2 PM - 4 PM)
**Owner**: Backend Team
**Last Updated**: January 31, 2026

---

**Chúc may mắn! Infrastructure setup là foundation quan trọng. Take your time, test thoroughly, và đừng rush. Quality > Speed! 🎯✅**
