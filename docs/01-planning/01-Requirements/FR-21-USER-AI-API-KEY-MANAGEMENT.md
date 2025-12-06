# FR-21: User API Key Management (BYOK - Bring Your Own Key)

**Version**: 1.0.0  
**Date**: December 13, 2025  
**Status**: ✅ **APPROVED** (CTO + CPO)  
**Authority**: CTO + CPO Approved  
**Framework**: SDLC 5.0.0  
**Priority**: Medium-High (Sprint 32)

---

## Executive Summary

**Capability**: Cho phép users quản lý API keys của third-party AI providers (OpenAI, Anthropic, Google Gemini, Custom) để sử dụng AI features mà không phụ thuộc vào system-wide keys.

**Business Value**:
- **Cost Reduction**: Users dùng own keys → giảm system cost
- **Privacy**: Support local Ollama → no data leaves premises
- **Flexibility**: Support custom providers (OpenAI-compatible APIs)
- **User Control**: Users có thể switch providers per feature

**User Personas**:
- **Developer**: Muốn dùng own OpenAI key để test
- **Enterprise User**: Muốn dùng local Ollama cho privacy
- **Custom Provider User**: Muốn dùng OpenAI-compatible API (local server)

---

## FR-21.1: User AI Provider Configuration

### Use Case 21.1.1: Add AI Provider API Key

**Actor**: User  
**Precondition**: User authenticated  
**Trigger**: User navigates to Settings > API Keys

**Main Flow**:
1. User clicks "Add Provider" button
2. System displays provider selector (OpenAI, Anthropic, Gemini, Custom)
3. User selects provider type
4. User enters API key (secure input with show/hide toggle)
5. User optionally enters base URL (for custom/OpenAI-compatible)
6. User optionally enters default model
7. System encrypts API key (AES-256)
8. System validates API key (real-time test connection)
9. System saves provider configuration
10. System displays success message với validation status

**Postcondition**: Provider configuration saved, API key encrypted, validation status displayed.

**Acceptance Criteria**:
- AC1: API key encrypted at-rest (AES-256)
- AC2: Real-time validation với test connection
- AC3: Support 4 provider types (OpenAI, Anthropic, Gemini, Custom)
- AC4: Support custom base URL (for OpenAI-compatible)
- AC5: Validation status displayed (✅ Valid / ❌ Invalid)

---

### Use Case 21.1.2: Validate API Key

**Actor**: User  
**Precondition**: Provider configured  
**Trigger**: User clicks "Test Connection" button

**Main Flow**:
1. System calls provider validation endpoint
2. System checks API key validity
3. System retrieves available models
4. System updates validation status
5. System displays validation result

**Postcondition**: Validation status updated, available models displayed.

**Acceptance Criteria**:
- AC1: Validation completes in <5s
- AC2: Available models displayed
- AC3: Error messages clear và actionable

---

### Use Case 21.1.3: Update/Delete Provider

**Actor**: User  
**Precondition**: Provider configured  
**Trigger**: User clicks "Edit" or "Delete" button

**Main Flow**:
1. User updates API key hoặc deletes provider
2. System validates changes (if update)
3. System saves changes hoặc removes provider
4. System updates AI service fallback chain

**Postcondition**: Provider updated hoặc removed, fallback chain updated.

**Acceptance Criteria**:
- AC1: Update preserves existing configuration if validation fails
- AC2: Delete requires confirmation
- AC3: Fallback chain updated immediately

---

## FR-21.2: AI Provider Priority (Fallback Chain)

### Priority Order

**Fallback Chain Logic**:
```
1. User's configured provider (if valid)
2. Project-level override (if set)
3. Organization default (if enterprise) - Future
4. System default (Ollama → Claude → GPT-4o)
```

**Implementation**:
- User keys checked first
- If invalid/missing → fallback to system keys
- Per-request provider selection (user can override)

---

## FR-21.3: Cost Tracking

### Per-User Cost Tracking

**Requirement**: Track AI usage cost per user khi dùng own keys.

**Implementation**:
- Extend `AIRequest` table với `user_provider_id` (nullable)
- Track cost per user provider
- Display usage statistics trong Settings page

**Acceptance Criteria**:
- AC1: Cost tracked per user provider
- AC2: Usage statistics displayed (requests, tokens, cost)
- AC3: Monthly cost summary available

---

## API Contract

### Endpoints

```typescript
// List user's configured providers
GET /api/v1/users/me/ai-providers
Response: {
  providers: [
    {
      id: "uuid",
      name: "OpenAI",
      type: "openai",
      baseUrl: "https://api.openai.com/v1",
      defaultModel: "gpt-4o",
      hasApiKey: true,
      isValid: true,
      lastValidated: "2025-12-13T10:00:00Z",
      availableModels: ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
    }
  ]
}

// Add AI provider
POST /api/v1/users/me/ai-providers
Request: {
  type: "openai" | "anthropic" | "gemini" | "openai_compatible" | "custom",
  name: "My OpenAI Key",
  apiKey: "sk-...",
  baseUrl?: "https://api.openai.com/v1",
  defaultModel?: "gpt-4o"
}
Response: {
  id: "uuid",
  name: "My OpenAI Key",
  type: "openai",
  isValid: true,
  availableModels: ["gpt-4o", "gpt-4-turbo"]
}

// Validate API key
POST /api/v1/users/me/ai-providers/{id}/validate
Response: {
  isValid: true,
  error: null,
  availableModels: ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
}

// Update provider
PUT /api/v1/users/me/ai-providers/{id}
Request: {
  name?: string,
  apiKey?: string,
  baseUrl?: string,
  defaultModel?: string
}

// Delete provider
DELETE /api/v1/users/me/ai-providers/{id}
```

