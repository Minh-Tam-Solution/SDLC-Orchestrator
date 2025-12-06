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
/**
 * Authentication Service for SDLC Orchestrator
 */
export declare class AuthService {
    private secrets;
    constructor(context: vscode.ExtensionContext);
    /**
     * Checks if user is currently authenticated
     */
    isAuthenticated(): Promise<boolean>;
    /**
     * Gets the current access token
     */
    getToken(): Promise<string | undefined>;
    /**
     * Sets the access token
     */
    setToken(token: string, expiresIn?: number): Promise<void>;
    /**
     * Sets the refresh token
     */
    setRefreshToken(token: string): Promise<void>;
    /**
     * Refreshes the access token using refresh token
     */
    refreshToken(): Promise<void>;
    /**
     * Logs out the user and clears all tokens
     */
    logout(): Promise<void>;
    /**
     * Initiates GitHub OAuth device flow login
     *
     * This follows the OAuth 2.0 Device Authorization Grant flow:
     * 1. Request device code from backend
     * 2. Show user code and verification URL
     * 3. Poll for token completion
     */
    loginWithGitHub(): Promise<void>;
    /**
     * Polls the auth endpoint for token completion
     */
    private pollForToken;
    /**
     * Validates that the stored token is still valid
     */
    validateStoredToken(): Promise<boolean>;
    /**
     * Gets user info from stored token (if JWT)
     */
    getTokenUserInfo(): Promise<{
        userId?: string;
        email?: string;
        exp?: number;
    } | null>;
}
//# sourceMappingURL=authService.d.ts.map