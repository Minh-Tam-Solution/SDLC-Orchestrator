-- =========================================================================
-- DEMO SEED DATA - SDLC Orchestrator
-- =========================================================================
-- Version: 3.0.0
-- Date: November 29, 2025
-- Status: ACTIVE - STAGE 03 (BUILD)
-- Authority: QA Lead + Backend Lead Approved
-- Framework: SDLC 5.1.3.1 Complete Lifecycle
--
-- Purpose:
-- Comprehensive seed data for E2E testing using REAL NQH-Bot Platform project.
-- This data reflects the actual team structure of NQH organization:
--   CEO: Tai Dang (taidt@mtsolution.com.vn) - leads 2 teams
--   CPO: Dung Luong (dunglt@mtsolution.com.vn)
--   CTO: Hiep Dinh (dvhiep@nqh.com.vn)
--   Local Team Lead: Endior (dangtt1971@gmail.com)
--   Remote Team Lead: Ms Hang Le (ltmhang@nqh.com.vn)
--
-- Covers all 5 Functional Requirements (FR1-FR5):
--   FR1: Quality Gate Management (Gate Engine)
--   FR2: Evidence Vault (Auto-Collection + Storage)
--   FR3: AI Context Engine (Stage-Aware AI)
--   FR4: Real-Time Dashboard (Overview + Metrics)
--   FR5: Policy Pack Library (100+ SDLC 5.1.3.1 Policies)
--
-- Synchronized with: backend/alembic/versions/a502ce0d23a7_seed_data_realistic_mtc_nqh_examples.py
--
-- Usage:
-- psql -h localhost -U sdlc_user -d sdlc_orchestrator -f DEMO-SEED-DATA.sql
-- =========================================================================

-- =========================================================================
-- SECTION 1: CLEANUP (Optional - uncomment to reset)
-- =========================================================================
-- WARNING: This will delete ALL existing data!
-- TRUNCATE TABLE audit_logs CASCADE;
-- TRUNCATE TABLE policy_evaluations CASCADE;
-- TRUNCATE TABLE gate_evidence CASCADE;
-- TRUNCATE TABLE gate_approvals CASCADE;
-- TRUNCATE TABLE gates CASCADE;
-- TRUNCATE TABLE project_members CASCADE;
-- TRUNCATE TABLE projects CASCADE;
-- TRUNCATE TABLE user_roles CASCADE;
-- TRUNCATE TABLE ai_providers CASCADE;
-- TRUNCATE TABLE policies CASCADE;
-- TRUNCATE TABLE refresh_tokens CASCADE;
-- TRUNCATE TABLE users CASCADE;
-- TRUNCATE TABLE roles CASCADE;

-- =========================================================================
-- SECTION 2: TEST ACCOUNTS - NQH-Bot Platform Team
-- =========================================================================
-- NOTE: Primary seed data is in Alembic migration (a502ce0d23a7)
-- This SQL provides NQH-Bot Platform team data for E2E testing
--
-- NQH-Bot Platform Team Structure:
-- =========================================================================
-- | Role           | Email                         | Password    | Description                    |
-- |----------------|-------------------------------|-------------|--------------------------------|
-- | Platform Admin | admin@sdlc-orchestrator.io    | Admin@123   | Full access, superuser         |
-- | NQH CEO        | taidt@mtsolution.com.vn       | Admin@123   | Tai Dang - leads 2 teams       |
-- | NQH CPO        | dunglt@mtsolution.com.vn      | Admin@123   | Dung Luong - Product strategy  |
-- | NQH CTO        | dvhiep@nqh.com.vn             | Admin@123   | Hiep Dinh - Technical authority|
-- | Local TL       | dangtt1971@gmail.com          | Admin@123   | Endior - Local Team Lead       |
-- | Remote TL      | ltmhang@nqh.com.vn            | Admin@123   | Hang Le - Remote Team Lead     |
-- | Local Dev 1    | local.dev1@nqh.com.vn         | Admin@123   | Local Team Developer           |
-- | Local Dev 2    | local.dev2@nqh.com.vn         | Admin@123   | Local Team Developer           |
-- | Remote Dev 1   | remote.dev1@nqh.com.vn        | Admin@123   | Remote Team Developer          |
-- | Remote Dev 2   | remote.dev2@nqh.com.vn        | Admin@123   | Remote Team Developer          |
-- | QA Lead        | qa.lead@nqh.com.vn            | Admin@123   | QA Team Lead                   |
-- =========================================================================

-- =========================================================================
-- SECTION 3: NQH-BOT PLATFORM TEAM USERS
-- =========================================================================
-- Password hash for "Admin@123" (bcrypt, cost=12) - ALL users use same password for E2E consistency
-- Generated with: python3 -c "import bcrypt; print(bcrypt.hashpw('Admin@123'.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8'))"

