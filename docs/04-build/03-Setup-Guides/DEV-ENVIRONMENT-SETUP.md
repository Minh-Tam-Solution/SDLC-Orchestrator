# DEVELOPMENT ENVIRONMENT SETUP GUIDE
## Complete Setup for SDLC Orchestrator Development

**Version**: 1.0.0
**Last Updated**: December 2, 2025
**Target Audience**: Backend Developers, Frontend Developers, Full-Stack Developers
**Estimated Setup Time**: 30 minutes

**Framework**: SDLC 5.1.3 Complete Lifecycle (10 Stages)
**Current Stage**: Stage 04 (BUILD |

---

## 🎯 PREREQUISITES

### **System Requirements**

**Hardware**:
- CPU: 4+ cores (Intel i5/AMD Ryzen 5 or better)
- RAM: 8GB minimum, 16GB recommended
- Disk: 20GB free space (10GB for Docker images, 10GB for development)
- OS: macOS 12+, Ubuntu 20.04+, Windows 10+ (with WSL2)

**Software** (will install in this guide):
- Docker Desktop 24.0+ (or Docker Engine + Docker Compose)
- Python 3.11+
- Node.js 18+ (for frontend development)
- Git 2.30+
- VS Code 1.80+ (recommended IDE)

---

## 📦 STEP 1: INSTALL CORE TOOLS

### **1.1 Install Docker Desktop**

**macOS**:
```bash
# Install Docker Desktop via Homebrew
brew install --cask docker

# Start Docker Desktop
open -a Docker

# Verify installation
docker --version  # Should show: Docker version 24.0+
docker-compose --version  # Should show: Docker Compose version 2.20+
```

**Ubuntu**:
```bash
# Install Docker Engine
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get update
sudo apt-get install docker-compose-plugin

# Add user to docker group (no sudo needed)
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
docker compose version
```

**Windows (WSL2)**:
```powershell
# Download Docker Desktop for Windows from:
# https://www.docker.com/products/docker-desktop/

# Install and start Docker Desktop

# In WSL2 terminal, verify:
docker --version
docker compose version
```

---

### **1.2 Install Python 3.11+**

**macOS**:
```bash
# Install Python via Homebrew
brew install python@3.11

# Verify installation
python3.11 --version  # Should show: Python 3.11.x

# Create alias (optional, add to ~/.zshrc or ~/.bashrc)
alias python=python3.11
alias pip=pip3.11
```

**Ubuntu**:
```bash
# Install Python 3.11
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv python3.11-dev

# Install pip
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

# Verify installation
python3.11 --version
pip3.11 --version
```

**Windows (WSL2)**:
```bash
# Same as Ubuntu instructions above
sudo apt-get install python3.11 python3.11-venv python3.11-dev
```

---

### **1.3 Install Node.js 18+ (Frontend Development)**

**macOS**:
```bash
# Install Node.js via Homebrew
brew install node@18

# Verify installation
node --version  # Should show: v18.x.x
npm --version   # Should show: 9.x.x
```

**Ubuntu**:
```bash
# Install Node.js via NodeSource
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify installation
node --version
npm --version
```

---

### **1.4 Install Git**

**macOS**:
```bash
# Git comes pre-installed on macOS
# Verify installation
git --version  # Should show: git version 2.30+

# Configure Git (first time only)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

**Ubuntu**:
```bash
# Install Git
sudo apt-get install git

# Configure Git
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

---

### **1.5 Install VS Code (Recommended IDE)**

**macOS**:
```bash
# Install VS Code via Homebrew
brew install --cask visual-studio-code

# Launch VS Code
code .
```

**Ubuntu**:
```bash
# Download and install VS Code
wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
sudo install -o root -g root -m 644 packages.microsoft.gpg /etc/apt/trusted.gpg.d/
sudo sh -c 'echo "deb [arch=amd64] https://packages.microsoft.com/repos/code stable main" > /etc/apt/sources.list.d/vscode.list'
sudo apt-get update
sudo apt-get install code

# Launch VS Code
code .
```

---

## 📥 STEP 2: CLONE REPOSITORY

### **2.1 Clone Repository**

```bash
# Navigate to your projects directory
cd ~/Documents/Projects  # Or your preferred location

# Clone the repository
git clone https://github.com/your-org/SDLC-Orchestrator.git
cd SDLC-Orchestrator

# Verify you're on main branch
git branch  # Should show: * main
```

### **2.2 Verify Repository Structure**

```bash
# List directory structure
ls -la

# Should see:
# backend/          - FastAPI backend
# frontend/         - React frontend (Week 6-7)
# docs/             - Documentation
# docker-compose.yml - Development environment
# Makefile          - Common commands
# README.md         - Quick start guide
# .env.example      - Environment variables template
```

---

## 🔧 STEP 3: BACKEND SETUP

### **3.1 Create Python Virtual Environment**

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate

# Windows (WSL2):
source venv/bin/activate

# Verify activation (prompt should show (venv))
which python  # Should show: /path/to/backend/venv/bin/python
```

### **3.2 Install Python Dependencies**

```bash
# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Verify installation
pip list | grep fastapi  # Should show: fastapi 0.109+
pip list | grep sqlalchemy  # Should show: SQLAlchemy 2.0+
pip list | grep pytest  # Should show: pytest 7.4+
```

### **3.3 Install Pre-Commit Hooks**

```bash
# Install pre-commit
pip install pre-commit

# Install git hooks
pre-commit install

# Test pre-commit hooks
pre-commit run --all-files

# Should see:
# ruff.....................................................................Passed
# mypy.....................................................................Passed
# black....................................................................Passed
```

---

## 🐳 STEP 4: DOCKER ENVIRONMENT SETUP

### **4.1 Copy Environment Variables**

```bash
# Navigate to project root
cd ..  # Back to SDLC-Orchestrator/

# Copy .env.example to .env
cp .env.example .env

# Edit .env file (use your preferred editor)
nano .env  # or: code .env

# Update the following variables:
# DATABASE_URL=postgresql://sdlc_user:changeme_secure_password@postgres:5432/sdlc_db
# REDIS_URL=redis://redis:6379/0
# SECRET_KEY=<generate-a-secure-random-key-here>
# MINIO_ACCESS_KEY=minioadmin
# MINIO_SECRET_KEY=minioadmin
```

**Generate SECRET_KEY**:
```bash
# Generate a secure random key (32 bytes)
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Copy the output and paste into .env as SECRET_KEY
```

### **4.2 Start Docker Compose**

```bash
# Start all services (detached mode)
docker-compose up -d

# Verify all services are running
docker-compose ps

# Should see 8 services running:
# NAME                   STATUS              PORTS
# sdlc-backend           Up                  0.0.0.0:8000->8000/tcp
# sdlc-postgres          Up                  0.0.0.0:5432->5432/tcp
# sdlc-redis             Up                  0.0.0.0:6379->6379/tcp
# sdlc-minio             Up                  0.0.0.0:9000-9001->9000-9001/tcp
# sdlc-opa               Up                  0.0.0.0:8181->8181/tcp
# sdlc-grafana           Up                  0.0.0.0:3000->3000/tcp
# sdlc-prometheus        Up                  0.0.0.0:9090->9090/tcp
# sdlc-loki              Up                  0.0.0.0:3100->3100/tcp
```

### **4.3 View Service Logs**

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs backend

# Follow logs (real-time)
docker-compose logs -f backend

# View last 100 lines
docker-compose logs --tail=100 backend
```

### **4.4 Access Services**

Open your browser and verify the following services are accessible:

- **Backend API**: http://localhost:8000
- **API Documentation (Swagger)**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432 (use database client)
- **Redis**: localhost:6379 (use Redis client)
- **MinIO Console**: http://localhost:9001 (login: minioadmin/minioadmin)
- **Grafana**: http://localhost:3000 (login: admin/admin)
- **Prometheus**: http://localhost:9090
- **OPA**: http://localhost:8181

---

## 🗄️ STEP 5: DATABASE SETUP

### **5.1 Run Database Migrations**

```bash
# Navigate to backend directory
cd backend

# Activate virtual environment (if not already activated)
source venv/bin/activate

# Run Alembic migrations
python -m alembic upgrade head

# Verify migrations
python -m alembic current

# Should see: 001_initial_schema (head)
```

### **5.2 Seed Database (Optional)**

```bash
# Run seed script (creates system roles, default admin user)
python scripts/seed_database.py

# Verify seed data
docker exec -it sdlc-postgres psql -U sdlc_user -d sdlc_db -c "SELECT * FROM roles;"

# Should see 5 system roles:
# id | name  | description
# ---+-------+-------------
# 1  | Owner | Project owner
# 2  | Admin | Administrator
# 3  | PM    | Project manager
# 4  | Dev   | Developer
# 5  | QA    | Quality assurance
```

### **5.3 Verify Database Connection**

```bash
# Test database connection
python -c "from app.core.database import engine; print('Database connected!')"

# Should see: Database connected!
```

---

## 🧪 STEP 6: RUN TESTS

### **6.1 Run Unit Tests**

```bash
# Navigate to backend directory
cd backend

# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### **6.2 Run Specific Tests**

```bash
# Run authentication tests only
pytest tests/test_auth.py

# Run gates tests only
pytest tests/test_gates.py

# Run tests matching a pattern
pytest -k "test_login"

# Run tests with verbose output
pytest -v

# Run tests and stop on first failure
pytest -x
```

### **6.3 Run Performance Tests**

```bash
# Run benchmark tests
pytest tests/test_performance.py --benchmark-only

# Generate benchmark report
pytest tests/test_performance.py --benchmark-only --benchmark-autosave
```

---

## 🔍 STEP 7: VERIFY SETUP

### **7.1 Health Check**

```bash
# Check backend health
curl http://localhost:8000/health

# Should return:
# {"status":"healthy","version":"1.0.0","database":"connected","redis":"connected"}
```

### **7.2 Test Authentication**

```bash
# Register a new user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123!",
    "full_name": "Test User"
  }'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123!"
  }'

