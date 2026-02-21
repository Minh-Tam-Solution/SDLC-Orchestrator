# API Frontend Validation Checklist

**Version**: 1.0.0
**Date**: November 14, 2025
**Status**: ACTIVE - Pre-Week 3 Validation
**Authority**: Frontend Lead + Backend Lead
**Foundation**: API Specification v1.0 Template (OpenAPI 3.0)
**Framework**: SDLC 6.1.0

---

## Purpose

Validate API design with Frontend team BEFORE Week 3 implementation starts (Nov 28).

**Goal**: Ensure API meets Developer Experience (DX) targets:
- ✅ Time to first API call: <5 minutes
- ✅ Intuitive endpoint naming
- ✅ Consistent response formats
- ✅ Complete error handling

**CTO Recommendation**: "Share API template with Frontend Lead (Day 1-2 preview) - prevents API redesign during Week 3"

---

## Validation Process

### Step 1: Frontend Lead Review (1-2 hours)

**Reviewer**: Frontend Lead
**Timeline**: Before Nov 25 (Gate G1 meeting)

**Review Checklist**:

- [ ] **Endpoint Naming** - RESTful conventions followed?
  - GET /gates (list)
  - POST /gates (create)
  - GET /gates/{gate_id} (retrieve)
  - PATCH /gates/{gate_id} (update)
  - DELETE /gates/{gate_id} (soft delete)

- [ ] **Request/Response Formats** - Consistent schema?
  - All responses have `data` field
  - Pagination has `pagination` object (total, limit, offset, has_more)
  - Errors have `error`, `error_code`, `message`, `timestamp`

- [ ] **Authentication Flow** - Clear token management?
  - POST /auth/login → returns access_token + refresh_token
  - POST /auth/refresh → returns new access_token
  - POST /auth/logout → invalidates tokens
  - All protected endpoints use `Authorization: Bearer <token>`

- [ ] **File Upload** - Multipart form-data correct?
  - POST /evidence (multipart/form-data)
  - Fields: `file` (binary), `gate_id`, `evidence_type`, `description`
  - Response: Evidence object with `s3_key`, `sha256_hash`

- [ ] **Pagination** - Offset-based, consistent?
  - Query params: `limit` (max 100), `offset`
  - Response: `pagination.has_more` (boolean)
  - Example: GET /gates?limit=20&offset=40

