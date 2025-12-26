# QR Code Mobile Preview - Technical Design

**Version**: 1.0.0
**Status**: Ready for Implementation
**Sprint**: 51B
**Priority**: MEDIUM
**Effort**: 0.5 day
**Author**: CTO
**Date**: December 25, 2025

---

## 1. Overview

### 1.1 Problem Statement

Vietnam SME users often:
- Need to show generated apps to stakeholders on mobile devices
- Want to preview responsive design on actual phones
- Cannot easily share preview links during meetings

### 1.2 Solution

Implement QR code preview feature:
- Generate QR code for preview URL
- Preview URL with 24h expiration
- Mobile-optimized preview rendering
- Shareable link with optional password protection

### 1.3 Success Metrics

| Metric | Target |
|--------|--------|
| Mobile preview adoption | 30% of users |
| Time to share preview | <5 seconds |
| Preview load time (mobile) | <2 seconds |

---

## 2. Architecture

### 2.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     CodeGenerationPage                           │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    QR Preview Button                         │ │
│  │                       [📱 QR]                                │ │
│  └──────────────────────────┬──────────────────────────────────┘ │
│                             │                                     │
│  ┌──────────────────────────▼──────────────────────────────────┐ │
│  │                   QRPreviewModal                             │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌──────────────────────┐   │ │
│  │  │   QR Code   │ │   URL       │ │   Copy/Share         │   │ │
│  │  │   [▓▓▓▓▓]   │ │   Input     │ │   Buttons            │   │ │
│  │  └─────────────┘ └─────────────┘ └──────────────────────┘   │ │
│  └──────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Backend API                              │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  POST /api/v1/codegen/sessions/{id}/preview                 │ │
│  │  → Creates preview token, returns URL                       │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  GET /preview/{token}                                        │ │
│  │  → Validates token, serves preview                          │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                          Redis                                   │
│  preview:{token}:metadata → PreviewMetadata (JSON)              │
│  preview:{token}:files    → GeneratedFiles (JSON)               │
│  TTL: 24 hours                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Preview URL Flow

```
1. User clicks QR button
2. Frontend calls POST /codegen/sessions/{id}/preview
3. Backend generates unique token
4. Backend stores files + metadata in Redis (24h TTL)
5. Backend returns preview URL
6. Frontend generates QR code from URL
7. User scans QR or shares link
8. Preview page loads from GET /preview/{token}
```

---

## 3. Data Models

### 3.1 Preview Metadata

```python
# backend/app/schemas/preview.py

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import UUID


class PreviewMetadata(BaseModel):
    """Metadata for preview session"""
    token: str
    session_id: UUID
    project_id: UUID
    user_id: UUID
    app_name: str
    created_at: datetime
    expires_at: datetime
    view_count: int = 0
    password_protected: bool = False
    password_hash: Optional[str] = None  # bcrypt hash


class PreviewFile(BaseModel):
    """File for preview rendering"""
    path: str
    content: str
    language: str
    lines: int


class PreviewRequest(BaseModel):
    """Request to create preview"""
    session_id: UUID
    password: Optional[str] = None  # Optional password protection
    expires_in_hours: int = Field(default=24, ge=1, le=168)  # 1h to 7d


class PreviewResponse(BaseModel):
    """Response with preview URL and QR data"""
    preview_url: str
    token: str
    expires_at: datetime
    qr_data: str  # Base64 encoded QR code PNG


class PreviewAccessRequest(BaseModel):
    """Request to access preview with password"""
    password: Optional[str] = None
```

---

## 4. API Endpoints

### 4.1 Create Preview

