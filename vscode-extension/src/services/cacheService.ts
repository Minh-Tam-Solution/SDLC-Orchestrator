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
import { Logger } from '../utils/logger';

/**
 * Cache entry with metadata
 */
interface CacheEntry<T> {
    data: T;
    timestamp: number;
    ttl: number;
    etag?: string;
}

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
 * Default cache configuration
 */
const DEFAULT_CONFIG: CacheConfig = {
    defaultTtl: 5 * 60 * 1000, // 5 minutes
    maxSize: 100,
    staleWhileRevalidate: true,
    staleGracePeriod: 60 * 1000, // 1 minute
};

/**
 * Cache key prefixes for different data types
 */
export const CacheKeys = {
    PROJECTS: 'cache.projects',
    GATES: (projectId: string) => `cache.gates.${projectId}`,
    VIOLATIONS: (projectId: string) => `cache.violations.${projectId}`,
    PROJECT: (projectId: string) => `cache.project.${projectId}`,
    GATE: (gateId: string) => `cache.gate.${gateId}`,
    VIOLATION: (violationId: string) => `cache.violation.${violationId}`,
    USER: 'cache.user',
    COUNCIL_HISTORY: (projectId: string) => `cache.council.${projectId}`,
} as const;

/**
 * TTL values for different cache types (in milliseconds)
 */
export const CacheTTL = {
    /** Projects list - cache for 10 minutes */
    PROJECTS: 10 * 60 * 1000,
    /** Gates - cache for 2 minutes (frequently updated) */
    GATES: 2 * 60 * 1000,
    /** Violations - cache for 2 minutes */
    VIOLATIONS: 2 * 60 * 1000,
    /** Individual project/gate/violation - cache for 5 minutes */
    SINGLE_ITEM: 5 * 60 * 1000,
    /** User profile - cache for 30 minutes */
    USER: 30 * 60 * 1000,
    /** Council history - cache for 15 minutes */
    COUNCIL_HISTORY: 15 * 60 * 1000,
} as const;

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
export class CacheService {
    private context: vscode.ExtensionContext;
    private config: CacheConfig;
    private memoryCache: Map<string, CacheEntry<unknown>>;

    constructor(context: vscode.ExtensionContext, config?: Partial<CacheConfig>) {
        this.context = context;
        this.config = { ...DEFAULT_CONFIG, ...config };
        this.memoryCache = new Map();

        // Load persisted cache into memory on startup
        void this.loadPersistedCache();
    }

    /**
     * Gets data from cache
     *
     * @param key - Cache key
     * @returns Cached data or undefined if not found/expired
     */
    get<T>(key: string): CacheResult<T> | undefined {
        // Check memory cache first
        let entry = this.memoryCache.get(key) as CacheEntry<T> | undefined;

        // Fall back to persisted cache
        if (!entry) {
            entry = this.context.globalState.get<CacheEntry<T>>(key);
            if (entry) {
                // Populate memory cache
                this.memoryCache.set(key, entry);
            }
        }

        if (!entry) {
            return undefined;
        }

        const now = Date.now();
        const age = now - entry.timestamp;
        const isExpired = age > entry.ttl;
        const isStale = isExpired && age < entry.ttl + this.config.staleGracePeriod;

        // Return stale data if within grace period
        if (isExpired && !isStale) {
            // Data is too old, remove from cache
            void this.delete(key);
            return undefined;
        }

        return {
            data: entry.data,
            isStale,
            isCached: true,
            age,
        };
    }

    /**
     * Sets data in cache
     *
     * @param key - Cache key
     * @param data - Data to cache
     * @param ttl - Time to live in milliseconds (optional)
     * @param etag - ETag for conditional requests (optional)
     */
    async set<T>(key: string, data: T, ttl?: number, etag?: string): Promise<void> {
        const entry: CacheEntry<T> = {
            data,
            timestamp: Date.now(),
            ttl: ttl ?? this.config.defaultTtl,
        };
        if (etag !== undefined) {
            entry.etag = etag;
        }

        // Update memory cache
        this.memoryCache.set(key, entry);

        // Persist to globalState
        await this.context.globalState.update(key, entry);

        // Enforce max size
        await this.enforceMaxSize();

        Logger.debug(`Cache set: ${key} (TTL: ${entry.ttl}ms)`);
    }

    /**
     * Deletes data from cache
     *
     * @param key - Cache key
     */
    async delete(key: string): Promise<void> {
        this.memoryCache.delete(key);
        await this.context.globalState.update(key, undefined);
        Logger.debug(`Cache delete: ${key}`);
    }

    /**
     * Clears all cached data
     */
    async clear(): Promise<void> {
        const keys = this.context.globalState.keys();

        for (const key of keys) {
            if (key.startsWith('cache.')) {
                await this.context.globalState.update(key, undefined);
            }
        }

        this.memoryCache.clear();
        Logger.info('Cache cleared');
    }

    /**
     * Clears cache for a specific project
     *
     * @param projectId - Project ID
     */
    async clearProject(projectId: string): Promise<void> {
        const keysToDelete = [
            CacheKeys.GATES(projectId),
            CacheKeys.VIOLATIONS(projectId),
            CacheKeys.PROJECT(projectId),
            CacheKeys.COUNCIL_HISTORY(projectId),
        ];

        for (const key of keysToDelete) {
            await this.delete(key);
        }

        Logger.info(`Cache cleared for project: ${projectId}`);
    }

