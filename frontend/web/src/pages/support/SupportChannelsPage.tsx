import { ArrowLeft, BookOpen, Mail, MessageSquare, Phone, Search, Video } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import DashboardLayout from '@/components/layout/DashboardLayout';

const SupportChannelsPage = () => {
  const navigate = useNavigate();

  const supportTiers = [
    { tier: 'Self-Service', speed: 'Fastest', availability: '24/7', description: 'Documentation and in-platform help' },
    { tier: 'Team Support', speed: 'Quick Help', availability: 'Business Hrs', description: 'Ask colleagues and team members' },
    { tier: 'Admin Support', speed: 'System Issues', availability: 'SLA: 4hrs', description: 'Platform administration and configuration' },
    { tier: 'Engineering Support', speed: 'Complex Problems', availability: 'SLA: 24hrs', description: 'Bugs, features, and technical issues' }
  ];

  const selfServiceResources = [
    {
      icon: BookOpen,
      title: 'User Documentation',
      items: [
        'Getting Started - First steps',
        'Framework Overview - Methodology',
        'Platform Features - Capabilities',
        'Common Tasks - How-to guides',
        'Troubleshooting - Problem solving',
        'FAQ - Frequent questions',
        'Best Practices - Optimization'
      ]
    },
    {
      icon: Search,
      title: 'In-Platform Help',
      items: [
        'Help Icons (?) - Feature explanations',
        'Tooltips - Quick tips on hover',
        'Guided Tours - First-time walkthroughs',
        'Search (Ctrl+K) - Find anything'
      ]
    },
    {
      icon: Video,
      title: 'Video Tutorials',
      status: 'Coming Soon',
      items: [
        'Platform Overview (5 min)',
        'Creating Your First Project (10 min)',
        'Submitting Evidence (8 min)',
        'Gate Approval Process (12 min)',
        'Admin Panel Tour (15 min)'
      ]
    }
  ];

  const adminContacts = [
    { priority: 'P1', level: 'Critical', examples: 'Production down, security issue', response: '1 hour', resolution: '4 hours', color: 'bg-red-500' },
    { priority: 'P2', level: 'High', examples: 'Major feature broken, multiple users affected', response: '2 hours', resolution: '8 hours', color: 'bg-orange-500' },
    { priority: 'P3', level: 'Medium', examples: 'Single user affected, workaround available', response: '4 hours', resolution: '1-2 business days', color: 'bg-yellow-500' },
    { priority: 'P4', level: 'Low', examples: 'Feature request, enhancement, cosmetic', response: '1 business day', resolution: 'As scheduled', color: 'bg-blue-500' }
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
              <MessageSquare className="h-8 w-8 text-primary" />
              <h1 className="text-3xl font-bold tracking-tight">Support Channels</h1>
            </div>
            <p className="text-muted-foreground">
              Getting help with SDLC Orchestrator
            </p>
          </div>
          <Badge variant="outline" className="mt-8">Last Updated: Dec 20, 2025</Badge>
        </div>

        {/* Support Philosophy */}
        <Card className="border-primary">
          <CardHeader>
            <CardTitle>Support Philosophy</CardTitle>
            <CardDescription>
              We're committed to helping you succeed with SDLC Orchestrator
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {supportTiers.map((tier, index) => (
                <div key={index} className="text-center">
                  <div className="rounded-lg bg-muted p-4 space-y-2">
                    <p className="font-bold text-lg">{tier.tier}</p>
                    <Badge variant="outline">{tier.speed}</Badge>
                    <p className="text-xs text-muted-foreground">{tier.availability}</p>
                    <p className="text-xs pt-2">{tier.description}</p>
                  </div>
                  {index < 3 && (
                    <div className="hidden md:block text-2xl text-muted-foreground absolute -right-4 top-1/2 -translate-y-1/2">
                      →
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Self-Service Support */}
        <div className="space-y-4">
          <h2 className="text-2xl font-semibold">Self-Service Support (24/7)</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {selfServiceResources.map((resource, index) => {
              const Icon = resource.icon;
              return (
                <Card key={index}>
                  <CardHeader>
                    <div className="flex items-center gap-2">
                      <Icon className="h-5 w-5 text-primary" />
                      <CardTitle className="text-lg">{resource.title}</CardTitle>
                    </div>
                    {resource.status && (
                      <Badge variant="secondary" className="mt-2">{resource.status}</Badge>
                    )}
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      {resource.items.map((item, idx) => (
                        <li key={idx} className="text-sm flex items-start gap-2">
                          <span className="text-primary">•</span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>

        {/* Team Support */}
        <Card>
          <CardHeader>
            <CardTitle>Team Support (Business Hours)</CardTitle>
            <CardDescription>
              Ask your team first for project-specific questions
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <h4 className="font-semibold mb-3">When to Ask Team:</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-green-500">✓</span>
                    <span>Project-specific questions</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-green-500">✓</span>
                    <span>Clarification on requirements</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-green-500">✓</span>
                    <span>Feedback on evidence</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-green-500">✓</span>
                    <span>Best practices for your domain</span>
                  </div>
                </div>
              </div>

              <div className="rounded-lg bg-muted p-4">
                <h4 className="font-semibold mb-2">Team Members to Contact:</h4>
                <ul className="space-y-1 text-sm">
                  <li><span className="font-semibold">Project Lead</span> - Project-specific questions</li>
                  <li><span className="font-semibold">Senior Developers</span> - Technical guidance</li>
                  <li><span className="font-semibold">Peer Developers</span> - Day-to-day help</li>
                  <li><span className="font-semibold">Reviewers</span> - Gate approval questions</li>
                </ul>
                <p className="text-xs text-muted-foreground mt-3">Response Time: Usually within hours (same day)</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Admin Support */}
        <Card>
          <CardHeader>
            <CardTitle>Admin Support (Business Hours)</CardTitle>
            <CardDescription>
              For system issues, account management, and compliance
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <h4 className="font-semibold mb-3">When to Contact Admin:</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-green-500">✓</span>
                    <span>Cannot log in (after troubleshooting)</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-green-500">✓</span>
                    <span>Permission denied (should have access)</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-green-500">✓</span>
                    <span>User account needs creation/modification</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-green-500">✓</span>
                    <span>Bulk operations needed</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-green-500">✓</span>
                    <span>Compliance report generation</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-green-500">✓</span>
                    <span>Audit log access</span>
                  </div>
                </div>
              </div>

              <div className="rounded-lg border-2 border-primary p-4">
                <h4 className="font-semibold mb-3 flex items-center gap-2">
                  <Mail className="h-5 w-5 text-primary" />
                  Admin Contact Information
                </h4>
                <div className="space-y-2">
                  <div className="flex items-center gap-3">
                    <Mail className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <p className="text-sm font-semibold">Email</p>
                      <p className="text-sm">taidt@mtsolution.com.vn</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Phone className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <p className="text-sm font-semibold">Phone</p>
                      <p className="text-sm">+84 939 116 006</p>
                    </div>
                  </div>
                  <div className="mt-3 pt-3 border-t">
                    <p className="text-xs text-muted-foreground">
                      <span className="font-semibold">Email Subject:</span> [SDLC] Your Issue Summary
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      <span className="font-semibold">Include:</span> Username, issue description, steps to reproduce, expected vs actual behavior, screenshots
                    </p>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="font-semibold mb-3">Admin Response SLA:</h4>
                <div className="space-y-2">
                  {adminContacts.map((contact, index) => (
                    <div key={index} className="rounded-lg border p-3">
                      <div className="flex items-center gap-3 mb-2">
                        <Badge className={contact.color}>{contact.priority}</Badge>
                        <span className="font-semibold">{contact.level}</span>
                      </div>
                      <p className="text-sm text-muted-foreground mb-2">{contact.examples}</p>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div>
                          <span className="font-semibold">Response:</span> {contact.response}
                        </div>
                        <div>
                          <span className="font-semibold">Resolution:</span> {contact.resolution}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Engineering Support */}
        <Card>
          <CardHeader>
            <CardTitle>Engineering Support (For Complex Issues)</CardTitle>
            <CardDescription>
              Platform bugs, feature requests, and security concerns
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <h4 className="font-semibold mb-3">When to Escalate to Engineering:</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-green-500">✓</span>
                    <span>Feature not working as documented</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-green-500">✓</span>
                    <span>Error messages without clear resolution</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-green-500">✓</span>
                    <span>Data inconsistency issues</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-green-500">✓</span>
                    <span>Performance problems</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-green-500">✓</span>
                    <span>Integration failures</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-green-500">✓</span>
                    <span>Security concerns</span>
                  </div>
                </div>
              </div>

              <div className="rounded-lg bg-muted p-4">
                <h4 className="font-semibold mb-2">How to Report:</h4>
                <ol className="space-y-2 text-sm list-decimal list-inside">
                  <li>Contact admin first (they will escalate if needed)</li>
                  <li>Provide detailed reproduction steps</li>
                  <li>Include error messages and screenshots</li>
                  <li>Specify browser/version and environment</li>
                  <li>Describe expected vs actual behavior</li>
                </ol>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Quick Reference */}
        <Card className="border-primary">
          <CardHeader>
            <CardTitle>Quick Reference: Who to Contact</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="rounded-lg border p-4">
                <h4 className="font-semibold mb-2">Start Here:</h4>
                <ul className="space-y-1 text-sm">
                  <li>1. <span className="font-semibold">Self-Service</span> - Documentation, FAQ, Troubleshooting</li>
                  <li>2. <span className="font-semibold">Team</span> - Project questions, quick help</li>
                  <li>3. <span className="font-semibold">Admin</span> - System issues, permissions</li>
                  <li>4. <span className="font-semibold">Engineering</span> - Bugs, complex problems</li>
                </ul>
              </div>

              <div className="rounded-lg border p-4">
                <h4 className="font-semibold mb-2">Emergency Contact:</h4>
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <Phone className="h-4 w-4 text-red-500" />
                    <span className="text-sm font-semibold">+84 939 116 006</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Mail className="h-4 w-4 text-red-500" />
                    <span className="text-sm">taidt@mtsolution.com.vn</span>
                  </div>
                  <p className="text-xs text-muted-foreground pt-2">
                    For P1 (Critical) issues: Production down, security breach
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Next Steps */}
        <Card>
          <CardHeader>
            <CardTitle>Next Steps</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Button
                variant="outline"
                className="h-auto justify-start p-4"
                onClick={() => navigate('/support/troubleshooting')}
              >
                <div className="text-left">
                  <div className="font-semibold">Troubleshooting →</div>
                  <div className="text-sm text-muted-foreground">Try self-service first</div>
                </div>
              </Button>
              <Button
                variant="outline"
                className="h-auto justify-start p-4"
                onClick={() => navigate('/support/faq')}
              >
                <div className="text-left">
                  <div className="font-semibold">FAQ →</div>
                  <div className="text-sm text-muted-foreground">Quick answers</div>
                </div>
              </Button>
              <Button
                variant="outline"
                className="h-auto justify-start p-4"
                onClick={() => navigate('/support')}
              >
                <div className="text-left">
                  <div className="font-semibold">Support Hub →</div>
                  <div className="text-sm text-muted-foreground">All resources</div>
                </div>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default SupportChannelsPage;
