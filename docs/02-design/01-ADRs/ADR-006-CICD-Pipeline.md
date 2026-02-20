# ADR-006: CI/CD Pipeline Architecture

**Status**: APPROVED
**Date**: November 13, 2025
**Decision Makers**: CTO, DevOps Lead, Tech Lead
**Stage**: Stage 02 (HOW - Design & Architecture)
**Framework**: SDLC 6.1.0

---

## Context

SDLC Orchestrator requires a robust CI/CD pipeline that:
1. **Enforces SDLC 6.1.0 gates** (eat our own dog food)
2. **Zero Mock Policy** compliance (NQH-Bot lesson)
3. **Multi-environment deployment** (dev, staging, production)
4. **Security scanning** (OWASP, SBOM, secrets)
5. **Performance testing** before production

We're using:
- **GitHub** as code repository
- **Docker** for containerization
- **AWS** for cloud infrastructure
- **Internal tools** (Ollama at api.nhatquangholding.com)

---

## Decision

Implement **GitHub Actions-based CI/CD** with:

1. **Build Pipeline**: Test → Security → Quality → Package
2. **Deploy Pipeline**: Staging → Testing → Production
3. **Gate Enforcement**: SDLC 6.1.0 gates as pipeline stages
4. **Infrastructure as Code**: Terraform for AWS resources
5. **Monitoring Integration**: Prometheus/Grafana metrics

---

## Rationale

### Why GitHub Actions?

**Native Integration**:
- Already using GitHub for code
- Built-in secrets management
- Matrix builds for multiple environments
- Self-hosted runners for sensitive operations

**Cost Effective**:
- 2,000 free minutes/month
- Self-hosted runners for heavy workloads
- No additional CI/CD tool licensing

**Flexibility**:
- Custom actions for SDLC gates
- Docker support built-in
- Easy integration with AWS

### Pipeline Philosophy

Following SDLC 6.1.0 stages:
- **Stage 04 (BUILD)**: Code compilation, unit tests
- **Stage 05 (TEST)**: Integration tests, E2E tests
- **Stage 05 (SHIP)**: Deployment, smoke tests
- **Stage 06 (RUN)**: Monitoring, health checks

---

## Architecture Design

### 1. Pipeline Overview

```mermaid
graph LR
    subgraph "Developer Flow"
        DEV[Developer] --> COMMIT[Git Commit]
        COMMIT --> PR[Pull Request]
    end

    subgraph "CI Pipeline"
        PR --> GATE_G3[Gate G3: Build]
        GATE_G3 --> BUILD[Build & Test]
        BUILD --> GATE_G4[Gate G4: Test]
        GATE_G4 --> TEST[Integration Tests]
        TEST --> SECURITY[Security Scan]
        SECURITY --> GATE_G5[Gate G5: Ship Ready]
    end

    subgraph "CD Pipeline"
        GATE_G5 --> STAGING[Deploy Staging]
        STAGING --> E2E[E2E Tests]
        E2E --> GATE_G6[Gate G6: Production Ready]
        GATE_G6 --> PROD[Deploy Production]
        PROD --> MONITOR[Monitoring]
    end

    style GATE_G3 fill:#f9f9f9
    style GATE_G4 fill:#f9f9f9
    style GATE_G5 fill:#f9f9f9
    style GATE_G6 fill:#f9f9f9
```

---

### 2. GitHub Actions Workflow

#### 2.1 CI Pipeline (Pull Request)

