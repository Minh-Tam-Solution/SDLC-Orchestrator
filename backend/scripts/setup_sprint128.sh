#!/bin/bash

# ============================================================================
# Sprint 128 Interactive Setup Script
# ============================================================================
#
# This script guides you through the infrastructure setup for Sprint 128
#
# Usage:
#   bash scripts/setup_sprint128.sh
#
# Reference: docs/06-deploy/runbooks/SPRINT-128-INFRASTRUCTURE-SETUP.md
#
# ============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo ""
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Main script
clear
print_header "SPRINT 128 - INFRASTRUCTURE SETUP"

echo "This script will help you set up:"
echo "  1. Redis (rate limiting)"
echo "  2. SendGrid (email service)"
echo "  3. Environment configuration"
echo ""
echo "Estimated time: 30 minutes"
echo ""
read -p "Press Enter to continue..."

# ============================================================================
# Step 1: Check Redis
# ============================================================================

print_header "Step 1/3: Redis Configuration"

echo "Checking if Redis is running..."
if docker ps | grep -q redis-invitations; then
    print_success "Redis container 'redis-invitations' is running"

    # Test connection
    if docker exec redis-invitations redis-cli ping > /dev/null 2>&1; then
        print_success "Redis connection test: PONG"
    else
        print_error "Redis is running but not responding"
        exit 1
    fi
else
    print_warning "Redis container not found"
    echo ""
    echo "Creating Redis container..."

    docker run -d \
        --name redis-invitations \
        -p 6380:6379 \
        --restart unless-stopped \
        redis:7.2-alpine \
        redis-server --appendonly yes

    print_success "Redis container created on port 6380"

    # Wait for Redis to start
    sleep 2

    # Test connection
    if docker exec redis-invitations redis-cli ping > /dev/null 2>&1; then
        print_success "Redis connection test: PONG"
    else
        print_error "Redis failed to start"
        exit 1
    fi
fi

echo ""
read -p "Press Enter to continue to SendGrid setup..."

# ============================================================================
# Step 2: SendGrid Setup
# ============================================================================

print_header "Step 2/3: SendGrid Email Service"

echo "SendGrid Account Setup:"
echo ""
echo "1. Open your browser and go to: https://sendgrid.com/"
echo "2. Click 'Start for Free'"
echo "3. Create account (no credit card required)"
echo "4. Verify your email address (check inbox)"
echo ""
read -p "Press Enter when account is created and verified..."

echo ""
print_info "Next: Sender Email Verification"
echo ""
echo "1. Log in to SendGrid dashboard"
echo "2. Go to: Settings → Sender Authentication"
echo "3. Click: Single Sender Verification"
echo "4. Add sender email: noreply@sdlc-orchestrator.com"
echo "   (or use your domain)"
echo "5. Fill in required fields and click Create"
echo "6. Check your email and click verification link"
echo ""
read -p "Press Enter when sender email is verified..."

echo ""
print_info "Next: Generate API Key"
echo ""
echo "1. In SendGrid dashboard, go to: Settings → API Keys"
echo "2. Click: Create API Key"
echo "3. Name: SDLC Orchestrator - Team Invitations"
echo "4. Permissions: Full Access (Mail Send)"
echo "5. Click: Create & View"
echo "6. IMPORTANT: Copy the API key (only shown once!)"
echo ""
read -p "Press Enter when you have copied your API key..."

echo ""
echo "Now paste your SendGrid API key:"
read -p "API Key (SG.xxx...): " SENDGRID_API_KEY

if [[ ! "$SENDGRID_API_KEY" =~ ^SG\. ]]; then
    print_error "Invalid API key format (should start with 'SG.')"
    exit 1
fi

print_success "API key validated"

echo ""
echo "Sender email configuration:"
read -p "From Email (default: noreply@sdlc-orchestrator.com): " SENDGRID_FROM_EMAIL
SENDGRID_FROM_EMAIL=${SENDGRID_FROM_EMAIL:-noreply@sdlc-orchestrator.com}

read -p "From Name (default: SDLC Orchestrator): " SENDGRID_FROM_NAME
SENDGRID_FROM_NAME=${SENDGRID_FROM_NAME:-SDLC Orchestrator}

print_success "SendGrid configuration complete"

echo ""
read -p "Press Enter to update .env.local file..."

# ============================================================================
# Step 3: Update .env.local
# ============================================================================

print_header "Step 3/3: Update Environment Configuration"

ENV_FILE="backend/.env.local"

echo "Updating $ENV_FILE..."

# Create backup
cp "$ENV_FILE" "$ENV_FILE.backup"
print_info "Backup created: $ENV_FILE.backup"

# Update SendGrid variables
sed -i "s|^SENDGRID_API_KEY=.*|SENDGRID_API_KEY=\"$SENDGRID_API_KEY\"|" "$ENV_FILE"
sed -i "s|^SENDGRID_FROM_EMAIL=.*|SENDGRID_FROM_EMAIL=\"$SENDGRID_FROM_EMAIL\"|" "$ENV_FILE"
sed -i "s|^SENDGRID_FROM_NAME=.*|SENDGRID_FROM_NAME=\"$SENDGRID_FROM_NAME\"|" "$ENV_FILE"

print_success "Environment file updated"

# ============================================================================
# Step 4: Test Configuration
# ============================================================================

print_header "Testing Configuration"

echo "1. Testing Redis connection..."
export REDIS_URL="redis://localhost:6380/0"

if python scripts/test_redis.py > /dev/null 2>&1; then
    print_success "Redis test passed"
else
    print_error "Redis test failed"
    print_info "Run manually: python scripts/test_redis.py"
fi

echo ""
echo "2. Testing SendGrid email delivery..."
echo ""
read -p "Enter your email address to receive test email: " TEST_EMAIL

export $(cat "$ENV_FILE" | xargs)
export TEST_EMAIL="$TEST_EMAIL"

if python scripts/test_sendgrid.py; then
    print_success "SendGrid test initiated"
    print_info "Check your inbox: $TEST_EMAIL (may take 1-2 minutes)"
else
    print_error "SendGrid test failed"
    print_info "Run manually: TEST_EMAIL=$TEST_EMAIL python scripts/test_sendgrid.py"
fi

# ============================================================================
# Summary
# ============================================================================

print_header "Setup Complete! 🎉"

echo "Infrastructure Status:"
echo ""
print_success "Redis: Running on port 6380"
print_success "SendGrid: API key configured"
print_success "Environment: .env.local updated"
echo ""

print_info "Configuration Summary:"
echo "  Redis URL:        redis://localhost:6380/0"
echo "  SendGrid From:    $SENDGRID_FROM_EMAIL"
echo "  SendGrid Name:    $SENDGRID_FROM_NAME"
echo "  Test Email:       $TEST_EMAIL"
echo ""

print_info "Next Steps:"
echo "  1. Check your email inbox for test email"
echo "  2. If email received → Setup successful ✅"
echo "  3. If not received → Check spam folder"
echo "  4. Run code review session (2 PM - 4 PM)"
echo ""

print_info "To test manually:"
echo "  Redis:    python scripts/test_redis.py"
echo "  SendGrid: TEST_EMAIL=your@email.com python scripts/test_sendgrid.py"
echo ""

print_success "Infrastructure setup complete!"
echo ""
echo "Press Ctrl+C to exit"