```python
# backend/app/api/routes/preview.py

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional
import bcrypt
import qrcode
from io import BytesIO
import base64

from fastapi import APIRouter, Depends, HTTPException
from redis.asyncio import Redis

from app.core.config import settings
from app.core.deps import get_current_user, get_redis
from app.schemas.preview import (
    PreviewRequest,
    PreviewResponse,
    PreviewMetadata,
    PreviewFile,
    PreviewAccessRequest
)
from app.services.codegen.session_manager import SessionManager

router = APIRouter(prefix="/codegen", tags=["preview"])


@router.post("/sessions/{session_id}/preview", response_model=PreviewResponse)
async def create_preview(
    session_id: UUID,
    request: PreviewRequest,
    current_user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis)
):
    """
    Create a shareable preview URL for generated code.

    Returns:
        PreviewResponse with URL and QR code
    """
    session_manager = SessionManager(redis)

    # Get session
    session = await session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get generated files
    files = await session_manager.get_completed_files(session_id)
    if not files:
        raise HTTPException(status_code=400, detail="No files to preview")

    # Generate token
    token = secrets.token_urlsafe(32)

    # Calculate expiration
    expires_at = datetime.utcnow() + timedelta(hours=request.expires_in_hours)

    # Hash password if provided
    password_hash = None
    if request.password:
        password_hash = bcrypt.hashpw(
            request.password.encode(),
            bcrypt.gensalt()
        ).decode()

    # Create metadata
    metadata = PreviewMetadata(
        token=token,
        session_id=session_id,
        project_id=session.project_id,
        user_id=current_user.id,
        app_name=session.blueprint_version,  # Or extract from blueprint
        created_at=datetime.utcnow(),
        expires_at=expires_at,
        password_protected=password_hash is not None,
        password_hash=password_hash
    )

    # Store in Redis
    ttl_seconds = request.expires_in_hours * 3600

    pipe = redis.pipeline()
    pipe.setex(
        f"preview:{token}:metadata",
        ttl_seconds,
        metadata.model_dump_json()
    )
    pipe.setex(
        f"preview:{token}:files",
        ttl_seconds,
        json.dumps([f.model_dump() for f in files], default=str)
    )
    await pipe.execute()

    # Build preview URL
    preview_url = f"{settings.PREVIEW_BASE_URL}/preview/{token}"

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(preview_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to base64
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_data = base64.b64encode(buffer.getvalue()).decode()

    return PreviewResponse(
        preview_url=preview_url,
        token=token,
        expires_at=expires_at,
        qr_data=f"data:image/png;base64,{qr_data}"
    )


@router.get("/preview/{token}")
async def get_preview(
    token: str,
    password: Optional[str] = None,
    redis: Redis = Depends(get_redis)
) -> dict:
    """
    Get preview content by token.

    This is a public endpoint (no auth required).
    """
    # Get metadata
    metadata_json = await redis.get(f"preview:{token}:metadata")
    if not metadata_json:
        raise HTTPException(status_code=404, detail="Preview not found or expired")

    metadata = PreviewMetadata.model_validate_json(metadata_json)

    # Check password if protected
    if metadata.password_protected:
        if not password:
            raise HTTPException(
                status_code=401,
                detail="Password required",
                headers={"X-Password-Required": "true"}
            )
        if not bcrypt.checkpw(password.encode(), metadata.password_hash.encode()):
            raise HTTPException(status_code=401, detail="Invalid password")

    # Get files
    files_json = await redis.get(f"preview:{token}:files")
    if not files_json:
        raise HTTPException(status_code=404, detail="Preview files not found")

    files = [PreviewFile.model_validate(f) for f in json.loads(files_json)]

    # Increment view count
    metadata.view_count += 1
    ttl = await redis.ttl(f"preview:{token}:metadata")
    if ttl > 0:
        await redis.setex(
            f"preview:{token}:metadata",
            ttl,
            metadata.model_dump_json()
        )

    return {
        "app_name": metadata.app_name,
        "files": [f.model_dump() for f in files],
        "file_count": len(files),
        "total_lines": sum(f.lines for f in files),
        "created_at": metadata.created_at.isoformat(),
        "expires_at": metadata.expires_at.isoformat(),
        "view_count": metadata.view_count
    }


@router.delete("/preview/{token}")
async def delete_preview(
    token: str,
    current_user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis)
):
    """Delete a preview before expiration"""
    # Get metadata to check ownership
    metadata_json = await redis.get(f"preview:{token}:metadata")
    if not metadata_json:
        raise HTTPException(status_code=404, detail="Preview not found")

    metadata = PreviewMetadata.model_validate_json(metadata_json)

    if metadata.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Delete from Redis
    await redis.delete(f"preview:{token}:metadata", f"preview:{token}:files")

    return {"message": "Preview deleted"}
```

---

## 5. Frontend Components

### 5.1 QR Preview Modal