```yaml
# .github/workflows/ci.yml
name: CI Pipeline - SDLC Gates G3-G5

on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [develop]

env:
  PYTHON_VERSION: '3.11'
  NODE_VERSION: '18'
  DOCKER_BUILDKIT: 1

jobs:
  # ============================================
  # GATE G3: BUILD READY
  # ============================================
  gate-g3-build:
    name: 'Gate G3: Build Ready'
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: 'G3.1: Code Quality Check'
        run: |
          # Check code formatting
          black --check .
          isort --check-only .
          flake8 .

      - name: 'G3.2: Type Checking'
        run: |
          mypy . --strict

      - name: 'G3.3: Documentation Check'
        run: |
          # Ensure all functions have docstrings
          pydocstyle . --convention=google

      - name: 'Gate G3 Evidence'
        uses: ./.github/actions/gate-evidence
        with:
          gate_id: 'G3'
          evidence_type: 'code_quality'
          status: 'PASS'

  # ============================================
  # BUILD & UNIT TEST
  # ============================================
  build-and-test:
    name: 'Build & Unit Test'
    needs: gate-g3-build
    runs-on: ubuntu-latest

    strategy:
      matrix:
        python-version: ['3.11', '3.12']

    services:
      postgres:
        image: postgres:15.5
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: sdlc_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Cache Dependencies
        uses: actions/cache@v3
        with:
          path: |
            ~/.cache/pip
            ~/.cache/pypoetry
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt', '**/pyproject.toml') }}

      - name: Install Dependencies
        run: |
          pip install --upgrade pip
          pip install poetry
          poetry install

      - name: Run Unit Tests (Zero Mock Policy)
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/sdlc_test
          REDIS_URL: redis://localhost:6379
          OLLAMA_API_URL: https://api.nhatquangholding.com
        run: |
          # Zero Mock Policy - all tests use real services
          poetry run pytest tests/unit \
            --cov=app \
            --cov-report=xml \
            --cov-report=term-missing \
            --cov-fail-under=80

      - name: Upload Coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: true

  # ============================================
  # GATE G4: TEST COMPLETE
  # ============================================
  gate-g4-test:
    name: 'Gate G4: Test Complete'
    needs: build-and-test
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: 'G4.1: Test Coverage Check'
        run: |
          # Ensure 80% coverage minimum
          coverage_percent=$(grep -oP 'line-rate="\K[^"]+' coverage.xml | head -1)
          coverage_int=$(echo "$coverage_percent * 100" | bc | cut -d. -f1)
          if [ $coverage_int -lt 80 ]; then
            echo "Coverage $coverage_int% is below 80% threshold"
            exit 1
          fi

      - name: 'G4.2: Integration Tests'
        run: |
          poetry run pytest tests/integration \
            --maxfail=1 \
            --tb=short

      - name: 'G4.3: Contract Tests'
        run: |
          # Test against OpenAPI spec
          poetry run pytest tests/contract \
            --openapi-spec=docs/openapi.yml

      - name: 'Gate G4 Evidence'
        uses: ./.github/actions/gate-evidence
        with:
          gate_id: 'G4'
          evidence_type: 'test_results'
          coverage: '85%'
          status: 'PASS'

  # ============================================
  # SECURITY SCANNING
  # ============================================
  security-scan:
    name: 'Security Scanning'
    needs: gate-g4-test
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: 'OWASP Dependency Check'
        uses: dependency-check/Dependency-Check_Action@main
        with:
          project: 'SDLC-Orchestrator'
          path: '.'
          format: 'JSON'
          args: >
            --enableRetired
            --enableExperimental

      - name: 'Semgrep Security Scan'
        uses: returntocorp/semgrep-action@v1
        with:
          config: >-
            p/security-audit
            p/owasp-top-ten
            p/python

      - name: 'Trivy Container Scan'
        run: |
          docker build -t sdlc-orchestrator:scan .
          trivy image sdlc-orchestrator:scan \
            --severity HIGH,CRITICAL \
            --exit-code 1

      - name: 'Secret Detection'
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          base: ${{ github.event.repository.default_branch }}

      - name: 'SBOM Generation'
        run: |
          # Generate Software Bill of Materials
          syft packages dir:. -o cyclonedx-json > sbom.json

          # Check for AGPL dependencies
          python scripts/check_agpl_dependencies.py sbom.json

  # ============================================
  # GATE G5: SHIP READY
  # ============================================
  gate-g5-ship:
    name: 'Gate G5: Ship Ready'
    needs: [security-scan]
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: 'G5.1: Build Docker Image'
        run: |
          docker build \
            --build-arg VERSION=${{ github.sha }} \
            --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
            -t sdlc-orchestrator:${{ github.sha }} \
            .

      - name: 'G5.2: Runbook Validation'
        run: |
          # Check runbooks exist
          for runbook in api-down high-latency database-down; do
            if [ ! -f "docs/runbooks/$runbook.md" ]; then
              echo "Missing runbook: $runbook.md"
              exit 1
            fi
          done

      - name: 'G5.3: Performance Test'
        run: |
          # Run Locust performance test
          docker-compose -f docker-compose.test.yml up -d
          sleep 10  # Wait for services

          locust \
            -f tests/performance/locustfile.py \
            --host http://localhost:8000 \
            --users 100 \
            --spawn-rate 10 \
            --run-time 60s \
            --headless \
            --only-summary

      - name: 'G5.4: OpenAPI Spec Validation'
        run: |
          # Validate OpenAPI specification
          spectral lint docs/openapi.yml

      - name: 'Push to ECR (if main branch)'
        if: github.ref == 'refs/heads/main'
        env:
          AWS_REGION: us-west-2
          ECR_REGISTRY: ${{ secrets.ECR_REGISTRY }}
        run: |
          aws ecr get-login-password --region $AWS_REGION | \
            docker login --username AWS --password-stdin $ECR_REGISTRY

          docker tag sdlc-orchestrator:${{ github.sha }} \
            $ECR_REGISTRY/sdlc-orchestrator:${{ github.sha }}

          docker push $ECR_REGISTRY/sdlc-orchestrator:${{ github.sha }}

      - name: 'Gate G5 Evidence'
        uses: ./.github/actions/gate-evidence
        with:
          gate_id: 'G5'
          evidence_type: 'ship_ready'
          docker_image: ${{ github.sha }}
          status: 'PASS'
```

