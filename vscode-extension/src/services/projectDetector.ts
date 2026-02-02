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

import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import * as yaml from 'js-yaml';
import { ApiClient } from './apiClient';
import { Logger } from '../utils/logger';

/**
 * Detected project information
 */
export interface DetectedProject {
    name: string;
    uuid: string;
    source: 'sdlc-config' | 'package-json' | 'git-remote' | 'folder-name' | 'manual-config';
}

/**
 * SDLC config file schema (.sdlc/config.yaml or .sdlc-config.json)
 */
interface SDLCConfig {
    version?: string;
    project?: {
        id?: string;  // UUID - if present, skip API resolution
        name?: string;
        description?: string;
    };
    // Legacy format support
    project_uuid?: string;
}

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
export class ProjectDetector {
    private static instance: ProjectDetector | undefined;
    private cachedProject: DetectedProject | null = null;
    private cacheTimestamp: number = 0;
    private readonly CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes

    private constructor(
        private readonly apiClient: ApiClient
    ) {}

    /**
     * Get singleton instance
     */
    static getInstance(apiClient: ApiClient): ProjectDetector {
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
    async getCurrentProject(): Promise<DetectedProject | null> {
        // Check cache (5 min TTL)
        const now = Date.now();
        if (this.cachedProject && (now - this.cacheTimestamp < this.CACHE_TTL_MS)) {
            Logger.debug(`Using cached project: ${this.cachedProject.name}`);
            return this.cachedProject;
        }

        try {
            // Step 1: Detect project info (name + optional UUID from config)
            const detected = this.detectProjectInfo();
            if (!detected) {
                Logger.warn('No project detected from workspace');
                return null;
            }

            const { name, uuid: configUuid, source } = detected;
            Logger.info(`Project detected: ${name} (source: ${source})${configUuid ? ' with UUID from config' : ''}`);

            // Step 2: Use UUID from config OR resolve via API
            let uuid: string;
            if (configUuid) {
                uuid = configUuid;
                Logger.info(`Using UUID from config file: ${uuid}`);
            } else {
                Logger.debug(`No UUID in config, resolving via API...`);
                const resolvedUuid = await this.resolveProjectUUID(name);
                if (!resolvedUuid) {
                    Logger.error(`Failed to resolve project name to UUID: ${name}`);
                    return null;
                }
                uuid = resolvedUuid;
            }

            // Cache result
            this.cachedProject = { name, uuid, source };
            this.cacheTimestamp = now;

            return this.cachedProject;
        } catch (error) {
            Logger.error(`Failed to detect project: ${error}`);
            return null;
        }
    }

    /**
     * Detect project info (name + optional UUID) from workspace
     *
     * @returns Project name, optional UUID, and detection source
     */
    private detectProjectInfo(): { name: string; uuid?: string; source: DetectedProject['source'] } | null {
        const workspace = vscode.workspace.workspaceFolders?.[0];
        if (!workspace) {
            Logger.debug('No workspace folder open');
            return null;
        }

        const workspacePath = workspace.uri.fsPath;

        // Priority 1: .sdlc/config.yaml or .sdlc-config.json (may include UUID)
        const sdlcConfigPath = path.join(workspacePath, '.sdlc', 'config.yaml');
        const sdlcConfigJsonPath = path.join(workspacePath, '.sdlc-config.json');

        if (fs.existsSync(sdlcConfigPath)) {
            try {
                const content = fs.readFileSync(sdlcConfigPath, 'utf8');
                const config = yaml.load(content) as SDLCConfig;
                const name = config.project?.name;
                const uuid = config.project?.id || config.project_uuid;
                if (name) {
                    Logger.debug(`Detected from .sdlc/config.yaml: ${name}${uuid ? ' (UUID: ' + uuid + ')' : ''}`);
                    // Only include uuid if it's a valid string (not undefined)
                    return uuid
                        ? { name, uuid, source: 'sdlc-config' as const }
                        : { name, source: 'sdlc-config' as const };
                }
            } catch (error) {
                Logger.warn(`Failed to parse .sdlc/config.yaml: ${error}`);
            }
        } else if (fs.existsSync(sdlcConfigJsonPath)) {
            try {
                const content = fs.readFileSync(sdlcConfigJsonPath, 'utf8');
                const config = JSON.parse(content) as SDLCConfig;
                const name = config.project?.name;
                const uuid = config.project?.id || config.project_uuid;
                if (name) {
                    Logger.debug(`Detected from .sdlc-config.json: ${name}${uuid ? ' (UUID: ' + uuid + ')' : ''}`);
                    // Only include uuid if it's a valid string (not undefined)
                    return uuid
                        ? { name, uuid, source: 'sdlc-config' as const }
                        : { name, source: 'sdlc-config' as const };
                }
            } catch (error) {
                Logger.warn(`Failed to parse .sdlc-config.json: ${error}`);
            }
        }

        // Priority 2: package.json
        const packageJsonPath = path.join(workspacePath, 'package.json');
        if (fs.existsSync(packageJsonPath)) {
            try {
                const content = fs.readFileSync(packageJsonPath, 'utf8');
                const pkg = JSON.parse(content);
                if (pkg.name) {
                    Logger.debug(`Detected from package.json: ${pkg.name}`);
                    return { name: pkg.name, source: 'package-json' };
                }
            } catch (error) {
                Logger.warn(`Failed to parse package.json: ${error}`);
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
                    Logger.debug(`Detected from .git/config: ${match[1]}`);
                    return { name: match[1], source: 'git-remote' };
                }
            } catch (error) {
                Logger.warn(`Failed to read .git/config: ${error}`);
            }
        }

        // Priority 4: Folder name (fallback)
        const folderName = path.basename(workspacePath);
        Logger.debug(`Detected from folder name: ${folderName}`);
        return { name: folderName, source: 'folder-name' };
    }

