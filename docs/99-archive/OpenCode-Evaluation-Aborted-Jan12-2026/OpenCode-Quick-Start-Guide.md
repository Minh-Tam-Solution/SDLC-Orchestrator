# OpenCode Quick Start Guide - Backend Lead

**Date**: January 12, 2026
**Owner**: Backend Lead
**OpenCode Location**: `/home/nqh/shared/opencode`
**Reference**: [ISSUE-OpenCode-Level0-Week1-2.md](./ISSUE-OpenCode-Level0-Week1-2.md)

---

## ✅ Completed

- [x] Repository cloned to `/home/nqh/shared/opencode`

---

## 📋 Next Steps (In Order)

### Step 1: Review OpenCode Documentation (15-30 minutes)

```bash
cd /home/nqh/shared/opencode

# Read main documentation
cat README.md

# Check available documentation
ls -la docs/ 2>/dev/null || echo "No docs folder found"

# Check for Docker setup
ls -la docker* Dockerfile* docker-compose* 2>/dev/null

# Check for server mode documentation
find . -name "*server*" -o -name "*api*" 2>/dev/null | head -20

# Review repository structure
tree -L 2 -I 'node_modules|__pycache__|.git' || ls -la
```

**What to Look For**:
- ✅ Server Mode documentation (how to run as API server)
- ✅ Docker/Docker Compose setup files
- ✅ API endpoint documentation (health check, code generation)
- ✅ Environment variables needed
- ✅ Port configuration (default: 8080?)

---

### Step 2: Check OpenCode Architecture (10 minutes)

```bash
cd /home/nqh/shared/opencode

# Check package.json or requirements.txt
cat package.json 2>/dev/null || cat requirements.txt 2>/dev/null || cat pyproject.toml 2>/dev/null

# Check for main entry points
ls -la src/ lib/ app/ main.py server.py index.js 2>/dev/null

# Look for configuration files
ls -la .env.example config.* settings.* 2>/dev/null
```

**Key Questions**:
- What language/framework? (Python, Node.js, Go?)
- What are the dependencies?
- How to configure server mode?
- What ports does it use?

---

### Step 3: Setup Docker Environment (Target: Jan 15, 2026)

**Option A: If Docker Compose Exists**
```bash
cd /home/nqh/shared/opencode

# Review docker-compose.yml
cat docker-compose.yml

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f opencode

# Verify health
curl http://localhost:8080/health
```

**Option B: If Dockerfile Only**
```bash
cd /home/nqh/shared/opencode

# Review Dockerfile
cat Dockerfile

# Build image
docker build -t opencode-local:latest .

# Run in server mode
docker run -d \
  --name opencode-server \
  -p 8080:8080 \
  -e OPENCODE_MODE=server \
  opencode-local:latest

# Check logs
docker logs -f opencode-server

# Verify health
curl http://localhost:8080/health
```

**Option C: If No Docker Files (Need to Build)**
```bash
cd /home/nqh/shared/opencode

# Check if there's a build/run script
ls -la scripts/ bin/ *.sh

# Check README for setup instructions
grep -i "install\|setup\|getting started" README.md -A 20

# Manual setup (example for Python)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python server.py --port 8080
```

---

### Step 4: Verify Health Endpoint (5 minutes)

```bash
# Test health endpoint
curl http://localhost:8080/health

# Expected response (example):
# {"status": "ok", "version": "x.y.z"}

# If different port, try:
curl http://localhost:3000/health
curl http://localhost:5000/health
curl http://localhost:8000/health

# Check what ports are listening
docker ps
netstat -tulpn | grep LISTEN
```

---

### Step 5: Test Basic API Call (Target: Jan 17, 2026)

**Prepare Test Spec**:
```bash
cd /home/nqh/shared/opencode

# Create test specification
cat > task1-spec.json <<'EOF'
{
  "task": "Create a simple Python function that adds two numbers",
  "workflow": "feature",
  "language": "python"
}
EOF
```

**Make API Call**:
```bash
# Test basic code generation
curl -X POST http://localhost:8080/api/v1/feature \
  -H "Content-Type: application/json" \
  -d @task1-spec.json \
  | jq '.' > task1-output.json

# Check output
cat task1-output.json
```

**Extract Generated Code**:
```bash
# If response contains code field
cat task1-output.json | jq -r '.code' > task1-generated.py

# OR if multi-file response
cat task1-output.json | jq -r '.files'
```

---

### Step 6: Run FastAPI CRUD Sample (Target: Jan 17, 2026)

**Create Full CRUD Spec**:
```bash
cat > task1-crud-spec.json <<'EOF'
{
  "task": "Create a FastAPI endpoint for user CRUD operations with the following requirements:\n- POST /users - Create new user (accepts: name, email)\n- GET /users/{user_id} - Get user by ID\n- PUT /users/{user_id} - Update user\n- DELETE /users/{user_id} - Delete user\n- Use Pydantic models for validation\n- Return proper HTTP status codes (201, 200, 404)\n- No database required, use in-memory list",
  "workflow": "feature",
  "language": "python",
  "framework": "fastapi"
}
EOF
```

**Execute Generation**:
```bash
# Generate code
time curl -X POST http://localhost:8080/api/v1/feature \
  -H "Content-Type: application/json" \
  -d @task1-crud-spec.json \
  | jq '.' > task1-crud-output.json

# Note: Record generation time (for latency assessment)
```

**Test Generated Code**:
```bash
# Extract code
cat task1-crud-output.json | jq -r '.code' > task1-crud-generated.py

# Install dependencies
pip install fastapi uvicorn pydantic

# Run FastAPI server
uvicorn task1-crud-generated:app --reload --port 8000

# In another terminal, test endpoints:
# Create user
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com"}'

# Get user
curl http://localhost:8000/users/1

# Expected: 200 OK with user data
```