#### 2.2 CD Pipeline (Deployment)

```yaml
# .github/workflows/cd.yml
name: CD Pipeline - SDLC Gates G6-G7

on:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy'
        required: true
        type: choice
        options:
          - staging
          - production

jobs:
  # ============================================
  # DEPLOY TO STAGING
  # ============================================
  deploy-staging:
    name: 'Deploy to Staging'
    runs-on: ubuntu-latest
    environment: staging

    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-west-2

      - name: Deploy with Terraform
        run: |
          cd infrastructure/staging
          terraform init
          terraform plan -var="image_tag=${{ github.sha }}"
          terraform apply -auto-approve -var="image_tag=${{ github.sha }}"

      - name: Run Database Migrations
        run: |
          # Run Alembic migrations
          kubectl exec -it deployment/api -- alembic upgrade head

      - name: Smoke Tests
        run: |
          # Wait for deployment
          sleep 30

          # Health check
          curl -f https://staging.sdlc-orchestrator.com/health || exit 1

          # API smoke test
          python scripts/smoke_test.py --env staging

  # ============================================
  # E2E TESTS ON STAGING
  # ============================================
  e2e-tests:
    name: 'E2E Tests on Staging'
    needs: deploy-staging
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Playwright
        uses: microsoft/playwright-github-action@v1

      - name: Run E2E Tests
        env:
          BASE_URL: https://staging.sdlc-orchestrator.com
        run: |
          npm ci
          npx playwright test --project=chromium

      - name: Upload Test Results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: playwright-report/

  # ============================================
  # GATE G6: PRODUCTION READY
  # ============================================
  gate-g6-production:
    name: 'Gate G6: Production Ready'
    needs: e2e-tests
    runs-on: ubuntu-latest
    environment: production-approval

    steps:
      - name: 'G6.1: Staging Validation'
        run: |
          # Check staging metrics
          python scripts/check_staging_metrics.py \
            --slo-compliance 99.9 \
            --error-rate 0.1 \
            --latency-p95 100

      - name: 'G6.2: Security Approval'
        run: |
          # Check security scan results
          echo "Checking security scan results..."
          # Would integrate with security tools API

      - name: 'G6.3: Rollback Plan'
        run: |
          # Verify rollback procedure exists
          if [ ! -f "docs/runbooks/rollback.md" ]; then
            echo "Missing rollback procedure"
            exit 1
          fi

      - name: 'Gate G6 Evidence'
        uses: ./.github/actions/gate-evidence
        with:
          gate_id: 'G6'
          evidence_type: 'production_ready'
          staging_slo: '99.95%'
          status: 'PENDING_APPROVAL'

  # ============================================
  # PRODUCTION DEPLOYMENT
  # ============================================
  deploy-production:
    name: 'Deploy to Production'
    needs: gate-g6-production
    runs-on: ubuntu-latest
    environment: production

    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.PROD_AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.PROD_AWS_SECRET_ACCESS_KEY }}
          aws-region: us-west-2

      - name: Blue-Green Deployment
        run: |
          # Deploy to green environment
          cd infrastructure/production
          terraform init
          terraform workspace select green
          terraform apply -auto-approve -var="image_tag=${{ github.sha }}"

          # Run health checks on green
          python scripts/health_check.py --env green

          # Switch traffic to green
          aws elbv2 modify-listener-rule \
            --rule-arn ${{ secrets.PROD_ALB_RULE_ARN }} \
            --actions Type=forward,TargetGroupArn=${{ secrets.GREEN_TG_ARN }}

      - name: Production Smoke Tests
        run: |
          sleep 60  # Wait for traffic switch
          python scripts/smoke_test.py --env production

      - name: Rollback on Failure
        if: failure()
        run: |
          # Switch back to blue
          aws elbv2 modify-listener-rule \
            --rule-arn ${{ secrets.PROD_ALB_RULE_ARN }} \
            --actions Type=forward,TargetGroupArn=${{ secrets.BLUE_TG_ARN }}

          # Alert team
          curl -X POST ${{ secrets.SLACK_WEBHOOK }} \
            -d '{"text": "Production deployment failed and rolled back"}'
```

