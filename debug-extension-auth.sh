#!/bin/bash
# Debug Extension Authentication Flow
# Finds exactly what's wrong with Context Overlay

set -e

API_URL="https://sdlc.nhatquangholding.com"
PROJECT_ID="local-sdlc-orchestrator"

echo "======================================================"
echo "🔍 SDLC Extension Authentication Debug"
echo "======================================================"
echo ""

# Step 1: Test Backend Health
echo "Step 1: Testing backend health..."
HEALTH=$(curl -s "$API_URL/api/v1/auth/health")
echo "✅ Backend: $(echo $HEALTH | jq -r '.status')"
echo ""

# Step 2: Test Device Flow Initiation
echo "Step 2: Testing GitHub Device Flow initiation..."
DEVICE_FLOW=$(curl -s -X POST "$API_URL/api/v1/auth/github/device")

if echo "$DEVICE_FLOW" | jq -e '.detail' > /dev/null 2>&1; then
    echo "❌ Device Flow Error: $(echo $DEVICE_FLOW | jq -r '.detail')"
    exit 1
fi

USER_CODE=$(echo "$DEVICE_FLOW" | jq -r '.user_code')
DEVICE_CODE=$(echo "$DEVICE_FLOW" | jq -r '.device_code')
VERIFICATION_URI=$(echo "$DEVICE_FLOW" | jq -r '.verification_uri')

echo "✅ Device Flow initiated"
echo "   User Code: $USER_CODE"
echo "   Verification: $VERIFICATION_URI"
echo ""

# Step 3: Ask user to authorize
echo "======================================================"
echo "📋 ACTION REQUIRED:"
echo "======================================================"
echo ""
echo "1. Open: $VERIFICATION_URI"
echo "2. Enter code: $USER_CODE"
echo "3. Click Authorize"
echo ""
read -p "Press ENTER when you've authorized..."
echo ""

# Step 4: Poll for token
echo "Step 4: Polling for access token..."
MAX_ATTEMPTS=20
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    ATTEMPT=$((ATTEMPT + 1))

    TOKEN_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/auth/github/token" \
        -H "Content-Type: application/json" \
        -d "{\"device_code\": \"$DEVICE_CODE\"}")

    # Check if we got tokens
    if echo "$TOKEN_RESPONSE" | jq -e '.access_token' > /dev/null 2>&1; then
        ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token')
        echo ""
        echo "✅ Access token received!"
        echo "   Token: ${ACCESS_TOKEN:0:30}..."
        break
    fi

    # Check error
    ERROR=$(echo "$TOKEN_RESPONSE" | jq -r '.error // empty')
    if [ "$ERROR" == "authorization_pending" ]; then
        echo -n "."
        sleep 5
    else
        echo ""
        echo "❌ Error: $ERROR"
        echo "   Response: $TOKEN_RESPONSE"
        exit 1
    fi
done

if [ -z "$ACCESS_TOKEN" ]; then
    echo ""
    echo "❌ Timeout waiting for authorization"
    exit 1
fi

echo ""
echo "======================================================"
echo "Step 5: Testing Context Overlay API with token"
echo "======================================================"
echo ""

# Test without auth (should fail)
echo "Test 5a: Without auth token (should fail)..."
NO_AUTH_RESPONSE=$(curl -s "$API_URL/api/v1/agents-md/context/$PROJECT_ID")
echo "Response: $NO_AUTH_RESPONSE"
echo ""

# Test with auth (should succeed)
echo "Test 5b: With auth token (should succeed)..."
WITH_AUTH_RESPONSE=$(curl -s "$API_URL/api/v1/agents-md/context/$PROJECT_ID" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

echo "$WITH_AUTH_RESPONSE" | jq . 2>&1 | head -30

if echo "$WITH_AUTH_RESPONSE" | jq -e '.detail' > /dev/null 2>&1; then
    ERROR_DETAIL=$(echo "$WITH_AUTH_RESPONSE" | jq -r '.detail')
    echo ""
    echo "❌ API Error: $ERROR_DETAIL"
    echo ""
    echo "Possible causes:"
    echo "1. Token is valid but user doesn't have access to project"
    echo "2. Project '$PROJECT_ID' doesn't exist"
    echo "3. Backend authorization logic issue"
    echo ""

    # Try to get user info
    echo "Checking user info..."
    USER_INFO=$(curl -s "$API_URL/api/v1/auth/me" \
        -H "Authorization: Bearer $ACCESS_TOKEN")
    echo "User: $USER_INFO" | jq .

else
    echo ""
    echo "======================================================"
    echo "✅ SUCCESS! Context Overlay API working!"
    echo "======================================================"
    echo ""
fi

# Step 6: Save token for Extension testing
echo ""
echo "======================================================"
echo "Step 6: Token for Extension"
echo "======================================================"
echo ""
echo "Copy this access token to test in Extension:"
echo ""
echo "$ACCESS_TOKEN"
echo ""
echo "To test in Extension Developer Console:"
echo "1. Cmd+Shift+P → Developer: Toggle Developer Tools"
echo "2. Console tab"
echo "3. Run: localStorage.setItem('sdlc_access_token', '$ACCESS_TOKEN')"
echo "4. Reload Extension"
echo ""
