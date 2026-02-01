#!/bin/bash
# Manual GitHub Device Flow Test
# Usage: ./test-github-device-flow-manual.sh

set -e

API_URL="http://localhost:8300/api/v1"

echo "======================================================"
echo "GitHub OAuth Device Flow - Manual Test"
echo "======================================================"
echo ""

# Step 1: Initiate device flow
echo "Step 1: Initiating device flow..."
RESPONSE=$(curl -s -X POST "$API_URL/auth/github/device")

# Check if error
if echo "$RESPONSE" | jq -e '.detail' > /dev/null 2>&1; then
    ERROR=$(echo "$RESPONSE" | jq -r '.detail')
    echo "❌ Error: $ERROR"
    echo ""
    echo "Possible causes:"
    echo "1. Device Flow chưa enable trên GitHub OAuth App"
    echo "   → https://github.com/settings/developers → Enable Device Flow"
    echo "2. GitHub OAuth chưa configured trong backend .env.staging"
    echo "   → Check GITHUB_CLIENT_ID và GITHUB_CLIENT_SECRET"
    exit 1
fi

# Extract device flow data
DEVICE_CODE=$(echo "$RESPONSE" | jq -r '.device_code')
USER_CODE=$(echo "$RESPONSE" | jq -r '.user_code')
VERIFICATION_URI=$(echo "$RESPONSE" | jq -r '.verification_uri')
INTERVAL=$(echo "$RESPONSE" | jq -r '.interval')

echo "✅ Device flow initiated successfully"
echo ""
echo "======================================================"
echo "📋 YOUR ACTION REQUIRED:"
echo "======================================================"
echo ""
echo "1. Open browser: $VERIFICATION_URI"
echo "2. Enter code: $USER_CODE"
echo "3. Authorize the app"
echo ""
echo "Press ENTER after you've authorized..."
read

# Step 2: Poll for token
echo ""
echo "Step 2: Polling for authorization..."
MAX_ATTEMPTS=60  # 5 minutes max (60 attempts * 5 seconds)
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    ATTEMPT=$((ATTEMPT + 1))

    TOKEN_RESPONSE=$(curl -s -X POST "$API_URL/auth/github/token" \
        -H "Content-Type: application/json" \
        -d "{\"device_code\": \"$DEVICE_CODE\"}")

    # Check if we got tokens
    if echo "$TOKEN_RESPONSE" | jq -e '.access_token' > /dev/null 2>&1; then
        echo ""
        echo "✅ Authorization successful!"
        echo ""
        ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token')
        REFRESH_TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.refresh_token')

        echo "======================================================"
        echo "🎉 Login Successful!"
        echo "======================================================"
        echo ""
        echo "Access Token: ${ACCESS_TOKEN:0:50}..."
        echo "Refresh Token: ${REFRESH_TOKEN:0:50}..."
        echo ""

        # Test API call with token
        echo "Testing API with token..."
        USER_INFO=$(curl -s "$API_URL/auth/me" \
            -H "Authorization: Bearer $ACCESS_TOKEN")

        if echo "$USER_INFO" | jq -e '.email' > /dev/null 2>&1; then
            EMAIL=$(echo "$USER_INFO" | jq -r '.email')
            NAME=$(echo "$USER_INFO" | jq -r '.name')
            echo "✅ Logged in as: $NAME ($EMAIL)"
        fi

        echo ""
        echo "======================================================"
        echo "✅ Device Flow Test PASSED!"
        echo "======================================================"
        exit 0
    fi

    # Check for errors
    ERROR_CODE=$(echo "$TOKEN_RESPONSE" | jq -r '.error // empty')

    if [ "$ERROR_CODE" == "authorization_pending" ]; then
        echo -n "."
        sleep $INTERVAL
        continue
    elif [ "$ERROR_CODE" == "slow_down" ]; then
        echo ""
        echo "⚠️  Polling too fast, slowing down..."
        INTERVAL=$((INTERVAL + 5))
        sleep $INTERVAL
        continue
    elif [ "$ERROR_CODE" == "expired_token" ]; then
        echo ""
        echo "❌ Device code expired (15 minutes timeout)"
        exit 1
    elif [ "$ERROR_CODE" == "access_denied" ]; then
        echo ""
        echo "❌ User denied authorization"
        exit 1
    else
        echo ""
        echo "❌ Unknown error: $TOKEN_RESPONSE"
        exit 1
    fi
done

echo ""
echo "❌ Timeout: User did not authorize within 5 minutes"
exit 1