- [ ] **Error Handling** - HTTP status codes correct?
  - 401 Unauthorized (missing/invalid token)
  - 403 Forbidden (insufficient permissions)
  - 404 Not Found (resource doesn't exist)
  - 400 Bad Request (validation error)
  - 429 Too Many Requests (rate limited)

---

### Step 2: Developer Experience (DX) Test (30 minutes)

**Tester**: Frontend Lead
**Approach**: Simulate first-time API usage

**DX Checklist**:

- [ ] **Swagger UI Usable?**
  - Open http://localhost:8000/docs
  - All endpoints visible?
  - "Try it out" buttons work?
  - Example payloads provided?

- [ ] **Authentication Flow Intuitive?**
  - POST /auth/login with email/password
  - Copy access_token from response
  - Paste into "Authorize" button (Swagger UI)
  - All endpoints now authorized?

- [ ] **First API Call <5 minutes?**
  - Start: Read API docs
  - Step 1: POST /auth/login (get token)
  - Step 2: GET /gates (list gates)
  - End: Successful 200 response
  - **Target**: <5 minutes total time

- [ ] **Error Messages Helpful?**
  - Submit invalid request (missing required field)
  - Response has clear error message?
  - Example: `"Validation failed: gate_name is required"`

---

### Step 3: Frontend Integration Planning (1 hour)

**Participants**: Frontend Lead + Backend Lead
**Timeline**: Before Nov 25

**Integration Checklist**:

- [ ] **React Query Setup** - Endpoint mapping clear?
  - `useAuth()` hook → POST /auth/login
  - `useGates()` hook → GET /gates
  - `useGate(gateId)` hook → GET /gates/{gate_id}
  - `useCreateGate()` mutation → POST /gates

- [ ] **Zustand State Management** - API responses fit state shape?
  - `authStore` → stores `user`, `access_token`, `refresh_token`
  - `gateStore` → stores `gates[]`, `currentGate`, `filters`
  - API responses map 1:1 to store fields?

- [ ] **File Upload (Evidence)** - Frontend can construct multipart request?
  - Use `FormData` API (browser native)
  - Append `file` (File object), `gate_id`, `evidence_type`, `description`
  - Example code snippet provided?

- [ ] **WebSocket (Real-Time Dashboard FR4)** - Not in OpenAPI spec?
  - Separate WebSocket endpoint: `ws://localhost:8000/ws/dashboard`
  - Message format: `{"event": "gate_updated", "data": {...}}`
  - Frontend Lead aware WebSocket is separate from REST API?

---

## Frontend Feedback Template

**Reviewer**: [Frontend Lead Name]
**Date**: [Review Date]

### Endpoint Feedback

| Endpoint | Status | Feedback |
|----------|--------|----------|
| POST /auth/login | ✅ APPROVED | Clear, matches OAuth providers later |
| POST /auth/refresh | ✅ APPROVED | Standard JWT refresh flow |
| GET /gates | ⚠️ NEEDS CHANGE | Add `sort_by` query param (created_at, updated_at) |
| POST /gates | ✅ APPROVED | - |
| POST /evidence | ⚠️ NEEDS CHANGE | Add `max_file_size` to error response (UX clarity) |
| ... | ... | ... |

### Developer Experience (DX) Feedback

**Time to First API Call**: [X minutes] (Target: <5 minutes)

**Issues Found**:
1. [Issue 1]: [Description + Suggested Fix]
2. [Issue 2]: [Description + Suggested Fix]

**Recommendations**:
1. [Recommendation 1]
2. [Recommendation 2]

### Overall Assessment

**API Design Quality**: [X]/10

**Approval Status**:
- [ ] ✅ APPROVED - Ready for Week 3 implementation
- [ ] ⚠️ APPROVED WITH CHANGES - Minor changes needed (list above)
- [ ] 🔴 REJECTED - Major redesign required (detailed feedback above)

**Signature**: ___________________
**Date**: ___________________

---

## Backend Response Template

**Reviewer**: [Backend Lead Name]
**Date**: [Response Date]

### Frontend Feedback Response

| Feedback Item | Action | Timeline | Status |
|---------------|--------|----------|--------|
| Add `sort_by` param to GET /gates | ✅ ACCEPTED | Day 1 (Nov 28) | Pending |
| Add `max_file_size` to error | ✅ ACCEPTED | Day 1 (Nov 28) | Pending |
| ... | ... | ... | ... |

### Changes Incorporated

**Updated OpenAPI Spec**: [Link to updated YAML file]

**Change Summary**:
1. [Change 1]: [Description]
2. [Change 2]: [Description]

**Re-Review Required?**: [ ] Yes [ ] No

**Signature**: ___________________
**Date**: ___________________

---

## Example Frontend Code (React Query)

### Authentication Hook

```typescript
// hooks/useAuth.ts
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';

interface LoginRequest {
  email: string;
  password: string;
}

interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: {
    user_id: string;
    email: string;
    full_name: string;
    roles: string[];
  };
}

export const useLogin = () => {
  return useMutation({
    mutationFn: async (credentials: LoginRequest) => {
      const response = await apiClient.post<LoginResponse>(
        '/auth/login',
        credentials
      );
      return response.data;
    },
    onSuccess: (data) => {
      // Store tokens in auth store
      authStore.setState({
        user: data.user,
        accessToken: data.access_token,
        refreshToken: data.refresh_token,
      });
    },
  });
};

// Usage in component:
const LoginForm = () => {
  const login = useLogin();

  const handleSubmit = (email: string, password: string) => {
    login.mutate({ email, password });
  };

  // Time to first API call: <5 minutes ✅
  // Developer experience: Intuitive, type-safe ✅
};
```

### Gates Hook

```typescript
// hooks/useGates.ts
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';

interface Gate {
  gate_id: string;
  gate_name: string;
  gate_type: string;
  status: string;
  created_at: string;
}

interface GatesResponse {
  data: Gate[];
  pagination: {
    total: number;
    limit: number;
    offset: number;
    has_more: boolean;
  };
}

export const useGates = (filters?: {
  project_id?: string;
  status?: string;
  limit?: number;
  offset?: number;
}) => {
  return useQuery({
    queryKey: ['gates', filters],
    queryFn: async () => {
      const response = await apiClient.get<GatesResponse>('/gates', {
        params: filters,
      });
      return response.data;
    },
  });
};

// Usage in component:
const GatesList = () => {
  const { data, isLoading } = useGates({ limit: 20, offset: 0 });

  if (isLoading) return <Spinner />;

  return (
    <div>
      {data.data.map((gate) => (
        <GateCard key={gate.gate_id} gate={gate} />
      ))}
      {data.pagination.has_more && <LoadMoreButton />}
    </div>
  );
};
```

### Evidence Upload Hook

```typescript
// hooks/useUploadEvidence.ts
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';

interface UploadEvidenceRequest {
  file: File;
  gate_id: string;
  evidence_type: string;
  description?: string;
}

export const useUploadEvidence = () => {
  return useMutation({
    mutationFn: async (request: UploadEvidenceRequest) => {
      const formData = new FormData();
      formData.append('file', request.file);
      formData.append('gate_id', request.gate_id);
      formData.append('evidence_type', request.evidence_type);
      if (request.description) {
        formData.append('description', request.description);
      }

      const response = await apiClient.post('/evidence', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    },
  });
};

// Usage in component:
const EvidenceUpload = ({ gateId }: { gateId: string }) => {
  const upload = useUploadEvidence();

  const handleFileChange = (file: File) => {
    upload.mutate({
      file,
      gate_id: gateId,
      evidence_type: 'TEST_RESULTS',
      description: 'Unit test results for user authentication',
    });
  };

  return <FileInput onChange={handleFileChange} />;
};
```

---

## Success Criteria

**Validation Complete** when:

- [ ] Frontend Lead has reviewed API template (1-2 hours)
- [ ] DX test completed (<5 min to first API call achieved)
- [ ] Frontend integration plan documented (React Query hooks)
- [ ] Backend Lead has responded to feedback (changes incorporated)
- [ ] Frontend Lead approval received (✅ APPROVED or ⚠️ APPROVED WITH CHANGES)

**Timeline**: Complete before Nov 25 (Gate G1 meeting)

**Outcome**: Week 3 starts with **95% frontend-backend alignment** (prevents mid-week API redesign)

---

## Approvals

| Role | Name | Approval | Date |
|------|------|----------|------|
| **Frontend Lead** | [Name] | ⏳ Pending | __________ |
| **Backend Lead** | [Name] | ⏳ Pending | __________ |
| **CTO** | [Name] | ⏳ Pending | __________ |

**Required**: Frontend Lead + Backend Lead approval before Nov 28 (Week 3 start)

---

## References

- [API Specification v1.0 Template](./API-Specification-v1.0-Template.yaml) - OpenAPI 3.0 YAML
- [Functional Requirements Document](../../01-Planning-Analysis/Functional-Requirements/Functional-Requirements-Document.md) - FR1-FR5
- [React Query Documentation](https://tanstack.com/query/latest/docs/react/overview) - Data fetching
- [Zustand Documentation](https://zustand-demo.pmnd.rs/) - State management

---

**End of API Frontend Validation Checklist**

**Status**: ACTIVE - Awaiting Frontend Lead review
**Timeline**: Complete before Nov 25 (Gate G1 meeting)
**Goal**: Prevent API redesign during Week 3 (CTO recommendation)
