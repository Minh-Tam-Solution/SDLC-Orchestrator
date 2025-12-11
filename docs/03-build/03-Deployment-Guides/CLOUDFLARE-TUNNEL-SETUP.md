# Cloudflare Tunnel Setup - SDLC Orchestrator Beta
**Created**: 2025-12-16 (Sprint 33 Day 3)
**Domain**: `sdlc.nqh.vn`
**Target**: `http://localhost:8311` (Beta Frontend)

---

## ✅ **Current Status**

- ✅ **Beta Environment Deployed**: 9/9 services healthy
- ✅ **Frontend Running**: `http://localhost:8311`
- ✅ **Ingress Rule Added**: `/home/dttai/.cloudflared/config.yml` updated
- ⏳ **DNS Route**: Requires manual setup via Cloudflare Dashboard
- ⏳ **Tunnel Reload**: Requires root or tunnel owner permission

---

## 📋 **Manual Setup Steps**

### **Step 1: Verify Ingress Rule** ✅ COMPLETE

The ingress rule has been added to `/home/dttai/.cloudflared/config.yml`:

```yaml
# SDLC Orchestrator Beta Environment
- hostname: sdlc.nqh.vn
  service: http://localhost:8311
  originRequest:
    connectTimeout: 30s
    tlsTimeout: 10s
    keepAliveTimeout: 90s
    keepAliveConnections: 100
    noTLSVerify: false
```

### **Step 2: Add DNS Route** ⏳ MANUAL REQUIRED

**Option A: Via Cloudflare Dashboard (Recommended)**

1. Login to Cloudflare Dashboard: https://dash.cloudflare.com
2. Navigate to: **Zero Trust** → **Networks** → **Tunnels**
3. Select tunnel: `my-tunnel` (ID: `4eb54608-b582-450e-b081-bd6bcc8f59f9`)
4. Click **Public Hostnames** tab
5. Click **Add a public hostname**
6. Fill in:
   - **Subdomain**: `sdlc`
   - **Domain**: `nqh.vn`
   - **Type**: `HTTP`
   - **URL**: `localhost:8311`
7. Click **Save**

**Option B: Via CLI (Requires Authentication)**

```bash
cloudflared tunnel route dns my-tunnel sdlc.nqh.vn
```

*Note: This requires proper Cloudflare authentication. If you get "Authentication error", use Option A instead.*

### **Step 3: Reload Tunnel** ⏳ MANUAL REQUIRED

After adding the DNS route, reload the tunnel to apply changes:

**Option A: Restart via systemd (if running as service)**
```bash
sudo systemctl restart cloudflared
```

**Option B: Send SIGHUP to reload config**
```bash
# Find PID
ps aux | grep cloudflared | grep "config.yml"

# Send reload signal (replace <PID> with actual PID)
sudo kill -HUP <PID>
```

**Option C: Full restart (if above fails)**
```bash
# Stop
sudo killall cloudflared

# Start (check which config file is in use)
sudo cloudflared tunnel --config /etc/cloudflared/config.yml run
```

### **Step 4: Verify DNS Resolution**

After 1-2 minutes, verify DNS propagation:

```bash
# Check DNS record
dig sdlc.nqh.vn

# Should return Cloudflare CNAME:
# sdlc.nqh.vn. IN CNAME <tunnel-id>.cfargotunnel.com
```

### **Step 5: Test External Access**

```bash
# From external network (or use incognito browser)
curl -I https://sdlc.nqh.vn

# Expected:
# HTTP/2 200
# server: cloudflare
# content-type: text/html
```

---

## 🔍 **Troubleshooting**

### **Issue 1: DNS Route Not Found**
**Symptom**: `curl https://sdlc.nqh.vn` returns "DNS_PROBE_FINISHED_NXDOMAIN"

**Solution**:
1. Verify DNS route added in Cloudflare Dashboard
2. Wait 2-5 minutes for DNS propagation
3. Clear browser DNS cache: `chrome://net-internals/#dns`

### **Issue 2: 502 Bad Gateway**
**Symptom**: `curl https://sdlc.nqh.vn` returns "502 Bad Gateway"

**Diagnosis**:
```bash
# Check if frontend is running
curl http://localhost:8311/health
# Expected: "healthy"

# Check cloudflared logs
sudo journalctl -u cloudflared -f
# or
sudo tail -f /var/log/cloudflared.log
```

**Common Causes**:
- Frontend container stopped → Restart: `docker compose -f docker-compose.beta.yml --env-file .env.beta up -d frontend`
- Wrong port in ingress rule → Verify config shows `8311` not `8310`
- Tunnel daemon not reloaded → Restart tunnel (Step 3)

### **Issue 3: Authentication Error**
**Symptom**: `cloudflared tunnel route dns` fails with "Authentication error"

**Solution**: Use Cloudflare Dashboard (Option A in Step 2) instead of CLI

### **Issue 4: CORS Error**
**Symptom**: Frontend loads but API calls fail with CORS error

