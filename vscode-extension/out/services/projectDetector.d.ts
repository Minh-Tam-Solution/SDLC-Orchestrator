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
import { ApiClient } from './apiClient';
/**
 * Detected project information
 */
export interface DetectedProject {
    name: string;
    uuid: string;
    source: 'sdlc-config' | 'package-json' | 'git-remote' | 'folder-name' | 'manual-config';
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
export declare class ProjectDetector {
    private readonly apiClient;
    private static instance;
    private cachedProject;
    private cacheTimestamp;
    private readonly CACHE_TTL_MS;
    private constructor();
    /**
     * Get singleton instance
     */
    static getInstance(apiClient: ApiClient): ProjectDetector;
    /**
     * Get current project (auto-detected or from cache)
     *
     * @returns Detected project with name and UUID, or null if detection fails
     */
    getCurrentProject(): Promise<DetectedProject | null>;
    /**
     * Detect project info (name + optional UUID) from workspace
     *
     * @returns Project name, optional UUID, and detection source
     */
    private detectProjectInfo;
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
    detectProjectName(): {
        name: string;
        source: DetectedProject['source'];
    } | null;
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
    resolveProjectUUID(name: string): Promise<string | null>;
    /**
     * Get local git repository URL from .git/config
     */
    private getLocalGitRepoUrl;
    /**
     * Normalize git URL for comparison
     * Converts SSH, HTTPS, and various formats to a standard form
     */
    private normalizeGitUrl;
    /**
     * Invalidate cache (force re-detection on next call)
     *
     * Call this when:
     * - Workspace folder changes
     * - User manually refreshes
     * - .sdlc/config.yaml is modified
     */
    invalidateCache(): void;
    /**
     * Check if PROJECTS panel should be shown
     *
     * Show panel only if:
     * - Multiple .sdlc/config.yaml files exist (monorepo)
     * - OR sdlc.showProjectsPanel setting is true (user opt-in)
     *
     * @returns Promise that resolves to true if panel should be visible
     */
    shouldShowProjectsPanel(): Promise<boolean>;
}
//# sourceMappingURL=projectDetector.d.ts.map