    /**
     * Invalidates cache entries matching a pattern
     *
     * @param pattern - Key pattern to match
     */
    async invalidatePattern(pattern: string): Promise<void> {
        const keys = this.context.globalState.keys();
        const regex = new RegExp(pattern);

        for (const key of keys) {
            if (regex.test(key)) {
                await this.delete(key);
            }
        }

        // Also clear from memory cache
        for (const key of this.memoryCache.keys()) {
            if (regex.test(key)) {
                this.memoryCache.delete(key);
            }
        }

        Logger.debug(`Cache invalidated for pattern: ${pattern}`);
    }

    /**
     * Gets cache statistics
     */
    getStats(): {
        memoryEntries: number;
        persistedEntries: number;
        oldestEntry: number | null;
        newestEntry: number | null;
    } {
        const keys = this.context.globalState.keys().filter((k) => k.startsWith('cache.'));

        let oldestTimestamp: number | null = null;
        let newestTimestamp: number | null = null;

        for (const key of keys) {
            const entry = this.context.globalState.get<CacheEntry<unknown>>(key);
            if (entry) {
                if (oldestTimestamp === null || entry.timestamp < oldestTimestamp) {
                    oldestTimestamp = entry.timestamp;
                }
                if (newestTimestamp === null || entry.timestamp > newestTimestamp) {
                    newestTimestamp = entry.timestamp;
                }
            }
        }

        return {
            memoryEntries: this.memoryCache.size,
            persistedEntries: keys.length,
            oldestEntry: oldestTimestamp,
            newestEntry: newestTimestamp,
        };
    }

    /**
     * Checks if data is cached and fresh
     *
     * @param key - Cache key
     */
    isFresh(key: string): boolean {
        const result = this.get(key);
        return result !== undefined && !result.isStale;
    }

    /**
     * Gets cached data or fetches fresh data
     *
     * @param key - Cache key
     * @param fetcher - Function to fetch fresh data
     * @param ttl - TTL for cache entry
     */
    async getOrFetch<T>(
        key: string,
        fetcher: () => Promise<T>,
        ttl?: number
    ): Promise<CacheResult<T>> {
        // Try to get from cache first
        const cached = this.get<T>(key);

        if (cached && !cached.isStale) {
            return cached;
        }

        // If stale, return stale data and revalidate in background
        if (cached?.isStale && this.config.staleWhileRevalidate) {
            void this.revalidateInBackground(key, fetcher, ttl);
            return cached;
        }

        // Fetch fresh data
        try {
            const data = await fetcher();
            await this.set(key, data, ttl);

            return {
                data,
                isStale: false,
                isCached: false,
                age: 0,
            };
        } catch (error) {
            // If fetch fails and we have stale data, return it
            if (cached) {
                Logger.warn(`Fetch failed, returning stale data for: ${key}`);
                return cached;
            }
            throw error;
        }
    }

    /**
     * Revalidates cache entry in background
     */
    private async revalidateInBackground<T>(
        key: string,
        fetcher: () => Promise<T>,
        ttl?: number
    ): Promise<void> {
        try {
            Logger.debug(`Background revalidation: ${key}`);
            const data = await fetcher();
            await this.set(key, data, ttl);
        } catch (error) {
            Logger.warn(`Background revalidation failed for: ${key}`);
        }
    }

    /**
     * Enforces maximum cache size by removing oldest entries
     */
    private async enforceMaxSize(): Promise<void> {
        const keys = this.context.globalState.keys().filter((k) => k.startsWith('cache.'));

        if (keys.length <= this.config.maxSize) {
            return;
        }

        // Get all entries with timestamps
        const entries: Array<{ key: string; timestamp: number }> = [];

        for (const key of keys) {
            const entry = this.context.globalState.get<CacheEntry<unknown>>(key);
            if (entry) {
                entries.push({ key, timestamp: entry.timestamp });
            }
        }

        // Sort by timestamp (oldest first)
        entries.sort((a, b) => a.timestamp - b.timestamp);

        // Remove oldest entries until we're under the limit
        const toRemove = entries.slice(0, entries.length - this.config.maxSize);

        for (const { key } of toRemove) {
            await this.delete(key);
        }

        Logger.debug(`Cache size enforced, removed ${toRemove.length} entries`);
    }

    /**
     * Loads persisted cache into memory cache
     */
    private loadPersistedCache(): void {
        const keys = this.context.globalState.keys().filter((k) => k.startsWith('cache.'));

        for (const key of keys) {
            const entry = this.context.globalState.get<CacheEntry<unknown>>(key);
            if (entry) {
                this.memoryCache.set(key, entry);
            }
        }

        Logger.debug(`Loaded ${this.memoryCache.size} cache entries from storage`);
    }

    /**
     * Preloads cache for a project (call after project selection)
     */
    async preloadProject(
        projectId: string,
        fetchers: {
            gates?: () => Promise<unknown>;
            violations?: () => Promise<unknown>;
        }
    ): Promise<void> {
        Logger.info(`Preloading cache for project: ${projectId}`);

        const promises: Promise<void>[] = [];

        if (fetchers.gates) {
            promises.push(
                this.getOrFetch(
                    CacheKeys.GATES(projectId),
                    fetchers.gates,
                    CacheTTL.GATES
                ).then(() => undefined)
            );
        }

        if (fetchers.violations) {
            promises.push(
                this.getOrFetch(
                    CacheKeys.VIOLATIONS(projectId),
                    fetchers.violations,
                    CacheTTL.VIOLATIONS
                ).then(() => undefined)
            );
        }

        await Promise.allSettled(promises);
        Logger.info(`Cache preload complete for project: ${projectId}`);
    }
}