-- NQH-Bot Platform Team (REAL team structure)
INSERT INTO users (id, email, name, password_hash, is_active, is_superuser, mfa_enabled, created_at, updated_at)
VALUES
  -- CEO - Tai Dang (leads 2 teams: Local + Remote)
  ('b0000000-0000-0000-0000-000000000001', 'taidt@mtsolution.com.vn', 'Tai Dang',
   '$2b$12$gbdaanPRphcu5qGFfd1AxuPE9tEuPDjazMcnz8oSfqDKE/T1961tm', -- Admin@123
   true, false, false, NOW(), NOW()),

  -- CPO - Dung Luong (Product strategy, business gates approval)
  ('b0000000-0000-0000-0000-000000000002', 'dunglt@mtsolution.com.vn', 'Dung Luong',
   '$2b$12$gbdaanPRphcu5qGFfd1AxuPE9tEuPDjazMcnz8oSfqDKE/T1961tm',
   true, false, false, NOW(), NOW()),

  -- CTO - Hiep Dinh (Technical authority, G2/G3 gates approval)
  ('b0000000-0000-0000-0000-000000000003', 'dvhiep@nqh.com.vn', 'Hiep Dinh',
   '$2b$12$gbdaanPRphcu5qGFfd1AxuPE9tEuPDjazMcnz8oSfqDKE/T1961tm',
   true, false, false, NOW(), NOW()),

  -- Local Team Lead - Endior
  ('b0000000-0000-0000-0000-000000000004', 'dangtt1971@gmail.com', 'Endior',
   '$2b$12$gbdaanPRphcu5qGFfd1AxuPE9tEuPDjazMcnz8oSfqDKE/T1961tm',
   true, false, false, NOW(), NOW()),

  -- Remote Team Lead - Ms Hang Le
  ('b0000000-0000-0000-0000-000000000005', 'ltmhang@nqh.com.vn', 'Hang Le',
   '$2b$12$gbdaanPRphcu5qGFfd1AxuPE9tEuPDjazMcnz8oSfqDKE/T1961tm',
   true, false, false, NOW(), NOW()),

  -- Local Team Developer 1
  ('b0000000-0000-0000-0000-000000000006', 'local.dev1@nqh.com.vn', 'Local Dev 1',
   '$2b$12$gbdaanPRphcu5qGFfd1AxuPE9tEuPDjazMcnz8oSfqDKE/T1961tm',
   true, false, false, NOW(), NOW()),

  -- Local Team Developer 2
  ('b0000000-0000-0000-0000-000000000007', 'local.dev2@nqh.com.vn', 'Local Dev 2',
   '$2b$12$gbdaanPRphcu5qGFfd1AxuPE9tEuPDjazMcnz8oSfqDKE/T1961tm',
   true, false, false, NOW(), NOW()),

  -- Remote Team Developer 1
  ('b0000000-0000-0000-0000-000000000008', 'remote.dev1@nqh.com.vn', 'Remote Dev 1',
   '$2b$12$gbdaanPRphcu5qGFfd1AxuPE9tEuPDjazMcnz8oSfqDKE/T1961tm',
   true, false, false, NOW(), NOW()),

  -- Remote Team Developer 2
  ('b0000000-0000-0000-0000-000000000009', 'remote.dev2@nqh.com.vn', 'Remote Dev 2',
   '$2b$12$gbdaanPRphcu5qGFfd1AxuPE9tEuPDjazMcnz8oSfqDKE/T1961tm',
   true, false, false, NOW(), NOW()),

  -- QA Lead
  ('b0000000-0000-0000-0000-000000000010', 'qa.lead@nqh.com.vn', 'QA Lead',
   '$2b$12$gbdaanPRphcu5qGFfd1AxuPE9tEuPDjazMcnz8oSfqDKE/T1961tm',
   true, false, false, NOW(), NOW()),

  -- Inactive User (for testing inactive account scenarios)
  ('b0000000-0000-0000-0000-000000000011', 'inactive@nqh.com.vn', 'Inactive User',
   '$2b$12$gbdaanPRphcu5qGFfd1AxuPE9tEuPDjazMcnz8oSfqDKE/T1961tm', -- Admin@123
   false, false, false, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- =========================================================================
-- SECTION 4: NQH-BOT PLATFORM PROJECTS
-- =========================================================================
-- Projects reflecting REAL NQH-Bot Platform development using SDLC 5.1.3.1

-- Project 1: NQH-Bot Platform - Main project (BUILD stage)
INSERT INTO projects (id, name, slug, description, owner_id, is_active, created_at, updated_at)
VALUES (
  'c0000000-0000-0000-0000-000000000001',
  'NQH-Bot Platform',
  'nqh-bot-platform',
  'AI-powered chatbot platform for enterprise automation. Multi-channel support (Telegram, Zalo, Facebook), Vietnamese NLP, CRM integration. Led by CEO Tai Dang with Local + Remote teams.',
  'b0000000-0000-0000-0000-000000000001', -- CEO Tai Dang owns
  true,
  '2025-09-01 09:00:00',
  NOW()
) ON CONFLICT (id) DO UPDATE SET updated_at = NOW();

-- Project 2: NQH-Bot Analytics Module - Feature (WHAT stage)
INSERT INTO projects (id, name, slug, description, owner_id, is_active, created_at, updated_at)
VALUES (
  'c0000000-0000-0000-0000-000000000002',
  'NQH-Bot Analytics Module',
  'nqh-bot-analytics',
  'Real-time analytics dashboard for bot performance. Conversation metrics, user engagement, response time tracking. Handled by Remote Team.',
  'b0000000-0000-0000-0000-000000000005', -- Remote TL Hang Le owns
  true,
  '2025-10-15 10:00:00',
  NOW()
) ON CONFLICT (id) DO UPDATE SET updated_at = NOW();

-- Project 3: NQH-Bot NLP Engine - Feature (HOW stage)
INSERT INTO projects (id, name, slug, description, owner_id, is_active, created_at, updated_at)
VALUES (
  'c0000000-0000-0000-0000-000000000003',
  'NQH-Bot NLP Engine',
  'nqh-bot-nlp-engine',
  'Vietnamese NLP processing engine. Intent detection, entity extraction, sentiment analysis. Uses Ollama + Claude fallback. Handled by Local Team.',
  'b0000000-0000-0000-0000-000000000004', -- Local TL Endior owns
  true,
  '2025-10-01 08:00:00',
  NOW()
) ON CONFLICT (id) DO UPDATE SET updated_at = NOW();

-- Project 4: NQH-Bot CRM Integration - Feature (VERIFY stage)
INSERT INTO projects (id, name, slug, description, owner_id, is_active, created_at, updated_at)
VALUES (
  'c0000000-0000-0000-0000-000000000004',
  'NQH-Bot CRM Integration',
  'nqh-bot-crm',
  'CRM integration module. Sync conversations to Salesforce/HubSpot, lead scoring, customer 360 view. Joint effort Local + Remote teams.',
  'b0000000-0000-0000-0000-000000000003', -- CTO Hiep Dinh owns
  true,
  '2025-08-15 09:00:00',
  NOW()
) ON CONFLICT (id) DO UPDATE SET updated_at = NOW();

-- Project 5: NQH-Bot Mobile App - Feature (WHY stage - new)
INSERT INTO projects (id, name, slug, description, owner_id, is_active, created_at, updated_at)
VALUES (
  'c0000000-0000-0000-0000-000000000005',
  'NQH-Bot Mobile App',
  'nqh-bot-mobile',
  'Mobile companion app for bot management. Push notifications, quick replies, admin dashboard. React Native cross-platform.',
  'b0000000-0000-0000-0000-000000000002', -- CPO Dung Luong owns
  true,
  NOW(),
  NOW()
) ON CONFLICT (id) DO UPDATE SET updated_at = NOW();

-- Project 6: Archived PoC (inactive)
INSERT INTO projects (id, name, slug, description, owner_id, is_active, created_at, updated_at, deleted_at)
VALUES (
  'c0000000-0000-0000-0000-000000000006',
  'NQH-Bot PoC v0.1 (Archived)',
  'nqh-bot-poc-v01',
  'Initial proof of concept. Archived after successful validation and pivot to current architecture.',
  'b0000000-0000-0000-0000-000000000001',
  false,
  '2025-06-01 10:00:00',
  '2025-08-31 17:00:00',
  '2025-09-01 09:00:00'
) ON CONFLICT (id) DO UPDATE SET updated_at = NOW();

-- =========================================================================
-- SECTION 5: PROJECT MEMBERS - NQH-Bot Platform Teams
-- =========================================================================
-- Team assignments reflecting REAL NQH organization structure:
-- - CEO leads all projects
-- - Local Team (Endior + Local Devs)
-- - Remote Team (Hang Le + Remote Devs)

-- NQH-Bot Platform Main Project Team (CEO + CTO + CPO + Both Team Leads + All Devs)
INSERT INTO project_members (id, project_id, user_id, role, invited_by, invited_at, joined_at, created_at)
VALUES
  -- CEO Tai Dang - Owner
  ('d0000000-0000-0000-0000-000000000001', 'c0000000-0000-0000-0000-000000000001',
   'b0000000-0000-0000-0000-000000000001', 'owner', NULL, NOW(), NOW(), NOW()),
  -- CPO Dung Luong - Admin
  ('d0000000-0000-0000-0000-000000000002', 'c0000000-0000-0000-0000-000000000001',
   'b0000000-0000-0000-0000-000000000002', 'admin', 'b0000000-0000-0000-0000-000000000001', NOW(), NOW(), NOW()),
  -- CTO Hiep Dinh - Admin
  ('d0000000-0000-0000-0000-000000000003', 'c0000000-0000-0000-0000-000000000001',
   'b0000000-0000-0000-0000-000000000003', 'admin', 'b0000000-0000-0000-0000-000000000001', NOW(), NOW(), NOW()),
  -- Local TL Endior - Admin
  ('d0000000-0000-0000-0000-000000000004', 'c0000000-0000-0000-0000-000000000001',
   'b0000000-0000-0000-0000-000000000004', 'admin', 'b0000000-0000-0000-0000-000000000001', NOW(), NOW(), NOW()),
  -- Remote TL Hang Le - Admin
  ('d0000000-0000-0000-0000-000000000005', 'c0000000-0000-0000-0000-000000000001',
   'b0000000-0000-0000-0000-000000000005', 'admin', 'b0000000-0000-0000-0000-000000000001', NOW(), NOW(), NOW()),
  -- Local Dev 1
  ('d0000000-0000-0000-0000-000000000006', 'c0000000-0000-0000-0000-000000000001',
   'b0000000-0000-0000-0000-000000000006', 'member', 'b0000000-0000-0000-0000-000000000004', NOW(), NOW(), NOW()),
  -- Local Dev 2
  ('d0000000-0000-0000-0000-000000000007', 'c0000000-0000-0000-0000-000000000001',
   'b0000000-0000-0000-0000-000000000007', 'member', 'b0000000-0000-0000-0000-000000000004', NOW(), NOW(), NOW()),
  -- Remote Dev 1
  ('d0000000-0000-0000-0000-000000000008', 'c0000000-0000-0000-0000-000000000001',
   'b0000000-0000-0000-0000-000000000008', 'member', 'b0000000-0000-0000-0000-000000000005', NOW(), NOW(), NOW()),
  -- Remote Dev 2
  ('d0000000-0000-0000-0000-000000000009', 'c0000000-0000-0000-0000-000000000001',
   'b0000000-0000-0000-0000-000000000009', 'member', 'b0000000-0000-0000-0000-000000000005', NOW(), NOW(), NOW()),
  -- QA Lead
  ('d0000000-0000-0000-0000-000000000010', 'c0000000-0000-0000-0000-000000000001',
   'b0000000-0000-0000-0000-000000000010', 'member', 'b0000000-0000-0000-0000-000000000001', NOW(), NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- NQH-Bot Analytics Module (Remote Team)
INSERT INTO project_members (id, project_id, user_id, role, invited_by, invited_at, joined_at, created_at)
VALUES
  ('d0000000-0000-0000-0000-000000000011', 'c0000000-0000-0000-0000-000000000002',
   'b0000000-0000-0000-0000-000000000005', 'owner', NULL, NOW(), NOW(), NOW()),
  ('d0000000-0000-0000-0000-000000000012', 'c0000000-0000-0000-0000-000000000002',
   'b0000000-0000-0000-0000-000000000008', 'member', 'b0000000-0000-0000-0000-000000000005', NOW(), NOW(), NOW()),
  ('d0000000-0000-0000-0000-000000000013', 'c0000000-0000-0000-0000-000000000002',
   'b0000000-0000-0000-0000-000000000009', 'member', 'b0000000-0000-0000-0000-000000000005', NOW(), NOW(), NOW()),
  ('d0000000-0000-0000-0000-000000000014', 'c0000000-0000-0000-0000-000000000002',
   'b0000000-0000-0000-0000-000000000001', 'admin', NULL, NOW(), NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- NQH-Bot NLP Engine (Local Team)
INSERT INTO project_members (id, project_id, user_id, role, invited_by, invited_at, joined_at, created_at)
VALUES
  ('d0000000-0000-0000-0000-000000000015', 'c0000000-0000-0000-0000-000000000003',
   'b0000000-0000-0000-0000-000000000004', 'owner', NULL, NOW(), NOW(), NOW()),
  ('d0000000-0000-0000-0000-000000000016', 'c0000000-0000-0000-0000-000000000003',
   'b0000000-0000-0000-0000-000000000006', 'member', 'b0000000-0000-0000-0000-000000000004', NOW(), NOW(), NOW()),
  ('d0000000-0000-0000-0000-000000000017', 'c0000000-0000-0000-0000-000000000003',
   'b0000000-0000-0000-0000-000000000007', 'member', 'b0000000-0000-0000-0000-000000000004', NOW(), NOW(), NOW()),
  ('d0000000-0000-0000-0000-000000000018', 'c0000000-0000-0000-0000-000000000003',
   'b0000000-0000-0000-0000-000000000003', 'admin', NULL, NOW(), NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- NQH-Bot CRM Integration (CTO + Both Teams)
INSERT INTO project_members (id, project_id, user_id, role, invited_by, invited_at, joined_at, created_at)
VALUES
  ('d0000000-0000-0000-0000-000000000019', 'c0000000-0000-0000-0000-000000000004',
   'b0000000-0000-0000-0000-000000000003', 'owner', NULL, NOW(), NOW(), NOW()),
  ('d0000000-0000-0000-0000-000000000020', 'c0000000-0000-0000-0000-000000000004',
   'b0000000-0000-0000-0000-000000000004', 'admin', 'b0000000-0000-0000-0000-000000000003', NOW(), NOW(), NOW()),
  ('d0000000-0000-0000-0000-000000000021', 'c0000000-0000-0000-0000-000000000004',
   'b0000000-0000-0000-0000-000000000005', 'admin', 'b0000000-0000-0000-0000-000000000003', NOW(), NOW(), NOW()),
  ('d0000000-0000-0000-0000-000000000022', 'c0000000-0000-0000-0000-000000000004',
   'b0000000-0000-0000-0000-000000000010', 'member', 'b0000000-0000-0000-0000-000000000003', NOW(), NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- NQH-Bot Mobile App (CPO + Selected team)
INSERT INTO project_members (id, project_id, user_id, role, invited_by, invited_at, joined_at, created_at)
VALUES
  ('d0000000-0000-0000-0000-000000000023', 'c0000000-0000-0000-0000-000000000005',
   'b0000000-0000-0000-0000-000000000002', 'owner', NULL, NOW(), NOW(), NOW()),
  ('d0000000-0000-0000-0000-000000000024', 'c0000000-0000-0000-0000-000000000005',
   'b0000000-0000-0000-0000-000000000001', 'admin', NULL, NOW(), NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- Platform Admin access to all projects
INSERT INTO project_members (id, project_id, user_id, role, invited_by, invited_at, joined_at, created_at)
VALUES
  ('d0000000-0000-0000-0000-000000000025', 'c0000000-0000-0000-0000-000000000001',
   'a0000000-0000-0000-0000-000000000001', 'admin', NULL, NOW(), NOW(), NOW()),
  ('d0000000-0000-0000-0000-000000000026', 'c0000000-0000-0000-0000-000000000002',
   'a0000000-0000-0000-0000-000000000001', 'admin', NULL, NOW(), NOW(), NOW()),
  ('d0000000-0000-0000-0000-000000000027', 'c0000000-0000-0000-0000-000000000003',
   'a0000000-0000-0000-0000-000000000001', 'admin', NULL, NOW(), NOW(), NOW()),
  ('d0000000-0000-0000-0000-000000000028', 'c0000000-0000-0000-0000-000000000004',
   'a0000000-0000-0000-0000-000000000001', 'admin', NULL, NOW(), NOW(), NOW()),
  ('d0000000-0000-0000-0000-000000000029', 'c0000000-0000-0000-0000-000000000005',
   'a0000000-0000-0000-0000-000000000001', 'admin', NULL, NOW(), NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- =========================================================================
-- SECTION 6: GATES (FR1: Quality Gate Management)
-- =========================================================================
-- Gates for NQH-Bot Platform - covering all SDLC 5.1.3.1 stages

-- NQH-Bot Platform Main (WHY → WHAT → HOW complete, BUILD in progress)
INSERT INTO gates (id, project_id, gate_name, gate_type, stage, status, description, exit_criteria, created_by, created_at, updated_at, approved_at)
VALUES
  -- Stage 00: WHY
  ('e0000000-0000-0000-0000-000000000001', 'c0000000-0000-0000-0000-000000000001',
   'G0.1', 'PROBLEM_DEFINITION', 'WHY', 'APPROVED',
   'Problem validated: Enterprise chatbots have 40% failure rate in Vietnamese NLP, 70% user drop-off in complex workflows.',
   '["Problem statement documented", "User personas defined (5 types)", "Market research: $2B VN chatbot market"]'::jsonb,
   'b0000000-0000-0000-0000-000000000001', '2025-09-05 10:00:00', '2025-09-10 15:00:00', '2025-09-10 15:00:00'),

  ('e0000000-0000-0000-0000-000000000002', 'c0000000-0000-0000-0000-000000000001',
   'G0.2', 'SOLUTION_DIVERSITY', 'WHY', 'APPROVED',
   '5 solutions evaluated: Multi-channel bot with Vietnamese NLP selected. Ollama local AI for cost reduction.',
   '["5 solution alternatives evaluated", "ROI: 300% Year 1", "Ollama vs Claude cost analysis complete"]'::jsonb,
   'b0000000-0000-0000-0000-000000000001', '2025-09-10 10:00:00', '2025-09-15 16:00:00', '2025-09-15 16:00:00'),

  -- Stage 01: WHAT
  ('e0000000-0000-0000-0000-000000000003', 'c0000000-0000-0000-0000-000000000001',
   'G1', 'PLANNING_COMPLETE', 'WHAT', 'APPROVED',
   'FRD approved: 25 functional requirements. API spec 2,100 lines. Data model: 35 tables.',
   '["FRD complete (25 FRs)", "API spec defined (2,100 lines)", "Data model designed (35 tables)"]'::jsonb,
   'b0000000-0000-0000-0000-000000000002', '2025-09-20 09:00:00', '2025-09-30 14:00:00', '2025-09-30 14:00:00'),

  -- Stage 02: HOW
  ('e0000000-0000-0000-0000-000000000004', 'c0000000-0000-0000-0000-000000000001',
   'G2', 'DESIGN_READY', 'HOW', 'APPROVED',
   'Architecture: Microservices with event-driven messaging. Vietnamese NLP pipeline. Multi-channel integration.',
   '["Architecture document approved", "Security baseline OWASP ASVS L2", "Vietnamese NLP design complete"]'::jsonb,
   'b0000000-0000-0000-0000-000000000003', '2025-10-05 10:00:00', '2025-10-15 17:00:00', '2025-10-15 17:00:00'),

  -- Stage 03: BUILD (in progress)
  ('e0000000-0000-0000-0000-000000000005', 'c0000000-0000-0000-0000-000000000001',
   'G3', 'SHIP_READY', 'BUILD', 'PENDING_APPROVAL',
   'MVP 75% complete. Telegram + Zalo channels working. Vietnamese NLP: 85% accuracy. CRM sync in progress.',
   '["Core features implemented", "Unit tests 90%+", "Integration tests passing", "NLP accuracy 85%+"]'::jsonb,
   'b0000000-0000-0000-0000-000000000004', '2025-11-01 08:00:00', NOW(), NULL)
ON CONFLICT (id) DO NOTHING;

-- NQH-Bot Analytics Module (WHAT stage - Remote Team)
INSERT INTO gates (id, project_id, gate_name, gate_type, stage, status, description, exit_criteria, created_by, created_at, updated_at, approved_at)
VALUES
  ('e0000000-0000-0000-0000-000000000006', 'c0000000-0000-0000-0000-000000000002',
   'G0.1', 'PROBLEM_DEFINITION', 'WHY', 'APPROVED',
   'Problem: No visibility into bot performance. Businesses cant measure ROI.',
   '["Analytics requirements gathered", "KPI definitions documented"]'::jsonb,
   'b0000000-0000-0000-0000-000000000005', '2025-10-18 10:00:00', '2025-10-22 15:00:00', '2025-10-22 15:00:00'),

  ('e0000000-0000-0000-0000-000000000007', 'c0000000-0000-0000-0000-000000000002',
   'G0.2', 'SOLUTION_DIVERSITY', 'WHY', 'APPROVED',
   'Real-time dashboard with Grafana embed selected over custom charting.',
   '["3 alternatives evaluated", "Grafana AGPL containment validated"]'::jsonb,
   'b0000000-0000-0000-0000-000000000005', '2025-10-22 10:00:00', '2025-10-28 16:00:00', '2025-10-28 16:00:00'),

  ('e0000000-0000-0000-0000-000000000008', 'c0000000-0000-0000-0000-000000000002',
   'G1', 'PLANNING_COMPLETE', 'WHAT', 'PENDING_APPROVAL',
   'Analytics FRD 90% complete. Missing: Custom report builder specs.',
   '["FRD complete", "Dashboard wireframes approved", "Data warehouse schema"]'::jsonb,
   'b0000000-0000-0000-0000-000000000008', '2025-11-05 09:00:00', NOW(), NULL)
ON CONFLICT (id) DO NOTHING;

-- NQH-Bot NLP Engine (HOW stage - Local Team)
INSERT INTO gates (id, project_id, gate_name, gate_type, stage, status, description, exit_criteria, created_by, created_at, updated_at, approved_at)
VALUES
  ('e0000000-0000-0000-0000-000000000009', 'c0000000-0000-0000-0000-000000000003',
   'G0.1', 'PROBLEM_DEFINITION', 'WHY', 'APPROVED',
   'Problem: Vietnamese NLP accuracy in existing solutions: 60%. Target: 90%+.',
   '["Vietnamese NLP benchmarks documented", "5 competitor analysis complete"]'::jsonb,
   'b0000000-0000-0000-0000-000000000004', '2025-10-05 10:00:00', '2025-10-10 15:00:00', '2025-10-10 15:00:00'),

  ('e0000000-0000-0000-0000-000000000010', 'c0000000-0000-0000-0000-000000000003',
   'G0.2', 'SOLUTION_DIVERSITY', 'WHY', 'APPROVED',
   'Hybrid approach: Ollama (local) + Claude fallback (complex queries). 95% cost reduction.',
   '["Ollama vs GPT-4 benchmarks", "Cost analysis: $50 vs $1000/month", "Latency: <100ms target"]'::jsonb,
   'b0000000-0000-0000-0000-000000000004', '2025-10-10 10:00:00', '2025-10-15 16:00:00', '2025-10-15 16:00:00'),

  ('e0000000-0000-0000-0000-000000000011', 'c0000000-0000-0000-0000-000000000003',
   'G1', 'PLANNING_COMPLETE', 'WHAT', 'APPROVED',
   'NLP Engine FRD: Intent detection, entity extraction, sentiment analysis.',
   '["NLP pipeline designed", "Training data spec", "Ollama integration contract"]'::jsonb,
   'b0000000-0000-0000-0000-000000000006', '2025-10-20 09:00:00', '2025-10-28 14:00:00', '2025-10-28 14:00:00'),

  ('e0000000-0000-0000-0000-000000000012', 'c0000000-0000-0000-0000-000000000003',
   'G2', 'DESIGN_READY', 'HOW', 'DRAFT',
   'NLP architecture 80% complete. Missing: Fallback strategy documentation.',
   '["NLP pipeline architecture", "Model selection rationale", "Fallback chain design"]'::jsonb,
   'b0000000-0000-0000-0000-000000000006', '2025-11-10 10:00:00', NOW(), NULL)
ON CONFLICT (id) DO NOTHING;

-- NQH-Bot CRM Integration (VERIFY stage - CTO led)
INSERT INTO gates (id, project_id, gate_name, gate_type, stage, status, description, exit_criteria, created_by, created_at, updated_at, approved_at)
VALUES
  ('e0000000-0000-0000-0000-000000000013', 'c0000000-0000-0000-0000-000000000004',
   'G0.1', 'PROBLEM_DEFINITION', 'WHY', 'APPROVED',
   'Problem: Bot conversations not synced to CRM. Sales team loses context.',
   '["CRM integration requirements", "Data mapping documented"]'::jsonb,
   'b0000000-0000-0000-0000-000000000003', '2025-08-20 10:00:00', '2025-08-25 15:00:00', '2025-08-25 15:00:00'),

  ('e0000000-0000-0000-0000-000000000014', 'c0000000-0000-0000-0000-000000000004',
   'G0.2', 'SOLUTION_DIVERSITY', 'WHY', 'APPROVED',
   'Webhook-based sync selected. Supports Salesforce, HubSpot, custom CRMs.',
   '["3 integration patterns evaluated", "Webhook vs API poll comparison"]'::jsonb,
   'b0000000-0000-0000-0000-000000000003', '2025-08-25 10:00:00', '2025-09-01 16:00:00', '2025-09-01 16:00:00'),

  ('e0000000-0000-0000-0000-000000000015', 'c0000000-0000-0000-0000-000000000004',
   'G1', 'PLANNING_COMPLETE', 'WHAT', 'APPROVED',
   'CRM Integration FRD complete. Supports 3 major CRMs + custom webhook.',
   '["FRD approved", "API contracts for 3 CRMs", "Error handling spec"]'::jsonb,
   'b0000000-0000-0000-0000-000000000004', '2025-09-10 09:00:00', '2025-09-20 14:00:00', '2025-09-20 14:00:00'),

  ('e0000000-0000-0000-0000-000000000016', 'c0000000-0000-0000-0000-000000000004',
   'G2', 'DESIGN_READY', 'HOW', 'APPROVED',
   'CRM adapter pattern. Event-driven sync. Retry with exponential backoff.',
   '["Architecture document approved", "Adapter pattern documented"]'::jsonb,
   'b0000000-0000-0000-0000-000000000003', '2025-10-01 10:00:00', '2025-10-10 17:00:00', '2025-10-10 17:00:00'),

  ('e0000000-0000-0000-0000-000000000017', 'c0000000-0000-0000-0000-000000000004',
   'G3', 'SHIP_READY', 'BUILD', 'APPROVED',
   'CRM integration MVP complete. Salesforce + HubSpot working. 99.9% sync reliability.',
   '["Core sync working", "Tests passing", "Performance: <500ms sync"]'::jsonb,
   'b0000000-0000-0000-0000-000000000003', '2025-10-20 08:00:00', '2025-11-05 18:00:00', '2025-11-05 18:00:00'),

  ('e0000000-0000-0000-0000-000000000018', 'c0000000-0000-0000-0000-000000000004',
   'G4', 'TEST_COMPLETE', 'VERIFY', 'PENDING_APPROVAL',
   'Testing: Unit 92%, Integration 88%, E2E 75%. Pending: Load test results.',
   '["Unit tests 95%+", "Integration tests 90%+", "Load test: 1000 req/s"]'::jsonb,
   'b0000000-0000-0000-0000-000000000010', '2025-11-10 08:00:00', NOW(), NULL)
ON CONFLICT (id) DO NOTHING;

-- NQH-Bot Mobile App (WHY stage - new project)
INSERT INTO gates (id, project_id, gate_name, gate_type, stage, status, description, exit_criteria, created_by, created_at, updated_at, approved_at)
VALUES
  ('e0000000-0000-0000-0000-000000000019', 'c0000000-0000-0000-0000-000000000005',
   'G0.1', 'PROBLEM_DEFINITION', 'WHY', 'DRAFT',
   'Problem statement in progress: Mobile bot management for on-the-go admin.',
   '["Problem statement documented", "Mobile-specific user research"]'::jsonb,
   'b0000000-0000-0000-0000-000000000002', NOW(), NOW(), NULL)
ON CONFLICT (id) DO NOTHING;

-- =========================================================================
-- SECTION 7: GATE APPROVALS - NQH-Bot Platform
-- Approval history for approved gates
-- =========================================================================

INSERT INTO gate_approvals (id, gate_id, approver_id, status, comment, approved_at, created_at)
VALUES
  -- NQH-Bot Platform G0.1 approval (CEO Tai Dang)
  ('f0000000-0000-0000-0000-000000000001', 'e0000000-0000-0000-0000-000000000001',
   'b0000000-0000-0000-0000-000000000002', 'APPROVED',
   'Problem statement clear: Vietnamese NLP gap validated. Market research solid. Approved.',
   '2025-09-10 15:00:00', '2025-09-10 15:00:00'),

  -- NQH-Bot Platform G0.2 approval (CPO Dung Luong)
  ('f0000000-0000-0000-0000-000000000002', 'e0000000-0000-0000-0000-000000000002',
   'b0000000-0000-0000-0000-000000000002', 'APPROVED',
   '5 solutions well explored. Ollama cost savings validated. Excellent ROI projection.',
   '2025-09-15 16:00:00', '2025-09-15 16:00:00'),

  -- NQH-Bot Platform G1 approval (dual: CTO + CPO)
  ('f0000000-0000-0000-0000-000000000003', 'e0000000-0000-0000-0000-000000000003',
   'b0000000-0000-0000-0000-000000000003', 'APPROVED',
   'Technical requirements sound. API spec comprehensive (2,100 lines). Data model well-designed.',
   '2025-09-29 14:00:00', '2025-09-29 14:00:00'),
  ('f0000000-0000-0000-0000-000000000004', 'e0000000-0000-0000-0000-000000000003',
   'b0000000-0000-0000-0000-000000000002', 'APPROVED',
   'Business requirements align with market needs. 25 FRs cover all use cases.',
   '2025-09-30 14:00:00', '2025-09-30 14:00:00'),

  -- NQH-Bot Platform G2 approval (CTO Hiep Dinh)
  ('f0000000-0000-0000-0000-000000000005', 'e0000000-0000-0000-0000-000000000004',
   'b0000000-0000-0000-0000-000000000003', 'APPROVED',
   'Microservices architecture approved. Vietnamese NLP pipeline well-designed. OWASP L2 compliance.',
   '2025-10-15 17:00:00', '2025-10-15 17:00:00'),

  -- NQH-Bot Analytics G0.1 approval (Hang Le)
  ('f0000000-0000-0000-0000-000000000006', 'e0000000-0000-0000-0000-000000000006',
   'b0000000-0000-0000-0000-000000000001', 'APPROVED',
   'Analytics requirements clear. KPI definitions comprehensive.',
   '2025-10-22 15:00:00', '2025-10-22 15:00:00'),

  -- NQH-Bot Analytics G0.2 approval (CEO Tai Dang)
  ('f0000000-0000-0000-0000-000000000007', 'e0000000-0000-0000-0000-000000000007',
   'b0000000-0000-0000-0000-000000000001', 'APPROVED',
   'Grafana embed approach approved. AGPL containment validated.',
   '2025-10-28 16:00:00', '2025-10-28 16:00:00'),

  -- NQH-Bot NLP Engine G0.1 approval (CTO Hiep Dinh)
  ('f0000000-0000-0000-0000-000000000008', 'e0000000-0000-0000-0000-000000000009',
   'b0000000-0000-0000-0000-000000000003', 'APPROVED',
   'Vietnamese NLP benchmarks well-documented. Competitor analysis thorough.',
   '2025-10-10 15:00:00', '2025-10-10 15:00:00'),

  -- NQH-Bot NLP Engine G0.2 approval (CEO + CTO)
  ('f0000000-0000-0000-0000-000000000009', 'e0000000-0000-0000-0000-000000000010',
   'b0000000-0000-0000-0000-000000000001', 'APPROVED',
   'Ollama hybrid approach approved. 95% cost savings validated.',
   '2025-10-14 16:00:00', '2025-10-14 16:00:00'),
  ('f0000000-0000-0000-0000-000000000010', 'e0000000-0000-0000-0000-000000000010',
   'b0000000-0000-0000-0000-000000000003', 'APPROVED',
   'Technical feasibility confirmed. Latency targets achievable.',
   '2025-10-15 16:00:00', '2025-10-15 16:00:00'),

  -- NQH-Bot NLP Engine G1 approval (CTO)
  ('f0000000-0000-0000-0000-000000000011', 'e0000000-0000-0000-0000-000000000011',
   'b0000000-0000-0000-0000-000000000003', 'APPROVED',
   'NLP Engine FRD approved. Training data spec comprehensive.',
   '2025-10-28 14:00:00', '2025-10-28 14:00:00'),

  -- NQH-Bot CRM Integration (all gates through G3)
  ('f0000000-0000-0000-0000-000000000012', 'e0000000-0000-0000-0000-000000000013',
   'b0000000-0000-0000-0000-000000000001', 'APPROVED',
   'CRM integration requirements clear.',
   '2025-08-25 15:00:00', '2025-08-25 15:00:00'),
  ('f0000000-0000-0000-0000-000000000013', 'e0000000-0000-0000-0000-000000000014',
   'b0000000-0000-0000-0000-000000000001', 'APPROVED',
   'Webhook approach approved.',
   '2025-09-01 16:00:00', '2025-09-01 16:00:00'),
  ('f0000000-0000-0000-0000-000000000014', 'e0000000-0000-0000-0000-000000000015',
   'b0000000-0000-0000-0000-000000000003', 'APPROVED',
   'FRD comprehensive. 3 CRM support confirmed.',
   '2025-09-20 14:00:00', '2025-09-20 14:00:00'),
  ('f0000000-0000-0000-0000-000000000015', 'e0000000-0000-0000-0000-000000000016',
   'b0000000-0000-0000-0000-000000000003', 'APPROVED',
   'Adapter pattern well-designed.',
   '2025-10-10 17:00:00', '2025-10-10 17:00:00'),
  ('f0000000-0000-0000-0000-000000000016', 'e0000000-0000-0000-0000-000000000017',
   'b0000000-0000-0000-0000-000000000003', 'APPROVED',
   'CRM MVP approved. 99.9% reliability impressive.',
   '2025-11-05 18:00:00', '2025-11-05 18:00:00')
ON CONFLICT (id) DO NOTHING;

-- =========================================================================
-- SECTION 8: GATE EVIDENCE (FR2: Evidence Vault) - NQH-Bot Platform
-- Sample evidence documents for gates
-- =========================================================================

INSERT INTO gate_evidence (id, gate_id, evidence_type, title, description, file_path, file_name, file_size, mime_type, sha256_hash, uploaded_by, created_at, updated_at)
VALUES
  -- NQH-Bot Platform G0.1 evidence
  ('g0000000-0000-0000-0000-000000000001', 'e0000000-0000-0000-0000-000000000001',
   'DOCUMENT', 'NQH-Bot Problem Statement', 'Vietnamese chatbot market analysis and pain points',
   's3://evidence-vault/nqh-bot/g01/problem-statement.pdf', 'problem-statement.pdf',
   2048576, 'application/pdf', 'a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef12345678',
   'b0000000-0000-0000-0000-000000000001', '2025-09-06 11:00:00', '2025-09-06 11:00:00'),

  ('g0000000-0000-0000-0000-000000000002', 'e0000000-0000-0000-0000-000000000001',
   'DATA', 'Enterprise Chatbot Survey', 'Survey of 50 Vietnamese enterprises on chatbot usage',
   's3://evidence-vault/nqh-bot/g01/enterprise-survey.xlsx', 'enterprise-survey.xlsx',
   524288, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
   'b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456789a',
   'b0000000-0000-0000-0000-000000000002', '2025-09-07 14:00:00', '2025-09-07 14:00:00'),

  ('g0000000-0000-0000-0000-000000000003', 'e0000000-0000-0000-0000-000000000001',
   'DOCUMENT', 'Market Research: Vietnam Chatbot Market', '$2B TAM, 35% CAGR analysis',
   's3://evidence-vault/nqh-bot/g01/market-research.pdf', 'market-research.pdf',
   3145728, 'application/pdf', 'c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456789ab1',
   'b0000000-0000-0000-0000-000000000002', '2025-09-08 10:00:00', '2025-09-08 10:00:00'),

  -- NQH-Bot Platform G0.2 evidence
  ('g0000000-0000-0000-0000-000000000004', 'e0000000-0000-0000-0000-000000000002',
   'DOCUMENT', 'Solution Alternatives Analysis', '5 approaches: Ollama local, Claude API, GPT-4, Rule-based, Hybrid',
   's3://evidence-vault/nqh-bot/g02/solution-analysis.pdf', 'solution-analysis.pdf',
   4194304, 'application/pdf', 'd4e5f6789012345678901234567890abcdef1234567890abcdef123456789ab1c2',
   'b0000000-0000-0000-0000-000000000003', '2025-09-12 09:00:00', '2025-09-12 09:00:00'),

  ('g0000000-0000-0000-0000-000000000005', 'e0000000-0000-0000-0000-000000000002',
   'DATA', 'Ollama vs Claude Cost Analysis', 'Monthly cost comparison: $50 vs $1000',
   's3://evidence-vault/nqh-bot/g02/cost-analysis.xlsx', 'cost-analysis.xlsx',
   256000, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
   'e5f6789012345678901234567890abcdef1234567890abcdef123456789ab1c2d3',
   'b0000000-0000-0000-0000-000000000003', '2025-09-13 11:00:00', '2025-09-13 11:00:00'),

  -- NQH-Bot Platform G1 evidence
  ('g0000000-0000-0000-0000-000000000006', 'e0000000-0000-0000-0000-000000000003',
   'DOCUMENT', 'Functional Requirements Document', 'NQH-Bot FRD with 25 functional requirements',
   's3://evidence-vault/nqh-bot/g1/frd.pdf', 'nqh-bot-frd.pdf',
   5242880, 'application/pdf', 'f6789012345678901234567890abcdef1234567890abcdef123456789ab1c2d3e4',
   'b0000000-0000-0000-0000-000000000002', '2025-09-22 09:00:00', '2025-09-22 09:00:00'),

  ('g0000000-0000-0000-0000-000000000007', 'e0000000-0000-0000-0000-000000000003',
   'CODE', 'API Specification', 'OpenAPI 3.0 specification (2,100 lines)',
   's3://evidence-vault/nqh-bot/g1/openapi.yaml', 'openapi.yaml',
   128000, 'application/x-yaml', '6789012345678901234567890abcdef1234567890abcdef123456789ab1c2d3e4f5',
   'b0000000-0000-0000-0000-000000000004', '2025-09-25 11:00:00', '2025-09-25 11:00:00'),

  ('g0000000-0000-0000-0000-000000000008', 'e0000000-0000-0000-0000-000000000003',
   'DIAGRAM', 'Data Model ERD', 'Entity-Relationship Diagram for 35 tables',
   's3://evidence-vault/nqh-bot/g1/data-model-erd.png', 'data-model-erd.png',
   1048576, 'image/png', '789012345678901234567890abcdef1234567890abcdef123456789ab1c2d3e4f56',
   'b0000000-0000-0000-0000-000000000004', '2025-09-26 14:00:00', '2025-09-26 14:00:00'),

  -- NQH-Bot Platform G2 evidence
  ('g0000000-0000-0000-0000-000000000009', 'e0000000-0000-0000-0000-000000000004',
   'DOCUMENT', 'System Architecture Document', 'Microservices with event-driven messaging',
   's3://evidence-vault/nqh-bot/g2/system-architecture.pdf', 'system-architecture.pdf',
   4194304, 'application/pdf', '89012345678901234567890abcdef1234567890abcdef123456789ab1c2d3e4f567',
   'b0000000-0000-0000-0000-000000000003', '2025-10-08 10:00:00', '2025-10-08 10:00:00'),

  ('g0000000-0000-0000-0000-000000000010', 'e0000000-0000-0000-0000-000000000004',
   'DOCUMENT', 'Vietnamese NLP Pipeline Design', 'Intent detection, entity extraction, sentiment',
   's3://evidence-vault/nqh-bot/g2/nlp-pipeline-design.pdf', 'nlp-pipeline-design.pdf',
   3145728, 'application/pdf', '9012345678901234567890abcdef1234567890abcdef123456789ab1c2d3e4f5678',
   'b0000000-0000-0000-0000-000000000004', '2025-10-10 11:00:00', '2025-10-10 11:00:00'),

  ('g0000000-0000-0000-0000-000000000011', 'e0000000-0000-0000-0000-000000000004',
   'DOCUMENT', 'Security Baseline', 'OWASP ASVS Level 2 compliance checklist',
   's3://evidence-vault/nqh-bot/g2/security-baseline.pdf', 'security-baseline.pdf',
   2097152, 'application/pdf', '012345678901234567890abcdef1234567890abcdef123456789ab1c2d3e4f56789',
   'b0000000-0000-0000-0000-000000000003', '2025-10-12 11:00:00', '2025-10-12 11:00:00'),

  -- NQH-Bot CRM G4 evidence (testing phase)
  ('g0000000-0000-0000-0000-000000000012', 'e0000000-0000-0000-0000-000000000018',
   'REPORT', 'Test Coverage Report', 'Unit 92%, Integration 88%, E2E 75%',
   's3://evidence-vault/nqh-bot-crm/g4/coverage-report.html', 'coverage-report.html',
   524288, 'text/html', '12345678901234567890abcdef1234567890abcdef123456789ab1c2d3e4f567890a',
   'b0000000-0000-0000-0000-000000000010', '2025-11-15 16:00:00', NOW()),

  ('g0000000-0000-0000-0000-000000000013', 'e0000000-0000-0000-0000-000000000018',
   'REPORT', 'Integration Test Results', 'Salesforce + HubSpot integration tests passing',
   's3://evidence-vault/nqh-bot-crm/g4/integration-tests.html', 'integration-tests.html',
   256000, 'text/html', '2345678901234567890abcdef1234567890abcdef123456789ab1c2d3e4f567890ab',
   'b0000000-0000-0000-0000-000000000010', '2025-11-18 10:00:00', NOW())
ON CONFLICT (id) DO NOTHING;

-- =========================================================================
-- SECTION 9: POLICIES (FR5: Policy Pack Library)
-- Policy packs and individual policies
-- =========================================================================

INSERT INTO policies (id, name, description, stage, rego_code, is_active, version, created_by, created_at, updated_at)
VALUES
  -- Stage 00: WHY policies
  ('h0000000-0000-0000-0000-000000000001', 'problem_statement_required',
   'Problem statement document must be uploaded', 'WHY',
   'package sdlc.why.problem

default allow = false

allow {
  count(input.evidence) > 0
  some e in input.evidence
  e.type == "DOCUMENT"
  contains(lower(e.title), "problem")
}',
   true, '1.0.0', 'a0000000-0000-0000-0000-000000000001', NOW(), NOW()),

  ('h0000000-0000-0000-0000-000000000002', 'user_research_required',
   'User research or survey data must be provided', 'WHY',
   'package sdlc.why.research

default allow = false

allow {
  count(input.evidence) > 0
  some e in input.evidence
  e.type == "DATA"
}',
   true, '1.0.0', 'a0000000-0000-0000-0000-000000000001', NOW(), NOW()),

  ('h0000000-0000-0000-0000-000000000003', 'solution_alternatives_required',
   'At least 3 solution alternatives must be evaluated', 'WHY',
   'package sdlc.why.solutions

default allow = false

allow {
  input.solution_count >= 3
}',
   true, '1.0.0', 'a0000000-0000-0000-0000-000000000001', NOW(), NOW()),

  -- Stage 01: WHAT policies
  ('h0000000-0000-0000-0000-000000000004', 'frd_required',
   'Functional Requirements Document must be uploaded', 'WHAT',
   'package sdlc.what.frd

default allow = false

allow {
  some e in input.evidence
  e.type == "DOCUMENT"
  contains(lower(e.title), "functional")
  contains(lower(e.title), "requirement")
}',
   true, '1.0.0', 'a0000000-0000-0000-0000-000000000001', NOW(), NOW()),

  ('h0000000-0000-0000-0000-000000000005', 'api_spec_required',
   'API specification (OpenAPI) must be provided for API projects', 'WHAT',
   'package sdlc.what.api

default allow = false

allow {
  some e in input.evidence
  e.type == "CODE"
  endswith(e.file_name, ".yaml")
}

allow {
  some e in input.evidence
  e.type == "CODE"
  endswith(e.file_name, ".json")
}',
   true, '1.0.0', 'a0000000-0000-0000-0000-000000000001', NOW(), NOW()),

  ('h0000000-0000-0000-0000-000000000006', 'data_model_required',
   'Data model or ERD must be provided', 'WHAT',
   'package sdlc.what.data

default allow = false

allow {
  some e in input.evidence
  e.type == "DIAGRAM"
  contains(lower(e.title), "data")
}

allow {
  some e in input.evidence
  e.type == "DIAGRAM"
  contains(lower(e.title), "erd")
}',
   true, '1.0.0', 'a0000000-0000-0000-0000-000000000001', NOW(), NOW()),

  -- Stage 02: HOW policies
  ('h0000000-0000-0000-0000-000000000007', 'architecture_doc_required',
   'System architecture document must be uploaded', 'HOW',
   'package sdlc.how.architecture

default allow = false

allow {
  some e in input.evidence
  e.type == "DOCUMENT"
  contains(lower(e.title), "architecture")
}',
   true, '1.0.0', 'a0000000-0000-0000-0000-000000000001', NOW(), NOW()),

  ('h0000000-0000-0000-0000-000000000008', 'security_baseline_required',
   'Security baseline document must be provided', 'HOW',
   'package sdlc.how.security

default allow = false

allow {
  some e in input.evidence
  e.type == "DOCUMENT"
  contains(lower(e.title), "security")
}',
   true, '1.0.0', 'a0000000-0000-0000-0000-000000000001', NOW(), NOW()),

  -- Stage 04: VERIFY policies
  ('h0000000-0000-0000-0000-000000000009', 'test_coverage_threshold',
   'Code coverage must be at least 80%', 'VERIFY',
   'package sdlc.verify.coverage

default allow = false

allow {
  input.coverage >= 80
}',
   true, '1.0.0', 'a0000000-0000-0000-0000-000000000001', NOW(), NOW()),

  ('h0000000-0000-0000-0000-000000000010', 'no_critical_bugs',
   'No critical or blocker bugs in bug tracker', 'VERIFY',
   'package sdlc.verify.bugs

default allow = false

allow {
  input.critical_bugs == 0
  input.blocker_bugs == 0
}',
   true, '1.0.0', 'a0000000-0000-0000-0000-000000000001', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- =========================================================================
-- SECTION 10: POLICY EVALUATIONS - NQH-Bot Platform
-- Sample policy evaluation results
-- =========================================================================

INSERT INTO policy_evaluations (id, gate_id, policy_id, result, details, evaluated_at, created_at)
VALUES
  -- NQH-Bot Platform G0.1 evaluations
  ('i0000000-0000-0000-0000-000000000001', 'e0000000-0000-0000-0000-000000000001',
   'h0000000-0000-0000-0000-000000000001', 'PASS',
   '{"message": "Problem statement document found", "evidence_id": "g0000000-0000-0000-0000-000000000001"}'::jsonb,
   '2025-09-09 14:00:00', '2025-09-09 14:00:00'),

  ('i0000000-0000-0000-0000-000000000002', 'e0000000-0000-0000-0000-000000000001',
   'h0000000-0000-0000-0000-000000000002', 'PASS',
   '{"message": "Enterprise chatbot survey found", "evidence_id": "g0000000-0000-0000-0000-000000000002"}'::jsonb,
   '2025-09-09 14:00:00', '2025-09-09 14:00:00'),

  -- NQH-Bot Platform G1 evaluations
  ('i0000000-0000-0000-0000-000000000003', 'e0000000-0000-0000-0000-000000000003',
   'h0000000-0000-0000-0000-000000000004', 'PASS',
   '{"message": "FRD document found", "evidence_id": "g0000000-0000-0000-0000-000000000006"}'::jsonb,
   '2025-09-28 10:00:00', '2025-09-28 10:00:00'),

  ('i0000000-0000-0000-0000-000000000004', 'e0000000-0000-0000-0000-000000000003',
   'h0000000-0000-0000-0000-000000000005', 'PASS',
   '{"message": "OpenAPI spec found (2,100 lines)", "evidence_id": "g0000000-0000-0000-0000-000000000007"}'::jsonb,
   '2025-09-28 10:00:00', '2025-09-28 10:00:00'),

  ('i0000000-0000-0000-0000-000000000005', 'e0000000-0000-0000-0000-000000000003',
   'h0000000-0000-0000-0000-000000000006', 'PASS',
   '{"message": "Data model ERD found (35 tables)", "evidence_id": "g0000000-0000-0000-0000-000000000008"}'::jsonb,
   '2025-09-28 10:00:00', '2025-09-28 10:00:00'),

  -- NQH-Bot Platform G2 evaluations
  ('i0000000-0000-0000-0000-000000000006', 'e0000000-0000-0000-0000-000000000004',
   'h0000000-0000-0000-0000-000000000007', 'PASS',
   '{"message": "Architecture document found", "evidence_id": "g0000000-0000-0000-0000-000000000009"}'::jsonb,
   '2025-10-14 16:00:00', '2025-10-14 16:00:00'),

  ('i0000000-0000-0000-0000-000000000007', 'e0000000-0000-0000-0000-000000000004',
   'h0000000-0000-0000-0000-000000000008', 'PASS',
   '{"message": "Security baseline found", "evidence_id": "g0000000-0000-0000-0000-000000000011"}'::jsonb,
   '2025-10-14 16:00:00', '2025-10-14 16:00:00'),

  -- NQH-Bot CRM G4 evaluations
  ('i0000000-0000-0000-0000-000000000008', 'e0000000-0000-0000-0000-000000000018',
   'h0000000-0000-0000-0000-000000000009', 'PASS',
   '{"message": "Test coverage: 92% (threshold: 80%)", "coverage": 92}'::jsonb,
   '2025-11-15 10:00:00', '2025-11-15 10:00:00'),

  ('i0000000-0000-0000-0000-000000000009', 'e0000000-0000-0000-0000-000000000018',
   'h0000000-0000-0000-0000-000000000010', 'PASS',
   '{"message": "No critical bugs found", "critical_bugs": 0, "blocker_bugs": 0}'::jsonb,
   '2025-11-15 10:00:00', '2025-11-15 10:00:00')
ON CONFLICT (id) DO NOTHING;

-- =========================================================================
-- SECTION 11: AUDIT LOGS - NQH-Bot Platform
-- Sample audit trail entries for E2E testing
-- =========================================================================

INSERT INTO audit_logs (id, user_id, action, entity_type, entity_id, details, ip_address, user_agent, created_at)
VALUES
  -- CEO Tai Dang creates NQH-Bot Platform project
  ('j0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000001',
   'CREATE', 'PROJECT', 'c0000000-0000-0000-0000-000000000001',
   '{"project_name": "NQH-Bot Platform", "owner": "Tai Dang"}'::jsonb,
   '192.168.1.100', 'Mozilla/5.0 Chrome/119.0', '2025-09-01 09:00:00'),

  -- CEO creates G0.1 gate
  ('j0000000-0000-0000-0000-000000000002', 'b0000000-0000-0000-0000-000000000001',
   'CREATE', 'GATE', 'e0000000-0000-0000-0000-000000000001',
   '{"gate_name": "G0.1", "stage": "WHY", "type": "PROBLEM_DEFINITION"}'::jsonb,
   '192.168.1.100', 'Mozilla/5.0 Chrome/119.0', '2025-09-05 10:00:00'),

  -- CEO uploads problem statement
  ('j0000000-0000-0000-0000-000000000003', 'b0000000-0000-0000-0000-000000000001',
   'UPLOAD', 'EVIDENCE', 'g0000000-0000-0000-0000-000000000001',
   '{"file_name": "problem-statement.pdf", "file_size": 2048576}'::jsonb,
   '192.168.1.100', 'Mozilla/5.0 Chrome/119.0', '2025-09-06 11:00:00'),

  -- CPO Dung Luong approves G0.1
  ('j0000000-0000-0000-0000-000000000004', 'b0000000-0000-0000-0000-000000000002',
   'APPROVE', 'GATE', 'e0000000-0000-0000-0000-000000000001',
   '{"status": "APPROVED", "comment": "Vietnamese NLP gap validated. Market research solid."}'::jsonb,
   '192.168.1.101', 'Mozilla/5.0 Chrome/119.0', '2025-09-10 15:00:00'),

  -- CTO Hiep Dinh reviews architecture
  ('j0000000-0000-0000-0000-000000000005', 'b0000000-0000-0000-0000-000000000003',
   'APPROVE', 'GATE', 'e0000000-0000-0000-0000-000000000004',
   '{"status": "APPROVED", "comment": "Microservices architecture approved. OWASP L2 compliance."}'::jsonb,
   '192.168.1.102', 'Mozilla/5.0 Chrome/119.0', '2025-10-15 17:00:00'),

  -- Local TL Endior uploads NLP design
  ('j0000000-0000-0000-0000-000000000006', 'b0000000-0000-0000-0000-000000000004',
   'UPLOAD', 'EVIDENCE', 'g0000000-0000-0000-0000-000000000010',
   '{"file_name": "nlp-pipeline-design.pdf", "file_size": 3145728}'::jsonb,
   '192.168.1.103', 'Mozilla/5.0 Chrome/119.0', '2025-10-10 11:00:00'),

  -- Remote TL Hang Le creates Analytics module
  ('j0000000-0000-0000-0000-000000000007', 'b0000000-0000-0000-0000-000000000005',
   'CREATE', 'PROJECT', 'c0000000-0000-0000-0000-000000000002',
   '{"project_name": "NQH-Bot Analytics Module", "team": "Remote Team"}'::jsonb,
   '192.168.1.104', 'Mozilla/5.0 Chrome/119.0', '2025-10-15 10:00:00'),

  -- QA Lead uploads test coverage
  ('j0000000-0000-0000-0000-000000000008', 'b0000000-0000-0000-0000-000000000010',
   'UPLOAD', 'EVIDENCE', 'g0000000-0000-0000-0000-000000000012',
   '{"file_name": "coverage-report.html", "coverage": "92%"}'::jsonb,
   '192.168.1.105', 'Mozilla/5.0 Chrome/119.0', '2025-11-15 16:00:00'),

  -- Platform Admin login
  ('j0000000-0000-0000-0000-000000000009', 'a0000000-0000-0000-0000-000000000001',
   'LOGIN', 'USER', 'a0000000-0000-0000-0000-000000000001',
   '{"method": "email_password"}'::jsonb,
   '192.168.1.1', 'Mozilla/5.0 Chrome/119.0', NOW())
ON CONFLICT (id) DO NOTHING;

-- =========================================================================
-- SECTION 12: VERIFICATION QUERIES
-- Run these queries to verify seed data is loaded correctly
-- =========================================================================

-- Verify users count
SELECT 'Users' as entity, COUNT(*) as count FROM users;

-- Verify projects count (active only)
SELECT 'Active Projects' as entity, COUNT(*) as count FROM projects WHERE deleted_at IS NULL AND is_active = true;

-- Verify gates count by status
SELECT 'Gates by Status' as description;
SELECT status, COUNT(*) as count FROM gates WHERE deleted_at IS NULL GROUP BY status ORDER BY count DESC;

-- Verify evidence count
SELECT 'Evidence Files' as entity, COUNT(*) as count FROM gate_evidence WHERE deleted_at IS NULL;

-- Verify policies count
SELECT 'Active Policies' as entity, COUNT(*) as count FROM policies WHERE is_active = true;

-- Summary report
SELECT
  (SELECT COUNT(*) FROM users) as total_users,
  (SELECT COUNT(*) FROM projects WHERE deleted_at IS NULL AND is_active = true) as active_projects,
  (SELECT COUNT(*) FROM gates WHERE deleted_at IS NULL) as total_gates,
  (SELECT COUNT(*) FROM gate_evidence WHERE deleted_at IS NULL) as total_evidence,
  (SELECT COUNT(*) FROM policies WHERE is_active = true) as active_policies,
  (SELECT COUNT(*) FROM audit_logs) as audit_logs;

-- =========================================================================
-- SECTION 13: E2E TEST SCENARIO DATA SUMMARY - NQH-Bot Platform
-- =========================================================================
--
-- VERSION: 3.0.0 - NQH-Bot Platform (Nov 29, 2025)
-- FRAMEWORK: SDLC 5.1.3.1 Complete Lifecycle
-- PROJECT: NQH-Bot Platform - Vietnamese Enterprise Chatbot
--
-- This seed data supports the following E2E test scenarios using
-- the real NQH-Bot Platform team and project structure:
--
-- =========================================================================
-- TEST ACCOUNTS (12 USERS)
-- =========================================================================
--
-- PLATFORM ADMIN:
--   Email: admin@sdlc-orchestrator.io
--   Password: Admin@123
--   Role: Superuser (platform administration)
--
-- NQH-BOT PLATFORM TEAM (11 USERS):
--
--   EXECUTIVES (3):
--   - CEO: Tai Dang (taidt@mtsolution.com.vn) - Leads both teams
--   - CPO: Dung Luong (dunglt@mtsolution.com.vn) - Product strategy
--   - CTO: Hiep Dinh (dvhiep@nqh.com.vn) - Technical leadership
--
--   LOCAL TEAM (3):
--   - Team Lead: Endior (dangtt1971@gmail.com)
--   - Dev 1: local.dev1@nqh.com.vn
--   - Dev 2: local.dev2@nqh.com.vn
--
--   REMOTE TEAM (3):
--   - Team Lead: Hang Le (ltmhang@nqh.com.vn)
--   - Dev 1: remote.dev1@nqh.com.vn
--   - Dev 2: remote.dev2@nqh.com.vn
--
--   QA TEAM (1):
--   - QA Lead: qa.lead@nqh.com.vn
--
--   INACTIVE (1):
--   - Former contractor: inactive@nqh.com.vn (for auth tests)
--
-- =========================================================================
-- TEST PROJECTS (5 ACTIVE + 1 ARCHIVED)
-- =========================================================================
--
-- 1. NQH-Bot Platform (Main Project)
--    - Stage: BUILD (Stage 03)
--    - Owner: CEO Tai Dang
--    - Description: Vietnamese enterprise AI chatbot with NLP
--    - Gates: G0.1 → G0.2 → G1 → G2 (APPROVED), G3 (PENDING)
--
-- 2. NQH-Bot Analytics Module
--    - Stage: WHAT (Stage 01)
--    - Owner: Remote TL Hang Le
--    - Team: Remote Team
--    - Gates: G0.1 → G0.2 → G1 (APPROVED), G2 (PENDING)
--
-- 3. NQH-Bot NLP Engine
--    - Stage: HOW (Stage 02)
--    - Owner: Local TL Endior
--    - Team: Local Team
--    - Gates: G0.1 → G0.2 (APPROVED), G1 (DRAFT)
--
-- 4. NQH-Bot CRM Integration
--    - Stage: VERIFY (Stage 04)
--    - Owner: CTO Hiep Dinh
--    - Description: CRM system integration
--    - Gates: G0.1 → G0.2 → G1 → G2 → G3 → G4 (APPROVED), G5 (PENDING)
--
-- 5. NQH-Bot Mobile App
--    - Stage: WHY (Stage 00)
--    - Owner: CPO Dung Luong
--    - Status: Early exploration phase
--    - Gates: G0.1 (DRAFT)
--
-- 6. Archived PoC (INACTIVE)
--    - For testing inactive project filtering
--
-- =========================================================================
-- E2E TEST SCENARIOS
-- =========================================================================
--
-- 1. AUTHENTICATION TESTS (TC-AUTH-001 to TC-AUTH-005)
--    - Valid login: admin@sdlc-orchestrator.io / Admin@123
--    - Team login: taidt@mtsolution.com.vn / Admin@123 (CEO)
--    - Invalid login: any email with wrong password
--    - Inactive user: inactive@nqh.com.vn (is_active = false)
--    - Token refresh: use refresh_token from login response
--
-- 2. DASHBOARD TESTS (TC-DASH-001 to TC-DASH-003)
--    - Total Projects: 5 active projects
--    - Active Gates: 19 gates across projects
--    - Pending Approvals: 4 (G3 Main, G2 Analytics, G5 CRM, G0.1 Mobile)
--    - Pass Rate: ~68% (13 approved / 19 total)
--
-- 3. PROJECT TESTS (TC-PROJ-001 to TC-PROJ-003)
--    - NQH-Bot Platform: WHY → WHAT → HOW complete, BUILD in progress
--    - Analytics Module: WHY complete, WHAT in progress (Remote Team)
--    - NLP Engine: WHY complete, HOW in progress (Local Team)
--    - CRM Integration: Complete through BUILD, VERIFY in progress (CTO)
--    - Mobile App: WHY stage started (CPO)
--    - Archived PoC: Inactive (filtered out)
--
-- 4. GATE TESTS (TC-GATE-001 to TC-GATE-005)
--    - APPROVED gates (13):
--      * Main: G0.1, G0.2, G1, G2
--      * Analytics: G0.1, G0.2, G1
--      * NLP Engine: G0.1, G0.2
--      * CRM: G0.1, G0.2, G1, G2, G3, G4
--    - PENDING_APPROVAL gates (4):
--      * Main: G3 (Ship Ready)
--      * Analytics: G2 (Design Ready)
--      * CRM: G5 (Deploy Ready)
--    - DRAFT gates (2):
--      * NLP Engine: G1
--      * Mobile App: G0.1
--
-- 5. EVIDENCE TESTS (TC-EVID-001 to TC-EVID-005)
--    - 13 evidence files across gates
--    - Types: DOCUMENT, DATA, CODE, DIAGRAM, REPORT
--    - NQH-specific files:
--      * Vietnamese market research (G0.1)
--      * NLP pipeline design (G2)
--      * Ollama integration specs (G2)
--    - SHA256 hashes for integrity verification
--
-- 6. POLICY TESTS (TC-POL-001 to TC-POL-004)
--    - 10 active policies across stages
--    - Stages: WHY (3), WHAT (3), HOW (2), VERIFY (2)
--    - Policy evaluations: 9 evaluations for approved gates
--
-- 7. TEAM COLLABORATION TESTS
--    - CEO approves gates across all projects
--    - CPO approves business requirements (G0.x, G1)
--    - CTO approves technical design (G2, G3)
--    - Team Leads upload evidence for their teams
--    - QA Lead uploads test coverage reports
--
-- 8. AUDIT LOG TESTS
--    - 9 audit log entries
--    - Actions: CREATE, APPROVE, UPLOAD, LOGIN
--    - Tracks: Project creation, gate approvals, evidence uploads
--
-- =========================================================================
-- DATA COUNTS SUMMARY
-- =========================================================================
--
-- Users:           12 (1 admin + 11 NQH team)
-- Active Projects:  5 (Main + Analytics + NLP + CRM + Mobile)
-- Inactive Projects: 1 (Archived PoC)
-- Total Gates:     19
--   - APPROVED:    13 (68%)
--   - PENDING:      4 (21%)
--   - DRAFT:        2 (11%)
-- Evidence Files:  13
-- Policies:        10
-- Policy Evals:     9
-- Gate Approvals:  16
-- Audit Logs:       9
--
-- =========================================================================
-- END OF SEED DATA - NQH-Bot Platform v3.0.0
-- =========================================================================
