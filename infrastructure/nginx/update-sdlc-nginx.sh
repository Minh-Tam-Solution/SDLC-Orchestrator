#!/bin/bash
# ============================================
# Script to update SDLC nginx config
# Run with: sudo bash update-sdlc-nginx.sh
# ============================================

set -e

NGINX_CONFIG="/etc/nginx/sites-enabled/nhatquangholding-services"
NEW_SDLC_BLOCK="/home/nqh/shared/SDLC-Orchestrator/infrastructure/nginx/sdlc-server-update.conf"
BACKUP_FILE="${NGINX_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"

echo "=== SDLC Nginx Config Update Script ==="
echo ""

# Step 1: Backup
echo "[1/4] Creating backup..."
cp "$NGINX_CONFIG" "$BACKUP_FILE"
echo "  Backup created: $BACKUP_FILE"

# Step 2: Find line numbers for SDLC block
echo "[2/4] Finding SDLC server block..."
START_LINE=$(grep -n "# SDLC Platform - sdlc.nhatquangholding.com" "$NGINX_CONFIG" | head -1 | cut -d: -f1)
# Find the line with "# SOP Generator" which marks end of SDLC block
END_LINE=$(grep -n "# SOP Generator - sop.nhatquangholding.com" "$NGINX_CONFIG" | head -1 | cut -d: -f1)

if [ -z "$START_LINE" ] || [ -z "$END_LINE" ]; then
    echo "ERROR: Could not find SDLC or SOP Generator markers"
    exit 1
fi

# SDLC block ends 2 lines before SOP Generator (the # ==== separator line)
END_LINE=$((END_LINE - 2))
echo "  Found SDLC block: lines $START_LINE to $END_LINE"

# Step 3: Replace the block
echo "[3/4] Replacing SDLC server block..."

# Create temp file with:
# 1. Everything before SDLC block (including the # ==== line before it)
# 2. New SDLC block
# 3. Everything after SDLC block (starting from # ==== before SOP)
{
    # Keep lines 1 to START_LINE-1 (everything before SDLC including separator)
    head -n $((START_LINE - 1)) "$NGINX_CONFIG"

    # Insert new SDLC block
    cat "$NEW_SDLC_BLOCK"

    # Keep lines from END_LINE+1 to end (# ==== separator and SOP Generator onwards)
    tail -n +$((END_LINE + 1)) "$NGINX_CONFIG"
} > "${NGINX_CONFIG}.tmp"

# Replace original with temp
mv "${NGINX_CONFIG}.tmp" "$NGINX_CONFIG"
echo "  Replaced successfully"

# Step 4: Test and reload
echo "[4/4] Testing nginx config..."
nginx -t

echo ""
echo "=== Config test passed! Reloading nginx... ==="
systemctl reload nginx

echo ""
echo "=== DONE! Verifying routes... ==="
echo ""
echo "Testing / (should show Next.js Landing - lang='vi'):"
curl -s https://sdlc.nhatquangholding.com/ 2>/dev/null | head -1

echo ""
echo "Testing /login (should go to Landing 8311):"
curl -s -o /dev/null -w "  Status: %{http_code}\n" https://sdlc.nhatquangholding.com/login

echo ""
echo "Testing /platform-admin (should show React Dashboard - lang='en'):"
curl -s https://sdlc.nhatquangholding.com/platform-admin 2>/dev/null | head -1

echo ""
echo "=== Update complete! ==="
echo ""
echo "Expected results:"
echo "  / → Next.js landing (lang='vi', SDLC Orchestrator title)"
echo "  /login → Next.js login page"
echo "  /platform-admin → React dashboard (lang='en', Vite)"