```typescript
// frontend/web/src/components/codegen/QRPreviewModal.tsx

import React, { useState } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import { Copy, Share2, ExternalLink, Lock, Clock, Eye } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useToast } from '@/components/ui/use-toast';
import { usePreview } from '@/hooks/usePreview';
import { formatDistanceToNow } from 'date-fns';

interface QRPreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  sessionId: string;
}

export function QRPreviewModal({ isOpen, onClose, sessionId }: QRPreviewModalProps) {
  const { toast } = useToast();
  const [password, setPassword] = useState('');
  const [usePassword, setUsePassword] = useState(false);
  const [expiresIn, setExpiresIn] = useState('24');

  const {
    createPreview,
    previewData,
    isCreating,
  } = usePreview();

  const handleCreate = async () => {
    try {
      await createPreview({
        session_id: sessionId,
        password: usePassword ? password : undefined,
        expires_in_hours: parseInt(expiresIn),
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to create preview',
        variant: 'destructive',
      });
    }
  };

  const handleCopy = async () => {
    if (previewData?.preview_url) {
      await navigator.clipboard.writeText(previewData.preview_url);
      toast({
        title: 'Copied!',
        description: 'Preview URL copied to clipboard',
      });
    }
  };

  const handleShare = async () => {
    if (previewData?.preview_url && navigator.share) {
      try {
        await navigator.share({
          title: 'Code Preview',
          url: previewData.preview_url,
        });
      } catch (error) {
        // User cancelled or share failed
      }
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={() => onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Mobile Preview</DialogTitle>
          <DialogDescription>
            Scan QR code or share link to preview on mobile device
          </DialogDescription>
        </DialogHeader>

        {!previewData ? (
          <div className="space-y-4">
            {/* Password protection */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Lock className="h-4 w-4 text-muted-foreground" />
                <Label htmlFor="password-toggle">Password protect</Label>
              </div>
              <Switch
                id="password-toggle"
                checked={usePassword}
                onCheckedChange={setUsePassword}
              />
            </div>

            {usePassword && (
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter password"
                />
              </div>
            )}

            {/* Expiration */}
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <Label>Expires in</Label>
              </div>
              <Select value={expiresIn} onValueChange={setExpiresIn}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">1 hour</SelectItem>
                  <SelectItem value="6">6 hours</SelectItem>
                  <SelectItem value="24">24 hours</SelectItem>
                  <SelectItem value="72">3 days</SelectItem>
                  <SelectItem value="168">7 days</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Button
              onClick={handleCreate}
              disabled={isCreating || (usePassword && !password)}
              className="w-full"
            >
              {isCreating ? 'Creating...' : 'Generate QR Code'}
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            {/* QR Code */}
            <div className="flex justify-center p-4 bg-white rounded-lg">
              <QRCodeSVG
                value={previewData.preview_url}
                size={200}
                level="L"
                includeMargin
              />
            </div>

            {/* URL */}
            <div className="flex items-center gap-2">
              <Input
                value={previewData.preview_url}
                readOnly
                className="font-mono text-sm"
              />
              <Button variant="outline" size="icon" onClick={handleCopy}>
                <Copy className="h-4 w-4" />
              </Button>
            </div>

            {/* Actions */}
            <div className="flex gap-2">
              <Button
                variant="outline"
                className="flex-1"
                onClick={handleShare}
              >
                <Share2 className="mr-2 h-4 w-4" />
                Share
              </Button>
              <Button
                variant="outline"
                className="flex-1"
                onClick={() => window.open(previewData.preview_url, '_blank')}
              >
                <ExternalLink className="mr-2 h-4 w-4" />
                Open
              </Button>
            </div>

            {/* Info */}
            <div className="text-sm text-muted-foreground text-center space-y-1">
              <p className="flex items-center justify-center gap-1">
                <Clock className="h-3 w-3" />
                Expires {formatDistanceToNow(new Date(previewData.expires_at), { addSuffix: true })}
              </p>
              {usePassword && (
                <p className="flex items-center justify-center gap-1">
                  <Lock className="h-3 w-3" />
                  Password protected
                </p>
              )}
            </div>

            {/* Create new */}
            <Button
              variant="ghost"
              className="w-full"
              onClick={() => {
                // Reset to create new
              }}
            >
              Create new preview
            </Button>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
```

### 5.2 Preview Hook