# Should return access_token and refresh_token
```

### **7.3 Access API Documentation**

Open http://localhost:8000/docs in your browser

**You should see**:
- Swagger UI with all API endpoints
- Authentication endpoints (register, login, profile, refresh, logout)
- Gates endpoints (create, get, update, delete, submit, approve)
- Try out endpoints interactively

---

## 🛠️ STEP 8: IDE CONFIGURATION (VS CODE)

### **8.1 Install VS Code Extensions**

Open VS Code and install the following extensions:

**Required Extensions**:
- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- Ruff (charliermarsh.ruff)
- Black Formatter (ms-python.black-formatter)
- mypy (ms-python.mypy-type-checker)

**Recommended Extensions**:
- Docker (ms-azuretools.vscode-docker)
- GitLens (eamodio.gitlens)
- REST Client (humao.rest-client)
- SQLTools (mtxr.sqltools)
- Thunder Client (rangav.vscode-thunder-client)

**Install via command line**:
```bash
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension charliermarsh.ruff
code --install-extension ms-python.black-formatter
code --install-extension ms-python.mypy-type-checker
code --install-extension ms-azuretools.vscode-docker
code --install-extension eamodio.gitlens
code --install-extension humao.rest-client
```

### **8.2 Configure VS Code Settings**

Create `.vscode/settings.json` in project root:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/backend/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length", "100"],
  "python.linting.mypyEnabled": true,
  "python.linting.mypyArgs": ["--strict"],
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.formatOnSave": true,
    "editor.tabSize": 4
  },
  "files.exclude": {
    "**/__pycache__": true,
    "**/.pytest_cache": true,
    "**/.mypy_cache": true,
    "**/.ruff_cache": true,
    "**/venv": true
  }
}
```

