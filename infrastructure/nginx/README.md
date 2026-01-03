# NGINX Reverse Proxy Configuration

## Domain
- **Production**: `https://sdlc.nhatquangholding.com`
- **Access**: NAT from router to internal server 192.168.1.2 (no Cloudflare)
- **Reference**: `/home/nqh/shared/models/docs/admin/PORT_ALLOCATION_MANAGEMENT.md`

## Architecture

### Dual-Frontend Setup (Sprint 60)

SDLC Orchestrator uses a **dual-frontend architecture**:
- **Landing Page** (Next.js) - Marketing, Auth, Docs, Checkout
- **Dashboard** (React Vite) - Platform Admin SPA for authenticated users

```
Internet
    │
    ▼
Router (NAT port 80, 443 → 192.168.1.2)
    │
    ▼
NGINX Reverse Proxy (this config)
    │
    ├── /api/*           → localhost:8300 (FastAPI Backend)
    ├── /grafana/*       → localhost:3002 (Grafana Dashboards)
    │
    │ ─── Landing Page (Next.js - port 8311) ───
    ├── /                → localhost:8311 (Homepage/Marketing)
    ├── /login           → localhost:8311 (Login page)
    ├── /register        → localhost:8311 (Registration)
    ├── /auth/*          → localhost:8311 (OAuth callbacks)
    ├── /docs/*          → localhost:8311 (Documentation)
    ├── /checkout/*      → localhost:8311 (VNPay payment)
    ├── /demo            → localhost:8311 (Demo page)
    ├── /marketplace     → localhost:8311 (Marketplace)
    ├── /_next/*         → localhost:8311 (Next.js static)
    │
    │ ─── Dashboard (React Vite - port 8310) ───
    ├── /platform-admin/*→ localhost:8310 (Platform Admin SPA)
    └── /assets/*        → localhost:8310 (Vite static)
```

### Design Decision

See [ADR-024: Frontend Architecture - Dual vs Monolithic](../../docs/02-design/01-ADRs/ADR-024-Frontend-Architecture-Dual-vs-Monolithic.md) for rationale.

## Alternative Domain (via Cloudflare Tunnel)
Per PORT_ALLOCATION_MANAGEMENT.md, Cloudflare routes are also available:
- `https://sdlc.nqh.vn` → Frontend (8310)
- `https://sdlc-api.nhatquangholding.com` → Backend (8300)

## Quick Install

```bash
# On the server
cd /home/nqh/shared/SDLC-Orchestrator/infrastructure/nginx
sudo ./install-nginx.sh
```

## Manual Installation

### 1. Install NGINX and Certbot
```bash
sudo apt-get update
sudo apt-get install -y nginx certbot python3-certbot-nginx
```

### 2. Copy Configuration
```bash
sudo cp sdlc.nhatquangholding.com.conf /etc/nginx/sites-available/sdlc.nhatquangholding.com
sudo ln -s /etc/nginx/sites-available/sdlc.nhatquangholding.com /etc/nginx/sites-enabled/
```

### 3. Get SSL Certificate
```bash
sudo certbot --nginx -d sdlc.nhatquangholding.com
```

### 4. Test and Reload
```bash
sudo nginx -t
sudo systemctl reload nginx
```

## Port Mapping

| Service | Internal Port | Description |
|---------|--------------|-------------|
| Dashboard | 8310 | React Vite (Platform Admin SPA) |
| Landing | 8311 | Next.js (Marketing, Auth, Docs) |
| Backend | 8300 | FastAPI API |
| Grafana | 3002 | Monitoring |
| OPA | 8185 | Policy Engine (internal only) |
| PostgreSQL | 5451 | Database (internal only) |
| Redis | 6395 | Cache (internal only) |
| MinIO | 9097/9098 | Object Storage (internal only) |

## OAuth Flow

After OAuth authentication, users are redirected through the Landing page callback:

```
1. User clicks "Login with GitHub" on /login
2. Redirected to GitHub → GitHub OAuth
3. GitHub redirects to /auth/github/callback (Landing page)
4. Landing page exchanges code for tokens
5. User redirected to /platform-admin (Dashboard)
```

## Rate Limiting

- **API**: 30 requests/second (burst: 50)
- **Login**: 5 requests/minute (burst: 3)

## Security Features

- TLS 1.2/1.3 only
- HSTS enabled (1 year)
- CSP header configured
- X-Frame-Options: SAMEORIGIN
- OCSP Stapling enabled

## Logs

```bash
# Access logs
tail -f /var/log/nginx/sdlc.nhatquangholding.com.access.log

# Error logs
tail -f /var/log/nginx/sdlc.nhatquangholding.com.error.log
```

## SSL Certificate Renewal

Auto-renewal is configured via systemd timer:
```bash
# Check timer status
systemctl status certbot.timer

# Manual renewal test
sudo certbot renew --dry-run
```

## Troubleshooting

### 502 Bad Gateway
- Check if Docker containers are running: `docker ps`
- Check backend health: `curl http://localhost:8300/health`

### SSL Certificate Issues
```bash
# Check certificate status
sudo certbot certificates

# Force renewal
sudo certbot renew --force-renewal
```

### Configuration Errors
```bash
# Test config
sudo nginx -t

# Check syntax
nginx -T | grep -A 5 "server_name sdlc"
```
