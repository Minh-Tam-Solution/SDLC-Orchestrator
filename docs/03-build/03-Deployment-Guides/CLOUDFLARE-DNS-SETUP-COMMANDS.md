# Cloudflare DNS Setup - Ready-to-Execute Commands
**Created**: 2025-12-16 (Sprint 33 Day 3)
**Estimated Time**: 10-15 minutes
**Prerequisites**: Cloudflare Dashboard access + root/sudo access

---

## Step 1: Add DNS Routes via Cloudflare Dashboard (5 min)

### Option A: Via Cloudflare Dashboard (Recommended - No CLI auth needed)

1. **Login to Cloudflare**:
   - URL: https://dash.cloudflare.com
   - Account: NQH account with nqh.vn domain access

2. **Navigate to Tunnel Configuration**:
   ```
   Dashboard → Zero Trust → Networks → Tunnels → my-tunnel (4eb54608-b582-450e-b081-bd6bcc8f59f9)
   ```

3. **Add Frontend Hostname**:
   - Click **"Public Hostnames"** tab
   - Click **"Add a public hostname"** button
   - Fill in:
     - **Subdomain**: `sdlc`
     - **Domain**: `nqh.vn` (select from dropdown)
     - **Type**: `HTTP`
     - **URL**: `localhost:8310`
   - Click **"Save hostname"**

4. **Add Backend API Hostname**:
   - Click **"Add a public hostname"** button again
   - Fill in:
     - **Subdomain**: `sdlc-api`
     - **Domain**: `nqh.vn` (select from dropdown)
     - **Type**: `HTTP`
     - **URL**: `localhost:8300`
   - Click **"Save hostname"**

5. **Verify in Dashboard**:
   - You should now see 2 new entries in the Public Hostnames list:
     ```
     sdlc.nqh.vn → http://localhost:8310
     sdlc-api.nqh.vn → http://localhost:8300
     ```

### Option B: Via CLI (Requires Authentication)

If you have cloudflared authenticated and prefer CLI:

```bash
# Add frontend hostname
cloudflared tunnel route dns my-tunnel sdlc.nqh.vn

# Add backend API hostname
cloudflared tunnel route dns my-tunnel sdlc-api.nqh.vn
```

**Note**: If you get "Authentication error", use Option A (Dashboard) instead.

---

## Step 2: Reload Cloudflare Tunnel (2 min)

After adding DNS routes, reload the tunnel to apply the new ingress rules from config.yml.

### Check Current Tunnel Process

```bash
# Find cloudflared process
ps aux | grep cloudflared | grep -v grep

# Expected output (2 processes):
# candvg  4113  ... /usr/local/bin/cloudflared tunnel --config /home/candvg/.cloudflared/config.yml run
# root    4115  ... /usr/bin/cloudflared --no-autoupdate --config /etc/cloudflared/config.yml tunnel run
```

### Reload Tunnel (Choose ONE method)

**Method 1: Systemd Restart (Recommended if running as service)**
```bash
# Check if cloudflared is running as systemd service
sudo systemctl status cloudflared

# If yes, restart service
sudo systemctl restart cloudflared

# Verify service is active
sudo systemctl status cloudflared
# Expected: "Active: active (running)"
```

**Method 2: Send SIGHUP to Reload Config (No downtime)**
```bash
# Find PID of root process (the one using /etc/cloudflared/config.yml)
CLOUDFLARED_PID=$(ps aux | grep "/etc/cloudflared/config.yml" | grep -v grep | awk '{print $2}')

# Send reload signal (graceful reload, no downtime)
sudo kill -HUP $CLOUDFLARED_PID

# Verify process is still running
ps -p $CLOUDFLARED_PID
```

**Method 3: Full Restart (If above methods fail)**
```bash
# Stop all cloudflared processes
sudo killall cloudflared

# Wait 5 seconds
sleep 5

# Start tunnel with system config
sudo cloudflared tunnel --config /etc/cloudflared/config.yml run &

# Or if it's a systemd service:
sudo systemctl start cloudflared
```

### Verify Tunnel is Running

```bash
# Check process
ps aux | grep cloudflared | grep -v grep

# Check tunnel connections
cloudflared tunnel info my-tunnel

# Expected output shows active connections:
# Connections:
#   1xsin06 (registered)
#   2xsin11 (registered)
#   1xsin21 (registered)
```

---

## Step 3: Verify DNS Propagation (2-5 min)

Wait 2-5 minutes for DNS to propagate, then test:

### Check DNS Resolution

```bash
# Frontend DNS
dig sdlc.nqh.vn

# Expected output includes:
# sdlc.nqh.vn.  300  IN  CNAME  4eb54608-b582-450e-b081-bd6bcc8f59f9.cfargotunnel.com.

# Backend API DNS
dig sdlc-api.nqh.vn

# Expected output includes:
# sdlc-api.nqh.vn.  300  IN  CNAME  4eb54608-b582-450e-b081-bd6bcc8f59f9.cfargotunnel.com.
```

### Test External HTTPS Access

```bash
# Test frontend
curl -I https://sdlc.nqh.vn

# Expected output:
# HTTP/2 200
# server: cloudflare
# content-type: text/html
# ...

# Test backend API
curl -I https://sdlc-api.nqh.vn/health

# Expected output:
# HTTP/2 200
# server: cloudflare
# content-type: application/json
# ...

# Get full health response
curl -s https://sdlc-api.nqh.vn/health | python3 -m json.tool

# Expected output:
# {
#     "status": "healthy",
#     "version": "1.1.0",
#     "service": "sdlc-orchestrator-backend"
# }
```

---

