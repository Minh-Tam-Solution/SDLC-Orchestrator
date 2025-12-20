import { ArrowLeft, BookOpen, CheckCircle2, Layers, Shield, Target, TrendingUp } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import DashboardLayout from '@/components/layout/DashboardLayout';

const FrameworkOverviewPage = () => {
  const navigate = useNavigate();

  const successStories = [
    { name: 'BFlow', result: '$43M revenue', roi: '827:1 ROI', impact: 'Complete 10-stage implementation' },
    { name: 'NQH-Bot', result: '₫15B+ value', roi: '95% recovery', impact: 'Crisis prevention & resolution' },
    { name: 'MTEP', result: '<30 min PaaS', roi: '<50ms response', impact: 'Rapid deployment excellence' }
  ];

  const stages = [
    { num: '00', name: 'FOUNDATION', question: 'WHY?', focus: 'Strategic Discovery', gate: 'G0' },
    { num: '01', name: 'PLANNING', question: 'WHAT?', focus: 'Requirements Gathering', gate: 'G1' },
    { num: '02', name: 'DESIGN', question: 'HOW?', focus: 'System Architecture', gate: 'G2' },
    { num: '03', name: 'INTEGRATE', question: '', focus: 'API Contracts', gate: '' },
    { num: '04', name: 'BUILD', question: '', focus: 'Development Sprint', gate: 'G3/G4' },
    { num: '05', name: 'TEST', question: '', focus: 'Integration Testing', gate: 'G5' },
    { num: '06', name: 'DEPLOY', question: '', focus: 'Release Execution', gate: 'G6' },
    { num: '07', name: 'OPERATE', question: '', focus: 'Monitoring & Alerting', gate: 'G7' },
    { num: '08', name: 'COLLABORATE', question: '', focus: 'Team Communication', gate: '' },
    { num: '09', name: 'GOVERN', question: '', focus: 'Compliance Management', gate: 'G8/G9' }
  ];

  const gates = [
    { name: 'G0', title: 'Foundation Ready', type: 'Pre-Stage', description: 'Business case validated' },
    { name: 'G1', title: 'Design Ready', type: 'Pre-Stage', description: 'Requirements approved' },
    { name: 'G2', title: 'Build Ready', type: 'Pre-Stage', description: 'Architecture approved' },
    { name: 'G3', title: 'Dev Checkpoint', type: 'Mid-Stage', description: 'Code quality verified' },
    { name: 'G4', title: 'Integration Checkpoint', type: 'Mid-Stage', description: 'Integrations working' },
    { name: 'G5', title: 'Deploy Ready', type: 'Post-Stage', description: 'Testing complete' },
    { name: 'G6', title: 'Production Ready', type: 'Post-Stage', description: 'Deployment verified' },
    { name: 'G7', title: 'Operational Excellence', type: 'Post-Stage', description: 'Monitoring active' }
  ];

  const tiers = [
    { name: 'LITE', duration: '1-2 weeks', team: '1-3 people', gates: 'Essential only', example: 'Internal tool', color: 'bg-blue-500' },
    { name: 'STANDARD', duration: '1-3 months', team: '3-7 people', gates: 'Core gates', example: 'Web application', color: 'bg-green-500' },
    { name: 'PREMIUM', duration: '3-6 months', team: '7-15 people', gates: 'All gates', example: 'Platform system', color: 'bg-yellow-500' },
    { name: 'ENTERPRISE', duration: '6+ months', team: '15+ people', gates: 'Enhanced', example: 'Mission-critical', color: 'bg-red-500' }
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
              <Layers className="h-8 w-8 text-primary" />
              <h1 className="text-3xl font-bold tracking-tight">SDLC 5.1.1 Framework Overview</h1>
            </div>
            <p className="text-muted-foreground">
              Understanding the governance policy behind SDLC Orchestrator
            </p>
          </div>
          <Badge variant="outline" className="mt-8">Last Updated: Dec 20, 2025</Badge>
        </div>

        {/* Introduction */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BookOpen className="h-5 w-5" />
              What is SDLC 5.1.1?
            </CardTitle>
            <CardDescription>
              A battle-tested, AI+Human software development methodology with proven results
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="rounded-lg bg-muted p-4">
                <p className="text-center font-mono text-lg font-semibold">
                  Built BY Battle, FOR Victory
                </p>
                <div className="mt-2 space-y-1 text-center text-sm text-muted-foreground">
                  <p>Every practice = Battle-tested</p>
                  <p>Every gate = Proven checkpoint</p>
                  <p>Every stage = Real-world validated</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                {successStories.map((story) => (
                  <Card key={story.name}>
                    <CardContent className="pt-6">
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <h3 className="font-semibold">{story.name}</h3>
                          <Badge variant="secondary" className="bg-green-100 text-green-800">Success</Badge>
                        </div>
                        <div className="space-y-1 text-sm">
                          <p className="font-semibold text-primary">{story.result}</p>
                          <p className="text-muted-foreground">{story.roi}</p>
                          <p className="text-xs">{story.impact}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 10-Stage Lifecycle */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5" />
              The 10-Stage Lifecycle
            </CardTitle>
            <CardDescription>
              Complete software development journey from strategy to governance
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
                {stages.map((stage) => (
                <div
                  key={stage.num}
                  className="flex items-center gap-4 rounded-lg border p-4 hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-center justify-center w-12 h-12 rounded-full bg-primary/10 text-primary font-bold">
                    {stage.num}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold">{stage.name}</h3>
                      {stage.question && (
                        <Badge variant="outline" className="text-xs">{stage.question}</Badge>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground">{stage.focus}</p>
                  </div>
                  {stage.gate && (
                    <Badge variant="secondary" className="font-mono">{stage.gate}</Badge>
                  )}
                  <CheckCircle2 className="h-5 w-5 text-muted-foreground" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Quality Gates */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Quality Gates System
            </CardTitle>
            <CardDescription>
              Mandatory checkpoints that ensure quality at each stage
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {gates.map((gate) => (
                  <Card key={gate.name}>
                    <CardContent className="pt-6">
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <Badge className="font-mono">{gate.name}</Badge>
                          <Badge variant="outline" className="text-xs">{gate.type}</Badge>
                        </div>
                        <h3 className="font-semibold text-sm">{gate.title}</h3>
                        <p className="text-xs text-muted-foreground">{gate.description}</p>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              <div className="rounded-lg bg-muted p-4 mt-4">
                <h4 className="font-semibold mb-2">Gate Approval Process</h4>
                <div className="flex items-center gap-2 text-sm">
                  <span className="font-mono">Evidence Submission</span>
                  <span>→</span>
                  <span className="font-mono">Review</span>
                  <span>→</span>
                  <span className="font-mono">Approval/Rejection</span>
                  <span>→</span>
                  <span className="font-mono">Next Stage</span>
                </div>
                <div className="grid grid-cols-3 gap-4 mt-3 text-xs text-muted-foreground">
                  <div>
                    <p className="font-semibold">Evidence</p>
                    <p>Artifacts, Documents, Test Results</p>
                  </div>
                  <div>
                    <p className="font-semibold">Review</p>
                    <p>AI Council, Risk Check, Standards</p>
                  </div>
                  <div>
                    <p className="font-semibold">Outcome</p>
                    <p>Audit Trail, Compliance, History</p>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 4-Tier Classification */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              4-Tier Classification System
            </CardTitle>
            <CardDescription>
              Projects classified by complexity and requirements
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {tiers.map((tier) => (
                <Card key={tier.name} className="border-2">
                  <CardContent className="pt-6">
                    <div className="space-y-3">
                      <div className={`w-full h-2 rounded-full ${tier.color}`} />
                      <h3 className="font-bold text-lg">{tier.name}</h3>
                      <div className="space-y-1 text-sm">
                        <p className="text-muted-foreground">
                          <span className="font-semibold">Duration:</span> {tier.duration}
                        </p>
                        <p className="text-muted-foreground">
                          <span className="font-semibold">Team:</span> {tier.team}
                        </p>
                        <p className="text-muted-foreground">
                          <span className="font-semibold">Gates:</span> {tier.gates}
                        </p>
                        <div className="pt-2">
                          <Badge variant="outline" className="text-xs">{tier.example}</Badge>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
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
                onClick={() => navigate('/support/platform-features')}
              >
                <div className="text-left">
                  <div className="font-semibold">Platform Features →</div>
                  <div className="text-sm text-muted-foreground">Explore what the platform can do</div>
                </div>
              </Button>
              <Button
                variant="outline"
                className="h-auto justify-start p-4"
                onClick={() => navigate('/support/common-tasks')}
              >
                <div className="text-left">
                  <div className="font-semibold">Common Tasks →</div>
                  <div className="text-sm text-muted-foreground">Learn how to use the platform</div>
                </div>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default FrameworkOverviewPage;
