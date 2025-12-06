/**
 * SDLC Orchestrator Authentication Service
 *
 * Manages JWT token storage, refresh, and authentication flows
 * including OAuth device flow for GitHub authentication.
 *
 * Sprint 27 Day 1 - Auth Service
 * @version 0.1.0
 */

import * as vscode from 'vscode';
import axios from 'axios';
import { Logger } from '../utils/logger';
import { ConfigManager } from '../utils/config';

/**
 * Token storage keys
 */
const TOKEN_KEY = 'sdlc.accessToken';
const REFRESH_TOKEN_KEY = 'sdlc.refreshToken';
const TOKEN_EXPIRY_KEY = 'sdlc.tokenExpiry';

/**
 * GitHub OAuth device flow response
 */
interface DeviceCodeResponse {
    device_code: string;
    user_code: string;
    verification_uri: string;
    expires_in: number;
    interval: number;
}

/**
 * Token response from auth endpoint
 */
interface TokenResponse {
    access_token: string;
    refresh_token?: string;
    token_type: string;
    expires_in: number;
}

/**
 * Authentication Service for SDLC Orchestrator
 */
export class AuthService {
    private secrets: vscode.SecretStorage;

    constructor(context: vscode.ExtensionContext) {
        this.secrets = context.secrets;
    }

