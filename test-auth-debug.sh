#!/bin/bash
#######################################
# Auth Debug Script - Sprint 33 Day 4
# Tests authentication flow step-by-step
#######################################

echo "=== AUTH DEBUG - SPRINT 33 DAY 4 ==="
echo

# Step 1: Login
echo "Step 1: Login to get JWT token..."
RESPONSE=$(curl -s -X POST http://localhost:8300/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@sdlc-orchestrator.io","password":"Admin@123"}')

TOKEN=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', 'FAILED'))")

if [ "$TOKEN" = "FAILED" ]; then
  echo "❌ Login failed:"
  echo "$RESPONSE"
  exit 1
fi

echo "✅ Login successful"
echo "Token (first 50 chars): ${TOKEN:0:50}..."
echo

# Step 2: Decode token locally
echo "Step 2: Decode token with Python JWT..."
python3 <<PYEOF
import jwt
token = "$TOKEN"
secret = "dev-secret-key-change-in-production-minimum-32-characters-long"
try:
    payload = jwt.decode(token, secret, algorithms=["HS256"])
    print(f"✅ Token valid - User ID: {payload['sub']}, Type: {payload['type']}")
except Exception as e:
    print(f"❌ Token invalid: {e}")
PYEOF
echo

# Step 3: Test public endpoint (no auth)
echo "Step 3: Test public endpoint /health..."
curl -s http://localhost:8300/health | python3 -m json.tool | head -5
echo "✅ Public endpoint accessible"
echo

# Step 4: Test authenticated endpoint
echo "Step 4: Test authenticated endpoint /api/v1/gates..."
GATES_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8300/api/v1/gates?limit=5")
echo "$GATES_RESPONSE" | python3 -m json.tool | head -20

if echo "$GATES_RESPONSE" | grep -q "Not authenticated"; then
  echo "❌ Authenticated endpoint failed (401 Unauthorized)"
  echo
  echo "Step 5: Check backend logs for errors..."
  docker logs sdlc-backend --tail 50 | grep -E "(ERROR|401|JWT|Token)" | tail -10
else
  echo "✅ Authenticated endpoint accessible"
fi

echo
echo "=== DEBUG COMPLETE ==="