## Step 4: Verify CORS & Frontend Access (3 min)

### Test Frontend in Browser

1. Open browser (incognito mode to avoid cache): https://sdlc.nqh.vn
2. Open Developer Console (F12)
3. Check for errors:
   - ✅ No CORS errors
   - ✅ No CSP violations
   - ✅ Network tab shows API calls to https://sdlc-api.nqh.vn

### Test CORS from Command Line

```bash
# Test CORS preflight (OPTIONS request from allowed origin)
curl -I -X OPTIONS https://sdlc-api.nqh.vn/health \
  -H "Origin: https://sdlc.nqh.vn" \
  -H "Access-Control-Request-Method: GET"

# Expected headers in response:
# Access-Control-Allow-Origin: https://sdlc.nqh.vn
# Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
# Access-Control-Allow-Headers: Content-Type, Authorization

# Test CORS from disallowed origin (should fail)
curl -I https://sdlc-api.nqh.vn/health \
  -H "Origin: https://evil.com"

# Expected: No Access-Control-Allow-Origin header or 403
```

---

## Troubleshooting

### Issue 1: DNS Not Resolving After 5 Minutes

**Symptom**: `dig sdlc.nqh.vn` returns NXDOMAIN

**Solutions**:
1. Verify DNS routes added in Cloudflare Dashboard (Step 1)
2. Check tunnel is running: `ps aux | grep cloudflared`
3. Flush DNS cache:
   ```bash
   # Linux
   sudo systemd-resolve --flush-caches

   # macOS
   sudo dscacheutil -flushcache
   ```
4. Try from different network or use Cloudflare DNS: `dig @1.1.1.1 sdlc.nqh.vn`

### Issue 2: 502 Bad Gateway

**Symptom**: `curl https://sdlc.nqh.vn` returns 502 Bad Gateway

**Diagnosis**:
```bash
# Check if frontend is running
curl http://localhost:8310/health
# Expected: "healthy"

# Check backend
curl http://localhost:8300/health
# Expected: {"status":"healthy",...}

# Check tunnel logs
sudo journalctl -u cloudflared -f --since "5 minutes ago"
# Look for connection errors
```

**Common Causes**:
- Frontend/backend container stopped → `docker compose ps`
- Wrong port in config.yml → Verify shows 8310 and 8300
- Tunnel not reloaded → Restart tunnel (Step 2)

### Issue 3: CORS Errors in Browser

**Symptom**: Browser console shows "CORS policy blocked"

**Diagnosis**:
```bash
# Check backend ALLOWED_ORIGINS
docker exec sdlc-backend env | grep ALLOWED_ORIGINS

# Expected:
# ALLOWED_ORIGINS=https://sdlc.nqh.vn,http://localhost:8310,...
```

**Solution**:
```bash
# If missing, backend needs restart to pick up env change
docker compose restart backend

# Wait 30s for health check
sleep 30

# Verify
curl http://localhost:8300/health
```

### Issue 4: Tunnel Keeps Disconnecting

**Symptom**: `cloudflared tunnel info` shows no active connections

**Solutions**:
1. Check cloudflared logs:
   ```bash
   sudo journalctl -u cloudflared -f
   ```
2. Verify credentials file exists:
   ```bash
   ls -la /etc/cloudflared/*.json
   # or
   ls -la ~/.cloudflared/*.json
   ```
3. Test connectivity:
   ```bash
   cloudflared tunnel --config /etc/cloudflared/config.yml --loglevel debug run
   ```

---

## Success Checklist

After completing all steps, verify:

- [ ] DNS routes added in Cloudflare Dashboard (sdlc.nqh.vn + sdlc-api.nqh.vn)
- [ ] Tunnel daemon restarted/reloaded
- [ ] DNS resolution working (`dig sdlc.nqh.vn` returns CNAME)
- [ ] Frontend accessible (`curl -I https://sdlc.nqh.vn` returns 200)
- [ ] Backend API accessible (`curl -I https://sdlc-api.nqh.vn/health` returns 200)
- [ ] CORS working (browser console clean, no errors)
- [ ] CSP working (browser console clean, no violations)

---

## Quick Verification Script

Run this script after completing all steps:

```bash
#!/bin/bash
echo "=== CLOUDFLARE TUNNEL VERIFICATION ==="

# 1. DNS Resolution
echo -n "Frontend DNS (sdlc.nqh.vn): "
dig +short sdlc.nqh.vn | grep -q "cfargotunnel.com" && echo "✅ OK" || echo "❌ FAIL"

echo -n "Backend DNS (sdlc-api.nqh.vn): "
dig +short sdlc-api.nqh.vn | grep -q "cfargotunnel.com" && echo "✅ OK" || echo "❌ FAIL"

# 2. HTTPS Access
echo -n "Frontend HTTPS: "
curl -sf -I https://sdlc.nqh.vn > /dev/null 2>&1 && echo "✅ OK" || echo "❌ FAIL"

echo -n "Backend HTTPS: "
curl -sf -I https://sdlc-api.nqh.vn/health > /dev/null 2>&1 && echo "✅ OK" || echo "❌ FAIL"

# 3. Backend Health
echo "Backend Health Response:"
curl -s https://sdlc-api.nqh.vn/health | python3 -m json.tool

# 4. Tunnel Status
echo -e "\nTunnel Connections:"
cloudflared tunnel info my-tunnel | grep -A 5 "Connections:"

echo -e "\n=== VERIFICATION COMPLETE ==="
```

---

**Estimated Total Time**: 10-15 minutes
**Next Steps**: After verification passes, proceed to DB migration investigation and Day 4 monitoring setup.
