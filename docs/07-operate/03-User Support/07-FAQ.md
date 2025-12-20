# Frequently Asked Questions (FAQ)
**Last Updated**: December 20, 2025

---

## General Questions

### What is SDLC Orchestrator?

SDLC Orchestrator is an AI-native platform that implements and enforces **SDLC 5.1.1 Enterprise Framework** - a proven 10-stage software development lifecycle with battle-tested results:
- **BFlow**: $43M revenue, 827:1 ROI
- **NQH-Bot**: ₫15B+ value
- **MTEP**: <30 min PaaS deployment

Think of it as:
- **Framework** = The rulebook for software development
- **Orchestrator** = The platform that enforces the rules

### Why should I use SDLC Orchestrator?

✅ **Proven Success**: Real projects with measurable ROI  
✅ **Quality Assurance**: Catch issues before production  
✅ **Compliance**: Automated governance and audit trails  
✅ **AI Assistance**: Intelligent decision support  
✅ **Team Alignment**: Everyone follows same process  
✅ **Career Growth**: Learn industry best practices  

### Who is it for?

- **Developers**: Build quality software systematically
- **Reviewers**: Ensure standards and compliance
- **Project Managers**: Track progress and risks
- **Executives**: Strategic oversight and reporting
- **Admins**: Manage platform and users

---

## Getting Started

### How do I get access?

1. **Request Access**: Contact your organization's admin
2. **Receive Invitation**: Email with credentials
3. **First Login**: Set password, complete profile
4. **Explore**: Take platform tour

### What do I need to know before starting?

**Must Know**:
- SDLC 5.1.1 has 10 stages (Foundation → Govern)
- Quality gates ensure quality at checkpoints
- Evidence is required for gate approval
- AI Council provides intelligent support

**Nice to Know**:
- Read [SDLC Framework Overview](02-SDLC-Framework-Overview.md)
- Explore [Platform Features](03-Platform-Features.md)
- Review [Common Tasks](05-Common-Tasks.md)

### How long does it take to learn?

**Basic Usage**: 1-2 hours
- Login, navigate interface
- Create project, submit evidence
- Understand gates

**Proficient**: 1-2 weeks
- Complete first project
- Use all major features
- Understand framework

**Expert**: 1-3 months
- Multiple projects
- Best practices mastered
- Mentor others

---

## Projects & Lifecycle

### What are the 10 stages?

```
00 FOUNDATION  → Why build this?
01 PLANNING    → What exactly do we need?
02 DESIGN      → How will we build it?
03 INTEGRATE   → How does it connect?
04 BUILD       → Are we building right?
05 TEST        → Does it work?
06 DEPLOY      → Can we ship safely?
07 OPERATE     → Is it running well?
08 COLLABORATE → Is team effective?
09 GOVERN      → Are we compliant?
```

Each stage has specific activities, artifacts, and quality gates.

### What are quality gates?

**Quality Gates** are mandatory checkpoints that ensure quality before proceeding:

- **G0**: Foundation Ready (business case validated)
- **G1**: Design Ready (requirements approved)
- **G2**: Build Ready (architecture approved)
- **G3**: Dev Checkpoint (code quality verified)
- **G4**: Integration Checkpoint (integrations working)
- **G5**: Deploy Ready (testing complete)
- **G6**: Production Ready (deployment verified)
- **G7**: Operational Excellence (monitoring active)
- **G8/G9**: Governance Complete (compliance verified)

You **cannot** skip gates. Each must be passed to proceed.

### What are the project tiers?

| Tier | Duration | Team | Gates | Example |
|------|----------|------|-------|---------|
| **LITE** | 1-2 weeks | 1-3 | Essential only | Internal tool |
| **STANDARD** | 1-3 months | 3-7 | Core gates | Web app |
| **PREMIUM** | 3-6 months | 7-15 | All gates | Platform |
| **ENTERPRISE** | 6+ months | 15+ | Enhanced | Mission-critical |

Your project complexity determines the tier.

### Can I change project tier?

Yes, but requires admin approval:

1. Navigate to Project → Settings
2. Click "Request Tier Change"
3. Provide justification
4. Admin reviews and approves/rejects

**Note**: Changing tier may add/remove gates.

---

## Evidence & Approval

### What is evidence?

**Evidence** = Artifacts that prove you've completed stage activities:

**Examples**:
- **G0**: Business case, stakeholder analysis
- **G1**: Requirements doc, user stories
- **G2**: Architecture diagrams, API specs
- **G5**: Test reports, coverage metrics
- **G6**: Deployment checklist, runbook

Evidence can be:
- **Documents**: PDF, DOCX, etc.
- **Links**: GitHub repos, Jira tickets
- **Reports**: Test results, CI/CD outputs

### What evidence is required?

Each gate has **specific requirements**. To see them:

1. Go to Project → Gates
2. Click on gate (e.g., G0)
3. View "Required Evidence" section
4. AI Council shows completeness check