    /**
     * Checks if user is currently authenticated
     */
    async isAuthenticated(): Promise<boolean> {
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
                } catch {
                    return false;
                }
            }
        }

        return true;
    }

    /**
     * Gets the current access token
     */
    async getToken(): Promise<string | undefined> {
        return this.secrets.get(TOKEN_KEY);
    }

    /**
     * Sets the access token
     */
    async setToken(token: string, expiresIn?: number): Promise<void> {
        await this.secrets.store(TOKEN_KEY, token);

        if (expiresIn) {
            // Store expiry time (with 5 minute buffer)
            const expiryTime = Date.now() + (expiresIn - 300) * 1000;
            await this.secrets.store(TOKEN_EXPIRY_KEY, expiryTime.toString());
        }

        Logger.info('Access token stored successfully');
    }

    /**
     * Sets the refresh token
     */
    async setRefreshToken(token: string): Promise<void> {
        await this.secrets.store(REFRESH_TOKEN_KEY, token);
        Logger.info('Refresh token stored successfully');
    }

    /**
     * Refreshes the access token using refresh token
     */
    async refreshToken(): Promise<void> {
        const refreshToken = await this.secrets.get(REFRESH_TOKEN_KEY);
        if (!refreshToken) {
            throw new Error('No refresh token available');
        }

        const config = ConfigManager.getInstance();

        try {
            const response = await axios.post<TokenResponse>(
                `${config.apiUrl}/api/v1/auth/refresh`,
                { refresh_token: refreshToken },
                {
                    headers: {
                        'Content-Type': 'application/json',
                    },
                }
            );

            await this.setToken(response.data.access_token, response.data.expires_in);

            if (response.data.refresh_token) {
                await this.setRefreshToken(response.data.refresh_token);
            }

            Logger.info('Token refreshed successfully');
        } catch (error) {
            Logger.error('Token refresh failed');
            // Clear invalid tokens
            await this.logout();
            throw error;
        }
    }

    /**
     * Logs out the user and clears all tokens
     */
    async logout(): Promise<void> {
        await this.secrets.delete(TOKEN_KEY);
        await this.secrets.delete(REFRESH_TOKEN_KEY);
        await this.secrets.delete(TOKEN_EXPIRY_KEY);
        Logger.info('User logged out, tokens cleared');
    }

    /**
     * Initiates GitHub OAuth device flow login
     *
     * This follows the OAuth 2.0 Device Authorization Grant flow:
     * 1. Request device code from backend
     * 2. Show user code and verification URL
     * 3. Poll for token completion
     */
    async loginWithGitHub(): Promise<void> {
        const config = ConfigManager.getInstance();

        try {
            // Step 1: Request device code
            Logger.info('Initiating GitHub device flow');
            const deviceResponse = await axios.post<DeviceCodeResponse>(
                `${config.apiUrl}/api/v1/auth/github/device`,
                {},
                {
                    headers: {
                        'Content-Type': 'application/json',
                    },
                }
            );

            const {
                device_code,
                user_code,
                verification_uri,
                expires_in,
                interval,
            } = deviceResponse.data;

            // Step 2: Show user code to user
            const result = await vscode.window.showInformationMessage(
                `Enter code ${user_code} at ${verification_uri}`,
                { modal: true },
                'Open Browser',
                'Copy Code'
            );

            if (result === 'Open Browser') {
                await vscode.env.openExternal(vscode.Uri.parse(verification_uri));
                await vscode.env.clipboard.writeText(user_code);
                void vscode.window.showInformationMessage(
                    `Code ${user_code} copied to clipboard`
                );
            } else if (result === 'Copy Code') {
                await vscode.env.clipboard.writeText(user_code);
            }

            // Step 3: Poll for token
            await this.pollForToken(device_code, expires_in, interval);
        } catch (error) {
            const message = error instanceof Error ? error.message : 'Unknown error';
            Logger.error(`GitHub login failed: ${message}`);
            throw new Error(`GitHub login failed: ${message}`);
        }
    }

    /**
     * Polls the auth endpoint for token completion
     */
    private async pollForToken(
        deviceCode: string,
        expiresIn: number,
        interval: number
    ): Promise<void> {
        const config = ConfigManager.getInstance();
        const pollInterval = Math.max(interval, 5) * 1000; // Minimum 5 seconds
        const expiryTime = Date.now() + expiresIn * 1000;

        return new Promise((resolve, reject) => {
            const poll = async (): Promise<void> => {
                if (Date.now() >= expiryTime) {
                    reject(new Error('Device code expired. Please try again.'));
                    return;
                }

                try {
                    const response = await axios.post<TokenResponse>(
                        `${config.apiUrl}/api/v1/auth/github/token`,
                        { device_code: deviceCode },
                        {
                            headers: {
                                'Content-Type': 'application/json',
                            },
                        }
                    );

                    // Success - store tokens
                    await this.setToken(
                        response.data.access_token,
                        response.data.expires_in
                    );

                    if (response.data.refresh_token) {
                        await this.setRefreshToken(response.data.refresh_token);
                    }

                    Logger.info('GitHub authentication successful');
                    resolve();
                } catch (error) {
                    if (axios.isAxiosError(error)) {
                        const errorCode =
                            (error.response?.data as { error?: string })?.error ?? '';

                        if (errorCode === 'authorization_pending') {
                            // User hasn't authorized yet - continue polling
                            setTimeout(() => void poll(), pollInterval);
                            return;
                        } else if (errorCode === 'slow_down') {
                            // Slow down polling
                            setTimeout(() => void poll(), pollInterval + 5000);
                            return;
                        } else if (errorCode === 'expired_token') {
                            reject(new Error('Device code expired. Please try again.'));
                            return;
                        } else if (errorCode === 'access_denied') {
                            reject(new Error('Authorization denied by user.'));
                            return;
                        }
                    }

                    // Unexpected error - reject
                    const message =
                        error instanceof Error ? error.message : 'Unknown error';
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
    async validateStoredToken(): Promise<boolean> {
        const token = await this.getToken();
        if (!token) {
            return false;
        }

        const config = ConfigManager.getInstance();

        try {
            await axios.get(`${config.apiUrl}/api/v1/auth/validate`, {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });
            return true;
        } catch {
            return false;
        }
    }

    /**
     * Gets user info from stored token (if JWT)
     */
    async getTokenUserInfo(): Promise<{
        userId?: string;
        email?: string;
        exp?: number;
    } | null> {
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

            const payload = JSON.parse(
                Buffer.from(parts[1] ?? '', 'base64').toString('utf-8')
            ) as { sub?: string; email?: string; exp?: number };

            const result: { userId?: string; email?: string; exp?: number } = {};
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
        } catch {
            return null;
        }
    }
}
