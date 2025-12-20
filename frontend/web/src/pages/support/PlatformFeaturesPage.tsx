import { ArrowLeft, Bot, CheckCircle2, Database, FileText, GitBranch, Search, Settings, Shield, Upload } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import DashboardLayout from '@/components/layout/DashboardLayout';

const PlatformFeaturesPage = () => {
  const navigate = useNavigate();

  const coreFeatures = [
    {
      icon: Shield,
      title: 'Quality Gates Management',
      description: 'Enforce framework quality gates at each lifecycle stage',
      capabilities: [
        'View all gates for your project',
        'Submit evidence for gate approval',
        'Track review status in real-time',
        'Automated gate routing'
      ]
    },
    {
      icon: Database,
      title: 'Evidence Management',
      description: 'Centralized repository for all project artifacts',
      capabilities: [
        'Upload documents and artifacts',
        'Version control for evidence',
        'Search and filter evidence',
        'AI validation and quality check'
      ]
    },
    {
      icon: Bot,
      title: 'AI Council Integration',
      description: 'Intelligent decision support and risk assessment',
      capabilities: [
        'Automated risk assessment',
        'Decision support recommendations',
        'Compliance verification',
        'Historical context analysis'
      ]
    }
  ];

  const evidenceTypes = [
    { type: 'Documents', formats: 'PDF, DOCX, XLSX, PPTX', icon: FileText, color: 'text-blue-500' },
    { type: 'Artifacts', formats: 'PNG, JPG, SVG, diagrams', icon: GitBranch, color: 'text-green-500' },
    { type: 'External Links', formats: 'GitHub, Jira, Confluence', icon: Upload, color: 'text-purple-500' }
  ];

  const gateStatuses = [
    { status: 'PASSED', icon: '🟢', description: 'Gate approved, can proceed' },
    { status: 'IN_REVIEW', icon: '🟡', description: 'Under review by approvers' },
    { status: 'PENDING', icon: '⚪', description: 'Not yet submitted' },
    { status: 'REJECTED', icon: '🔴', description: 'Failed review, needs rework' },
    { status: 'WAIVED', icon: '🔵', description: 'Approved with exceptions' }
  ];

  const aiCapabilities = [
    { area: 'Technical Risks', checks: ['Architecture complexity', 'Technology choices', 'Integration challenges'] },
    { area: 'Project Risks', checks: ['Timeline feasibility', 'Resource availability', 'Dependency issues'] },
    { area: 'Compliance Risks', checks: ['Missing evidence', 'Incomplete documentation', 'Gate readiness'] }
  ];

  const advancedFeatures = [
    {
      icon: Search,
      title: 'Advanced Search',
      description: 'Find anything across projects, evidence, and documentation',
      features: ['Full-text search', 'Filter by metadata', 'Search history', 'Quick navigation']
    },
    {
      icon: Settings,
      title: 'Project Configuration',
      description: 'Customize projects to fit your needs',
      features: ['Tier selection', 'Team management', 'Custom gates', 'Notification settings']
    },
    {
      icon: FileText,
      title: 'Reporting & Analytics',
      description: 'Track progress and generate compliance reports',
      features: ['Gate progress tracking', 'Compliance reports', 'Audit trails', 'Export capabilities']
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
              <Settings className="h-8 w-8 text-primary" />
              <h1 className="text-3xl font-bold tracking-tight">Platform Features</h1>
            </div>
            <p className="text-muted-foreground">
              Comprehensive capabilities for SDLC governance
            </p>
          </div>
          <Badge variant="outline" className="mt-8">Last Updated: Dec 20, 2025</Badge>
        </div>

        {/* Core Features */}
        <div className="space-y-4">
          <h2 className="text-2xl font-semibold">Core Features</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {coreFeatures.map((feature) => {
              const Icon = feature.icon;
              return (
                <Card key={feature.title}>
                  <CardHeader>
                    <div className="flex items-center gap-2">
                      <Icon className="h-5 w-5 text-primary" />
                      <CardTitle className="text-lg">{feature.title}</CardTitle>
                    </div>
                    <CardDescription>{feature.description}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      {feature.capabilities.map((capability, index) => (
                        <li key={index} className="flex items-start gap-2 text-sm">
                          <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                          <span>{capability}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>

        {/* Gate Operations */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Quality Gate Operations
            </CardTitle>
            <CardDescription>
              How to work with quality gates in the platform
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
                {gateStatuses.map((status) => (
                  <Card key={status.status} className="border-2">
                    <CardContent className="pt-6">
                      <div className="text-center space-y-2">
                        <div className="text-2xl">{status.icon}</div>
                        <div className="font-semibold text-sm">{status.status}</div>
                        <p className="text-xs text-muted-foreground">{status.description}</p>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              <div className="rounded-lg bg-muted p-4 space-y-2">
                <h4 className="font-semibold">Gate Workflow</h4>
                <ol className="space-y-2 text-sm list-decimal list-inside">
                  <li>View gate requirements and criteria</li>
                  <li>Submit all required evidence</li>
                  <li>Request approval when complete</li>
                  <li>Track review status in real-time</li>
                  <li>Address feedback if needed</li>
                  <li>Proceed to next stage upon approval</li>
                </ol>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Evidence Management */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5" />
              Evidence Management
            </CardTitle>
            <CardDescription>
              Centralized repository for all project artifacts
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {evidenceTypes.map((type) => {
                  const Icon = type.icon;
                  return (
                    <Card key={type.type}>
                      <CardContent className="pt-6">
                        <div className="space-y-2">
                          <Icon className={`h-8 w-8 ${type.color}`} />
                          <h3 className="font-semibold">{type.type}</h3>
                          <p className="text-sm text-muted-foreground">{type.formats}</p>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="rounded-lg border p-4">
                  <h4 className="font-semibold mb-2">Evidence Features</h4>
                  <ul className="space-y-1 text-sm">
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                      Version control for all evidence
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                      Search and filter capabilities
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                      AI validation and quality check
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                      Automated tagging by gate
                    </li>
                  </ul>
                </div>

                <div className="rounded-lg border p-4">
                  <h4 className="font-semibold mb-2">Upload Limits</h4>
                  <ul className="space-y-1 text-sm">
                    <li><span className="font-semibold">Max file size:</span> 50MB</li>
                    <li><span className="font-semibold">Supported formats:</span> PDF, DOCX, XLSX, PPTX, PNG, JPG, SVG, TXT, MD, JSON, YAML</li>
                    <li><span className="font-semibold">Storage:</span> Unlimited per project (fair use)</li>
                    <li><span className="font-semibold">Versions:</span> Full history retained</li>
                  </ul>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* AI Council */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bot className="h-5 w-5" />
              AI Council Integration
            </CardTitle>
            <CardDescription>
              Intelligent decision support powered by AI
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {aiCapabilities.map((capability) => (
                  <Card key={capability.area}>
                    <CardContent className="pt-6">
                      <h3 className="font-semibold mb-3">{capability.area}</h3>
                      <ul className="space-y-2">
                        {capability.checks.map((check, index) => (
                          <li key={index} className="flex items-start gap-2 text-sm">
                            <CheckCircle2 className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
                            <span>{check}</span>
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                ))}
              </div>

              <div className="rounded-lg bg-muted p-4">
                <h4 className="font-semibold mb-2">AI Council Benefits</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3">
                  <ul className="space-y-1 text-sm">
                    <li>• Automated quality assessment</li>
                    <li>• Risk identification and mitigation</li>
                    <li>• Best practice recommendations</li>
                  </ul>
                  <ul className="space-y-1 text-sm">
                    <li>• Compliance verification</li>
                    <li>• Historical pattern analysis</li>
                    <li>• 24/7 intelligent support</li>
                  </ul>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Advanced Features */}
        <div className="space-y-4">
          <h2 className="text-2xl font-semibold">Advanced Features</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {advancedFeatures.map((feature) => {
              const Icon = feature.icon;
              return (
                <Card key={feature.title}>
                  <CardHeader>
                    <div className="flex items-center gap-2">
                      <Icon className="h-5 w-5 text-primary" />
                      <CardTitle className="text-lg">{feature.title}</CardTitle>
                    </div>
                    <CardDescription>{feature.description}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-1">
                      {feature.features.map((f, index) => (
                        <li key={index} className="text-sm">• {f}</li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>

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
                  <div className="text-sm text-muted-foreground">Learn how to use these features</div>
                </div>
              </Button>
              <Button
                variant="outline"
                className="h-auto justify-start p-4"
                onClick={() => navigate('/support/user-roles')}
              >
                <div className="text-left">
                  <div className="font-semibold">User Roles →</div>
                  <div className="text-sm text-muted-foreground">Understand permissions and access</div>
                </div>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default PlatformFeaturesPage;
