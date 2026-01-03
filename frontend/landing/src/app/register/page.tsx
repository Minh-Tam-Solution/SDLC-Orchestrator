/**
 * Register Page - SDLC Orchestrator Landing
 *
 * @module frontend/landing/src/app/register/page
 * @description Registration form with email/password and OAuth validation
 * @sdlc SDLC 5.1.2 Universal Framework
 * @status Sprint 60 - i18n Localization
 */

"use client";

import { useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Header, Footer } from "@/components/landing";
import { register, getOAuthAuthorizeUrl, APIError } from "@/lib/api";
import { trackRegistrationStart, trackRegistrationComplete, trackEvent, ANALYTICS_EVENTS } from "@/lib/analytics";
import Link from "next/link";

interface FormErrors {
  email?: string;
  password?: string;
  confirmPassword?: string;
  fullName?: string;
}

export default function RegisterPage() {
  const t = useTranslations("auth.register");

  // Form state
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fullName, setFullName] = useState("");

  // UI state
  const [errors, setErrors] = useState<FormErrors>({});
  const [apiError, setApiError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [startTime, setStartTime] = useState<number | null>(null);
  const [oauthLoading, setOauthLoading] = useState<"github" | "google" | null>(null);

  // Track registration start when user begins typing
  useEffect(() => {
    if ((email || password) && !startTime) {
      setStartTime(Date.now());
      trackRegistrationStart("email");
    }
  }, [email, password, startTime]);

  // Validate form fields
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!email) {
      newErrors.email = t("validation.emailRequired");
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = t("validation.emailInvalid");
    }

    if (!password) {
      newErrors.password = t("validation.passwordRequired");
    } else if (password.length < 8) {
      newErrors.password = t("error.weakPassword");
    } else if (password.length > 128) {
      newErrors.password = t("validation.passwordTooLong");
    }

    if (!confirmPassword) {
      newErrors.confirmPassword = t("validation.confirmPasswordRequired");
    } else if (password !== confirmPassword) {
      newErrors.confirmPassword = t("error.passwordMismatch");
    }

    if (fullName && fullName.length > 100) {
      newErrors.fullName = t("validation.nameTooLong");
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setApiError(null);

    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      await register({
        email: email.toLowerCase().trim(),
        password,
        full_name: fullName.trim() || undefined,
      });

      const timeToComplete = startTime ? Math.round((Date.now() - startTime) / 1000) : 0;
      trackRegistrationComplete("email", timeToComplete);

      setIsSuccess(true);
    } catch (error) {
      const apiErr = error as APIError;
      if (apiErr.status === 409) {
        setApiError(t("error.emailExists"));
      } else {
        setApiError(apiErr.detail || t("error.serverError"));
      }

      trackEvent(ANALYTICS_EVENTS.REGISTRATION_ERROR, {
        error_type: apiErr.detail || "unknown",
        method: "email",
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Handle OAuth signup
  // NOTE: Using localStorage instead of sessionStorage for OAuth state
  // because sessionStorage can be lost in Incognito mode when redirecting
  // to external OAuth providers (GitHub, Google) and back
  const handleOAuthSignup = async (provider: "github" | "google") => {
    setOauthLoading(provider);
    setApiError(null);

    try {
      trackRegistrationStart(provider);

      const response = await getOAuthAuthorizeUrl(provider);

      // Store OAuth state in localStorage (survives redirect in Incognito)
      localStorage.setItem("oauth_state", response.state);
      // Redirect to Dashboard root after successful registration
      localStorage.setItem("oauth_redirect", "/");
      localStorage.setItem("oauth_flow", "signup");
      localStorage.setItem("oauth_provider", provider);

      window.location.href = response.authorization_url;
    } catch (error) {
      const apiErr = error as APIError;
      const providerLabel = provider === "github" ? "GitHub" : "Google";
      setApiError(apiErr.detail || t("oauth.connectFailed", { provider: providerLabel }));
      setOauthLoading(null);

      trackEvent(ANALYTICS_EVENTS.REGISTRATION_ERROR, {
        error_type: apiErr.detail || "oauth_connection_failed",
        method: provider,
      });
    }
  };

  // Success state
  if (isSuccess) {
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
              <CardTitle className="text-heading-2">{t("success.title")}</CardTitle>
              <CardDescription>
                {t("success.subtitle")}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 text-center">
              <p className="text-body text-muted-foreground">
                {t("success.description")}
              </p>
              <Button asChild className="w-full">
                <Link href="/login">{t("success.signInButton")}</Link>
              </Button>
            </CardContent>
          </Card>
        </main>
        <Footer />
      </>
    );
  }

  return (
    <>
      <Header />
      <main className="min-h-screen bg-secondary/30 flex items-center justify-center py-16">
        <Card className="w-full max-w-md mx-4">
          <CardHeader className="text-center">
            <CardTitle className="text-heading-2">{t("title")}</CardTitle>
            <CardDescription>
              {t("description")}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {apiError && (
                <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-md">
                  <p className="text-sm text-destructive">{apiError}</p>
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="fullName">{t("name")}</Label>
                <Input
                  id="fullName"
                  type="text"
                  placeholder={t("namePlaceholder")}
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  disabled={isLoading}
                  className={errors.fullName ? "border-destructive" : ""}
                />
                {errors.fullName && (
                  <p className="text-sm text-destructive">{errors.fullName}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="email">{t("email")}</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder={t("emailPlaceholder")}
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={isLoading}
                  className={errors.email ? "border-destructive" : ""}
                  autoComplete="email"
                />
                {errors.email && (
                  <p className="text-sm text-destructive">{errors.email}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">{t("password")}</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder={t("passwordPlaceholder")}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={isLoading}
                  className={errors.password ? "border-destructive" : ""}
                  autoComplete="new-password"
                />
                {errors.password && (
                  <p className="text-sm text-destructive">{errors.password}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirmPassword">{t("confirmPassword")}</Label>
                <Input
                  id="confirmPassword"
                  type="password"
                  placeholder={t("confirmPasswordPlaceholder")}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  disabled={isLoading}
                  className={errors.confirmPassword ? "border-destructive" : ""}
                  autoComplete="new-password"
                />
                {errors.confirmPassword && (
                  <p className="text-sm text-destructive">{errors.confirmPassword}</p>
                )}
              </div>

              <Button type="submit" className="w-full" disabled={isLoading || oauthLoading !== null}>
                {isLoading ? (
                  <>
                    <svg
                      className="animate-spin -ml-1 mr-2 h-4 w-4"
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
                    {t("submitting")}
                  </>
                ) : (
                  t("submit")
                )}
              </Button>

              <div className="relative my-4">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-background px-2 text-muted-foreground">
                    {t("orContinueWith")}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => handleOAuthSignup("github")}
                  disabled={isLoading || oauthLoading !== null}
                >
                  {oauthLoading === "github" ? (
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                  ) : (
                    <svg className="w-4 h-4 mr-2" viewBox="0 0 24 24">
                      <path fill="currentColor" d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                    </svg>
                  )}
                  GitHub
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => handleOAuthSignup("google")}
                  disabled={isLoading || oauthLoading !== null}
                >
                  {oauthLoading === "google" ? (
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                  ) : (
                    <svg className="w-4 h-4 mr-2" viewBox="0 0 24 24">
                      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                    </svg>
                  )}
                  Google
                </Button>
              </div>

              <p className="text-xs text-center text-muted-foreground">
                {t("terms")}{" "}
                <Link href="/terms" className="text-primary hover:underline">
                  {t("termsLink")}
                </Link>{" "}
                {t("and")}{" "}
                <Link href="/privacy" className="text-primary hover:underline">
                  {t("privacyLink")}
                </Link>
              </p>

              <div className="text-center text-body-sm text-muted-foreground pt-2">
                {t("hasAccount")}{" "}
                <Link href="/login" className="text-primary hover:underline font-medium">
                  {t("signIn")}
                </Link>
              </div>
            </form>
          </CardContent>
        </Card>
      </main>
      <Footer />
    </>
  );
}