### **8.3 Configure VS Code Launch Configuration**

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--host",
        "0.0.0.0",
        "--port",
        "8000"
      ],
      "jinja": true,
      "justMyCode": false,
      "cwd": "${workspaceFolder}/backend",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/backend"
      }
    },
    {
      "name": "Python: Pytest",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": [
        "-v",
        "-s"
      ],
      "cwd": "${workspaceFolder}/backend",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/backend"
      }
    }
  ]
}
```

---

## 🚀 STEP 9: QUICK START COMMANDS (MAKEFILE)

### **9.1 Common Makefile Commands**

```bash
# Start development environment
make dev

# Stop development environment
make stop

# View logs
make logs

# Run tests
make test

# Run tests with coverage
make test-cov

# Run linting
make lint

# Run formatting
make format

# Run type checking
make typecheck

# Clean up (remove containers, volumes, caches)
make clean

# Full reset (clean + rebuild)
make reset
```

### **9.2 Daily Development Workflow**

```bash
# Morning: Start development environment
make dev

# Develop: Make code changes, write tests

# Before commit: Run quality checks
make lint      # Check code style
make typecheck # Check type hints
make test      # Run tests

# Commit: Git commit (pre-commit hooks run automatically)
git add .
git commit -m "feat: Add user authentication endpoint"

# Evening: Stop development environment
make stop
```

---

## 🐛 TROUBLESHOOTING

### **Issue 1: Docker Compose Won't Start**

**Symptoms**:
```bash
docker-compose up -d
# Error: Cannot start service postgres: driver failed programming external connectivity
```

**Solution**:
```bash
# Check if port 5432 is already in use
lsof -i :5432

# If PostgreSQL is running locally, stop it
# macOS:
brew services stop postgresql

# Ubuntu:
sudo systemctl stop postgresql

# Or change port in docker-compose.yml:
# ports:
#   - "5433:5432"  # Use 5433 instead of 5432
```

---

### **Issue 2: Database Migration Fails**

**Symptoms**:
```bash
python -m alembic upgrade head
# Error: Target database is not up to date
```

**Solution**:
```bash
# Check current migration version
python -m alembic current

# If stuck, reset migrations (WARNING: drops all data)
python -m alembic downgrade base
python -m alembic upgrade head

