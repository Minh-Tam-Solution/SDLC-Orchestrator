/**
 * Demo Page - SDLC Orchestrator Landing
 *
 * @module frontend/landing/src/app/demo/page
 * @description Demo video and screenshots per plan v2.2 Section 8.1
 * @sdlc SDLC 5.1.2 Universal Framework
 * @status Sprint 57 - Placeholder (video TBD)
 */

import { Button } from "@/components/ui/button";
import { Header, Footer } from "@/components/landing";
import Link from "next/link";

export default function DemoPage() {
  return (
    <>
      <Header />
      <main className="min-h-screen bg-background">
        <div className="container mx-auto px-4 py-16 md:py-24">
          <div className="max-w-3xl mx-auto text-center">
            <h1 className="text-display font-bold tracking-tight text-foreground mb-6">
              See SDLC Orchestrator in Action
            </h1>
            <p className="text-body-lg text-muted-foreground mb-8">
              Watch a 3-5 minute walkthrough of the platform.
            </p>

            {/* Video Placeholder */}
            <div className="aspect-video bg-muted rounded-lg flex items-center justify-center mb-8 border">
              <div className="text-center p-8">
                <p className="text-muted-foreground mb-4">
                  Demo video coming soon
                </p>
                <p className="text-body-sm text-muted-foreground">
                  In the meantime, start your free trial to explore the platform.
                </p>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button asChild size="lg">
                <Link href="/register">Start Free Trial</Link>
              </Button>
              <Button asChild variant="outline" size="lg">
                <Link href="https://calendly.com/sdlc-orchestrator" target="_blank" rel="noopener noreferrer">
                  Schedule a Demo Call
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </>
  );
}
