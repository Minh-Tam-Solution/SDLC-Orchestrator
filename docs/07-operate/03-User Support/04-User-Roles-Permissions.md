# User Roles & Permissions Guide
**Access Control and Role Management**  
**Last Updated**: December 20, 2025

---

## Overview

SDLC Orchestrator uses **Role-Based Access Control (RBAC)** to manage what users can see and do. This ensures:
- ✅ Security: Only authorized actions
- ✅ Compliance: Audit trail of permissions
- ✅ Clarity: Clear responsibilities
- ✅ Flexibility: Adapt to organization needs

---

## User Roles

### 1. Developer Role

**Purpose**: Build and submit work through SDLC stages

**Who Should Have This Role**:
- Software developers
- QA engineers
- DevOps engineers
- Junior team members
- Contractors (project-specific)

**Permissions**:

**✅ CAN DO**:
```
Projects:
- Create new projects
- View own projects
- Update project details
- Add comments/discussions

Evidence:
- Submit evidence
- Upload artifacts
- Update own evidence
- View project evidence

Gates:
- View gate requirements
- Request gate approval
- View gate status
- Respond to feedback

Dashboard:
- View own project dashboards
- View assigned tasks
- See notifications
- Access reports (own projects)

Profile:
- Update own profile
- Change password
- Configure notifications
- Generate API keys (own)
```

**❌ CANNOT DO**:
```
- Approve/reject gates
- Create/delete users
- Modify system settings
- Access admin panel
- View all projects
- Delete others' evidence
- Override compliance rules
```

**Typical Use Cases**:
1. Create project for new feature
2. Submit G0 business case evidence
3. Upload architecture diagrams for G2
4. Request gate approval
5. Address reviewer feedback

---

### 2. Reviewer Role

**Purpose**: Review evidence and approve quality gates

**Who Should Have This Role**:
- Senior developers
- Tech leads
- Architects
- QA leads
- Security specialists

**Permissions**:

**✅ CAN DO**:
```
All Developer permissions, PLUS:

Reviews:
- Review gate evidence
- Approve/reject gates
- Provide feedback
- Request revisions

Projects:
- View all projects (read-only)
- Access any project for review
- View audit trails
- See compliance status

Reports:
- Generate compliance reports
- View team metrics
- Export audit logs
- Access analytics dashboards

AI Council:
- View AI recommendations
- Override AI flags (with justification)
- Configure AI thresholds (project-level)
```

**❌ CANNOT DO**:
```
- Create/delete users
- Modify system configuration
- Delete projects
- Override framework rules
- Access admin panel
- Bulk operations (admin only)
```

**Typical Use Cases**:
1. Review G0 business case submission
2. Approve G2 architecture design
3. Request revisions on incomplete evidence
4. Generate compliance report for audit
5. Provide feedback on testing strategy

**Review Responsibilities**:
```
Must:
- Review within SLA (typically 3 business days)
- Provide constructive feedback
- Follow framework standards
- Document decision rationale
- Maintain objectivity

Should:
- Use AI Council recommendations
- Check completeness
- Verify compliance
- Consider risk factors
- Suggest improvements
```

---

### 3. Admin Role

**Purpose**: Manage platform, users, and system configuration

**Who Should Have This Role**:
- System administrators
- Platform owners
- IT managers
- Compliance officers
- Senior leadership (limited number)

**Permissions**:

**✅ CAN DO**:
```
All Reviewer permissions, PLUS:

User Management:
- Create new users
- Update user details
- Delete users (permanent)
- Bulk user operations
- Reset passwords
- Manage roles
- View user activity logs

System Configuration:
- Configure platform settings
- Manage integrations (GitHub, Jira, etc.)
- Set compliance rules
- Configure notifications
- Manage templates
- Set SLA targets

Project Administration:
- Delete projects
- Archive projects
- Reassign ownership
- Override project settings
- Force gate approvals (emergency)

Access Control:
- View all audit logs
- Export compliance data
- Manage API keys
- Configure security settings
- Set password policies

Monitoring:
- View system health
- Check resource usage
- Monitor performance
- Review error logs
- Access backend logs
```

**❌ CANNOT DO**:
```
- Modify audit logs (immutable)
- Delete compliance records
- Bypass framework gates (except emergency waiver)
- Change historical data
```

**Typical Use Cases**:
1. Create new user account for hire
2. Bulk delete inactive users
3. Generate compliance report for executive team
4. Configure GitHub integration
5. Review audit logs for security incident
6. Emergency gate waiver (with justification)

**Admin Responsibilities**:
```
Must:
- Maintain system security
- Ensure compliance
- Manage access appropriately
- Monitor system health
- Respond to support requests
- Document configuration changes

Should:
- Regular security reviews
- User access audits
- System backups
- Performance optimization
- Stay updated on platform updates
```

---

### 4. Executive Role

**Purpose**: Strategic oversight and reporting (read-only)

**Who Should Have This Role**:
- C-level executives (CEO, CTO, CFO)
- VPs and directors
- Product owners
- Stakeholders
- Board members

**Permissions**:

**✅ CAN DO**:
```
Viewing:
- View all projects
- View dashboards (strategic view)
- View compliance reports
- View team metrics
- View risk assessments

Reports:
- Generate executive reports
- Export portfolio view
- View ROI metrics
- See resource utilization
- Access historical data

Strategic:
- View strategic alignment
- See project pipeline
- Monitor gate progress
- Track budget vs actuals
- View success metrics
```

**❌ CANNOT DO**:
```
- Create/modify projects
- Submit evidence
- Approve gates
- Manage users
- Change system settings
- Access admin panel
- Day-to-day operations
- Approve/reject anything
```

**Typical Use Cases**:
1. Review portfolio dashboard
2. Generate executive summary report
3. Monitor strategic alignment
4. Track budget and resource utilization
5. View risk heatmap across projects

**Key Dashboards**:
```
- Portfolio Overview
- Risk & Compliance Heatmap
- Resource Utilization
- ROI & Success Metrics
- Strategic Alignment Matrix
```

---

## Permission Matrix

### Detailed Permissions

| Action | Developer | Reviewer | Admin | Executive |
|--------|-----------|----------|-------|-----------|
| **Projects** |
| Create project | ✅ | ✅ | ✅ | ❌ |
| View own projects | ✅ | ✅ | ✅ | ❌ |
| View all projects | ❌ | ✅ | ✅ | ✅ |
| Update project | ✅ Owner | ✅ | ✅ | ❌ |
| Delete project | ❌ | ❌ | ✅ | ❌ |
| Archive project | ❌ | ❌ | ✅ | ❌ |
| **Evidence** |
| Submit evidence | ✅ | ✅ | ✅ | ❌ |
| View evidence | ✅ Project | ✅ All | ✅ All | ✅ All |
| Update own evidence | ✅ | ✅ | ✅ | ❌ |
| Delete own evidence | ✅ Draft | ✅ | ✅ | ❌ |
| Delete any evidence | ❌ | ❌ | ✅ | ❌ |
| **Gates** |
| View gate status | ✅ Project | ✅ All | ✅ All | ✅ All |
| Request approval | ✅ | ✅ | ✅ | ❌ |
| Review evidence | ❌ | ✅ | ✅ | ❌ |
| Approve gate | ❌ | ✅ | ✅ | ❌ |
| Reject gate | ❌ | ✅ | ✅ | ❌ |
| Waive gate | ❌ | ❌ | ✅ Emergency | ❌ |
| **Users** |
| View users | ✅ Team | ✅ All | ✅ All | ✅ All |
| Create user | ❌ | ❌ | ✅ | ❌ |
| Update user | ❌ | ❌ | ✅ | ❌ |
| Delete user | ❌ | ❌ | ✅ | ❌ |
| Bulk operations | ❌ | ❌ | ✅ | ❌ |
| Manage roles | ❌ | ❌ | ✅ | ❌ |
| **Reports** |
| Project reports | ✅ Own | ✅ All | ✅ All | ✅ All |
| Compliance reports | ❌ | ✅ | ✅ | ✅ |
| Executive dashboard | ❌ | ❌ | ✅ | ✅ |
| Audit logs | ❌ | ✅ Own | ✅ All | ❌ |
| **System** |
| Admin panel | ❌ | ❌ | ✅ | ❌ |
| System config | ❌ | ❌ | ✅ | ❌ |
| Integrations | ❌ | ❌ | ✅ | ❌ |
| API keys (own) | ✅ | ✅ | ✅ | ✅ |
| API keys (others) | ❌ | ❌ | ✅ | ❌ |

---

## Project-Level Roles

In addition to global roles, users can have **project-specific roles**:

### Project Member
```
- View project details
- View evidence
- Comment on discussions
- Receive notifications
```

### Project Lead
```
All Member permissions, PLUS:
- Edit project details
- Add/remove team members
- Assign tasks
- Manage project settings
```

### Project Stakeholder
```
- View project (read-only)
- View dashboards
- Receive updates
- Cannot make changes
```

**Note**: Global role takes precedence. Admin can do everything regardless of project role.

---

## Role Assignment

### How Roles Are Assigned

**Initial Assignment**:
1. Admin creates user account
2. Assigns global role (Developer/Reviewer/Admin/Executive)
3. User receives invitation email
4. User logs in and accepts role

**Role Changes**:
1. User requests role upgrade
2. Manager/Admin reviews request
3. Checks qualification criteria
4. Approves or denies
5. Role updated if approved

**Project-Level Assignment**:
1. Project Lead or Admin adds user to project
2. Assigns project role (Member/Lead/Stakeholder)
3. User gets project access
4. Permissions active immediately

---

## Role Qualification Criteria

### Developer → Reviewer

**Requirements**:
```
Experience:
- 3+ months using platform
- 5+ projects completed
- Demonstrated understanding of SDLC 5.1.1

Skills:
- Technical expertise in domain
- Understanding of quality standards
- Good communication skills

Endorsement:
- Recommendation from current Reviewer
- Manager approval
```

**Process**:
1. Submit request via platform
2. Provide justification
3. Manager reviews
4. Admin approves
5. Training (if required)

