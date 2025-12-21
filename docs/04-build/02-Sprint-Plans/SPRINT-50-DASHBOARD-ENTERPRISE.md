# SPRINT-50: Dashboard & Enterprise Features
## EP-05: Enterprise SDLC Migration | Phase 4 (Final)

---

**Document Information**

| Field | Value |
|-------|-------|
| **Sprint ID** | SPRINT-50 |
| **Epic** | EP-05: Enterprise SDLC Migration Engine |
| **Duration** | 2 weeks (May 19-30, 2026) |
| **Status** | PLANNED |
| **Team** | 2 Backend + 2 Frontend + 1 QA |
| **Story Points** | 18 SP |
| **Budget** | $10,000 |
| **Framework** | SDLC 5.1.1 + SASE Level 2 |
| **Reference** | ADR-020, Sprint 47-49 |

---

## Sprint Goals

### Primary Objectives

| # | Objective | Priority | Owner |
|---|-----------|----------|-------|
| 1 | Build Migration Dashboard with history | P0 | Frontend Lead |
| 2 | Implement multi-project support | P0 | Backend Lead |
| 3 | Create Enterprise tier features | P1 | Backend Dev |
| 4 | Build reporting & export | P1 | Frontend Dev |
| 5 | Complete E2E testing & documentation | P0 | QA Lead |

### Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Dashboard load time | <2s | Performance test |
| Multi-project switching | <1s | UX testing |
| Report generation | <10s | Benchmark |
| E2E test coverage | ≥90% | Test report |

---

## Architecture

### Enterprise Dashboard Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  SDLC Migration Dashboard                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Navigation Bar                                                        │ │
│  │  [Home] [Projects ▼] [Migrations] [Reports] [Settings]                │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌─────────────────────────────────┐ ┌─────────────────────────────────┐   │
│  │  Project Selector               │ │  Quick Actions                   │   │
│  │  ┌─────────────────────────┐   │ │  [+ New Migration]               │   │
│  │  │ Bflow CRM          ✓   │   │ │  [📊 Generate Report]            │   │
│  │  │ SDLC-Orchestrator      │   │ │  [⚙️ Configure]                  │   │
│  │  │ Enterprise Portal      │   │ └─────────────────────────────────┘   │
│  │  └─────────────────────────┘   │                                       │
│  └─────────────────────────────────┘                                       │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Compliance Overview                                                   │ │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │ │
│  │  │  Overall     │ │  Header      │ │  Naming      │ │  Version     │ │ │
│  │  │    87%       │ │    92%       │ │    85%       │ │    78%       │ │ │
│  │  │  [===----]   │ │  [====--]    │ │  [===---]    │ │  [==----]    │ │ │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Migration History                                                     │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │ │
│  │  │ Date       │ Version    │ Files │ Status  │ Duration │ Actions │ │ │
│  │  ├─────────────────────────────────────────────────────────────────┤ │ │
│  │  │ 2026-05-20 │ 5.0→5.1    │ 1,247 │ Success │ 2m 34s   │ [View]  │ │ │
│  │  │ 2026-05-15 │ 4.8→5.0    │ 1,198 │ Success │ 3m 12s   │ [View]  │ │ │
│  │  │ 2026-05-10 │ Init       │ 1,120 │ Success │ 1m 05s   │ [View]  │ │ │
│  │  └─────────────────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Compliance Trend (30 Days)                                           │ │
│  │      100%|                                          ___/``            │ │
│  │       90%|                              ___/```----´                  │ │
│  │       80%|              ___/```----```-´                              │ │
│  │       70%|___/```------´                                              │ │
│  │       60%+----+----+----+----+----+----+----+----+----+----+         │ │
│  │           W1   W2   W3   W4   W5                                      │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Week 1: Dashboard & Multi-Project (May 19-23)

### Day 1-2: Project Management Backend

**Task**: Multi-project support with PostgreSQL

