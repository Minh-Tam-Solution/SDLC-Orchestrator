/**
 * PilotSignupForm - Pilot Program Application Form
 *
 * @module frontend/src/components/pilot/PilotSignupForm
 * @description Form for applying to the pilot program with validation
 * @sprint 171 - Market Expansion Foundation (Phase 6)
 */

"use client";

import { useTranslations } from "next-intl";
import { Loader2, CheckCircle } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { usePilotSignup } from "@/hooks/usePilotSignup";

interface PilotSignupFormProps {
  onSuccess?: () => void;
}

export function PilotSignupForm({ onSuccess }: PilotSignupFormProps) {
  const t = useTranslations("pilot.form");
  const {
    name,
    setName,
    email,
    setEmail,
    company,
    setCompany,
    role,
    setRole,
    errors,
    apiError,
    isLoading,
    isSuccess,
    markFormStarted,
    handleSubmit,
  } = usePilotSignup();

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await handleSubmit();
    if (onSuccess) {
      onSuccess();
    }
  };

  // Success state - show confirmation message
  if (isSuccess) {
    return (
      <section className="container mx-auto px-4 py-16" id="pilot-signup">
        <div className="mx-auto max-w-md">
          <Card className="border-success/30 bg-success/10">
            <CardHeader>
              <div className="mb-4 flex justify-center">
                <CheckCircle className="h-16 w-16 text-success" />
              </div>
              <CardTitle className="text-center text-2xl">
                {t("success.title")}
              </CardTitle>
              <CardDescription className="text-center">
                {t("success.description")}
              </CardDescription>
            </CardHeader>
          </Card>
        </div>
      </section>
    );
  }

  return (
    <section className="container mx-auto px-4 py-16" id="pilot-signup">
      <div className="mx-auto max-w-md">
        <Card>
          <CardHeader>
            <CardTitle className="text-2xl">{t("title")}</CardTitle>
            <CardDescription>{t("subtitle")}</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={onSubmit} className="space-y-4" noValidate>
              {/* Full Name */}
              <div className="space-y-2">
                <Label htmlFor="pilot-name">{t("name")}</Label>
                <Input
                  id="pilot-name"
                  type="text"
                  placeholder={t("namePlaceholder")}
                  value={name}
                  onChange={(e) => {
                    markFormStarted();
                    setName(e.target.value);
                  }}
                  disabled={isLoading}
                  className={errors.name ? "border-destructive" : ""}
                  aria-invalid={!!errors.name}
                  aria-describedby={errors.name ? "name-error" : undefined}
                />
                {errors.name && (
                  <p id="name-error" className="text-sm text-destructive" role="alert">
                    {errors.name}
                  </p>
                )}
              </div>

              {/* Email */}
              <div className="space-y-2">
                <Label htmlFor="pilot-email">{t("email")}</Label>
                <Input
                  id="pilot-email"
                  type="email"
                  placeholder={t("emailPlaceholder")}
                  value={email}
                  onChange={(e) => {
                    markFormStarted();
                    setEmail(e.target.value);
                  }}
                  disabled={isLoading}
                  className={errors.email ? "border-destructive" : ""}
                  aria-invalid={!!errors.email}
                  aria-describedby={errors.email ? "email-error" : undefined}
                />
                {errors.email && (
                  <p id="email-error" className="text-sm text-destructive" role="alert">
                    {errors.email}
                  </p>
                )}
              </div>

              {/* Company Name */}
              <div className="space-y-2">
                <Label htmlFor="pilot-company">{t("company")}</Label>
                <Input
                  id="pilot-company"
                  type="text"
                  placeholder={t("companyPlaceholder")}
                  value={company}
                  onChange={(e) => {
                    markFormStarted();
                    setCompany(e.target.value);
                  }}
                  disabled={isLoading}
                  className={errors.company ? "border-destructive" : ""}
                  aria-invalid={!!errors.company}
                  aria-describedby={errors.company ? "company-error" : undefined}
                />
                {errors.company && (
                  <p id="company-error" className="text-sm text-destructive" role="alert">
                    {errors.company}
                  </p>
                )}
              </div>

              {/* Role */}
              <div className="space-y-2">
                <Label htmlFor="pilot-role">{t("role")}</Label>
                <Select
                  value={role}
                  onValueChange={(value) => {
                    markFormStarted();
                    setRole(value);
                  }}
                  disabled={isLoading}
                >
                  <SelectTrigger
                    id="pilot-role"
                    className={errors.role ? "border-destructive" : ""}
                    aria-invalid={!!errors.role}
                    aria-describedby={errors.role ? "role-error" : undefined}
                    aria-label={t("role")}
                  >
                    <SelectValue placeholder={t("rolePlaceholder")} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="founder">{t("roleOptions.founder")}</SelectItem>
                    <SelectItem value="cto">{t("roleOptions.cto")}</SelectItem>
                    <SelectItem value="manager">{t("roleOptions.manager")}</SelectItem>
                    <SelectItem value="developer">{t("roleOptions.developer")}</SelectItem>
                    <SelectItem value="other">{t("roleOptions.other")}</SelectItem>
                  </SelectContent>
                </Select>
                {errors.role && (
                  <p id="role-error" className="text-sm text-destructive" role="alert">
                    {errors.role}
                  </p>
                )}
              </div>

              {/* API Error Message */}
              {apiError && (
                <div
                  className="rounded-md border border-destructive/30 bg-destructive/10 p-3"
                  role="alert"
                >
                  <p className="text-sm text-destructive">
                    {apiError}
                  </p>
                </div>
              )}

              {/* Submit Button */}
              <Button
                type="submit"
                className="w-full"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    {t("submitting")}
                  </>
                ) : (
                  t("submit")
                )}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </section>
  );
}
