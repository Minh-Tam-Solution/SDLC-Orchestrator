/**
 * Payment Success Page - SDLC Orchestrator Landing
 *
 * @module frontend/landing/src/app/checkout/success/page
 * @description VNPay payment success confirmation
 * @sdlc SDLC 5.1.2 Universal Framework
 * @status Sprint 58 - Registration + VNPay
 */

"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Header, Footer } from "@/components/landing";
import { getPaymentStatus, PaymentStatus } from "@/lib/api";
import { trackPaymentSuccess } from "@/lib/analytics";
import Link from "next/link";

function SuccessContent() {
  const searchParams = useSearchParams();
  const vnpTxnRef = searchParams.get("vnp_TxnRef");
  const vnpResponseCode = searchParams.get("vnp_ResponseCode");
  const t = useTranslations("checkout");

  const [status, setStatus] = useState<"loading" | "success" | "pending" | "error">("loading");
  const [paymentInfo, setPaymentInfo] = useState<PaymentStatus | null>(null);
  const [pollCount, setPollCount] = useState(0);

  useEffect(() => {
    if (!vnpTxnRef) {
      setStatus("error");
      return;
    }

    // Quick check based on VNPay response code
    if (vnpResponseCode !== "00") {
      setStatus("error");
      return;
    }

    // Poll for payment status
    const pollStatus = async () => {
      try {
        const accessToken = localStorage.getItem("access_token");
        if (!accessToken) {
          setStatus("error");
          return;
        }

        const payment = await getPaymentStatus(accessToken, vnpTxnRef);
        setPaymentInfo(payment);

        if (payment.status === "completed") {
          setStatus("success");
          trackPaymentSuccess(payment.plan, payment.amount, vnpTxnRef);
        } else if (payment.status === "failed") {
          setStatus("error");
        } else {
          // Still pending, poll again
          if (pollCount < 15) {
            setPollCount((c) => c + 1);
            setTimeout(pollStatus, 2000);
          } else {
            setStatus("pending");
          }
        }
      } catch {
        setStatus("error");
      }
    };

    pollStatus();
  }, [vnpTxnRef, vnpResponseCode, pollCount]);

  if (status === "loading" || status === "pending") {
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
              <CardTitle className="text-heading-2">
                {status === "pending" ? t("processing.title") : t("verifying.title")}
              </CardTitle>
              <CardDescription>
                {status === "pending" ? t("processing.subtitle") : t("verifying.subtitle")}
              </CardDescription>
            </CardHeader>
            <CardContent className="text-center">
              <p className="text-sm text-muted-foreground">
                {status === "pending" ? t("processing.description") : t("verifying.description")}
              </p>
            </CardContent>
          </Card>
        </main>
        <Footer />
      </>
    );
  }

  if (status === "error") {
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
              <CardTitle className="text-heading-2">{t("error.title")}</CardTitle>
              <CardDescription>
                {t("error.subtitle")}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 text-center">
              <p className="text-body text-muted-foreground">
                {t("error.description")}
              </p>
              <div className="flex flex-col gap-2">
                <Button asChild>
                  <Link href="/checkout?plan=founder">{t("error.tryAgain")}</Link>
                </Button>
                <Button asChild variant="outline">
                  <Link href="mailto:support@sdlc-orchestrator.com">{t("error.contactSupport")}</Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        </main>
        <Footer />
      </>
    );
  }

  // Success state
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
          <CardContent className="space-y-6">
            {/* Order Details */}
            {paymentInfo && (
              <div className="p-4 bg-muted rounded-lg space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">{t("success.orderId")}</span>
                  <span className="font-mono">{paymentInfo.vnp_txn_ref}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">{t("success.plan")}</span>
                  <span className="font-medium">
                    {paymentInfo.plan === "founder" ? t("planInfo.founderName") : paymentInfo.plan}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">{t("success.amount")}</span>
                  <span className="font-medium">
                    {new Intl.NumberFormat("vi-VN", {
                      style: "currency",
                      currency: paymentInfo.currency,
                      maximumFractionDigits: 0,
                    }).format(paymentInfo.amount)}
                  </span>
                </div>
              </div>
            )}

            {/* Next Steps */}
            <div className="space-y-3">
              <h4 className="font-medium">{t("success.nextSteps")}</h4>
              <ol className="space-y-2 text-sm text-muted-foreground">
                <li className="flex items-start gap-2">
                  <span className="flex-shrink-0 w-5 h-5 bg-primary/10 text-primary rounded-full flex items-center justify-center text-xs font-medium">1</span>
                  <span>{t("success.step1")}</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="flex-shrink-0 w-5 h-5 bg-primary/10 text-primary rounded-full flex items-center justify-center text-xs font-medium">2</span>
                  <span>{t("success.step2")}</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="flex-shrink-0 w-5 h-5 bg-primary/10 text-primary rounded-full flex items-center justify-center text-xs font-medium">3</span>
                  <span>{t("success.step3")}</span>
                </li>
              </ol>
            </div>

            {/* Actions */}
            <div className="flex flex-col gap-2">
              <Button asChild className="w-full">
                <a href="https://app.sdlc.nhatquangholding.com" target="_blank" rel="noopener noreferrer">
                  {t("success.goToDashboard")}
                </a>
              </Button>
              <Button asChild variant="outline" className="w-full">
                <Link href="/docs/getting-started">{t("success.viewDocs")}</Link>
              </Button>
            </div>

            {/* Support */}
            <p className="text-xs text-center text-muted-foreground">
              {t("success.needHelp")}{" "}
              <Link href="mailto:support@sdlc-orchestrator.com" className="text-primary hover:underline">
                {t("success.contactUs")}
              </Link>
            </p>
          </CardContent>
        </Card>
      </main>
      <Footer />
    </>
  );
}

function SuccessLoading() {
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
          <p className="text-muted-foreground">{t("verifying.title")}</p>
        </div>
      </main>
      <Footer />
    </>
  );
}

export default function SuccessPage() {
  return (
    <Suspense fallback={<SuccessLoading />}>
      <SuccessContent />
    </Suspense>
  );
}
