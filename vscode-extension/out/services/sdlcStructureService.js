"use strict";
/**
 * SDLC Structure Generator Service
 *
 * Generates SDLC 5.1.2 compliant folder structures based on tier selection.
 * Supports offline mode with local-first approach.
 *
 * IMPORTANT: Only folders under /docs are mapped to SDLC stages.
 * Code folders (src, backend, frontend, tests) are NOT mapped to stages.
 *
 * Sprint 53 - SDLC 5.1.2 Compliance
 * @version 1.0.0
 */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.SDLCStructureService = exports.TIER_DESCRIPTIONS = void 0;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const logger_1 = require("../utils/logger");
/**
 * SDLC 5.1.2 Stage Definitions (Contract-First Order)
 *
 * Note: Folder names use SHORT format per SDLC 5.1.2 standard:
 * - docs/00-discover (Stage 00 - WHY)
 * - docs/01-planning (Stage 01 - WHAT)
 *
 * IMPORTANT: Only /docs folders are mapped to stages.
 * Code folders (src, backend, frontend, tests) remain OUTSIDE stage mapping.
 */
const SDLC_STAGES = [
    {
        number: '00',
        name: 'discover',
        displayName: 'Discover (WHY)',
        description: 'Problem Definition - Design Thinking',
        folder: 'docs/00-discover',
        requiredTiers: ['LITE', 'STANDARD', 'PROFESSIONAL', 'ENTERPRISE'],
    },
    {
        number: '01',
        name: 'planning',
        displayName: 'Planning (WHAT)',
        description: 'Requirements Analysis - FRD, User Stories',
        folder: 'docs/01-planning',
        requiredTiers: ['LITE', 'STANDARD', 'PROFESSIONAL', 'ENTERPRISE'],
    },
    {
        number: '02',
        name: 'design',
        displayName: 'Design (HOW)',
        description: 'Architecture Design - System Design, ADRs',
        folder: 'docs/02-design',
        requiredTiers: ['STANDARD', 'PROFESSIONAL', 'ENTERPRISE'],
    },
    {
        number: '03',
        name: 'integrate',
        displayName: 'Integrate',
        description: 'API Design & System Integration (Contract-First)',
        folder: 'docs/03-integrate',
        requiredTiers: ['STANDARD', 'PROFESSIONAL', 'ENTERPRISE'],
    },
    {
        number: '04',
        name: 'build',
        displayName: 'Build',
        description: 'Development & Implementation (docs only)',
        folder: 'docs/04-build',
        requiredTiers: ['LITE', 'STANDARD', 'PROFESSIONAL', 'ENTERPRISE'],
    },
    {
        number: '05',
        name: 'deploy',
        displayName: 'Deploy',
        description: 'Release & Deployment',
        folder: 'docs/05-deploy',
        requiredTiers: ['LITE', 'STANDARD', 'PROFESSIONAL', 'ENTERPRISE'],
    },
    {
        number: '06',
        name: 'validate',
        displayName: 'Validate',
        description: 'Quality Assurance & Testing',
        folder: 'docs/06-validate',
        requiredTiers: ['LITE', 'STANDARD', 'PROFESSIONAL', 'ENTERPRISE'],
    },
    {
        number: '07',
        name: 'operate',
        displayName: 'Operate',
        description: 'Production & Operations',
        folder: 'docs/07-operate',
        requiredTiers: ['STANDARD', 'PROFESSIONAL', 'ENTERPRISE'],
    },
    {
        number: '08',
        name: 'iterate',
        displayName: 'Iterate',
        description: 'Feedback & Continuous Improvement',
        folder: 'docs/08-iterate',
        requiredTiers: ['PROFESSIONAL', 'ENTERPRISE'],
    },
    {
        number: '09',
        name: 'govern',
        displayName: 'Govern',
        description: 'Compliance & Governance',
        folder: 'docs/09-govern',
        requiredTiers: ['ENTERPRISE'],
    },
];
/**
 * Tier descriptions for UI
 */
exports.TIER_DESCRIPTIONS = {
    LITE: {
        label: '$(person) LITE',
        description: 'Minimal governance for small projects',
        teamSize: '1-2 developers',
    },
    STANDARD: {
        label: '$(organization) STANDARD',
        description: 'Balanced governance with API-first design',
        teamSize: '3-10 developers',
    },
    PROFESSIONAL: {
        label: '$(rocket) PROFESSIONAL',
        description: 'Comprehensive governance with collaboration',
        teamSize: '10-50 developers',
    },
    ENTERPRISE: {
        label: '$(shield) ENTERPRISE',
        description: 'Full governance with compliance & audit',
        teamSize: '50+ developers',
    },
};
/**
 * SDLC Structure Generator Service
 */
