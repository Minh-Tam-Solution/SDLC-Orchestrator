-- Sprint 74: Planning Hierarchy Tables
-- Execute this SQL against sdlc_orchestrator database
-- Date: 2026-01-18
-- Revision: s74_planning_hierarchy
-- Revises: s74_merge_heads

-- 1. Create roadmaps table
CREATE TABLE IF NOT EXISTS roadmaps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    vision TEXT,
    start_date DATE,
    end_date DATE,
    review_cadence VARCHAR(50) NOT NULL DEFAULT 'quarterly',
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_roadmaps_project_name UNIQUE (project_id, name)
);

CREATE INDEX IF NOT EXISTS idx_roadmaps_project ON roadmaps(project_id);
CREATE INDEX IF NOT EXISTS idx_roadmaps_status ON roadmaps(status);

COMMENT ON TABLE roadmaps IS 'SDLC 5.1.3 Strategic Planning - 12-month roadmaps';

-- 2. Create phases table
CREATE TABLE IF NOT EXISTS phases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    roadmap_id UUID NOT NULL REFERENCES roadmaps(id) ON DELETE CASCADE,
    number INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    theme TEXT,
    objective TEXT,
    start_date DATE,
    end_date DATE,
    status VARCHAR(50) NOT NULL DEFAULT 'planned',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_phases_roadmap_number UNIQUE (roadmap_id, number)
);

CREATE INDEX IF NOT EXISTS idx_phases_roadmap ON phases(roadmap_id);
CREATE INDEX IF NOT EXISTS idx_phases_status ON phases(status);

COMMENT ON TABLE phases IS 'SDLC 5.1.3 Phase Planning - 4-8 week themed objectives';

-- 3. Create sprints table (SDLC 5.1.3 compliant)
CREATE TABLE IF NOT EXISTS sprints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phase_id UUID REFERENCES phases(id) ON DELETE SET NULL,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    number INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    goal TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'planning',
    start_date DATE,
    end_date DATE,
    capacity_points INTEGER,
    team_size INTEGER,
    velocity_target INTEGER,

    -- SDLC 5.1.3 Sprint Governance Gates
    g_sprint_status VARCHAR(50) NOT NULL DEFAULT 'pending',
    g_sprint_approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    g_sprint_approved_at TIMESTAMP,
    g_sprint_close_status VARCHAR(50) NOT NULL DEFAULT 'pending',
    g_sprint_close_approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    g_sprint_close_approved_at TIMESTAMP,
    documentation_deadline TIMESTAMP,

    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_sprints_project_number UNIQUE (project_id, number)
);

CREATE INDEX IF NOT EXISTS idx_sprints_project ON sprints(project_id);
CREATE INDEX IF NOT EXISTS idx_sprints_phase ON sprints(phase_id);
CREATE INDEX IF NOT EXISTS idx_sprints_status ON sprints(status);
CREATE INDEX IF NOT EXISTS idx_sprints_g_sprint_status ON sprints(g_sprint_status);
CREATE INDEX IF NOT EXISTS idx_sprints_g_sprint_close_status ON sprints(g_sprint_close_status);

COMMENT ON TABLE sprints IS 'SDLC 5.1.3 Sprint Planning - 5-10 day delivery cycles with G-Sprint gates';

-- 4. Create sprint_gate_evaluations table
CREATE TABLE IF NOT EXISTS sprint_gate_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sprint_id UUID NOT NULL REFERENCES sprints(id) ON DELETE CASCADE,
    gate_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    checklist JSONB NOT NULL,
    notes TEXT,
    evaluated_by UUID REFERENCES users(id) ON DELETE SET NULL,
    evaluated_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_gate_eval_sprint_type UNIQUE (sprint_id, gate_type)
);

CREATE INDEX IF NOT EXISTS idx_gate_eval_sprint ON sprint_gate_evaluations(sprint_id);
CREATE INDEX IF NOT EXISTS idx_gate_eval_type ON sprint_gate_evaluations(gate_type);
CREATE INDEX IF NOT EXISTS idx_gate_eval_status ON sprint_gate_evaluations(status);

COMMENT ON TABLE sprint_gate_evaluations IS 'SDLC 5.1.3 Sprint Gate Evaluations';
COMMENT ON COLUMN sprint_gate_evaluations.gate_type IS 'Gate type: g_sprint or g_sprint_close';
COMMENT ON COLUMN sprint_gate_evaluations.checklist IS 'SDLC 5.1.3 checklist with pass/fail per item';

-- 5. Create backlog_items table
CREATE TABLE IF NOT EXISTS backlog_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sprint_id UUID REFERENCES sprints(id) ON DELETE SET NULL,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    acceptance_criteria TEXT,
    priority VARCHAR(10) NOT NULL DEFAULT 'P2',
    story_points INTEGER,
    status VARCHAR(50) NOT NULL DEFAULT 'todo',
    assignee_id UUID REFERENCES users(id) ON DELETE SET NULL,
    parent_id UUID REFERENCES backlog_items(id) ON DELETE SET NULL,
    labels JSONB NOT NULL DEFAULT '[]',
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_backlog_sprint ON backlog_items(sprint_id);
CREATE INDEX IF NOT EXISTS idx_backlog_project ON backlog_items(project_id);
CREATE INDEX IF NOT EXISTS idx_backlog_status ON backlog_items(status);
CREATE INDEX IF NOT EXISTS idx_backlog_assignee ON backlog_items(assignee_id);
CREATE INDEX IF NOT EXISTS idx_backlog_priority ON backlog_items(priority);
CREATE INDEX IF NOT EXISTS idx_backlog_type ON backlog_items(type);
CREATE INDEX IF NOT EXISTS idx_backlog_parent ON backlog_items(parent_id);

COMMENT ON TABLE backlog_items IS 'SDLC 5.1.3 Backlog Items - User stories, tasks, bugs';
COMMENT ON COLUMN backlog_items.type IS 'Item type: story, task, bug, spike';
COMMENT ON COLUMN backlog_items.priority IS 'Priority: P0 (critical), P1 (high), P2 (normal)';
COMMENT ON COLUMN backlog_items.status IS 'Status: todo, in_progress, review, done, blocked';

-- Update alembic_version to mark migration as applied
INSERT INTO alembic_version (version_num)
VALUES ('s74_planning_hierarchy')
ON CONFLICT (version_num) DO NOTHING;

-- Verification query
SELECT
    'Tables created: ' || (SELECT COUNT(*) FROM information_schema.tables WHERE table_name IN ('roadmaps', 'phases', 'sprints', 'sprint_gate_evaluations', 'backlog_items')) as result;
