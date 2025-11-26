# SDLC Orchestrator API - cURL Examples

**Version**: 1.0.0
**Date**: December 8, 2025
**Base URL**: `http://localhost:8000/api/v1` (Local Development)

---

## 📚 **Table of Contents**

1. [Authentication Workflows](#authentication-workflows)
2. [Gate Management Workflows](#gate-management-workflows)
3. [Evidence Upload Workflows](#evidence-upload-workflows)
4. [Policy Management Workflows](#policy-management-workflows)
5. [Complete End-to-End Workflows](#complete-end-to-end-workflows)
6. [CI/CD Integration Examples](#cicd-integration-examples)

---

## 🔐 **Authentication Workflows**

### **Workflow 1: Login and Get Access Token**

```bash
#!/bin/bash
# login.sh - Login and save access token

BASE_URL="http://localhost:8000/api/v1"
EMAIL="nguyen.van.anh@mtc.com.vn"
PASSWORD="SecurePassword123!"

# Login
echo "=== Login ==="
RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$EMAIL\",
    \"password\": \"$PASSWORD\"
  }")

# Extract access token
ACCESS_TOKEN=$(echo "$RESPONSE" | jq -r '.access_token')
REFRESH_TOKEN=$(echo "$RESPONSE" | jq -r '.refresh_token')

echo "✅ Login successful"
echo "Access Token: ${ACCESS_TOKEN:0:20}..."
echo "Refresh Token: ${REFRESH_TOKEN:0:20}..."

# Save to file for reuse
echo "$ACCESS_TOKEN" > .access_token
echo "$REFRESH_TOKEN" > .refresh_token

echo "💾 Tokens saved to .access_token and .refresh_token"
```

**Usage**:
```bash
chmod +x login.sh
./login.sh
```

---

### **Workflow 2: Get Current User Profile**

```bash
#!/bin/bash
# get-me.sh - Get current user profile

BASE_URL="http://localhost:8000/api/v1"
TOKEN=$(cat .access_token)

echo "=== Get Current User ==="
curl -s -X GET "$BASE_URL/auth/me" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.'
```

**Output**:
```json
{
  "id": "25e9ed25-c232-4ce3-a3ea-5458a85a915b",
  "email": "nguyen.van.anh@mtc.com.vn",
  "username": "nguyen.van.anh",
  "role": "developer",
  "created_at": "2025-11-13T10:30:00Z",
  "last_login_at": "2025-12-08T14:30:00Z"
}
```

---

### **Workflow 3: Refresh Access Token**

```bash
#!/bin/bash
# refresh-token.sh - Refresh expired access token

BASE_URL="http://localhost:8000/api/v1"
REFRESH_TOKEN=$(cat .refresh_token)

echo "=== Refresh Access Token ==="
RESPONSE=$(curl -s -X POST "$BASE_URL/auth/refresh" \
  -H "Content-Type: application/json" \
  -d "{
    \"refresh_token\": \"$REFRESH_TOKEN\"
  }")

# Extract new tokens
NEW_ACCESS_TOKEN=$(echo "$RESPONSE" | jq -r '.access_token')
NEW_REFRESH_TOKEN=$(echo "$RESPONSE" | jq -r '.refresh_token')

echo "✅ Token refreshed"
echo "New Access Token: ${NEW_ACCESS_TOKEN:0:20}..."

# Update saved tokens
echo "$NEW_ACCESS_TOKEN" > .access_token
echo "$NEW_REFRESH_TOKEN" > .refresh_token

echo "💾 New tokens saved"
```

---

## 🚪 **Gate Management Workflows**

### **Workflow 1: List All Gates**

```bash
#!/bin/bash
# list-gates.sh - List all quality gates

BASE_URL="http://localhost:8000/api/v1"
TOKEN=$(cat .access_token)

echo "=== List All Gates ==="
curl -s -X GET "$BASE_URL/gates?limit=10&offset=0" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.gates[] | {id, gate_type, status, title, created_at}'
```

**Output**:
```json
{
  "id": "c9bf9e57-1685-4c89-bafb-ff5af830be8a",
  "gate_type": "G0.1",
  "status": "pending",
  "title": "Problem Definition Review",
  "created_at": "2025-12-08T14:30:00Z"
}
{
  "id": "d8ce0f68-2796-5d9a-ca0c-ge6bg941cf9b",
  "gate_type": "G0.2",
  "status": "approved",
  "title": "Solution Diversity Analysis",
  "created_at": "2025-12-08T15:00:00Z"
}
```

---

### **Workflow 2: Create New Gate**

```bash
#!/bin/bash
# create-gate.sh - Create new quality gate

BASE_URL="http://localhost:8000/api/v1"
TOKEN=$(cat .access_token)
PROJECT_ID="550e8400-e29b-41d4-a716-446655440001"

echo "=== Create New Gate (G0.1) ==="
RESPONSE=$(curl -s -X POST "$BASE_URL/gates" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"project_id\": \"$PROJECT_ID\",
    \"gate_type\": \"G0.1\",
    \"status\": \"pending\",
    \"title\": \"Problem Definition Review\",
    \"description\": \"Define the business problem we are solving\"
  }")

GATE_ID=$(echo "$RESPONSE" | jq -r '.id')

echo "✅ Gate created successfully"
echo "Gate ID: $GATE_ID"
echo "$GATE_ID" > .gate_id
echo "💾 Gate ID saved to .gate_id"
```

---

### **Workflow 3: Get Gate Details**

```bash
#!/bin/bash
# get-gate.sh - Get gate details

BASE_URL="http://localhost:8000/api/v1"
TOKEN=$(cat .access_token)
GATE_ID=$(cat .gate_id)

echo "=== Get Gate Details ==="
curl -s -X GET "$BASE_URL/gates/$GATE_ID" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.'
```

---

### **Workflow 4: Update Gate Status (Approve)**

```bash
#!/bin/bash
# approve-gate.sh - Approve a gate

BASE_URL="http://localhost:8000/api/v1"
TOKEN=$(cat .access_token)
GATE_ID=$(cat .gate_id)

echo "=== Approve Gate ==="
curl -s -X PUT "$BASE_URL/gates/$GATE_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "approved",
    "approval_notes": "Problem definition is clear and well-documented. Approved by CTO."
  }' \
  | jq '.'

echo "✅ Gate approved successfully"
```

---

### **Workflow 5: Filter Gates by Status**

```bash
#!/bin/bash
# filter-gates.sh - Filter gates by status and type

BASE_URL="http://localhost:8000/api/v1"
TOKEN=$(cat .access_token)

echo "=== Filter Gates (Pending G0.1) ==="
curl -s -X GET "$BASE_URL/gates?status=pending&gate_type=G0.1&limit=10" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.gates[] | {id, title, status, gate_type}'
```

---

## 📁 **Evidence Upload Workflows**

### **Workflow 1: Upload Evidence File**

```bash
#!/bin/bash
# upload-evidence.sh - Upload evidence file to gate

BASE_URL="http://localhost:8000/api/v1"
TOKEN=$(cat .access_token)
GATE_ID=$(cat .gate_id)
FILE_PATH="problem-statement.pdf"

echo "=== Upload Evidence File ==="
RESPONSE=$(curl -s -X POST "$BASE_URL/evidence" \
  -H "Authorization: Bearer $TOKEN" \
  -F "gate_id=$GATE_ID" \
  -F "file=@$FILE_PATH" \
  -F "description=Problem Statement Document")

EVIDENCE_ID=$(echo "$RESPONSE" | jq -r '.id')

echo "✅ Evidence uploaded successfully"
echo "Evidence ID: $EVIDENCE_ID"
echo "File: $FILE_PATH"
echo "$EVIDENCE_ID" > .evidence_id
```

---

### **Workflow 2: List Evidence for Gate**

```bash
#!/bin/bash
# list-evidence.sh - List all evidence for a gate

BASE_URL="http://localhost:8000/api/v1"
TOKEN=$(cat .access_token)
GATE_ID=$(cat .gate_id)

echo "=== List Evidence for Gate ==="
curl -s -X GET "$BASE_URL/evidence?gate_id=$GATE_ID" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.evidence[] | {id, file_name, file_size, created_at}'
```

**Output**:
```json
{
  "id": "e8d7c6b5-a4b3-c2d1-e0f9-g8h7i6j5k4l3",
  "file_name": "problem-statement.pdf",
  "file_size": 245678,
  "created_at": "2025-12-08T14:45:00Z"
}
```

---

### **Workflow 3: Download Evidence File**

```bash
#!/bin/bash
# download-evidence.sh - Download evidence file

BASE_URL="http://localhost:8000/api/v1"
TOKEN=$(cat .access_token)
EVIDENCE_ID=$(cat .evidence_id)
OUTPUT_FILE="downloaded-evidence.pdf"

echo "=== Download Evidence File ==="
curl -X GET "$BASE_URL/evidence/$EVIDENCE_ID/download" \
  -H "Authorization: Bearer $TOKEN" \
  -o "$OUTPUT_FILE"

echo "✅ File downloaded: $OUTPUT_FILE"
ls -lh "$OUTPUT_FILE"
```

---

### **Workflow 4: Get Evidence Metadata**

```bash
#!/bin/bash
# get-evidence-metadata.sh - Get evidence metadata

BASE_URL="http://localhost:8000/api/v1"
TOKEN=$(cat .access_token)
EVIDENCE_ID=$(cat .evidence_id)

echo "=== Get Evidence Metadata ==="
curl -s -X GET "$BASE_URL/evidence/$EVIDENCE_ID" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.'
```

**Output**:
```json
{
  "id": "e8d7c6b5-a4b3-c2d1-e0f9-g8h7i6j5k4l3",
  "gate_id": "c9bf9e57-1685-4c89-bafb-ff5af830be8a",
  "file_name": "problem-statement.pdf",
  "file_size": 245678,
  "file_type": "application/pdf",
  "sha256_hash": "d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2",
  "minio_path": "s3://evidence-vault/c9bf9e57-1685-4c89-bafb-ff5af830be8a/problem-statement.pdf",
  "created_at": "2025-12-08T14:45:00Z"
}
```

---

## 📜 **Policy Management Workflows**

### **Workflow 1: List All Policies**

```bash
#!/bin/bash
# list-policies.sh - List all gate policies

BASE_URL="http://localhost:8000/api/v1"
TOKEN=$(cat .access_token)

echo "=== List All Policies ==="
curl -s -X GET "$BASE_URL/policies?limit=10" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.policies[] | {id, name, gate_type, created_at}'
```

---

### **Workflow 2: Create New Policy**

```bash
#!/bin/bash
# create-policy.sh - Create new gate policy

BASE_URL="http://localhost:8000/api/v1"
TOKEN=$(cat .access_token)

echo "=== Create New Policy (G0.1) ==="
RESPONSE=$(curl -s -X POST "$BASE_URL/policies" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "G0.1 Problem Statement Required",
    "description": "Validate that problem statement document is uploaded",
    "gate_type": "G0.1",
    "policy_content": {
      "package": "sdlc.gates.g01",
      "rules": [
        {
          "name": "problem_statement_required",
          "condition": "count(input.evidence) > 0",
          "result": "approved"
        }
      ]
    }
  }')

POLICY_ID=$(echo "$RESPONSE" | jq -r '.id')

echo "✅ Policy created successfully"
echo "Policy ID: $POLICY_ID"
echo "$POLICY_ID" > .policy_id
```

---

### **Workflow 3: Get Policy Details**

```bash
#!/bin/bash
# get-policy.sh - Get policy details

BASE_URL="http://localhost:8000/api/v1"
TOKEN=$(cat .access_token)
POLICY_ID=$(cat .policy_id)

echo "=== Get Policy Details ==="
curl -s -X GET "$BASE_URL/policies/$POLICY_ID" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.'
```

---

## 🔄 **Complete End-to-End Workflows**

### **Workflow: Create Project → Gate → Evidence → Approval**

```bash
#!/bin/bash
# complete-gate-workflow.sh - Complete quality gate workflow

set -e  # Exit on error

BASE_URL="http://localhost:8000/api/v1"
TOKEN=$(cat .access_token)

echo "==============================================="
echo "Complete Quality Gate Workflow"
echo "==============================================="

# Step 1: Login (if needed)
if [ ! -f .access_token ]; then
    echo "Step 0: Login..."
    ./login.sh
    TOKEN=$(cat .access_token)
fi

# Step 2: Create Gate
echo -e "\nStep 1: Create Gate (G0.1 - Problem Definition)"
GATE_RESPONSE=$(curl -s -X POST "$BASE_URL/gates" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "550e8400-e29b-41d4-a716-446655440001",
    "gate_type": "G0.1",
    "status": "pending",
    "title": "Problem Definition Review",
    "description": "Define the business problem we are solving"
  }')

GATE_ID=$(echo "$GATE_RESPONSE" | jq -r '.id')
echo "✅ Gate created: $GATE_ID"

# Step 3: Upload Evidence
echo -e "\nStep 2: Upload Evidence (Problem Statement)"
EVIDENCE_RESPONSE=$(curl -s -X POST "$BASE_URL/evidence" \
  -H "Authorization: Bearer $TOKEN" \
  -F "gate_id=$GATE_ID" \
  -F "file=@problem-statement.pdf" \
  -F "description=Problem Statement Document")

EVIDENCE_ID=$(echo "$EVIDENCE_RESPONSE" | jq -r '.id')
echo "✅ Evidence uploaded: $EVIDENCE_ID"

# Step 4: Approve Gate
echo -e "\nStep 3: Approve Gate"
APPROVE_RESPONSE=$(curl -s -X PUT "$BASE_URL/gates/$GATE_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "approved",
    "approval_notes": "Problem definition is clear. Approved by CTO."
  }')

echo "✅ Gate approved"

# Step 5: Verify Final Status
echo -e "\nStep 4: Verify Gate Status"
curl -s -X GET "$BASE_URL/gates/$GATE_ID" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '{id, gate_type, status, title, approval_notes}'

echo -e "\n✅ Complete workflow finished successfully!"
echo "Gate ID: $GATE_ID"
echo "Evidence ID: $EVIDENCE_ID"
```

---

## 🤖 **CI/CD Integration Examples**

### **Example 1: Check Gate Approval Before Deploy**

```bash
#!/bin/bash
# ci-gate-check.sh - CI/CD gate approval check

set -e

BASE_URL="http://localhost:8000/api/v1"
API_KEY="$SDLC_API_KEY"  # Set in CI/CD environment
PROJECT_ID="550e8400-e29b-41d4-a716-446655440001"
GATE_TYPE="G2"  # Design Ready gate

echo "=== CI/CD: Checking Gate G2 Approval ==="

# Get gate status
GATE_STATUS=$(curl -s -X GET \
  "$BASE_URL/gates?project_id=$PROJECT_ID&gate_type=$GATE_TYPE" \
  -H "X-API-Key: $API_KEY" \
  | jq -r '.gates[0].status')

echo "Gate G2 Status: $GATE_STATUS"

if [ "$GATE_STATUS" != "approved" ]; then
    echo "❌ DEPLOYMENT BLOCKED: Gate G2 is not approved"
    echo "Current status: $GATE_STATUS"
    echo "Please get CTO approval before deploying to production"
    exit 1
fi

echo "✅ Gate G2 approved. Proceeding with deployment..."
# Continue with deployment
```

**Usage in GitHub Actions**:
```yaml
# .github/workflows/deploy.yml
jobs:
  check-gate:
    runs-on: ubuntu-latest
    steps:
      - name: Check Gate G2 Approval
        env:
          SDLC_API_KEY: ${{ secrets.SDLC_API_KEY }}
        run: ./ci-gate-check.sh

  deploy:
    needs: check-gate
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Production
        run: ./deploy.sh
```

---

### **Example 2: Auto-Upload Test Evidence**

```bash
#!/bin/bash
# ci-upload-test-evidence.sh - Auto-upload test reports

set -e

BASE_URL="http://localhost:8000/api/v1"
API_KEY="$SDLC_API_KEY"
GATE_ID="$GATE_G2_ID"  # Set in CI/CD environment

echo "=== CI/CD: Auto-Upload Test Evidence ==="

# Step 1: Run tests
echo "Running tests..."
pytest --junitxml=test-report.xml --cov=app --cov-report=html

# Step 2: Upload test report
echo "Uploading test report..."
curl -X POST "$BASE_URL/evidence" \
  -H "X-API-Key: $API_KEY" \
  -F "gate_id=$GATE_ID" \
  -F "file=@test-report.xml" \
  -F "description=Automated Test Report (95% coverage)"

# Step 3: Upload coverage report
echo "Uploading coverage report..."
tar -czf coverage-report.tar.gz htmlcov/
curl -X POST "$BASE_URL/evidence" \
  -H "X-API-Key: $API_KEY" \
  -F "gate_id=$GATE_ID" \
  -F "file=@coverage-report.tar.gz" \
  -F "description=Code Coverage Report (HTML)"

echo "✅ Test evidence uploaded successfully"
```

---

### **Example 3: Daily Gate Status Report**

```bash
#!/bin/bash
# daily-gate-report.sh - Generate daily gate status report

BASE_URL="http://localhost:8000/api/v1"
API_KEY="$SDLC_API_KEY"

echo "=== Daily Gate Status Report - $(date +%Y-%m-%d) ==="

# Get all pending gates
PENDING_GATES=$(curl -s -X GET "$BASE_URL/gates?status=pending&limit=100" \
  -H "X-API-Key: $API_KEY")

PENDING_COUNT=$(echo "$PENDING_GATES" | jq '.gates | length')

echo "Pending Gates: $PENDING_COUNT"
echo "$PENDING_GATES" | jq -r '.gates[] | "- [\(.gate_type)] \(.title) (created: \(.created_at))"'

# Get approved gates (last 24 hours)
echo -e "\nApproved Gates (Last 24h):"
APPROVED_GATES=$(curl -s -X GET "$BASE_URL/gates?status=approved&limit=100" \
  -H "X-API-Key: $API_KEY")

echo "$APPROVED_GATES" | jq -r '.gates[] | select(.updated_at > (now - 86400 | todate)) | "- [\(.gate_type)] \(.title)"'

# Send to Slack (optional)
# curl -X POST $SLACK_WEBHOOK_URL -d "{\"text\": \"$REPORT\"}"
```

---

## 🔧 **Helper Scripts**

### **Setup Environment**

```bash
#!/bin/bash
# setup-environment.sh - Setup API testing environment

# Create .env file
cat > .env << EOF
BASE_URL=http://localhost:8000/api/v1
USER_EMAIL=nguyen.van.anh@mtc.com.vn
USER_PASSWORD=SecurePassword123!
PROJECT_ID=550e8400-e29b-41d4-a716-446655440001
EOF

echo "✅ Environment file created (.env)"

# Make all scripts executable
chmod +x *.sh

echo "✅ All scripts are now executable"

# Login and save tokens
./login.sh

echo "✅ Setup complete! You can now run other scripts."
```

---

### **Clean Up Tokens**

```bash
#!/bin/bash
# cleanup.sh - Clean up saved tokens

rm -f .access_token .refresh_token .gate_id .evidence_id .policy_id

echo "✅ All saved tokens and IDs cleaned up"
```

---

## 📖 **Additional Resources**

- **OpenAPI Spec**: [openapi.yml](openapi.yml)
- **Postman Collection**: [SDLC-Orchestrator.postman_collection.json](SDLC-Orchestrator.postman_collection.json)
- **API Developer Guide**: [API-DEVELOPER-GUIDE.md](../04-API-Design/API-DEVELOPER-GUIDE.md)

---

**Last Updated**: December 8, 2025
**Version**: 1.0.0
**Status**: Production Ready

---

**End of cURL Examples Guide**