### Reviewer → Admin

**Requirements**:
```
Experience:
- 6+ months as Reviewer
- 20+ gate reviews completed
- Trusted user status

Skills:
- Platform expertise
- User management experience
- System administration knowledge

Justification:
- Clear need (team growth, backup admin)
- Manager approval
- Security clearance (if required)
```

**Process**:
1. Formal request to Admin
2. Business justification
3. Admin team reviews
4. Security check
5. Training required
6. Probation period (optional)

---

## Best Practices

### For Developers

**Do**:
- ✅ Submit evidence early
- ✅ Request feedback before formal submission
- ✅ Respond promptly to reviews
- ✅ Keep evidence organized
- ✅ Follow documentation standards

**Don't**:
- ❌ Try to bypass gates
- ❌ Rush submissions for approval
- ❌ Ignore reviewer feedback
- ❌ Share credentials
- ❌ Request unnecessary role upgrades

### For Reviewers

**Do**:
- ✅ Review within SLA (3 business days)
- ✅ Provide constructive, specific feedback
- ✅ Use AI Council recommendations
- ✅ Document decision rationale
- ✅ Be objective and fair

**Don't**:
- ❌ Rubber-stamp approvals
- ❌ Be unnecessarily harsh
- ❌ Approve without reviewing
- ❌ Let personal relationships influence decisions
- ❌ Skip framework requirements

### For Admins

**Do**:
- ✅ Follow principle of least privilege
- ✅ Regular access reviews (quarterly)
- ✅ Audit admin actions
- ✅ Document configuration changes
- ✅ Maintain security standards

**Don't**:
- ❌ Share admin credentials
- ❌ Grant admin role without justification
- ❌ Skip security checks
- ❌ Modify audit logs
- ❌ Bypass compliance rules without documentation

---

## Security Considerations

### Password Requirements

```
Minimum:
- 12 characters
- Uppercase + lowercase
- Numbers
- Special characters
- Not in breach database

Recommended:
- 16+ characters
- Use password manager
- Unique per service
- Enable MFA
```

### Multi-Factor Authentication (MFA)

**Required For**:
- All Admin users
- Reviewers (recommended)
- Developers (optional)

**Setup**:
1. Profile → Security Settings
2. Enable MFA
3. Scan QR code with authenticator app (Google Auth, Authy)
4. Enter verification code
5. Save backup codes

### API Keys

**Permissions**:
- Developer: Can generate own API keys
- Reviewer: Can generate own API keys
- Admin: Can generate and manage all API keys
- Executive: Read-only keys

**Best Practices**:
```
Do:
- Rotate keys regularly (90 days)
- Use environment variables
- Revoke unused keys
- Monitor key usage

Don't:
- Commit to Git
- Share keys
- Use same key across environments
- Hard-code in applications
```

---

## Audit & Compliance

### Audit Logging

**What Is Logged**:
```
Every action:
- User login/logout
- Role changes
- Project access
- Evidence submission
- Gate approvals/rejections
- Configuration changes
- User management actions
```

**Who Can View**:
- Developer: Own actions only
- Reviewer: Own + related project actions
- Admin: All actions
- Executive: Summary reports

### Compliance Reports

**Available Reports**:
```
User Access Report:
- Who has what role
- When assigned
- By whom
- Access changes

Action Audit Report:
- All user actions
- Timestamps
- Results
- Context

Role Change Report:
- Role upgrades/downgrades
- Justification
- Approver
- Timeline
```

---

## Troubleshooting

### "Permission Denied" Error

**Check**:
1. ✓ Your current role
2. ✓ Required role for action
3. ✓ Project membership (if project-specific)
4. ✓ Session not expired

**Solution**:
- If you should have access: Contact admin
- If wrong project: Request project access
- If session expired: Re-login
- If role insufficient: Request role upgrade

### Can't See Project

**Possible Reasons**:
1. Not a project member
2. Project archived/deleted
3. Insufficient role
4. Wrong filter applied

**Solution**:
- Request project access from Project Lead
- Check with admin if project exists
- Clear filters in project list
- Search by project name

### Can't Approve Gate

**Requirements**:
- Must have Reviewer or Admin role
- Must not be the submitter (conflict of interest)
- Gate must be in "IN_REVIEW" status
- All required evidence must be submitted

**Solution**:
- Check your role in Profile
- Contact admin if you should be Reviewer
- Assign different reviewer if conflict of interest
- Ensure evidence complete before reviewing

---

## Summary

### Role Hierarchy

```
Executive (Read-Only Strategic View)
    ↑
Admin (Full System Control)
    ↑
Reviewer (Gate Approval)
    ↑
Developer (Submit & Build)
```

### Key Principles

1. **Least Privilege**: Users get minimum access needed
2. **Separation of Duties**: Submitters can't approve own work
3. **Audit Everything**: All actions logged
4. **Clear Hierarchy**: Roles have clear boundaries
5. **Security First**: MFA, strong passwords, API key management

---

**Framework**: SDLC 5.1.1 Complete Lifecycle  
**Platform**: SDLC Orchestrator v1.2.0  
**Last Updated**: December 20, 2025
