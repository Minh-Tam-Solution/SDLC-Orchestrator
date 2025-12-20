import { ArrowLeft, CheckCircle2, ChevronRight, FileText, Play } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import DashboardLayout from '@/components/layout/DashboardLayout';

const CommonTasksPage = () => {
  const navigate = useNavigate();

  const tasks = [
    {
      title: 'Create a New Project',
      time: '5 minutes',
      role: 'Developer+',
      steps: [
        'Navigate to Projects (or press P)',
        'Click "Create Project" button',
        'Fill project details (name, description, classification)',
        'Choose classification tier (LITE/STANDARD/PREMIUM/ENTERPRISE)',
        'Submit - Project created with G0 stage active'
      ],
      fields: [
        { name: 'Name', example: 'Customer Self-Service Portal', required: true },
        { name: 'Description', example: 'Enable customers to manage their accounts', required: true },
        { name: 'Classification', example: 'STANDARD (most common)', required: true },
        { name: 'Repository URL', example: 'https://github.com/org/project', required: false }
      ],
      nextTask: 'Submit Evidence for G0'
    },
    {
      title: 'Submit Evidence for a Gate',
      time: '10-15 minutes',
      role: 'Developer+',
      steps: [
        'Navigate to Project → Select gate (e.g., G0: Foundation)',
        'Review required evidence list',
        'Click "Submit Evidence" button',
        'Choose upload method (file upload or external link)',
        'Fill evidence details (title, description, type)',
        'Submit and wait for AI Council review (30-60 seconds)',
        'Repeat for all required evidence'
      ],
      evidenceFor: {
        G0: ['Business case document', 'Stakeholder analysis', 'Risk assessment'],
        G1: ['Requirements doc', 'User stories', 'Acceptance criteria'],
        G2: ['Architecture diagrams', 'API specs', 'Database schema']
      },
      nextTask: 'Request Gate Approval'
    },
    {
      title: 'Request Gate Approval',
      time: '2 minutes',
      role: 'Developer+',
      steps: [
        'Verify all required evidence is submitted',
        'Check AI Council completeness check (green checkmark)',
        'Click "Request Approval" button',
        'Add optional review notes for context',
        'Submit request - Reviewers automatically notified',
        'Track status in activity feed'
      ],
      timeline: '1-3 business days for typical approval',
      nextTask: 'Address Gate Review Feedback'
    },
    {
      title: 'Address Gate Review Feedback',
      time: 'Varies',
      role: 'Developer+',
      steps: [
        'Receive notification (email + platform)',
        'Navigate to Project → Gate → Reviews Tab',
        'Read reviewer feedback and identified issues',
        'Create action plan for each issue',
        'Fix issues and update evidence',
        'Document changes in comment',
        'Click "Resubmit for Review"'
      ],
      commonIssues: [
        'Missing artifacts',
        'Incomplete documentation',
        'Quality standards not met',
        'Compliance gaps',
        'Clarification needed'
      ],
      tip: 'Respond promptly (within 1-2 days) and over-communicate changes'
    },
    {
      title: 'View Project Dashboard',
      time: '2 minutes',
      role: 'All roles',
      steps: [
        'Projects → Select Project → Dashboard tab (or press D)',
        'Review Overview Panel (status, stage, progress)',
        'Check Gate Status panel (all gates and their status)',
        'Monitor Team Activity feed (recent actions)',
        'Review Metrics panel (evidence count, approvals)',
        'Check Upcoming milestones'
      ],
      panels: ['Overview', 'Gate Status', 'Team Activity', 'Metrics', 'Milestones']
    }
  ];

  const reviewerTasks = [
    {
      title: 'Review Gate Evidence',
      time: '15-30 minutes',
      steps: [
        'Navigate to Reviews → Pending Reviews',
        'Select gate to review',
        'Review all submitted evidence',
        'Check AI Council assessment',
        'Verify compliance with framework',
        'Make decision (Approve/Reject/Request Changes)',
        'Provide detailed feedback',
        'Submit review'
      ]
    },
    {
      title: 'Generate Compliance Report',
      time: '5 minutes',
      steps: [
        'Navigate to Reports → Compliance',
        'Select date range',
        'Choose projects to include',
        'Select report type',
        'Generate and download'
      ]
    }
  ];

  const adminTasks = [
    {
      title: 'Create New User',
      time: '3 minutes',
      steps: [
        'Admin Panel → Users → Create User',
        'Fill user details',
        'Assign role(s)',
        'Set project access',
        'Send invitation email'
      ]
    },
    {
      title: 'Manage Project Settings',
      time: '5 minutes',
      steps: [
        'Admin Panel → Projects → Select Project',
        'Update settings (tier, gates, team)',
        'Configure notifications',
        'Save changes'
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
              <Play className="h-8 w-8 text-primary" />
              <h1 className="text-3xl font-bold tracking-tight">Common Tasks</h1>
            </div>
            <p className="text-muted-foreground">
              Step-by-step how-to guides for everyday operations
            </p>
          </div>
          <Badge variant="outline" className="mt-8">Last Updated: Dec 20, 2025</Badge>
        </div>

        {/* Developer Tasks */}
        <div className="space-y-4">
          <h2 className="text-2xl font-semibold flex items-center gap-2">
            <Badge>For Developers</Badge>
          </h2>
          
          {tasks.map((task, index) => (
            <Card key={index}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <span className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary font-bold text-sm">
                        {index + 1}
                      </span>
                      {task.title}
                    </CardTitle>
                    <CardDescription className="mt-2">
                      <span className="font-semibold">Time:</span> {task.time} • <span className="font-semibold">Role:</span> {task.role}
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Steps */}
                  <div>
                    <h4 className="font-semibold mb-3">Steps:</h4>
                    <ol className="space-y-2">
                      {task.steps.map((step, stepIndex) => (
                        <li key={stepIndex} className="flex items-start gap-3">
                          <span className="flex items-center justify-center w-6 h-6 rounded-full bg-muted text-sm font-semibold mt-0.5 flex-shrink-0">
                            {stepIndex + 1}
                          </span>
                          <span className="text-sm pt-0.5">{step}</span>
                        </li>
                      ))}
                    </ol>
                  </div>

                  {/* Additional Info */}
                  {task.fields && (
                    <div className="rounded-lg bg-muted p-4">
                      <h4 className="font-semibold mb-2">Required Fields:</h4>
                      <div className="space-y-2">
                        {task.fields.map((field, idx) => (
                          <div key={idx} className="text-sm">
                            <span className="font-semibold">{field.name}:</span> {field.example}
                            {field.required && <Badge variant="secondary" className="ml-2 text-xs">Required</Badge>}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {task.evidenceFor && (
                    <div className="rounded-lg bg-muted p-4">
                      <h4 className="font-semibold mb-2">Evidence Examples:</h4>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {Object.entries(task.evidenceFor).map(([gate, items]) => (
                          <div key={gate}>
                            <Badge className="mb-2">{gate}</Badge>
                            <ul className="space-y-1">
                              {(items as string[]).map((item, idx) => (
                                <li key={idx} className="text-xs flex items-center gap-1">
                                  <CheckCircle2 className="h-3 w-3 text-green-500" />
                                  {item}
                                </li>
                              ))}
                            </ul>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {task.commonIssues && (
                    <div className="rounded-lg border p-4">
                      <h4 className="font-semibold mb-2">Common Issues:</h4>
                      <div className="flex flex-wrap gap-2">
                        {task.commonIssues.map((issue, idx) => (
                          <Badge key={idx} variant="outline">{issue}</Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {task.panels && (
                    <div className="rounded-lg border p-4">
                      <h4 className="font-semibold mb-2">Dashboard Panels:</h4>
                      <div className="flex flex-wrap gap-2">
                        {task.panels.map((panel, idx) => (
                          <Badge key={idx} variant="secondary">{panel}</Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {task.timeline && (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <FileText className="h-4 w-4" />
                      <span><span className="font-semibold">Timeline:</span> {task.timeline}</span>
                    </div>
                  )}

                  {task.tip && (
                    <div className="rounded-lg bg-blue-50 border border-blue-200 p-3">
                      <p className="text-sm text-blue-900">
                        <span className="font-semibold">💡 Tip:</span> {task.tip}
                      </p>
                    </div>
                  )}

                  {task.nextTask && (
                    <div className="flex items-center gap-2 text-sm font-semibold text-primary">
                      <ChevronRight className="h-4 w-4" />
                      Next: {task.nextTask}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Reviewer Tasks */}
        <div className="space-y-4">
          <h2 className="text-2xl font-semibold flex items-center gap-2">
            <Badge variant="secondary">For Reviewers</Badge>
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {reviewerTasks.map((task, index) => (
              <Card key={index}>
                <CardHeader>
                  <CardTitle className="text-lg">{task.title}</CardTitle>
                  <CardDescription>Time: {task.time}</CardDescription>
                </CardHeader>
                <CardContent>
                  <ol className="space-y-2">
                    {task.steps.map((step, stepIndex) => (
                      <li key={stepIndex} className="flex items-start gap-2 text-sm">
                        <span className="text-primary font-semibold">{stepIndex + 1}.</span>
                        <span>{step}</span>
                      </li>
                    ))}
                  </ol>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Admin Tasks */}
        <div className="space-y-4">
          <h2 className="text-2xl font-semibold flex items-center gap-2">
            <Badge variant="destructive">For Admins</Badge>
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {adminTasks.map((task, index) => (
              <Card key={index}>
                <CardHeader>
                  <CardTitle className="text-lg">{task.title}</CardTitle>
                  <CardDescription>Time: {task.time}</CardDescription>
                </CardHeader>
                <CardContent>
                  <ol className="space-y-2">
                    {task.steps.map((step, stepIndex) => (
                      <li key={stepIndex} className="flex items-start gap-2 text-sm">
                        <span className="text-primary font-semibold">{stepIndex + 1}.</span>
                        <span>{step}</span>
                      </li>
                    ))}
                  </ol>
                </CardContent>
              </Card>
            ))}
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
                onClick={() => navigate('/support/best-practices')}
              >
                <div className="text-left">
                  <div className="font-semibold">Best Practices →</div>
                  <div className="text-sm text-muted-foreground">Optimize your workflow</div>
                </div>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default CommonTasksPage;