**Diagnosis**:
```bash
# Check backend ALLOWED_ORIGINS
docker exec sdlc-beta-backend env | grep ALLOWED_ORIGINS
# Expected: ALLOWED_ORIGINS=https://sdlc.nqh.vn,http://localhost:8311
```

**Solution**: If missing, update `.env.beta` and restart backend:
```bash
echo "ALLOWED_ORIGINS=https://sdlc.nqh.vn,http://localhost:8311" >> .env.beta
docker compose -f docker-compose.beta.yml --env-file .env.beta restart backend
```

---

## 🧪 **Quick Health Check**

Run this script to verify everything is ready:

```bash
#!/bin/bash
echo "=== SDLC Beta Environment Health Check ==="

# 1. Frontend local access
echo -n "Frontend (localhost:8311): "
curl -sf http://localhost:8311/health > /dev/null && echo "✅ OK" || echo "❌ FAIL"

# 2. Backend local access
echo -n "Backend (localhost:8001): "
curl -sf http://localhost:8001/health > /dev/null && echo "✅ OK" || echo "❌ FAIL"

# 3. Cloudflare config
echo -n "Cloudflare ingress rule: "
grep -q "sdlc.nqh.vn" ~/.cloudflared/config.yml && echo "✅ OK" || echo "❌ MISSING"

# 4. DNS resolution
echo -n "DNS resolution: "
dig +short sdlc.nqh.vn | grep -q "cfargotunnel.com" && echo "✅ OK" || echo "⏳ PENDING"

# 5. External access (requires DNS setup)
echo -n "External HTTPS: "
curl -sf -I https://sdlc.nqh.vn > /dev/null 2>&1 && echo "✅ OK" || echo "⏳ PENDING (Run after DNS setup)"

echo ""
echo "Next steps:"
echo "1. Add DNS route via Cloudflare Dashboard (see Step 2)"
echo "2. Reload tunnel daemon (see Step 3)"
echo "3. Wait 2-5 minutes for DNS propagation"
echo "4. Test: curl -I https://sdlc.nqh.vn"
```

---

## 📊 **Current Infrastructure**

### **Running Tunnels**
```
ID: 4eb54608-b582-450e-b081-bd6bcc8f59f9
Name: my-tunnel
Active Connections: 4 (1xsin06, 2xsin11, 1xsin21)
```

### **Existing Routes**
| Hostname | Service | Purpose |
|----------|---------|---------|
| chat.nqh.vn | http://localhost:3000 | Open WebUI |
| sd.nqh.vn | http://localhost:8188 | Stable Diffusion |
| mysql-master.nqh.vn | tcp://localhost:13306 | MySQL Data Warehouse |
| mysql-read1.nqh.vn | tcp://localhost:13307 | MySQL Read Replica 1 |
| mysql-read2.nqh.vn | tcp://localhost:13308 | MySQL Read Replica 2 |
| **sdlc.nqh.vn** | **http://localhost:8311** | **SDLC Orchestrator Beta** ⭐ |

---

## 🔐 **Security Considerations**

### **Current Security Posture**
✅ **HTTPS**: Cloudflare provides automatic TLS encryption
✅ **Origin Certificates**: Cloudflare validates tunnel connections
✅ **SECRET_KEY**: Beta uses production-grade 64-char secret
✅ **CORS**: Restricted to `https://sdlc.nqh.vn` only
✅ **JWT**: 15-minute expiry with secure refresh tokens

### **Recommended Additional Security** (Post-Launch)
- [ ] Enable Cloudflare Access for authentication layer
- [ ] Add IP whitelisting for pilot team members
- [ ] Enable WAF rules for common attack vectors
- [ ] Set up rate limiting (100 req/min per IP)
- [ ] Configure Cloudflare Page Rules for caching static assets

---

## 📝 **Notes for Operations Team**

1. **Monitoring**: Cloudflare tunnel metrics available at https://dash.cloudflare.com
2. **Logs**: Cloudflared logs available via `journalctl -u cloudflared`
3. **Downtime**: If tunnel goes down, frontend will still be accessible via `http://localhost:8311` for local testing
4. **Scaling**: Cloudflare tunnel supports automatic load balancing across multiple tunnel instances
5. **Cost**: Cloudflare tunnel is free for up to 50 concurrent connections

---

## ✅ **Completion Checklist**

- [x] Beta environment deployed (9/9 services)
- [x] Ingress rule added to config
- [ ] DNS route configured in Cloudflare Dashboard
- [ ] Tunnel daemon reloaded
- [ ] DNS propagation verified (`dig sdlc.nqh.vn`)
- [ ] External HTTPS access tested (`curl -I https://sdlc.nqh.vn`)
- [ ] Pilot team notified with access URL

---

**Last Updated**: 2025-12-16 (Sprint 33 Day 3)
**Status**: ⏳ AWAITING MANUAL DNS SETUP
**Owner**: DevOps Team
**Next Action**: Add DNS route via Cloudflare Dashboard → Reload tunnel daemon → Test external access