    /**
     * Detect project name from workspace (backward compatible wrapper)
     *
     * Priority:
     * 1. .sdlc/config.yaml → project.name
     * 2. package.json → name
     * 3. .git/config → remote repo name
     * 4. Workspace folder name
     *
     * @returns Project name and detection source
     */
    detectProjectName(): { name: string; source: DetectedProject['source'] } | null {
        const info = this.detectProjectInfo();
        if (!info) {
            return null;
        }
        return { name: info.name, source: info.source };
    }

    /**
     * Resolve project to UUID via backend API
     *
     * Matching priority:
     * 1. Match by git repository URL (most reliable)
     * 2. Match by project name (case-insensitive)
     *
     * @param name - Project name to resolve
     * @returns Project UUID or null if not found
     */
    async resolveProjectUUID(name: string): Promise<string | null> {
        try {
            // Get all projects (backend already supports this)
            const projects = await this.apiClient.getProjects();

            // Get local git repo URL for matching
            const localRepoUrl = this.getLocalGitRepoUrl();

            // Priority 1: Match by git repository URL (most reliable)
            if (localRepoUrl) {
                const normalizedLocalUrl = this.normalizeGitUrl(localRepoUrl);
                const projectByRepo = projects.find((p: { repository_url?: string; github_repo?: string }) => {
                    const repoUrl = p.repository_url || p.github_repo;
                    if (!repoUrl) return false;
                    return this.normalizeGitUrl(repoUrl) === normalizedLocalUrl;
                });

                if (projectByRepo) {
                    Logger.info(`Resolved by git repo URL: ${localRepoUrl} → UUID: ${projectByRepo.id}`);
                    return projectByRepo.id;
                }
            }

            // Priority 2: Match by project name (case-insensitive)
            const nameLower = name.toLowerCase();
            const projectByName = projects.find(
                (p: { name: string }) => p.name.toLowerCase() === nameLower
            );

            if (projectByName) {
                Logger.info(`Resolved by name: ${name} → UUID: ${projectByName.id}`);
                return projectByName.id;
            }

            Logger.warn(`Project not found in backend: ${name}`);
            return null;
        } catch (error) {
            Logger.error(`Failed to resolve project UUID: ${error}`);
            return null;
        }
    }

    /**
     * Get local git repository URL from .git/config
     */
    private getLocalGitRepoUrl(): string | null {
        const workspace = vscode.workspace.workspaceFolders?.[0];
        if (!workspace) {
            return null;
        }

        const gitConfigPath = path.join(workspace.uri.fsPath, '.git', 'config');
        if (!fs.existsSync(gitConfigPath)) {
            return null;
        }

        try {
            const content = fs.readFileSync(gitConfigPath, 'utf8');
            // Match: url = https://github.com/user/repo.git or git@github.com:user/repo.git
            const match = content.match(/url\s*=\s*(.+)$/m);
            return match?.[1]?.trim() || null;
        } catch {
            return null;
        }
    }

    /**
     * Normalize git URL for comparison
     * Converts SSH, HTTPS, and various formats to a standard form
     */
    private normalizeGitUrl(url: string): string {
        return url
            .trim()
            .toLowerCase()
            // Remove .git suffix
            .replace(/\.git$/, '')
            // Convert SSH to HTTPS-like format: git@github.com:user/repo → github.com/user/repo
            .replace(/^git@([^:]+):(.+)$/, '$1/$2')
            // Remove protocol
            .replace(/^https?:\/\//, '')
            // Remove www.
            .replace(/^www\./, '')
            // Remove trailing slash
            .replace(/\/$/, '');
    }

    /**
     * Invalidate cache (force re-detection on next call)
     *
     * Call this when:
     * - Workspace folder changes
     * - User manually refreshes
     * - .sdlc/config.yaml is modified
     */
    invalidateCache(): void {
        this.cachedProject = null;
        this.cacheTimestamp = 0;
        Logger.debug('Project cache invalidated');
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
    async shouldShowProjectsPanel(): Promise<boolean> {
        // Check user setting (opt-in)
        const config = vscode.workspace.getConfiguration('sdlc');
        const showPanel = config.get<boolean>('showProjectsPanel', false);
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
        } catch {
            return false;
        }
    }
}
