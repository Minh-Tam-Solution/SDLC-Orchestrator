# SPRINT-54: Frontend Polish + CodePreview
## EP-06: IR-Based Vietnamese SME Codegen | UX Enhancement

---

**Document Information**

| Field | Value |
|-------|-------|
| **Sprint ID** | SPRINT-54 |
| **Epic** | EP-06: IR-Based Codegen Engine |
| **Duration** | 5 days (Jan 13-17, 2026) |
| **Status** | PLANNED ⏳ |
| **Priority** | P1 Should Have |
| **Dependencies** | Sprint 53 complete |
| **Framework** | SDLC 5.1.2 Universal Framework |

---

## Sprint Goal

Polish frontend components for code generation UX including real-time file list, code preview, and download manager.

---

## Sprint Objectives

| Feature | Description | Effort |
|---------|-------------|--------|
| StreamingFileList | Real-time file list with progress | 1.5 days |
| CodePreviewPanel | Syntax-highlighted code viewer | 1 day |
| DiffViewer | Before/after comparison | 1 day |
| DownloadManager | Zip download with structure | 0.5 day |
| Mobile Responsive | App Builder mobile layout | 1 day |

---

## Files to Create

```
frontend/web/src/components/codegen/
├── StreamingFileList.tsx       # Real-time file list with progress
├── CodePreviewPanel.tsx        # Syntax-highlighted code viewer
├── DiffViewer.tsx              # Before/after comparison view
├── DownloadManager.tsx         # Zip download with structure
└── MobileAppBuilder.tsx        # Mobile-responsive layout
```

---

## Component Specifications

### StreamingFileList

**Features**:
- Real-time file addition animation
- Progress indicator per file
- Status icons (pending, generating, complete, error)
- Click to preview code
- Collapsible folder structure

### CodePreviewPanel

**Features**:
- Syntax highlighting (Prism.js)
- Language detection from extension
- Line numbers
- Copy to clipboard
- File path breadcrumb

### DiffViewer

**Features**:
- Side-by-side comparison
- Inline diff view
- Change statistics
- Navigate between changes

### DownloadManager

**Features**:
- Generate zip with folder structure
- Include README.md with setup instructions
- Progress indicator for large projects
- Optional: include .gitignore, requirements.txt

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Component render time | <100ms |
| Mobile usability score | 90+ |
| Code preview accuracy | 100% syntax highlight |
| Download speed (100 files) | <3s |

---

## Files Summary

| Category | Files | Lines (Est.) |
|----------|-------|--------------|
| Components | 5 | ~1,200 |
| Tests | 5 | ~300 |
| **Total** | **10** | **~1,500** |

---

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Last Updated** | December 27, 2025 |
| **Owner** | Frontend Lead |
| **Approved By** | CTO (Pending) |
