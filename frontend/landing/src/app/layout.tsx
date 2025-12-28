/**
 * Root Layout - SDLC Orchestrator Landing Page
 *
 * @module frontend/landing/src/app/layout
 * @description Root layout with SEO metadata and i18n support
 * @sdlc SDLC 5.1.2 Universal Framework
 * @status Sprint 60 - i18n Localization
 * @approved CTO December 27, 2025
 */

import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
import { AnalyticsProvider } from "@/components/AnalyticsProvider";
import { LanguageProvider } from "@/app/providers/LanguageProvider";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});

const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

/**
 * SEO Metadata - Per approved plan v2.2 Section 8.3
 */
export const metadata: Metadata = {
  metadataBase: new URL("https://sdlc.nhatquangholding.com"),
  title: "SDLC Orchestrator - Operating System for Software 3.0",
  description: "Control plane that governs all your AI coders. Native codegen for Vietnamese SME. Quality Gates, Evidence Vault, Policy Guards.",
  keywords: ["SDLC", "AI governance", "code quality", "Vietnam SME", "software development", "quality gates", "evidence vault"],
  authors: [{ name: "NQH Technology" }],
  openGraph: {
    title: "SDLC Orchestrator - Operating System for Software 3.0",
    description: "Control plane that governs all your AI coders. Native codegen for Vietnamese SME. Quality Gates, Evidence Vault, Policy Guards.",
    url: "https://sdlc.nhatquangholding.com",
    siteName: "SDLC Orchestrator",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "SDLC Orchestrator - Operating System for Software 3.0",
      },
    ],
    locale: "vi_VN",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "SDLC Orchestrator - Operating System for Software 3.0",
    description: "Control plane that governs all your AI coders. Native codegen for Vietnamese SME.",
    images: ["/og-image.png"],
  },
  robots: {
    index: true,
    follow: true,
  },
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <LanguageProvider>
          <AnalyticsProvider>
            {children}
          </AnalyticsProvider>
        </LanguageProvider>
      </body>
    </html>
  );
}