```python
# backend/app/models/project.py

from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from ..db.base import Base

class ProjectTier(str, enum.Enum):
    LITE = "LITE"
    STANDARD = "STANDARD"
    PROFESSIONAL = "PROFESSIONAL"
    ENTERPRISE = "ENTERPRISE"

class Project(Base):
    """SDLC Project model"""
    
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1000))
    
    # Configuration
    tier = Column(Enum(ProjectTier), default=ProjectTier.STANDARD)
    sdlc_version = Column(String(20), default="5.1.0")
    docs_root = Column(String(500), default="docs")
    config_json = Column(JSON, nullable=True)
    
    # Repository info
    repo_url = Column(String(500))
    repo_branch = Column(String(100), default="main")
    
    # Stats
    total_files = Column(Integer, default=0)
    compliance_score = Column(Integer, default=0)
    last_scan = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    migrations = relationship("Migration", back_populates="project")
    owner_id = Column(String, ForeignKey("users.id"))


class Migration(Base):
    """Migration history model"""
    
    __tablename__ = "migrations"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"))
    
    # Migration details
    from_version = Column(String(20))
    to_version = Column(String(20))
    
    # Results
    files_scanned = Column(Integer, default=0)
    files_modified = Column(Integer, default=0)
    fixes_applied = Column(Integer, default=0)
    fixes_failed = Column(Integer, default=0)
    
    # Status
    status = Column(String(20))  # pending, running, success, failed, rolled_back
    error_message = Column(String(2000))
    
    # Backup info
    backup_branch = Column(String(100))
    commit_hash = Column(String(40))
    
    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)
    
    # Relationships
    project = relationship("Project", back_populates="migrations")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)


# backend/app/services/project_service.py

from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from ..models.project import Project, Migration, ProjectTier
from ..schemas.project import ProjectCreate, ProjectUpdate

class ProjectService:
    """Service for managing SDLC projects"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_project(self, data: ProjectCreate, owner_id: str) -> Project:
        """Create a new project"""
        project = Project(
            id=str(uuid.uuid4()),
            name=data.name,
            description=data.description,
            tier=data.tier or ProjectTier.STANDARD,
            sdlc_version=data.sdlc_version or "5.1.0",
            docs_root=data.docs_root or "docs",
            repo_url=data.repo_url,
            repo_branch=data.repo_branch or "main",
            owner_id=owner_id,
        )
        
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        
        return project
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """Get project by ID"""
        return self.db.query(Project).filter(Project.id == project_id).first()
    
    def list_projects(
        self,
        owner_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Project]:
        """List projects for owner"""
        return (
            self.db.query(Project)
            .filter(Project.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def update_project(
        self,
        project_id: str,
        data: ProjectUpdate
    ) -> Optional[Project]:
        """Update project"""
        project = self.get_project(project_id)
        if not project:
            return None
        
        for field, value in data.dict(exclude_unset=True).items():
            setattr(project, field, value)
        
        project.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(project)
        
        return project
    
    def update_compliance_score(
        self,
        project_id: str,
        score: int,
        total_files: int
    ):
        """Update project compliance score"""
        project = self.get_project(project_id)
        if project:
            project.compliance_score = score
            project.total_files = total_files
            project.last_scan = datetime.utcnow()
            self.db.commit()
    
    def add_migration(
        self,
        project_id: str,
        from_version: str,
        to_version: str
    ) -> Migration:
        """Create new migration record"""
        migration = Migration(
            id=str(uuid.uuid4()),
            project_id=project_id,
            from_version=from_version,
            to_version=to_version,
            status="pending",
            started_at=datetime.utcnow(),
        )
        
        self.db.add(migration)
        self.db.commit()
        self.db.refresh(migration)
        
        return migration
    
    def update_migration(
        self,
        migration_id: str,
        **kwargs
    ) -> Optional[Migration]:
        """Update migration record"""
        migration = self.db.query(Migration).filter(Migration.id == migration_id).first()
        if not migration:
            return None
        
        for key, value in kwargs.items():
            if hasattr(migration, key):
                setattr(migration, key, value)
        
        self.db.commit()
        self.db.refresh(migration)
        
        return migration
    
    def get_migration_history(
        self,
        project_id: str,
        limit: int = 10
    ) -> List[Migration]:
        """Get migration history for project"""
        return (
            self.db.query(Migration)
            .filter(Migration.project_id == project_id)
            .order_by(Migration.created_at.desc())
            .limit(limit)
            .all()
        )
```

---

### Day 3-4: Migration Dashboard Frontend

**Task**: React dashboard with project switching