class SDLCStructureService {
    configFileName = '.sdlc-config.json';
    schemaUrl = 'https://sdlc-orchestrator.io/schemas/config-v1.json';
    /**
     * Check if current workspace has an SDLC config file
     */
    hasSDLCConfig(workspaceRoot) {
        const configPath = path.join(workspaceRoot, this.configFileName);
        return fs.existsSync(configPath);
    }
    /**
     * Check if workspace folder is empty or has minimal files
     */
    isEmptyOrMinimalFolder(workspaceRoot) {
        try {
            const files = fs.readdirSync(workspaceRoot);
            const significantFiles = files.filter((f) => {
                const basename = path.basename(f);
                return (!basename.startsWith('.') &&
                    basename !== 'node_modules' &&
                    basename !== '__pycache__' &&
                    basename !== 'venv' &&
                    basename !== '.venv');
            });
            return significantFiles.length === 0;
        }
        catch {
            return true;
        }
    }
    /**
     * Get stages for a specific tier
     */
    getStagesForTier(tier) {
        return SDLC_STAGES.filter((stage) => stage.requiredTiers.includes(tier));
    }
    /**
     * Generate SDLC config object
     */
    generateConfig(projectName, tier, serverUrl) {
        const stages = this.getStagesForTier(tier);
        const stageMapping = {};
        for (const stage of stages) {
            stageMapping[`${stage.number}-${stage.name}`] = stage.folder;
        }
        const slug = projectName
            .toLowerCase()
            .replace(/[^a-z0-9]+/g, '-')
            .replace(/^-|-$/g, '');
        return {
            $schema: this.schemaUrl,
            version: '1.0.0',
            project: {
                id: `local-${Date.now()}`,
                name: projectName,
                slug: slug,
            },
            sdlc: {
                frameworkVersion: '5.1.2',
                tier: tier,
                stages: stageMapping,
            },
            server: {
                url: serverUrl || 'https://sdlc.mtsolution.com.vn',
                connected: false,
            },
            gates: {
                current: 'G0.1',
                passed: [],
            },
        };
    }
    /**
     * Generate folder structure for a tier
     */
    generateStructure(workspaceRoot, projectName, tier, options = {}) {
        const createdFolders = [];
        const createdFiles = [];
        try {
            const stages = this.getStagesForTier(tier);
            // Create folders
            for (const stage of stages) {
                const folderPath = path.join(workspaceRoot, stage.folder);
                if (!fs.existsSync(folderPath)) {
                    fs.mkdirSync(folderPath, { recursive: true });
                    createdFolders.push(stage.folder);
                    logger_1.Logger.info(`Created folder: ${stage.folder}`);
                }
            }
            // Create .sdlc-config.json
            const config = this.generateConfig(projectName, tier, options.serverUrl);
            const configPath = path.join(workspaceRoot, this.configFileName);
            fs.writeFileSync(configPath, JSON.stringify(config, null, 2), 'utf-8');
            createdFiles.push(this.configFileName);
            logger_1.Logger.info('Created .sdlc-config.json');
            // Create template files if requested
            if (options.createTemplates) {
                const templates = this.generateTemplateFiles(projectName, tier);
                for (const template of templates) {
                    const templatePath = path.join(workspaceRoot, template.path);
                    const templateDir = path.dirname(templatePath);
                    if (!fs.existsSync(templateDir)) {
                        fs.mkdirSync(templateDir, { recursive: true });
                    }
                    if (!fs.existsSync(templatePath)) {
                        fs.writeFileSync(templatePath, template.content, 'utf-8');
                        createdFiles.push(template.path);
                        logger_1.Logger.info(`Created template: ${template.path}`);
                    }
                }
            }
            // Create .vscode/settings.json with recommended settings
            const vscodeDir = path.join(workspaceRoot, '.vscode');
            if (!fs.existsSync(vscodeDir)) {
                fs.mkdirSync(vscodeDir, { recursive: true });
            }
            const settingsPath = path.join(vscodeDir, 'settings.json');
            if (!fs.existsSync(settingsPath)) {
                const vscodeSettings = this.generateVSCodeSettings();
                fs.writeFileSync(settingsPath, JSON.stringify(vscodeSettings, null, 2), 'utf-8');
                createdFiles.push('.vscode/settings.json');
            }
            return { success: true, createdFolders, createdFiles };
        }
        catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            logger_1.Logger.error(`Failed to generate structure: ${errorMessage}`);
            return { success: false, createdFolders, createdFiles };
        }
    }
    /**
     * Generate template files based on tier
     */
    generateTemplateFiles(projectName, tier) {
        const templates = [];
        const date = new Date().toISOString().split('T')[0];
        // Foundation templates (all tiers)
        templates.push({
            path: 'docs/00-foundation/problem-statement.md',
            content: `# Problem Statement

## Project: ${projectName}

**Created**: ${date}
**SDLC Framework**: 5.1.2
**Tier**: ${tier}

---

## 1. Problem Definition

### What problem are we solving?

<!-- Describe the core problem in 2-3 sentences -->

### Who has this problem?

<!-- Target users/customers affected by this problem -->

### Why is this problem worth solving?

<!-- Business impact, market opportunity, or user pain points -->

---

## 2. Current State (As-Is)

<!-- Describe how things work today without your solution -->

---

## 3. Desired State (To-Be)

<!-- Describe the ideal state after your solution is implemented -->

---

## 4. Success Metrics

| Metric | Current | Target | Measurement Method |
|--------|---------|--------|-------------------|
| <!-- e.g., Time to complete task --> | <!-- 10 min --> | <!-- 2 min --> | <!-- Timer logs --> |

---

## 5. Constraints & Assumptions

### Constraints
- <!-- Technical, budget, timeline, or resource constraints -->

### Assumptions
- <!-- Assumptions that need to be validated -->

---

**Gate**: G0.1 (Problem Definition)
**Status**: Draft
`,
        });
        // Planning templates (all tiers)
        templates.push({
            path: 'docs/01-planning/requirements.md',
            content: `# Requirements Document

## Project: ${projectName}

**Created**: ${date}
**SDLC Framework**: 5.1.2
**Tier**: ${tier}

---

## 1. Functional Requirements

### FR-001: <!-- Requirement Name -->

- **Priority**: High / Medium / Low
- **Description**: <!-- What the system should do -->
- **Acceptance Criteria**:
  - [ ] <!-- Criterion 1 -->
  - [ ] <!-- Criterion 2 -->

---

## 2. Non-Functional Requirements

### NFR-001: Performance

- **Response Time**: < 200ms (p95)
- **Throughput**: 1000 req/sec
- **Availability**: 99.9%

### NFR-002: Security

- **Authentication**: JWT + OAuth 2.0
- **Authorization**: RBAC
- **Data Protection**: AES-256 at rest, TLS 1.3 in transit

---

## 3. User Stories

### US-001: <!-- Story Title -->

**As a** <!-- user role -->
**I want to** <!-- action -->
**So that** <!-- benefit -->

**Acceptance Criteria**:
- [ ] <!-- Criterion 1 -->
- [ ] <!-- Criterion 2 -->

---

**Gate**: G1 (Requirements Ready)
**Status**: Draft
`,
        });
        // Design templates (STANDARD+)
        if (['STANDARD', 'PROFESSIONAL', 'ENTERPRISE'].includes(tier)) {
            templates.push({
                path: 'docs/02-design/architecture-overview.md',
                content: `# Architecture Overview

## Project: ${projectName}

**Created**: ${date}
**SDLC Framework**: 5.1.2
**Tier**: ${tier}

---

## 1. System Context

\`\`\`
┌─────────────────────────────────────────────────────────────┐
│                      External Systems                        │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ Client  │  │ API     │  │ Database│  │ Cache   │        │
│  │ Apps    │  │ Gateway │  │ (PG)    │  │ (Redis) │        │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘        │
└─────────────────────────────────────────────────────────────┘
\`\`\`

---

## 2. High-Level Architecture

### Layers

1. **Presentation Layer**: <!-- UI/API -->
2. **Business Logic Layer**: <!-- Services -->
3. **Data Access Layer**: <!-- Repositories -->
4. **Infrastructure Layer**: <!-- External services -->

---

## 3. Key Design Decisions

### ADR-001: <!-- Decision Title -->

- **Status**: Proposed / Accepted / Deprecated
- **Context**: <!-- Why this decision is needed -->
- **Decision**: <!-- What was decided -->
- **Consequences**: <!-- Impact of this decision -->

---

## 4. Technology Stack

| Layer | Technology | Version | Rationale |
|-------|------------|---------|-----------|
| Frontend | <!-- React --> | <!-- 18.x --> | <!-- Modern UI framework --> |
| Backend | <!-- FastAPI --> | <!-- 0.104+ --> | <!-- Async Python --> |
| Database | <!-- PostgreSQL --> | <!-- 15.x --> | <!-- ACID compliance --> |

---

**Gate**: G2 (Design Ready)
**Status**: Draft
`,
            });
            // Integration templates (STANDARD+)
            templates.push({
                path: 'docs/03-integration/api-contracts.md',
                content: `# API Contracts

## Project: ${projectName}

**Created**: ${date}
**SDLC Framework**: 5.1.2
**Tier**: ${tier}

---

## 1. API Overview

**Base URL**: \`/api/v1\`
**Authentication**: Bearer Token (JWT)
**Content-Type**: application/json

---

## 2. Endpoints

### 2.1 Resource: <!-- Resource Name -->

#### GET /api/v1/<!-- resource -->

**Description**: <!-- What this endpoint does -->

**Request**:
\`\`\`http
GET /api/v1/<!-- resource -->?page=1&limit=20
Authorization: Bearer <token>
\`\`\`

**Response** (200 OK):
\`\`\`json
{
  "data": [],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 0
  }
}
\`\`\`

**Error Responses**:
- 401 Unauthorized
- 403 Forbidden
- 500 Internal Server Error

---

## 3. Data Models

### Model: <!-- ModelName -->

\`\`\`typescript
interface <!-- ModelName --> {
  id: string;
  created_at: string;
  updated_at: string;
  // Add fields
}
\`\`\`

---

**Gate**: G2 (Design Ready)
**Status**: Draft
`,
            });
        }
        // README.md (all tiers)
        templates.push({
            path: 'README.md',
            content: `# ${projectName}

[![SDLC 5.1.2](https://img.shields.io/badge/SDLC-5.1.2-blue)](https://sdlc-orchestrator.dev)
[![Tier: ${tier}](https://img.shields.io/badge/Tier-${tier}-green)](https://sdlc-orchestrator.dev/tiers)

## Overview

<!-- Brief project description -->

## SDLC Configuration

This project follows **SDLC 5.1.2** framework with **${tier}** tier governance.

### Project Structure

\`\`\`
${projectName}/
├── .sdlc-config.json      # SDLC configuration
├── docs/
│   ├── 00-foundation/     # WHY - Problem Definition
│   ├── 01-planning/       # WHAT - Requirements
${['STANDARD', 'PROFESSIONAL', 'ENTERPRISE'].includes(tier) ? `│   ├── 02-design/        # HOW - Architecture
│   ├── 03-integration/    # API Design (Contract-First)` : ''}
${['PROFESSIONAL', 'ENTERPRISE'].includes(tier) ? '│   ├── 08-collaborate/   # Team Collaboration' : ''}
${tier === 'ENTERPRISE' ? '│   └── 09-govern/        # Compliance & Governance' : '│   └── ...'}
├── src/                   # Source code (Stage 04)
├── tests/                 # Tests (Stage 05)
└── infrastructure/        # Deployment (Stage 06)
\`\`\`

## Getting Started

1. Install VS Code Extension: \`SDLC Orchestrator\`
2. Run: \`Cmd+Shift+P\` → \`SDLC: View Gate Status\`
3. Start with Gate G0.1 (Problem Definition)

## Gates Progress

- [ ] G0.1 - Problem Definition
- [ ] G0.2 - Solution Diversity
- [ ] G1 - Requirements Ready
- [ ] G2 - Design Ready
- [ ] G3 - Ship Ready
- [ ] G4 - Launch Ready
- [ ] G5 - Scale Ready

## Documentation

- [Problem Statement](docs/00-foundation/problem-statement.md)
- [Requirements](docs/01-planning/requirements.md)
${['STANDARD', 'PROFESSIONAL', 'ENTERPRISE'].includes(tier) ? `- [Architecture](docs/02-design/architecture-overview.md)
- [API Contracts](docs/03-integration/api-contracts.md)` : ''}

---

Generated by SDLC Orchestrator VS Code Extension
`,
        });
        return templates;
    }
    /**
     * Generate recommended VS Code settings
     */
    generateVSCodeSettings() {
        return {
            'sdlc.apiUrl': 'https://sdlc.mtsolution.com.vn',
            'sdlc.enableNotifications': true,
            'sdlc.aiCouncilEnabled': true,
            'editor.formatOnSave': true,
            'files.exclude': {
                '**/__pycache__': true,
                '**/.pytest_cache': true,
                '**/node_modules': true,
            },
        };
    }
    /**
     * Perform gap analysis on existing folder structure
     */
    analyzeExistingStructure(workspaceRoot, targetTier) {
        const stages = this.getStagesForTier(targetTier);
        const existingFolders = [];
        const missingFolders = [];
        const suggestedMappings = {};
        const recommendations = [];
        // SDLC 5.1.2: Only /docs folders are mapped to stages
        // Code folders (src, backend, frontend, tests) are NOT stage-mapped
        const folderPatterns = {
            '00-discover': ['docs/00-discover', 'docs/00-foundation', 'docs/00-Project-Foundation', 'docs/foundation', 'docs/why', 'docs/vision'],
            '01-planning': ['docs/01-planning', 'docs/01-Planning-Analysis', 'docs/planning', 'docs/requirements'],
            '02-design': ['docs/02-design', 'docs/02-Design-Architecture', 'docs/design', 'docs/architecture'],
            '03-integrate': ['docs/03-integrate', 'docs/03-integration', 'docs/03-Integration-API', 'docs/api'],
            '04-build': ['docs/04-build', 'docs/03-Development-Implementation', 'docs/development'],
            '05-deploy': ['docs/05-deploy', 'docs/05-Deployment-Release', 'docs/deployment', 'docs/release'],
            '06-validate': ['docs/06-validate', 'docs/04-Testing-Quality', 'docs/testing', 'docs/qa'],
            '07-operate': ['docs/07-operate', 'docs/06-Operations-Monitoring', 'docs/operations', 'docs/runbooks'],
            '08-iterate': ['docs/08-iterate', 'docs/08-Training-Knowledge', 'docs/feedback', 'docs/collaboration'],
            '09-govern': ['docs/09-govern', 'docs/09-Executive-Reports', 'docs/compliance', 'docs/governance'],
        };
        // Check existing folders
        for (const stage of stages) {
            const expectedFolder = stage.folder;
            const stageKey = `${stage.number}-${stage.name}`;
            if (fs.existsSync(path.join(workspaceRoot, expectedFolder))) {
                existingFolders.push(expectedFolder);
            }
            else {
                // Look for alternative folders
                const patterns = folderPatterns[stageKey] || [];
                let found = false;
                for (const pattern of patterns) {
                    if (fs.existsSync(path.join(workspaceRoot, pattern))) {
                        suggestedMappings[pattern] = expectedFolder;
                        recommendations.push(`Consider renaming '${pattern}' to '${expectedFolder}' for SDLC 5.1.2 compliance`);
                        found = true;
                        break;
                    }
                }
                if (!found) {
                    missingFolders.push(expectedFolder);
                }
            }
        }
        // Check for legacy SDLC 4.9.x folders
        const legacyFolders = [
            '07-Integration-APIs',
            '08-Operations-Monitoring',
            '09-Collaboration-Communication',
            '10-Governance-Compliance',
        ];
        for (const legacy of legacyFolders) {
            const legacyPath = path.join(workspaceRoot, 'docs', legacy);
            if (fs.existsSync(legacyPath)) {
                recommendations.push(`Found legacy SDLC 4.9.x folder 'docs/${legacy}'. Run 'sdlcctl migrate' to upgrade to 5.1.2`);
            }
        }
        return {
            existingFolders,
            missingFolders,
            suggestedMappings,
            recommendations,
        };
    }
    /**
     * Read existing SDLC config
     */
    readConfig(workspaceRoot) {
        const configPath = path.join(workspaceRoot, this.configFileName);
        try {
            if (fs.existsSync(configPath)) {
                const content = fs.readFileSync(configPath, 'utf-8');
                return JSON.parse(content);
            }
        }
        catch (error) {
            const errorMsg = error instanceof Error ? error.message : String(error);
            logger_1.Logger.error(`Failed to read SDLC config: ${errorMsg}`);
        }
        return null;
    }
    /**
     * Update existing SDLC config
     */
    updateConfig(workspaceRoot, updates) {
        const configPath = path.join(workspaceRoot, this.configFileName);
        try {
            const existing = this.readConfig(workspaceRoot);
            if (existing) {
                const updated = { ...existing, ...updates };
                fs.writeFileSync(configPath, JSON.stringify(updated, null, 2), 'utf-8');
                return true;
            }
        }
        catch (error) {
            const errorMsg = error instanceof Error ? error.message : String(error);
            logger_1.Logger.error(`Failed to update SDLC config: ${errorMsg}`);
        }
        return false;
    }
}
exports.SDLCStructureService = SDLCStructureService;
//# sourceMappingURL=sdlcStructureService.js.map