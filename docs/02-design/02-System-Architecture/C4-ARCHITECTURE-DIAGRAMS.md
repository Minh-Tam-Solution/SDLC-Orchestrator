# C4 Architecture Diagrams - SDLC Orchestrator

**Version**: 1.0.0
**Date**: November 18, 2025
**Status**: ACTIVE - Week 4 Day 1 Architecture Documentation
**Authority**: Solutions Architect + CTO Approved
**Foundation**: Week 3 Complete (23 APIs, 21 tables, 28 tests)
**Framework**: SDLC 6.1.0

---

## Table of Contents

1. [Overview](#overview)
2. [C4 Model Introduction](#c4-model-introduction)
3. [Level 1: System Context Diagram](#level-1-system-context-diagram)
4. [Level 2: Container Diagram](#level-2-container-diagram)
5. [Level 3: Component Diagram - Backend](#level-3-component-diagram---backend)
6. [Level 3: Component Diagram - Frontend](#level-3-component-diagram---frontend)
7. [Deployment Architecture](#deployment-architecture)
8. [Technology Stack](#technology-stack)

---

## Overview

This document provides comprehensive C4 architecture diagrams for the SDLC Orchestrator platform, following the C4 model for visualizing software architecture created by Simon Brown.

**Purpose**:
- Provide clear communication of system architecture to stakeholders
- Document system structure at multiple levels of abstraction
- Support Gate G2 approval (architecture completeness)
- Guide development teams during implementation

**Scope**: Full system architecture covering:
- System Context (external integrations)
- Containers (applications and data stores)
- Components (internal structure)
- Deployment (infrastructure)

---

## C4 Model Introduction

The C4 model consists of 4 levels of abstraction:

1. **Context**: Shows the system in its environment with external dependencies
2. **Container**: Shows high-level technology choices (applications, databases)
3. **Component**: Shows internal structure of containers
4. **Code**: Shows class diagrams (not included - use IDE for this level)

**Notation**:
- `Person` - Human user
- `System` - Software system
- `Container` - Application or data store
- `Component` - Internal module/package

---

## Level 1: System Context Diagram

Shows SDLC Orchestrator in its environment with external systems and users.

```mermaid
C4Context
    title System Context Diagram - SDLC Orchestrator

    Person(developer, "Developer", "Software engineer working on projects")
    Person(manager, "Engineering Manager", "Manages teams and projects")
    Person(executive, "Executive", "C-level stakeholders (CTO, CPO, CEO)")

    System(sdlc_orch, "SDLC Orchestrator", "AI-Native SDLC Governance Platform<br/>Quality Gates + Evidence Vault + Policy Engine")

    System_Ext(github, "GitHub", "Source code repository<br/>PR management + webhooks")
    System_Ext(claude, "Claude API", "Anthropic Claude 3.5 Sonnet<br/>AI context generation")
    System_Ext(gpt4, "OpenAI GPT-4o", "OpenAI API<br/>AI fallback provider")
    System_Ext(gemini, "Google Gemini", "Google AI<br/>Cost-effective AI provider")
    System_Ext(slack, "Slack", "Team notifications<br/>Gate approvals + alerts")
    System_Ext(email, "Email (SMTP)", "Email notifications<br/>Gate status updates")

    Rel(developer, sdlc_orch, "Uses", "HTTPS/WebSocket")
    Rel(manager, sdlc_orch, "Reviews gates<br/>Approves/Rejects", "HTTPS")
    Rel(executive, sdlc_orch, "Views dashboards<br/>Monitors metrics", "HTTPS")

    Rel(sdlc_orch, github, "Fetches PRs<br/>Receives webhooks", "REST API<br/>Webhooks")
    Rel(sdlc_orch, claude, "Generates context<br/>Drafts docs", "REST API")
    Rel(sdlc_orch, gpt4, "Fallback AI", "REST API")
    Rel(sdlc_orch, gemini, "Cost-effective AI", "REST API")
    Rel(sdlc_orch, slack, "Sends notifications", "Webhooks")
    Rel(sdlc_orch, email, "Sends emails", "SMTP")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="2")
```

**Key External Dependencies**:
1. **GitHub** - Source code repository (PR auto-collection, webhooks)
2. **AI Providers** - Multi-provider strategy (Claude primary, GPT-4o/Gemini fallback)
3. **Notifications** - Slack webhooks + SMTP email
4. **Users** - Developers, managers, executives (RBAC roles)

---

## Level 2: Container Diagram

Shows applications and data stores within SDLC Orchestrator.

```mermaid
C4Container
    title Container Diagram - SDLC Orchestrator

    Person(user, "User", "Developer/Manager/Executive")

    System_Boundary(sdlc_boundary, "SDLC Orchestrator") {
        Container(web_app, "Web Application", "React + TypeScript + Vite", "Single-page application<br/>Real-time dashboard")
        Container(mobile_app, "Mobile App", "React Native", "iOS/Android app<br/>Gate approvals on-the-go")
        Container(api, "Backend API", "FastAPI + Python 3.11", "RESTful API<br/>23 endpoints")
        Container(websocket, "WebSocket Server", "FastAPI WebSocket", "Real-time updates<br/>Live gate status")

        ContainerDb(postgres, "Database", "PostgreSQL 15.5", "Primary data store<br/>21 tables, 1.9M rows/year")
        ContainerDb(redis, "Cache", "Redis 7.2", "Session store<br/>Rate limiting")
        ContainerDb(minio, "Object Storage", "MinIO S3", "Evidence files<br/>200K files/year")

        Container(opa, "Policy Engine", "Open Policy Agent 0.68", "Rego policy evaluation<br/>110+ pre-built policies")
        Container(prometheus, "Metrics", "Prometheus", "Time-series metrics<br/>Performance monitoring")
        Container(grafana, "Dashboards", "Grafana", "Visualization<br/>Real-time dashboards")
    }

    System_Ext(github, "GitHub", "Source code repository")
    System_Ext(claude, "Claude API", "AI provider")

    Rel(user, web_app, "Uses", "HTTPS")
    Rel(user, mobile_app, "Uses", "HTTPS")

    Rel(web_app, api, "API calls", "JSON/HTTPS")
    Rel(web_app, websocket, "Real-time updates", "WebSocket/WSS")
    Rel(mobile_app, api, "API calls", "JSON/HTTPS")

    Rel(api, postgres, "Reads/Writes", "SQL/asyncpg")
    Rel(api, redis, "Caches", "Redis protocol")
    Rel(api, minio, "Stores files", "S3 API")
    Rel(api, opa, "Evaluates policies", "REST API")
    Rel(api, prometheus, "Exposes metrics", "Prometheus protocol")
    Rel(api, github, "Fetches PRs", "REST API")
    Rel(api, claude, "AI context", "REST API")

    Rel(grafana, prometheus, "Queries metrics", "PromQL")
    Rel(websocket, redis, "Pub/Sub", "Redis Pub/Sub")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="2")
```

**Key Containers**:
1. **Web Application** - React SPA (real-time dashboard, gate management)
2. **Backend API** - FastAPI (23 endpoints, async I/O)
3. **PostgreSQL** - Primary database (21 tables, transactional data)
4. **MinIO** - S3-compatible storage (evidence files)
5. **OPA** - Policy evaluation engine (Rego policies)
6. **Redis** - Cache + rate limiting + WebSocket pub/sub
7. **Prometheus + Grafana** - Monitoring stack

---

## Level 3: Component Diagram - Backend

Shows internal components of the FastAPI backend.

```mermaid
C4Component
    title Component Diagram - Backend API (FastAPI)

    Container_Boundary(api_boundary, "Backend API - FastAPI") {
        Component(auth_api, "Authentication API", "FastAPI Router", "6 endpoints<br/>JWT login/refresh/logout")
        Component(gates_api, "Gates API", "FastAPI Router", "8 endpoints<br/>CRUD + submit/approve/reject")
        Component(evidence_api, "Evidence API", "FastAPI Router", "5 endpoints<br/>Upload + integrity checks")
        Component(policies_api, "Policies API", "FastAPI Router", "4 endpoints<br/>List + evaluate policies")

        Component(auth_service, "Auth Service", "Business Logic", "User authentication<br/>JWT token generation")
        Component(gate_service, "Gate Service", "Business Logic", "Gate workflow<br/>Approval logic")
        Component(evidence_service, "Evidence Service", "Business Logic", "File upload<br/>SHA256 integrity")
        Component(policy_service, "Policy Service", "Business Logic", "OPA integration<br/>Policy evaluation")

        Component(user_model, "User Model", "SQLAlchemy ORM", "User + Role + OAuth")
        Component(gate_model, "Gate Model", "SQLAlchemy ORM", "Gate + Approval + Transition")
        Component(evidence_model, "Evidence Model", "SQLAlchemy ORM", "GateEvidence + IntegrityCheck")
        Component(policy_model, "Policy Model", "SQLAlchemy ORM", "Policy + Evaluation")

        Component(security, "Security Core", "bcrypt + JWT", "Password hashing<br/>Token generation")
        Component(db_session, "DB Session", "SQLAlchemy Async", "Database connection pool<br/>Transaction management")
    }

    ContainerDb(postgres, "PostgreSQL", "Database")
    ContainerDb(redis, "Redis", "Cache")
    ContainerDb(minio, "MinIO", "Object Storage")
    Container(opa, "OPA", "Policy Engine")

    Rel(auth_api, auth_service, "Uses")
    Rel(gates_api, gate_service, "Uses")
    Rel(evidence_api, evidence_service, "Uses")
    Rel(policies_api, policy_service, "Uses")

    Rel(auth_service, user_model, "Uses")
    Rel(gate_service, gate_model, "Uses")
    Rel(evidence_service, evidence_model, "Uses")
    Rel(policy_service, policy_model, "Uses")

    Rel(auth_service, security, "Uses")
    Rel(user_model, db_session, "Uses")
    Rel(gate_model, db_session, "Uses")
    Rel(evidence_model, db_session, "Uses")
    Rel(policy_model, db_session, "Uses")

    Rel(db_session, postgres, "Reads/Writes", "SQL")
    Rel(auth_service, redis, "Caches tokens", "Redis")
    Rel(evidence_service, minio, "Uploads files", "S3 API")
    Rel(policy_service, opa, "Evaluates", "REST API")

    UpdateLayoutConfig($c4ShapeInRow="4", $c4BoundaryInRow="2")
```

**Backend Architecture**:
- **Layered Architecture**: API → Service → Model → Database
- **API Layer**: 4 FastAPI routers (Auth, Gates, Evidence, Policies)
- **Service Layer**: Business logic (authentication, workflows, file management)
- **Data Layer**: SQLAlchemy ORM models (21 tables)
- **Infrastructure**: Database session management, security core

---

## Level 3: Component Diagram - Frontend

Shows internal components of the React frontend.

```mermaid
C4Component
    title Component Diagram - Web Application (React)

    Container_Boundary(web_boundary, "Web Application - React") {
        Component(auth_page, "Auth Pages", "React Components", "Login/Logout<br/>OAuth callbacks")
        Component(dashboard, "Dashboard", "React Components", "Real-time overview<br/>Gate status")
        Component(gates_page, "Gates Pages", "React Components", "Gate list<br/>Gate details + approval")
        Component(evidence_page, "Evidence Pages", "React Components", "Evidence upload<br/>Integrity history")
        Component(policies_page, "Policies Pages", "React Components", "Policy library<br/>Evaluation results")

        Component(auth_store, "Auth Store", "Zustand State", "User session<br/>JWT tokens")
        Component(gates_store, "Gates Store", "Zustand State", "Gates data<br/>Real-time updates")
        Component(notifications, "Notifications", "React Context", "Toast notifications<br/>WebSocket events")

        Component(api_client, "API Client", "Axios + React Query", "HTTP requests<br/>Caching + retry")
        Component(websocket_client, "WebSocket Client", "Socket.io", "Real-time updates<br/>Gate status changes")
        Component(router, "Router", "React Router v6", "Client-side routing<br/>Protected routes")
    }

    Container(api, "Backend API", "FastAPI")
    Container(websocket, "WebSocket Server", "FastAPI WebSocket")

    Rel(auth_page, auth_store, "Updates")
    Rel(dashboard, gates_store, "Reads")
    Rel(gates_page, gates_store, "Reads/Updates")
    Rel(evidence_page, gates_store, "Reads")
    Rel(policies_page, gates_store, "Reads")

    Rel(auth_store, api_client, "Uses")
    Rel(gates_store, api_client, "Uses")
    Rel(gates_store, websocket_client, "Uses")
    Rel(notifications, websocket_client, "Listens")

    Rel(api_client, api, "HTTP/HTTPS", "JSON")
    Rel(websocket_client, websocket, "WebSocket", "JSON")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="2")
```

**Frontend Architecture**:
- **Component-Based**: React 18 with TypeScript
- **State Management**: Zustand (lightweight Redux alternative)
- **Data Fetching**: React Query (caching + optimistic updates)
- **Real-time**: WebSocket client (live gate status)
- **Routing**: React Router v6 (protected routes with RBAC)

---

## Deployment Architecture

Shows production deployment on AWS/GCP/Azure.

```mermaid
C4Deployment
    title Deployment Diagram - Production (AWS/GCP/Azure)

    Deployment_Node(cloud, "Cloud Provider", "AWS/GCP/Azure") {
        Deployment_Node(cdn, "CDN", "CloudFront/Cloud CDN") {
            Container(static_files, "Static Files", "S3/Cloud Storage", "React build<br/>JS/CSS/Images")
        }

        Deployment_Node(k8s, "Kubernetes Cluster", "EKS/GKE/AKS") {
            Deployment_Node(ingress, "Ingress", "NGINX Ingress Controller") {
                Container(lb, "Load Balancer", "AWS ALB/GCP LB", "TLS termination<br/>SSL certificates")
            }

            Deployment_Node(backend_pods, "Backend Pods", "3 replicas") {
                Container(api_pod, "Backend API", "FastAPI", "1 CPU, 2GB RAM")
            }

            Deployment_Node(db_cluster, "Database Cluster", "RDS/Cloud SQL") {
                ContainerDb(postgres_primary, "PostgreSQL Primary", "PostgreSQL 15.5", "4 vCPU, 16GB RAM")
                ContainerDb(postgres_replica, "PostgreSQL Replica", "PostgreSQL 15.5", "Read replica<br/>Backups")
            }

            Deployment_Node(cache_cluster, "Cache Cluster", "ElastiCache/Memorystore") {
                ContainerDb(redis_primary, "Redis Primary", "Redis 7.2", "2 vCPU, 4GB RAM")
                ContainerDb(redis_replica, "Redis Replica", "Redis 7.2", "Failover replica")
            }

            Deployment_Node(object_storage, "Object Storage", "S3/Cloud Storage") {
                ContainerDb(evidence_bucket, "Evidence Bucket", "MinIO/S3", "Lifecycle policies<br/>Versioning enabled")
            }

            Deployment_Node(monitoring, "Monitoring Stack") {
                Container(prometheus, "Prometheus", "Prometheus", "Metrics storage")
                Container(grafana, "Grafana", "Grafana", "Dashboards")
            }
        }
    }

    Deployment_Node(external, "External Services") {
        System_Ext(github, "GitHub", "Source code")
        System_Ext(claude, "Claude API", "AI provider")
    }

    Rel(lb, api_pod, "Routes", "HTTPS")
    Rel(api_pod, postgres_primary, "Writes", "SQL/TLS")
    Rel(api_pod, postgres_replica, "Reads", "SQL/TLS")
    Rel(api_pod, redis_primary, "Caches", "Redis/TLS")
    Rel(api_pod, evidence_bucket, "Stores", "S3 API/TLS")
    Rel(api_pod, github, "Fetches", "HTTPS")
    Rel(api_pod, claude, "AI", "HTTPS")
    Rel(prometheus, api_pod, "Scrapes", "HTTP")

    UpdateLayoutConfig($c4ShapeInRow="2", $c4BoundaryInRow="1")
```

**Deployment Highlights**:
- **High Availability**: 3 backend replicas, database replication
- **Auto-Scaling**: Horizontal pod autoscaling (HPA) based on CPU/memory
- **Security**: TLS everywhere, private subnets, security groups
- **Disaster Recovery**: Automated backups (daily), cross-region replication
- **Monitoring**: Prometheus + Grafana (metrics, alerts, dashboards)

---

## Technology Stack

### Frontend
- **Framework**: React 18.2 + TypeScript 5.3
- **Build Tool**: Vite 5.0 (fast dev server, optimized builds)
- **State Management**: Zustand 4.4 (lightweight Redux alternative)
- **Data Fetching**: React Query 5.0 (caching, optimistic updates)
- **UI Components**: shadcn/ui + Tailwind CSS 3.4
- **Real-time**: Socket.io client (WebSocket)
- **Routing**: React Router v6
- **Forms**: React Hook Form + Zod (validation)

### Backend
- **Framework**: FastAPI 0.109 + Python 3.11
- **ORM**: SQLAlchemy 2.0 (async)
- **Database**: PostgreSQL 15.5 (asyncpg driver)
- **Migrations**: Alembic 1.13
- **Authentication**: JWT (python-jose) + OAuth 2.0
- **Password Hashing**: bcrypt
- **Validation**: Pydantic v2
- **Testing**: pytest + httpx + pytest-asyncio
- **API Docs**: OpenAPI 3.1 (auto-generated)

### Infrastructure
- **Database**: PostgreSQL 15.5 (primary data store)
- **Cache**: Redis 7.2 (sessions, rate limiting, pub/sub)
- **Object Storage**: MinIO (S3-compatible, evidence files)
- **Policy Engine**: Open Policy Agent 0.68 (Rego policies)
- **Monitoring**: Prometheus + Grafana + Alertmanager
- **Container Runtime**: Docker 24.0
- **Orchestration**: Kubernetes 1.28 (production)
- **CI/CD**: GitHub Actions

### AI Providers
- **Primary**: Claude 3.5 Sonnet (Anthropic)
- **Fallback**: GPT-4o (OpenAI)
- **Cost-Effective**: Gemini 1.5 Pro (Google)

---

## Next Steps

1. **Week 4 Day 1**: ✅ C4 Architecture Diagrams Complete
2. **Week 4 Day 2**: API Specification Documentation (OpenAPI enhancement)
3. **Week 4 Day 2**: Deployment Guides (Docker, Kubernetes, AWS/GCP/Azure)
4. **Week 4 Day 3-4**: Real Integration (MinIO + OPA) - CRITICAL PATH

---

**Document Metadata**:
- **Version**: 1.0.0
- **Last Updated**: November 18, 2025
- **Status**: ACTIVE - Week 4 Day 1
- **Authority**: Solutions Architect + CTO
- **Framework**: SDLC 5.1.3 + C4 Model
- **Quality**: Production-ready architecture documentation

---

**References**:
- C4 Model: https://c4model.com/
- Mermaid C4 Diagrams: https://mermaid.js.org/syntax/c4.html
- Week 3 Complete: 23 APIs, 21 tables, 28 tests, 6,600+ lines
- Gate G2 Readiness: 95% (highest this project)
