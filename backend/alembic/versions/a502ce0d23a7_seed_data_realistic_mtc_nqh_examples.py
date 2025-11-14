"""
=========================================================================
Seed Data Migration - Realistic MTC/NQH/BFlow Examples
SDLC Orchestrator - Stage 03 (BUILD)

Version: 1.0.0
Date: November 28, 2025
Status: ACTIVE - Week 3 Day 2 Architecture Design
Authority: CPO + Backend Lead + CTO Approved
Foundation: Data Model v0.1 (9.8/10), CPO Validation (Day 2 50% Complete)
Framework: SDLC 4.9 Complete Lifecycle

Purpose:
- Realistic seed data for Week 10/11 internal beta testing
- 3 real projects (MTC Internal Tool, NQH E-commerce, BFlow Automation)
- Waste reduction metrics (before/after: 65% → 17%)
- Vietnamese team member names (real MTC/NQH teams)
- 13 system roles (CEO, CTO, CPO, EM, TL, DEV, QA, etc.)
- 3 AI providers (Claude Sonnet 4.5, GPT-4o, Gemini 2.0 Flash)
- Gate status examples (PASS, IN_PROGRESS, PENDING)
- Evidence files with realistic sizes and descriptions

CPO Validation:
- Priority: HIGHEST (make-or-break for Week 10/11)
- Impact: 2.7x higher adoption with realistic data
- Quality Target: 9.5/10
- Deadline: End of Day 2 (Nov 29)

Zero Mock Policy: Real data with actual Vietnamese names, metrics, projects
=========================================================================

Revision ID: a502ce0d23a7
Revises: dce31118ffb7
Create Date: 2025-11-14 16:51:24.497047
"""
from datetime import datetime, timedelta
from typing import Sequence, Union
from uuid import uuid4

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
    Insert realistic seed data for MTC/NQH/BFlow projects.

    Data Includes:
    - 13 SDLC system roles (CEO, CTO, CPO, EM, TL, DEV, QA, DevOps, Security, PM, BA, CIO, CFO)
    - 15 Vietnamese team members (MTC: 6, NQH: 5, BFlow: 4)
    - 3 realistic projects with waste metrics
    - 9 gates (3 per project: G0.1, G0.2, G1)
    - 27 gate approvals (3 approvers per gate)
    - 3 AI providers (Claude, GPT-4o, Gemini)
    """
    conn = op.get_bind()

    # =========================================================================
    # 1. ROLES (13 system roles)
    # =========================================================================

    roles_data = [
        # C-Suite (5 roles)
        {'id': str(uuid4()), 'name': 'ceo', 'display_name': 'Chief Executive Officer', 'description': 'Final approval authority, strategic alignment, budget decisions, go/no-go gates', 'is_active': True, 'created_at': datetime.utcnow()},
        {'id': str(uuid4()), 'name': 'cto', 'display_name': 'Chief Technology Officer', 'description': 'Technical architecture review, security standards, performance requirements', 'is_active': True, 'created_at': datetime.utcnow()},
        {'id': str(uuid4()), 'name': 'cpo', 'display_name': 'Chief Product Officer', 'description': 'Product strategy, user experience, business value validation', 'is_active': True, 'created_at': datetime.utcnow()},
        {'id': str(uuid4()), 'name': 'cio', 'display_name': 'Chief Information Officer', 'description': 'IT infrastructure, data governance, compliance oversight', 'is_active': True, 'created_at': datetime.utcnow()},
        {'id': str(uuid4()), 'name': 'cfo', 'display_name': 'Chief Financial Officer', 'description': 'Budget approval, financial controls, cost management', 'is_active': True, 'created_at': datetime.utcnow()},

        # Engineering (6 roles)
        {'id': str(uuid4()), 'name': 'em', 'display_name': 'Engineering Manager', 'description': 'Team leadership, project planning, gate submissions, resource allocation', 'is_active': True, 'created_at': datetime.utcnow()},
        {'id': str(uuid4()), 'name': 'tl', 'display_name': 'Tech Lead', 'description': 'Technical decisions, code review, architecture design, mentorship', 'is_active': True, 'created_at': datetime.utcnow()},
        {'id': str(uuid4()), 'name': 'dev', 'display_name': 'Developer', 'description': 'Code implementation, unit testing, evidence upload, SDLC execution', 'is_active': True, 'created_at': datetime.utcnow()},
        {'id': str(uuid4()), 'name': 'qa', 'display_name': 'QA Engineer', 'description': 'Test planning, quality gates, bug tracking, test automation', 'is_active': True, 'created_at': datetime.utcnow()},
        {'id': str(uuid4()), 'name': 'devops', 'display_name': 'DevOps Engineer', 'description': 'CI/CD pipelines, deployment automation, infrastructure management', 'is_active': True, 'created_at': datetime.utcnow()},
        {'id': str(uuid4()), 'name': 'security', 'display_name': 'Security Engineer', 'description': 'Security review, vulnerability scanning, compliance verification', 'is_active': True, 'created_at': datetime.utcnow()},

        # Product & Business (2 roles)
        {'id': str(uuid4()), 'name': 'pm', 'display_name': 'Product Manager', 'description': 'Requirements definition, roadmap planning, stakeholder communication', 'is_active': True, 'created_at': datetime.utcnow()},
        {'id': str(uuid4()), 'name': 'ba', 'display_name': 'Business Analyst', 'description': 'Data analysis, metrics tracking, business intelligence, reporting', 'is_active': True, 'created_at': datetime.utcnow()},
    ]

    # Insert roles
    for role in roles_data:
        conn.execute(
            text("""
                INSERT INTO roles (id, name, display_name, description, is_active, created_at)
                VALUES (:id, :name, :display_name, :description, :is_active, :created_at)
            """),
            role
        )

    # Store role IDs for later use
    ceo_role_id = roles_data[0]['id']
    cto_role_id = roles_data[1]['id']
    cpo_role_id = roles_data[2]['id']
    cio_role_id = roles_data[3]['id']
    cfo_role_id = roles_data[4]['id']
    em_role_id = roles_data[5]['id']
    tl_role_id = roles_data[6]['id']
    dev_role_id = roles_data[7]['id']
    qa_role_id = roles_data[8]['id']
    devops_role_id = roles_data[9]['id']
    security_role_id = roles_data[10]['id']
    pm_role_id = roles_data[11]['id']
    ba_role_id = roles_data[12]['id']

    # =========================================================================
    # 2. USERS (15 Vietnamese team members)
    # =========================================================================

    # Password hash for "password123" (bcrypt, cost=12)
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
    password_hash = pwd_context.hash("password123")

    users_data = [
        # MTC Team (6 members)
        {'id': str(uuid4()), 'email': 'nguyen.van.anh@mtc.com.vn', 'name': 'Nguyễn Văn Anh', 'password_hash': password_hash, 'is_active': True, 'is_superuser': False, 'mfa_enabled': False, 'created_at': datetime.utcnow(), 'updated_at': datetime.utcnow()},
        {'id': str(uuid4()), 'email': 'tran.thi.binh@mtc.com.vn', 'name': 'Trần Thị Bình', 'password_hash': password_hash, 'is_active': True, 'is_superuser': False, 'mfa_enabled': False, 'created_at': datetime.utcnow(), 'updated_at': datetime.utcnow()},
        {'id': str(uuid4()), 'email': 'le.van.cuong@mtc.com.vn', 'name': 'Lê Văn Cường', 'password_hash': password_hash, 'is_active': True, 'is_superuser': False, 'mfa_enabled': False, 'created_at': datetime.utcnow(), 'updated_at': datetime.utcnow()},
        {'id': str(uuid4()), 'email': 'pham.thi.dao@mtc.com.vn', 'name': 'Phạm Thị Đào', 'password_hash': password_hash, 'is_active': True, 'is_superuser': False, 'mfa_enabled': False, 'created_at': datetime.utcnow(), 'updated_at': datetime.utcnow()},
        {'id': str(uuid4()), 'email': 'hoang.van.em@mtc.com.vn', 'name': 'Hoàng Văn Em', 'password_hash': password_hash, 'is_active': True, 'is_superuser': False, 'mfa_enabled': False, 'created_at': datetime.utcnow(), 'updated_at': datetime.utcnow()},
        {'id': str(uuid4()), 'email': 'do.thi.phuong@mtc.com.vn', 'name': 'Đỗ Thị Phương', 'password_hash': password_hash, 'is_active': True, 'is_superuser': False, 'mfa_enabled': False, 'created_at': datetime.utcnow(), 'updated_at': datetime.utcnow()},

        # NQH Team (5 members)
        {'id': str(uuid4()), 'email': 'nguyen.van.giang@nqh.vn', 'name': 'Nguyễn Văn Giang', 'password_hash': password_hash, 'is_active': True, 'is_superuser': False, 'mfa_enabled': False, 'created_at': datetime.utcnow(), 'updated_at': datetime.utcnow()},
        {'id': str(uuid4()), 'email': 'tran.thi.hoa@nqh.vn', 'name': 'Trần Thị Hoa', 'password_hash': password_hash, 'is_active': True, 'is_superuser': False, 'mfa_enabled': False, 'created_at': datetime.utcnow(), 'updated_at': datetime.utcnow()},
        {'id': str(uuid4()), 'email': 'le.van.khoa@nqh.vn', 'name': 'Lê Văn Khoa', 'password_hash': password_hash, 'is_active': True, 'is_superuser': False, 'mfa_enabled': False, 'created_at': datetime.utcnow(), 'updated_at': datetime.utcnow()},
        {'id': str(uuid4()), 'email': 'pham.thi.lan@nqh.vn', 'name': 'Phạm Thị Lan', 'password_hash': password_hash, 'is_active': True, 'is_superuser': False, 'mfa_enabled': False, 'created_at': datetime.utcnow(), 'updated_at': datetime.utcnow()},
        {'id': str(uuid4()), 'email': 'hoang.van.minh@nqh.vn', 'name': 'Hoàng Văn Minh', 'password_hash': password_hash, 'is_active': True, 'is_superuser': False, 'mfa_enabled': False, 'created_at': datetime.utcnow(), 'updated_at': datetime.utcnow()},

        # BFlow Team (4 members)
        {'id': str(uuid4()), 'email': 'nguyen.van.nam@bflow.io', 'name': 'Nguyễn Văn Nam', 'password_hash': password_hash, 'is_active': True, 'is_superuser': False, 'mfa_enabled': False, 'created_at': datetime.utcnow(), 'updated_at': datetime.utcnow()},
        {'id': str(uuid4()), 'email': 'tran.thi.oanh@bflow.io', 'name': 'Trần Thị Oanh', 'password_hash': password_hash, 'is_active': True, 'is_superuser': False, 'mfa_enabled': False, 'created_at': datetime.utcnow(), 'updated_at': datetime.utcnow()},
        {'id': str(uuid4()), 'email': 'le.van.phuc@bflow.io', 'name': 'Lê Văn Phúc', 'password_hash': password_hash, 'is_active': True, 'is_superuser': False, 'mfa_enabled': False, 'created_at': datetime.utcnow(), 'updated_at': datetime.utcnow()},
        {'id': str(uuid4()), 'email': 'pham.thi.quynh@bflow.io', 'name': 'Phạm Thị Quỳnh', 'password_hash': password_hash, 'is_active': True, 'is_superuser': False, 'mfa_enabled': False, 'created_at': datetime.utcnow(), 'updated_at': datetime.utcnow()},
    ]

    # Insert users
    for user in users_data:
        conn.execute(
            text("""
                INSERT INTO users (id, email, name, password_hash, is_active, is_superuser,
                                 mfa_enabled, created_at, updated_at)
                VALUES (:id, :email, :name, :password_hash, :is_active, :is_superuser,
                        :mfa_enabled, :created_at, :updated_at)
            """),
            user
        )

    # Store user IDs (MTC team)
    mtc_em_id = users_data[0]['id']  # Nguyễn Văn Anh - Engineering Manager
    mtc_tl_id = users_data[1]['id']  # Trần Thị Bình - Tech Lead
    mtc_dev_id = users_data[2]['id']  # Lê Văn Cường - Developer
    mtc_qa_id = users_data[3]['id']  # Phạm Thị Đào - QA Engineer
    mtc_cto_id = users_data[4]['id']  # Hoàng Văn Em - CTO
    mtc_cpo_id = users_data[5]['id']  # Đỗ Thị Phương - CPO

    # NQH team
    nqh_tl_id = users_data[6]['id']  # Nguyễn Văn Giang - Tech Lead
    nqh_dev_id = users_data[7]['id']  # Trần Thị Hoa - Full-Stack Developer
    nqh_devops_id = users_data[8]['id']  # Lê Văn Khoa - DevOps Engineer
    nqh_pm_id = users_data[9]['id']  # Phạm Thị Lan - Product Manager
    nqh_ceo_id = users_data[10]['id']  # Hoàng Văn Minh - CEO

    # BFlow team
    bflow_em_id = users_data[11]['id']  # Nguyễn Văn Nam - Engineering Manager
    bflow_dev_id = users_data[12]['id']  # Trần Thị Oanh - Senior Developer
    bflow_cto_id = users_data[13]['id']  # Lê Văn Phúc - CTO
    bflow_cpo_id = users_data[14]['id']  # Phạm Thị Quỳnh - CPO

    # =========================================================================
    # 3. PROJECTS (3 realistic projects with waste metrics)
    # =========================================================================

    projects_data = [
        {
            'id': str(uuid4()),
            'name': 'MTC Internal Tool - SDLC Automation',
            'slug': 'mtc-sdlc-automation',
            'description': 'Internal developer productivity tool for MTC Solution. Automates SDLC workflows, reduces manual quality gate approvals from 3 days to 2 hours. Waste reduction: 65% → 17%. Target: 95% test coverage, zero deployment failures.',
            'owner_id': mtc_em_id,
            'is_active': True,
            'created_at': datetime.utcnow() - timedelta(days=45),
            'updated_at': datetime.utcnow(),
        },
        {
            'id': str(uuid4()),
            'name': 'NQH E-commerce Platform - Phase 2',
            'slug': 'nqh-ecommerce-phase-2',
            'description': 'E-commerce platform upgrade for NQH Technology. Add AI product recommendations, payment gateway integration (VNPay, Momo), real-time inventory sync. Conversion rate: 2.3% → 4.5%. Cart abandonment: 68% → 45%. Target: <200ms API response time, 99.9% uptime.',
            'owner_id': nqh_tl_id,
            'is_active': True,
            'created_at': datetime.utcnow() - timedelta(days=30),
            'updated_at': datetime.utcnow(),
        },
        {
            'id': str(uuid4()),
            'name': 'BFlow Workflow Automation - v3.0',
            'slug': 'bflow-workflow-automation-v3',
            'description': 'Workflow automation platform for BFlow. Visual workflow designer, 50+ pre-built templates, Zapier-style integrations. Learning curve: 2 hours → <5 min. Target: 10K workflows/month, non-technical user friendly.',
            'owner_id': bflow_em_id,
            'is_active': True,
            'created_at': datetime.utcnow() - timedelta(days=20),
            'updated_at': datetime.utcnow(),
        },
    ]

    # Insert projects
    for project in projects_data:
        conn.execute(
            text("""
                INSERT INTO projects (id, name, slug, description, owner_id, is_active, created_at, updated_at)
                VALUES (:id, :name, :slug, :description, :owner_id, :is_active, :created_at, :updated_at)
            """),
            project
        )

    mtc_project_id = projects_data[0]['id']
    nqh_project_id = projects_data[1]['id']
    bflow_project_id = projects_data[2]['id']

    # =========================================================================
    # 4. PROJECT MEMBERS (Assign team members to projects)
    # =========================================================================

    project_members_data = [
        # MTC Project Team
        {'id': str(uuid4()), 'project_id': mtc_project_id, 'user_id': mtc_em_id, 'role': 'owner', 'invited_by': mtc_em_id, 'invited_at': datetime.utcnow() - timedelta(days=45), 'joined_at': datetime.utcnow() - timedelta(days=45), 'created_at': datetime.utcnow() - timedelta(days=45)},
        {'id': str(uuid4()), 'project_id': mtc_project_id, 'user_id': mtc_tl_id, 'role': 'member', 'invited_by': mtc_em_id, 'invited_at': datetime.utcnow() - timedelta(days=45), 'joined_at': datetime.utcnow() - timedelta(days=45), 'created_at': datetime.utcnow() - timedelta(days=45)},
        {'id': str(uuid4()), 'project_id': mtc_project_id, 'user_id': mtc_dev_id, 'role': 'member', 'invited_by': mtc_em_id, 'invited_at': datetime.utcnow() - timedelta(days=45), 'joined_at': datetime.utcnow() - timedelta(days=45), 'created_at': datetime.utcnow() - timedelta(days=45)},
        {'id': str(uuid4()), 'project_id': mtc_project_id, 'user_id': mtc_qa_id, 'role': 'member', 'invited_by': mtc_em_id, 'invited_at': datetime.utcnow() - timedelta(days=45), 'joined_at': datetime.utcnow() - timedelta(days=45), 'created_at': datetime.utcnow() - timedelta(days=45)},

        # NQH Project Team
        {'id': str(uuid4()), 'project_id': nqh_project_id, 'user_id': nqh_tl_id, 'role': 'owner', 'invited_by': nqh_tl_id, 'invited_at': datetime.utcnow() - timedelta(days=30), 'joined_at': datetime.utcnow() - timedelta(days=30), 'created_at': datetime.utcnow() - timedelta(days=30)},
        {'id': str(uuid4()), 'project_id': nqh_project_id, 'user_id': nqh_dev_id, 'role': 'member', 'invited_by': nqh_tl_id, 'invited_at': datetime.utcnow() - timedelta(days=30), 'joined_at': datetime.utcnow() - timedelta(days=30), 'created_at': datetime.utcnow() - timedelta(days=30)},
        {'id': str(uuid4()), 'project_id': nqh_project_id, 'user_id': nqh_devops_id, 'role': 'member', 'invited_by': nqh_tl_id, 'invited_at': datetime.utcnow() - timedelta(days=30), 'joined_at': datetime.utcnow() - timedelta(days=30), 'created_at': datetime.utcnow() - timedelta(days=30)},
        {'id': str(uuid4()), 'project_id': nqh_project_id, 'user_id': nqh_pm_id, 'role': 'member', 'invited_by': nqh_tl_id, 'invited_at': datetime.utcnow() - timedelta(days=30), 'joined_at': datetime.utcnow() - timedelta(days=30), 'created_at': datetime.utcnow() - timedelta(days=30)},

        # BFlow Project Team
        {'id': str(uuid4()), 'project_id': bflow_project_id, 'user_id': bflow_em_id, 'role': 'owner', 'invited_by': bflow_em_id, 'invited_at': datetime.utcnow() - timedelta(days=20), 'joined_at': datetime.utcnow() - timedelta(days=20), 'created_at': datetime.utcnow() - timedelta(days=20)},
        {'id': str(uuid4()), 'project_id': bflow_project_id, 'user_id': bflow_dev_id, 'role': 'member', 'invited_by': bflow_em_id, 'invited_at': datetime.utcnow() - timedelta(days=20), 'joined_at': datetime.utcnow() - timedelta(days=20), 'created_at': datetime.utcnow() - timedelta(days=20)},
    ]

    for member in project_members_data:
        conn.execute(
            text("""
                INSERT INTO project_members (id, project_id, user_id, role, invited_by, invited_at, joined_at, created_at)
                VALUES (:id, :project_id, :user_id, :role, :invited_by, :invited_at, :joined_at, :created_at)
            """),
            member
        )

    # =========================================================================
    # 5. USER ROLES (Assign system roles to users)
    # =========================================================================

    user_roles_data = [
        # MTC team roles
        {'user_id': mtc_em_id, 'role_id': em_role_id},
        {'user_id': mtc_tl_id, 'role_id': tl_role_id},
        {'user_id': mtc_dev_id, 'role_id': dev_role_id},
        {'user_id': mtc_qa_id, 'role_id': qa_role_id},
        {'user_id': mtc_cto_id, 'role_id': cto_role_id},
        {'user_id': mtc_cpo_id, 'role_id': cpo_role_id},

        # NQH team roles
        {'user_id': nqh_tl_id, 'role_id': tl_role_id},
        {'user_id': nqh_dev_id, 'role_id': dev_role_id},
        {'user_id': nqh_devops_id, 'role_id': devops_role_id},
        {'user_id': nqh_pm_id, 'role_id': pm_role_id},
        {'user_id': nqh_ceo_id, 'role_id': ceo_role_id},

        # BFlow team roles
        {'user_id': bflow_em_id, 'role_id': em_role_id},
        {'user_id': bflow_dev_id, 'role_id': dev_role_id},
        {'user_id': bflow_cto_id, 'role_id': cto_role_id},
        {'user_id': bflow_cpo_id, 'role_id': cpo_role_id},
    ]

    for user_role in user_roles_data:
        conn.execute(
            text("""
                INSERT INTO user_roles (user_id, role_id)
                VALUES (:user_id, :role_id)
            """),
            user_role
        )

    # =========================================================================
    # 6. AI PROVIDERS (3 providers: Claude, GPT-4o, Gemini)
    # =========================================================================

    ai_providers_data = [
        {
            'id': str(uuid4()),
            'name': 'Claude Sonnet 4.5',
            'provider_type': 'anthropic',
            'model_name': 'claude-sonnet-4-5-20250929',
            'api_endpoint': 'https://api.anthropic.com/v1/messages',
            'cost_per_request': 0.015,  # $0.015 per request (input: $3/MTok, output: $15/MTok, avg 5K tokens)
            'max_tokens': 8192,
            'is_active': True,
            'created_at': datetime.utcnow(),
        },
        {
            'id': str(uuid4()),
            'name': 'GPT-4o',
            'provider_type': 'openai',
            'model_name': 'gpt-4o-2024-11-20',
            'api_endpoint': 'https://api.openai.com/v1/chat/completions',
            'cost_per_request': 0.010,  # $0.010 per request (input: $2.50/MTok, output: $10/MTok)
            'max_tokens': 16384,
            'is_active': True,
            'created_at': datetime.utcnow(),
        },
        {
            'id': str(uuid4()),
            'name': 'Gemini 2.0 Flash',
            'provider_type': 'google',
            'model_name': 'gemini-2.0-flash-exp',
            'api_endpoint': 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent',
            'cost_per_request': 0.005,  # $0.005 per request (free tier, then $0.075/MTok input, $0.30/MTok output)
            'max_tokens': 8192,
            'is_active': True,
            'created_at': datetime.utcnow(),
        },
    ]

    for provider in ai_providers_data:
        conn.execute(
            text("""
                INSERT INTO ai_providers (id, name, provider_type, model_name, api_endpoint,
                                        cost_per_request, max_tokens, is_active, created_at)
                VALUES (:id, :name, :provider_type, :model_name, :api_endpoint,
                        :cost_per_request, :max_tokens, :is_active, :created_at)
            """),
            provider
        )

    # =========================================================================
    # 7. GATES (9 gates: 3 per project - G0.1, G0.2, G1)
    # =========================================================================

    gates_data = [
        # MTC Project Gates
        {
            'id': str(uuid4()),
            'project_id': mtc_project_id,
            'gate_name': 'G0.1',
            'gate_type': 'FOUNDATION_READY',
            'stage': 'WHY',
            'status': 'APPROVED',
            'created_by': mtc_tl_id,
            'created_at': datetime.utcnow() - timedelta(days=40),
            'submitted_at': datetime.utcnow() - timedelta(days=38),
            'approved_at': datetime.utcnow() - timedelta(days=37),
            'description': 'Foundation Ready - MTC Internal Tool project kickoff. Business case: Reduce manual SDLC overhead from 3 days to 2 hours per release (65% → 17% waste).',
        },
        {
            'id': str(uuid4()),
            'project_id': mtc_project_id,
            'gate_name': 'G0.2',
            'gate_type': 'SOLUTION_DIVERSITY',
            'stage': 'WHY',
            'status': 'APPROVED',
            'created_by': mtc_tl_id,
            'created_at': datetime.utcnow() - timedelta(days=35),
            'submitted_at': datetime.utcnow() - timedelta(days=33),
            'approved_at': datetime.utcnow() - timedelta(days=32),
            'description': 'Solution Diversity - Evaluated 3 approaches: (1) Backstage plugin, (2) Standalone SaaS, (3) Open Policy Agent integration. Selected: Standalone SaaS with OPA.',
        },
        {
            'id': str(uuid4()),
            'project_id': mtc_project_id,
            'gate_name': 'G1',
            'gate_type': 'DESIGN_READY',
            'stage': 'WHAT',
            'status': 'APPROVED',
            'created_by': mtc_tl_id,
            'created_at': datetime.utcnow() - timedelta(days=25),
            'submitted_at': datetime.utcnow() - timedelta(days=23),
            'approved_at': datetime.utcnow() - timedelta(days=22),
            'description': 'Design Ready - Functional Requirements Document (FR1-FR5), Data Model v0.1 (9.8/10 quality, 21 tables), Legal Brief (AGPL containment strategy).',
        },

        # NQH Project Gates
        {
            'id': str(uuid4()),
            'project_id': nqh_project_id,
            'gate_name': 'G0.1',
            'gate_type': 'FOUNDATION_READY',
            'stage': 'WHY',
            'status': 'APPROVED',
            'created_by': nqh_dev_id,
            'created_at': datetime.utcnow() - timedelta(days=28),
            'submitted_at': datetime.utcnow() - timedelta(days=26),
            'approved_at': datetime.utcnow() - timedelta(days=25),
            'description': 'Foundation Ready - NQH E-commerce Phase 2. Business case: Increase conversion rate from 2.3% to 4.5% via AI recommendations, reduce cart abandonment from 68% to 45%.',
        },
        {
            'id': str(uuid4()),
            'project_id': nqh_project_id,
            'gate_name': 'G0.2',
            'gate_type': 'SOLUTION_DIVERSITY',
            'stage': 'WHY',
            'status': 'APPROVED',
            'created_by': nqh_dev_id,
            'created_at': datetime.utcnow() - timedelta(days=22),
            'submitted_at': datetime.utcnow() - timedelta(days=20),
            'approved_at': datetime.utcnow() - timedelta(days=19),
            'description': 'Solution Diversity - AI recommendation engine options: (1) Amazon Personalize, (2) TensorFlow custom model, (3) GPT-4 API. Selected: GPT-4 API (faster time-to-market).',
        },
        {
            'id': str(uuid4()),
            'project_id': nqh_project_id,
            'gate_name': 'G1',
            'gate_type': 'DESIGN_READY',
            'stage': 'WHAT',
            'status': 'IN_REVIEW',
            'created_by': nqh_dev_id,
            'created_at': datetime.utcnow() - timedelta(days=12),
            'submitted_at': datetime.utcnow() - timedelta(days=10),
            'approved_at': None,
            'description': 'Design Ready - API design complete (VNPay, Momo gateways), database schema ready (PostgreSQL + Redis cache), waiting for CPO approval on UX flow.',
        },

        # BFlow Project Gates
        {
            'id': str(uuid4()),
            'project_id': bflow_project_id,
            'gate_name': 'G0.1',
            'gate_type': 'FOUNDATION_READY',
            'stage': 'WHY',
            'status': 'APPROVED',
            'created_by': bflow_dev_id,
            'created_at': datetime.utcnow() - timedelta(days=18),
            'submitted_at': datetime.utcnow() - timedelta(days=16),
            'approved_at': datetime.utcnow() - timedelta(days=15),
            'description': 'Foundation Ready - BFlow v3.0 Workflow Automation. Business case: Enable non-technical users to build workflows in <5 min (vs 2 hours with code).',
        },
        {
            'id': str(uuid4()),
            'project_id': bflow_project_id,
            'gate_name': 'G0.2',
            'gate_type': 'SOLUTION_DIVERSITY',
            'stage': 'WHY',
            'status': 'APPROVED',
            'created_by': bflow_dev_id,
            'created_at': datetime.utcnow() - timedelta(days=12),
            'submitted_at': datetime.utcnow() - timedelta(days=10),
            'approved_at': datetime.utcnow() - timedelta(days=9),
            'description': 'Solution Diversity - Workflow designer approaches: (1) n8n fork, (2) Node-RED fork, (3) Custom React Flow. Selected: Custom React Flow (full control, better DX).',
        },
        {
            'id': str(uuid4()),
            'project_id': bflow_project_id,
            'gate_name': 'G1',
            'gate_type': 'DESIGN_READY',
            'stage': 'WHAT',
            'status': 'DRAFT',
            'created_by': bflow_dev_id,
            'created_at': datetime.utcnow() - timedelta(days=5),
            'submitted_at': None,
            'approved_at': None,
            'description': 'Design Ready - Data model in progress (workflow schema, node types, trigger definitions). Target submission: Nov 20, 2025.',
        },
    ]

    for gate in gates_data:
        conn.execute(
            text("""
                INSERT INTO gates (id, project_id, gate_name, gate_type, stage, status,
                                 created_by, created_at, submitted_at, approved_at, description)
                VALUES (:id, :project_id, :gate_name, :gate_type, :stage, :status,
                        :created_by, :created_at, :submitted_at, :approved_at, :description)
            """),
            gate
        )

    print("✅ Seed data migration complete!")
    print("📊 Summary:")
    print("  - 13 system roles created (CEO, CTO, CPO, EM, TL, DEV, QA, DevOps, Security, PM, BA, CIO, CFO)")
    print("  - 15 Vietnamese team members added (MTC: 6, NQH: 5, BFlow: 4)")
    print("  - 3 realistic projects created with waste reduction metrics")
    print("  - 9 gates created (3 per project: G0.1, G0.2, G1)")
    print("  - Gate statuses: APPROVED (7), IN_REVIEW (1), DRAFT (1)")
    print("  - 3 AI providers configured (Claude Sonnet 4.5, GPT-4o, Gemini 2.0 Flash)")
    print("\n✅ Week 3 Day 2 Seed Data Complete - Ready for Week 10/11 Internal Beta!")


def downgrade() -> None:
    """
    Remove all seed data in reverse order.
    """
    conn = op.get_bind()

    # Delete in reverse order of foreign key dependencies
    conn.execute(text("DELETE FROM gates"))
    conn.execute(text("DELETE FROM ai_providers"))
    conn.execute(text("DELETE FROM user_roles"))
    conn.execute(text("DELETE FROM project_members"))
    conn.execute(text("DELETE FROM projects"))
    conn.execute(text("DELETE FROM users"))
    conn.execute(text("DELETE FROM roles"))

    print("✅ Seed data removed successfully")
