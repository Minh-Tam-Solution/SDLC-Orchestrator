import { ArrowLeft, Bot, CheckCircle2, HelpCircle, Layers, Shield } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import DashboardLayout from '@/components/layout/DashboardLayout';

const FAQPage = () => {
  const navigate = useNavigate();
  const [expandedIndex, setExpandedIndex] = useState<number | null>(0);

  const categories = [
    {
      category: 'General Questions',
      icon: HelpCircle,
      questions: [
        {
          q: 'What is SDLC Orchestrator?',
          a: 'SDLC Orchestrator is an AI-native platform that implements and enforces SDLC 5.1.1 Enterprise Framework - a proven 10-stage software development lifecycle with battle-tested results: BFlow ($43M revenue, 827:1 ROI), NQH-Bot (₫15B+ value), MTEP (<30 min PaaS).'
        },
        {
          q: 'Why should I use SDLC Orchestrator?',
          a: 'Proven success with measurable ROI, quality assurance to catch issues before production, automated compliance and audit trails, AI-powered decision support, team alignment on processes, and career growth through industry best practices.'
        },
        {
          q: 'Who is it for?',
          a: 'Developers (build quality software), Reviewers (ensure standards), Project Managers (track progress), Executives (strategic oversight), and Admins (manage platform).'
        }
      ]
    },
    {
      category: 'Projects & Lifecycle',
      icon: Layers,
      questions: [
        {
          q: 'What are the 10 stages?',
          a: '00 FOUNDATION (Why?), 01 PLANNING (What?), 02 DESIGN (How?), 03 INTEGRATE (Connect), 04 BUILD (Build right), 05 TEST (Works?), 06 DEPLOY (Ship safely), 07 OPERATE (Running well), 08 COLLABORATE (Team effective), 09 GOVERN (Compliant).'
        },
        {
          q: 'What are quality gates?',
          a: 'Mandatory checkpoints that ensure quality before proceeding: G0 (Foundation Ready), G1 (Design Ready), G2 (Build Ready), G3 (Dev Checkpoint), G4 (Integration Checkpoint), G5 (Deploy Ready), G6 (Production Ready), G7 (Operational Excellence), G8/G9 (Governance Complete). You cannot skip gates.'
        },
        {
          q: 'What are the project tiers?',
          a: 'LITE (1-2 weeks, 1-3 people, essential gates, internal tools), STANDARD (1-3 months, 3-7 people, core gates, web apps), PREMIUM (3-6 months, 7-15 people, all gates, platforms), ENTERPRISE (6+ months, 15+ people, enhanced gates, mission-critical).'
        },
        {
          q: 'Can I change project tier?',
          a: 'Yes, but requires admin approval. Navigate to Project → Settings → "Request Tier Change" → Provide justification. Note: Changing tier may add/remove gates.'
        }
      ]
    },
    {
      category: 'Evidence & Approval',
      icon: CheckCircle2,
      questions: [
        {
          q: 'What is evidence?',
          a: 'Artifacts that prove you\'ve completed stage activities. Examples: G0 (business case, stakeholder analysis), G1 (requirements doc, user stories), G2 (architecture diagrams, API specs), G5 (test reports, coverage metrics), G6 (deployment checklist, runbook).'
        },
        {
          q: 'How do I submit evidence?',
          a: 'Navigate to project → go to gate → click "Submit Evidence" → upload file or provide URL → add title and description → tag with gate (auto-filled) → submit. Evidence is stored, AI Council reviews automatically, and reviewers are notified.'
        },
        {
          q: 'How long does approval take?',
          a: 'AI Council: 30-60 seconds (automatic). Human Review: 1-3 business days typically. Complex Gates: 3-5 business days. Emergency: Can be expedited. Factors: reviewer availability, evidence completeness, project tier, organization SLA.'
        },
        {
          q: 'What if my gate is rejected?',
          a: 'Read feedback to understand why → Address identified issues → Update evidence with corrections → Resubmit for review → Iterate until approved. Common reasons: incomplete evidence, missing artifacts, quality standards not met, compliance issues.'
        }
      ]
    },
    {
      category: 'AI Council',
      icon: Bot,
      questions: [
        {
          q: 'What is AI Council?',
          a: 'The intelligent decision support system that reviews evidence automatically, assesses risks, provides recommendations, learns from past projects, and flags compliance issues. Think of it as your AI advisor that knows SDLC 5.1.1 framework inside-out.'
        },
        {
          q: 'Is AI Council required?',
          a: 'No, AI Council is advisory only. It provides recommendations and flags potential issues, but final decisions are made by human reviewers. However, it\'s highly valuable for catching issues early, saving review time, and improving quality.'
        },
        {
          q: 'Can AI Council approve gates?',
          a: 'No. Only human reviewers can approve gates. AI Council = Advisory, Human Reviewer = Decision maker.'
        },
        {
          q: 'What if AI Council flags an issue?',
          a: 'Investigate the flagged issue to understand the concern, address the issue if valid, provide justification if you disagree, and resubmit for review. Human reviewers consider AI Council feedback but make final decisions.'
        }
      ]
    },
    {
      category: 'Access & Permissions',
      icon: Shield,
      questions: [
        {
          q: 'How do I get access?',
          a: 'Contact your organization\'s admin → Receive invitation email with credentials → First login: set password and complete profile → Explore the platform tour.'
        },
        {
          q: 'What can I do as Developer?',
          a: 'Create projects, submit evidence, request gate approval, view own dashboards, update own profile. Cannot: approve gates, manage users, modify system settings, access admin panel.'
        },
        {
          q: 'What can I do as Reviewer?',
          a: 'All Developer permissions PLUS: review gate evidence, approve/reject gates, view all projects (read-only), generate compliance reports, view AI recommendations. Cannot: create/delete users, modify system config, delete projects.'
        },
        {
          q: 'What can I do as Admin?',
          a: 'All Reviewer permissions PLUS: create/manage users, configure system settings, manage all projects, perform bulk operations, view audit logs. Cannot: override compliance rules without justification.'
        }
      ]
    }
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
              <HelpCircle className="h-8 w-8 text-primary" />
              <h1 className="text-3xl font-bold tracking-tight">Frequently Asked Questions</h1>
            </div>
            <p className="text-muted-foreground">
              Quick answers to common questions about SDLC Orchestrator
            </p>
          </div>
          <Badge variant="outline" className="mt-8">Last Updated: Dec 20, 2025</Badge>
        </div>

        {/* FAQ by Category */}
        {categories.map((cat, catIndex) => {
          const Icon = cat.icon;
          return (
            <Card key={catIndex}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Icon className="h-5 w-5 text-primary" />
                  {cat.category}
                </CardTitle>
                <CardDescription>
                  {cat.questions.length} questions
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {cat.questions.map((faq, faqIndex) => {
                    const globalIndex = categories.slice(0, catIndex).reduce((sum, c) => sum + c.questions.length, 0) + faqIndex;
                    const isExpanded = expandedIndex === globalIndex;
                    
                    return (
                      <div key={faqIndex} className="rounded-lg border overflow-hidden">
                        <button
                          className="w-full text-left p-4 hover:bg-muted/50 transition-colors flex items-start justify-between gap-3"
                          onClick={() => setExpandedIndex(isExpanded ? null : globalIndex)}
                        >
                          <div className="flex items-start gap-3 flex-1">
                            <HelpCircle className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
                            <div>
                              <p className="font-semibold">{faq.q}</p>
                              {isExpanded && (
                                <p className="text-sm text-muted-foreground mt-2">{faq.a}</p>
                              )}
                            </div>
                          </div>
                          <span className="text-muted-foreground">
                            {isExpanded ? '−' : '+'}
                          </span>
                        </button>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          );
        })}

        {/* Can't Find Answer */}
        <Card className="border-primary">
          <CardHeader>
            <CardTitle>Can't Find Your Answer?</CardTitle>
            <CardDescription>
              Try these resources or contact support
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Button
                variant="outline"
                className="h-auto justify-start p-4"
                onClick={() => navigate('/support/getting-started')}
              >
                <div className="text-left">
                  <div className="font-semibold">Getting Started →</div>
                  <div className="text-sm text-muted-foreground">First-time user guide</div>
                </div>
              </Button>
              <Button
                variant="outline"
                className="h-auto justify-start p-4"
                onClick={() => navigate('/support/troubleshooting')}
              >
                <div className="text-left">
                  <div className="font-semibold">Troubleshooting →</div>
                  <div className="text-sm text-muted-foreground">Fix common issues</div>
                </div>
              </Button>
              <Button
                variant="outline"
                className="h-auto justify-start p-4"
                onClick={() => navigate('/support/support-channels')}
              >
                <div className="text-left">
                  <div className="font-semibold">Contact Support →</div>
                  <div className="text-sm text-muted-foreground">Get personalized help</div>
                </div>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default FAQPage;
