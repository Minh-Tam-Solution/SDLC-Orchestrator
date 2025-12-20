/**
 * File: frontend/web/src/pages/support/GettingStartedPage.tsx
 * Version: 1.0.0
 * Status: ACTIVE - STAGE 04 (BUILD)
 * Date: 2025-12-20
 * Authority: Frontend Lead + CTO Approved
 * Foundation: SDLC 5.1.1 Complete Lifecycle
 *
 * Description:
 * Getting Started guide with proper UI/UX design.
 * Replaces simple markdown rendering with structured components.
 */

import { Link } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import DashboardLayout from '@/components/layout/DashboardLayout'
import { 
  ArrowLeft, 
  Rocket, 
  CheckCircle2, 
  Circle,
  Play,
  Users,
  Shield,
  TrendingUp
} from 'lucide-react'

export default function GettingStartedPage() {
  return (
    <DashboardLayout>
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <Link to="/support">
            <Button variant="outline" size="sm" className="mb-4">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Support
            </Button>
          </Link>
          <div className="flex items-center gap-3 mb-4">
            <Rocket className="h-8 w-8 text-primary" />
            <div>
              <h1 className="text-3xl font-bold">Getting Started with SDLC Orchestrator</h1>
              <p className="text-muted-foreground">Quick Start Guide</p>
            </div>
          </div>
          <Badge variant="secondary">Last Updated: December 20, 2025</Badge>
        </div>

        {/* Welcome Section */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-2xl">Welcome to SDLC Orchestrator! 🚀</CardTitle>
            <CardDescription>
              Your AI-native platform for implementing <strong>SDLC 5.1.1 Enterprise Framework</strong>
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 border rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp className="h-5 w-5 text-green-600" />
                  <h3 className="font-semibold">BFlow</h3>
                </div>
                <p className="text-sm text-muted-foreground">$43M revenue, 827:1 ROI</p>
              </div>
              <div className="p-4 border rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp className="h-5 w-5 text-blue-600" />
                  <h3 className="font-semibold">NQH-Bot</h3>
                </div>
                <p className="text-sm text-muted-foreground">₫15B+ value delivered</p>
              </div>
              <div className="p-4 border rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Play className="h-5 w-5 text-purple-600" />
                  <h3 className="font-semibold">MTEP</h3>
                </div>
                <p className="text-sm text-muted-foreground">&lt;30 minute PaaS deployment</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 5-Minute Quick Start */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>5-Minute Quick Start</CardTitle>
            <CardDescription>Get up and running in 5 simple steps</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Step 1 */}
            <div className="flex gap-4">
              <div className="flex-shrink-0">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
                  <span className="text-lg font-bold text-primary">1</span>
                </div>
              </div>
              <div className="flex-1">
                <h3 className="font-semibold mb-2">Access the Platform</h3>
                <div className="bg-muted p-3 rounded-md">
                  <code className="text-sm">Production URL: https://sdlc.nhatquangholding.com</code>
                </div>
              </div>
            </div>

            {/* Step 2 */}
            <div className="flex gap-4">
              <div className="flex-shrink-0">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
                  <span className="text-lg font-bold text-primary">2</span>
                </div>
              </div>
              <div className="flex-1">
                <h3 className="font-semibold mb-2">Log In</h3>
                <ul className="space-y-1 text-sm text-muted-foreground">
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4" />
                    Navigate to the login page
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4" />
                    Enter credentials (or use OAuth: GitHub/Google/Microsoft)
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4" />
                    Complete MFA if enabled
                  </li>
                </ul>
              </div>
            </div>

            {/* Step 3 */}
            <div className="flex gap-4">
              <div className="flex-shrink-0">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
                  <span className="text-lg font-bold text-primary">3</span>
                </div>
              </div>
              <div className="flex-1">
                <h3 className="font-semibold mb-2">Understand Your Role</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div className="p-3 border rounded-lg">
                    <Users className="h-5 w-5 mb-2 text-blue-600" />
                    <h4 className="font-medium text-sm">Developer</h4>
                    <p className="text-xs text-muted-foreground">Create projects, submit evidence, view gates</p>
                  </div>
                  <div className="p-3 border rounded-lg">
                    <Shield className="h-5 w-5 mb-2 text-green-600" />
                    <h4 className="font-medium text-sm">Reviewer</h4>
                    <p className="text-xs text-muted-foreground">Review evidence, approve gates</p>
                  </div>
                  <div className="p-3 border rounded-lg">
                    <Shield className="h-5 w-5 mb-2 text-purple-600" />
                    <h4 className="font-medium text-sm">Admin</h4>
                    <p className="text-xs text-muted-foreground">Manage users, configure system</p>
                  </div>
                  <div className="p-3 border rounded-lg">
                    <TrendingUp className="h-5 w-5 mb-2 text-orange-600" />
                    <h4 className="font-medium text-sm">Executive</h4>
                    <p className="text-xs text-muted-foreground">View dashboards, strategic oversight</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Step 4 */}
            <div className="flex gap-4">
              <div className="flex-shrink-0">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
                  <span className="text-lg font-bold text-primary">4</span>
                </div>
              </div>
              <div className="flex-1">
                <h3 className="font-semibold mb-2">Your First Project</h3>
                <ol className="space-y-2 text-sm">
                  <li className="flex gap-2">
                    <span className="font-medium text-primary">1.</span>
                    <span><strong>Navigate to Projects</strong> → Click "Create Project"</span>
                  </li>
                  <li className="flex gap-2">
                    <span className="font-medium text-primary">2.</span>
                    <div>
                      <strong>Fill Details:</strong>
                      <ul className="ml-4 mt-1 space-y-1 text-muted-foreground">
                        <li>• Project Name: "My First Project"</li>
                        <li>• Description: Brief overview</li>
                        <li>• Classification: Choose tier (LITE/STANDARD/PREMIUM/ENTERPRISE)</li>
                      </ul>
                    </div>
                  </li>
                  <li className="flex gap-2">
                    <span className="font-medium text-primary">3.</span>
                    <span><strong>Submit</strong> → Your project is created!</span>
                  </li>
                </ol>
              </div>
            </div>

            {/* Step 5 */}
            <div className="flex gap-4">
              <div className="flex-shrink-0">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
                  <span className="text-lg font-bold text-primary">5</span>
                </div>
              </div>
              <div className="flex-1">
                <h3 className="font-semibold mb-2">Navigate the 10-Stage Lifecycle</h3>
                <div className="bg-muted p-4 rounded-md space-y-2 text-sm font-mono">
                  <div className="flex justify-between">
                    <span>00 FOUNDATION</span>
                    <span className="text-muted-foreground">→ Why are we building this?</span>
                  </div>
                  <div className="flex justify-between">
                    <span>01 PLANNING</span>
                    <span className="text-muted-foreground">→ What exactly do we need?</span>
                  </div>
                  <div className="flex justify-between">
                    <span>02 DESIGN</span>
                    <span className="text-muted-foreground">→ How will we build it?</span>
                  </div>
                  <div className="flex justify-between">
                    <span>03 INTEGRATE</span>
                    <span className="text-muted-foreground">→ How does it connect?</span>
                  </div>
                  <div className="flex justify-between">
                    <span>04 BUILD</span>
                    <span className="text-muted-foreground">→ Are we building right?</span>
                  </div>
                  <div className="flex justify-between">
                    <span>05 TEST</span>
                    <span className="text-muted-foreground">→ Does it work correctly?</span>
                  </div>
                  <div className="flex justify-between">
                    <span>06 DEPLOY</span>
                    <span className="text-muted-foreground">→ Can we ship safely?</span>
                  </div>
                  <div className="flex justify-between">
                    <span>07 OPERATE</span>
                    <span className="text-muted-foreground">→ Is it running reliably?</span>
                  </div>
                  <div className="flex justify-between">
                    <span>08 COLLABORATE</span>
                    <span className="text-muted-foreground">→ Is the team effective?</span>
                  </div>
                  <div className="flex justify-between">
                    <span>09 GOVERN</span>
                    <span className="text-muted-foreground">→ Are we compliant?</span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Framework Understanding */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Understanding SDLC 5.1.1 Framework</CardTitle>
            <CardDescription>The methodology powering SDLC Orchestrator</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Quality Gates */}
            <div>
              <h3 className="font-semibold mb-3 flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-green-600" />
                Quality Gates at Every Stage
              </h3>
              <p className="text-sm text-muted-foreground mb-3">
                Each stage has specific quality gates that must be passed:
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {[
                  { gate: 'G0', name: 'Foundation', desc: 'Strategic validation' },
                  { gate: 'G1', name: 'Planning', desc: 'Requirements approval' },
                  { gate: 'G2', name: 'Design', desc: 'Architecture review' },
                  { gate: 'G3-G4', name: 'Build', desc: 'Code quality & integration' },
                  { gate: 'G5', name: 'Test', desc: 'QA validation' },
                  { gate: 'G6', name: 'Deploy', desc: 'Release readiness' },
                  { gate: 'G7-G9', name: 'Production', desc: 'Operational excellence' },
                ].map((item) => (
                  <div key={item.gate} className="p-3 border rounded-lg">
                    <Badge variant="outline" className="mb-2">{item.gate}</Badge>
                    <h4 className="font-medium text-sm">{item.name}</h4>
                    <p className="text-xs text-muted-foreground">{item.desc}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* 4-Tier Classification */}
            <div>
              <h3 className="font-semibold mb-3 flex items-center gap-2">
                <Circle className="h-5 w-5 text-blue-600" />
                4-Tier Classification
              </h3>
              <p className="text-sm text-muted-foreground mb-3">
                Projects are classified by complexity:
              </p>
              <div className="space-y-2">
                <div className="flex items-center justify-between p-3 border rounded-lg">
                  <div>
                    <Badge>LITE</Badge>
                    <p className="text-sm text-muted-foreground mt-1">Simple projects</p>
                  </div>
                  <span className="text-sm font-medium">1-2 weeks</span>
                </div>
                <div className="flex items-center justify-between p-3 border rounded-lg">
                  <div>
                    <Badge variant="secondary">STANDARD</Badge>
                    <p className="text-sm text-muted-foreground mt-1">Medium projects</p>
                  </div>
                  <span className="text-sm font-medium">1-3 months</span>
                </div>
                <div className="flex items-center justify-between p-3 border rounded-lg">
                  <div>
                    <Badge variant="default">PREMIUM</Badge>
                    <p className="text-sm text-muted-foreground mt-1">Large projects</p>
                  </div>
                  <span className="text-sm font-medium">3-6 months</span>
                </div>
                <div className="flex items-center justify-between p-3 border rounded-lg">
                  <div>
                    <Badge variant="destructive">ENTERPRISE</Badge>
                    <p className="text-sm text-muted-foreground mt-1">Mission-critical</p>
                  </div>
                  <span className="text-sm font-medium">6+ months</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Next Steps */}
        <Card>
          <CardHeader>
            <CardTitle>Next Steps</CardTitle>
            <CardDescription>Continue learning about the platform</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Link to="/support/framework-overview">
                <Button variant="outline" className="w-full justify-start h-auto p-4">
                  <div className="text-left">
                    <h4 className="font-semibold mb-1">SDLC Framework Overview</h4>
                    <p className="text-xs text-muted-foreground">Deep dive into the methodology</p>
                  </div>
                </Button>
              </Link>
              <Link to="/support/platform-features">
                <Button variant="outline" className="w-full justify-start h-auto p-4">
                  <div className="text-left">
                    <h4 className="font-semibold mb-1">Platform Features</h4>
                    <p className="text-xs text-muted-foreground">Explore all capabilities</p>
                  </div>
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}
