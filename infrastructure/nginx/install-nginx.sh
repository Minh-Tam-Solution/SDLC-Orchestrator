#!/bin/bash
# SDLC Orchestrator - NGINX Installation Script
#
# Domain: sdlc.nhatquangholding.com
# Access: NAT from router to internal server
#
# Prerequisites:
#   - Ubuntu 22.04+ or Debian 11+
#   - Root access
#   - Docker containers running
#   - Port 80 and 443 open on firewall
#
# Usage:
#   sudo ./install-nginx.sh

set -e

DOMAIN="sdlc.nhatquangholding.com"
EMAIL="it@nhatquangholding.com"  # For Let's Encrypt notifications
NGINX_CONF_DIR="/etc/nginx/sites-available"
NGINX_ENABLED_DIR="/etc/nginx/sites-enabled"
CERTBOT_WEBROOT="/var/www/certbot"

echo "=========================================="
echo "SDLC Orchestrator - NGINX Setup"
echo "Domain: $DOMAIN"
echo "=========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Please run as root (sudo ./install-nginx.sh)"
    exit 1
fi

# Install NGINX and Certbot
echo "[1/6] Installing NGINX and Certbot..."
apt-get update
apt-get install -y nginx certbot python3-certbot-nginx

# Create certbot webroot
echo "[2/6] Creating certbot webroot..."
mkdir -p $CERTBOT_WEBROOT

# Copy NGINX config
echo "[3/6] Copying NGINX configuration..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$SCRIPT_DIR/$DOMAIN.conf" "$NGINX_CONF_DIR/$DOMAIN"

# Create temporary config for certbot (HTTP only)
echo "[4/6] Creating temporary HTTP config for certbot..."
cat > "$NGINX_CONF_DIR/$DOMAIN.temp" << 'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name sdlc.nhatquangholding.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 200 "Waiting for SSL certificate...";
        add_header Content-Type text/plain;
    }
}
EOF

# Enable temporary config
rm -f "$NGINX_ENABLED_DIR/$DOMAIN"
ln -s "$NGINX_CONF_DIR/$DOMAIN.temp" "$NGINX_ENABLED_DIR/$DOMAIN"

# Test and reload NGINX
nginx -t
systemctl reload nginx

# Obtain SSL certificate
echo "[5/6] Obtaining Let's Encrypt SSL certificate..."
certbot certonly \
    --webroot \
    --webroot-path=$CERTBOT_WEBROOT \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    --domain $DOMAIN

# Enable full config with SSL
echo "[6/6] Enabling full NGINX configuration..."
rm -f "$NGINX_ENABLED_DIR/$DOMAIN"
rm -f "$NGINX_CONF_DIR/$DOMAIN.temp"
ln -s "$NGINX_CONF_DIR/$DOMAIN" "$NGINX_ENABLED_DIR/$DOMAIN"

# Test and reload
nginx -t
systemctl reload nginx

# Setup auto-renewal
echo "[OK] Setting up SSL auto-renewal..."
systemctl enable certbot.timer
systemctl start certbot.timer

echo ""
echo "=========================================="
echo "NGINX Setup Complete!"
echo "=========================================="
echo ""
echo "Your SDLC Orchestrator is now accessible at:"
echo "  https://$DOMAIN"
echo ""
echo "SSL Certificate:"
echo "  - Location: /etc/letsencrypt/live/$DOMAIN/"
echo "  - Auto-renewal: Enabled (certbot.timer)"
echo ""
echo "Logs:"
echo "  - Access: /var/log/nginx/$DOMAIN.access.log"
echo "  - Error:  /var/log/nginx/$DOMAIN.error.log"
echo ""
echo "Commands:"
echo "  - Test config:  nginx -t"
echo "  - Reload:       systemctl reload nginx"
echo "  - View logs:    tail -f /var/log/nginx/$DOMAIN.*.log"
echo "  - SSL renew:    certbot renew --dry-run"
echo ""
