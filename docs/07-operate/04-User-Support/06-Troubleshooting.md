# Troubleshooting Guide
**Common Issues and Solutions**  
**Last Updated**: December 20, 2025

---

## Quick Troubleshooting

### I Can't Log In

**Symptoms**: Login fails, incorrect credentials, or error message

**Solutions**:

1. **Check Credentials**
   ```
   - Verify username/email is correct
   - Check CAPS LOCK is off
   - Ensure password is correct
   - Try "Forgot Password" if needed
   ```

2. **Clear Browser Cache**
   ```
   Chrome: Ctrl+Shift+Del → Clear cache
   Firefox: Ctrl+Shift+Del → Clear cache
   Safari: Cmd+Option+E
   ```

3. **Try Different Browser**
   - Test with Chrome, Firefox, or Edge
   - Disable browser extensions
   - Try incognito/private mode

4. **Check MFA**
   - Ensure authenticator app is synced
   - Try backup codes if available
   - Contact admin to reset MFA

5. **Account Status**
   - Verify account is active (not disabled)
   - Contact admin to check account status

---

### Page Not Loading / 500 Error

**Symptoms**: White screen, 500 Internal Server Error, or loading forever

**Solutions**:

1. **Refresh the Page**
   ```
   - Press F5 or Ctrl+R (Cmd+R on Mac)
   - Hard refresh: Ctrl+Shift+R (Cmd+Shift+R on Mac)
   ```

2. **Check Network Connection**
   ```
   - Verify internet connectivity
   - Check if https://sdlc.nhatquangholding.com is accessible
   - Try ping or traceroute
   ```

3. **Clear Browser Data**
   ```
   - Clear cache and cookies
   - Clear local storage
   - Restart browser
   ```

4. **Check Backend Status**
   ```
   # For admins with server access
   docker ps | grep backend
   docker logs backend -f
   ```

5. **Contact Support**
   - If persistent, report to admin
   - Include: browser, time, error message
   - Screenshot if possible

---

### Upload Failing

**Symptoms**: File upload fails, error message, or stuck at uploading

**Solutions**:

1. **Check File Size**
   ```
   Maximum file size: 50MB
   - Compress large files
   - Split into smaller files
   - Use external link instead
   ```

2. **Check File Type**
   ```
   Supported formats:
   ✅ PDF, DOCX, XLSX, PPTX
   ✅ PNG, JPG, SVG
   ✅ TXT, MD, JSON, YAML
   ❌ EXE, DMG, APP (executables)
   ```

3. **Network Timeout**
   ```
   - Check internet stability
   - Try smaller file first
   - Upload during off-peak hours
   ```

4. **Browser Issues**
   ```
   - Try different browser
   - Disable ad blockers
   - Check JavaScript is enabled
   ```

5. **Storage Quota**
   ```
   - Project may have reached storage limit
   - Contact admin to increase quota
   ```

---

### Bulk Delete Not Working (FIXED)

**Symptoms**: Bulk delete returns 422 error

**Status**: ✅ **FIXED** on December 20, 2025

**What Was Wrong**:
- FastAPI was matching `/users/bulk` against `/users/{user_id}` route first
- "bulk" failed UUID validation
- Route ordering issue in backend

**Solution Applied**:
- Reordered routes: bulk delete now before single delete
- Added validation error handler
- Added explicit Content-Type header in frontend

**If Still Having Issues**:
1. **Clear Browser Cache**
   ```
   Ctrl+Shift+Del → Clear cache
   Hard refresh: Ctrl+Shift+R
   ```

2. **Check Production Deployment**
   ```
   # For admins
   docker logs backend | grep "BULK DELETE"
   # Should see: "=== BULK DELETE ENDPOINT CALLED ==="
   ```

3. **Verify Backend Version**
   ```
   GET /api/health
   Should show commit: e3215ec or later
   ```

4. **Contact Support**
   - Include: user IDs being deleted, error message
   - Check browser console (F12 → Console)

**Reference**: See [hotfix documentation](../../hotfixes/2025-12-20-bulk-delete-422-fix.md)

---

### Gate Approval Stuck

**Symptoms**: Gate shows "In Review" but no progress

**Solutions**:

1. **Check Reviewer Assignments**
   ```
   - Verify reviewers are assigned
   - Ensure reviewers have been notified
   - Check reviewer email/notifications
   ```

