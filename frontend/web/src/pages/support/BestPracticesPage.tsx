import { ArrowLeft, CheckCircle2, TrendingUp, XCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import DashboardLayout from '@/components/layout/DashboardLayout';

const BestPracticesPage = () => {
  const navigate = useNavigate();

  const generalPractices = [
    {
      title: 'Start Right: Foundation Matters',
      bad: ['Rushed G0 approval', 'Vague business case', 'Unclear objectives', 'Missing stakeholder buy-in'],
      good: ['Invest time in G0 Foundation', 'Clear, measurable objectives', 'Strong stakeholder alignment', 'Comprehensive risk assessment'],
      why: 'BFlow\'s 827:1 ROI started with solid foundation validation',
      action: 'Spend 10-15% of project time on G0'
    },
    {
      title: 'Evidence Early, Evidence Often',
      bad: ['Wait until gate deadline', 'Submit all evidence last minute', 'No version control', 'Minimal documentation'],
      good: ['Submit evidence as soon as ready', 'Version documents incrementally', 'Get early feedback', 'Document continuously'],
      why: 'Early evidence allows early course correction',
      action: 'Submit draft evidence for feedback before formal submission'
    },
    {
      title: 'Leverage AI Council Intelligently',
      bad: ['Ignore AI Council feedback', 'Rely 100% on AI Council', 'Don\'t review recommendations', 'Skip risk flags'],
      good: ['Review all AI Council feedback', 'Use as advisory, not decision', 'Investigate flagged risks', 'Combine with human judgment'],
      why: 'AI Council caught critical architectural issue in NQH-Bot early',
      action: 'Dedicate 15 minutes to review each AI Council report'
    },
    {
      title: 'Don\'t Skip Gates',
      bad: ['Request gate waivers frequently', 'Justify skipping with "urgent deadline"', 'Minimal evidence for quick approval', 'Parallel stages without approval'],
      good: ['Complete every gate properly', 'Request waiver only if truly exceptional', 'Provide full justification if needed', 'Wait for approval before proceeding'],
      why: 'MTEP\'s <30 min deployment relies on gate discipline',
      action: 'If tempted to skip, ask "What could go wrong?"'
    }
  ];

  const stagePractices = [
    {
      stage: 'G0: Foundation',
      practices: [
        {
          title: 'Clear Business Case',
          items: ['Problem statement (quantified)', 'Proposed solution (concrete)', 'Expected ROI (measurable)', 'Strategic alignment (explicit)', 'Success metrics (SMART)']
        },
        {
          title: 'Comprehensive Stakeholder Analysis',
          items: ['Primary stakeholders (decision makers)', 'Secondary stakeholders (influencers)', 'Impact analysis (who\'s affected)', 'Buy-in status (confirmed in writing)', 'RACI matrix (clear responsibilities)']
        }
      ]
    },
    {
      stage: 'G1: Planning',
      practices: [
        {
          title: 'Detailed Requirements',
          items: ['User stories (As a...I want...So that...)', 'Acceptance criteria (Given...When...Then...)', 'Non-functional requirements (performance, security)', 'Constraints (budget, timeline, resources)']
        },
        {
          title: 'Prioritized Backlog',
          items: ['MoSCoW (Must/Should/Could/Won\'t)', 'Value vs effort matrix', 'Risk-based ordering', 'MVP identification']
        }
      ]
    },
    {
      stage: 'G2: Design',
      practices: [
        {
          title: 'Architecture First',
          items: ['System architecture diagram', 'Component interactions', 'Data flow diagrams', 'Technology choices (justified)', 'Scalability considerations']
        },
        {
          title: 'API-First Design',
          items: ['API contracts (OpenAPI/Swagger)', 'Data models (schemas)', 'Authentication/authorization', 'Error handling', 'Versioning strategy']
        }
      ]
    },
    {
      stage: 'G3-G4: Build',
      practices: [
        {
          title: 'Code Quality Standards',
          items: ['Linting (automated)', 'Code reviews (mandatory)', 'Testing (unit + integration)', 'Coverage (>80% target)', 'Documentation (inline + external)']
        },
        {
          title: 'Git Workflow',
          items: ['Feature branches', 'Descriptive commits', 'Pull requests (with review)', 'CI/CD pipeline', 'Protected main branch']
        }
      ]
    },
    {
      stage: 'G5: Test',
      practices: [
        {
          title: 'Comprehensive Testing',
          items: ['Unit tests (>80% coverage)', 'Integration tests (all APIs)', 'E2E tests (critical paths)', 'Performance tests (load, stress)', 'Security tests (OWASP)']
        },
        {
          title: 'Test Automation',
          items: ['Automated test runs', 'CI/CD integration', 'Test reports', 'Failure alerting']
        }
      ]
    },
    {
      stage: 'G6: Deploy',
      practices: [
        {
          title: 'Deployment Checklist',
          items: ['Backup plan', 'Rollback procedure', 'Monitoring setup', 'Health checks', 'Smoke tests']
        },
        {
          title: 'Blue-Green Deployment',
          items: ['Zero-downtime deployment', 'Traffic switching', 'Rollback capability', 'Monitoring during switch']
        }
      ]
    }
  ];

  const teamPractices = [
    { title: 'Daily Standups', description: 'Keep team aligned, identify blockers early' },
    { title: 'Code Reviews', description: 'Knowledge sharing, quality assurance, mentoring' },
    { title: 'Documentation', description: 'Knowledge preservation, onboarding efficiency' },
    { title: 'Retrospectives', description: 'Continuous improvement, team morale' }
  ];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/support')}
              className="mb-2 -ml-2"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Support
            </Button>
            <div className="flex items-center gap-2">
              <TrendingUp className="h-8 w-8 text-primary" />
              <h1 className="text-3xl font-bold tracking-tight">Best Practices</h1>
            </div>
            <p className="text-muted-foreground">
              Optimize your SDLC Orchestrator usage with battle-tested practices
            </p>
          </div>
          <Badge variant="outline" className="mt-8">Last Updated: Dec 20, 2025</Badge>
        </div>

        {/* Success Stories Banner */}
        <Card className="border-green-200 bg-green-50">
          <CardContent className="pt-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-2xl font-bold text-green-900">$43M</p>
                <p className="text-sm text-green-700">BFlow Revenue (827:1 ROI)</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-green-900">₫15B+</p>
                <p className="text-sm text-green-700">NQH-Bot Value (95% recovery)</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-green-900">&lt;30min</p>
                <p className="text-sm text-green-700">MTEP PaaS Deployment</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* General Best Practices */}
        <div className="space-y-4">
          <h2 className="text-2xl font-semibold">General Best Practices</h2>
          
          {generalPractices.map((practice, index) => (
            <Card key={index}>
              <CardHeader>
                <CardTitle>{practice.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="rounded-lg border border-red-200 bg-red-50 p-4">
                      <h4 className="font-semibold mb-3 flex items-center gap-2 text-red-900">
                        <XCircle className="h-4 w-4" />
                        Bad Practice
                      </h4>
                      <ul className="space-y-1">
                        {practice.bad.map((item, idx) => (
                          <li key={idx} className="flex items-start gap-2 text-sm text-red-800">
                            <span>✗</span>
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div className="rounded-lg border border-green-200 bg-green-50 p-4">
                      <h4 className="font-semibold mb-3 flex items-center gap-2 text-green-900">
                        <CheckCircle2 className="h-4 w-4" />
                        Best Practice
                      </h4>
                      <ul className="space-y-1">
                        {practice.good.map((item, idx) => (
                          <li key={idx} className="flex items-start gap-2 text-sm text-green-800">
                            <span>✓</span>
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  <div className="rounded-lg bg-muted p-4">
                    <div className="space-y-2 text-sm">
                      <p><span className="font-semibold">Why It Matters:</span> {practice.why}</p>
                      <p><span className="font-semibold">Action:</span> {practice.action}</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Stage-Specific Best Practices */}
        <div className="space-y-4">
          <h2 className="text-2xl font-semibold">Stage-Specific Best Practices</h2>
          
          {stagePractices.map((stage, index) => (
            <Card key={index}>
              <CardHeader>
                <CardTitle>{stage.stage}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {stage.practices.map((practice, practiceIndex) => (
                    <div key={practiceIndex} className="rounded-lg border p-4">
                      <h4 className="font-semibold mb-3">{practice.title}</h4>
                      <ul className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        {practice.items.map((item, itemIndex) => (
                          <li key={itemIndex} className="flex items-start gap-2 text-sm">
                            <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Team Collaboration */}
        <Card>
          <CardHeader>
            <CardTitle>Team Collaboration Best Practices</CardTitle>
            <CardDescription>
              Foster effective teamwork and communication
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {teamPractices.map((practice, index) => (
                <div key={index} className="rounded-lg border p-4">
                  <h4 className="font-semibold mb-2">{practice.title}</h4>
                  <p className="text-sm text-muted-foreground">{practice.description}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Key Takeaways */}
        <Card className="border-primary">
          <CardHeader>
            <CardTitle>Key Takeaways</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
                <span><span className="font-semibold">Quality over speed</span> - Invest in foundation, don't skip gates</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
                <span><span className="font-semibold">Evidence early</span> - Submit as you go, get early feedback</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
                <span><span className="font-semibold">AI Council is advisory</span> - Review recommendations, make informed decisions</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
                <span><span className="font-semibold">Learn from success</span> - BFlow, NQH-Bot, MTEP followed these practices</span>
              </li>
            </ul>
          </CardContent>
        </Card>

        {/* Next Steps */}
        <Card>
          <CardHeader>
            <CardTitle>Next Steps</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Button
                variant="outline"
                className="h-auto justify-start p-4"
                onClick={() => navigate('/support/common-tasks')}
              >
                <div className="text-left">
                  <div className="font-semibold">Common Tasks →</div>
                  <div className="text-sm text-muted-foreground">Apply these practices to daily work</div>
                </div>
              </Button>
              <Button
                variant="outline"
                className="h-auto justify-start p-4"
                onClick={() => navigate('/support/framework-overview')}
              >
                <div className="text-left">
                  <div className="font-semibold">Framework Overview →</div>
                  <div className="text-sm text-muted-foreground">Understand the methodology</div>
                </div>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default BestPracticesPage;