**Tip**: Use templates from `/SDLC-Enterprise-Framework/03-Templates-Tools/`

### How do I submit evidence?

```
Step-by-step:
1. Navigate to project
2. Go to gate requiring evidence
3. Click "Submit Evidence"
4. Upload file or provide URL
5. Add title and description
6. Tag with gate (auto-filled)
7. Submit

Result:
- Evidence stored in repository
- AI Council reviews automatically
- Appears in gate detail page
- Reviewers notified
```

### How long does approval take?

**Typical Timeline**:
- **AI Council**: 30-60 seconds (automatic)
- **Human Review**: 1-3 business days
- **Complex Gates**: 3-5 business days
- **Emergency**: Can be expedited

**Factors**:
- Reviewer availability
- Evidence completeness
- Project tier (ENTERPRISE may take longer)
- Organization SLA

### What if my gate is rejected?

1. **Read Feedback**: Reviewer explains why
2. **Address Issues**: Fix problems identified
3. **Update Evidence**: Upload corrected artifacts
4. **Resubmit**: Request review again
5. **Iterate**: Repeat until approved

**Common Rejection Reasons**:
- Incomplete evidence
- Missing required artifacts
- Quality standards not met
- Compliance issues

---

## AI Council

### What is AI Council?

**AI Council** is the intelligent decision support system that:
- Reviews evidence automatically
- Assesses risks
- Provides recommendations
- Learns from past projects
- Flags compliance issues

Think of it as your **AI advisor** that knows SDLC 5.1.1 framework inside-out.

### Is AI Council required?

**No**, AI Council is **advisory only**:
- Provides recommendations
- Flags potential issues
- Suggests improvements
- Final decision = human reviewers

**But** it's highly valuable:
- Catches issues early
- Saves review time
- Improves quality
- Learns from 1000s of projects

### Can AI Council approve gates?

**No**. Only **human reviewers** can approve gates:
- AI Council = Advisory
- Human Reviewer = Decision maker

### What if AI Council flags an issue?

**AI Council Warning** ≠ Rejection

1. **Review Warning**: Understand the concern
2. **Assess Risk**: Is it valid?
3. **Take Action**: Fix if necessary
4. **Justify**: Explain why it's acceptable if not fixing
5. **Proceed**: Submit for human review

Human reviewers make final call.

---

## Roles & Permissions

### What roles exist?

| Role | Create Projects | Submit Evidence | Approve Gates | Admin Panel |
|------|----------------|-----------------|---------------|-------------|
| **Developer** | ✅ | ✅ | ❌ | ❌ |
| **Reviewer** | ✅ | ✅ | ✅ | ❌ |
| **Admin** | ✅ | ✅ | ✅ | ✅ |
| **Executive** | ❌ | ❌ | ❌ | Dashboards only |

### How do I get a role upgrade?

1. **Discuss with Manager**: Justify need
2. **Request from Admin**: Submit formal request
3. **Admin Reviews**: Checks qualifications
4. **Approval**: Role updated if approved

**Typical Requirements**:
- **Developer → Reviewer**: 3+ months experience, 5+ projects
- **Reviewer → Admin**: 6+ months, trusted user

### Can I have multiple roles?

**No**, one role per user. But roles are **hierarchical**:
- Admin can do everything Reviewer can
- Reviewer can do everything Developer can

### What if I need temporary elevated access?

Contact admin for:
- **Temporary Role**: Upgraded for specific project
- **Project-Specific**: Access to specific project
- **Time-Limited**: Auto-reverts after period

---

## Technical Questions

### What browsers are supported?

**Recommended**:
- ✅ Chrome 120+ (best support)
- ✅ Firefox 120+
- ✅ Edge 120+

**Limited Support**:
- ⚠️ Safari 17+ (some UI issues)
- ⚠️ Mobile browsers (use desktop for best experience)

**Not Supported**:
- ❌ Internet Explorer (retired)
- ❌ Chrome <100
- ❌ Firefox <100

### What file formats are supported?

**Documents**:
- ✅ PDF, DOCX, XLSX, PPTX
- ✅ TXT, MD, CSV
- ✅ JSON, YAML, XML

**Images**:
- ✅ PNG, JPG, JPEG, SVG
- ✅ GIF (static)

**Not Supported**:
- ❌ Executables (EXE, DMG, APP)
- ❌ Archives (ZIP, RAR) - extract first
- ❌ Video (MP4, AVI) - use links

**File Size Limit**: 50MB per file

### Can I use the API?

**Yes!** API documentation at `/api/docs`

**Get API Key**:
1. Settings → API Keys
2. Click "Generate Key"
3. Copy key (shown once)
4. Use in Authorization header

