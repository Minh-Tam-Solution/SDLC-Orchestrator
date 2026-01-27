/**
 * OAuth Callback Page - SDLC Orchestrator Landing
 *
 * @module frontend/landing/src/app/auth/callback/page
 * @description Handles OAuth callback from GitHub/Google providers
 * @sdlc SDLC 5.1.2 Universal Framework
 * @status Sprint 59 - OAuth Integration
 */

"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Header, Footer } from "@/components/landing";
import { exchangeOAuthCode, APIError } from "@/lib/api";
import { trackRegistrationComplete, trackEvent, ANALYTICS_EVENTS } from "@/lib/analytics";
import Link from "next/link";

type CallbackStatus = "processing" | "success" | "error";

function OAuthCallbackHandler() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [status, setStatus] = useState<CallbackStatus>("processing");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    const handleCallback = async () => {
      // Get OAuth parameters from URL
      const code = searchParams.get("code");
      const state = searchParams.get("state");
      const error = searchParams.get("error");
      const errorDescription = searchParams.get("error_description");

      // Handle OAuth error from provider
      if (error) {
        setStatus("error");
        setErrorMessage(errorDescription || `OAuth error: ${error}`);
        trackEvent(ANALYTICS_EVENTS.REGISTRATION_ERROR, {
          error_type: error,
          method: "oauth",
        });
        return;
      }

      // Validate required parameters
      if (!code || !state) {
        setStatus("error");
        setErrorMessage("Missing authorization code or state parameter");
        return;
      }

      // Validate state matches what we stored (CSRF protection)
      // NOTE: Using localStorage instead of sessionStorage because sessionStorage
      // can be lost in Incognito mode when redirecting to external OAuth providers
      const storedState = localStorage.getItem("oauth_state");

      // Debug logging to identify state mismatch issue
      console.log("[OAuth Debug]", {
        urlState: state,
        urlStateLength: state?.length,
        storedState: storedState,
        storedStateLength: storedState?.length,
        match: storedState === state,
        localStorage: {
          oauth_state: storedState,
          oauth_redirect: localStorage.getItem("oauth_redirect"),
          oauth_flow: localStorage.getItem("oauth_flow"),
          oauth_provider: localStorage.getItem("oauth_provider"),
        },
      });

      if (!storedState || storedState !== state) {
        setStatus("error");
        setErrorMessage("Invalid state parameter. Please try again.");
        trackEvent(ANALYTICS_EVENTS.REGISTRATION_ERROR, {
          error_type: "state_mismatch",
          method: "oauth",
        });
        return;
      }

      // Provider is selected by the user at login/register time.
      // Avoid decoding `state` in the browser (it's urlsafe base64 and backend-defined).
      const provider = (localStorage.getItem("oauth_provider") as "github" | "google" | null) || "github";

      // Capture redirect BEFORE cleanup - default to /app for logged in users
      const redirectTo = localStorage.getItem("oauth_redirect") || "/app";

      try {
        // Exchange code for tokens
        console.log("[OAuth Callback] Starting token exchange at:", new Date().toISOString());
        console.log("[OAuth Callback] Provider:", provider, "Code length:", code?.length);
        const startTime = Date.now();
        const response = await exchangeOAuthCode(provider, {
          code,
          state,
        });
        console.log("[OAuth Callback] Token exchange completed in:", Date.now() - startTime, "ms");

        // Store tokens
        if (response.access_token) {
          localStorage.setItem("access_token", response.access_token);
          if (response.refresh_token) {
            localStorage.setItem("refresh_token", response.refresh_token);
          }
        }

        // Track successful authentication
        const oauthFlow = localStorage.getItem("oauth_flow");
        if (oauthFlow === "signup") {
          trackRegistrationComplete(provider, 0);
        } else {
          trackEvent(ANALYTICS_EVENTS.LOGIN_SUCCESS, { method: provider });
        }

        // Clean up localStorage (OAuth state data)
        localStorage.removeItem("oauth_state");
        localStorage.removeItem("oauth_redirect");
        localStorage.removeItem("oauth_flow");
        localStorage.removeItem("oauth_provider");

        setStatus("success");

        // Redirect after short delay
        setTimeout(() => {
          router.push(redirectTo);
        }, 1500);

      } catch (error) {
        console.log("[OAuth Callback] Error caught:", error);
        console.log("[OAuth Callback] Error at:", new Date().toISOString());
        const apiErr = error as APIError;
        setStatus("error");
        setErrorMessage(apiErr.detail || "Failed to complete authentication. Please try again.");

        trackEvent(ANALYTICS_EVENTS.REGISTRATION_ERROR, {
          error_type: apiErr.detail || "token_exchange_failed",
          method: provider,
        });

        // Clean up localStorage on error too
        localStorage.removeItem("oauth_state");
        localStorage.removeItem("oauth_redirect");
        localStorage.removeItem("oauth_flow");
        localStorage.removeItem("oauth_provider");
      }
    };

    handleCallback();
  }, [searchParams, router]);

  // Processing state
  if (status === "processing") {
    return (
      <>
        <Header />
        <main className="min-h-screen bg-secondary/30 flex items-center justify-center py-16">
          <Card className="w-full max-w-md mx-4">
            <CardHeader className="text-center">
              <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg
                  className="animate-spin h-8 w-8 text-primary"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
              </div>
              <CardTitle className="text-heading-2">Completing Sign In</CardTitle>
              <CardDescription>
                Please wait while we verify your account...
              </CardDescription>
            </CardHeader>
          </Card>
        </main>
        <Footer />
      </>
    );
  }

  // Success state
  if (status === "success") {
    return (
      <>
        <Header />
        <main className="min-h-screen bg-secondary/30 flex items-center justify-center py-16">
          <Card className="w-full max-w-md mx-4">
            <CardHeader className="text-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg
                  className="w-8 h-8 text-green-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
              <CardTitle className="text-heading-2">Welcome!</CardTitle>
              <CardDescription>
                You have been successfully signed in.
              </CardDescription>
            </CardHeader>
            <CardContent className="text-center">
              <p className="text-body text-muted-foreground">
                Redirecting you to your dashboard...
              </p>
            </CardContent>
          </Card>
        </main>
        <Footer />
      </>
    );
  }

  // Error state
  return (
    <>
      <Header />
      <main className="min-h-screen bg-secondary/30 flex items-center justify-center py-16">
        <Card className="w-full max-w-md mx-4">
          <CardHeader className="text-center">
            <div className="w-16 h-16 bg-destructive/10 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg
                className="w-8 h-8 text-destructive"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </div>
            <CardTitle className="text-heading-2">Authentication Failed</CardTitle>
            <CardDescription>
              We couldn&apos;t complete the sign in process.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {errorMessage && (
              <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-md">
                <p className="text-sm text-destructive">{errorMessage}</p>
              </div>
            )}
            <div className="flex flex-col gap-2">
              <Button asChild className="w-full">
                <Link href="/login">Try Again</Link>
              </Button>
              <Button asChild variant="outline" className="w-full">
                <Link href="/">Go to Home</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </main>
      <Footer />
    </>
  );
}

// Loading fallback for Suspense
function CallbackFallback() {
  const t = useTranslations("auth.callback");
  return (
    <>
      <Header />
      <main className="min-h-screen bg-secondary/30 flex items-center justify-center py-16">
        <Card className="w-full max-w-md mx-4">
          <CardHeader className="text-center">
            <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg
                className="animate-spin h-8 w-8 text-primary"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
            </div>
            <CardTitle className="text-heading-2">{t("loadingTitle")}</CardTitle>
            <CardDescription>
              {t("loadingDescription")}
            </CardDescription>
          </CardHeader>
        </Card>
      </main>
      <Footer />
    </>
  );
}

// Wrap with Suspense for useSearchParams
export default function OAuthCallbackPage() {
  return (
    <Suspense fallback={<CallbackFallback />}>
      <OAuthCallbackHandler />
    </Suspense>
  );
}
