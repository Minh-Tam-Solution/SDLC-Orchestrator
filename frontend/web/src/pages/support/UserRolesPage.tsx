import { ArrowLeft, CheckCircle2, Code, Settings, Shield, TrendingUp, Users, XCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import DashboardLayout from '@/components/layout/DashboardLayout';

const UserRolesPage = () => {
  const navigate = useNavigate();

  const roles = [
    {
      name: 'Developer',
      icon: Code,
      color: 'text-blue-500',
      purpose: 'Build and submit work through SDLC stages',
      users: ['Software developers', 'QA engineers', 'DevOps engineers', 'Junior team members', 'Contractors'],
      canDo: [
        'Create new projects',
        'Submit evidence and artifacts',
        'Request gate approval',
        'View own project dashboards',
        'Update own profile'
      ],
      cannotDo: [
        'Approve/reject gates',
        'Create/delete users',
        'Modify system settings',
        'Access admin panel',
        'View all projects'
      ]
    },
    {
      name: 'Reviewer',
      icon: Shield,
      color: 'text-green-500',
      purpose: 'Review evidence and approve quality gates',
      users: ['Senior developers', 'Tech leads', 'Architects', 'QA leads', 'Security specialists'],
      canDo: [
        'All Developer permissions',
        'Review gate evidence',
        'Approve/reject gates',
        'View all projects (read-only)',
        'Generate compliance reports'
      ],
      cannotDo: [
        'Create/delete users',
        'Modify system configuration',
        'Delete projects',
        'Override framework rules',
        'Bulk operations (admin only)'
      ]
    },
    {
      name: 'Admin',
      icon: Settings,
      color: 'text-purple-500',
      purpose: 'Manage platform, users, and system configuration',
      users: ['System administrators', 'Platform managers', 'IT support'],
      canDo: [
        'All Reviewer permissions',
        'Create/manage users',
        'Configure system settings',
        'Manage projects (all)',
        'Bulk operations',
        'View audit logs'
      ],
      cannotDo: [
        'Override compliance rules (without justification)',
        'Delete framework stages',
        'Modify audit trails'
      ]
    },
    {
      name: 'Executive',
      icon: TrendingUp,
      color: 'text-red-500',
      purpose: 'Strategic oversight and high-level reporting',
      users: ['C-level executives', 'VPs', 'Directors', 'Board members'],
      canDo: [
        'View all projects (read-only)',
        'Access executive dashboards',
        'Generate strategic reports',
        'View compliance metrics',
        'Export data for analysis'
      ],
      cannotDo: [
        'Create/modify projects',
        'Approve gates',
        'Manage users',
        'Access admin panel',
        'Modify any data'
      ]
    }
  ];

  const permissionMatrix = [
    { action: 'Create Projects', developer: true, reviewer: true, admin: true, executive: false },
    { action: 'Submit Evidence', developer: true, reviewer: true, admin: true, executive: false },
    { action: 'Approve Gates', developer: false, reviewer: true, admin: true, executive: false },
    { action: 'View All Projects', developer: false, reviewer: true, admin: true, executive: true },
    { action: 'Manage Users', developer: false, reviewer: false, admin: true, executive: false },
    { action: 'System Config', developer: false, reviewer: false, admin: true, executive: false },
    { action: 'Executive Reports', developer: false, reviewer: false, admin: true, executive: true }
  ];

  const bestPractices = [
    {
      title: 'Principle of Least Privilege',
      description: 'Users should have minimum permissions needed for their role',
      examples: ['Developer for coding tasks', 'Reviewer for approval duties', 'Admin only when necessary']
    },
    {
      title: 'Regular Access Review',
      description: 'Periodically review and update user permissions',
      examples: ['Quarterly access audits', 'Remove inactive users', 'Update roles when responsibilities change']
    },
    {
      title: 'Role Separation',
      description: 'Avoid conflicts of interest in critical operations',
      examples: ['Developers cannot approve own gates', 'Reviewers rotate assignments', 'Admins log all changes']
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
              <Users className="h-8 w-8 text-primary" />
              <h1 className="text-3xl font-bold tracking-tight">User Roles & Permissions</h1>
            </div>
            <p className="text-muted-foreground">
              Access control and role management in SDLC Orchestrator
            </p>
          </div>
          <Badge variant="outline" className="mt-8">Last Updated: Dec 20, 2025</Badge>
        </div>

        {/* Introduction */}
        <Card>
          <CardHeader>
            <CardTitle>Role-Based Access Control (RBAC)</CardTitle>
            <CardDescription>
              SDLC Orchestrator uses RBAC to manage what users can see and do
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-4 rounded-lg bg-muted">
                <CheckCircle2 className="h-8 w-8 text-green-500 mx-auto mb-2" />
                <p className="font-semibold">Security</p>
                <p className="text-xs text-muted-foreground">Only authorized actions</p>
              </div>
              <div className="text-center p-4 rounded-lg bg-muted">
                <CheckCircle2 className="h-8 w-8 text-green-500 mx-auto mb-2" />
                <p className="font-semibold">Compliance</p>
                <p className="text-xs text-muted-foreground">Audit trail of permissions</p>
              </div>
              <div className="text-center p-4 rounded-lg bg-muted">
                <CheckCircle2 className="h-8 w-8 text-green-500 mx-auto mb-2" />
                <p className="font-semibold">Clarity</p>
                <p className="text-xs text-muted-foreground">Clear responsibilities</p>
              </div>
              <div className="text-center p-4 rounded-lg bg-muted">
                <CheckCircle2 className="h-8 w-8 text-green-500 mx-auto mb-2" />
                <p className="font-semibold">Flexibility</p>
                <p className="text-xs text-muted-foreground">Adapt to org needs</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Role Cards */}
        {roles.map((role) => {
          const Icon = role.icon;
          return (
            <Card key={role.name}>
              <CardHeader>
                <div className="flex items-center gap-3">
                  <Icon className={`h-6 w-6 ${role.color}`} />
                  <div>
                    <CardTitle>{role.name} Role</CardTitle>
                    <CardDescription>{role.purpose}</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <h4 className="font-semibold mb-2">Who Should Have This Role:</h4>
                    <div className="flex flex-wrap gap-2">
                      {role.users.map((user) => (
                        <Badge key={user} variant="secondary">{user}</Badge>
                      ))}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="rounded-lg border p-4">
                      <h4 className="font-semibold mb-3 flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                        CAN DO
                      </h4>
                      <ul className="space-y-2">
                        {role.canDo.map((permission, index) => (
                          <li key={index} className="flex items-start gap-2 text-sm">
                            <span className="text-green-500">✓</span>
                            <span>{permission}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div className="rounded-lg border p-4">
                      <h4 className="font-semibold mb-3 flex items-center gap-2">
                        <XCircle className="h-4 w-4 text-red-500" />
                        CANNOT DO
                      </h4>
                      <ul className="space-y-2">
                        {role.cannotDo.map((restriction, index) => (
                          <li key={index} className="flex items-start gap-2 text-sm">
                            <span className="text-red-500">✗</span>
                            <span>{restriction}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}

        {/* Permission Matrix */}
        <Card>
          <CardHeader>
            <CardTitle>Permission Matrix</CardTitle>
            <CardDescription>
              Quick reference for role capabilities
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2 font-semibold">Action</th>
                    <th className="text-center p-2 font-semibold">Developer</th>
                    <th className="text-center p-2 font-semibold">Reviewer</th>
                    <th className="text-center p-2 font-semibold">Admin</th>
                    <th className="text-center p-2 font-semibold">Executive</th>
                  </tr>
                </thead>
                <tbody>
                  {permissionMatrix.map((row, index) => (
                    <tr key={index} className="border-b hover:bg-muted/50">
                      <td className="p-2">{row.action}</td>
                      <td className="text-center p-2">
                        {row.developer ? (
                          <CheckCircle2 className="h-5 w-5 text-green-500 mx-auto" />
                        ) : (
                          <XCircle className="h-5 w-5 text-muted-foreground mx-auto" />
                        )}
                      </td>
                      <td className="text-center p-2">
                        {row.reviewer ? (
                          <CheckCircle2 className="h-5 w-5 text-green-500 mx-auto" />
                        ) : (
                          <XCircle className="h-5 w-5 text-muted-foreground mx-auto" />
                        )}
                      </td>
                      <td className="text-center p-2">
                        {row.admin ? (
                          <CheckCircle2 className="h-5 w-5 text-green-500 mx-auto" />
                        ) : (
                          <XCircle className="h-5 w-5 text-muted-foreground mx-auto" />
                        )}
                      </td>
                      <td className="text-center p-2">
                        {row.executive ? (
                          <CheckCircle2 className="h-5 w-5 text-green-500 mx-auto" />
                        ) : (
                          <XCircle className="h-5 w-5 text-muted-foreground mx-auto" />
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Best Practices */}
        <Card>
          <CardHeader>
            <CardTitle>Best Practices</CardTitle>
            <CardDescription>
              Guidelines for effective role management
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {bestPractices.map((practice, index) => (
                <div key={index} className="rounded-lg border p-4">
                  <h4 className="font-semibold mb-2">{practice.title}</h4>
                  <p className="text-sm text-muted-foreground mb-3">{practice.description}</p>
                  <div className="flex flex-wrap gap-2">
                    {practice.examples.map((example, idx) => (
                      <Badge key={idx} variant="outline" className="text-xs">{example}</Badge>
                    ))}
                  </div>
                </div>
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
                onClick={() => navigate('/support/common-tasks')}
              >
                <div className="text-left">
                  <div className="font-semibold">Common Tasks →</div>
                  <div className="text-sm text-muted-foreground">Learn what you can do with your role</div>
                </div>
              </Button>
              <Button
                variant="outline"
                className="h-auto justify-start p-4"
                onClick={() => navigate('/support/troubleshooting')}
              >
                <div className="text-left">
                  <div className="font-semibold">Troubleshooting →</div>
                  <div className="text-sm text-muted-foreground">Fix common permission issues</div>
                </div>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default UserRolesPage;
