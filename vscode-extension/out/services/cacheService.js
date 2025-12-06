"use strict";
/**
 * SDLC Orchestrator Cache Service
 *
 * Provides offline caching for API responses using VS Code's globalState.
 * Implements TTL-based cache invalidation and stale-while-revalidate pattern.
 *
 * Sprint 27 Day 2 - Cache Service
 * @version 0.1.0
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.CacheService = exports.CacheTTL = exports.CacheKeys = void 0;
const logger_1 = require("../utils/logger");
/**
 * Default cache configuration
 */
const DEFAULT_CONFIG = {
    defaultTtl: 5 * 60 * 1000, // 5 minutes
    maxSize: 100,
    staleWhileRevalidate: true,
    staleGracePeriod: 60 * 1000, // 1 minute
};
/**
 * Cache key prefixes for different data types
 */
exports.CacheKeys = {
    PROJECTS: 'cache.projects',
    GATES: (projectId) => `cache.gates.${projectId}`,
    VIOLATIONS: (projectId) => `cache.violations.${projectId}`,
    PROJECT: (projectId) => `cache.project.${projectId}`,
    GATE: (gateId) => `cache.gate.${gateId}`,
    VIOLATION: (violationId) => `cache.violation.${violationId}`,
    USER: 'cache.user',
    COUNCIL_HISTORY: (projectId) => `cache.council.${projectId}`,
};
/**
 * TTL values for different cache types (in milliseconds)
 */
exports.CacheTTL = {
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
};
/**
 * Cache Service for offline support
 */
class CacheService {
    context;
    config;
    memoryCache;
    constructor(context, config) {
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
    get(key) {
        // Check memory cache first
        let entry = this.memoryCache.get(key);
        // Fall back to persisted cache
        if (!entry) {
            entry = this.context.globalState.get(key);
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
    async set(key, data, ttl, etag) {
        const entry = {
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
        logger_1.Logger.debug(`Cache set: ${key} (TTL: ${entry.ttl}ms)`);
    }
    /**
     * Deletes data from cache
     *
     * @param key - Cache key
     */
    async delete(key) {
        this.memoryCache.delete(key);
        await this.context.globalState.update(key, undefined);
        logger_1.Logger.debug(`Cache delete: ${key}`);
    }
    /**
     * Clears all cached data
     */
    async clear() {
        const keys = this.context.globalState.keys();
        for (const key of keys) {
            if (key.startsWith('cache.')) {
                await this.context.globalState.update(key, undefined);
            }
        }
        this.memoryCache.clear();
        logger_1.Logger.info('Cache cleared');
    }
    /**
     * Clears cache for a specific project
     *
     * @param projectId - Project ID
     */
    async clearProject(projectId) {
        const keysToDelete = [
            exports.CacheKeys.GATES(projectId),
            exports.CacheKeys.VIOLATIONS(projectId),
            exports.CacheKeys.PROJECT(projectId),
            exports.CacheKeys.COUNCIL_HISTORY(projectId),
        ];
        for (const key of keysToDelete) {
            await this.delete(key);
        }
        logger_1.Logger.info(`Cache cleared for project: ${projectId}`);
    }
    /**
     * Invalidates cache entries matching a pattern
     *
     * @param pattern - Key pattern to match
     */
    async invalidatePattern(pattern) {
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
        logger_1.Logger.debug(`Cache invalidated for pattern: ${pattern}`);
    }
    /**
     * Gets cache statistics
     */
    getStats() {
        const keys = this.context.globalState.keys().filter((k) => k.startsWith('cache.'));
        let oldestTimestamp = null;
        let newestTimestamp = null;
        for (const key of keys) {
            const entry = this.context.globalState.get(key);
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
    isFresh(key) {
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
    async getOrFetch(key, fetcher, ttl) {
        // Try to get from cache first
        const cached = this.get(key);
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
        }
        catch (error) {
            // If fetch fails and we have stale data, return it
            if (cached) {
                logger_1.Logger.warn(`Fetch failed, returning stale data for: ${key}`);
                return cached;
            }
            throw error;
        }
    }
    /**
     * Revalidates cache entry in background
     */
    async revalidateInBackground(key, fetcher, ttl) {
        try {
            logger_1.Logger.debug(`Background revalidation: ${key}`);
            const data = await fetcher();
            await this.set(key, data, ttl);
        }
        catch (error) {
            logger_1.Logger.warn(`Background revalidation failed for: ${key}`);
        }
    }
    /**
     * Enforces maximum cache size by removing oldest entries
     */
    async enforceMaxSize() {
        const keys = this.context.globalState.keys().filter((k) => k.startsWith('cache.'));
        if (keys.length <= this.config.maxSize) {
            return;
        }
        // Get all entries with timestamps
        const entries = [];
        for (const key of keys) {
            const entry = this.context.globalState.get(key);
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
        logger_1.Logger.debug(`Cache size enforced, removed ${toRemove.length} entries`);
    }
    /**
     * Loads persisted cache into memory cache
     */
    loadPersistedCache() {
        const keys = this.context.globalState.keys().filter((k) => k.startsWith('cache.'));
        for (const key of keys) {
            const entry = this.context.globalState.get(key);
            if (entry) {
                this.memoryCache.set(key, entry);
            }
        }
        logger_1.Logger.debug(`Loaded ${this.memoryCache.size} cache entries from storage`);
    }
    /**
     * Preloads cache for a project (call after project selection)
     */
    async preloadProject(projectId, fetchers) {
        logger_1.Logger.info(`Preloading cache for project: ${projectId}`);
        const promises = [];
        if (fetchers.gates) {
            promises.push(this.getOrFetch(exports.CacheKeys.GATES(projectId), fetchers.gates, exports.CacheTTL.GATES).then(() => undefined));
        }
        if (fetchers.violations) {
            promises.push(this.getOrFetch(exports.CacheKeys.VIOLATIONS(projectId), fetchers.violations, exports.CacheTTL.VIOLATIONS).then(() => undefined));
        }
        await Promise.allSettled(promises);
        logger_1.Logger.info(`Cache preload complete for project: ${projectId}`);
    }
}
exports.CacheService = CacheService;
//# sourceMappingURL=cacheService.js.map