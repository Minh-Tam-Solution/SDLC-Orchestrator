# SOP: Deployment of SDLC Orchestrator to Kubernetes

## Document Control
- **Document ID:** SOP-DEPLOYMENT-01
- **Version:** 1.0.0
- **Effective Date:** October 24, 2023
- **Owner:** DevOps Team Lead
- **Approver:** CTO

## 1. Purpose
This Standard Operating Procedure (SOP) outlines the steps required to deploy the SDLC Orchestrator application to a Kubernetes cluster with zero-downtime using rolling updates and health checks. The purpose is to ensure consistency, reliability, and security in production releases.

## 2. Scope
- **Systems/Processes Covered:** Deployment of SDLC Orchestrator on Kubernetes clusters.
- **Explicitly Excluded:** Initial setup and configuration of Kubernetes environments.

## 3. Procedure

### Pre-deployment Requirements and Checks

1. Ensure all necessary environment variables are set in the Kubernetes cluster (e.g., database connection strings, API keys).
2. Verify that Helm charts for SDLC Orchestrator are up-to-date with the latest version.
3. Check application code is tagged with a valid release version number.
4. Confirm that the staging environment reflects production accurately to ensure no unexpected issues arise during live deployment.

### Step-by-Step Deployment Procedure

1. **Prepare Release Artifacts:**
   - Tag and push new Docker images for SDLC Orchestrator to the container registry.
   
2. **Update Helm Charts:**
   - Update Helm charts with the latest Docker image tags from step 1.

3. **Run Pre-deployment Checks (Kubernetes):**
   - Execute `helm lint` command on the updated Helm chart to ensure there are no syntax or logical issues.

4. **Deploy Application:**
   - Run `helm upgrade --install <release-name> ./sdld-orchestrator/ --set image.tag=<new-version>` to start rolling update deployment.
   
5. **Monitor Deployment Status:**
   - Use `kubectl rollout status deployment/<deployment-name>` to monitor progress of the new release.

6. **Wait for Health Checks:**
   - Wait until all pods are in a ready state and health checks (HTTP/HTTPS) pass successfully before proceeding.

### Post-deployment Verification

1. Perform manual smoke tests on SDLC Orchestrator to ensure functionality.
2. Validate logs from deployed containers for any unexpected errors or warnings.
3. Review application metrics (CPU, memory usage) against baseline to confirm stability.

### Rollback Procedure if Issues Occur

1. **Identify Issue:**
   - Determine the nature and severity of deployment failure based on monitoring tools and logs.

2. **Initiate Rollback Process:**
   - Execute `helm rollback <release-name> <previous-version>` command to revert to a previous stable version.
   
3. **Monitor Rollback Status:**
   - Use kubectl commands like `kubectl rollout status` to track the progress of rolling back.
   
4. **Validate Environment Stability Post-Rollback:**
   - Repeat post-deployment verification steps from section 3.6.

### Approval Requirements

- Deployment must be approved by a designated approver (e.g., DevOps Manager) before proceeding with step-by-step deployment procedures.

## 4. Roles and Responsibilities
| Role | Responsibility | RACI |
|------|----------------|------|
| DevOps Engineer | Execute deployment steps as per the SOP | R |
| QA Lead | Conduct pre-deployment testing and validation | A |
| CTO | Approve release for production environment | I |

## 5. Quality Criteria
- [ ] All necessary environment variables are set.
- [ ] Helm charts are updated with correct Docker image tags.
- [ ] Deployment progresses smoothly without any major errors.
- [ ] Post-deployment verification confirms stability and functionality of SDLC Orchestrator.

## Revision History
| Version | Date       | Author         | Changes                                       |
|---------|------------|----------------|----------------------------------------------|
| 1.0.0   | October 24, 2023 | AI Agent    | Initial version                             |