2. **Evidence Completeness**
   ```
   - All required evidence submitted?
   - AI Council flagged any issues?
   - Missing artifacts?
   ```

3. **Notify Reviewers**
   ```
   - Send reminder via platform
   - Contact reviewers directly
   - Check reviewer availability
   ```

4. **Check Permissions**
   ```
   - Reviewers have "Reviewer" or "Admin" role?
   - Project access granted?
   ```

5. **Escalate**
   ```
   - Contact project lead
   - Escalate to admin if urgent
   - Consider gate waiver if justified
   ```

---

### AI Council Not Responding

**Symptoms**: AI Council review not appearing or taking too long

**Solutions**:

1. **Wait for Processing**
   ```
   Normal processing time: 30-60 seconds
   Large projects: up to 5 minutes
   ```

2. **Check Evidence Quality**
   ```
   - Evidence properly formatted?
   - Files readable (not corrupted)?
   - External links accessible?
   ```

3. **Retry AI Review**
   ```
   - Refresh page
   - Resubmit evidence
   - Click "Request AI Review" again
   ```

4. **Backend Issues**
   ```
   # For admins
   docker logs backend | grep "AI Council"
   Check Ollama service is running
   ```

5. **Fallback to Manual Review**
   ```
   - Proceed with human reviewer
   - AI Council optional, not required
   ```

---

### Permission Denied

**Symptoms**: "You don't have permission" or 403 Forbidden

**Solutions**:

1. **Check Your Role**
   ```
   Profile → View Role
   Required roles:
   - Create project: Developer+
   - Approve gate: Reviewer+
   - Admin panel: Admin only
   ```

2. **Project Access**
   ```
   - Are you a team member?
   - Request access from project lead
   - Ask admin to add you
   ```

3. **Session Expired**
   ```
   - Logout and login again
   - Clear cookies
   - Check token expiration
   ```

4. **Contact Admin**
   ```
   If you should have access:
   - Request role upgrade
   - Verify project membership
   - Check access control rules
   ```

---

### Report Generation Failed

**Symptoms**: Report export fails or shows error

**Solutions**:

1. **Check Report Size**
   ```
   Large projects may timeout
   - Filter by date range
   - Generate smaller reports
   - Try different format (CSV vs PDF)
   ```

2. **Browser Issues**
   ```
   - Disable pop-up blockers
   - Allow downloads from site
   - Try different browser
   ```

3. **Backend Timeout**
   ```
   # For admins
   Increase timeout in docker-compose.yml:
   environment:
     REPORT_TIMEOUT: 300
   ```

4. **Try Different Format**
   ```
   If PDF fails: Try Excel
   If Excel fails: Try CSV
   If all fail: Contact support
   ```

---

### Search Not Working

**Symptoms**: Search returns no results or wrong results

**Solutions**:

1. **Check Search Syntax**
   ```
   ✅ Simple terms: "architecture"
   ✅ Quoted phrases: "system design"
   ✅ Wildcards: "arch*"
   ❌ Special chars: "@#$%"
   ```

2. **Filters Applied**
   ```
   - Clear all filters
   - Try broader search terms
   - Remove date restrictions
   ```

3. **Index Update**
   ```
   Search index updates every hour
   Recent uploads may not appear immediately
   Wait 1 hour and try again
   ```

4. **Backend Issue**
   ```
   # For admins
   Check Elasticsearch service:
   docker ps | grep search
   docker logs elasticsearch
   ```

---

### Integration Not Connecting

**Symptoms**: GitHub/Jira/Slack integration fails

**Solutions**:

1. **Check Credentials**
   ```
   - API tokens still valid?
   - Permissions granted?
   - Organization access?
   ```

2. **Reconfigure Integration**
   ```
   Settings → Integrations
   - Remove integration
   - Add again with fresh credentials
   - Test connection
   ```

3. **Network Issues**
   ```
   - Firewall blocking requests?
   - Proxy configuration needed?
   - VPN interfering?
   ```

4. **Service Status**
   ```
   Check if external service is down:
   - GitHub: https://www.githubstatus.com
   - Jira: https://status.atlassian.com
   - Slack: https://status.slack.com
   ```

---

### Performance Issues