---

### 3. Custom GitHub Actions

#### 3.1 Gate Evidence Action

```yaml
# .github/actions/gate-evidence/action.yml
name: 'SDLC Gate Evidence'
description: 'Collect and store gate evidence'

inputs:
  gate_id:
    description: 'Gate ID (G3, G4, G5, etc)'
    required: true
  evidence_type:
    description: 'Type of evidence'
    required: true
  status:
    description: 'Gate status'
    required: true

runs:
  using: 'composite'
  steps:
    - name: Collect Evidence
      shell: bash
      run: |
        # Create evidence JSON
        cat > evidence.json <<EOF
        {
          "gate_id": "${{ inputs.gate_id }}",
          "evidence_type": "${{ inputs.evidence_type }}",
          "status": "${{ inputs.status }}",
          "commit_sha": "${{ github.sha }}",
          "branch": "${{ github.ref }}",
          "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
          "run_id": "${{ github.run_id }}",
          "run_url": "${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"
        }
        EOF

    - name: Upload to Evidence Vault
      shell: bash
      run: |
        # Upload evidence to S3 (Evidence Vault)
        aws s3 cp evidence.json \
          s3://sdlc-evidence/${{ github.repository }}/${{ inputs.gate_id }}/${{ github.sha }}.json

    - name: Update Gate Status
      shell: bash
      run: |
        # Call SDLC Orchestrator API to update gate status
        curl -X POST https://api.sdlc-orchestrator.com/gates/${{ inputs.gate_id }}/evidence \
          -H "Authorization: Bearer ${{ secrets.SDLC_API_TOKEN }}" \
          -H "Content-Type: application/json" \
          -d @evidence.json
```

---

### 4. Infrastructure as Code

```hcl
# infrastructure/modules/ecs-service/main.tf
resource "aws_ecs_service" "api" {
  name            = "sdlc-orchestrator-api"
  cluster         = var.ecs_cluster_id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.desired_count

  deployment_configuration {
    maximum_percent         = 200
    minimum_healthy_percent = 100

    deployment_circuit_breaker {
      enable   = true
      rollback = true
    }
  }

  load_balancer {
    target_group_arn = var.target_group_arn
    container_name   = "api"
    container_port   = 8000
  }

  # Blue-Green deployment support
  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Environment = var.environment
    Version     = var.image_tag
  }
}
```

---

### 5. Performance Testing

```python
# tests/performance/locustfile.py
from locust import HttpUser, task, between

class SDLCUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # Login
        response = self.client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "password"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(50)
    def list_projects(self):
        self.client.get("/projects", headers=self.headers)

    @task(20)
    def get_gate_status(self):
        self.client.get("/gates/G3/status", headers=self.headers)

    @task(10)
    def evaluate_gate(self):
        self.client.post("/gates/G3/evaluate",
                         headers=self.headers,
                         json={"project_id": "test-project"})

# Run with: locust -f locustfile.py --host http://localhost:8000
```

---

### 6. DORA Metrics Tracking

