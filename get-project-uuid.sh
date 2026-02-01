#!/bin/bash
# Get Project UUID for Extension Config

if [ -z "$1" ]; then
    echo "Usage: ./get-project-uuid.sh <ACCESS_TOKEN>"
    echo ""
    echo "Get ACCESS_TOKEN from previous debug script output"
    exit 1
fi

ACCESS_TOKEN="$1"
API_URL="https://sdlc.nhatquangholding.com"

echo "======================================================"
echo "Fetching Projects..."
echo "======================================================"
echo ""

PROJECTS=$(curl -s "$API_URL/api/v1/projects" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

echo "$PROJECTS" | jq .

echo ""
echo "======================================================"
echo "Looking for SDLC-Orchestrator project..."
echo "======================================================"
echo ""

# Find SDLC-Orchestrator project
PROJECT_UUID=$(echo "$PROJECTS" | jq -r '.[] | select(.name == "SDLC-Orchestrator" or .name == "sdlc-orchestrator") | .id' | head -1)

if [ -n "$PROJECT_UUID" ]; then
    echo "✅ Found SDLC-Orchestrator project!"
    echo "   UUID: $PROJECT_UUID"
    echo ""
    echo "======================================================"
    echo "Update Extension Config:"
    echo "======================================================"
    echo ""
    echo "Update .vscode/settings.json:"
    echo ""
    echo '{'
    echo '  "sdlc.apiUrl": "https://sdlc.nhatquangholding.com",'
    echo "  \"sdlc.defaultProjectId\": \"$PROJECT_UUID\""
    echo '}'
    echo ""
else
    echo "❌ SDLC-Orchestrator project not found"
    echo ""
    echo "Available projects:"
    echo "$PROJECTS" | jq -r '.[] | "  - \(.name) (UUID: \(.id))"'
    echo ""
    echo "You may need to:"
    echo "1. Create a new project named 'SDLC-Orchestrator'"
    echo "2. Or use an existing project UUID"
fi
