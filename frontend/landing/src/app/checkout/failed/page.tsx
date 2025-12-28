/**
 * Payment Failed Page - SDLC Orchestrator Landing
 *
 * @module frontend/landing/src/app/checkout/failed/page
 * @description VNPay payment failure handling
 * @sdlc SDLC 5.1.2 Universal Framework
 * @status Sprint 60 - i18n Localization
 */

"use client";

import { useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Header, Footer } from "@/components/landing";
import { trackEvent, ANALYTICS_EVENTS } from "@/lib/analytics";
import Link from "next/link";

// VNPay error codes for i18n lookup
const VNPAY_ERROR_CODES = ["07", "09", "10", "11", "12", "13", "24", "51", "65", "75", "79", "99"] as const;

function FailedContent() {
  const searchParams = useSearchParams();
  const vnpResponseCode = searchParams.get("vnp_ResponseCode") || "";
  const vnpTxnRef = searchParams.get("vnp_TxnRef");
  const t = useTranslations("checkout");

  // Get error message from i18n - check if code exists, fallback to default
  const getErrorMessage = (code: string): string => {
    if (VNPAY_ERROR_CODES.includes(code as typeof VNPAY_ERROR_CODES[number])) {
      return t(`failed.errors.${code}`);
    }
    return t("failed.errors.default");
  };

  const errorMessage = getErrorMessage(vnpResponseCode);

  // Track payment failure
  useEffect(() => {
    trackEvent(ANALYTICS_EVENTS.PAYMENT_FAILED, {
      plan: "founder",
      error_code: vnpResponseCode,
    });
  }, [vnpResponseCode]);

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
            <CardTitle className="text-heading-2">{t("failed.title")}</CardTitle>
            <CardDescription>
              {errorMessage}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Error Details */}
            <div className="p-4 bg-muted rounded-lg space-y-2">
              {vnpTxnRef && (
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">{t("failed.transactionId")}</span>
                  <span className="font-mono">{vnpTxnRef}</span>
                </div>
              )}
              {vnpResponseCode && (
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">{t("failed.errorCode")}</span>
                  <span className="font-mono">{vnpResponseCode}</span>
                </div>
              )}
            </div>

            {/* Troubleshooting Tips */}
            <div className="space-y-3">
              <h4 className="font-medium">{t("failed.troubleshooting")}</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li className="flex items-start gap-2">
                  <svg className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  <span>{t("failed.tip1")}</span>
                </li>
                <li className="flex items-start gap-2">
                  <svg className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  <span>{t("failed.tip2")}</span>
                </li>
                <li className="flex items-start gap-2">
                  <svg className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  <span>{t("failed.tip3")}</span>
                </li>
                <li className="flex items-start gap-2">
                  <svg className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  <span>{t("failed.tip4")}</span>
                </li>
              </ul>
            </div>

            {/* Actions */}
            <div className="flex flex-col gap-2">
              <Button asChild className="w-full">
                <Link href="/checkout?plan=founder">{t("error.tryAgain")}</Link>
              </Button>
              <Button asChild variant="outline" className="w-full">
                <Link href="/#pricing">{t("error.choosePlan")}</Link>
              </Button>
            </div>

            {/* Support */}
            <div className="text-center space-y-2">
              <p className="text-sm text-muted-foreground">
                {t("error.stillHavingIssues")}
              </p>
              <div className="flex justify-center gap-4">
                <Link
                  href="mailto:support@sdlc-orchestrator.com"
                  className="text-sm text-primary hover:underline"
                >
                  {t("error.emailSupport")}
                </Link>
                <Link
                  href="https://discord.gg/sdlc-orchestrator"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-primary hover:underline"
                >
                  {t("error.discord")}
                </Link>
              </div>
            </div>
          </CardContent>
        </Card>
      </main>
      <Footer />
    </>
  );
}

function FailedLoading() {
  const tCommon = useTranslations("common");
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
          <p className="text-muted-foreground">{tCommon("loading")}</p>
        </div>
      </main>
      <Footer />
    </>
  );
}

export default function FailedPage() {
  return (
    <Suspense fallback={<FailedLoading />}>
      <FailedContent />
    </Suspense>
  );
}
