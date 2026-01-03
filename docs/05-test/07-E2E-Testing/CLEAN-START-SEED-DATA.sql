-- =========================================================================
-- CLEAN START SEED DATA - SDLC Orchestrator
-- =========================================================================
-- Version: 1.0.2
-- Date: December 29, 2025
-- Purpose: Minimal seed data with only platform admin account
--
-- Usage (after running migrations):
-- cat CLEAN-START-SEED-DATA.sql | docker exec -i postgres-central psql -U sdlc_user -d sdlc_orchestrator
--
-- OR use the reset script:
-- ./scripts/reset-database.sh
-- =========================================================================

-- Insert system roles (9 core roles)
INSERT INTO roles (id, name, display_name, description, is_active, created_at)
VALUES
  ('10000000-0000-0000-0000-000000000001', 'CEO', 'Chief Executive Officer', 'Executive leadership with full access', true, NOW()),
  ('10000000-0000-0000-0000-000000000002', 'CTO', 'Chief Technology Officer', 'Technical leadership', true, NOW()),
  ('10000000-0000-0000-0000-000000000003', 'CPO', 'Chief Product Officer', 'Product leadership', true, NOW()),
  ('10000000-0000-0000-0000-000000000006', 'ENGINEERING_MANAGER', 'Engineering Manager', 'Engineering team management', true, NOW()),
  ('10000000-0000-0000-0000-000000000007', 'TECH_LEAD', 'Tech Lead', 'Technical team leadership', true, NOW()),
  ('10000000-0000-0000-0000-000000000008', 'DEVELOPER', 'Developer', 'Software development', true, NOW()),
  ('10000000-0000-0000-0000-000000000009', 'QA_ENGINEER', 'QA Engineer', 'Quality assurance', true, NOW()),
  ('10000000-0000-0000-0000-000000000012', 'PROJECT_MANAGER', 'Project Manager', 'Project management', true, NOW()),
  ('10000000-0000-0000-0000-000000000013', 'BUSINESS_ANALYST', 'Business Analyst', 'Requirements analysis', true, NOW())
ON CONFLICT (id) DO NOTHING;

-- Insert Platform Admin (password: Admin@123)
-- Hash generated with: python3 -c "import bcrypt; print(bcrypt.hashpw('Admin@123'.encode(), bcrypt.gensalt(12)).decode())"
INSERT INTO users (id, email, name, password_hash, is_active, is_superuser, mfa_enabled, created_at, updated_at)
VALUES (
  'a0000000-0000-0000-0000-000000000001',
  'taidt@mtsolution.com.vn',
  'Platform Admin',
  '$2b$12$gbdaanPRphcu5qGFfd1AxuPE9tEuPDjazMcnz8oSfqDKE/T1961tm',
  true, true, false, NOW(), NOW()
)
ON CONFLICT (id) DO NOTHING;

-- Insert AI Providers
INSERT INTO ai_providers (id, provider_name, provider_type, api_key_encrypted, model_name, is_active, priority, cost_per_1k_input_tokens, cost_per_1k_output_tokens, max_tokens, temperature, created_at, updated_at)
VALUES
  ('00000000-0000-0000-0000-000000000001', 'Ollama Local', 'ollama', 'encrypted_key_placeholder', 'qwen3:32b', true, 1, 0.0001, 0.0001, 32000, 0.70, NOW(), NOW()),
  ('00000000-0000-0000-0000-000000000002', 'Anthropic Claude', 'anthropic', 'encrypted_key_placeholder', 'claude-sonnet-4-5-20250929', true, 2, 0.003, 0.015, 200000, 0.70, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- Verify
SELECT 'Clean Start Data Summary:' as info;
SELECT
  (SELECT COUNT(*) FROM users) as users,
  (SELECT COUNT(*) FROM roles) as roles,
  (SELECT COUNT(*) FROM projects) as projects,
  (SELECT COUNT(*) FROM ai_providers) as ai_providers;

-- =========================================================================
-- Test Scenario Instructions
-- =========================================================================
-- 1. Platform Admin Login:
--    - URL: https://sdlc.nhatquangholding.com/login
--    - Email: taidt@mtsolution.com.vn
--    - Password: Admin@123
--
-- 2. First Owner Onboarding:
--    - Email: dangtt1971@gmail.com
--    - Method: GitHub OAuth or Email Registration
--    - Project: Endior Translator
--    - Path: /Users/dttai/Documents/Python/Endior Translator/
--
-- 3. Expected Flow:
--    a. Owner registers/logs in via OAuth or email
--    b. Owner creates first project "Endior Translator"
--    c. Owner invites team members as needed
--    d. Team starts uploading evidence and creating gates
-- =========================================================================
