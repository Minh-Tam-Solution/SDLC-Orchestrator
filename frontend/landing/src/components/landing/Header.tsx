/**
 * Header/Navigation - SDLC Orchestrator Landing Page
 *
 * @module frontend/landing/src/components/landing/Header
 * @description Sticky header with navigation and language toggle
 * @sdlc SDLC 5.1.2 Universal Framework
 * @status Sprint 60 - i18n Localization
 */

"use client";

import { useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { LanguageToggle } from "@/components/ui/LanguageToggle";

/**
 * Header component with responsive navigation and language toggle
 */
export function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const t = useTranslations("header");

  const navLinks = [
    { label: t("features"), href: "#features" },
    { label: t("pricing"), href: "#pricing" },
    { label: t("docs"), href: "/docs/getting-started" },
  ];

  return (
    <header
      className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60"
      role="banner"
    >
      <div className="container mx-auto px-4 md:px-6">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2">
            <span className="text-heading-3 font-bold text-foreground">SDLC</span>
            <span className="text-body-sm text-muted-foreground hidden sm:inline">
              Orchestrator
            </span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-6" aria-label="Main navigation">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="text-body-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
              >
                {link.label}
              </Link>
            ))}
          </nav>

          {/* Desktop CTAs + Language Toggle */}
          <div className="hidden md:flex items-center gap-3">
            <LanguageToggle />
            <Button asChild variant="ghost" size="sm">
              <Link href="/login">{t("signIn")}</Link>
            </Button>
            <Button asChild size="sm">
              <Link href="/register">{t("getStarted")}</Link>
            </Button>
          </div>

          {/* Mobile: Language Toggle + Menu Button */}
          <div className="md:hidden flex items-center gap-2">
            <LanguageToggle />
            <button
              type="button"
              className="p-2 text-muted-foreground hover:text-foreground"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-expanded={mobileMenuOpen}
              aria-controls="mobile-menu"
              aria-label={mobileMenuOpen ? t("menu.close") : t("menu.open")}
            >
              {mobileMenuOpen ? (
                <svg
                  className="h-6 w-6"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth="1.5"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              ) : (
                <svg
                  className="h-6 w-6"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth="1.5"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5"
                  />
                </svg>
              )}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <nav
            id="mobile-menu"
            className="md:hidden py-4 border-t"
            aria-label="Mobile navigation"
          >
            <div className="flex flex-col gap-4">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="text-body font-medium text-muted-foreground hover:text-foreground transition-colors py-2"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  {link.label}
                </Link>
              ))}
              <div className="flex flex-col gap-2 pt-4 border-t">
                <Button asChild variant="outline" className="w-full">
                  <Link href="/login">{t("signIn")}</Link>
                </Button>
                <Button asChild className="w-full">
                  <Link href="/register">{t("getStarted")}</Link>
                </Button>
              </div>
            </div>
          </nav>
        )}
      </div>
    </header>
  );
}
