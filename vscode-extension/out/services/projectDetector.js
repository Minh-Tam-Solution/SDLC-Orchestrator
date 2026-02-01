"use strict";
/**
 * Project Detector Service
 *
 * Auto-detects project from workspace and resolves to UUID.
 * Eliminates need for manual project selection and UUID configuration.
 *
 * Sprint 127 - Multi-Frontend Alignment - Auto-Detect Project
 * SPEC-0015: Extension Auto-Detect Project
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
exports.ProjectDetector = void 0;
const vscode = __importStar(require("vscode"));
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const yaml = __importStar(require("js-yaml"));
const logger_1 = require("../utils/logger");
/**
 * Project Detector Service
 *
 * Automatically detects project from workspace using 4-level priority:
 * 1. .sdlc/config.yaml (highest priority - official SDLC config)
 * 2. package.json (npm project name)
 * 3. .git/config (git remote repo name)
 * 4. Workspace folder name (fallback)
 *
 * Then resolves project name to UUID via backend API.
 */
class ProjectDetector {
    apiClient;
    static instance;
    cachedProject = null;
    cacheTimestamp = 0;
    CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes
    constructor(apiClient) {
        this.apiClient = apiClient;
    }
    /**
     * Get singleton instance
     */
    static getInstance(apiClient) {
        if (!ProjectDetector.instance) {
            ProjectDetector.instance = new ProjectDetector(apiClient);
        }
        return ProjectDetector.instance;
    }
    /**
     * Get current project (auto-detected or from cache)
     *
     * @returns Detected project with name and UUID, or null if detection fails
     */
    async getCurrentProject() {
        // Check cache (5 min TTL)
        const now = Date.now();
        if (this.cachedProject && (now - this.cacheTimestamp < this.CACHE_TTL_MS)) {
            logger_1.Logger.debug(`Using cached project: ${this.cachedProject.name}`);
            return this.cachedProject;
        }
        try {
            // Step 1: Detect project name
            const detected = this.detectProjectName();
            if (!detected) {
                logger_1.Logger.warn('No project detected from workspace');
                return null;
            }
            const { name, source } = detected;
            logger_1.Logger.info(`Project detected: ${name} (source: ${source})`);
            // Step 2: Resolve name to UUID
            const uuid = await this.resolveProjectUUID(name);
            if (!uuid) {
                logger_1.Logger.error(`Failed to resolve project name to UUID: ${name}`);
                return null;
            }
            // Cache result
            this.cachedProject = { name, uuid, source };
            this.cacheTimestamp = now;
            return this.cachedProject;
        }
        catch (error) {
            logger_1.Logger.error(`Failed to detect project: ${error}`);
            return null;
        }
    }
    /**
     * Detect project name from workspace
     *
     * Priority:
     * 1. .sdlc/config.yaml → project.name
     * 2. package.json → name
     * 3. .git/config → remote repo name
     * 4. Workspace folder name
     *
     * @returns Project name and detection source
     */
    detectProjectName() {
        const workspace = vscode.workspace.workspaceFolders?.[0];
        if (!workspace) {
            logger_1.Logger.debug('No workspace folder open');
            return null;
        }
        const workspacePath = workspace.uri.fsPath;
        // Priority 1: .sdlc/config.yaml or .sdlc-config.json
        const sdlcConfigPath = path.join(workspacePath, '.sdlc', 'config.yaml');
        const sdlcConfigJsonPath = path.join(workspacePath, '.sdlc-config.json');
        if (fs.existsSync(sdlcConfigPath)) {
            try {
                const content = fs.readFileSync(sdlcConfigPath, 'utf8');
                const config = yaml.load(content);
                if (config.project?.name) {
                    logger_1.Logger.debug(`Detected from .sdlc/config.yaml: ${config.project.name}`);
                    return { name: config.project.name, source: 'sdlc-config' };
                }
            }
            catch (error) {
                logger_1.Logger.warn(`Failed to parse .sdlc/config.yaml: ${error}`);
            }
        }
        else if (fs.existsSync(sdlcConfigJsonPath)) {
            try {
                const content = fs.readFileSync(sdlcConfigJsonPath, 'utf8');
                const config = JSON.parse(content);
                if (config.project?.name) {
                    logger_1.Logger.debug(`Detected from .sdlc-config.json: ${config.project.name}`);
                    return { name: config.project.name, source: 'sdlc-config' };
                }
            }
            catch (error) {
                logger_1.Logger.warn(`Failed to parse .sdlc-config.json: ${error}`);
            }
        }
        // Priority 2: package.json
        const packageJsonPath = path.join(workspacePath, 'package.json');
        if (fs.existsSync(packageJsonPath)) {
            try {
                const content = fs.readFileSync(packageJsonPath, 'utf8');
                const pkg = JSON.parse(content);
                if (pkg.name) {
                    logger_1.Logger.debug(`Detected from package.json: ${pkg.name}`);
                    return { name: pkg.name, source: 'package-json' };
                }
            }
            catch (error) {
                logger_1.Logger.warn(`Failed to parse package.json: ${error}`);
            }
        }
        // Priority 3: .git/config (remote repo name)
        const gitConfigPath = path.join(workspacePath, '.git', 'config');
        if (fs.existsSync(gitConfigPath)) {
            try {
                const content = fs.readFileSync(gitConfigPath, 'utf8');
                // Match: url = https://github.com/user/repo.git
                const match = content.match(/url\s*=\s*.*\/([^\/]+?)(?:\.git)?$/m);
                if (match?.[1]) {
                    logger_1.Logger.debug(`Detected from .git/config: ${match[1]}`);
                    return { name: match[1], source: 'git-remote' };
                }
            }
            catch (error) {
                logger_1.Logger.warn(`Failed to read .git/config: ${error}`);
            }
        }
        // Priority 4: Folder name (fallback)
        const folderName = path.basename(workspacePath);
        logger_1.Logger.debug(`Detected from folder name: ${folderName}`);
        return { name: folderName, source: 'folder-name' };
    }
    /**
     * Resolve project name to UUID via backend API
     *
     * Calls: GET /api/v1/projects?name={name}
     * Or: GET /api/v1/projects (filter client-side)
     *
     * @param name - Project name to resolve
     * @returns Project UUID or null if not found
     */
    async resolveProjectUUID(name) {
        try {
            // Get all projects (backend already supports this)
            const projects = await this.apiClient.getProjects();
            // Find project by name (case-insensitive)
            const nameLower = name.toLowerCase();
            const project = projects.find((p) => p.name.toLowerCase() === nameLower);
            if (!project) {
                logger_1.Logger.warn(`Project not found in backend: ${name}`);
                return null;
            }
            logger_1.Logger.info(`Resolved ${name} to UUID: ${project.id}`);
            return project.id;
        }
        catch (error) {
            logger_1.Logger.error(`Failed to resolve project UUID: ${error}`);
            return null;
        }
    }
    /**
     * Invalidate cache (force re-detection on next call)
     *
     * Call this when:
     * - Workspace folder changes
     * - User manually refreshes
     * - .sdlc/config.yaml is modified
     */
    invalidateCache() {
        this.cachedProject = null;
        this.cacheTimestamp = 0;
        logger_1.Logger.debug('Project cache invalidated');
    }
    /**
     * Check if PROJECTS panel should be shown
     *
     * Show panel only if:
     * - Multiple .sdlc/config.yaml files exist (monorepo)
     * - OR sdlc.showProjectsPanel setting is true (user opt-in)
     *
     * @returns Promise that resolves to true if panel should be visible
     */
    async shouldShowProjectsPanel() {
        // Check user setting (opt-in)
        const config = vscode.workspace.getConfiguration('sdlc');
        const showPanel = config.get('showProjectsPanel', false);
        if (showPanel) {
            return true;
        }
        // Check for monorepo (multiple .sdlc/config.yaml)
        const workspace = vscode.workspace.workspaceFolders?.[0];
        if (!workspace) {
            return false;
        }
        // Find all .sdlc/config.yaml files (limit search to 2 levels deep)
        const pattern = new vscode.RelativePattern(workspace, '**/.sdlc/config.yaml');
        try {
            const files = await vscode.workspace.findFiles(pattern, null, 2);
            return files.length > 1; // Show for monorepo
        }
        catch {
            return false;
        }
    }
}
exports.ProjectDetector = ProjectDetector;
//# sourceMappingURL=projectDetector.js.map