```typescript
// frontend/web/src/hooks/usePreview.ts

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';

interface PreviewRequest {
  session_id: string;
  password?: string;
  expires_in_hours: number;
}

interface PreviewResponse {
  preview_url: string;
  token: string;
  expires_at: string;
  qr_data: string;
}

export function usePreview() {
  const [previewData, setPreviewData] = useState<PreviewResponse | null>(null);

  const createMutation = useMutation({
    mutationFn: async (request: PreviewRequest): Promise<PreviewResponse> => {
      const response = await apiClient.post<PreviewResponse>(
        `/codegen/sessions/${request.session_id}/preview`,
        {
          password: request.password,
          expires_in_hours: request.expires_in_hours,
        }
      );
      return response.data;
    },
    onSuccess: (data) => {
      setPreviewData(data);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (token: string) => {
      await apiClient.delete(`/codegen/preview/${token}`);
    },
    onSuccess: () => {
      setPreviewData(null);
    },
  });

  return {
    previewData,
    createPreview: createMutation.mutateAsync,
    deletePreview: deleteMutation.mutateAsync,
    isCreating: createMutation.isPending,
    isDeleting: deleteMutation.isPending,
    reset: () => setPreviewData(null),
  };
}
```

### 5.3 Preview Page (Public)

```typescript
// frontend/web/src/pages/PreviewPage.tsx

import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Lock, FileCode, Clock, Eye, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { apiClient } from '@/lib/api';
import { CodePreview } from '@/components/codegen/CodePreview';
import { formatDistanceToNow } from 'date-fns';

interface PreviewData {
  app_name: string;
  files: Array<{
    path: string;
    content: string;
    language: string;
    lines: number;
  }>;
  file_count: number;
  total_lines: number;
  created_at: string;
  expires_at: string;
  view_count: number;
}

export function PreviewPage() {
  const { token } = useParams<{ token: string }>();
  const [password, setPassword] = useState('');
  const [passwordRequired, setPasswordRequired] = useState(false);
  const [passwordError, setPasswordError] = useState(false);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['preview', token, password],
    queryFn: async (): Promise<PreviewData> => {
      try {
        const response = await apiClient.get(`/codegen/preview/${token}`, {
          params: password ? { password } : undefined,
        });
        setPasswordRequired(false);
        setPasswordError(false);
        return response.data;
      } catch (err: any) {
        if (err.response?.status === 401) {
          if (err.response?.headers?.['x-password-required']) {
            setPasswordRequired(true);
          } else {
            setPasswordError(true);
          }
        }
        throw err;
      }
    },
    enabled: !!token,
    retry: false,
  });

  const handlePasswordSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    refetch();
  };

  if (isLoading) {
    return (
      <div className="container mx-auto p-4 max-w-4xl">
        <Skeleton className="h-8 w-48 mb-4" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (error && !passwordRequired) {
    return (
      <div className="container mx-auto p-4 max-w-4xl">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Preview not found or has expired
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  if (passwordRequired) {
    return (
      <div className="container mx-auto p-4 max-w-md">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lock className="h-5 w-5" />
              Password Protected
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handlePasswordSubmit} className="space-y-4">
              <div className="space-y-2">
                <Input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter password"
                  autoFocus
                />
                {passwordError && (
                  <p className="text-sm text-destructive">
                    Invalid password
                  </p>
                )}
              </div>
              <Button type="submit" className="w-full">
                View Preview
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <div className="container mx-auto p-4 max-w-6xl">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-2">{data.app_name}</h1>
        <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
          <Badge variant="secondary" className="gap-1">
            <FileCode className="h-3 w-3" />
            {data.file_count} files
          </Badge>
          <Badge variant="secondary" className="gap-1">
            {data.total_lines} lines
          </Badge>
          <Badge variant="secondary" className="gap-1">
            <Eye className="h-3 w-3" />
            {data.view_count} views
          </Badge>
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            Expires {formatDistanceToNow(new Date(data.expires_at), { addSuffix: true })}
          </span>
        </div>
      </div>

      {/* Files */}
      <div className="space-y-4">
        {data.files.map((file) => (
          <Card key={file.path}>
            <CardHeader className="py-3">
              <CardTitle className="text-sm font-mono">
                {file.path}
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <CodePreview
                code={file.content}
                language={file.language}
                showLineNumbers
                maxHeight="400px"
              />
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Footer */}
      <div className="mt-8 text-center text-sm text-muted-foreground">
        Generated by SDLC Orchestrator
      </div>
    </div>
  );
}
```

---

## 6. Configuration

### 6.1 Environment Variables

```bash
# .env.example additions

# Preview Configuration
PREVIEW_BASE_URL=https://preview.sdlc.nhatquangholding.com
PREVIEW_DEFAULT_TTL=86400  # 24 hours
PREVIEW_MAX_TTL=604800     # 7 days
```

