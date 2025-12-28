/**
 * Footer Section - SDLC Orchestrator Landing Page
 *
 * @module frontend/landing/src/components/landing/Footer
 * @description Footer with links and company info with i18n support
 * @sdlc SDLC 5.1.2 Universal Framework
 * @status Sprint 60 - i18n Localization
 */

"use client";

import { useTranslations } from "next-intl";
import Link from "next/link";

const sectionKeys = ["product", "resources", "company", "legal"] as const;

const sectionLinks = {
  product: [
    { key: "features", href: "#features" },
    { key: "pricing", href: "#pricing" },
    { key: "demo", href: "/demo" },
  ],
  resources: [
    { key: "docs", href: "/docs/getting-started" },
    { key: "blog", href: "/blog" },
    { key: "changelog", href: "/changelog" },
  ],
  company: [
    { key: "about", href: "/about" },
    { key: "contact", href: "mailto:support@nhatquangholding.com" },
    { key: "careers", href: "/careers" },
  ],
  legal: [
    { key: "privacy", href: "/privacy" },
    { key: "terms", href: "/terms" },
    { key: "cookies", href: "/cookies" },
  ],
};

/**
 * Footer component with navigation links and company info
 */
export function Footer() {
  const t = useTranslations("footer");

  return (
    <footer
      className="bg-foreground text-background py-12 md:py-16"
      role="contentinfo"
    >
      <div className="container mx-auto px-4 md:px-6">
        {/* Footer Grid */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8 mb-12">
          {/* Brand Column */}
          <div className="col-span-2 md:col-span-1">
            <Link href="/" className="inline-block mb-4">
              <span className="text-heading-3 font-bold">SDLC</span>
              <span className="text-body-sm block text-background/70">Orchestrator</span>
            </Link>
            <p className="text-body-sm text-background/70 mb-4">
              {t("tagline")}
            </p>
          </div>

          {/* Link Sections */}
          {sectionKeys.map((sectionKey) => (
            <div key={sectionKey}>
              <h3 className="text-body font-semibold mb-4">
                {t(`${sectionKey}.title`)}
              </h3>
              <ul className="space-y-2">
                {sectionLinks[sectionKey].map((link) => (
                  <li key={link.key}>
                    <Link
                      href={link.href}
                      target={link.href.startsWith("http") ? "_blank" : undefined}
                      rel={link.href.startsWith("http") ? "noopener noreferrer" : undefined}
                      className="text-body-sm text-background/70 hover:text-background transition-colors"
                    >
                      {t(`${sectionKey}.${link.key}`)}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 border-t border-background/10">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-body-sm text-background/50">
              {t("copyright")}
            </p>

            {/* Social Links */}
            <div className="flex items-center gap-4">
              <Link
                href="https://github.com/Minh-Tam-Solution/SDLC-Orchestrator"
                target="_blank"
                rel="noopener noreferrer"
                className="text-background/50 hover:text-background transition-colors"
                aria-label="GitHub"
              >
                <svg
                  className="w-5 h-5"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path
                    fillRule="evenodd"
                    d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
                    clipRule="evenodd"
                  />
                </svg>
              </Link>
              <Link
                href="https://discord.gg/sdlc-orchestrator"
                target="_blank"
                rel="noopener noreferrer"
                className="text-background/50 hover:text-background transition-colors"
                aria-label="Discord"
              >
                <svg
                  className="w-5 h-5"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path d="M20.317 4.492c-1.53-.69-3.17-1.2-4.885-1.49a.075.075 0 0 0-.079.036c-.21.369-.444.85-.608 1.23a18.566 18.566 0 0 0-5.487 0 12.36 12.36 0 0 0-.617-1.23A.077.077 0 0 0 8.562 3c-1.714.29-3.354.8-4.885 1.491a.07.07 0 0 0-.032.027C.533 9.093-.32 13.555.099 17.961a.08.08 0 0 0 .031.055 20.03 20.03 0 0 0 5.993 2.98.078.078 0 0 0 .084-.026c.462-.62.874-1.275 1.226-1.963.021-.04.001-.088-.041-.104a13.201 13.201 0 0 1-1.872-.878.075.075 0 0 1-.008-.125c.126-.093.252-.19.372-.287a.075.075 0 0 1 .078-.01c3.927 1.764 8.18 1.764 12.061 0a.075.075 0 0 1 .079.009c.12.098.245.195.372.288a.075.075 0 0 1-.006.125c-.598.344-1.22.635-1.873.877a.075.075 0 0 0-.041.105c.36.687.772 1.341 1.225 1.962a.077.077 0 0 0 .084.028 19.963 19.963 0 0 0 6.002-2.981.076.076 0 0 0 .032-.054c.5-5.094-.838-9.52-3.549-13.442a.06.06 0 0 0-.031-.028zM8.02 15.278c-1.182 0-2.157-1.069-2.157-2.38 0-1.312.956-2.38 2.157-2.38 1.21 0 2.176 1.077 2.157 2.38 0 1.312-.956 2.38-2.157 2.38zm7.975 0c-1.183 0-2.157-1.069-2.157-2.38 0-1.312.955-2.38 2.157-2.38 1.21 0 2.176 1.077 2.157 2.38 0 1.312-.946 2.38-2.157 2.38z" />
                </svg>
              </Link>
              <Link
                href="https://linkedin.com/company/nqh-technology"
                target="_blank"
                rel="noopener noreferrer"
                className="text-background/50 hover:text-background transition-colors"
                aria-label="LinkedIn"
              >
                <svg
                  className="w-5 h-5"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 0 1-2.063-2.065 2.064 2.064 0 1 1 2.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
                </svg>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
