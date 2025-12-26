"use strict";
/**
 * SDLC Orchestrator Authentication Service
 *
 * Manages JWT token storage, refresh, and authentication flows
 * including OAuth device flow for GitHub authentication.
 *
 * Sprint 27 Day 1 - Auth Service
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
exports.AuthService = void 0;
const vscode = __importStar(require("vscode"));
const axios_1 = __importDefault(require("axios"));
const logger_1 = require("../utils/logger");
const config_1 = require("../utils/config");
/**
 * Token storage keys
 */
const TOKEN_KEY = 'sdlc.accessToken';
const REFRESH_TOKEN_KEY = 'sdlc.refreshToken';
const TOKEN_EXPIRY_KEY = 'sdlc.tokenExpiry';
/**
 * Authentication Service for SDLC Orchestrator
 */
class AuthService {
    secrets;
    constructor(context) {
        this.secrets = context.secrets;
    }
    /**
     * Checks if user is currently authenticated
     */
    async isAuthenticated() {
        const token = await this.getToken();
        if (!token) {
            return false;
        }
        // Check if token is expired
        const expiryStr = await this.secrets.get(TOKEN_EXPIRY_KEY);
        if (expiryStr) {
            const expiry = parseInt(expiryStr, 10);
            if (Date.now() >= expiry) {
                // Try to refresh the token
                try {
                    await this.refreshToken();
                    return true;
                }
                catch {
                    return false;
                }
            }
        }
        return true;
    }
    /**
     * Gets the current access token
     */
    async getToken() {
        return this.secrets.get(TOKEN_KEY);
    }
    /**
     * Sets the access token
     */
    async setToken(token, expiresIn) {
        await this.secrets.store(TOKEN_KEY, token);
        if (expiresIn) {
            // Store expiry time (with 5 minute buffer)
            const expiryTime = Date.now() + (expiresIn - 300) * 1000;
            await this.secrets.store(TOKEN_EXPIRY_KEY, expiryTime.toString());
        }
        logger_1.Logger.info('Access token stored successfully');
    }
    /**
     * Sets the refresh token
     */
    async setRefreshToken(token) {
        await this.secrets.store(REFRESH_TOKEN_KEY, token);
        logger_1.Logger.info('Refresh token stored successfully');
    }
    /**
     * Refreshes the access token using refresh token
     */
    async refreshToken() {
        const refreshToken = await this.secrets.get(REFRESH_TOKEN_KEY);
        if (!refreshToken) {
            throw new Error('No refresh token available');
        }
        const config = config_1.ConfigManager.getInstance();
        try {
            const response = await axios_1.default.post(`${config.apiUrl}/api/v1/auth/refresh`, { refresh_token: refreshToken }, {
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            await this.setToken(response.data.access_token, response.data.expires_in);
            if (response.data.refresh_token) {
                await this.setRefreshToken(response.data.refresh_token);
            }
            logger_1.Logger.info('Token refreshed successfully');
        }
        catch (error) {
            logger_1.Logger.error('Token refresh failed');
            // Clear invalid tokens
            await this.logout();
            throw error;
        }
    }
    /**
     * Logs out the user and clears all tokens
     */
    async logout() {
        await this.secrets.delete(TOKEN_KEY);
        await this.secrets.delete(REFRESH_TOKEN_KEY);
        await this.secrets.delete(TOKEN_EXPIRY_KEY);
        logger_1.Logger.info('User logged out, tokens cleared');
    }
    /**
     * Login with email and password
     *
     * Authenticates the user with the SDLC Orchestrator backend
     * using email and password credentials.
     *
     * @param email - User's email address
     * @param password - User's password
     */
    async loginWithEmailPassword(email, password) {
        const config = config_1.ConfigManager.getInstance();
        try {
            logger_1.Logger.info('Initiating email/password login');
            const response = await axios_1.default.post(`${config.apiUrl}/api/v1/auth/login`, { email, password }, {
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            // Store tokens
            await this.setToken(response.data.access_token, response.data.expires_in);
            if (response.data.refresh_token) {
                await this.setRefreshToken(response.data.refresh_token);
            }
            logger_1.Logger.info('Email/password authentication successful');
        }
        catch (error) {
            if (axios_1.default.isAxiosError(error)) {
                const detail = error.response?.data?.detail;
                const message = detail ?? error.message ?? 'Authentication failed';
                logger_1.Logger.error(`Email/password login failed: ${message}`);
                throw new Error(message);
            }
            const message = error instanceof Error ? error.message : 'Unknown error';
            logger_1.Logger.error(`Email/password login failed: ${message}`);
            throw new Error(`Login failed: ${message}`);
        }
    }
    /**
     * Initiates GitHub OAuth device flow login
     *
     * This follows the OAuth 2.0 Device Authorization Grant flow:
     * 1. Request device code from backend
     * 2. Show user code and verification URL
     * 3. Poll for token completion
     */
    async loginWithGitHub() {
        const config = config_1.ConfigManager.getInstance();
        try {
            // Step 1: Request device code
            logger_1.Logger.info('Initiating GitHub device flow');
            const deviceResponse = await axios_1.default.post(`${config.apiUrl}/api/v1/auth/github/device`, {}, {
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            const { device_code, user_code, verification_uri, expires_in, interval, } = deviceResponse.data;
            // Step 2: Show user code to user
            const result = await vscode.window.showInformationMessage(`Enter code ${user_code} at ${verification_uri}`, { modal: true }, 'Open Browser', 'Copy Code');
            if (result === 'Open Browser') {
                await vscode.env.openExternal(vscode.Uri.parse(verification_uri));
                await vscode.env.clipboard.writeText(user_code);
                void vscode.window.showInformationMessage(`Code ${user_code} copied to clipboard`);
            }
            else if (result === 'Copy Code') {
                await vscode.env.clipboard.writeText(user_code);
            }
            // Step 3: Poll for token
            await this.pollForToken(device_code, expires_in, interval);
        }
        catch (error) {
            const message = error instanceof Error ? error.message : 'Unknown error';
            logger_1.Logger.error(`GitHub login failed: ${message}`);
            throw new Error(`GitHub login failed: ${message}`);
        }
    }
    /**
     * Polls the auth endpoint for token completion
     */
    async pollForToken(deviceCode, expiresIn, interval) {
        const config = config_1.ConfigManager.getInstance();
        const pollInterval = Math.max(interval, 5) * 1000; // Minimum 5 seconds
        const expiryTime = Date.now() + expiresIn * 1000;
        return new Promise((resolve, reject) => {
            const poll = async () => {
                if (Date.now() >= expiryTime) {
                    reject(new Error('Device code expired. Please try again.'));
                    return;
                }
                try {
                    const response = await axios_1.default.post(`${config.apiUrl}/api/v1/auth/github/token`, { device_code: deviceCode }, {
                        headers: {
                            'Content-Type': 'application/json',
                        },
                    });
                    // Success - store tokens
                    await this.setToken(response.data.access_token, response.data.expires_in);
                    if (response.data.refresh_token) {
                        await this.setRefreshToken(response.data.refresh_token);
                    }
                    logger_1.Logger.info('GitHub authentication successful');
                    resolve();
                }
                catch (error) {
                    if (axios_1.default.isAxiosError(error)) {
                        const errorCode = error.response?.data?.error ?? '';
                        if (errorCode === 'authorization_pending') {
                            // User hasn't authorized yet - continue polling
                            setTimeout(() => void poll(), pollInterval);
                            return;
                        }
                        else if (errorCode === 'slow_down') {
                            // Slow down polling
                            setTimeout(() => void poll(), pollInterval + 5000);
                            return;
                        }
                        else if (errorCode === 'expired_token') {
                            reject(new Error('Device code expired. Please try again.'));
                            return;
                        }
                        else if (errorCode === 'access_denied') {
                            reject(new Error('Authorization denied by user.'));
                            return;
                        }
                    }
                    // Unexpected error - reject
                    const message = error instanceof Error ? error.message : 'Unknown error';
                    reject(new Error(message));
                }
            };
            // Start polling
            void poll();
        });
    }
    /**
     * Validates that the stored token is still valid
     */
    async validateStoredToken() {
        const token = await this.getToken();
        if (!token) {
            return false;
        }
        const config = config_1.ConfigManager.getInstance();
        try {
            await axios_1.default.get(`${config.apiUrl}/api/v1/auth/validate`, {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });
            return true;
        }
        catch {
            return false;
        }
    }
    /**
     * Gets user info from stored token (if JWT)
     */
    async getTokenUserInfo() {
        const token = await this.getToken();
        if (!token) {
            return null;
        }
        try {
            // Decode JWT payload (base64)
            const parts = token.split('.');
            if (parts.length !== 3) {
                return null;
            }
            const payload = JSON.parse(Buffer.from(parts[1] ?? '', 'base64').toString('utf-8'));
            const result = {};
            if (payload.sub !== undefined) {
                result.userId = payload.sub;
            }
            if (payload.email !== undefined) {
                result.email = payload.email;
            }
            if (payload.exp !== undefined) {
                result.exp = payload.exp;
            }
            return result;
        }
        catch {
            return null;
        }
    }
}
exports.AuthService = AuthService;
//# sourceMappingURL=authService.js.map