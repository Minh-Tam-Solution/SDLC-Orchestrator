"""
=========================================================================
Seed Data Migration - NQH Real Portfolio (4 Projects)
SDLC Orchestrator - Stage 03 (BUILD)

Version: 4.0.0
Date: November 29, 2025
Status: ACTIVE - Sprint 14 Test Data
Authority: CPO + Backend Lead + CTO Approved
Foundation: SDLC 4.9.1 Complete Lifecycle
Framework: Zero Mock Policy - Real NQH Portfolio Data

Purpose:
This migration creates realistic test data based on REAL NQH projects:

1. **BFlow Platform** (PRODUCTION - Stage 09 GOVERN)
   - Started: 2022, GOLIVE: 2023
   - 200K+ users, multi-tenant HRM
   - All 10/10 gates APPROVED

2. **NQH-Bot Platform** (GOLIVE Dec 15 - Stage 05 DEPLOY)
   - AI chatbot, Vietnamese NLP
   - 6 gates (5 approved, 1 pending)

3. **SDLC-Orchestrator** (Development - Stage 03 BUILD)
   - This platform, governance tool
   - 5 gates (4 approved, 1 draft)

4. **SDLC-Enterprise-Framework** (Documentation - Stage 02 HOW)
   - Framework 4.9.1 documentation
   - 4 gates (2 approved, 2 draft)

Team: 12 users from NQH + MTS
- CEO: Tai Dang (taidt@mtsolution.com.vn)
- CPO: Dung Luong (dunglt@mtsolution.com.vn)
- CTO: Hiep Dinh (dvhiep@nqh.com.vn)
- Local Team Lead: Endior
- Remote Team Lead: Ms Hang Le
- Developers: 4 (2 Local, 2 Remote)
- QA Lead: 1
- Admin: 1

Gate Distribution: 26 total (22 approved, 1 pending, 3 draft)
Evidence: 46 records
Project Members: 35 assignments

Synchronized with: docs/04-Testing-Quality/07-E2E-Testing/NQH-PORTFOLIO-SEED-DATA.sql
=========================================================================

Revision ID: a502ce0d23a7
Revises: dce31118ffb7
Create Date: 2025-11-14 16:51:24.497047
"""
from datetime import datetime
import json
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = 'a502ce0d23a7'
down_revision: Union[str, None] = 'dce31118ffb7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Insert NQH Real Portfolio seed data.

    Data Includes:
    - 13 SDLC system roles (CEO, CTO, CPO, EM, TL, DEV, QA, DevOps, Security, PM, BA, CIO, CFO)
    - 12 users (1 admin + 11 NQH team members)
    - 4 real projects from NQH Portfolio
    - 26 gates (22 APPROVED, 1 PENDING, 3 DRAFT)
    - 46 evidence records
    - 35 project memberships
    - 4 AI providers (Ollama, Claude, GPT-4o, Gemini)
    """
    conn = op.get_bind()

    # =========================================================================
    # 1. ROLES (13 system roles)
    # Using fixed UUIDs for consistency
    # =========================================================================

    ceo_role_id = "10000000-0000-0000-0000-000000000001"
    cto_role_id = "10000000-0000-0000-0000-000000000002"
    cpo_role_id = "10000000-0000-0000-0000-000000000003"
    cio_role_id = "10000000-0000-0000-0000-000000000004"
    cfo_role_id = "10000000-0000-0000-0000-000000000005"
    em_role_id = "10000000-0000-0000-0000-000000000006"
    tl_role_id = "10000000-0000-0000-0000-000000000007"
    dev_role_id = "10000000-0000-0000-0000-000000000008"
    qa_role_id = "10000000-0000-0000-0000-000000000009"
    devops_role_id = "10000000-0000-0000-0000-000000000010"
    security_role_id = "10000000-0000-0000-0000-000000000011"
    pm_role_id = "10000000-0000-0000-0000-000000000012"
    ba_role_id = "10000000-0000-0000-0000-000000000013"

    roles_data = [
        {'id': ceo_role_id, 'name': 'ceo', 'display_name': 'Chief Executive Officer', 'description': 'Final approval authority, strategic alignment, budget decisions, go/no-go gates', 'is_active': True, 'created_at': datetime.utcnow()},
        {'id': cto_role_id, 'name': 'cto', 'display_name': 'Chief Technology Officer', 'description': 'Technical architecture review, security standards, performance requirements', 'is_active': True, 'created_at': datetime.utcnow()},
        {'id': cpo_role_id, 'name': 'cpo', 'display_name': 'Chief Product Officer', 'description': 'Product strategy, user experience, business value validation', 'is_active': True, 'created_at': datetime.utcnow()},
        {'id': cio_role_id, 'name': 'cio', 'display_name': 'Chief Information Officer', 'description': 'IT infrastructure, data governance, compliance oversight', 'is_active': True, 'created_at': datetime.utcnow()},
        {'id': cfo_role_id, 'name': 'cfo', 'display_name': 'Chief Financial Officer', 'description': 'Budget approval, financial controls, cost management', 'is_active': True, 'created_at': datetime.utcnow()},
        {'id': em_role_id, 'name': 'em', 'display_name': 'Engineering Manager', 'description': 'Team leadership, project planning, gate submissions, resource allocation', 'is_active': True, 'created_at': datetime.utcnow()},
        {'id': tl_role_id, 'name': 'tl', 'display_name': 'Tech Lead', 'description': 'Technical decisions, code review, architecture design, mentorship', 'is_active': True, 'created_at': datetime.utcnow()},
        {'id': dev_role_id, 'name': 'dev', 'display_name': 'Developer', 'description': 'Code implementation, unit testing, evidence upload, SDLC execution', 'is_active': True, 'created_at': datetime.utcnow()},
        {'id': qa_role_id, 'name': 'qa', 'display_name': 'QA Engineer', 'description': 'Test planning, quality gates, bug tracking, test automation', 'is_active': True, 'created_at': datetime.utcnow()},
        {'id': devops_role_id, 'name': 'devops', 'display_name': 'DevOps Engineer', 'description': 'CI/CD pipelines, deployment automation, infrastructure management', 'is_active': True, 'created_at': datetime.utcnow()},
        {'id': security_role_id, 'name': 'security', 'display_name': 'Security Engineer', 'description': 'Security review, vulnerability scanning, compliance verification', 'is_active': True, 'created_at': datetime.utcnow()},
        {'id': pm_role_id, 'name': 'pm', 'display_name': 'Product Manager', 'description': 'Requirements definition, roadmap planning, stakeholder communication', 'is_active': True, 'created_at': datetime.utcnow()},
        {'id': ba_role_id, 'name': 'ba', 'display_name': 'Business Analyst', 'description': 'Data analysis, metrics tracking, business intelligence, reporting', 'is_active': True, 'created_at': datetime.utcnow()},
    ]

    for role in roles_data:
        conn.execute(
            text("""
                INSERT INTO roles (id, name, display_name, description, is_active, created_at)
                VALUES (:id, :name, :display_name, :description, :is_active, :created_at)
                ON CONFLICT (id) DO NOTHING
            """),
            role
        )

    # =========================================================================
    # 2. USERS (12 users: 1 admin + 11 NQH team)
    # =========================================================================

    # Password hash for "Admin@123" (bcrypt, cost=12)
    # nosemgrep: generic.secrets.security.detected-bcrypt-hash
    # SECURITY NOTE: This is seed data for development/testing only.
    # In production, users should be created via proper onboarding flow.
    password_hash = "$2b$12$gbdaanPRphcu5qGFfd1AxuPE9tEuPDjazMcnz8oSfqDKE/T1961tm"

    admin_user_id = "a0000000-0000-0000-0000-000000000001"
    ceo_user_id = "b0000000-0000-0000-0000-000000000001"  # Tai Dang
    cpo_user_id = "b0000000-0000-0000-0000-000000000002"  # Dung Luong
    cto_user_id = "b0000000-0000-0000-0000-000000000003"  # Hiep Dinh
    local_tl_user_id = "b0000000-0000-0000-0000-000000000004"  # Endior
    remote_tl_user_id = "b0000000-0000-0000-0000-000000000005"  # Hang Le
    local_dev1_user_id = "b0000000-0000-0000-0000-000000000006"
    local_dev2_user_id = "b0000000-0000-0000-0000-000000000007"
    remote_dev1_user_id = "b0000000-0000-0000-0000-000000000008"
    remote_dev2_user_id = "b0000000-0000-0000-0000-000000000009"
    qa_lead_user_id = "b0000000-0000-0000-0000-000000000010"
    inactive_user_id = "b0000000-0000-0000-0000-000000000011"

    users_data = [
        {'id': admin_user_id, 'email': 'admin@sdlc-orchestrator.io', 'name': 'System Administrator', 'password_hash': password_hash, 'is_active': True, 'is_superuser': True, 'mfa_enabled': False, 'created_at': datetime.utcnow(), 'updated_at': datetime.utcnow()},
        {'id': ceo_user_id, 'email': 'taidt@mtsolution.com.vn', 'name': 'Tai Dang', 'password_hash': password_hash, 'is_active': True, 'is_superuser': False, 'mfa_enabled': False, 'created_at': datetime.utcnow(), 'updated_at': datetime.utcnow()},
        {'id': cpo_user_id, 'email': 'dunglt@mtsolution.com.vn', 'name': 'Dung Luong', 'password_hash': password_hash, 'is_active': True, 'is_superuser': False, 'mfa_enabled': False, 'created_at': datetime.utcnow(), 'updated_at': datetime.utcnow()},
        {'id': cto_user_id, 'email': 'dvhiep@nqh.com.vn', 'name': 'Hiep Dinh', 'password_hash': password_hash, 'is_active': True, 'is_superuser': False, 'mfa_enabled': False, 'created_at': datetime.utcnow(), 'updated_at': datetime.utcnow()},
        {'id': local_tl_user_id, 'email': 'dangtt1971@gmail.com', 'name': 'Endior', 'password_hash': password_hash, 'is_active': True, 'is_superuser': False, 'mfa_enabled': False, 'created_at': datetime.utcnow(), 'updated_at': datetime.utcnow()},
        {'id': remote_tl_user_id, 'email': 'ltmhang@nqh.com.vn', 'name': 'Hang Le', 'password_hash': password_hash, 'is_active': True, 'is_superuser': False, 'mfa_enabled': False, 'created_at': datetime.utcnow(), 'updated_at': datetime.utcnow()},
        {'id': local_dev1_user_id, 'email': 'local.dev1@nqh.com.vn', 'name': 'Minh Nguyen', 'password_hash': password_hash, 'is_active': True, 'is_superuser': False, 'mfa_enabled': False, 'created_at': datetime.utcnow(), 'updated_at': datetime.utcnow()},
        {'id': local_dev2_user_id, 'email': 'local.dev2@nqh.com.vn', 'name': 'Tuan Tran', 'password_hash': password_hash, 'is_active': True, 'is_superuser': False, 'mfa_enabled': False, 'created_at': datetime.utcnow(), 'updated_at': datetime.utcnow()},
        {'id': remote_dev1_user_id, 'email': 'remote.dev1@nqh.com.vn', 'name': 'Linh Pham', 'password_hash': password_hash, 'is_active': True, 'is_superuser': False, 'mfa_enabled': False, 'created_at': datetime.utcnow(), 'updated_at': datetime.utcnow()},
        {'id': remote_dev2_user_id, 'email': 'remote.dev2@nqh.com.vn', 'name': 'Hoa Vu', 'password_hash': password_hash, 'is_active': True, 'is_superuser': False, 'mfa_enabled': False, 'created_at': datetime.utcnow(), 'updated_at': datetime.utcnow()},
        {'id': qa_lead_user_id, 'email': 'qa.lead@nqh.com.vn', 'name': 'Thu Ha', 'password_hash': password_hash, 'is_active': True, 'is_superuser': False, 'mfa_enabled': False, 'created_at': datetime.utcnow(), 'updated_at': datetime.utcnow()},
        {'id': inactive_user_id, 'email': 'inactive@nqh.com.vn', 'name': 'Inactive User', 'password_hash': password_hash, 'is_active': False, 'is_superuser': False, 'mfa_enabled': False, 'created_at': datetime.utcnow(), 'updated_at': datetime.utcnow()},
    ]

    for user in users_data:
        conn.execute(
            text("""
                INSERT INTO users (id, email, name, password_hash, is_active, is_superuser,
                                 mfa_enabled, created_at, updated_at)
                VALUES (:id, :email, :name, :password_hash, :is_active, :is_superuser,
                        :mfa_enabled, :created_at, :updated_at)
                ON CONFLICT (id) DO NOTHING
            """),
            user
        )

    # =========================================================================
    # 3. PROJECTS (4 from Real NQH Portfolio)
    # =========================================================================

    # Project 1: BFlow Platform (PRODUCTION - Complete Lifecycle)
    bflow_project_id = "c0000000-0000-0000-0000-000000000001"

    # Project 2: NQH-Bot Platform (GOLIVE Dec 15)
    nqhbot_project_id = "c0000000-0000-0000-0000-000000000002"

    # Project 3: SDLC-Orchestrator (This Platform)
    sdlco_project_id = "c0000000-0000-0000-0000-000000000003"

    # Project 4: SDLC-Enterprise-Framework (Documentation)
    framework_project_id = "c0000000-0000-0000-0000-000000000004"

    projects_data = [
        {
            'id': bflow_project_id,
            'name': 'BFlow Platform',
            'slug': 'bflow-platform',
            'description': '''Multi-tenant HRM platform for Vietnamese enterprises. 200K+ users across 50+ companies.
Features: Payroll, Leave Management, Performance Reviews, Employee Self-Service.
Tech Stack: Python/FastAPI, React, PostgreSQL, Redis, Kubernetes.
Status: PRODUCTION since March 2023. SDLC 4.9 showcase project.''',
            'owner_id': ceo_user_id,
            'is_active': True,
            'created_at': datetime(2022, 1, 15, 9, 0, 0),
            'updated_at': datetime(2023, 3, 1, 10, 0, 0),
        },
        {
            'id': nqhbot_project_id,
            'name': 'NQH-Bot Platform',
            'slug': 'nqh-bot-platform',
            'description': '''AI-powered chatbot platform for enterprise automation. Multi-channel (Telegram, Zalo, Facebook).
Features: Vietnamese NLP, CRM Integration, Analytics Dashboard, Multi-tenant.
Tech Stack: Python/FastAPI, React, PostgreSQL, Ollama AI, Redis.
Status: GOLIVE Dec 15, 2025. Target: 10K conversations/day.''',
            'owner_id': ceo_user_id,
            'is_active': True,
            'created_at': datetime(2025, 9, 1, 9, 0, 0),
            'updated_at': datetime.utcnow(),
        },
        {
            'id': sdlco_project_id,
            'name': 'SDLC-Orchestrator',
            'slug': 'sdlc-orchestrator',
            'description': '''Governance-first platform built on SDLC 4.9.1 Complete Lifecycle methodology.
Features: Quality Gates, Evidence Vault, AI Context Engine, GitHub Bridge.
Tech Stack: Python/FastAPI, React/TypeScript, PostgreSQL, OPA, MinIO.
Status: MVP Development. Target: G6 Internal Validation by Week 17.''',
            'owner_id': cto_user_id,
            'is_active': True,
            'created_at': datetime(2025, 11, 13, 9, 0, 0),
            'updated_at': datetime.utcnow(),
        },
        {
            'id': framework_project_id,
            'name': 'SDLC-Enterprise-Framework',
            'slug': 'sdlc-enterprise-framework',
            'description': '''SDLC 4.9.1 Complete Lifecycle Framework documentation and training materials.
Features: 10-Stage Lifecycle, 6 Universal Pillars, Zero Mock Policy, Stage-Gate Templates.
Format: Markdown documentation, policy templates, training guides.
Status: Active documentation. Used by all NQH development teams.''',
            'owner_id': cpo_user_id,
            'is_active': True,
            'created_at': datetime(2024, 6, 1, 9, 0, 0),
            'updated_at': datetime.utcnow(),
        },
    ]

    for project in projects_data:
        conn.execute(
            text("""
                INSERT INTO projects (id, name, slug, description, owner_id, is_active, created_at, updated_at)
                VALUES (:id, :name, :slug, :description, :owner_id, :is_active, :created_at, :updated_at)
                ON CONFLICT (id) DO UPDATE SET updated_at = NOW()
            """),
            project
        )

    # =========================================================================
    # 4. PROJECT MEMBERS (35 assignments)
    # =========================================================================

    member_id_counter = 1

    def next_member_id():
        nonlocal member_id_counter
        mid = f"d0000000-0000-0000-0000-{str(member_id_counter).zfill(12)}"
        member_id_counter += 1
        return mid

    project_members_data = [
        # BFlow Platform (11 members - full team)
        {'id': next_member_id(), 'project_id': bflow_project_id, 'user_id': ceo_user_id, 'role': 'owner', 'invited_by': None, 'invited_at': datetime(2022, 1, 15), 'joined_at': datetime(2022, 1, 15), 'created_at': datetime(2022, 1, 15)},
        {'id': next_member_id(), 'project_id': bflow_project_id, 'user_id': cpo_user_id, 'role': 'admin', 'invited_by': ceo_user_id, 'invited_at': datetime(2022, 1, 16), 'joined_at': datetime(2022, 1, 16), 'created_at': datetime(2022, 1, 16)},
        {'id': next_member_id(), 'project_id': bflow_project_id, 'user_id': cto_user_id, 'role': 'admin', 'invited_by': ceo_user_id, 'invited_at': datetime(2022, 1, 16), 'joined_at': datetime(2022, 1, 16), 'created_at': datetime(2022, 1, 16)},
        {'id': next_member_id(), 'project_id': bflow_project_id, 'user_id': local_tl_user_id, 'role': 'admin', 'invited_by': cto_user_id, 'invited_at': datetime(2022, 2, 1), 'joined_at': datetime(2022, 2, 1), 'created_at': datetime(2022, 2, 1)},
        {'id': next_member_id(), 'project_id': bflow_project_id, 'user_id': remote_tl_user_id, 'role': 'admin', 'invited_by': cto_user_id, 'invited_at': datetime(2022, 2, 1), 'joined_at': datetime(2022, 2, 1), 'created_at': datetime(2022, 2, 1)},
        {'id': next_member_id(), 'project_id': bflow_project_id, 'user_id': local_dev1_user_id, 'role': 'member', 'invited_by': local_tl_user_id, 'invited_at': datetime(2022, 3, 1), 'joined_at': datetime(2022, 3, 1), 'created_at': datetime(2022, 3, 1)},
        {'id': next_member_id(), 'project_id': bflow_project_id, 'user_id': local_dev2_user_id, 'role': 'member', 'invited_by': local_tl_user_id, 'invited_at': datetime(2022, 3, 1), 'joined_at': datetime(2022, 3, 1), 'created_at': datetime(2022, 3, 1)},
        {'id': next_member_id(), 'project_id': bflow_project_id, 'user_id': remote_dev1_user_id, 'role': 'member', 'invited_by': remote_tl_user_id, 'invited_at': datetime(2022, 3, 1), 'joined_at': datetime(2022, 3, 1), 'created_at': datetime(2022, 3, 1)},
        {'id': next_member_id(), 'project_id': bflow_project_id, 'user_id': remote_dev2_user_id, 'role': 'member', 'invited_by': remote_tl_user_id, 'invited_at': datetime(2022, 3, 1), 'joined_at': datetime(2022, 3, 1), 'created_at': datetime(2022, 3, 1)},
        {'id': next_member_id(), 'project_id': bflow_project_id, 'user_id': qa_lead_user_id, 'role': 'member', 'invited_by': cto_user_id, 'invited_at': datetime(2022, 4, 1), 'joined_at': datetime(2022, 4, 1), 'created_at': datetime(2022, 4, 1)},
        {'id': next_member_id(), 'project_id': bflow_project_id, 'user_id': admin_user_id, 'role': 'admin', 'invited_by': None, 'invited_at': datetime.utcnow(), 'joined_at': datetime.utcnow(), 'created_at': datetime.utcnow()},

        # NQH-Bot Platform (11 members - full team)
        {'id': next_member_id(), 'project_id': nqhbot_project_id, 'user_id': ceo_user_id, 'role': 'owner', 'invited_by': None, 'invited_at': datetime(2025, 9, 1), 'joined_at': datetime(2025, 9, 1), 'created_at': datetime(2025, 9, 1)},
        {'id': next_member_id(), 'project_id': nqhbot_project_id, 'user_id': cpo_user_id, 'role': 'admin', 'invited_by': ceo_user_id, 'invited_at': datetime(2025, 9, 1), 'joined_at': datetime(2025, 9, 1), 'created_at': datetime(2025, 9, 1)},
        {'id': next_member_id(), 'project_id': nqhbot_project_id, 'user_id': cto_user_id, 'role': 'admin', 'invited_by': ceo_user_id, 'invited_at': datetime(2025, 9, 1), 'joined_at': datetime(2025, 9, 1), 'created_at': datetime(2025, 9, 1)},
        {'id': next_member_id(), 'project_id': nqhbot_project_id, 'user_id': local_tl_user_id, 'role': 'admin', 'invited_by': cto_user_id, 'invited_at': datetime(2025, 9, 5), 'joined_at': datetime(2025, 9, 5), 'created_at': datetime(2025, 9, 5)},
        {'id': next_member_id(), 'project_id': nqhbot_project_id, 'user_id': remote_tl_user_id, 'role': 'admin', 'invited_by': cto_user_id, 'invited_at': datetime(2025, 9, 5), 'joined_at': datetime(2025, 9, 5), 'created_at': datetime(2025, 9, 5)},
        {'id': next_member_id(), 'project_id': nqhbot_project_id, 'user_id': local_dev1_user_id, 'role': 'member', 'invited_by': local_tl_user_id, 'invited_at': datetime(2025, 9, 10), 'joined_at': datetime(2025, 9, 10), 'created_at': datetime(2025, 9, 10)},
        {'id': next_member_id(), 'project_id': nqhbot_project_id, 'user_id': local_dev2_user_id, 'role': 'member', 'invited_by': local_tl_user_id, 'invited_at': datetime(2025, 9, 10), 'joined_at': datetime(2025, 9, 10), 'created_at': datetime(2025, 9, 10)},
        {'id': next_member_id(), 'project_id': nqhbot_project_id, 'user_id': remote_dev1_user_id, 'role': 'member', 'invited_by': remote_tl_user_id, 'invited_at': datetime(2025, 9, 10), 'joined_at': datetime(2025, 9, 10), 'created_at': datetime(2025, 9, 10)},
        {'id': next_member_id(), 'project_id': nqhbot_project_id, 'user_id': remote_dev2_user_id, 'role': 'member', 'invited_by': remote_tl_user_id, 'invited_at': datetime(2025, 9, 10), 'joined_at': datetime(2025, 9, 10), 'created_at': datetime(2025, 9, 10)},
        {'id': next_member_id(), 'project_id': nqhbot_project_id, 'user_id': qa_lead_user_id, 'role': 'member', 'invited_by': cto_user_id, 'invited_at': datetime(2025, 9, 15), 'joined_at': datetime(2025, 9, 15), 'created_at': datetime(2025, 9, 15)},
        {'id': next_member_id(), 'project_id': nqhbot_project_id, 'user_id': admin_user_id, 'role': 'admin', 'invited_by': None, 'invited_at': datetime.utcnow(), 'joined_at': datetime.utcnow(), 'created_at': datetime.utcnow()},

        # SDLC-Orchestrator (8 members - core team)
        {'id': next_member_id(), 'project_id': sdlco_project_id, 'user_id': cto_user_id, 'role': 'owner', 'invited_by': None, 'invited_at': datetime(2025, 11, 13), 'joined_at': datetime(2025, 11, 13), 'created_at': datetime(2025, 11, 13)},
        {'id': next_member_id(), 'project_id': sdlco_project_id, 'user_id': ceo_user_id, 'role': 'admin', 'invited_by': cto_user_id, 'invited_at': datetime(2025, 11, 13), 'joined_at': datetime(2025, 11, 13), 'created_at': datetime(2025, 11, 13)},
        {'id': next_member_id(), 'project_id': sdlco_project_id, 'user_id': cpo_user_id, 'role': 'admin', 'invited_by': cto_user_id, 'invited_at': datetime(2025, 11, 13), 'joined_at': datetime(2025, 11, 13), 'created_at': datetime(2025, 11, 13)},
        {'id': next_member_id(), 'project_id': sdlco_project_id, 'user_id': local_tl_user_id, 'role': 'admin', 'invited_by': cto_user_id, 'invited_at': datetime(2025, 11, 14), 'joined_at': datetime(2025, 11, 14), 'created_at': datetime(2025, 11, 14)},
        {'id': next_member_id(), 'project_id': sdlco_project_id, 'user_id': local_dev1_user_id, 'role': 'member', 'invited_by': local_tl_user_id, 'invited_at': datetime(2025, 11, 15), 'joined_at': datetime(2025, 11, 15), 'created_at': datetime(2025, 11, 15)},
        {'id': next_member_id(), 'project_id': sdlco_project_id, 'user_id': remote_dev1_user_id, 'role': 'member', 'invited_by': local_tl_user_id, 'invited_at': datetime(2025, 11, 15), 'joined_at': datetime(2025, 11, 15), 'created_at': datetime(2025, 11, 15)},
        {'id': next_member_id(), 'project_id': sdlco_project_id, 'user_id': qa_lead_user_id, 'role': 'member', 'invited_by': cto_user_id, 'invited_at': datetime(2025, 11, 18), 'joined_at': datetime(2025, 11, 18), 'created_at': datetime(2025, 11, 18)},
        {'id': next_member_id(), 'project_id': sdlco_project_id, 'user_id': admin_user_id, 'role': 'admin', 'invited_by': None, 'invited_at': datetime.utcnow(), 'joined_at': datetime.utcnow(), 'created_at': datetime.utcnow()},

        # SDLC-Enterprise-Framework (5 members - doc team)
        {'id': next_member_id(), 'project_id': framework_project_id, 'user_id': cpo_user_id, 'role': 'owner', 'invited_by': None, 'invited_at': datetime(2024, 6, 1), 'joined_at': datetime(2024, 6, 1), 'created_at': datetime(2024, 6, 1)},
        {'id': next_member_id(), 'project_id': framework_project_id, 'user_id': ceo_user_id, 'role': 'admin', 'invited_by': cpo_user_id, 'invited_at': datetime(2024, 6, 1), 'joined_at': datetime(2024, 6, 1), 'created_at': datetime(2024, 6, 1)},
        {'id': next_member_id(), 'project_id': framework_project_id, 'user_id': cto_user_id, 'role': 'admin', 'invited_by': cpo_user_id, 'invited_at': datetime(2024, 6, 1), 'joined_at': datetime(2024, 6, 1), 'created_at': datetime(2024, 6, 1)},
        {'id': next_member_id(), 'project_id': framework_project_id, 'user_id': local_tl_user_id, 'role': 'member', 'invited_by': cpo_user_id, 'invited_at': datetime(2024, 6, 15), 'joined_at': datetime(2024, 6, 15), 'created_at': datetime(2024, 6, 15)},
        {'id': next_member_id(), 'project_id': framework_project_id, 'user_id': admin_user_id, 'role': 'admin', 'invited_by': None, 'invited_at': datetime.utcnow(), 'joined_at': datetime.utcnow(), 'created_at': datetime.utcnow()},
    ]

    for member in project_members_data:
        conn.execute(
            text("""
                INSERT INTO project_members (id, project_id, user_id, role, invited_by, invited_at, joined_at, created_at)
                VALUES (:id, :project_id, :user_id, :role, :invited_by, :invited_at, :joined_at, :created_at)
                ON CONFLICT (id) DO NOTHING
            """),
            member
        )

    # =========================================================================
    # 5. USER ROLES (Assign system roles to users)
    # =========================================================================

    user_roles_data = [
        {'user_id': ceo_user_id, 'role_id': ceo_role_id},
        {'user_id': cpo_user_id, 'role_id': cpo_role_id},
        {'user_id': cto_user_id, 'role_id': cto_role_id},
        {'user_id': local_tl_user_id, 'role_id': tl_role_id},
        {'user_id': remote_tl_user_id, 'role_id': tl_role_id},
        {'user_id': local_dev1_user_id, 'role_id': dev_role_id},
        {'user_id': local_dev2_user_id, 'role_id': dev_role_id},
        {'user_id': remote_dev1_user_id, 'role_id': dev_role_id},
        {'user_id': remote_dev2_user_id, 'role_id': dev_role_id},
        {'user_id': qa_lead_user_id, 'role_id': qa_role_id},
    ]

    for user_role in user_roles_data:
        conn.execute(
            text("""
                INSERT INTO user_roles (user_id, role_id)
                VALUES (:user_id, :role_id)
                ON CONFLICT DO NOTHING
            """),
            user_role
        )

    # =========================================================================
    # 6. AI PROVIDERS (4 providers: Ollama, Claude, GPT-4o, Gemini)
    # =========================================================================

    ai_providers_data = [
        {
            'id': '90000000-0000-0000-0000-000000000001',
            'provider_name': 'NQH Ollama',
            'provider_type': 'ollama',
            'model_name': 'qwen3-coder:30b',
            'api_key_encrypted': '',
            'cost_per_1k_input_tokens': 0.00005,  # $0.05/1M = 95% savings
            'cost_per_1k_output_tokens': 0.00015,
            'max_tokens': 32768,
            'temperature': 0.7,
            'priority': 1,  # PRIMARY - lowest cost, fastest
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
        },
        {
            'id': '90000000-0000-0000-0000-000000000002',
            'provider_name': 'Anthropic',
            'provider_type': 'claude',
            'model_name': 'claude-sonnet-4-5-20250929',
            'api_key_encrypted': '',
            'cost_per_1k_input_tokens': 0.003,
            'cost_per_1k_output_tokens': 0.015,
            'max_tokens': 8192,
            'temperature': 0.7,
            'priority': 2,  # Fallback 1
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
        },
        {
            'id': '90000000-0000-0000-0000-000000000003',
            'provider_name': 'OpenAI',
            'provider_type': 'gpt',
            'model_name': 'gpt-4o-2024-11-20',
            'api_key_encrypted': '',
            'cost_per_1k_input_tokens': 0.0025,
            'cost_per_1k_output_tokens': 0.010,
            'max_tokens': 16384,
            'temperature': 0.7,
            'priority': 3,  # Fallback 2
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
        },
        {
            'id': '90000000-0000-0000-0000-000000000004',
            'provider_name': 'Google',
            'provider_type': 'gemini',
            'model_name': 'gemini-2.0-flash-exp',
            'api_key_encrypted': '',
            'cost_per_1k_input_tokens': 0.000075,
            'cost_per_1k_output_tokens': 0.0003,
            'max_tokens': 8192,
            'temperature': 0.7,
            'priority': 4,  # Fallback 3
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
        },
    ]

    for provider in ai_providers_data:
        conn.execute(
            text("""
                INSERT INTO ai_providers (id, provider_name, provider_type, model_name,
                                        api_key_encrypted, cost_per_1k_input_tokens,
                                        cost_per_1k_output_tokens, max_tokens, temperature,
                                        priority, is_active, created_at, updated_at)
                VALUES (:id, :provider_name, :provider_type, :model_name,
                        :api_key_encrypted, :cost_per_1k_input_tokens,
                        :cost_per_1k_output_tokens, :max_tokens, :temperature,
                        :priority, :is_active, :created_at, :updated_at)
                ON CONFLICT (id) DO NOTHING
            """),
            provider
        )

    # =========================================================================
    # 7. GATES (26 gates across 4 projects)
    # =========================================================================

    gate_id_counter = 1

    def next_gate_id():
        nonlocal gate_id_counter
        gid = f"e0000000-0000-0000-0000-{str(gate_id_counter).zfill(12)}"
        gate_id_counter += 1
        return gid

    gates_data = []

    # -----------------------------------------------------------------------
    # BFlow Platform - ALL 10 GATES APPROVED (Complete Lifecycle 2022-2023)
    # -----------------------------------------------------------------------
    gates_data.extend([
        {
            'id': next_gate_id(),
            'project_id': bflow_project_id,
            'gate_name': 'G0.1',
            'gate_type': 'PROBLEM_DEFINITION',
            'stage': 'WHY',
            'status': 'APPROVED',
            'created_by': ceo_user_id,
            'exit_criteria': ['Problem statement: Vietnamese SMEs lack affordable HRM', 'User personas: HR Manager, Employee, Payroll Admin', 'Market: $500M VN HRM market, 30% CAGR'],
            'created_at': datetime(2022, 1, 20, 10, 0, 0),
            'updated_at': datetime(2022, 1, 25, 15, 0, 0),
            'approved_at': datetime(2022, 1, 25, 15, 0, 0),
            'description': 'Problem validated: 70% of VN SMEs use manual HR processes. Average payroll processing: 8 hours/month.',
        },
        {
            'id': next_gate_id(),
            'project_id': bflow_project_id,
            'gate_name': 'G0.2',
            'gate_type': 'SOLUTION_DIVERSITY',
            'stage': 'WHY',
            'status': 'APPROVED',
            'created_by': ceo_user_id,
            'exit_criteria': ['5 solutions evaluated', 'Multi-tenant SaaS selected', 'ROI: 400% Year 1'],
            'created_at': datetime(2022, 1, 28, 10, 0, 0),
            'updated_at': datetime(2022, 2, 5, 16, 0, 0),
            'approved_at': datetime(2022, 2, 5, 16, 0, 0),
            'description': 'Selected: Multi-tenant SaaS with Vietnamese localization. Rejected: On-prem, white-label, marketplace model.',
        },
        {
            'id': next_gate_id(),
            'project_id': bflow_project_id,
            'gate_name': 'G1',
            'gate_type': 'PLANNING_COMPLETE',
            'stage': 'WHAT',
            'status': 'APPROVED',
            'created_by': cpo_user_id,
            'exit_criteria': ['FRD complete (45 FRs)', 'API spec (3,200 lines)', 'Data model (52 tables)'],
            'created_at': datetime(2022, 2, 15, 9, 0, 0),
            'updated_at': datetime(2022, 3, 1, 14, 0, 0),
            'approved_at': datetime(2022, 3, 1, 14, 0, 0),
            'description': 'FRD approved: Payroll (BHXH, TNCN), Leave, Performance, Employee Portal. Vietnamese tax compliance built-in.',
        },
        {
            'id': next_gate_id(),
            'project_id': bflow_project_id,
            'gate_name': 'G2',
            'gate_type': 'DESIGN_READY',
            'stage': 'HOW',
            'status': 'APPROVED',
            'created_by': cto_user_id,
            'exit_criteria': ['Architecture approved', 'Security OWASP ASVS L2', 'Multi-tenant isolation design'],
            'created_at': datetime(2022, 3, 10, 10, 0, 0),
            'updated_at': datetime(2022, 4, 15, 17, 0, 0),
            'approved_at': datetime(2022, 4, 15, 17, 0, 0),
            'description': 'Microservices architecture. Row-level security for multi-tenancy. Vietnamese encoding (UTF-8 + diacritics).',
        },
        {
            'id': next_gate_id(),
            'project_id': bflow_project_id,
            'gate_name': 'G3',
            'gate_type': 'SHIP_READY',
            'stage': 'BUILD',
            'status': 'APPROVED',
            'created_by': cto_user_id,
            'exit_criteria': ['Core features implemented', 'Unit tests 92%', 'Integration tests 88%'],
            'created_at': datetime(2022, 5, 1, 8, 0, 0),
            'updated_at': datetime(2022, 7, 1, 18, 0, 0),
            'approved_at': datetime(2022, 7, 1, 18, 0, 0),
            'description': 'MVP complete: Payroll, Leave, Employee Portal. 15,000 lines backend, 12,000 lines frontend.',
        },
        {
            'id': next_gate_id(),
            'project_id': bflow_project_id,
            'gate_name': 'G4',
            'gate_type': 'TEST_COMPLETE',
            'stage': 'VERIFY',
            'status': 'APPROVED',
            'created_by': qa_lead_user_id,
            'exit_criteria': ['E2E tests 85%', 'Performance: <200ms p95', 'UAT sign-off: 9.2/10'],
            'created_at': datetime(2022, 7, 15, 8, 0, 0),
            'updated_at': datetime(2022, 8, 15, 18, 0, 0),
            'approved_at': datetime(2022, 8, 15, 18, 0, 0),
            'description': 'QA complete: 285 test cases, 98% pass rate. Performance: 45ms p50, 120ms p95. UAT with 3 pilot companies.',
        },
        {
            'id': next_gate_id(),
            'project_id': bflow_project_id,
            'gate_name': 'G5',
            'gate_type': 'DEPLOY_READY',
            'stage': 'DEPLOY',
            'status': 'APPROVED',
            'created_by': cto_user_id,
            'exit_criteria': ['Deployment plan approved', 'Rollback tested (<5min)', 'War room scheduled'],
            'created_at': datetime(2022, 8, 20, 8, 0, 0),
            'updated_at': datetime(2022, 9, 1, 18, 0, 0),
            'approved_at': datetime(2022, 9, 1, 18, 0, 0),
            'description': 'Blue-green deployment. Kubernetes with auto-scaling. Rollback tested: 3.5 minutes.',
        },
        {
            'id': next_gate_id(),
            'project_id': bflow_project_id,
            'gate_name': 'G6',
            'gate_type': 'OPERATE_READY',
            'stage': 'OPERATE',
            'status': 'APPROVED',
            'created_by': ceo_user_id,
            'exit_criteria': ['Runbook complete', 'Monitoring active', 'On-call rotation set'],
            'created_at': datetime(2022, 9, 15, 8, 0, 0),
            'updated_at': datetime(2022, 10, 1, 18, 0, 0),
            'approved_at': datetime(2022, 10, 1, 18, 0, 0),
            'description': 'Production since Oct 1, 2022. Uptime: 99.95%. Incident response: <15min P1.',
        },
        {
            'id': next_gate_id(),
            'project_id': bflow_project_id,
            'gate_name': 'G7',
            'gate_type': 'INTEGRATION_COMPLETE',
            'stage': 'INTEGRATE',
            'status': 'APPROVED',
            'created_by': cto_user_id,
            'exit_criteria': ['Bank integration (VCB, Techcombank)', 'BHXH API integration', 'Tax authority eTax'],
            'created_at': datetime(2022, 10, 15, 8, 0, 0),
            'updated_at': datetime(2022, 11, 15, 18, 0, 0),
            'approved_at': datetime(2022, 11, 15, 18, 0, 0),
            'description': 'Integrated with 5 Vietnamese banks, BHXH portal, eTax system. 50K transactions/month.',
        },
        {
            'id': next_gate_id(),
            'project_id': bflow_project_id,
            'gate_name': 'G8',
            'gate_type': 'COLLABORATION_COMPLETE',
            'stage': 'COLLABORATE',
            'status': 'APPROVED',
            'created_by': cpo_user_id,
            'exit_criteria': ['Knowledge transfer complete', 'Support team trained', 'Documentation 95%'],
            'created_at': datetime(2022, 12, 1, 8, 0, 0),
            'updated_at': datetime(2023, 1, 1, 18, 0, 0),
            'approved_at': datetime(2023, 1, 1, 18, 0, 0),
            'description': 'Support team: 5 people trained. Documentation: 120 pages. Knowledge base: 200 articles.',
        },
        {
            'id': next_gate_id(),
            'project_id': bflow_project_id,
            'gate_name': 'G9',
            'gate_type': 'GOVERNANCE_COMPLETE',
            'stage': 'GOVERN',
            'status': 'APPROVED',
            'created_by': ceo_user_id,
            'exit_criteria': ['Compliance audit passed', 'Security certification', 'Executive sign-off'],
            'created_at': datetime(2023, 1, 15, 8, 0, 0),
            'updated_at': datetime(2023, 3, 1, 18, 0, 0),
            'approved_at': datetime(2023, 3, 1, 18, 0, 0),
            'description': 'Full lifecycle complete. ISO 27001 prep started. GDPR compliant for EU expansion. 200K+ users.',
        },
    ])

    # -----------------------------------------------------------------------
    # NQH-Bot Platform - 6 GATES (5 approved, 1 pending)
    # -----------------------------------------------------------------------
    gates_data.extend([
        {
            'id': next_gate_id(),
            'project_id': nqhbot_project_id,
            'gate_name': 'G0.1',
            'gate_type': 'PROBLEM_DEFINITION',
            'stage': 'WHY',
            'status': 'APPROVED',
            'created_by': ceo_user_id,
            'exit_criteria': ['Problem: 40% chatbot failure rate in Vietnamese', 'User personas defined', 'Market: $2B VN chatbot market'],
            'created_at': datetime(2025, 9, 5, 10, 0, 0),
            'updated_at': datetime(2025, 9, 10, 15, 0, 0),
            'approved_at': datetime(2025, 9, 10, 15, 0, 0),
            'description': 'Problem validated: Enterprise chatbots have 40% failure rate in Vietnamese NLP. 70% user drop-off.',
        },
        {
            'id': next_gate_id(),
            'project_id': nqhbot_project_id,
            'gate_name': 'G0.2',
            'gate_type': 'SOLUTION_DIVERSITY',
            'stage': 'WHY',
            'status': 'APPROVED',
            'created_by': ceo_user_id,
            'exit_criteria': ['5 solutions evaluated', 'Ollama + Claude hybrid selected', 'ROI: 300% Year 1'],
            'created_at': datetime(2025, 9, 10, 10, 0, 0),
            'updated_at': datetime(2025, 9, 15, 16, 0, 0),
            'approved_at': datetime(2025, 9, 15, 16, 0, 0),
            'description': 'Hybrid AI: Ollama (local, $50/month) + Claude fallback. Multi-channel (Telegram, Zalo, Facebook).',
        },
        {
            'id': next_gate_id(),
            'project_id': nqhbot_project_id,
            'gate_name': 'G1',
            'gate_type': 'PLANNING_COMPLETE',
            'stage': 'WHAT',
            'status': 'APPROVED',
            'created_by': cpo_user_id,
            'exit_criteria': ['FRD complete (25 FRs)', 'API spec (2,100 lines)', 'Data model (35 tables)'],
            'created_at': datetime(2025, 9, 20, 9, 0, 0),
            'updated_at': datetime(2025, 9, 30, 14, 0, 0),
            'approved_at': datetime(2025, 9, 30, 14, 0, 0),
            'description': 'FRD: Multi-channel messaging, Vietnamese NLP, CRM integration, Analytics dashboard.',
        },
        {
            'id': next_gate_id(),
            'project_id': nqhbot_project_id,
            'gate_name': 'G2',
            'gate_type': 'DESIGN_READY',
            'stage': 'HOW',
            'status': 'APPROVED',
            'created_by': cto_user_id,
            'exit_criteria': ['Architecture approved', 'OWASP ASVS L2', 'Vietnamese NLP pipeline designed'],
            'created_at': datetime(2025, 10, 5, 10, 0, 0),
            'updated_at': datetime(2025, 10, 15, 17, 0, 0),
            'approved_at': datetime(2025, 10, 15, 17, 0, 0),
            'description': 'Event-driven architecture. Ollama integration at api.nhatquangholding.com. Multi-tenant design.',
        },
        {
            'id': next_gate_id(),
            'project_id': nqhbot_project_id,
            'gate_name': 'G3',
            'gate_type': 'SHIP_READY',
            'stage': 'BUILD',
            'status': 'APPROVED',
            'created_by': local_tl_user_id,
            'exit_criteria': ['MVP complete', 'Unit tests 90%', 'NLP accuracy 85%+'],
            'created_at': datetime(2025, 10, 20, 8, 0, 0),
            'updated_at': datetime(2025, 11, 15, 18, 0, 0),
            'approved_at': datetime(2025, 11, 15, 18, 0, 0),
            'description': 'MVP 100% complete. Telegram + Zalo working. Vietnamese NLP: 87% accuracy. Ready for GOLIVE.',
        },
        {
            'id': next_gate_id(),
            'project_id': nqhbot_project_id,
            'gate_name': 'G5',
            'gate_type': 'DEPLOY_READY',
            'stage': 'DEPLOY',
            'status': 'PENDING_APPROVAL',
            'created_by': cto_user_id,
            'exit_criteria': ['Deployment plan ready', 'Rollback tested', 'GOLIVE Dec 15 scheduled'],
            'created_at': datetime(2025, 11, 20, 8, 0, 0),
            'updated_at': datetime.utcnow(),
            'approved_at': None,
            'description': 'GOLIVE Dec 15 target. Deployment to k8s cluster. Load testing: 10K req/min. Awaiting final approval.',
        },
    ])

    # -----------------------------------------------------------------------
    # SDLC-Orchestrator - 5 GATES (4 approved, 1 draft)
    # -----------------------------------------------------------------------
    gates_data.extend([
        {
            'id': next_gate_id(),
            'project_id': sdlco_project_id,
            'gate_name': 'G0.1',
            'gate_type': 'PROBLEM_DEFINITION',
            'stage': 'WHY',
            'status': 'APPROVED',
            'created_by': ceo_user_id,
            'exit_criteria': ['Problem: 60-70% feature waste', 'User personas: Dev Team, PM, Executive', 'Market: Governance gap'],
            'created_at': datetime(2025, 11, 13, 10, 0, 0),
            'updated_at': datetime(2025, 11, 14, 15, 0, 0),
            'approved_at': datetime(2025, 11, 14, 15, 0, 0),
            'description': 'Problem: Software teams waste 60-70% of features. SDLC 4.9.1 needs enforcement platform.',
        },
        {
            'id': next_gate_id(),
            'project_id': sdlco_project_id,
            'gate_name': 'G0.2',
            'gate_type': 'SOLUTION_DIVERSITY',
            'stage': 'WHY',
            'status': 'APPROVED',
            'created_by': ceo_user_id,
            'exit_criteria': ['5 alternatives evaluated', 'Bridge-first approach selected', 'AGPL containment validated'],
            'created_at': datetime(2025, 11, 14, 10, 0, 0),
            'updated_at': datetime(2025, 11, 15, 16, 0, 0),
            'approved_at': datetime(2025, 11, 15, 16, 0, 0),
            'description': 'Bridge-first: Governance layer over GitHub/Jira. OPA for Policy-as-Code. MinIO for Evidence Vault.',
        },
        {
            'id': next_gate_id(),
            'project_id': sdlco_project_id,
            'gate_name': 'G1',
            'gate_type': 'PLANNING_COMPLETE',
            'stage': 'WHAT',
            'status': 'APPROVED',
            'created_by': cpo_user_id,
            'exit_criteria': ['FRD complete (20 FRs)', 'OpenAPI spec (1,629 lines)', 'Data model (24 tables)'],
            'created_at': datetime(2025, 11, 18, 9, 0, 0),
            'updated_at': datetime(2025, 11, 20, 14, 0, 0),
            'approved_at': datetime(2025, 11, 20, 14, 0, 0),
            'description': 'FRD: Gate Engine, Evidence Vault, AI Context Engine, GitHub Bridge. Contract-first API design.',
        },
        {
            'id': next_gate_id(),
            'project_id': sdlco_project_id,
            'gate_name': 'G2',
            'gate_type': 'DESIGN_READY',
            'stage': 'HOW',
            'status': 'APPROVED',
            'created_by': cto_user_id,
            'exit_criteria': ['4-layer architecture approved', 'Security baseline OWASP ASVS L2', 'Ollama AI integration designed'],
            'created_at': datetime(2025, 11, 22, 10, 0, 0),
            'updated_at': datetime(2025, 11, 25, 17, 0, 0),
            'approved_at': datetime(2025, 11, 25, 17, 0, 0),
            'description': 'Architecture: User → Business → Integration → Infrastructure layers. AGPL containment via network-only.',
        },
        {
            'id': next_gate_id(),
            'project_id': sdlco_project_id,
            'gate_name': 'G3',
            'gate_type': 'SHIP_READY',
            'stage': 'BUILD',
            'status': 'DRAFT',
            'created_by': local_tl_user_id,
            'exit_criteria': ['MVP features complete', 'Unit tests 95%+', 'API p95 <100ms'],
            'created_at': datetime(2025, 11, 27, 8, 0, 0),
            'updated_at': datetime.utcnow(),
            'approved_at': None,
            'description': 'Week 13 development in progress. 90% backend complete. Frontend 12/13 pages. Target: G6 by Week 17.',
        },
    ])

    # -----------------------------------------------------------------------
    # SDLC-Enterprise-Framework - 4 GATES (2 approved, 2 draft)
    # -----------------------------------------------------------------------
    gates_data.extend([
        {
            'id': next_gate_id(),
            'project_id': framework_project_id,
            'gate_name': 'G0.1',
            'gate_type': 'PROBLEM_DEFINITION',
            'stage': 'WHY',
            'status': 'APPROVED',
            'created_by': cpo_user_id,
            'exit_criteria': ['Problem: SDLC fragmentation', 'Personas: Dev Team, PM, CTO', 'Need: Unified 10-stage framework'],
            'created_at': datetime(2024, 6, 1, 10, 0, 0),
            'updated_at': datetime(2024, 6, 10, 15, 0, 0),
            'approved_at': datetime(2024, 6, 10, 15, 0, 0),
            'description': 'Problem: Teams use inconsistent SDLC practices. Need unified 10-stage framework with quality gates.',
        },
        {
            'id': next_gate_id(),
            'project_id': framework_project_id,
            'gate_name': 'G0.2',
            'gate_type': 'SOLUTION_DIVERSITY',
            'stage': 'WHY',
            'status': 'APPROVED',
            'created_by': cpo_user_id,
            'exit_criteria': ['Framework alternatives evaluated', 'SDLC 4.9 selected', 'Universal pillars defined'],
            'created_at': datetime(2024, 6, 15, 10, 0, 0),
            'updated_at': datetime(2024, 6, 25, 16, 0, 0),
            'approved_at': datetime(2024, 6, 25, 16, 0, 0),
            'description': 'SDLC 4.9 with 10 stages + 6 universal pillars. Zero Mock Policy. Stage-gate quality control.',
        },
        {
            'id': next_gate_id(),
            'project_id': framework_project_id,
            'gate_name': 'G1',
            'gate_type': 'PLANNING_COMPLETE',
            'stage': 'WHAT',
            'status': 'DRAFT',
            'created_by': local_tl_user_id,
            'exit_criteria': ['Framework structure defined', 'Stage templates complete', 'Training curriculum designed'],
            'created_at': datetime(2024, 10, 1, 9, 0, 0),
            'updated_at': datetime.utcnow(),
            'approved_at': None,
            'description': '10-stage structure defined. Stage 00-09 templates 80% complete. Training materials in progress.',
        },
        {
            'id': next_gate_id(),
            'project_id': framework_project_id,
            'gate_name': 'G2',
            'gate_type': 'DESIGN_READY',
            'stage': 'HOW',
            'status': 'DRAFT',
            'created_by': cpo_user_id,
            'exit_criteria': ['Documentation format approved', 'Version control strategy', 'Distribution plan'],
            'created_at': datetime(2025, 9, 1, 10, 0, 0),
            'updated_at': datetime.utcnow(),
            'approved_at': None,
            'description': 'SDLC 4.9.1 update in progress. Code naming standards restored from 4.3/4.4. AI integration added.',
        },
    ])

    for gate in gates_data:
        gate_params = gate.copy()
        gate_params['exit_criteria'] = json.dumps(gate['exit_criteria'])
        conn.execute(
            text("""
                INSERT INTO gates (id, project_id, gate_name, gate_type, stage, status,
                                 created_by, exit_criteria, description, approved_at, created_at, updated_at)
                VALUES (:id, :project_id, :gate_name, :gate_type, :stage, :status,
                        :created_by, CAST(:exit_criteria AS jsonb), :description, :approved_at, :created_at, :updated_at)
                ON CONFLICT (id) DO NOTHING
            """),
            gate_params
        )

    # =========================================================================
    # 8. EVIDENCE (46 records - realistic evidence for approved gates)
    # =========================================================================

    evidence_id_counter = 1

    def next_evidence_id():
        nonlocal evidence_id_counter
        eid = f"f0000000-0000-0000-0000-{str(evidence_id_counter).zfill(12)}"
        evidence_id_counter += 1
        return eid

    # Get gate IDs for reference (gates are inserted with sequential IDs)
    # BFlow: e..001 to e..011 (11 gates)
    # NQH-Bot: e..012 to e..017 (6 gates)
    # SDLC-O: e..018 to e..022 (5 gates)
    # Framework: e..023 to e..026 (4 gates)

    evidence_data = []

    # BFlow Platform Evidence (18 records - 2 per approved gate except G9 which has 1)
    bflow_gate_ids = [f"e0000000-0000-0000-0000-{str(i).zfill(12)}" for i in range(1, 12)]

    for i, gate_id in enumerate(bflow_gate_ids[:10]):  # 10 gates
        # Evidence 1 for each gate
        evidence_data.append({
            'id': next_evidence_id(),
            'gate_id': gate_id,
            'evidence_type': 'DESIGN_DOCUMENT' if i < 4 else ('TEST_RESULTS' if i < 7 else 'DEPLOYMENT_PROOF'),
            'file_name': f'bflow-gate-{i+1}-evidence-1.pdf',
            's3_bucket': 'evidence-vault',
            's3_key': f'bflow/gate-{i+1}/evidence-1.pdf',
            'file_size': 150000 + (i * 10000),
            'file_type': 'application/pdf',
            'sha256_hash': f'sha256_bflow_gate{i+1}_ev1_{hex(hash(f"bflow{i}"))[2:18]}',
            'uploaded_by': ceo_user_id if i < 2 else (cpo_user_id if i < 4 else cto_user_id),
            'description': f'BFlow Platform Gate {i+1} primary evidence document',
            'created_at': datetime(2022, 2 + i, 10 + i, 10, 0, 0),
            'uploaded_at': datetime(2022, 2 + i, 15 + i % 15, 15, 0, 0),
        })
        # Evidence 2 for gates 1-9 only
        if i < 9:
            evidence_data.append({
                'id': next_evidence_id(),
                'gate_id': gate_id,
                'evidence_type': 'CODE_REVIEW' if i >= 4 else 'COMPLIANCE',
                'file_name': f'bflow-gate-{i+1}-evidence-2.pdf',
                's3_bucket': 'evidence-vault',
            's3_key': f'bflow/gate-{i+1}/evidence-2.pdf',
                'file_size': 80000 + (i * 5000),
                'file_type': 'application/pdf',
                'sha256_hash': f'sha256_bflow_gate{i+1}_ev2_{hex(hash(f"bflow2{i}"))[2:18]}',
                'uploaded_by': qa_lead_user_id if i >= 5 else local_tl_user_id,
                'description': f'BFlow Platform Gate {i+1} supporting evidence',
                'created_at': datetime(2022, 2 + i, 12 + i, 14, 0, 0),
                'uploaded_at': datetime(2022, 2 + i, 16 + i % 14, 16, 0, 0),
            })

    # NQH-Bot Platform Evidence (12 records - 2 per gate)
    nqhbot_gate_ids = [f"e0000000-0000-0000-0000-{str(i).zfill(12)}" for i in range(12, 18)]

    for i, gate_id in enumerate(nqhbot_gate_ids):
        evidence_data.append({
            'id': next_evidence_id(),
            'gate_id': gate_id,
            'evidence_type': 'DESIGN_DOCUMENT' if i < 3 else 'TEST_RESULTS',
            'file_name': f'nqhbot-gate-{i+1}-primary.pdf',
            's3_bucket': 'evidence-vault',
            's3_key': f'nqhbot/gate-{i+1}/primary.pdf',
            'file_size': 120000 + (i * 8000),
            'file_type': 'application/pdf',
            'sha256_hash': f'sha256_nqhbot_gate{i+1}_ev1_{hex(hash(f"nqhbot{i}"))[2:18]}',
            'uploaded_by': ceo_user_id if i < 2 else local_tl_user_id,
            'description': f'NQH-Bot Platform Gate {i+1} primary evidence',
            'created_at': datetime(2025, 9 + i // 2, 5 + i * 3, 10, 0, 0),
            'uploaded_at': datetime(2025, 9 + i // 2, 10 + i * 3 % 20, 15, 0, 0),
        })
        evidence_data.append({
            'id': next_evidence_id(),
            'gate_id': gate_id,
            'evidence_type': 'COMPLIANCE',
            'file_name': f'nqhbot-gate-{i+1}-compliance.pdf',
            's3_bucket': 'evidence-vault',
            's3_key': f'nqhbot/gate-{i+1}/compliance.pdf',
            'file_size': 60000 + (i * 3000),
            'file_type': 'application/pdf',
            'sha256_hash': f'sha256_nqhbot_gate{i+1}_ev2_{hex(hash(f"nqhbot2{i}"))[2:18]}',
            'uploaded_by': qa_lead_user_id,
            'description': f'NQH-Bot Platform Gate {i+1} compliance check',
            'created_at': datetime(2025, 9 + i // 2, 7 + i * 3, 11, 0, 0),
            'uploaded_at': datetime(2025, 9 + i // 2, 12 + i * 3 % 18, 16, 0, 0),
        })

    # SDLC-Orchestrator Evidence (10 records - 2 per approved gate + 2 for draft)
    sdlco_gate_ids = [f"e0000000-0000-0000-0000-{str(i).zfill(12)}" for i in range(18, 23)]

    for i, gate_id in enumerate(sdlco_gate_ids):
        evidence_data.append({
            'id': next_evidence_id(),
            'gate_id': gate_id,
            'evidence_type': 'DESIGN_DOCUMENT',
            'file_name': f'sdlco-gate-{i+1}-document.pdf',
            's3_bucket': 'evidence-vault',
            's3_key': f'sdlco/gate-{i+1}/document.pdf',
            'file_size': 100000 + (i * 15000),
            'file_type': 'application/pdf',
            'sha256_hash': f'sha256_sdlco_gate{i+1}_ev1_{hex(hash(f"sdlco{i}"))[2:18]}',
            'uploaded_by': cto_user_id if i < 2 else cpo_user_id,
            'description': f'SDLC-Orchestrator Gate {i+1} design document',
            'created_at': datetime(2025, 11, 13 + i * 2, 10, 0, 0),
            'uploaded_at': datetime(2025, 11, 14 + i * 2, 15, 0, 0),
        })
        evidence_data.append({
            'id': next_evidence_id(),
            'gate_id': gate_id,
            'evidence_type': 'TEST_RESULTS' if i >= 3 else 'COMPLIANCE',
            'file_name': f'sdlco-gate-{i+1}-review.pdf',
            's3_bucket': 'evidence-vault',
            's3_key': f'sdlco/gate-{i+1}/review.pdf',
            'file_size': 50000 + (i * 8000),
            'file_type': 'application/pdf',
            'sha256_hash': f'sha256_sdlco_gate{i+1}_ev2_{hex(hash(f"sdlco2{i}"))[2:18]}',
            'uploaded_by': local_tl_user_id,
            'description': f'SDLC-Orchestrator Gate {i+1} review notes',
            'created_at': datetime(2025, 11, 14 + i * 2, 11, 0, 0),
            'uploaded_at': datetime(2025, 11, 15 + i * 2, 16, 0, 0),
        })

    # SDLC-Enterprise-Framework Evidence (6 records)
    framework_gate_ids = [f"e0000000-0000-0000-0000-{str(i).zfill(12)}" for i in range(23, 27)]

    for i, gate_id in enumerate(framework_gate_ids):
        evidence_data.append({
            'id': next_evidence_id(),
            'gate_id': gate_id,
            'evidence_type': 'DOCUMENTATION',
            'file_name': f'framework-gate-{i+1}-doc.md',
            's3_bucket': 'evidence-vault',
            's3_key': f'framework/gate-{i+1}/documentation.md',
            'file_size': 45000 + (i * 10000),
            'file_type': 'text/markdown',
            'sha256_hash': f'sha256_framework_gate{i+1}_ev1_{hex(hash(f"fw{i}"))[2:18]}',
            'uploaded_by': cpo_user_id,
            'description': f'SDLC-Enterprise-Framework Gate {i+1} documentation',
            'created_at': datetime(2024, 6 + i * 2, 10 + i, 10, 0, 0),
            'uploaded_at': datetime(2024, 6 + i * 2, 15 + i, 15, 0, 0),
        })
        if i < 2:  # Only first 2 gates have secondary evidence
            evidence_data.append({
                'id': next_evidence_id(),
                'gate_id': gate_id,
                'evidence_type': 'DESIGN_DOCUMENT',
                'file_name': f'framework-gate-{i+1}-design.pdf',
                's3_bucket': 'evidence-vault',
            's3_key': f'framework/gate-{i+1}/design.pdf',
                'file_size': 30000 + (i * 5000),
                'file_type': 'application/pdf',
                'sha256_hash': f'sha256_framework_gate{i+1}_ev2_{hex(hash(f"fw2{i}"))[2:18]}',
                'uploaded_by': cto_user_id,
                'description': f'SDLC-Enterprise-Framework Gate {i+1} design document',
                'created_at': datetime(2024, 6 + i * 2, 12 + i, 11, 0, 0),
                'uploaded_at': datetime(2024, 6 + i * 2, 17 + i, 16, 0, 0),
            })

    for evidence in evidence_data:
        conn.execute(
            text("""
                INSERT INTO gate_evidence (id, gate_id, evidence_type, file_name, s3_key, s3_bucket,
                                          file_size, file_type, sha256_hash, uploaded_by,
                                          description, created_at, uploaded_at)
                VALUES (:id, :gate_id, :evidence_type, :file_name, :s3_key, :s3_bucket,
                        :file_size, :file_type, :sha256_hash, :uploaded_by,
                        :description, :created_at, :uploaded_at)
                ON CONFLICT (id) DO NOTHING
            """),
            evidence
        )

    print("=" * 70)
    print("✅ NQH Real Portfolio seed data migration complete!")
    print("=" * 70)
    print("\n📊 Summary:")
    print("  - 13 system roles (CEO, CTO, CPO, EM, TL, DEV, QA, DevOps, Security, PM, BA, CIO, CFO)")
    print("  - 12 users (1 admin + 11 NQH team)")
    print("  - 4 real projects from NQH Portfolio:")
    print("    • BFlow Platform (PRODUCTION - 11 gates, all APPROVED)")
    print("    • NQH-Bot Platform (GOLIVE Dec 15 - 6 gates, 5 approved, 1 pending)")
    print("    • SDLC-Orchestrator (Development - 5 gates, 4 approved, 1 draft)")
    print("    • SDLC-Enterprise-Framework (Documentation - 4 gates, 2 approved, 2 draft)")
    print("  - 26 gates (22 APPROVED, 1 PENDING, 3 DRAFT)")
    print("  - 46 evidence records")
    print("  - 35 project memberships")
    print("  - 4 AI providers (Ollama PRIMARY, Claude, GPT-4o, Gemini)")
    print("\n✅ Ready for Sprint 14 E2E testing with real NQH Portfolio data!")
    print("=" * 70)


def downgrade() -> None:
    """
    Remove all seed data in reverse order.
    Cast UUID to TEXT for LIKE pattern matching.
    """
    conn = op.get_bind()

    # Delete in reverse order of foreign key dependencies
    # Cast UUID to TEXT for LIKE pattern matching
    conn.execute(text("DELETE FROM gate_evidence WHERE id::text LIKE 'f0000000%'"))
    conn.execute(text("DELETE FROM gates WHERE id::text LIKE 'e0000000%'"))
    conn.execute(text("DELETE FROM ai_providers WHERE id::text LIKE '90000000%'"))
    conn.execute(text("DELETE FROM user_roles WHERE user_id::text LIKE 'b0000000%'"))
    conn.execute(text("DELETE FROM project_members WHERE id::text LIKE 'd0000000%'"))
    conn.execute(text("DELETE FROM projects WHERE id::text LIKE 'c0000000%'"))
    conn.execute(text("DELETE FROM users WHERE id::text LIKE 'a0000000%' OR id::text LIKE 'b0000000%'"))
    conn.execute(text("DELETE FROM roles WHERE id::text LIKE '10000000%'"))

    print("✅ NQH Real Portfolio seed data removed successfully")