**Symptoms**: Slow loading, laggy interface, timeouts

**Solutions**:

1. **Browser Optimization**
   ```
   - Close unused tabs
   - Disable heavy extensions
   - Clear cache regularly
   - Use Chrome/Firefox (best support)
   ```

2. **Network Issues**
   ```
   - Check internet speed
   - Use wired connection if possible
   - Avoid peak hours
   ```

3. **Large Projects**
   ```
   - Filter data by date range
   - Paginate large lists
   - Use search instead of browsing
   ```

4. **Server Load**
   ```
   # For admins
   Check server resources:
   docker stats
   Monitor CPU, RAM, disk usage
   Scale if necessary
   ```

---

## Error Code Reference

### Common HTTP Errors

| Code | Meaning | Common Cause | Solution |
|------|---------|--------------|----------|
| 400 | Bad Request | Invalid input | Check form fields |
| 401 | Unauthorized | Not logged in | Login again |
| 403 | Forbidden | No permission | Check role/access |
| 404 | Not Found | Resource missing | Check URL |
| 422 | Unprocessable | Validation failed | Check input format |
| 500 | Server Error | Backend issue | Contact admin |
| 502 | Bad Gateway | Service down | Wait/contact admin |
| 503 | Service Unavailable | Maintenance | Check status page |

### Platform-Specific Errors

**GATE_NOT_READY**
```
Cause: Prerequisites not met
Solution: Complete previous gate first
```

**EVIDENCE_INCOMPLETE**
```
Cause: Missing required artifacts
Solution: Upload all required evidence
```

**INVALID_TIER**
```
Cause: Wrong project classification
Solution: Request tier change from admin
```

**QUOTA_EXCEEDED**
```
Cause: Storage limit reached
Solution: Clean up old files or request increase
```

---

## Advanced Troubleshooting (For Admins)

### Backend Debugging

**Check Logs**
```bash
# All backend logs
docker logs backend -f

# Filter for errors
docker logs backend 2>&1 | grep ERROR

# Specific user/project
docker logs backend 2>&1 | grep "user_id=123"
```

**Database Access**
```bash
# Connect to PostgreSQL
docker exec -it postgres psql -U sdlc

# Check user count
SELECT COUNT(*) FROM users;

# Check gate status
SELECT project_id, gate_id, status FROM gates;
```

**Health Check**
```bash
# API health
curl https://sdlc.nhatquangholding.com/api/health

# Database connection
docker exec backend python -c "from app.db import get_db; next(get_db())"
```

### Frontend Debugging

**Browser Console**
```javascript
// Open DevTools (F12)
// Check Console for errors
// Network tab for API calls
// Application tab for localStorage
```

**Clear Everything**
```javascript
// In browser console
localStorage.clear();
sessionStorage.clear();
location.reload();
```

---

## Getting Help

### Self-Service Steps
1. Check this troubleshooting guide
2. Search [FAQ](07-FAQ.md)
3. Review [Common Tasks](05-Common-Tasks.md)
4. Try [Getting Started](01-Getting-Started.md) if new

### Support Channels
See [Support Channels](09-Support-Channels.md) for:
- Help desk
- Email support
- Emergency contacts
- Community forums

### When Reporting Issues

**Include**:
- What you were trying to do
- What happened instead
- Error messages (exact text)
- Screenshots
- Browser and version
- Time issue occurred
- Steps to reproduce

**Example Good Report**:
```
Issue: Bulk delete failing
Time: 2025-12-20 14:30 UTC
Browser: Chrome 120.0.6099.129
Steps:
1. Went to Admin Panel → Users
2. Selected 3 users
3. Clicked "Delete Selected"
4. Got 422 error
Error: "Unprocessable Entity"
Screenshot: attached
Console log: attached
```

---

## Known Issues

### Current Known Issues
✅ **Bulk Delete 422 Error**: FIXED (Dec 20, 2025)
⚪ **Large Report Export**: May timeout (use filters)
⚪ **Safari Mobile**: Some UI glitches (use Chrome mobile)

### Planned Fixes
- Mobile responsive improvements
- Faster report generation
- Enhanced search performance

---

**Framework**: SDLC 6.1.0
**Platform**: SDLC Orchestrator v1.2.0  
**Last Updated**: December 20, 2025
