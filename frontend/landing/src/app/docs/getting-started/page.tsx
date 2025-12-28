/**
 * Getting Started Docs Page - SDLC Orchestrator Landing
 *
 * @module frontend/landing/src/app/docs/getting-started/page
 * @description Basic getting started guide
 * @sdlc SDLC 5.1.2 Universal Framework
 * @status Sprint 57 - Basic content
 */

import { Header, Footer } from "@/components/landing";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function GettingStartedPage() {
  return (
    <>
      <Header />
      <main className="min-h-screen bg-background">
        <div className="container mx-auto px-4 py-16 md:py-24">
          <div className="max-w-3xl mx-auto">
            <h1 className="text-display font-bold tracking-tight text-foreground mb-6">
              Getting Started
            </h1>
            <p className="text-body-lg text-muted-foreground mb-8">
              Get up and running with SDLC Orchestrator in minutes.
            </p>

            {/* Quick Start Steps */}
            <div className="space-y-8">
              <section>
                <h2 className="text-heading-2 font-semibold text-foreground mb-4">
                  1. Create an Account
                </h2>
                <p className="text-body text-muted-foreground mb-4">
                  Sign up for a free account to get started. No credit card required.
                </p>
                <Button asChild>
                  <Link href="/register">Create Free Account</Link>
                </Button>
              </section>

              <section>
                <h2 className="text-heading-2 font-semibold text-foreground mb-4">
                  2. Connect Your Repository
                </h2>
                <p className="text-body text-muted-foreground">
                  Link your GitHub repository to SDLC Orchestrator. We support public and private repositories.
                </p>
              </section>

              <section>
                <h2 className="text-heading-2 font-semibold text-foreground mb-4">
                  3. Configure Quality Gates
                </h2>
                <p className="text-body text-muted-foreground">
                  Choose from 110+ built-in policies or create your own. Gates validate every PR automatically.
                </p>
              </section>

              <section>
                <h2 className="text-heading-2 font-semibold text-foreground mb-4">
                  4. Start Shipping with Confidence
                </h2>
                <p className="text-body text-muted-foreground">
                  Every change is validated against your policies. Evidence is automatically captured in the Evidence Vault.
                </p>
              </section>
            </div>

            {/* Help Section */}
            <div className="mt-12 p-6 bg-secondary/50 rounded-lg">
              <h3 className="text-heading-3 font-semibold text-foreground mb-2">
                Need Help?
              </h3>
              <p className="text-body text-muted-foreground mb-4">
                Join our Discord community or schedule a call with our team.
              </p>
              <div className="flex gap-4">
                <Button asChild variant="outline">
                  <Link href="https://discord.gg/sdlc-orchestrator" target="_blank" rel="noopener noreferrer">
                    Join Discord
                  </Link>
                </Button>
                <Button asChild variant="outline">
                  <Link href="https://calendly.com/sdlc-orchestrator" target="_blank" rel="noopener noreferrer">
                    Schedule Call
                  </Link>
                </Button>
              </div>
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </>
  );
}
