/**
 * Forgot Password Page - SDLC Orchestrator Landing
 *
 * @module frontend/landing/src/app/forgot-password/page
 * @description Request password reset by email
 * @sdlc SDLC 5.1.2 Universal Framework
 * @status Sprint 60 - Password Reset Feature
 */

"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Header, Footer } from "@/components/landing";
import { forgotPassword, APIError } from "@/lib/api";
import Link from "next/link";

export default function ForgotPasswordPage() {
  const t = useTranslations("auth.forgotPassword");

  // Form state
  const [email, setEmail] = useState("");
  const [emailError, setEmailError] = useState<string | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  // Validate email
  const validateEmail = (): boolean => {
    if (!email) {
      setEmailError(t("validation.emailRequired"));
      return false;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setEmailError(t("validation.emailInvalid"));
      return false;
    }
    setEmailError(null);
    return true;
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setApiError(null);

    if (!validateEmail()) {
      return;
    }

    setIsLoading(true);

    try {
      await forgotPassword({ email: email.toLowerCase().trim() });
      setIsSuccess(true);
    } catch (error) {
      const apiErr = error as APIError;
      if (apiErr.status === 429) {
        setApiError(t("error.tooManyRequests"));
      } else {
        setApiError(apiErr.detail || t("error.serverError"));
      }
    } finally {
      setIsLoading(false);
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
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground text-center">
                {t("success.checkEmail", { email })}
              </p>
              <p className="text-xs text-muted-foreground text-center">
                {t("success.expiry")}
              </p>
              <div className="pt-4">
                <Link href="/login">
                  <Button variant="outline" className="w-full">
                    {t("backToLogin")}
                  </Button>
                </Link>
              </div>
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
              {/* API Error Alert */}
              {apiError && (
                <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-md">
                  <p className="text-sm text-destructive">{apiError}</p>
                </div>
              )}

              {/* Email Field */}
              <div className="space-y-2">
                <Label htmlFor="email">{t("email")}</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder={t("emailPlaceholder")}
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={isLoading}
                  className={emailError ? "border-destructive" : ""}
                  autoComplete="email"
                  autoFocus
                />
                {emailError && (
                  <p className="text-sm text-destructive">{emailError}</p>
                )}
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

              {/* Back to Login Link */}
              <div className="text-center text-body-sm text-muted-foreground pt-2">
                <Link href="/login" className="text-primary hover:underline font-medium">
                  {t("backToLogin")}
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