# Or reset database
docker-compose down -v  # Remove volumes
docker-compose up -d
python -m alembic upgrade head
```

---

### **Issue 3: Pre-Commit Hooks Failing**

**Symptoms**:
```bash
git commit -m "test"
# ruff.....................................................................Failed
```

**Solution**:
```bash
# Run ruff manually to see errors
ruff check backend/

# Fix errors automatically (if possible)
ruff check --fix backend/

# Run black to format code
black backend/

# Retry commit
git commit -m "test"
```

---

### **Issue 4: Python Virtual Environment Not Activating**

**Symptoms**:
```bash
source venv/bin/activate
# bash: venv/bin/activate: No such file or directory
```

**Solution**:
```bash
# Verify you're in the backend directory
pwd  # Should show: /path/to/SDLC-Orchestrator/backend

# If virtual environment doesn't exist, create it
python3.11 -m venv venv

# Activate
source venv/bin/activate

# Verify
which python  # Should show: /path/to/backend/venv/bin/python
```

---

### **Issue 5: Tests Failing with Database Connection Error**

**Symptoms**:
```bash
pytest
# Error: could not connect to server: Connection refused
```

**Solution**:
```bash
# Verify Docker containers are running
docker-compose ps

# If postgres is not running, start it
docker-compose up -d postgres

# Verify database connection
docker exec -it sdlc-postgres psql -U sdlc_user -d sdlc_db

# If connection works, retry tests
pytest
```

---

## ✅ SETUP VERIFICATION CHECKLIST

### **Environment Setup** ✅

- [ ] Docker Desktop installed and running
- [ ] Python 3.11+ installed
- [ ] Node.js 18+ installed (for frontend)
- [ ] Git installed and configured
- [ ] VS Code installed with extensions

### **Project Setup** ✅

- [ ] Repository cloned
- [ ] Python virtual environment created
- [ ] Dependencies installed (requirements.txt)
- [ ] Pre-commit hooks installed

### **Docker Environment** ✅

- [ ] .env file created and configured
- [ ] docker-compose up -d successful
- [ ] All 8 services running (ps shows "Up")
- [ ] Backend accessible at http://localhost:8000
- [ ] Swagger UI accessible at http://localhost:8000/docs

### **Database Setup** ✅

- [ ] Alembic migrations run (upgrade head)
- [ ] Database seeded (system roles created)
- [ ] Database connection verified

### **Testing** ✅

- [ ] pytest runs successfully
- [ ] Test coverage >90%
- [ ] Pre-commit hooks passing

### **API Verification** ✅

- [ ] Health endpoint working (GET /health)
- [ ] User registration working (POST /auth/register)
- [ ] User login working (POST /auth/login)
- [ ] Swagger UI functional

---

## 🎉 NEXT STEPS

### **You're Ready to Develop!**

**Week 4 Sprint** (Dec 3-6, 2025):
- [ ] Implement Authentication API (6 endpoints)
- [ ] Implement Gates API (8 endpoints)
- [ ] Write unit tests (95%+ coverage)
- [ ] Write integration tests (90%+ coverage)

**Reference Documentation**:
- [Week 4 Sprint Plan](../01-Sprint-Plans/WEEK-4-SPRINT-PLAN.md) - Detailed implementation guide
- [API Developer Guide](../../02-Design-Architecture/04-API-Design/API-DEVELOPER-GUIDE.md) - API documentation
- [Database Schema](../../01-Planning-Analysis/03-Data-Model/Data-Model-ERD.md) - Database design

---

## 📋 QUICK REFERENCE

### **Common Commands**

```bash
# Start development environment
docker-compose up -d

# View logs
docker-compose logs -f backend

# Run tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=html

# Run linting
ruff check backend/

# Run formatting
black backend/

# Run type checking
mypy backend/app

# Database migration
python -m alembic upgrade head

# Stop environment
docker-compose down
```

### **Environment URLs**

- Backend API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379
- MinIO Console: http://localhost:9001
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090

---

**Setup Status**: ✅ COMPLETE
**Estimated Setup Time**: 30 minutes
**Next**: [Week 4 Sprint Plan](../01-Sprint-Plans/WEEK-4-SPRINT-PLAN.md)

---

*SDLC Orchestrator - First Governance-First Platform on SDLC 5.1.3. Zero Mock Policy enforced. Battle-tested patterns applied. Production excellence delivered.*

**"Development environment ready. Let's build with discipline."** ⚔️ - Backend Lead

---

**Document Version**: 1.0.0
**Last Updated**: December 2, 2025
**Status**: ✅ READY FOR DEVELOPMENT
**Framework**: SDLC 5.1.3 Complete Lifecycle (10 Stages)
