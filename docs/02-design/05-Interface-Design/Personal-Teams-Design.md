# Personal Teams Feature - Design Document

**Document Status:** Draft - Awaiting CTO Approval  
**Version:** 1.0  
**Date:** January 19, 2026  
**Author:** Development Team  
**SDLC Phase:** 02-Design

---

## Executive Summary

This design introduces **Personal Teams** alongside existing **Organization Teams**, enabling individual users to create and manage teams without organization affiliation. This feature democratizes team creation while maintaining clear ownership boundaries and subscription-based access control.

**Key Change:** Users can now own personal teams directly, while organization teams remain organization-owned.

---

## Table of Contents

1. [Background & Motivation](#background--motivation)
2. [Team Ownership Model](#team-ownership-model)
3. [Database Schema Changes](#database-schema-changes)
4. [API Changes](#api-changes)
5. [Frontend Changes](#frontend-changes)
6. [Subscription Tiers](#subscription-tiers)
7. [Security & Access Control](#security--access-control)
8. [Migration Strategy](#migration-strategy)
9. [Testing Strategy](#testing-strategy)
10. [Rollout Plan](#rollout-plan)
11. [Open Questions](#open-questions)

---

## Background & Motivation

### Current State

- **Organization Teams Only:** All teams must belong to an organization
- **Barrier to Entry:** Individual users cannot create teams without organization setup
- **User Feedback:** Requests for personal project management capabilities

### Desired State

- **Dual Ownership Model:** Support both personal and organization teams
- **Flexible Team Creation:** Users can create teams for personal projects
- **Clear Boundaries:** Explicit ownership model prevents ambiguity

### Business Value

- **Increased Adoption:** Lower barrier to entry for individual users
- **Freemium Funnel:** Personal teams as gateway to organization upgrades
- **Competitive Parity:** Match GitHub's personal vs. organization repositories model

---

## Team Ownership Model

### Two Team Types

#### 1. Personal Team
```
{
  "id": "uuid-123",
  "name": "John's Personal Team",
  "slug": "john-personal-team",
  "organization_id": NULL,           // ← Key difference
  "owner_id": "user-uuid-456",       // ← Key difference
  "is_personal": true,
  "subscription_tier": "free"
}
```

**Characteristics:**
- `organization_id` = `NULL`
- `owner_id` = User UUID
- Owner has full administrative control
- Cannot be transferred to another user
- Tied to user's subscription tier

#### 2. Organization Team
```
{
  "id": "uuid-789",
  "name": "Acme Corp Engineering",
  "slug": "acme-engineering",
  "organization_id": "org-uuid-101",  // ← Key difference
  "owner_id": NULL,                   // ← Key difference
  "is_personal": false,
  "subscription_tier": "pro"
}
```

**Characteristics:**
- `organization_id` = Organization UUID
- `owner_id` = `NULL`
- Managed by organization administrators
- Can be transferred between organizations
- Tied to organization's subscription tier

### Ownership Rules

| Property | Personal Team | Organization Team |
|----------|--------------|-------------------|
| `organization_id` | `NULL` | Organization UUID |
| `owner_id` | User UUID | `NULL` |
| Admin | Owner only | Org admins |
| Transfer | Not allowed | Allowed |
| Subscription | User's tier | Org's tier |

**Constraint:** Exactly one of `organization_id` OR `owner_id` must be set (XOR relationship).

---

## Database Schema Changes

### 1. Modify `teams` Table

```sql
-- Add owner_id column
ALTER TABLE teams 
ADD COLUMN owner_id UUID NULL 
REFERENCES users(id) ON DELETE CASCADE;

-- Make organization_id nullable
ALTER TABLE teams 
ALTER COLUMN organization_id DROP NOT NULL;

-- Add XOR constraint: Either organization_id OR owner_id must be set
ALTER TABLE teams 
ADD CONSTRAINT check_team_ownership 
CHECK (
  (organization_id IS NOT NULL AND owner_id IS NULL) OR
  (organization_id IS NULL AND owner_id IS NOT NULL)
);

-- Add index for personal team queries
CREATE INDEX idx_teams_owner_id ON teams(owner_id) 
WHERE owner_id IS NOT NULL;

-- Add composite index for organization teams
CREATE INDEX idx_teams_org_id ON teams(organization_id) 
WHERE organization_id IS NOT NULL;
```

### 2. Updated Schema Definition

```python
# backend/app/models/team.py

class Team(Base):
    __tablename__ = "teams"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    
    # Ownership fields (XOR relationship)
    organization_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True  # ← Changed from False
    )
    owner_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True  # ← New field
    )
    
    subscription_tier = Column(String(50), nullable=False, default="free")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="teams")
    owner = relationship("User", back_populates="personal_teams")  # ← New
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "(organization_id IS NOT NULL AND owner_id IS NULL) OR "
            "(organization_id IS NULL AND owner_id IS NOT NULL)",
            name="check_team_ownership"
        ),
    )
    
    @property
    def is_personal(self) -> bool:
        """Check if this is a personal team."""
        return self.owner_id is not None
```

### 3. Migration Script

```python
# backend/alembic/versions/YYYYMMDD_add_personal_teams.py

"""Add personal teams support

Revision ID: add_personal_teams
Revises: previous_migration
Create Date: 2026-01-19
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'add_personal_teams'
down_revision = 'previous_migration'
branch_labels = None
depends_on = None

def upgrade():
    # Add owner_id column
    op.add_column('teams', 
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    
    # Make organization_id nullable
    op.alter_column('teams', 'organization_id',
        existing_type=postgresql.UUID(),
        nullable=True
    )
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_teams_owner_id_users', 
        'teams', 
        'users',
        ['owner_id'], 
        ['id'],
        ondelete='CASCADE'
    )
    
    # Add XOR constraint
    op.create_check_constraint(
        'check_team_ownership',
        'teams',
        "(organization_id IS NOT NULL AND owner_id IS NULL) OR "
        "(organization_id IS NULL AND owner_id IS NOT NULL)"
    )
    
    # Add indexes
    op.create_index(
        'idx_teams_owner_id', 
        'teams', 
        ['owner_id'],
        postgresql_where=sa.text('owner_id IS NOT NULL')
    )
    
    op.create_index(
        'idx_teams_org_id',
        'teams',
        ['organization_id'],
        postgresql_where=sa.text('organization_id IS NOT NULL')
    )

def downgrade():
    # Drop indexes
    op.drop_index('idx_teams_org_id', table_name='teams')
    op.drop_index('idx_teams_owner_id', table_name='teams')
    
    # Drop constraint
    op.drop_constraint('check_team_ownership', 'teams', type_='check')
    
    # Drop foreign key
    op.drop_constraint('fk_teams_owner_id_users', 'teams', type_='foreignkey')
    
    # Make organization_id non-nullable
    op.alter_column('teams', 'organization_id',
        existing_type=postgresql.UUID(),
        nullable=False
    )
    
    # Drop owner_id column
    op.drop_column('teams', 'owner_id')
```

---

## API Changes

### 1. POST /teams - Create Team

**Request Changes:**

```typescript
// Before: organization_id was required
{
  "name": "Team Name",
  "slug": "team-slug",
  "organization_id": "org-uuid-123"  // Required
}

// After: organization_id is optional
{
  "name": "Team Name",
  "slug": "team-slug",
  "organization_id": "org-uuid-123"  // Optional
}
```

**Logic:**

```python
# backend/app/api/routes/teams.py

@router.post("/teams", response_model=TeamResponse, status_code=201)
async def create_team(
    team_data: TeamCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new team (personal or organization).
    
    - If organization_id provided: Create organization team (requires org admin)
    - If organization_id omitted: Create personal team (owned by current user)
    """
    
    # Validate slug uniqueness
    existing_team = db.query(Team).filter(Team.slug == team_data.slug).first()
    if existing_team:
        raise HTTPException(
            status_code=400,
            detail=f"Team slug '{team_data.slug}' is already taken"
        )
    
    if team_data.organization_id:
        # Organization team path
        # Verify user is org admin
        org = db.query(Organization).filter(
            Organization.id == team_data.organization_id
        ).first()
        
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        if not is_org_admin(current_user, org):
            raise HTTPException(
                status_code=403, 
                detail="Only organization admins can create organization teams"
            )
        
        team = Team(
            name=team_data.name,
            slug=team_data.slug,
            description=team_data.description,
            organization_id=org.id,
            owner_id=None,
            subscription_tier=org.subscription_tier
        )
    else:
        # Personal team path
        # Check user's personal team limit based on subscription
        personal_team_count = db.query(Team).filter(
            Team.owner_id == current_user.id
        ).count()
        
        max_personal_teams = get_max_personal_teams(current_user.subscription_tier)
        if personal_team_count >= max_personal_teams:
            raise HTTPException(
                status_code=403,
                detail=f"Personal team limit reached ({max_personal_teams}). "
                       f"Upgrade subscription for more teams."
            )
        
        team = Team(
            name=team_data.name,
            slug=team_data.slug,
            description=team_data.description,
            organization_id=None,
            owner_id=current_user.id,
            subscription_tier=current_user.subscription_tier
        )
    
    db.add(team)
    db.commit()
    db.refresh(team)
    
    return team
```

**Response Changes:**

```typescript
// Response now includes owner_id and is_personal
{
  "id": "uuid-123",
  "name": "Team Name",
  "slug": "team-slug",
  "organization_id": null,           // ← Can be null
  "owner_id": "user-uuid-456",       // ← New field
  "is_personal": true,               // ← New computed field
  "subscription_tier": "free",
  "created_at": "2026-01-19T10:00:00Z",
  "updated_at": "2026-01-19T10:00:00Z"
}
```

### 2. GET /teams - List Teams

**Query Parameters:**

```typescript
// New filter options
GET /teams?type=personal       // Only personal teams
GET /teams?type=organization   // Only organization teams
GET /teams                     // All teams user has access to
```

**Implementation:**

```python
@router.get("/teams", response_model=List[TeamResponse])
async def list_teams(
    type: Optional[str] = None,  # "personal" | "organization"
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List teams accessible to the current user.
    
    - Personal teams owned by user
    - Organization teams where user is member or org admin
    """
    
    query = db.query(Team)
    
    if type == "personal":
        query = query.filter(Team.owner_id == current_user.id)
    elif type == "organization":
        # Get orgs where user is member/admin
        user_org_ids = [org.id for org in current_user.organizations]
        query = query.filter(Team.organization_id.in_(user_org_ids))
    else:
        # All accessible teams
        user_org_ids = [org.id for org in current_user.organizations]
        query = query.filter(
            (Team.owner_id == current_user.id) |
            (Team.organization_id.in_(user_org_ids))
        )
    
    teams = query.all()
    return teams
```

### 3. Updated Pydantic Schemas

```python
# backend/app/schemas/team.py

from pydantic import BaseModel, Field, validator
from typing import Optional
from uuid import UUID
from datetime import datetime

class TeamCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255, regex=r'^[a-z0-9-]+$')
    description: Optional[str] = None
    organization_id: Optional[UUID] = None  # ← Now optional
    
    @validator('slug')
    def validate_slug(cls, v):
        if not v.islower():
            raise ValueError('Slug must be lowercase')
        if '__' in v or v.startswith('-') or v.endswith('-'):
            raise ValueError('Invalid slug format')
        return v

class TeamResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: Optional[str]
    organization_id: Optional[UUID]  # ← Can be null
    owner_id: Optional[UUID]         # ← New field
    is_personal: bool                # ← New computed field
    subscription_tier: str
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        orm_mode = True
```

---

## Frontend Changes

### 1. CreateTeamDialog Component

**Updated UI:**

```typescript
// frontend/web/src/components/teams/CreateTeamDialog.tsx

import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  RadioGroup,
  FormControlLabel,
  Radio,
  FormLabel,
  Alert,
  Select,
  MenuItem,
  FormHelperText
} from '@mui/material';

interface CreateTeamDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess: (team: Team) => void;
  userOrganizations: Organization[];
}

export const CreateTeamDialog: React.FC<CreateTeamDialogProps> = ({
  open,
  onClose,
  onSuccess,
  userOrganizations
}) => {
  const [teamType, setTeamType] = useState<'personal' | 'organization'>('personal');
  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');
  const [description, setDescription] = useState('');
  const [organizationId, setOrganizationId] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  
  const handleNameChange = (value: string) => {
    setName(value);
    // Auto-generate slug from name
    const generatedSlug = value
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '');
    setSlug(generatedSlug);
  };
  
  const handleSubmit = async () => {
    setErrors({});
    
    try {
      const payload: TeamCreatePayload = {
        name,
        slug,
        description: description || undefined,
        organization_id: teamType === 'organization' ? organizationId : undefined
      };
      
      const response = await fetch('/api/teams', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      if (!response.ok) {
        const error = await response.json();
        
        // Handle slug conflict with clear message
        if (response.status === 400 && error.detail?.includes('already taken')) {
          setErrors({ slug: error.detail });
          return;
        }
        
        // Handle personal team limit
        if (response.status === 403 && error.detail?.includes('limit reached')) {
          setErrors({ general: error.detail });
          return;
        }
        
        throw new Error(error.detail || 'Failed to create team');
      }
      
      const team = await response.json();
      onSuccess(team);
      onClose();
      resetForm();
    } catch (error) {
      setErrors({ general: error.message });
    }
  };
  
  const resetForm = () => {
    setTeamType('personal');
    setName('');
    setSlug('');
    setDescription('');
    setOrganizationId('');
    setErrors({});
  };
  
  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Create New Team</DialogTitle>
      <DialogContent>
        {errors.general && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {errors.general}
          </Alert>
        )}
        
        {/* Team Type Selection */}
        <FormLabel component="legend" sx={{ mt: 2, mb: 1 }}>
          Team Type
        </FormLabel>
        <RadioGroup
          value={teamType}
          onChange={(e) => setTeamType(e.target.value as 'personal' | 'organization')}
        >
          <FormControlLabel
            value="personal"
            control={<Radio />}
            label="Personal Team - Owned by you, for personal projects"
          />
          <FormControlLabel
            value="organization"
            control={<Radio />}
            label="Organization Team - Managed by organization admins"
            disabled={userOrganizations.length === 0}
          />
        </RadioGroup>
        
        {userOrganizations.length === 0 && teamType === 'organization' && (
          <FormHelperText>
            You need to be a member of an organization to create organization teams.
          </FormHelperText>
        )}
        
        {/* Organization Selection (only for org teams) */}
        {teamType === 'organization' && userOrganizations.length > 0 && (
          <Select
            fullWidth
            value={organizationId}
            onChange={(e) => setOrganizationId(e.target.value)}
            displayEmpty
            sx={{ mt: 2 }}
          >
            <MenuItem value="" disabled>
              Select Organization
            </MenuItem>
            {userOrganizations.map((org) => (
              <MenuItem key={org.id} value={org.id}>
                {org.name}
              </MenuItem>
            ))}
          </Select>
        )}
        
        {/* Team Name */}
        <TextField
          fullWidth
          label="Team Name"
          value={name}
          onChange={(e) => handleNameChange(e.target.value)}
          margin="normal"
          required
          helperText="A descriptive name for your team"
        />
        
        {/* Team Slug */}
        <TextField
          fullWidth
          label="Team Slug"
          value={slug}
          onChange={(e) => setSlug(e.target.value)}
          margin="normal"
          required
          error={!!errors.slug}
          helperText={
            errors.slug || 
            "Unique identifier (lowercase, numbers, hyphens only). Used in URLs."
          }
        />
        
        {/* Description */}
        <TextField
          fullWidth
          label="Description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          margin="normal"
          multiline
          rows={3}
          helperText="Optional description of the team's purpose"
        />
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={
            !name || 
            !slug || 
            (teamType === 'organization' && !organizationId)
          }
        >
          Create Team
        </Button>
      </DialogActions>
    </Dialog>
  );
};
```

### 2. Team List Component

**Show Ownership Badge:**

```typescript
// frontend/web/src/components/teams/TeamCard.tsx

export const TeamCard: React.FC<{ team: Team }> = ({ team }) => {
  return (
    <Card>
      <CardHeader
        title={
          <Box display="flex" alignItems="center" gap={1}>
            <Typography variant="h6">{team.name}</Typography>
            {team.is_personal ? (
              <Chip 
                label="Personal" 
                size="small" 
                color="primary" 
                icon={<PersonIcon />}
              />
            ) : (
              <Chip 
                label="Organization" 
                size="small" 
                color="secondary"
                icon={<BusinessIcon />}
              />
            )}
          </Box>
        }
        subheader={`@${team.slug}`}
      />
      <CardContent>
        <Typography variant="body2" color="text.secondary">
          {team.description || 'No description'}
        </Typography>
        
        {team.is_personal && (
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
            Owner: You
          </Typography>
        )}
      </CardContent>
    </Card>
  );
};
```

### 3. Slug Validation with Error Messages

**Client-Side Validation:**

```typescript
// frontend/web/src/utils/validation.ts

export const validateTeamSlug = (slug: string): string | null => {
  if (!slug) {
    return 'Slug is required';
  }
  
  if (slug.length < 3) {
    return 'Slug must be at least 3 characters';
  }
  
  if (slug.length > 255) {
    return 'Slug must be less than 255 characters';
  }
  
  if (!/^[a-z0-9-]+$/.test(slug)) {
    return 'Slug can only contain lowercase letters, numbers, and hyphens';
  }
  
  if (slug.startsWith('-') || slug.endsWith('-')) {
    return 'Slug cannot start or end with a hyphen';
  }
  
  if (slug.includes('--')) {
    return 'Slug cannot contain consecutive hyphens';
  }
  
  // Reserved slugs
  const reserved = ['admin', 'api', 'settings', 'dashboard', 'new', 'create'];
  if (reserved.includes(slug)) {
    return `Slug "${slug}" is reserved`;
  }
  
  return null; // Valid
};
```

**Real-Time Validation:**

```typescript
// In CreateTeamDialog component

const [slugError, setSlugError] = useState<string | null>(null);
const [isCheckingSlug, setIsCheckingSlug] = useState(false);

// Debounced slug availability check
useEffect(() => {
  if (!slug) {
    setSlugError(null);
    return;
  }
  
  const validationError = validateTeamSlug(slug);
  if (validationError) {
    setSlugError(validationError);
    return;
  }
  
  const timer = setTimeout(async () => {
    setIsCheckingSlug(true);
    try {
      const response = await fetch(`/api/teams/check-slug/${slug}`);
      const data = await response.json();
      
      if (data.available) {
        setSlugError(null);
      } else {
        setSlugError(`Slug "${slug}" is already taken. Try: ${data.suggestions.join(', ')}`);
      }
    } catch (error) {
      console.error('Slug check failed:', error);
    } finally {
      setIsCheckingSlug(false);
    }
  }, 500); // 500ms debounce
  
  return () => clearTimeout(timer);
}, [slug]);
```

---

## Subscription Tiers

### Tier Definitions

All organizations and users share the same tier structure (no separate "Enterprise" tier):

```typescript
// backend/app/models/subscription.py

from enum import Enum

class SubscriptionTier(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"

# Tier limits for personal teams
PERSONAL_TEAM_LIMITS = {
    SubscriptionTier.FREE: 1,        # 1 personal team
    SubscriptionTier.STARTER: 3,     # 3 personal teams
    SubscriptionTier.PRO: 10,        # 10 personal teams
    SubscriptionTier.ENTERPRISE: 50  # 50 personal teams
}

# Tier limits for organization teams
ORG_TEAM_LIMITS = {
    SubscriptionTier.FREE: 3,        # 3 teams per org
    SubscriptionTier.STARTER: 10,    # 10 teams per org
    SubscriptionTier.PRO: 50,        # 50 teams per org
    SubscriptionTier.ENTERPRISE: -1  # Unlimited
}

# Member limits per team
TEAM_MEMBER_LIMITS = {
    SubscriptionTier.FREE: 5,        # 5 members
    SubscriptionTier.STARTER: 15,    # 15 members
    SubscriptionTier.PRO: 50,        # 50 members
    SubscriptionTier.ENTERPRISE: -1  # Unlimited
}
```

### Tier Comparison Table

| Feature | Free | Starter | Pro | Enterprise |
|---------|------|---------|-----|------------|
| **Personal Teams** | 1 | 3 | 10 | 50 |
| **Organization Teams** | 3 | 10 | 50 | Unlimited |
| **Members per Team** | 5 | 15 | 50 | Unlimited |
| **Storage** | 1 GB | 10 GB | 100 GB | Unlimited |
| **API Rate Limit** | 60/hour | 300/hour | 1000/hour | Unlimited |
| **Support** | Community | Email | Priority | Dedicated |
| **Price** | $0 | $10/month | $50/month | Custom |

### Key Differences from GitHub

**Our Model:**
- ✅ All organizations are equal (free, starter, pro, enterprise)
- ✅ No separate "GitHub Enterprise" product
- ✅ Simpler pricing: One tier list applies to all

**GitHub's Model:**
- ❌ Separate products: GitHub.com vs. GitHub Enterprise Server
- ❌ Enterprise has different features entirely (SAML, LDAP, etc.)
- ❌ More complex pricing structure

**Why Our Approach:**
- **Simplicity:** Easier to understand and communicate
- **Flexibility:** Organizations can upgrade/downgrade seamlessly
- **Fair Access:** Same features available to all, just different limits

---

## Security & Access Control

### Authorization Rules

#### Personal Teams

```python
def can_manage_personal_team(user: User, team: Team) -> bool:
    """Only the owner can manage a personal team."""
    return team.owner_id == user.id

def can_view_personal_team(user: User, team: Team) -> bool:
    """Owner + members can view personal team."""
    return (
        team.owner_id == user.id or
        user.id in [member.user_id for member in team.members]
    )
```

#### Organization Teams

```python
def can_manage_org_team(user: User, team: Team) -> bool:
    """Organization admins can manage org teams."""
    if not team.organization_id:
        return False
    
    org = team.organization
    return is_org_admin(user, org)

def can_view_org_team(user: User, team: Team) -> bool:
    """Organization members + team members can view org teams."""
    if not team.organization_id:
        return False
    
    org = team.organization
    return (
        user in org.members or
        user.id in [member.user_id for member in team.members]
    )
```

### Ownership Transfer

**Personal Teams:** ❌ Cannot be transferred (tied to user)

**Organization Teams:** ✅ Can be transferred between organizations

```python
@router.patch("/teams/{team_id}/transfer")
async def transfer_team(
    team_id: UUID,
    transfer_data: TeamTransfer,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Transfer organization team to another organization."""
    
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404)
    
    # Only organization teams can be transferred
    if team.is_personal:
        raise HTTPException(
            status_code=400,
            detail="Personal teams cannot be transferred"
        )
    
    # Verify user is admin of source org
    if not can_manage_org_team(current_user, team):
        raise HTTPException(status_code=403)
    
    # Verify user is admin of target org
    target_org = db.query(Organization).filter(
        Organization.id == transfer_data.target_organization_id
    ).first()
    
    if not is_org_admin(current_user, target_org):
        raise HTTPException(
            status_code=403,
            detail="Must be admin of target organization"
        )
    
    # Transfer
    team.organization_id = target_org.id
    team.subscription_tier = target_org.subscription_tier
    db.commit()
    
    return {"message": "Team transferred successfully"}
```

---

## Migration Strategy

### Phase 1: Database Migration (Day 0)

**Goal:** Update schema without breaking existing functionality

**Steps:**
1. Run migration to add `owner_id` column (nullable)
2. Make `organization_id` nullable
3. Add XOR constraint
4. Add indexes

**Validation:**
```sql
-- Verify all existing teams still have organization_id set
SELECT COUNT(*) FROM teams WHERE organization_id IS NULL;
-- Expected: 0

-- Verify constraint is working
INSERT INTO teams (name, slug, organization_id, owner_id) 
VALUES ('Test', 'test', NULL, NULL);
-- Expected: ERROR (constraint violation)
```

### Phase 2: Backend Deployment (Day 1)

**Goal:** Deploy API changes with backward compatibility

**Changes:**
- Updated models with `owner_id` and `is_personal`
- Updated API endpoints (organization_id optional)
- New authorization logic

**Backward Compatibility:**
- Existing API calls with `organization_id` still work
- New API calls without `organization_id` create personal teams

**Testing:**
```bash
# Test existing organization team creation
curl -X POST /api/teams \
  -H "Content-Type: application/json" \
  -d '{"name": "Org Team", "slug": "org-team", "organization_id": "org-123"}'
# Expected: 201 Created

# Test new personal team creation
curl -X POST /api/teams \
  -H "Content-Type: application/json" \
  -d '{"name": "Personal Team", "slug": "personal-team"}'
# Expected: 201 Created (owner_id = current user)
```

### Phase 3: Frontend Deployment (Day 2-3)

**Goal:** Update UI to support personal teams

**Changes:**
- Updated CreateTeamDialog with team type selection
- Updated TeamCard to show ownership badges
- Slug validation with error messages

**Feature Flag:**
```typescript
// Control rollout with feature flag
const PERSONAL_TEAMS_ENABLED = getFeatureFlag('personal_teams');

if (PERSONAL_TEAMS_ENABLED) {
  // Show "Personal Team" option in dialog
} else {
  // Force organization_id requirement (old behavior)
}
```

### Phase 4: Monitoring & Validation (Day 4-7)

**Metrics to Track:**
- Personal team creation rate
- Organization team creation rate (should not decrease)
- API error rate (slug conflicts, limit errors)
- User upgrade conversions (personal team limit → upgrade)

**Rollback Plan:**
- Revert frontend to force organization_id
- Keep database schema (owner_id unused but not breaking)
- No data loss (all teams remain accessible)

---

## Testing Strategy

### Unit Tests

**Model Tests:**
```python
# tests/unit/test_team_model.py

def test_personal_team_constraint():
    """Test that personal team must have owner_id."""
    team = Team(
        name="Personal",
        slug="personal",
        organization_id=None,
        owner_id=None  # Invalid
    )
    with pytest.raises(IntegrityError):
        db.add(team)
        db.commit()

def test_org_team_constraint():
    """Test that org team must have organization_id."""
    team = Team(
        name="Org",
        slug="org",
        organization_id=None,  # Invalid
        owner_id=None
    )
    with pytest.raises(IntegrityError):
        db.add(team)
        db.commit()

def test_is_personal_property():
    """Test is_personal computed property."""
    personal = Team(owner_id="user-123", organization_id=None)
    assert personal.is_personal is True
    
    org = Team(owner_id=None, organization_id="org-123")
    assert org.is_personal is False
```

### Integration Tests

**API Tests:**
```python
# tests/integration/test_team_api.py

def test_create_personal_team(client, auth_headers):
    """Test creating a personal team."""
    response = client.post(
        "/api/teams",
        json={"name": "My Team", "slug": "my-team"},
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["owner_id"] is not None
    assert data["organization_id"] is None
    assert data["is_personal"] is True

def test_create_org_team(client, auth_headers, org_id):
    """Test creating an organization team."""
    response = client.post(
        "/api/teams",
        json={
            "name": "Org Team",
            "slug": "org-team",
            "organization_id": org_id
        },
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["owner_id"] is None
    assert data["organization_id"] == org_id
    assert data["is_personal"] is False

def test_slug_conflict_error(client, auth_headers):
    """Test slug uniqueness validation."""
    # Create first team
    client.post(
        "/api/teams",
        json={"name": "Team 1", "slug": "duplicate"},
        headers=auth_headers
    )
    
    # Try to create second team with same slug
    response = client.post(
        "/api/teams",
        json={"name": "Team 2", "slug": "duplicate"},
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "already taken" in response.json()["detail"]

def test_personal_team_limit(client, auth_headers, free_tier_user):
    """Test personal team limit enforcement."""
    # Create max allowed teams (1 for free tier)
    client.post(
        "/api/teams",
        json={"name": "Team 1", "slug": "team-1"},
        headers=auth_headers
    )
    
    # Try to create one more
    response = client.post(
        "/api/teams",
        json={"name": "Team 2", "slug": "team-2"},
        headers=auth_headers
    )
    
    assert response.status_code == 403
    assert "limit reached" in response.json()["detail"]
```

### Frontend Tests

**Component Tests:**
```typescript
// tests/components/CreateTeamDialog.test.tsx

describe('CreateTeamDialog', () => {
  it('defaults to personal team type', () => {
    const { getByLabelText } = render(<CreateTeamDialog {...props} />);
    
    const personalRadio = getByLabelText(/Personal Team/i) as HTMLInputElement;
    expect(personalRadio.checked).toBe(true);
  });
  
  it('does not send organization_id for personal teams', async () => {
    const { getByLabelText, getByText } = render(<CreateTeamDialog {...props} />);
    
    // Select personal team
    const personalRadio = getByLabelText(/Personal Team/i);
    fireEvent.click(personalRadio);
    
    // Fill form
    const nameInput = getByLabelText(/Team Name/i);
    fireEvent.change(nameInput, { target: { value: 'My Team' } });
    
    // Submit
    const createButton = getByText('Create Team');
    fireEvent.click(createButton);
    
    // Verify API call
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/api/teams', {
        method: 'POST',
        body: expect.not.stringContaining('organization_id')
      });
    });
  });
  
  it('shows slug conflict error', async () => {
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: async () => ({ detail: "Team slug 'duplicate' is already taken" })
    });
    
    const { getByLabelText, getByText, findByText } = render(<CreateTeamDialog {...props} />);
    
    // Fill and submit form
    fireEvent.change(getByLabelText(/Team Name/i), { target: { value: 'Test' } });
    fireEvent.change(getByLabelText(/Team Slug/i), { target: { value: 'duplicate' } });
    fireEvent.click(getByText('Create Team'));
    
    // Verify error message
    const errorMessage = await findByText(/already taken/i);
    expect(errorMessage).toBeInTheDocument();
  });
});
```

### E2E Tests

**User Flow:**
```typescript
// tests/e2e/personal-teams.spec.ts

describe('Personal Teams', () => {
  it('should allow creating and managing personal teams', async () => {
    // Login
    await page.goto('/login');
    await page.fill('[name="email"]', 'user@example.com');
    await page.fill('[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    
    // Navigate to teams page
    await page.goto('/teams');
    
    // Open create dialog
    await page.click('button:has-text("Create Team")');
    
    // Select personal team
    await page.click('label:has-text("Personal Team")');
    
    // Fill form
    await page.fill('[name="name"]', 'My Personal Team');
    await page.fill('[name="slug"]', 'my-personal-team');
    await page.fill('[name="description"]', 'A team for my projects');
    
    // Submit
    await page.click('button:has-text("Create Team")');
    
    // Verify team created
    await expect(page.locator('text=My Personal Team')).toBeVisible();
    await expect(page.locator('text=Personal')).toBeVisible(); // Badge
    
    // Verify team in list
    await page.goto('/teams');
    await expect(page.locator('text=My Personal Team')).toBeVisible();
  });
});
```

---

## Rollout Plan

### Timeline

| Phase | Duration | Status | Description |
|-------|----------|--------|-------------|
| **CTO Approval** | Day 0 | ⏳ Pending | This design document review |
| **Database Migration** | Day 1 | ⏸️ | Schema changes, constraint validation |
| **Backend Development** | Day 2-3 | ⏸️ | API changes, authorization logic |
| **Frontend Development** | Day 4-6 | ⏸️ | UI components, slug validation |
| **Testing** | Day 7-8 | ⏸️ | Unit, integration, E2E tests |
| **Staging Deployment** | Day 9 | ⏸️ | Deploy to staging, smoke tests |
| **Internal Beta** | Day 10-12 | ⏸️ | 20 internal users test personal teams |
| **Production Rollout** | Day 13 | ⏸️ | Feature flag: 10% → 50% → 100% |
| **Monitoring** | Day 14-20 | ⏸️ | Track metrics, collect feedback |

### Feature Flag Configuration

```typescript
// Feature flag for gradual rollout
{
  "personal_teams": {
    "enabled": true,
    "rollout_percentage": 10,  // Start with 10% of users
    "allowed_user_ids": [
      "internal-user-1",
      "internal-user-2"
    ],
    "allowed_orgs": [
      "internal-org-1"
    ]
  }
}
```

### Success Metrics

**Adoption Metrics:**
- Personal teams created (target: 100 in first week)
- Personal team vs. org team ratio (expect 60/40)
- User upgrade rate (personal team limit → paid tier)

**Quality Metrics:**
- API error rate < 1% (slug conflicts, limits)
- P95 response time < 200ms for team creation
- Zero data loss incidents
- Zero downtime during rollout

**User Satisfaction:**
- NPS score > 40 for personal teams feature
- <5% users reverting to organization-only teams
- Positive feedback in user surveys

### Rollback Criteria

**Trigger rollback if:**
- API error rate > 5%
- >10 user complaints about data loss
- P95 response time > 1s for team operations
- CTO requests halt due to security concerns

**Rollback Process:**
1. Disable feature flag (users see old UI)
2. Backend still works (organization teams unaffected)
3. No data migration needed (owner_id column remains)
4. Fix issues, then re-enable feature flag

---

## Open Questions

### 1. Team Deletion for Personal Teams

**Question:** When a user deletes their account, should personal teams be:
- (A) Deleted permanently?
- (B) Transferred to another user?
- (C) Archived for 30 days?

**Recommendation:** (A) Delete permanently with cascade (simpler, clearer ownership).

**Decision:** ⏳ Awaiting CTO input

---

### 2. Personal Team Member Invites

**Question:** Can personal team owners invite members from any domain, or restrict to specific domains?

**Recommendation:** Allow any domain (simpler), add domain restriction later if needed.

**Decision:** ⏳ Awaiting CTO input

---

### 3. Organization Inheritance for Personal Teams

**Question:** If a user is in multiple orgs, which org's subscription tier applies to their personal teams?

**Current Design:** User's own subscription tier (independent of orgs)

**Alternative:** Use highest org tier the user is in (more generous)

**Decision:** ⏳ Awaiting CTO input

---

### 4. Slug Namespace Collision

**Question:** Should personal and org teams share the same slug namespace?

**Current Design:** Yes (globally unique slugs)

**Alternative:** Namespaced slugs (`@username/slug` vs. `@org/slug`)

**Recommendation:** Keep globally unique (simpler URLs), revisit if collisions become frequent.

**Decision:** ⏳ Awaiting CTO input

---

### 5. Team Limits Enforcement

**Question:** What happens when a user downgrades subscription and exceeds new personal team limit?

**Options:**
- (A) Prevent downgrade until teams deleted
- (B) Archive excess teams (read-only)
- (C) Allow temporary overage with warning

**Recommendation:** (B) Archive excess teams (most user-friendly).

**Decision:** ⏳ Awaiting CTO input

---

## Appendix A: API Endpoints Summary

### New Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/teams` | Create personal or org team (organization_id optional) |
| GET | `/api/teams` | List teams (filter by type: personal/organization) |
| GET | `/api/teams/{id}` | Get team details (includes owner_id, is_personal) |
| GET | `/api/teams/check-slug/{slug}` | Check slug availability + suggestions |
| PATCH | `/api/teams/{id}/transfer` | Transfer org team to another org |

### Updated Schemas

**TeamCreate:**
```json
{
  "name": "string",
  "slug": "string",
  "description": "string?",
  "organization_id": "uuid?"  // ← Now optional
}
```

**TeamResponse:**
```json
{
  "id": "uuid",
  "name": "string",
  "slug": "string",
  "description": "string?",
  "organization_id": "uuid?",  // ← Can be null
  "owner_id": "uuid?",         // ← New
  "is_personal": "boolean",    // ← New
  "subscription_tier": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

## Appendix B: Database Schema Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         teams                               │
├─────────────────────────────────────────────────────────────┤
│ id                  UUID PRIMARY KEY                         │
│ name                VARCHAR(255) NOT NULL                    │
│ slug                VARCHAR(255) UNIQUE NOT NULL             │
│ description         TEXT                                     │
│ organization_id     UUID REFERENCES organizations(id) NULL   │ ← nullable
│ owner_id            UUID REFERENCES users(id) NULL          │ ← new
│ subscription_tier   VARCHAR(50) NOT NULL DEFAULT 'free'     │
│ created_at          TIMESTAMP DEFAULT NOW()                 │
│ updated_at          TIMESTAMP                               │
│                                                             │
│ CONSTRAINT check_team_ownership                             │
│   CHECK (                                                   │
│     (organization_id IS NOT NULL AND owner_id IS NULL) OR  │
│     (organization_id IS NULL AND owner_id IS NOT NULL)     │
│   )                                                         │
└─────────────────────────────────────────────────────────────┘
       ↑                        ↑
       │                        │
       │                        │
  ┌────┴───┐            ┌──────┴─────┐
  │ users  │            │organizations│
  └────────┘            └────────────┘
```

---

## Approval Signatures

**Prepared By:**  
Development Team - January 19, 2026

**Technical Review:**  
⏳ Pending - CTO

**Product Review:**  
⏳ Pending - Product Manager

**Security Review:**  
⏳ Pending - Security Team

---

**Next Steps:**
1. ⏳ **CTO Review** - Review this design document and approve/reject
2. ⏸️ **Address Open Questions** - Get decisions on 5 open questions
3. ⏸️ **Implementation** - Begin database migration and backend development

**Document Version History:**
- v1.0 (2026-01-19): Initial draft for CTO review
