# SendGrid Setup Guide - Sprint 128 Team Invitation System

**Date**: January 31, 2026
**Purpose**: Configure SendGrid email service for team invitation emails
**Time Estimate**: 2 hours
**Reference**: Sprint 128 Infrastructure Setup

---

## Overview

SendGrid will handle all invitation emails with proper DMARC/SPF/DKIM authentication to ensure high deliverability and prevent emails from going to spam.

**Free Tier Limits**:
- 100 emails/day (sufficient for MVP)
- All SendGrid features included
- No credit card required for free tier

---

## Step 1: Create SendGrid Account (15 minutes)

### 1.1 Sign Up

1. Go to: https://sendgrid.com/
2. Click **"Start for Free"**
3. Fill in registration form:
   - **Email**: nqh@nhatquangholding.com (or your work email)
   - **Password**: Use strong password (12+ chars)
   - **Company**: SDLC Orchestrator
   - **Role**: Developer

4. Verify email (check inbox for verification link)

### 1.2 Complete Profile

After email verification:
1. Log in to SendGrid dashboard
2. Complete profile setup:
   - **Use case**: Transactional emails
   - **Monthly email volume**: 0-1,000
   - **Industry**: Software Development

---

## Step 2: Sender Authentication (30 minutes)

### 2.1 Single Sender Verification (Quick Start)

**For Development/Testing** (fastest):

1. Go to **Settings** → **Sender Authentication** → **Single Sender Verification**
2. Click **"Create New Sender"**
3. Fill in sender details:
   ```
   From Name: SDLC Orchestrator
   From Email Address: noreply@sdlc-orchestrator.com
   Reply To: support@sdlc-orchestrator.com
   Company Address: [Your company address]
   City: [Your city]
   Country: Vietnam
   ```
4. Click **"Create"**
5. **CRITICAL**: Check email inbox for verification link
6. Click verification link to activate sender

**Status**: ✅ Ready to send emails immediately after verification

---

### 2.2 Domain Authentication (Production - Optional)

**For Production** (better deliverability, takes 24-48 hours):

1. Go to **Settings** → **Sender Authentication** → **Authenticate Your Domain**
2. Click **"Get Started"**
3. Select **DNS Provider**: Choose your DNS provider (e.g., Cloudflare, AWS Route53)
4. Enter your domain: `sdlc-orchestrator.com`
5. SendGrid will provide DNS records to add:

**Example DNS Records**:
```
# SPF Record
Type: TXT
Host: @
Value: v=spf1 include:sendgrid.net ~all

# DKIM Records (SendGrid provides 3 records)
Type: CNAME
Host: s1._domainkey
Value: s1.domainkey.u12345678.wl123.sendgrid.net

Type: CNAME
Host: s2._domainkey
Value: s2.domainkey.u12345678.wl123.sendgrid.net

Type: CNAME
Host: em1234
Value: u12345678.wl123.sendgrid.net
```

6. Add these records to your DNS provider
7. Return to SendGrid → Click **"Verify"**
8. Wait for DNS propagation (24-48 hours)

**For Sprint 128**: Use **Single Sender Verification** for now, domain authentication later.

---

## Step 3: Generate API Key (10 minutes)

### 3.1 Create API Key

1. Go to **Settings** → **API Keys**
2. Click **"Create API Key"**
3. Configuration:
   ```
   API Key Name: SDLC Orchestrator - Team Invitations
   API Key Permissions: Full Access (Mail Send)
   ```
4. Click **"Create & View"**
5. **CRITICAL**: Copy API key NOW (only shown once)
   ```
   SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

### 3.2 Store API Key Securely

**Development** (.env.local):
```bash
SENDGRID_API_KEY="SG.xxx_your_actual_key_here"
```

**Production** (Secrets Manager):
```bash
# AWS Secrets Manager
aws secretsmanager create-secret \
  --name sdlc-orchestrator/sendgrid-api-key \
  --secret-string "SG.xxx_your_actual_key_here"

# Or HashiCorp Vault
vault kv put secret/sendgrid api_key="SG.xxx_your_actual_key_here"
```

---

## Step 4: Test Email Sending (15 minutes)

### 4.1 Test with SendGrid Dashboard

1. Go to **Email API** → **Integration Guide**
2. Select **cURL** for quick test
3. Run test command:

```bash
curl --request POST \
  --url https://api.sendgrid.com/v3/mail/send \
  --header "Authorization: Bearer SG.xxx_your_actual_key_here" \
  --header 'Content-Type: application/json' \
  --data '{
    "personalizations": [
      {
        "to": [{"email": "YOUR_EMAIL@example.com"}],
        "subject": "SendGrid Test - SDLC Orchestrator"
      }
    ],
    "from": {
      "email": "noreply@sdlc-orchestrator.com",
      "name": "SDLC Orchestrator"
    },
    "content": [
      {
        "type": "text/plain",
        "value": "This is a test email from SDLC Orchestrator via SendGrid."
      }
    ]
  }'
```

4. Check your email inbox (should arrive within 1 minute)

### 4.2 Test with Backend Service

Create test script:

```bash
# backend/scripts/test_sendgrid.py
import os
import requests

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
TEST_EMAIL = "YOUR_EMAIL@example.com"