```typescript
// frontend/web/src/pages/migrations/MigrationDashboard.tsx

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Card, CardContent, CardHeader, CardTitle,
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
  Button,
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
  Badge,
  Tabs, TabsContent, TabsList, TabsTrigger,
} from '@/components/ui';
import { 
  Play, History, FileText, Settings, Download, 
  CheckCircle, XCircle, Clock, RefreshCw 
} from 'lucide-react';
import { ComplianceWidget } from '@/components/compliance/ComplianceWidget';
import { ComplianceTrendChart } from '@/components/charts/ComplianceTrendChart';

interface Project {
  id: string;
  name: string;
  tier: string;
  sdlcVersion: string;
  complianceScore: number;
  totalFiles: number;
  lastScan: string;
}

interface Migration {
  id: string;
  fromVersion: string;
  toVersion: string;
  status: string;
  filesModified: number;
  fixesApplied: number;
  durationSeconds: number;
  createdAt: string;
}

export const MigrationDashboard: React.FC = () => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [migrations, setMigrations] = useState<Migration[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Fetch projects
  useEffect(() => {
    fetch('/api/v1/projects')
      .then(res => res.json())
      .then(data => {
        setProjects(data);
        if (projectId) {
          const project = data.find((p: Project) => p.id === projectId);
          setSelectedProject(project);
        } else if (data.length > 0) {
          setSelectedProject(data[0]);
          navigate(`/migrations/${data[0].id}`);
        }
      })
      .finally(() => setIsLoading(false));
  }, [projectId, navigate]);

  // Fetch migrations when project changes
  useEffect(() => {
    if (selectedProject) {
      fetch(`/api/v1/projects/${selectedProject.id}/migrations`)
        .then(res => res.json())
        .then(data => setMigrations(data));
    }
  }, [selectedProject]);

  const handleProjectChange = (projectId: string) => {
    const project = projects.find(p => p.id === projectId);
    setSelectedProject(project || null);
    navigate(`/migrations/${projectId}`);
  };

  const handleStartMigration = async () => {
    if (!selectedProject) return;
    
    // Show migration dialog
    // ... implementation
  };

  const handleExportReport = async () => {
    if (!selectedProject) return;
    
    const response = await fetch(
      `/api/v1/projects/${selectedProject.id}/report?format=pdf`,
      { method: 'GET' }
    );
    
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${selectedProject.name}-compliance-report.pdf`;
    a.click();
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'success':
        return <Badge className="bg-green-500"><CheckCircle className="w-3 h-3 mr-1" />Success</Badge>;
      case 'failed':
        return <Badge className="bg-red-500"><XCircle className="w-3 h-3 mr-1" />Failed</Badge>;
      case 'running':
        return <Badge className="bg-blue-500"><RefreshCw className="w-3 h-3 mr-1 animate-spin" />Running</Badge>;
      case 'rolled_back':
        return <Badge className="bg-yellow-500"><History className="w-3 h-3 mr-1" />Rolled Back</Badge>;
      default:
        return <Badge className="bg-gray-500"><Clock className="w-3 h-3 mr-1" />Pending</Badge>;
    }
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">SDLC Migration Dashboard</h1>
          <p className="text-gray-500">Manage and monitor SDLC version migrations</p>
        </div>
        
        <div className="flex items-center gap-4">
          {/* Project Selector */}
          <Select value={selectedProject?.id} onValueChange={handleProjectChange}>
            <SelectTrigger className="w-64">
              <SelectValue placeholder="Select project" />
            </SelectTrigger>
            <SelectContent>
              {projects.map(project => (
                <SelectItem key={project.id} value={project.id}>
                  {project.name}
                  <Badge variant="outline" className="ml-2">{project.tier}</Badge>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          {/* Quick Actions */}
          <Button onClick={handleStartMigration}>
            <Play className="w-4 h-4 mr-2" />
            New Migration
          </Button>
          <Button variant="outline" onClick={handleExportReport}>
            <Download className="w-4 h-4 mr-2" />
            Export Report
          </Button>
        </div>
      </div>
      
      {selectedProject && (
        <Tabs defaultValue="overview" className="space-y-4">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="history">Migration History</TabsTrigger>
            <TabsTrigger value="reports">Reports</TabsTrigger>
            <TabsTrigger value="settings">Settings</TabsTrigger>
          </TabsList>
          
          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-4">
            {/* Compliance Overview */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <ComplianceWidget projectId={selectedProject.id} />
              
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">Total Files</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{selectedProject.totalFiles.toLocaleString()}</div>
                  <p className="text-xs text-gray-500">in docs folder</p>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">SDLC Version</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{selectedProject.sdlcVersion}</div>
                  <p className="text-xs text-gray-500">current version</p>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">Last Scan</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {new Date(selectedProject.lastScan).toLocaleDateString()}
                  </div>
                  <p className="text-xs text-gray-500">
                    {new Date(selectedProject.lastScan).toLocaleTimeString()}
                  </p>
                </CardContent>
              </Card>
            </div>
            
            {/* Compliance Trend Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Compliance Trend (30 Days)</CardTitle>
              </CardHeader>
              <CardContent>
                <ComplianceTrendChart projectId={selectedProject.id} days={30} />
              </CardContent>
            </Card>
            
            {/* Recent Migrations */}
            <Card>
              <CardHeader>
                <CardTitle>Recent Migrations</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead>Version</TableHead>
                      <TableHead>Files</TableHead>
                      <TableHead>Fixes</TableHead>
                      <TableHead>Duration</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {migrations.slice(0, 5).map(migration => (
                      <TableRow key={migration.id}>
                        <TableCell>
                          {new Date(migration.createdAt).toLocaleDateString()}
                        </TableCell>
                        <TableCell>
                          {migration.fromVersion} → {migration.toVersion}
                        </TableCell>
                        <TableCell>{migration.filesModified}</TableCell>
                        <TableCell>{migration.fixesApplied}</TableCell>
                        <TableCell>{formatDuration(migration.durationSeconds)}</TableCell>
                        <TableCell>{getStatusBadge(migration.status)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>
          
          {/* History Tab */}
          <TabsContent value="history">
            <MigrationHistoryTable 
              projectId={selectedProject.id} 
              migrations={migrations} 
            />
          </TabsContent>
          
          {/* Reports Tab */}
          <TabsContent value="reports">
            <ReportsPanel projectId={selectedProject.id} />
          </TabsContent>
          
          {/* Settings Tab */}
          <TabsContent value="settings">
            <ProjectSettingsForm project={selectedProject} />
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
};

export default MigrationDashboard;
```

---

### Day 5: Enterprise Features

**Task**: Enterprise tier capabilities

```python
# backend/app/services/enterprise_features.py

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json

class EnterpriseFeatures:
    """
    Enterprise tier features for SDLC Migration
    
    Features:
    - Multi-tenant support
    - Audit logging
    - Scheduled migrations
    - Custom rules engine
    - SSO integration
    - Advanced reporting
    """
    
    def __init__(self, db, redis_client):
        self.db = db
        self.redis = redis_client
    
    # Audit Logging
    async def log_audit_event(
        self,
        project_id: str,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        details: Dict = None,
    ):
        """Log audit event for compliance tracking"""
        from ..models.audit import AuditLog
        
        log = AuditLog(
            project_id=project_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=json.dumps(details) if details else None,
            timestamp=datetime.utcnow(),
            ip_address=self._get_client_ip(),
        )
        
        self.db.add(log)
        self.db.commit()
    
    async def get_audit_logs(
        self,
        project_id: str,
        start_date: datetime = None,
        end_date: datetime = None,
        action: str = None,
        limit: int = 100,
    ) -> List[Dict]:
        """Retrieve audit logs with filters"""
        from ..models.audit import AuditLog
        
        query = self.db.query(AuditLog).filter(
            AuditLog.project_id == project_id
        )
        
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        if action:
            query = query.filter(AuditLog.action == action)
        
        logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
        
        return [
            {
                "id": log.id,
                "action": log.action,
                "user_id": log.user_id,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "details": json.loads(log.details) if log.details else None,
                "timestamp": log.timestamp.isoformat(),
                "ip_address": log.ip_address,
            }
            for log in logs
        ]
    
    # Scheduled Migrations
    async def schedule_migration(
        self,
        project_id: str,
        target_version: str,
        scheduled_time: datetime,
        options: Dict = None,
    ) -> str:
        """Schedule a migration for later execution"""
        from ..models.scheduled_job import ScheduledJob
        
        job = ScheduledJob(
            project_id=project_id,
            job_type="migration",
            scheduled_time=scheduled_time,
            config=json.dumps({
                "target_version": target_version,
                "options": options or {},
            }),
            status="scheduled",
        )
        
        self.db.add(job)
        self.db.commit()
        
        # Add to job queue
        await self._enqueue_job(job.id, scheduled_time)
        
        return job.id
    
    async def cancel_scheduled_migration(self, job_id: str) -> bool:
        """Cancel a scheduled migration"""
        from ..models.scheduled_job import ScheduledJob
        
        job = self.db.query(ScheduledJob).filter(
            ScheduledJob.id == job_id
        ).first()
        
        if not job or job.status != "scheduled":
            return False
        
        job.status = "cancelled"
        self.db.commit()
        
        await self._dequeue_job(job_id)
        
        return True
    
    # Custom Rules Engine
    async def add_custom_rule(
        self,
        project_id: str,
        rule_name: str,
        rule_type: str,
        rule_config: Dict,
    ) -> str:
        """Add custom compliance rule"""
        from ..models.custom_rule import CustomRule
        
        rule = CustomRule(
            project_id=project_id,
            name=rule_name,
            rule_type=rule_type,
            config=json.dumps(rule_config),
            enabled=True,
        )
        
        self.db.add(rule)
        self.db.commit()
        
        return rule.id
    
    async def get_custom_rules(self, project_id: str) -> List[Dict]:
        """Get all custom rules for project"""
        from ..models.custom_rule import CustomRule
        
        rules = self.db.query(CustomRule).filter(
            CustomRule.project_id == project_id,
            CustomRule.enabled == True,
        ).all()
        
        return [
            {
                "id": rule.id,
                "name": rule.name,
                "rule_type": rule.rule_type,
                "config": json.loads(rule.config),
                "enabled": rule.enabled,
            }
            for rule in rules
        ]
    
    # Advanced Reporting
    async def generate_compliance_report(
        self,
        project_id: str,
        format: str = "pdf",
        include_details: bool = True,
    ) -> bytes:
        """Generate comprehensive compliance report"""
        from ..services.report_generator import ReportGenerator
        
        # Get project data
        project = self.db.query(Project).filter(Project.id == project_id).first()
        
        # Get compliance data
        from ..services.compliance_service import compliance_service
        score = await compliance_service.get_current_score(project_id)
        
        # Get migration history
        migrations = self.db.query(Migration).filter(
            Migration.project_id == project_id
        ).order_by(Migration.created_at.desc()).limit(10).all()
        
        # Generate report
        generator = ReportGenerator()
        
        if format == "pdf":
            return await generator.generate_pdf(
                project=project,
                score=score,
                migrations=migrations,
                include_details=include_details,
            )
        elif format == "excel":
            return await generator.generate_excel(
                project=project,
                score=score,
                migrations=migrations,
            )
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    # Compliance Trend Analysis
    async def get_compliance_trend(
        self,
        project_id: str,
        days: int = 30,
    ) -> List[Dict]:
        """Get compliance score trend over time"""
        from ..models.compliance_snapshot import ComplianceSnapshot
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        snapshots = self.db.query(ComplianceSnapshot).filter(
            ComplianceSnapshot.project_id == project_id,
            ComplianceSnapshot.timestamp >= start_date,
        ).order_by(ComplianceSnapshot.timestamp).all()
        
        return [
            {
                "date": snap.timestamp.strftime("%Y-%m-%d"),
                "score": snap.total_score,
                "category_scores": json.loads(snap.category_scores),
            }
            for snap in snapshots
        ]
    
    # Helper methods
    async def _enqueue_job(self, job_id: str, scheduled_time: datetime):
        """Add job to Redis sorted set for scheduling"""
        score = scheduled_time.timestamp()
        await self.redis.zadd("scheduled_migrations", {job_id: score})
    
    async def _dequeue_job(self, job_id: str):
        """Remove job from schedule"""
        await self.redis.zrem("scheduled_migrations", job_id)
    
    def _get_client_ip(self) -> str:
        """Get client IP from request context"""
        # Implementation depends on framework
        return "0.0.0.0"


# Report Generator

class ReportGenerator:
    """Generate compliance reports in various formats"""
    
    async def generate_pdf(
        self,
        project: 'Project',
        score: 'ComplianceScore',
        migrations: List['Migration'],
        include_details: bool = True,
    ) -> bytes:
        """Generate PDF compliance report"""
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from io import BytesIO
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []
        
        # Title
        elements.append(Paragraph(
            f"SDLC Compliance Report: {project.name}",
            styles['Title']
        ))
        elements.append(Spacer(1, 20))
        
        # Summary
        elements.append(Paragraph("Executive Summary", styles['Heading1']))
        summary_data = [
            ["Metric", "Value"],
            ["Overall Score", f"{score.total_score}%"],
            ["Grade", score.grade],
            ["Status", score.status],
            ["SDLC Version", project.sdlc_version],
            ["Total Files", str(project.total_files)],
        ]
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 20))
        
        # Category Breakdown
        elements.append(Paragraph("Category Scores", styles['Heading1']))
        category_data = [["Category", "Score"]]
        for category, cat_score in score.category_scores.items():
            category_data.append([category.title(), f"{cat_score:.1f}%"])
        
        category_table = Table(category_data)
        category_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(category_table)
        elements.append(Spacer(1, 20))
        
        # Violations (if include_details)
        if include_details and score.violations:
            elements.append(Paragraph("Violations", styles['Heading1']))
            violations_data = [["Rule", "Category", "File", "Message"]]
            
            for v in score.violations[:20]:  # First 20
                violations_data.append([
                    v.rule_id,
                    v.category.value,
                    str(v.file_path.name) if v.file_path else "N/A",
                    v.message[:50],
                ])
            
            violations_table = Table(violations_data)
            violations_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
            ]))
            elements.append(violations_table)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        return buffer.read()
    
    async def generate_excel(
        self,
        project: 'Project',
        score: 'ComplianceScore',
        migrations: List['Migration'],
    ) -> bytes:
        """Generate Excel compliance report"""
        import openpyxl
        from io import BytesIO
        
        wb = openpyxl.Workbook()
        
        # Summary sheet
        ws_summary = wb.active
        ws_summary.title = "Summary"
        ws_summary.append(["SDLC Compliance Report"])
        ws_summary.append([])
        ws_summary.append(["Project", project.name])
        ws_summary.append(["Overall Score", f"{score.total_score}%"])
        ws_summary.append(["Grade", score.grade])
        ws_summary.append(["SDLC Version", project.sdlc_version])
        
        # Category sheet
        ws_categories = wb.create_sheet("Categories")
        ws_categories.append(["Category", "Score"])
        for category, cat_score in score.category_scores.items():
            ws_categories.append([category, cat_score])
        
        # Violations sheet
        ws_violations = wb.create_sheet("Violations")
        ws_violations.append(["Rule", "Category", "File", "Message", "Severity"])
        for v in score.violations:
            ws_violations.append([
                v.rule_id,
                v.category.value,
                str(v.file_path) if v.file_path else "",
                v.message,
                v.severity,
            ])
        
        # Save to bytes
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        return buffer.read()
```

---

## Week 2: Testing & Documentation (May 26-30)

### Day 6-7: End-to-End Testing

**Task**: Complete E2E test coverage

```python
# tests/e2e/test_migration_workflow.py

import pytest
from playwright.sync_api import Page, expect
import subprocess
from pathlib import Path

class TestMigrationWorkflowE2E:
    """End-to-end tests for complete migration workflow"""
    
    @pytest.fixture
    def test_project(self, tmp_path):
        """Create test project with outdated SDLC docs"""
        # Clone template project
        subprocess.run([
            "git", "clone", "--depth", "1",
            "https://github.com/test/sdlc-template",
            str(tmp_path)
        ], check=True)
        
        # Modify docs to have outdated version
        for md_file in (tmp_path / "docs").rglob("*.md"):
            content = md_file.read_text()
            content = content.replace("5.1.0", "4.5.0")
            md_file.write_text(content)
        
        return tmp_path
    
    def test_complete_migration_flow(self, page: Page, test_project):
        """Test complete migration from UI"""
        
        # 1. Login
        page.goto("/login")
        page.fill("#email", "test@example.com")
        page.fill("#password", "password")
        page.click("button[type=submit]")
        expect(page).to_have_url("/dashboard")
        
        # 2. Create project
        page.click("text=New Project")
        page.fill("#project-name", "Test Migration Project")
        page.fill("#repo-url", str(test_project))
        page.click("button:has-text('Create')")
        
        # Wait for project creation
        expect(page.locator("text=Test Migration Project")).to_be_visible()
        
        # 3. Navigate to migrations
        page.click("text=Migrations")
        expect(page).to_have_url_matching(r"/migrations/.*")
        
        # 4. Check initial compliance score
        score_elem = page.locator("[data-testid=compliance-score]")
        expect(score_elem).to_be_visible()
        initial_score = float(score_elem.text_content().replace("%", ""))
        
        # Score should be less than 100 due to version mismatch
        assert initial_score < 100
        
        # 5. Start migration
        page.click("button:has-text('New Migration')")
        
        # Select target version
        page.select_option("#target-version", "5.1.0")
        
        # Start migration
        page.click("button:has-text('Start Migration')")
        
        # Wait for migration to complete
        expect(page.locator("text=Migration completed")).to_be_visible(timeout=60000)
        
        # 6. Verify improved score
        page.reload()
        new_score = float(page.locator("[data-testid=compliance-score]").text_content().replace("%", ""))
        
        assert new_score > initial_score
        
        # 7. Check migration history
        page.click("text=Migration History")
        
        history_row = page.locator("table tbody tr").first
        expect(history_row).to_contain_text("4.5.0 → 5.1.0")
        expect(history_row).to_contain_text("Success")
    
    def test_rollback_migration(self, page: Page, test_project):
        """Test migration rollback functionality"""
        
        # Setup: Create project and run migration
        # ... (similar to above)
        
        # Navigate to migration history
        page.goto("/migrations/test-project/history")
        
        # Click rollback on latest migration
        page.click("button:has-text('Rollback')")
        
        # Confirm rollback
        page.click("button:has-text('Confirm Rollback')")
        
        # Wait for rollback
        expect(page.locator("text=Rollback completed")).to_be_visible(timeout=30000)
        
        # Verify status changed to rolled_back
        expect(page.locator("table tbody tr").first).to_contain_text("Rolled Back")
    
    def test_export_compliance_report(self, page: Page):
        """Test report export functionality"""
        
        # Navigate to reports
        page.goto("/migrations/test-project")
        page.click("text=Export Report")
        
        # Select PDF format
        page.select_option("#format", "pdf")
        page.click("button:has-text('Generate')")
        
        # Wait for download
        with page.expect_download() as download_info:
            page.click("button:has-text('Download')")
        
        download = download_info.value
        assert download.suggested_filename.endswith(".pdf")
    
    def test_realtime_compliance_updates(self, page: Page, test_project):
        """Test real-time compliance score updates via WebSocket"""
        
        # Navigate to dashboard
        page.goto("/migrations/test-project")
        
        # Verify WebSocket connection
        ws_indicator = page.locator("[data-testid=ws-status]")
        expect(ws_indicator).to_have_text("Live")
        
        # Modify a file in the project
        readme = Path(test_project) / "docs" / "00-foundation" / "README.md"
        content = readme.read_text()
        content = content.replace("4.5.0", "5.1.0")
        readme.write_text(content)
        
        # Wait for score update
        page.wait_for_function("""
            () => {
                const score = document.querySelector('[data-testid=compliance-score]');
                return score && score.dataset.updated === 'true';
            }
        """, timeout=5000)
        
        # Score should have increased
        new_score = page.locator("[data-testid=compliance-score]").text_content()
        assert float(new_score.replace("%", "")) > 0


# CLI E2E Tests

class TestCLIE2E:
    """End-to-end tests for sdlcctl CLI"""
    
    def test_scan_command(self, test_project):
        """Test sdlcctl scan command"""
        result = subprocess.run(
            ["sdlcctl", "scan", str(test_project / "docs")],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "SDLC Versions Found" in result.stdout
        assert "4.5" in result.stdout or "5.1" in result.stdout
    
    def test_migrate_dry_run(self, test_project):
        """Test migration dry run"""
        result = subprocess.run(
            ["sdlcctl", "migrate", "run", str(test_project), "--mode", "dry-run"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "Dry run" in result.stdout
        assert "fixes" in result.stdout.lower()
    
    def test_migrate_with_backup(self, test_project):
        """Test migration creates backup"""
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=test_project, check=True)
        subprocess.run(["git", "add", "-A"], cwd=test_project, check=True)
        subprocess.run(["git", "commit", "-m", "Initial"], cwd=test_project, check=True)
        
        # Run migration
        result = subprocess.run(
            ["sdlcctl", "migrate", "run", str(test_project)],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "Backup" in result.stdout
        
        # Verify backup branch exists
        branches = subprocess.run(
            ["git", "branch", "-a"],
            cwd=test_project,
            capture_output=True,
            text=True
        )
        
        assert "sdlc-migration-backup" in branches.stdout
```

---

### Day 8-9: User Documentation

**Task**: Complete user guide and API documentation

```markdown
# SDLC Migration Engine User Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [CLI Usage](#cli-usage)
3. [Dashboard Guide](#dashboard-guide)
4. [Enterprise Features](#enterprise-features)
5. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites

- Python 3.10+
- Git repository
- SDLC documentation in `docs/` folder

### Installation

```bash
pip install sdlcctl
```

### Quick Start

```bash
# Scan your project
sdlcctl scan docs/

# Initialize config
sdlcctl init --project "My Project"

# Run migration
sdlcctl migrate run --mode dry-run
```

---

## CLI Usage

### Scan Command

Scan project for SDLC compliance:

```bash
# Basic scan
sdlcctl scan

# Scan specific folder
sdlcctl scan docs/

# Output as JSON
sdlcctl scan --output json

# Generate config from scan
sdlcctl scan --generate-config
```

### Migrate Command

Run SDLC version migration:

```bash
# Dry run (no changes)
sdlcctl migrate run --mode dry-run

# Interactive mode
sdlcctl migrate run --mode interactive

# Auto mode (applies all fixes)
sdlcctl migrate run --mode auto

# Skip backup (dangerous!)
sdlcctl migrate run --no-backup
```

### Backup Management

```bash
# List backups
sdlcctl migrate backups

# Rollback to backup
sdlcctl migrate rollback backup-20260520-143000
```

---

## Dashboard Guide

### Project Overview

The dashboard provides:
- Real-time compliance score
- Category breakdown (Header, Naming, Version, Reference, Stage)
- Migration history
- Trend charts

### Starting a Migration

1. Click "New Migration"
2. Select target SDLC version
3. Review migration plan
4. Click "Start Migration"
5. Monitor progress in real-time

### Rollback

1. Go to Migration History
2. Find the migration to rollback
3. Click "Rollback"
4. Confirm action

---

## Enterprise Features

Available for Enterprise tier:

### Audit Logging

All actions are logged:
- Migrations
- Rollbacks
- Configuration changes

View logs: Settings → Audit Logs

### Scheduled Migrations

Schedule migrations for off-hours:
1. Click "Schedule Migration"
2. Select date/time
3. Configure options
4. Confirm

### Custom Rules

Add organization-specific compliance rules:
1. Settings → Custom Rules
2. Click "Add Rule"
3. Define rule configuration
4. Enable/disable as needed

### Advanced Reporting

Generate PDF/Excel reports:
1. Click "Export Report"
2. Select format
3. Choose options
4. Download

---

## Troubleshooting

### Common Issues

**Q: Migration fails with "No backup branch"**
A: Ensure your project is a git repository with at least one commit.

**Q: Score doesn't update in real-time**
A: Check WebSocket connection (should show "Live" indicator).

**Q: High CPU usage during scan**
A: Large repositories may take longer. Consider excluding non-documentation folders.

### Support

- Documentation: https://docs.sdlc-orchestrator.io
- GitHub Issues: https://github.com/sdlc-orchestrator/issues
- Email: support@sdlc-orchestrator.io
```

---

### Day 10: Final Review & Release

**Task**: Sprint review and release preparation

**Release Checklist**:

- [ ] All tests passing (unit, integration, E2E)
- [ ] Documentation complete
- [ ] Performance benchmarks met
- [ ] Security review passed
- [ ] Code review completed
- [ ] Changelog updated
- [ ] Version bumped
- [ ] Docker images built
- [ ] Helm charts updated

---

## Deliverables

| # | Deliverable | Status |
|---|-------------|--------|
| 1 | Project management backend | ⏳ |
| 2 | Migration dashboard frontend | ⏳ |
| 3 | Enterprise features (audit, scheduling, reports) | ⏳ |
| 4 | E2E test suite | ⏳ |
| 5 | User documentation | ⏳ |
| 6 | API documentation | ⏳ |
| 7 | Release artifacts | ⏳ |

---

## EP-05 Completion Summary

### Sprint Overview

| Sprint | Focus | Duration | SP |
|--------|-------|----------|-----|
| 47 | Scanner & Config Generator | 2 weeks | 26 |
| 48 | Fixer & Backup Engine | 2 weeks | 24 |
| 49 | Real-Time Compliance | 2 weeks | 21 |
| 50 | Dashboard & Enterprise | 2 weeks | 18 |
| **Total** | | **8 weeks** | **89** |

### Key Deliverables

1. **ParallelScanner** - 18x faster than sequential
2. **ConfigGenerator** - 1KB config replaces 700KB manual docs
3. **Fixer Engine** - 15 automated fix types
4. **Backup System** - Git-integrated with rollback
5. **Real-Time Monitoring** - WebSocket updates
6. **Dashboard** - Multi-project support
7. **Enterprise Features** - Audit, scheduling, reports

### Success Metrics

| Metric | Target | Achieved |
|--------|--------|----------|
| 10K files scan | <5 min | TBD |
| Fix accuracy | ≥95% | TBD |
| Score accuracy | 100% | TBD |
| E2E coverage | ≥90% | TBD |

---

*Sprint planned: December 21, 2025*
*CTO Approval: Pending*
*Epic Completion: May 30, 2026*