**Example**:
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://sdlc.nhatquangholding.com/api/v1/projects
```

### Is my data secure?

**Yes**:
- ✅ HTTPS encryption (TLS 1.3)
- ✅ Role-based access control
- ✅ Audit logging (every action tracked)
- ✅ Regular backups
- ✅ SOC 2 compliant infrastructure
- ✅ Data encryption at rest

**Your Responsibilities**:
- Use strong passwords
- Enable MFA
- Don't share credentials
- Report suspicious activity

### What about data retention?

**Active Projects**: Indefinite retention  
**Archived Projects**: 7 years (compliance)  
**Deleted Projects**: 90-day recovery window  
**User Data**: Retained per GDPR requirements  

**Right to Delete**: Contact admin to request data deletion

---

## Troubleshooting

### Why can't I log in?

See [Troubleshooting Guide](06-Troubleshooting.md#i-cant-log-in)

Common fixes:
- Check credentials
- Clear browser cache
- Try different browser
- Reset password
- Contact admin

### Why is bulk delete failing?

**FIXED**: December 20, 2025

If still having issues:
1. Clear browser cache
2. Hard refresh (Ctrl+Shift+R)
3. Check you're on latest version
4. Contact admin

See [Troubleshooting Guide](06-Troubleshooting.md#bulk-delete-not-working-fixed)

### Page is loading forever?

1. Refresh page (F5)
2. Check internet connection
3. Clear cache
4. Try different browser
5. Contact support if persistent

See [Troubleshooting Guide](06-Troubleshooting.md#page-not-loading--500-error)

---

## Best Practices

### How often should I submit evidence?

**Best Practice**: Submit **early and often**

- **Don't wait until gate deadline**
- Submit drafts for early feedback
- Update as work progresses
- Better to submit partial than miss deadline

### Should I use AI Council for everything?

**Yes**, AI Council is free and fast:
- Use for every gate
- Review recommendations
- Learn from suggestions
- But don't rely solely on it

Human judgment > AI judgment

### How do I write good evidence descriptions?

**Good Description**:
```
Title: G0 Business Case - Customer Portal
Description: 
- Strategic justification for customer self-service portal
- Market analysis showing 40% cost reduction potential
- Stakeholder approval from VP Product and CFO
- Risk assessment included
```

**Bad Description**:
```
Title: Business case
Description: G0 stuff
```

**Tips**:
- Be specific
- Include key points
- Mention approvals
- Reference standards

---

## Support & Help

### How do I get help?

**Self-Service** (Fastest):
1. Search this FAQ
2. Check [Troubleshooting Guide](06-Troubleshooting.md)
3. Read [Getting Started](01-Getting-Started.md)
4. Review [Platform Features](03-Platform-Features.md)

**Human Support**:
1. Ask team members
2. Contact project lead
3. Submit help ticket
4. Contact admin

See [Support Channels](09-Support-Channels.md)

### Can I suggest features?

**Yes!** We welcome feedback:

1. **In-Platform**: Feedback button
2. **GitHub**: Submit issue (if repo access)
3. **Email**: support@nhatquangholding.com
4. **Quarterly Review**: Feature request sessions

### Where can I learn more about SDLC 5.1.1?

**Framework Documentation**:
- **Overview**: `/SDLC-Enterprise-Framework/README.md`
- **Methodology**: `/SDLC-Enterprise-Framework/02-Core-Methodology/`
- **Templates**: `/SDLC-Enterprise-Framework/03-Templates-Tools/`
- **Case Studies**: `/SDLC-Enterprise-Framework/04-Case-Studies/`
- **Training**: `/SDLC-Enterprise-Framework/06-Training-Materials/`

**Platform Documentation**:
- This user support section
- API documentation at `/api/docs`
- In-platform help and tooltips

---

## Terminology

| Term | Definition |
|------|------------|
| **SDLC** | Software Development Lifecycle |
| **Gate** | Quality checkpoint in lifecycle |
| **Evidence** | Artifacts proving stage completion |
| **Tier** | Project classification (LITE to ENTERPRISE) |
| **AI Council** | Intelligent advisory system |
| **Audit Trail** | Complete history of actions |
| **Framework** | SDLC 5.1.1 governance policy |
| **Orchestrator** | This platform (enforcement tool) |

---

## Still Have Questions?

### Documentation
- 📖 [Getting Started](01-Getting-Started.md)
- 🎯 [Framework Overview](02-SDLC-Framework-Overview.md)
- 🔧 [Platform Features](03-Platform-Features.md)
- 📝 [Common Tasks](05-Common-Tasks.md)
- 🐛 [Troubleshooting](06-Troubleshooting.md)
- 💡 [Best Practices](08-Best-Practices.md)
- 📞 [Support Channels](09-Support-Channels.md)

### Contact Support
See [Support Channels](09-Support-Channels.md) for all contact methods.

---

**Framework**: SDLC 5.1.1 Complete Lifecycle  
**Platform**: SDLC Orchestrator v1.2.0  
**Last Updated**: December 20, 2025