---

## Database Schema

### Migration: Create user_ai_providers table

```sql
CREATE TABLE user_ai_providers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  
  -- Provider Identity
  type VARCHAR(50) NOT NULL CHECK (type IN ('openai', 'anthropic', 'gemini', 'openai_compatible', 'custom')),
  name VARCHAR(100) NOT NULL,
  
  -- API Configuration
  api_key_encrypted BYTEA NOT NULL,  -- AES-256 encrypted
  base_url VARCHAR(255),  -- For custom/OpenAI-compatible
  default_model VARCHAR(100),
  
  -- Validation Status
  is_valid BOOLEAN DEFAULT FALSE,
  last_validated_at TIMESTAMP,
  available_models JSONB,  -- Array of available models
  
  -- Timestamps
  created_at TIMESTAMP DEFAULT NOW() NOT NULL,
  updated_at TIMESTAMP DEFAULT NOW() NOT NULL,
  
  -- Constraints
  UNIQUE(user_id, name)  -- Prevent duplicate names per user
);

-- Indexes
CREATE INDEX idx_user_ai_providers_user ON user_ai_providers(user_id);
CREATE INDEX idx_user_ai_providers_user_type ON user_ai_providers(user_id, type);
CREATE INDEX idx_user_ai_providers_user_valid ON user_ai_providers(user_id, is_valid) WHERE is_valid = true;
```

---

## Security Requirements

### Encryption

- **At-Rest**: AES-256 encryption với user-specific key
- **In-Transit**: TLS 1.3 (HTTPS only)
- **Key Storage**: Never store plaintext keys
- **Key Display**: Only show last 4 characters in UI

### Access Control

- **Row-Level Security**: Users chỉ access own keys
- **Audit Trail**: Log all key access/usage
- **Key Rotation**: Manual rotation, optional expiry

### Validation

- **Real-Time**: Test connection khi add/update
- **Periodic**: Auto-validate every 24 hours
- **Error Handling**: Clear error messages

---

## UI/UX Requirements

### Web Dashboard

**Page**: `/settings/api-keys`

**Components**:
- `ProviderCard` - Display provider với status badge
- `ApiKeyInput` - Secure input với show/hide toggle
- `ApiKeyValidator` - Real-time validation badge
- `ProviderSelector` - Dropdown cho provider selection
- `UsageStatistics` - Display usage (requests, tokens, cost)

**User Flow**:
1. Navigate to Settings > API Keys
2. See list of configured providers
3. Click "Add Provider" → Select type → Enter key → Test → Save
4. See validation status với last checked time
5. View usage statistics per provider

---

### VS Code Extension

**Command**: `SDLC: Configure AI Provider` (Cmd+Shift+,)

**UI**:
- Provider selector dropdown
- API key input (secure)
- Base URL input (optional)
- Default model selector
- "Test Connection" button
- Storage option (Local / Server / Both)

**Settings Storage**:
```json
{
  "sdlc-orchestrator.ai": {
    "provider": "openai",
    "apiKey": "${env:OPENAI_API_KEY}",
    "baseUrl": "https://api.openai.com/v1",
    "model": "gpt-4o",
    "storage": "local"  // "local" | "server" | "both"
  }
}
```

---

## Implementation Plan

### Phase 1: Database & Backend (Sprint 32)

**Deliverables**:
1. Database migration (user_ai_providers table)
2. Backend API endpoints (5 endpoints)
3. Encryption service (AES-256)
4. Validation service (test connection)
5. Cost tracking integration

**Effort**: 3-4 days

---

### Phase 2: Frontend Web (Sprint 32)

**Deliverables**:
1. Settings page (`/settings/api-keys`)
2. ProviderCard component
3. ApiKeyInput component
4. ApiKeyValidator component
5. UsageStatistics component

**Effort**: 2-3 days

---

### Phase 3: VS Code Extension (Sprint 33)

**Deliverables**:
1. Command: `SDLC: Configure AI Provider`
2. Settings UI integration
3. Local + Server sync
4. Environment variable support

**Effort**: 2 days

---

## Success Criteria

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| API key encryption | 100% encrypted | Security audit |
| Validation accuracy | 100% | Test connection success rate |
| User adoption | 30%+ users configure keys | Analytics |
| Cost reduction | 20%+ system cost reduction | Cost tracking |
| Security incidents | 0 | Security audit |

---

## Related Documents

- [CTO/CPO Review](./../../09-Executive-Reports/01-CTO-Reports/2025-12-13-CTO-CPO-PLAN-REVIEW.md)
- [ADR-007: AI Context Engine](./../../02-Design-Architecture/03-ADRs/ADR-007-AI-Context-Engine.md)
- [Security Baseline](./../../02-Design-Architecture/Security-Baseline.md)

---

**Status**: ✅ **APPROVED**  
**Next**: Implementation in Sprint 32 (post-G3)

