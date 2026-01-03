/**
 * Reset Password Page - SDLC Orchestrator Landing
 *
 * @module frontend/landing/src/app/reset-password/page
 * @description Reset password with token from email
 * @sdlc SDLC 5.1.2 Universal Framework
 * @status Sprint 60 - Password Reset Feature
 */

"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Header, Footer } from "@/components/landing";
import { verifyResetToken, resetPassword, APIError } from "@/lib/api";
import Link from "next/link";

interface FormErrors {
  password?: string;
  confirmPassword?: string;
}

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const t = useTranslations("auth.resetPassword");

  // Form state
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  // Token verification state
  const [isVerifying, setIsVerifying] = useState(true);
  const [tokenValid, setTokenValid] = useState(false);
  const [tokenError, setTokenError] = useState<string | null>(null);
  const [userEmail, setUserEmail] = useState<string | null>(null);

  // Form submission state
  const [errors, setErrors] = useState<FormErrors>({});
  const [apiError, setApiError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  // Verify token on mount
  useEffect(() => {
    const verifyToken = async () => {
      if (!token) {
        setTokenError(t("error.noToken"));
        setIsVerifying(false);
        return;
      }

      try {
        const response = await verifyResetToken(token);
        if (response.valid) {
          setTokenValid(true);
          setUserEmail(response.email);
        } else {
          setTokenError(response.error || t("error.invalidToken"));
        }
      } catch (error) {
        const apiErr = error as APIError;
        setTokenError(apiErr.detail || t("error.verificationFailed"));
      } finally {
        setIsVerifying(false);
      }
    };

    verifyToken();
  }, [token, t]);

  // Validate form
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!password) {
      newErrors.password = t("validation.passwordRequired");
    } else if (password.length < 8) {
      newErrors.password = t("validation.passwordTooShort");
    }

    if (!confirmPassword) {
      newErrors.confirmPassword = t("validation.confirmPasswordRequired");
    } else if (password !== confirmPassword) {
      newErrors.confirmPassword = t("validation.passwordsMismatch");
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setApiError(null);

    if (!validateForm() || !token) {
      return;
    }

    setIsLoading(true);

    try {
      await resetPassword({
        token,
        new_password: password,
      });
      setIsSuccess(true);
    } catch (error) {
      const apiErr = error as APIError;
      if (apiErr.status === 400) {
        setApiError(t("error.tokenExpired"));
      } else {
        setApiError(apiErr.detail || t("error.serverError"));
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Loading state
  if (isVerifying) {
    return (
      <>
        <Header />
        <main className="min-h-screen bg-secondary/30 flex items-center justify-center py-16">
          <Card className="w-full max-w-md mx-4">
            <CardContent className="flex flex-col items-center justify-center py-12">
              <svg
                className="animate-spin h-8 w-8 text-primary mb-4"
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
              <p className="text-muted-foreground">{t("verifying")}</p>
            </CardContent>
          </Card>
        </main>
        <Footer />
      </>
    );
  }

  // Token invalid state
  if (!tokenValid) {
    return (
      <>
        <Header />
        <main className="min-h-screen bg-secondary/30 flex items-center justify-center py-16">
          <Card className="w-full max-w-md mx-4">
            <CardHeader className="text-center">
              <div className="mx-auto w-12 h-12 bg-destructive/10 rounded-full flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-destructive" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
              <CardTitle className="text-heading-2">{t("invalid.title")}</CardTitle>
              <CardDescription className="mt-2">
                {tokenError || t("invalid.description")}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Link href="/forgot-password">
                <Button className="w-full">
                  {t("requestNewLink")}
                </Button>
              </Link>
              <Link href="/login">
                <Button variant="outline" className="w-full">
                  {t("backToLogin")}
                </Button>
              </Link>
            </CardContent>
          </Card>
        </main>
        <Footer />
      </>
    );
  }

  // Success state
  if (isSuccess) {
    return (
      <>
        <Header />
        <main className="min-h-screen bg-secondary/30 flex items-center justify-center py-16">
          <Card className="w-full max-w-md mx-4">
            <CardHeader className="text-center">
              <div className="mx-auto w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <CardTitle className="text-heading-2">{t("success.title")}</CardTitle>
              <CardDescription className="mt-2">
                {t("success.description")}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Link href="/login">
                <Button className="w-full">
                  {t("success.loginNow")}
                </Button>
              </Link>
            </CardContent>
          </Card>
        </main>
        <Footer />
      </>
    );
  }

  // Reset form
  return (
    <>
      <Header />
      <main className="min-h-screen bg-secondary/30 flex items-center justify-center py-16">
        <Card className="w-full max-w-md mx-4">
          <CardHeader className="text-center">
            <CardTitle className="text-heading-2">{t("title")}</CardTitle>
            <CardDescription>
              {t("description", { email: userEmail || "" })}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* API Error Alert */}
              {apiError && (
                <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-md">
                  <p className="text-sm text-destructive">{apiError}</p>
                </div>
              )}

              {/* New Password Field */}
              <div className="space-y-2">
                <Label htmlFor="password">{t("newPassword")}</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder={t("newPasswordPlaceholder")}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={isLoading}
                  className={errors.password ? "border-destructive" : ""}
                  autoComplete="new-password"
                  autoFocus
                />
                {errors.password && (
                  <p className="text-sm text-destructive">{errors.password}</p>
                )}
              </div>

              {/* Confirm Password Field */}
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

              {/* Password Requirements */}
              <div className="text-xs text-muted-foreground">
                {t("passwordRequirements")}
              </div>

              {/* Submit Button */}
              <Button type="submit" className="w-full" disabled={isLoading}>
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
            </form>
          </CardContent>
        </Card>
      </main>
      <Footer />
    </>
  );
}

// Loading fallback
function ResetPasswordFallback() {
  const t = useTranslations("auth.resetPassword");
  return (
    <>
      <Header />
      <main className="min-h-screen bg-secondary/30 flex items-center justify-center py-16">
        <Card className="w-full max-w-md mx-4">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <svg
              className="animate-spin h-8 w-8 text-primary mb-4"
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
            <p className="text-muted-foreground">{t("verifying")}</p>
          </CardContent>
        </Card>
      </main>
      <Footer />
    </>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<ResetPasswordFallback />}>
      <ResetPasswordForm />
    </Suspense>
  );
}
