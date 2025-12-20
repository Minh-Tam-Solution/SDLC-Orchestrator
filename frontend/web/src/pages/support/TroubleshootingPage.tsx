import { AlertTriangle, ArrowLeft, CheckCircle2, RefreshCw, WifiOff, XCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import DashboardLayout from '@/components/layout/DashboardLayout';

const TroubleshootingPage = () => {
  const navigate = useNavigate();

  const commonIssues = [
    {
      icon: XCircle,
      title: "I Can't Log In",
      symptoms: 'Login fails, incorrect credentials, or error message',
      solutions: [
        {
          step: 'Check Credentials',
          actions: ['Verify username/email is correct', 'Check CAPS LOCK is off', 'Ensure password is correct', 'Try "Forgot Password" if needed']
        },
        {
          step: 'Clear Browser Cache',
          actions: ['Chrome: Ctrl+Shift+Del → Clear cache', 'Firefox: Ctrl+Shift+Del → Clear cache', 'Safari: Cmd+Option+E']
        },
        {
          step: 'Try Different Browser',
          actions: ['Test with Chrome, Firefox, or Edge', 'Disable browser extensions', 'Try incognito/private mode']
        },
        {
          step: 'Check MFA',
          actions: ['Ensure authenticator app is synced', 'Try backup codes if available', 'Contact admin to reset MFA']
        }
      ],
      severity: 'high'
    },
    {
      icon: WifiOff,
      title: 'Page Not Loading / 500 Error',
      symptoms: 'White screen, 500 Internal Server Error, or loading forever',
      solutions: [
        {
          step: 'Refresh the Page',
          actions: ['Press F5 or Ctrl+R (Cmd+R on Mac)', 'Hard refresh: Ctrl+Shift+R (Cmd+Shift+R on Mac)']
        },
        {
          step: 'Check Network Connection',
          actions: ['Verify internet connectivity', 'Check if site is accessible', 'Try ping or traceroute']
        },
        {
          step: 'Clear Browser Data',
          actions: ['Clear cache and cookies', 'Clear local storage', 'Restart browser']
        },
        {
          step: 'Contact Support',
          actions: ['If persistent, report to admin', 'Include: browser, time, error message', 'Screenshot if possible']
        }
      ],
      severity: 'high'
    },
    {
      icon: AlertTriangle,
      title: 'Upload Failing',
      symptoms: 'File upload fails, error message, or stuck at uploading',
      solutions: [
        {
          step: 'Check File Size',
          actions: ['Maximum file size: 50MB', 'Compress large files', 'Split into smaller files', 'Use external link instead']
        },
        {
          step: 'Check File Type',
          actions: ['Supported: PDF, DOCX, XLSX, PPTX, PNG, JPG, SVG, TXT, MD, JSON, YAML', 'Not supported: EXE, DMG, APP (executables)']
        },
        {
          step: 'Network Timeout',
          actions: ['Check internet stability', 'Try smaller file first', 'Upload during off-peak hours']
        },
        {
          step: 'Storage Quota',
          actions: ['Project may have reached storage limit', 'Contact admin to increase quota']
        }
      ],
      severity: 'medium'
    },
    {
      icon: CheckCircle2,
      title: 'Bulk Delete Not Working (FIXED)',
      symptoms: 'Bulk delete returns 422 error',
      solutions: [
        {
          step: 'Status',
          actions: ['✅ FIXED on December 20, 2025', 'FastAPI route ordering corrected', 'Validation error handler added']
        },
        {
          step: 'If Still Having Issues',
          actions: ['Clear browser cache (Ctrl+Shift+Del)', 'Verify backend version (commit e3215ec or later)', 'Contact support with user IDs and error message']
        }
      ],
      severity: 'low',
      fixed: true
    },
    {
      icon: RefreshCw,
      title: 'Gate Approval Stuck',
      symptoms: 'Gate shows "In Review" but no progress',
      solutions: [
        {
          step: 'Check Reviewer Assignments',
          actions: ['Verify reviewers are assigned', 'Ensure reviewers have been notified', 'Check reviewer availability']
        },
        {
          step: 'Evidence Completeness',
          actions: ['All required evidence submitted?', 'AI Council flagged any issues?', 'Missing artifacts?']
        },
        {
          step: 'Notify Reviewers',
          actions: ['Send reminder via platform', 'Contact reviewers directly', 'Check reviewer availability']
        },
        {
          step: 'Escalate',
          actions: ['Contact project lead', 'Escalate to admin if urgent', 'Consider gate waiver if justified']
        }
      ],
      severity: 'medium'
    },
    {
      icon: AlertTriangle,
      title: 'AI Council Not Responding',
      symptoms: 'AI Council review not appearing or taking too long',
      solutions: [
        {
          step: 'Wait for Processing',
          actions: ['Normal processing time: 30-60 seconds', 'Large projects: up to 5 minutes']
        },
        {
          step: 'Check Evidence Quality',
          actions: ['Evidence properly formatted?', 'Files readable (not corrupted)?', 'External links accessible?']
        },
        {
          step: 'Retry AI Review',
          actions: ['Refresh page', 'Resubmit evidence', 'Click "Request AI Review" again']
        },
        {
          step: 'Fallback to Manual Review',
          actions: ['Proceed without AI Council if needed', 'Human reviewers can still approve']
        }
      ],
      severity: 'low'
    }
  ];

  const getSeverityColor = (severity: string, fixed?: boolean) => {
    if (fixed) return 'text-green-500';
    switch (severity) {
      case 'high': return 'text-red-500';
      case 'medium': return 'text-yellow-500';
      case 'low': return 'text-blue-500';
      default: return 'text-gray-500';
    }
  };

  const getSeverityBadge = (severity: string, fixed?: boolean) => {
    if (fixed) return <Badge className="bg-green-500">FIXED</Badge>;
    switch (severity) {
      case 'high': return <Badge variant="destructive">High Priority</Badge>;
      case 'medium': return <Badge className="bg-yellow-500">Medium</Badge>;
      case 'low': return <Badge variant="secondary">Low Priority</Badge>;
      default: return null;
    }
  };

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
              <AlertTriangle className="h-8 w-8 text-primary" />
              <h1 className="text-3xl font-bold tracking-tight">Troubleshooting Guide</h1>
            </div>
            <p className="text-muted-foreground">
              Common issues and solutions for SDLC Orchestrator
            </p>
          </div>
          <Badge variant="outline" className="mt-8">Last Updated: Dec 20, 2025</Badge>
        </div>

        {/* Quick Tips */}
        <Card className="border-blue-200 bg-blue-50">
          <CardHeader>
            <CardTitle className="text-blue-900">Quick Troubleshooting Tips</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-blue-900">
              <div className="flex items-start gap-2">
                <RefreshCw className="h-5 w-5 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-semibold">Refresh First</p>
                  <p className="text-xs">Hard refresh (Ctrl+Shift+R) clears cached issues</p>
                </div>
              </div>
              <div className="flex items-start gap-2">
                <CheckCircle2 className="h-5 w-5 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-semibold">Check Browser Console</p>
                  <p className="text-xs">Press F12 → Console for error messages</p>
                </div>
              </div>
              <div className="flex items-start gap-2">
                <WifiOff className="h-5 w-5 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-semibold">Verify Connection</p>
                  <p className="text-xs">Ensure stable internet and server accessibility</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Common Issues */}
        {commonIssues.map((issue, index) => {
          const Icon = issue.icon;
          return (
            <Card key={index}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <Icon className={`h-6 w-6 ${getSeverityColor(issue.severity, issue.fixed)}`} />
                    <div>
                      <CardTitle>{issue.title}</CardTitle>
                      <CardDescription className="mt-1">
                        <span className="font-semibold">Symptoms:</span> {issue.symptoms}
                      </CardDescription>
                    </div>
                  </div>
                  {getSeverityBadge(issue.severity, issue.fixed)}
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <h4 className="font-semibold">Solutions:</h4>
                  {issue.solutions.map((solution, solIndex) => (
                    <div key={solIndex} className="rounded-lg border p-4">
                      <div className="flex items-center gap-2 mb-3">
                        <span className="flex items-center justify-center w-6 h-6 rounded-full bg-primary text-primary-foreground text-sm font-bold">
                          {solIndex + 1}
                        </span>
                        <h5 className="font-semibold">{solution.step}</h5>
                      </div>
                      <ul className="space-y-2 ml-8">
                        {solution.actions.map((action, actIndex) => (
                          <li key={actIndex} className="flex items-start gap-2 text-sm">
                            {action.startsWith('✅') ? (
                              <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                            ) : (
                              <span className="text-primary">•</span>
                            )}
                            <span>{action}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          );
        })}

        {/* General Tips */}
        <Card>
          <CardHeader>
            <CardTitle>General Troubleshooting Strategy</CardTitle>
          </CardHeader>
          <CardContent>
            <ol className="space-y-3">
              <li className="flex items-start gap-3">
                <span className="flex items-center justify-center w-6 h-6 rounded-full bg-primary/10 text-primary font-bold text-sm mt-0.5">1</span>
                <div>
                  <p className="font-semibold">Identify the Problem</p>
                  <p className="text-sm text-muted-foreground">Note exact error message, what you were doing, and when it occurred</p>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <span className="flex items-center justify-center w-6 h-6 rounded-full bg-primary/10 text-primary font-bold text-sm mt-0.5">2</span>
                <div>
                  <p className="font-semibold">Try Simple Fixes First</p>
                  <p className="text-sm text-muted-foreground">Refresh page, clear cache, try different browser</p>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <span className="flex items-center justify-center w-6 h-6 rounded-full bg-primary/10 text-primary font-bold text-sm mt-0.5">3</span>
                <div>
                  <p className="font-semibold">Check Documentation</p>
                  <p className="text-sm text-muted-foreground">Search this guide and FAQ for similar issues</p>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <span className="flex items-center justify-center w-6 h-6 rounded-full bg-primary/10 text-primary font-bold text-sm mt-0.5">4</span>
                <div>
                  <p className="font-semibold">Ask Team</p>
                  <p className="text-sm text-muted-foreground">Colleagues may have encountered same issue</p>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <span className="flex items-center justify-center w-6 h-6 rounded-full bg-primary/10 text-primary font-bold text-sm mt-0.5">5</span>
                <div>
                  <p className="font-semibold">Contact Support</p>
                  <p className="text-sm text-muted-foreground">If unresolved, contact admin with detailed information</p>
                </div>
              </li>
            </ol>
          </CardContent>
        </Card>

        {/* Contact Support */}
        <Card className="border-primary">
          <CardHeader>
            <CardTitle>Need More Help?</CardTitle>
            <CardDescription>
              If you can't resolve the issue, contact support
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <h4 className="font-semibold mb-2">When Contacting Support, Include:</h4>
                <ul className="space-y-1 text-sm">
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                    Your username and role
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                    Exact error message or symptoms
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                    Steps to reproduce the issue
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                    Browser and version (Chrome 120, Firefox 121, etc.)
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                    Screenshots (if applicable)
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                    What you've tried so far
                  </li>
                </ul>
              </div>

              <div className="rounded-lg bg-muted p-4">
                <p className="font-semibold mb-2">Admin Contact:</p>
                <p className="text-sm">
                  <span className="font-semibold">Email:</span> taidt@mtsolution.com.vn<br />
                  <span className="font-semibold">Phone:</span> +84 939 116 006
                </p>
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
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Button
                variant="outline"
                className="h-auto justify-start p-4"
                onClick={() => navigate('/support/faq')}
              >
                <div className="text-left">
                  <div className="font-semibold">FAQ →</div>
                  <div className="text-sm text-muted-foreground">Frequently asked questions</div>
                </div>
              </Button>
              <Button
                variant="outline"
                className="h-auto justify-start p-4"
                onClick={() => navigate('/support/support-channels')}
              >
                <div className="text-left">
                  <div className="font-semibold">Support Channels →</div>
                  <div className="text-sm text-muted-foreground">How to get help</div>
                </div>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default TroubleshootingPage;
