"use strict";
/**
 * SDLC Orchestrator API Client
 *
 * Provides typed HTTP client for communicating with the SDLC Orchestrator backend.
 * Handles authentication, request/response transformation, and error handling.
 *
 * Sprint 27 Day 1 - API Client Service
 * @version 0.1.0
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
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.ApiClient = exports.ApiError = void 0;
const vscode = __importStar(require("vscode"));
const axios_1 = __importDefault(require("axios"));
const logger_1 = require("../utils/logger");
const config_1 = require("../utils/config");
/**
 * API Error class for typed error handling
 */
class ApiError extends Error {
    statusCode;
    statusText;
    responseData;
    constructor(statusCode, statusText, message, responseData) {
        super(message);
        this.statusCode = statusCode;
        this.statusText = statusText;
        this.responseData = responseData;
        this.name = 'ApiError';
    }
    static fromAxiosError(error) {
        const statusCode = error.response?.status ?? 0;
        const statusText = error.response?.statusText ?? 'Network Error';
        const message = error.response?.data?.detail ??
            error.message ??
            'Unknown error';
        return new ApiError(statusCode, statusText, message, error.response?.data);
    }
}
exports.ApiError = ApiError;
/**
 * API Client for SDLC Orchestrator backend
 */
class ApiClient {
    client;
    authService;
    baseUrl;
    constructor(_context, authService) {
        this.authService = authService;
        const config = config_1.ConfigManager.getInstance();
        this.baseUrl = config.apiUrl;
        this.client = axios_1.default.create({
            baseURL: this.baseUrl,
            timeout: 30000,
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'SDLC-Orchestrator-VSCode/0.1.0',
            },
        });
        this.setupInterceptors();
    }
    /**
     * Updates the base URL for API requests
     */
    updateBaseUrl(newUrl) {
        this.baseUrl = newUrl;
        this.client.defaults.baseURL = newUrl;
        logger_1.Logger.info(`API base URL updated to: ${newUrl}`);
    }
    /**
     * Sets up request/response interceptors
     */
    setupInterceptors() {
        // Request interceptor - add auth token
        this.client.interceptors.request.use(async (config) => {
            const token = await this.authService.getToken();
            if (token) {
                config.headers.Authorization = `Bearer ${token}`;
            }
            logger_1.Logger.debug(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
            return config;
        }, (error) => {
            logger_1.Logger.error(`Request interceptor error: ${error.message}`);
            return Promise.reject(error);
        });
        // Response interceptor - handle errors
        this.client.interceptors.response.use((response) => {
            logger_1.Logger.debug(`API Response: ${response.status} ${response.config.url}`);
            return response;
        }, async (error) => {
            if (error.response?.status === 401) {
                // Token expired - try to refresh
                try {
                    await this.authService.refreshToken();
                    // Retry the original request
                    const originalRequest = error.config;
                    if (originalRequest) {
                        const newToken = await this.authService.getToken();
                        originalRequest.headers.Authorization = `Bearer ${newToken}`;
                        return this.client.request(originalRequest);
                    }
                }
                catch {
                    // Refresh failed - logout user
                    await this.authService.logout();
                    void vscode.commands.executeCommand('setContext', 'sdlc.isAuthenticated', false);
                    void vscode.window.showErrorMessage('Session expired. Please log in again.');
                }
            }
            const apiError = ApiError.fromAxiosError(error);
            logger_1.Logger.error(`API Error: ${apiError.statusCode} - ${apiError.message}`);
            return Promise.reject(apiError);
        });
    }
    /**
     * Makes a typed GET request
     */
    async get(endpoint, config) {
        const response = await this.client.get(endpoint, config);
        return response.data;
    }
    /**
     * Makes a typed POST request
     */
    async post(endpoint, data, config) {
        const response = await this.client.post(endpoint, data, config);
        return response.data;
    }
    // ============================================
    // Project APIs
    // ============================================
    /**
     * Gets list of projects accessible to the current user
     */
    async getProjects(page = 1, pageSize = 50) {
        const response = await this.get(`/api/v1/projects?page=${page}&page_size=${pageSize}`);
        return response.items;
    }
    /**
     * Gets a single project by ID
     */
    async getProject(projectId) {
        return this.get(`/api/v1/projects/${projectId}`);
    }
    /**
     * Gets the currently selected project ID from configuration
     */
    getCurrentProjectId() {
        const config = config_1.ConfigManager.getInstance();
        return config.defaultProjectId || undefined;
    }
    // ============================================
    // Gate APIs
    // ============================================
    /**
     * Gets gates for a project
     */
    async getGates(projectId) {
        const response = await this.get(`/api/v1/projects/${projectId}/gates`);
        return response.items;
    }
    /**
     * Gets a single gate by ID
     */
    async getGate(gateId) {
        return this.get(`/api/v1/gates/${gateId}`);
    }
    /**
     * Gets gates for current project
     */
    async getCurrentProjectGates() {
        const projectId = this.getCurrentProjectId();
        if (!projectId) {
            return [];
        }
        return this.getGates(projectId);
    }
    // ============================================
    // Violation APIs
    // ============================================
    /**
     * Gets violations for a project
     */
    async getViolations(projectId, status, severity) {
        const params = new URLSearchParams();
        params.append('project_id', projectId);
        if (status) {
            params.append('status', status);
        }
        if (severity) {
            params.append('severity', severity);
        }
        const response = await this.get(`/api/v1/compliance/violations?${params.toString()}`);
        return response.items;
    }
    /**
     * Gets a single violation by ID
     */
    async getViolation(violationId) {
        return this.get(`/api/v1/compliance/violations/${violationId}`);
    }
    /**
     * Gets violations for current project
     */
    async getCurrentProjectViolations(status, severity) {
        const projectId = this.getCurrentProjectId();
        if (!projectId) {
            return [];
        }
        return this.getViolations(projectId, status, severity);
    }
    // ============================================
    // AI Council APIs
    // ============================================
    /**
     * Gets AI recommendation for a violation
     *
     * @param violationId - ID of the violation to get recommendation for
     * @param councilMode - If true, uses 3-stage AI Council deliberation
     */
    async getAIRecommendation(violationId, councilMode = true) {
        return this.post('/api/v1/ai/council/recommend', {
            violation_id: violationId,
            council_mode: councilMode,
        });
    }
    /**
     * Gets AI Council deliberation status for an async request
     */
    async getCouncilStatus(requestId) {
        return this.get(`/api/v1/ai/council/status/${requestId}`);
    }
    /**
     * Gets AI Council deliberation history for a project
     */
    async getCouncilHistory(projectId, limit = 10) {
        const response = await this.get(`/api/v1/ai/council/history/${projectId}?limit=${limit}`);
        return response.items;
    }
    // ============================================
    // Compliance Scan APIs
    // ============================================
    /**
     * Triggers a compliance scan for a project
     */
    async triggerComplianceScan(projectId) {
        return this.post('/api/v1/compliance/scan', { project_id: projectId });
    }
    /**
     * Gets compliance scan status
     */
    async getScanStatus(scanId) {
        return this.get(`/api/v1/compliance/scan/${scanId}`);
    }
    // ============================================
    // User & Auth APIs
    // ============================================
    /**
     * Gets current user profile
     */
    async getCurrentUser() {
        return this.get('/api/v1/users/me');
    }
    /**
     * Validates the current token
     */
    async validateToken() {
        try {
            await this.get('/api/v1/auth/validate');
            return true;
        }
        catch {
            return false;
        }
    }
}
exports.ApiClient = ApiClient;
//# sourceMappingURL=apiClient.js.map