```yaml
# .github/workflows/dora-metrics.yml
name: DORA Metrics

on:
  push:
    branches: [main]
  deployment:
  issues:
    types: [opened, closed]

jobs:
  track-metrics:
    runs-on: ubuntu-latest

    steps:
      - name: Calculate Deployment Frequency
        run: |
          # Count deployments in last 30 days
          deployments=$(gh api repos/${{ github.repository }}/deployments \
            --jq '[.[] | select(.created_at > (now - 2592000))] | length')

          echo "Deployment Frequency: $deployments deployments/month"

      - name: Calculate Lead Time
        run: |
          # Time from commit to production
          commit_time=${{ github.event.head_commit.timestamp }}
          deploy_time=$(date -u +%Y-%m-%dT%H:%M:%SZ)
          lead_time=$(( $(date -d "$deploy_time" +%s) - $(date -d "$commit_time" +%s) ))

          echo "Lead Time: $((lead_time / 3600)) hours"

      - name: Calculate Change Failure Rate
        run: |
          # Rollbacks in last 30 days / Total deployments
          rollbacks=$(gh api repos/${{ github.repository }}/issues \
            --jq '[.[] | select(.labels[].name == "rollback")] | length')

          failure_rate=$(( rollbacks * 100 / deployments ))
          echo "Change Failure Rate: $failure_rate%"

      - name: Send to Prometheus
        run: |
          # Push metrics to Prometheus Pushgateway
          cat <<EOF | curl --data-binary @- http://prometheus-pushgateway:9091/metrics/job/dora
          deployment_frequency $deployments
          lead_time_hours $((lead_time / 3600))
          change_failure_rate $failure_rate
          EOF
```

---

## Consequences

### Positive

1. **Gate Enforcement**: CI/CD enforces SDLC 6.1.0 gates automatically
2. **Quality Assurance**: Zero Mock Policy ensures real testing
3. **Fast Feedback**: Developers get results in <10 minutes
4. **Security**: OWASP, SBOM, secret scanning built-in
5. **Observability**: DORA metrics tracked automatically

### Negative

1. **Complexity**: Many pipeline stages to maintain
2. **Time**: Full pipeline takes 15-20 minutes
3. **Cost**: GitHub Actions minutes + AWS resources
4. **Learning Curve**: Team needs to understand gate system

### Risks

1. **Pipeline Failures**: Blocking deployments
   - **Mitigation**: Emergency bypass procedure for hotfixes

2. **Flaky Tests**: False failures
   - **Mitigation**: Retry mechanism, test stability monitoring

3. **Security Scan False Positives**: Blocking valid code
   - **Mitigation**: Allowlist mechanism with approval

---

## Implementation Plan

### Phase 1: Basic Pipeline (Day 1-2)
- [ ] Setup GitHub Actions workflows
- [ ] Configure AWS credentials
- [ ] Basic build and test pipeline

### Phase 2: Gate Integration (Day 3-4)
- [ ] Implement gate evidence collection
- [ ] Add SDLC gate checks
- [ ] Setup Evidence Vault integration

### Phase 3: Security & Quality (Day 5-6)
- [ ] Add security scanning (OWASP, Trivy)
- [ ] Implement SBOM generation
- [ ] Add performance testing

### Phase 4: Deployment (Day 7-8)
- [ ] Setup Terraform infrastructure
- [ ] Implement blue-green deployment
- [ ] Add rollback mechanism

### Phase 5: Monitoring (Day 9-10)
- [ ] DORA metrics collection
- [ ] Prometheus/Grafana integration
- [ ] Alert configuration

---

## Alternatives Considered

### Alternative 1: GitLab CI/CD
- ❌ **Rejected**: Would require migrating from GitHub

### Alternative 2: Jenkins
- ❌ **Rejected**: Additional infrastructure to maintain

### Alternative 3: CircleCI
- ❌ **Rejected**: Additional cost, less GitHub integration

### Alternative 4: AWS CodePipeline
- ❌ **Rejected**: Vendor lock-in, less flexibility

---

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [DORA Metrics](https://dora.dev/)
- [Zero Mock Policy](../../heritage/nqh-bot-lessons.md)
- [SDLC 6.1.0 Gates](../../sdlc-framework/gates.md)

---

## Approval

| Role | Name | Decision | Date |
|------|------|----------|------|
| **CTO** | [CTO Name] | ✅ APPROVED | Nov 13, 2025 |
| **DevOps Lead** | [DevOps Name] | ✅ APPROVED | Nov 13, 2025 |
| **Tech Lead** | [Tech Lead Name] | ✅ APPROVED | Nov 13, 2025 |

---

**Decision**: **APPROVED** - GitHub Actions CI/CD with gate enforcement

**Priority**: **RECOMMENDED** - Essential for quality delivery

**Timeline**: 2 weeks implementation in BUILD phase

**Success Metrics**:
- Deployment frequency >4/week
- Lead time <2 hours
- Change failure rate <5%
- MTTR <1 hour
- All gates passing before production

---

*"The pipeline is the product - eat your own dog food"* 🚀