/**
 * Checkout Page - SDLC Orchestrator Landing
 *
 * @module frontend/landing/src/app/checkout/page
 * @description VNPay checkout initiation for Founder plan
 * @sdlc SDLC 5.1.2 Universal Framework
 * @status Sprint 60 - i18n Localization
 */

"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Header, Footer } from "@/components/landing";
import { createVNPayPayment, APIError } from "@/lib/api";
import { trackCheckoutStart, trackEvent, ANALYTICS_EVENTS } from "@/lib/analytics";
import Link from "next/link";

// Pricing per Plan v2.2 - prices only, labels come from i18n
const PLAN_PRICING = {
  founder: {
    monthlyPrice: 2500000,
    annualPrice: 25000000,
    currency: "VND",
  },
};

// Feature keys for i18n lookup
const PLAN_FEATURE_KEYS = [
  "unlimitedMembers",
  "oneProduct",
  "aiCodegen",
  "qualityGates",
  "evidenceVault",
  "policyGuards",
  "aiRequests",
  "vnSupport",
  "sla",
] as const;

function CheckoutForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const planParam = searchParams.get("plan") || "founder";
  const t = useTranslations("checkout");

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [billingPeriod, setBillingPeriod] = useState<"monthly" | "annual">("monthly");

  const pricing = PLAN_PRICING.founder;
  const price = billingPeriod === "monthly" ? pricing.monthlyPrice : pricing.annualPrice;
  const periodLabel = billingPeriod === "monthly" ? t("periodMonthly") : t("periodAnnual");

  // Track checkout start
  useEffect(() => {
    trackCheckoutStart(planParam, price, pricing.currency);
  }, [planParam, price, pricing.currency]);

  const formatPrice = (amount: number) => {
    return new Intl.NumberFormat("vi-VN", {
      style: "currency",
      currency: "VND",
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const handlePayment = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Get access token from localStorage
      const accessToken = localStorage.getItem("access_token");

      if (!accessToken) {
        // Redirect to login if not authenticated
        router.push(`/login?redirect=/checkout?plan=${planParam}`);
        return;
      }

      // Track VNPay redirect
      trackEvent(ANALYTICS_EVENTS.VNPAY_REDIRECT, {
        plan: planParam,
        amount: price,
      });

      // Create VNPay payment URL
      const response = await createVNPayPayment(accessToken, {
        plan: "founder",
        billing_period: billingPeriod,
      });

      // Redirect to VNPay
      window.location.href = response.payment_url;
    } catch (err) {
      const apiErr = err as APIError;

      if (apiErr.status === 401) {
        // Token expired or invalid
        router.push(`/login?redirect=/checkout?plan=${planParam}`);
        return;
      }

      setError(apiErr.detail || t("error.createPaymentFailed"));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <Header />
      <main className="min-h-screen bg-secondary/30 py-16">
        <div className="container mx-auto px-4 max-w-4xl">
          <div className="grid md:grid-cols-2 gap-8">
            {/* Order Summary */}
            <Card>
              <CardHeader>
                <CardTitle className="text-heading-2">{t("summary")}</CardTitle>
                <CardDescription>
                  {t("planInfo.founderName")}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Billing Period Toggle */}
                <div className="flex gap-2 p-1 bg-muted rounded-lg">
                  <button
                    onClick={() => setBillingPeriod("monthly")}
                    className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                      billingPeriod === "monthly"
                        ? "bg-primary text-primary-foreground"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    {t("monthly")}
                  </button>
                  <button
                    onClick={() => setBillingPeriod("annual")}
                    className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                      billingPeriod === "annual"
                        ? "bg-primary text-primary-foreground"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    {t("annually")}
                    <span className="ml-1 text-xs text-green-600">{t("annualDiscount")}</span>
                  </button>
                </div>

                {/* Price */}
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-bold">{formatPrice(price)}</span>
                  <span className="text-muted-foreground">{periodLabel}</span>
                </div>

                {/* Features */}
                <div className="space-y-2">
                  <h4 className="font-medium">{t("features")}</h4>
                  <ul className="space-y-2">
                    {PLAN_FEATURE_KEYS.map((featureKey) => (
                      <li key={featureKey} className="flex items-center gap-2 text-sm">
                        <svg
                          className="w-4 h-4 text-green-600 flex-shrink-0"
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
                        {t(`planInfo.features.${featureKey}`)}
                      </li>
                    ))}
                  </ul>
                </div>
              </CardContent>
            </Card>

            {/* Payment */}
            <Card>
              <CardHeader>
                <CardTitle className="text-heading-2">{t("payment")}</CardTitle>
                <CardDescription>
                  {t("securePayment")}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Error Alert */}
                {error && (
                  <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-md">
                    <p className="text-sm text-destructive">{error}</p>
                  </div>
                )}

                {/* VNPay Info */}
                <div className="p-4 bg-muted rounded-lg">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-12 h-12 bg-white rounded-lg flex items-center justify-center">
                      <span className="font-bold text-red-600">VN</span>
                      <span className="font-bold text-blue-600">PAY</span>
                    </div>
                    <div>
                      <p className="font-medium">VNPay</p>
                      <p className="text-sm text-muted-foreground">
                        {t("vnpayDescription")}
                      </p>
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {t("vnpayRedirect")}
                  </p>
                </div>

                {/* Total */}
                <div className="flex justify-between items-center py-4 border-t">
                  <span className="font-medium">{t("total")}</span>
                  <span className="text-2xl font-bold">{formatPrice(price)}</span>
                </div>

                {/* Pay Button */}
                <Button
                  onClick={handlePayment}
                  className="w-full"
                  size="lg"
                  disabled={isLoading}
                >
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
                      {t("processing.title")}
                    </>
                  ) : (
                    t("payAmount", { amount: formatPrice(price) })
                  )}
                </Button>

                {/* Terms */}
                <p className="text-xs text-center text-muted-foreground">
                  {t("termsAgree")}{" "}
                  <Link href="/terms" className="text-primary hover:underline">
                    {t("termsLink")}
                  </Link>{" "}
                  {t("and")}{" "}
                  <Link href="/privacy" className="text-primary hover:underline">
                    {t("privacyLink")}
                  </Link>
                </p>

                {/* Back to pricing */}
                <div className="text-center">
                  <Link
                    href="/#pricing"
                    className="text-sm text-muted-foreground hover:text-primary"
                  >
                    {t("backToPricing")}
                  </Link>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
      <Footer />
    </>
  );
}

function CheckoutLoading() {
  const t = useTranslations("checkout");
  return (
    <>
      <Header />
      <main className="min-h-screen bg-secondary/30 flex items-center justify-center">
        <div className="text-center">
          <svg
            className="animate-spin h-12 w-12 text-primary mx-auto mb-4"
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
          <p className="text-muted-foreground">{t("loading")}</p>
        </div>
      </main>
      <Footer />
    </>
  );
}

export default function CheckoutPage() {
  return (
    <Suspense fallback={<CheckoutLoading />}>
      <CheckoutForm />
    </Suspense>
  );
}
