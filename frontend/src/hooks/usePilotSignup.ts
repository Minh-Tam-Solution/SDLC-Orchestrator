/**
 * usePilotSignup - Pilot Program Signup Hook
 *
 * @module frontend/src/hooks/usePilotSignup
 * @description Custom hook for pilot signup form state, validation, and submission
 * @sprint 171 - Market Expansion Foundation (Phase 6)
 */

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { registerPilotParticipant, type PilotParticipantData } from "@/lib/api";
import { trackEvent, ANALYTICS_EVENTS } from "@/lib/analytics";

interface FormErrors {
  name?: string;
  email?: string;
  company?: string;
  role?: string;
}

export function usePilotSignup() {
  const t = useTranslations("pilot.form");
  const router = useRouter();

  const getApiErrorFields = (error: unknown): { status?: number; detail?: string } => {
    if (typeof error !== "object" || error === null) return {};
    const record = error as Record<string, unknown>;

    const status = typeof record.status === "number" ? record.status : undefined;
    const detail = typeof record.detail === "string" ? record.detail : undefined;
    return { status, detail };
  };

  // Form state
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");

  // UI state
  const [errors, setErrors] = useState<FormErrors>({});
  const [apiError, setApiError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [formStarted, setFormStarted] = useState(false);

  const markFormStarted = () => {
    if (formStarted) return;
    setFormStarted(true);
    trackEvent(ANALYTICS_EVENTS.PILOT_FORM_START, {
      timestamp: new Date().toISOString(),
    });
  };

  /**
   * Validate form fields
   * Returns true if valid, false otherwise
   */
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    // Name validation
    if (!name || name.trim() === "") {
      newErrors.name = t("validation.nameRequired");
    } else if (name.trim().length < 2) {
      newErrors.name = t("validation.nameMin");
    } else if (name.length > 100) {
      newErrors.name = t("validation.nameTooLong");
    }

    // Email validation
    if (!email || email.trim() === "") {
      newErrors.email = t("validation.emailRequired");
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = t("validation.emailInvalid");
    }

    // Company validation
    if (!company || company.trim() === "") {
      newErrors.company = t("validation.companyRequired");
    } else if (company.length > 255) {
      newErrors.company = t("validation.companyTooLong");
    }

    // Role validation
    if (!role || role.trim() === "") {
      newErrors.role = t("validation.roleRequired");
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  /**
   * Handle form submission
   * Validates, submits to API, handles success/error states
   */
  const handleSubmit = async () => {
    // Reset states
    setApiError(null);

    // Validate form
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      // Prepare data for API
      const data: PilotParticipantData = {
        company_name: company.trim(),
        // Optional fields can be added later (domain, company_size, referral_source)
      };

      // Submit to API
      const response = await registerPilotParticipant(data);

      // Success! Track event and update UI
      trackEvent(ANALYTICS_EVENTS.PILOT_APPLICATION_SUBMITTED, {
        user_id: response.user_id,
        participant_id: response.id,
        timestamp: new Date().toISOString(),
      });

      setIsSuccess(true);
    } catch (error: unknown) {
      console.error("[usePilotSignup] Submission error:", error);
      const { status, detail } = getApiErrorFields(error);

      // Handle auth error - redirect to register with return URL
      if (status === 401 || (detail && detail.includes("Session expired"))) {
        router.push("/register?redirect=/pilot");
        return;
      }

      // Handle API errors
      if (detail) {
        setApiError(detail);
      } else {
        setApiError(t("errors.serverError"));
      }
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Reset form to initial state
   */
  const resetForm = () => {
    setName("");
    setEmail("");
    setCompany("");
    setRole("");
    setErrors({});
    setApiError(null);
    setIsSuccess(false);
    setFormStarted(false);
  };

  return {
    // Form state
    name,
    setName,
    email,
    setEmail,
    company,
    setCompany,
    role,
    setRole,

    // UI state
    errors,
    apiError,
    isLoading,
    isSuccess,

    // Actions
    markFormStarted,
    handleSubmit,
    resetForm,
    validateForm,
  };
}