payload = {
    "personalizations": [
        {
            "to": [{"email": TEST_EMAIL}],
            "subject": "Test Invitation - SDLC Orchestrator"
        }
    ],
    "from": {
        "email": "noreply@sdlc-orchestrator.com",
        "name": "SDLC Orchestrator"
    },
    "content": [
        {
            "type": "text/html",
            "value": "<h1>Test Email</h1><p>If you receive this, SendGrid is working!</p>"
        }
    ]
}

response = requests.post(
    "https://api.sendgrid.com/v3/mail/send",
    json=payload,
    headers={
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json"
    }
)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 202:
    print("✅ Email sent successfully!")
else:
    print("❌ Email send failed!")
```

Run test:
```bash
cd backend
SENDGRID_API_KEY="SG.xxx" python scripts/test_sendgrid.py
```

---

## Step 5: Configure Backend (30 minutes)

### 5.1 Update Environment Variables

Edit `backend/.env.local`:

```bash
# Email Service
SENDGRID_API_KEY="SG.xxx_your_actual_key_here"
SENDGRID_FROM_EMAIL="noreply@sdlc-orchestrator.com"
SENDGRID_FROM_NAME="SDLC Orchestrator"

# Frontend URLs
FRONTEND_URL="http://localhost:3000"
INVITATION_ACCEPT_URL="http://localhost:3000/invitations/accept"

# Invitation Settings
INVITATION_EXPIRY_DAYS=7
```

### 5.2 Update Config Class

Edit `backend/app/core/config.py`:

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # Email Service (SendGrid)
    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = "noreply@sdlc-orchestrator.com"
    SENDGRID_FROM_NAME: str = "SDLC Orchestrator"

    # Frontend URLs
    FRONTEND_URL: str = "http://localhost:3000"
    INVITATION_ACCEPT_URL: str = "http://localhost:3000/invitations/accept"

    # Invitation Settings
    INVITATION_EXPIRY_DAYS: int = 7
    MAX_INVITATIONS_PER_TEAM_PER_HOUR: int = 50
    MAX_INVITATIONS_PER_EMAIL_PER_DAY: int = 3
    MAX_INVITATION_RESENDS: int = 3
    INVITATION_RESEND_COOLDOWN_MINUTES: int = 5
```

### 5.3 Test Integration

```bash
# Start backend
cd backend
uvicorn app.main:app --reload

# In another terminal, test invitation email
curl -X POST http://localhost:8000/api/v1/teams/{team_id}/invitations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "email": "test@example.com",
    "role": "member",
    "message": "Welcome to the team!"
  }'
```

---

## Step 6: Monitor Email Activity (Ongoing)

### 6.1 SendGrid Dashboard Monitoring

1. Go to **Activity** → **Activity Feed**
2. Monitor:
   - Delivered emails
   - Bounces (invalid emails)
   - Spam reports
   - Clicks/Opens (if tracking enabled)

### 6.2 Email Deliverability Tips

**Best Practices**:
- ✅ Always use verified sender email
- ✅ Include unsubscribe link (for marketing emails)
- ✅ Monitor bounce rate (<5%)
- ✅ Avoid spam trigger words ("Free", "Click here", "Act now")
- ✅ Use plain text + HTML versions
- ✅ Test emails before sending to production

**Red Flags**:
- ❌ Bounce rate >10% (bad email list)
- ❌ Spam rate >0.1% (content issues)
- ❌ Hard bounces (permanent delivery failures)

---

## Troubleshooting

### Issue 1: Email Not Received

**Possible Causes**:
1. API key invalid or expired
2. Sender email not verified
3. Email went to spam folder
4. Recipient email invalid

**Solutions**:
```bash
# Check API key
curl https://api.sendgrid.com/v3/user/profile \
  -H "Authorization: Bearer SG.xxx"

# Should return 200 OK with user profile

# Check sender verification status
# Go to Settings → Sender Authentication
# Ensure status is "Verified" (green checkmark)

# Check spam folder
# Search for "SDLC Orchestrator" or "noreply@sdlc-orchestrator.com"
```

### Issue 2: 401 Unauthorized

**Cause**: Invalid API key

**Solution**:
1. Verify API key is correct (copy-paste carefully)
2. Check API key permissions (should be "Full Access")
3. Regenerate API key if needed

### Issue 3: 403 Forbidden

**Cause**: Sender email not verified

**Solution**:
1. Go to Settings → Sender Authentication
2. Verify sender email (check verification email)
3. Wait for DNS propagation (if using domain authentication)

---

## Success Criteria

- ✅ SendGrid account created and activated
- ✅ Sender email verified (green checkmark in dashboard)
- ✅ API key generated and stored securely
- ✅ Test email sent successfully (202 Accepted response)
- ✅ Test email received in inbox (not spam)
- ✅ Backend environment variables configured
- ✅ Integration test passed

---

## Next Steps

After SendGrid setup complete:
1. ✅ Move to **Priority 2**: Redis Configuration
2. ✅ Test rate limiting with Redis
3. ✅ Run full integration test (database + Redis + SendGrid)

---

**Status**: 🟡 **IN PROGRESS**
**Owner**: Backend Team
**Deadline**: January 31, 2026 (12 PM)
**Estimated Time**: 2 hours

---

**Last Updated**: January 31, 2026
**Next Review**: After successful test email delivery