---

## 🔍 Quality Assessment Checklist

**Syntax (Gate 1)**:
- [ ] Does code run without syntax errors?
- [ ] Are imports correct?
- [ ] Is code properly formatted (PEP 8)?

**Functionality (Gate 2)**:
- [ ] POST /users works (creates user, returns 201)
- [ ] GET /users/{user_id} works (returns 200 or 404)
- [ ] PUT /users/{user_id} works (updates user)
- [ ] DELETE /users/{user_id} works (removes user)

**Security (Gate 3)**:
- [ ] Input validation present (Pydantic models)
- [ ] No SQL injection risk (in-memory list)
- [ ] No XSS vulnerabilities
- [ ] Proper error handling (try/except)

**Code Quality (Gate 4)**:
- [ ] Code is readable and maintainable
- [ ] Variable/function names are clear
- [ ] Follows FastAPI best practices
- [ ] Docstrings present (if applicable)

**Performance**:
- [ ] Generation time < 30s (target)
- [ ] API response time acceptable

---

## 📊 Week 1-2 Report Template

Create: `/home/nqh/shared/opencode/evaluation/Week1-2-Report.md`

```markdown
# OpenCode Level 0 - Week 1-2 Report

**Date**: January 17, 2026
**Evaluator**: [Backend Lead Name]
**Status**: Week 1-2 Complete

## Setup Results

| Item | Status | Notes |
|------|--------|-------|
| Repository cloned | ✅ | `/home/nqh/shared/opencode` |
| Documentation review | ✅/❌ | Version: X.Y.Z |
| Docker setup | ✅/❌ | Port: 8080, Mode: Server |
| Health check | ✅/❌ | Response time: Xms |
| API test | ✅/❌ | Endpoint: /api/v1/feature |

## Sample Task 1: Simple CRUD API

| Metric | Result | Notes |
|--------|--------|-------|
| **Generation** |
| Latency | Xs | Target: <30s |
| Status | ✅/❌ | Success / Error |
| **Quality** |
| Syntax | ✅/❌ | Runs without errors? |
| Functionality | X/4 endpoints | POST, GET, PUT, DELETE |
| Security | ✅/❌ | Issues found? |
| Code Quality | X/5 | Readability, maintainability |
| **4-Gate Proxy** |
| Syntax (ast.parse) | ✅/❌ | Python AST validates? |
| Security (manual) | ✅/❌ | No obvious vulnerabilities? |
| Tests (manual) | ✅/❌ | Endpoints work as expected? |

## Observations

**Strengths**:
- [List what worked well]

**Weaknesses**:
- [List issues encountered]

**Blockers**:
- [List any blockers]

## Next Steps (Week 3-6)

- [ ] Run Task 2: React component with state
- [ ] Run Task 3: Multi-file auth flow
- [ ] Compare OpenCode vs manual coding time
- [ ] Update monitoring spreadsheet (week 2 data)

## Recommendation

**Preliminary Assessment**: [PROMISING / NEEDS_IMPROVEMENT / BLOCKED]

**Rationale**: [1-2 sentences]
```

---

## 🚨 Common Issues & Solutions

### Issue 1: Docker Build Fails
**Solution**:
```bash
# Check Docker daemon
docker info

# Check Dockerfile syntax
docker build --no-cache -t opencode-local:latest .

# Review build logs carefully
docker build -t opencode-local:latest . 2>&1 | tee build.log
```

### Issue 2: Port Already in Use
**Solution**:
```bash
# Find process using port 8080
lsof -i :8080

# Use different port
docker run -d -p 8081:8080 opencode-local:latest
curl http://localhost:8081/health
```

### Issue 3: Health Endpoint Not Found (404)
**Solution**:
```bash
# Try different health check paths
curl http://localhost:8080/
curl http://localhost:8080/health
curl http://localhost:8080/healthz
curl http://localhost:8080/status
curl http://localhost:8080/api/health

# Check container logs
docker logs opencode-server
```

### Issue 4: API Endpoint Not Documented
**Solution**:
```bash
# Check for OpenAPI/Swagger docs
curl http://localhost:8080/docs
curl http://localhost:8080/swagger
curl http://localhost:8080/api-docs

# Inspect source code
grep -r "route\|endpoint\|@app" /home/nqh/shared/opencode/src/
```

### Issue 5: Generation Takes Too Long (>60s)
**Solution**:
- Check container resource limits
- Review OpenCode logs for errors
- Try simpler task first
- Check network connectivity (if calling external APIs)

---

## 📞 Support

**Questions**:
- Slack: `#sdlc-orchestrator-dev`
- Architect: Technical architecture questions
- PM/PO: Process/timeline questions

**Documentation**:
- [ISSUE-OpenCode-Level0-Week1-2.md](./ISSUE-OpenCode-Level0-Week1-2.md)
- [ADR-026-OpenCode-Integration-Strategy.md](../../02-design/01-ADRs/ADR-026-OpenCode-Integration-Strategy.md)

---

## ✅ Success Criteria (Week 1-2)

- [x] Repository cloned: `/home/nqh/shared/opencode`
- [ ] OpenCode Docker container running locally
- [ ] Health endpoint responds with 200 OK
- [ ] First sample task executed (FastAPI CRUD)
- [ ] Quality assessment documented
- [ ] Week 1-2 report completed

**Checkpoint**: Friday, Jan 17, 2026 @ 3pm with CTO

---

**Last Updated**: January 12, 2026
**Next Review**: January 17, 2026 (Friday 3pm)