### 6.2 Dependencies

```json
// package.json additions
{
  "dependencies": {
    "qrcode.react": "^3.1.0"
  }
}
```

```txt
# requirements.txt additions
qrcode==7.4.2
Pillow>=10.0.0  # For image generation
```

---

## 7. Testing

### 7.1 Unit Tests

```python
# backend/tests/unit/api/test_preview.py

import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.api.routes.preview import create_preview, get_preview


class TestPreviewAPI:

    @pytest.mark.asyncio
    async def test_create_preview_returns_url_and_qr(self):
        """Test preview creation with QR code"""
        # Setup
        session_id = uuid4()
        mock_redis = AsyncMock()
        mock_redis.pipeline.return_value = AsyncMock()

        # Test
        response = await create_preview(
            session_id=session_id,
            request=PreviewRequest(
                session_id=session_id,
                expires_in_hours=24
            ),
            current_user=mock_user,
            redis=mock_redis
        )

        # Assert
        assert response.preview_url is not None
        assert response.token is not None
        assert response.qr_data.startswith("data:image/png;base64,")
        assert response.expires_at is not None

    @pytest.mark.asyncio
    async def test_create_preview_with_password(self):
        """Test password-protected preview"""
        # Test with password
        response = await create_preview(
            ...,
            request=PreviewRequest(
                session_id=session_id,
                password="secret123",
                expires_in_hours=24
            ),
            ...
        )

        # Verify password was stored
        assert "password" not in response.model_dump()

    @pytest.mark.asyncio
    async def test_get_preview_requires_password(self):
        """Test that password-protected preview requires password"""
        # Setup protected preview
        # ...

        # Test without password
        with pytest.raises(HTTPException) as exc:
            await get_preview(token=token, password=None, redis=mock_redis)

        assert exc.value.status_code == 401
        assert "Password required" in exc.value.detail

    @pytest.mark.asyncio
    async def test_get_preview_increments_view_count(self):
        """Test view count increments on access"""
        # Setup
        # ...

        # Access twice
        response1 = await get_preview(token=token, redis=mock_redis)
        response2 = await get_preview(token=token, redis=mock_redis)

        assert response2["view_count"] == response1["view_count"] + 1
```

### 7.2 Frontend Tests

```typescript
// frontend/web/src/components/codegen/__tests__/QRPreviewModal.test.tsx

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QRPreviewModal } from '../QRPreviewModal';

describe('QRPreviewModal', () => {
  it('renders create form when no preview exists', () => {
    render(
      <QRPreviewModal isOpen={true} onClose={() => {}} sessionId="123" />
    );

    expect(screen.getByText('Generate QR Code')).toBeInTheDocument();
    expect(screen.getByText('Password protect')).toBeInTheDocument();
  });

  it('shows QR code after creation', async () => {
    // Mock successful creation
    // ...

    render(
      <QRPreviewModal isOpen={true} onClose={() => {}} sessionId="123" />
    );

    fireEvent.click(screen.getByText('Generate QR Code'));

    await waitFor(() => {
      expect(screen.getByRole('img')).toBeInTheDocument();  // QR code SVG
    });
  });

  it('validates password field when protection enabled', () => {
    render(
      <QRPreviewModal isOpen={true} onClose={() => {}} sessionId="123" />
    );

    // Enable password
    fireEvent.click(screen.getByRole('switch'));

    // Button should be disabled without password
    expect(screen.getByText('Generate QR Code')).toBeDisabled();
  });
});
```

---

## 8. Rollout Plan

### Morning (2 hours): Backend
- [ ] Install qrcode library
- [ ] Implement preview API endpoints
- [ ] Add Redis storage
- [ ] Unit tests

### Afternoon (2 hours): Frontend
- [ ] Install qrcode.react
- [ ] Implement QRPreviewModal
- [ ] Implement PreviewPage
- [ ] Add to CodeGenerationPage
- [ ] E2E tests

### Deploy
- [ ] Deploy to staging
- [ ] Test QR scanning
- [ ] Deploy to production

---

## 9. References

- [Vibecode Pattern Adoption Plan](../15-Pattern-Adoption/Vibecode-Pattern-Adoption-Plan.md)
- [qrcode Python Library](https://pypi.org/project/qrcode/)
- [qrcode.react](https://www.npmjs.com/package/qrcode.react)

---

**Last Updated**: December 25, 2025
**Owner**: Frontend Team
**Status**: Ready for Implementation
