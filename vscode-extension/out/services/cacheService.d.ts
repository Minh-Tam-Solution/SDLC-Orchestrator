/**
 * SDLC Orchestrator Cache Service
 *
 * Provides offline caching for API responses using VS Code's globalState.
 * Implements TTL-based cache invalidation and stale-while-revalidate pattern.
 *
 * Sprint 27 Day 2 - Cache Service
 * @version 0.1.0
 */
import * as vscode from 'vscode';
/**
 * Cache configuration
 */
interface CacheConfig {
    /** Default TTL in milliseconds (5 minutes) */
    defaultTtl: number;
    /** Maximum cache size (number of entries) */
    maxSize: number;
    /** Enable stale-while-revalidate pattern */
    staleWhileRevalidate: boolean;
    /** Grace period for stale data in milliseconds (1 minute) */
    staleGracePeriod: number;
}
/**
 * Cache key prefixes for different data types
 */
export declare const CacheKeys: {
    readonly PROJECTS: "cache.projects";
    readonly GATES: (projectId: string) => string;
    readonly VIOLATIONS: (projectId: string) => string;
    readonly PROJECT: (projectId: string) => string;
    readonly GATE: (gateId: string) => string;
    readonly VIOLATION: (violationId: string) => string;
    readonly USER: "cache.user";
    readonly COUNCIL_HISTORY: (projectId: string) => string;
};
/**
 * TTL values for different cache types (in milliseconds)
 */
export declare const CacheTTL: {
    /** Projects list - cache for 10 minutes */
    readonly PROJECTS: number;
    /** Gates - cache for 2 minutes (frequently updated) */
    readonly GATES: number;
    /** Violations - cache for 2 minutes */
    readonly VIOLATIONS: number;
    /** Individual project/gate/violation - cache for 5 minutes */
    readonly SINGLE_ITEM: number;
    /** User profile - cache for 30 minutes */
    readonly USER: number;
    /** Council history - cache for 15 minutes */
    readonly COUNCIL_HISTORY: number;
};
/**
 * Cache result type
 */
export interface CacheResult<T> {
    data: T;
    isStale: boolean;
    isCached: boolean;
    age: number;
}
/**
 * Cache Service for offline support
 */
export declare class CacheService {
    private context;
    private config;
    private memoryCache;
    constructor(context: vscode.ExtensionContext, config?: Partial<CacheConfig>);
    /**
     * Gets data from cache
     *
     * @param key - Cache key
     * @returns Cached data or undefined if not found/expired
     */
    get<T>(key: string): CacheResult<T> | undefined;
    /**
     * Sets data in cache
     *
     * @param key - Cache key
     * @param data - Data to cache
     * @param ttl - Time to live in milliseconds (optional)
     * @param etag - ETag for conditional requests (optional)
     */
    set<T>(key: string, data: T, ttl?: number, etag?: string): Promise<void>;
    /**
     * Deletes data from cache
     *
     * @param key - Cache key
     */
    delete(key: string): Promise<void>;
    /**
     * Clears all cached data
     */
    clear(): Promise<void>;
    /**
     * Clears cache for a specific project
     *
     * @param projectId - Project ID
     */
    clearProject(projectId: string): Promise<void>;
    /**
     * Invalidates cache entries matching a pattern
     *
     * @param pattern - Key pattern to match
     */
    invalidatePattern(pattern: string): Promise<void>;
    /**
     * Gets cache statistics
     */
    getStats(): {
        memoryEntries: number;
        persistedEntries: number;
        oldestEntry: number | null;
        newestEntry: number | null;
    };
    /**
     * Checks if data is cached and fresh
     *
     * @param key - Cache key
     */
    isFresh(key: string): boolean;
    /**
     * Gets cached data or fetches fresh data
     *
     * @param key - Cache key
     * @param fetcher - Function to fetch fresh data
     * @param ttl - TTL for cache entry
     */
    getOrFetch<T>(key: string, fetcher: () => Promise<T>, ttl?: number): Promise<CacheResult<T>>;
    /**
     * Revalidates cache entry in background
     */
    private revalidateInBackground;
    /**
     * Enforces maximum cache size by removing oldest entries
     */
    private enforceMaxSize;
    /**
     * Loads persisted cache into memory cache
     */
    private loadPersistedCache;
    /**
     * Preloads cache for a project (call after project selection)
     */
    preloadProject(projectId: string, fetchers: {
        gates?: () => Promise<unknown>;
        violations?: () => Promise<unknown>;
    }): Promise<void>;
}
export {};
//# sourceMappingURL=cacheService.d.ts.map