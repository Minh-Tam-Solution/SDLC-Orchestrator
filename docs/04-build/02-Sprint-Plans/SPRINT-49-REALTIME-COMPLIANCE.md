# SPRINT-49: Real-Time Compliance Monitor
## EP-05: Enterprise SDLC Migration | Phase 3

---

**Document Information**

| Field | Value |
|-------|-------|
| **Sprint ID** | SPRINT-49 |
| **Epic** | EP-05: Enterprise SDLC Migration Engine |
| **Duration** | 2 weeks (May 5-16, 2026) |
| **Status** | PLANNED |
| **Team** | 2 Backend + 1 Frontend + 1 QA |
| **Story Points** | 21 SP |
| **Budget** | $12,000 |
| **Framework** | SDLC 5.1.1 + SASE Level 2 |
| **Reference** | ADR-020, Sprint 47-48 |

---

## Sprint Goals

### Primary Objectives

| # | Objective | Priority | Owner |
|---|-----------|----------|-------|
| 1 | Build real-time file watcher | P0 | Backend Lead |
| 2 | Implement compliance scoring engine | P0 | Backend Dev |
| 3 | Create WebSocket notification service | P1 | Backend Lead |
| 4 | Build compliance dashboard widget | P1 | Frontend Dev |
| 5 | Integrate with VS Code extension | P2 | Backend Dev |

### Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| File change detection latency | <500ms | Benchmark |
| Compliance score accuracy | 100% | Manual review |
| Dashboard refresh rate | Real-time (<1s) | User testing |
| CPU usage (idle) | <1% | Resource monitor |

---

## Architecture

### Real-Time Compliance Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Real-Time Compliance Monitor                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  File System                    Backend                      Frontend       │
│  ┌──────────────┐              ┌────────────────────────┐                  │
│  │  docs/       │              │  Compliance Engine     │                  │
│  │  ├── 00-*    │──watchdog──▶│  ┌─────────────────┐   │                  │
│  │  ├── 01-*    │              │  │ File Watcher    │   │                  │
│  │  └── ...     │              │  └────────┬────────┘   │                  │
│  └──────────────┘              │           │            │                  │
│                                │           ▼            │                  │
│                                │  ┌─────────────────┐   │                  │
│                                │  │ Compliance      │   │    ┌──────────┐ │
│                                │  │ Calculator      │───┼───▶│WebSocket │ │
│                                │  └────────┬────────┘   │    └────┬─────┘ │
│                                │           │            │         │       │
│                                │           ▼            │         ▼       │
│                                │  ┌─────────────────┐   │  ┌───────────┐  │
│                                │  │ Score Aggregator│   │  │ Dashboard │  │
│                                │  └─────────────────┘   │  │ Widget    │  │
│                                │                        │  └───────────┘  │
│                                └────────────────────────┘                  │
│                                                                             │
│  Compliance Score = (Passed Rules / Total Rules) × 100                     │
│                                                                             │
│  Rules:                                                                     │
│  - Header completeness (25%)                                               │
│  - Naming convention (20%)                                                 │
│  - Version consistency (20%)                                               │
│  - Cross-references (15%)                                                  │
│  - Stage compliance (20%)                                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Week 1: File Watcher & Scoring (May 5-9)

### Day 1-2: File Watcher Service

**Task**: Implement watchdog-based file watcher with debouncing

```python
# backend/sdlcctl/compliance/watcher.py

import asyncio
from pathlib import Path
from typing import Callable, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

logger = logging.getLogger(__name__)

@dataclass
class FileChange:
    """Represents a file change event"""
    path: Path
    event_type: str  # created, modified, deleted, moved
    timestamp: datetime
    old_path: Optional[Path] = None  # For moved events

class DebounceHandler(FileSystemEventHandler):
    """
    File system event handler with debouncing
    
    Debouncing prevents multiple events for same file
    (e.g., IDE saves file multiple times)
    """
    
    DEBOUNCE_SECONDS = 0.5  # 500ms debounce
    
    def __init__(
        self,
        callback: Callable[[FileChange], None],
        patterns: List[str] = None
    ):
        self.callback = callback
        self.patterns = patterns or ["*.md"]
        self._pending: dict = {}
        self._lock = asyncio.Lock()
    
    def on_any_event(self, event: FileSystemEvent):
        """Handle any file system event"""
        # Skip directories
        if event.is_directory:
            return
        
        # Check pattern match
        path = Path(event.src_path)
        if not self._matches_pattern(path):
            return
        
        # Determine event type
        event_type = event.event_type  # created, modified, deleted, moved
        
        # Create change object
        change = FileChange(
            path=path,
            event_type=event_type,
            timestamp=datetime.now(),
            old_path=Path(event.dest_path) if hasattr(event, 'dest_path') else None
        )
        
        # Debounce
        self._schedule_callback(change)
    
    def _matches_pattern(self, path: Path) -> bool:
        """Check if path matches any pattern"""
        for pattern in self.patterns:
            if path.match(pattern):
                return True
        return False
    
    def _schedule_callback(self, change: FileChange):
        """Schedule debounced callback"""
        key = str(change.path)
        
        # Cancel existing timer
        if key in self._pending:
            self._pending[key].cancel()
        
        # Schedule new callback
        loop = asyncio.get_event_loop()
        timer = loop.call_later(
            self.DEBOUNCE_SECONDS,
            lambda: self.callback(change)
        )
        self._pending[key] = timer


class ComplianceWatcher:
    """
    Watch docs folder for changes and trigger compliance checks
    
    Features:
    - Debounced file watching
    - Markdown file filtering
    - Async callback support
    """
    
    def __init__(
        self,
        docs_root: Path,
        on_change: Callable[[FileChange], None]
    ):
        self.docs_root = docs_root
        self.on_change = on_change
        self._observer: Optional[Observer] = None
        self._running = False
    
    def start(self):
        """Start watching for file changes"""
        if self._running:
            return
        
        handler = DebounceHandler(
            callback=self._handle_change,
            patterns=["*.md", "*.json"]
        )
        
        self._observer = Observer()
        self._observer.schedule(
            handler,
            str(self.docs_root),
            recursive=True
        )
        self._observer.start()
        self._running = True
        
        logger.info(f"Started watching: {self.docs_root}")
    
    def stop(self):
        """Stop watching"""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
        self._running = False
        logger.info("Stopped watching")
    
    def _handle_change(self, change: FileChange):
        """Handle file change with logging"""
        logger.debug(f"File changed: {change.path} ({change.event_type})")
        self.on_change(change)
    
    @property
    def is_running(self) -> bool:
        return self._running
```

---

### Day 3-4: Compliance Scoring Engine

**Task**: Calculate compliance score with weighted rules

```python
# backend/sdlcctl/compliance/scorer.py

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional
from enum import Enum
import re

class RuleCategory(Enum):
    """Compliance rule categories"""
    HEADER = "header"
    NAMING = "naming"
    VERSION = "version"
    REFERENCE = "reference"
    STAGE = "stage"

@dataclass
class RuleResult:
    """Result of a single rule check"""
    rule_id: str
    category: RuleCategory
    passed: bool
    message: str
    severity: str = "warning"  # error, warning, info
    file_path: Optional[Path] = None
    line_number: Optional[int] = None

@dataclass
class ComplianceScore:
    """Aggregated compliance score"""
    total_score: float  # 0-100
    category_scores: Dict[str, float]
    passed_rules: int
    total_rules: int
    violations: List[RuleResult]
    timestamp: str
    
    @property
    def grade(self) -> str:
        """Get letter grade"""
        if self.total_score >= 90:
            return "A"
        elif self.total_score >= 80:
            return "B"
        elif self.total_score >= 70:
            return "C"
        elif self.total_score >= 60:
            return "D"
        else:
            return "F"
    
    @property
    def status(self) -> str:
        """Get compliance status"""
        if self.total_score >= 90:
            return "Excellent"
        elif self.total_score >= 70:
            return "Good"
        elif self.total_score >= 50:
            return "Needs Improvement"
        else:
            return "Critical"

class ComplianceScorer:
    """
    Calculate SDLC compliance score
    
    Weights:
    - Header completeness: 25%
    - Naming convention: 20%
    - Version consistency: 20%
    - Cross-references: 15%
    - Stage compliance: 20%
    """
    
    CATEGORY_WEIGHTS = {
        RuleCategory.HEADER: 0.25,
        RuleCategory.NAMING: 0.20,
        RuleCategory.VERSION: 0.20,
        RuleCategory.REFERENCE: 0.15,
        RuleCategory.STAGE: 0.20,
    }
    
    def __init__(self, config: 'SDLCConfig'):
        self.config = config
        self.rules = self._initialize_rules()
    
    def score(self, docs_root: Path) -> ComplianceScore:
        """Calculate compliance score for entire docs folder"""
        from datetime import datetime
        
        all_results: List[RuleResult] = []
        
        # Scan all markdown files
        for file_path in docs_root.rglob("*.md"):
            file_results = self._check_file(file_path)
            all_results.extend(file_results)
        
        # Calculate scores
        category_scores = self._calculate_category_scores(all_results)
        total_score = self._calculate_total_score(category_scores)
        
        passed = len([r for r in all_results if r.passed])
        violations = [r for r in all_results if not r.passed]
        
        return ComplianceScore(
            total_score=total_score,
            category_scores=category_scores,
            passed_rules=passed,
            total_rules=len(all_results),
            violations=violations,
            timestamp=datetime.now().isoformat()
        )
    
    def score_file(self, file_path: Path) -> ComplianceScore:
        """Calculate compliance score for single file"""
        from datetime import datetime
        
        results = self._check_file(file_path)
        
        category_scores = self._calculate_category_scores(results)
        total_score = self._calculate_total_score(category_scores)
        
        passed = len([r for r in results if r.passed])
        violations = [r for r in results if not r.passed]
        
        return ComplianceScore(
            total_score=total_score,
            category_scores=category_scores,
            passed_rules=passed,
            total_rules=len(results),
            violations=violations,
            timestamp=datetime.now().isoformat()
        )
    
    def _check_file(self, file_path: Path) -> List[RuleResult]:
        """Run all rules on a file"""
        results = []
        
        try:
            content = file_path.read_text()
        except Exception as e:
            return [RuleResult(
                rule_id="file-read",
                category=RuleCategory.HEADER,
                passed=False,
                message=f"Cannot read file: {e}",
                severity="error",
                file_path=file_path
            )]
        
        for rule in self.rules:
            result = rule.check(content, file_path, self.config)
            result.file_path = file_path
            results.append(result)
        
        return results
    
    def _calculate_category_scores(
        self,
        results: List[RuleResult]
    ) -> Dict[str, float]:
        """Calculate score per category"""
        scores = {}
        
        for category in RuleCategory:
            category_results = [r for r in results if r.category == category]
            if category_results:
                passed = len([r for r in category_results if r.passed])
                scores[category.value] = (passed / len(category_results)) * 100
            else:
                scores[category.value] = 100.0  # No rules = full compliance
        
        return scores
    
    def _calculate_total_score(
        self,
        category_scores: Dict[str, float]
    ) -> float:
        """Calculate weighted total score"""
        total = 0.0
        
        for category, weight in self.CATEGORY_WEIGHTS.items():
            score = category_scores.get(category.value, 100.0)
            total += score * weight
        
        return round(total, 1)
    
    def _initialize_rules(self) -> List['ComplianceRule']:
        """Initialize all compliance rules"""
        return [
            HeaderVersionRule(),
            HeaderDateRule(),
            HeaderStageRule(),
            HeaderStatusRule(),
            NamingConventionRule(),
            FolderStructureRule(),
            VersionConsistencyRule(),
            CrossReferenceRule(),
            StageSequenceRule(),
        ]


# Individual Rules

class ComplianceRule:
    """Base class for compliance rules"""
    
    rule_id: str
    category: RuleCategory
    description: str
    
    def check(
        self,
        content: str,
        file_path: Path,
        config: 'SDLCConfig'
    ) -> RuleResult:
        raise NotImplementedError

class HeaderVersionRule(ComplianceRule):
    """Check for version header field"""
    
    rule_id = "header-version"
    category = RuleCategory.HEADER
    description = "Document must have Version field"
    
    def check(self, content: str, file_path: Path, config: 'SDLCConfig') -> RuleResult:
        has_version = bool(re.search(
            r'\|\s*\*\*Version\*\*\s*\|',
            content,
            re.IGNORECASE
        ))
        
        return RuleResult(
            rule_id=self.rule_id,
            category=self.category,
            passed=has_version,
            message="Version field present" if has_version else "Missing Version field"
        )

class HeaderDateRule(ComplianceRule):
    """Check for date header field"""
    
    rule_id = "header-date"
    category = RuleCategory.HEADER
    description = "Document must have Date field"
    
    def check(self, content: str, file_path: Path, config: 'SDLCConfig') -> RuleResult:
        has_date = bool(re.search(
            r'\|\s*\*\*Date\*\*\s*\|',
            content,
            re.IGNORECASE
        ))
        
        return RuleResult(
            rule_id=self.rule_id,
            category=self.category,
            passed=has_date,
            message="Date field present" if has_date else "Missing Date field"
        )

class HeaderStageRule(ComplianceRule):
    """Check for stage header field"""
    
    rule_id = "header-stage"
    category = RuleCategory.HEADER
    description = "Document must have Stage field"
    
    def check(self, content: str, file_path: Path, config: 'SDLCConfig') -> RuleResult:
        has_stage = bool(re.search(
            r'\|\s*\*\*Stage\*\*\s*\|',
            content,
            re.IGNORECASE
        ))
        
        return RuleResult(
            rule_id=self.rule_id,
            category=self.category,
            passed=has_stage,
            message="Stage field present" if has_stage else "Missing Stage field"
        )

class HeaderStatusRule(ComplianceRule):
    """Check for status header field"""
    
    rule_id = "header-status"
    category = RuleCategory.HEADER
    description = "Document must have Status field"
    
    def check(self, content: str, file_path: Path, config: 'SDLCConfig') -> RuleResult:
        has_status = bool(re.search(
            r'\|\s*\*\*Status\*\*\s*\|',
            content,
            re.IGNORECASE
        ))
        
        return RuleResult(
            rule_id=self.rule_id,
            category=self.category,
            passed=has_status,
            message="Status field present" if has_status else "Missing Status field"
        )

class NamingConventionRule(ComplianceRule):
    """Check folder naming convention"""
    
    rule_id = "naming-convention"
    category = RuleCategory.NAMING
    description = "Folder names must follow SDLC convention"
    
    def check(self, content: str, file_path: Path, config: 'SDLCConfig') -> RuleResult:
        # Check if file is in proper stage folder
        parts = file_path.parts
        
        for part in parts:
            if re.match(r"^\d{2}-", part):
                # Found stage folder, check naming
                if config.naming == "short":
                    valid = bool(re.match(r"^\d{2}-[a-z-]+$", part))
                else:
                    valid = bool(re.match(r"^\d{2}-[A-Z][a-z]+(-[A-Z][a-z]+)*$", part))
                
                return RuleResult(
                    rule_id=self.rule_id,
                    category=self.category,
                    passed=valid,
                    message=f"Folder '{part}' follows naming convention" if valid 
                            else f"Folder '{part}' violates naming convention"
                )
        
        return RuleResult(
            rule_id=self.rule_id,
            category=self.category,
            passed=False,
            message="File not in recognized stage folder"
        )

class VersionConsistencyRule(ComplianceRule):
    """Check version matches target"""
    
    rule_id = "version-consistency"
    category = RuleCategory.VERSION
    description = "Document version must match target SDLC version"
    
    def check(self, content: str, file_path: Path, config: 'SDLCConfig') -> RuleResult:
        # Extract version from content
        match = re.search(
            r'\|\s*\*\*Version\*\*\s*\|\s*([^|]+)\s*\|',
            content
        )
        
        if not match:
            return RuleResult(
                rule_id=self.rule_id,
                category=self.category,
                passed=False,
                message="Cannot determine document version"
            )
        
        doc_version = match.group(1).strip()
        target_version = config.sdlc_version
        
        # Normalize versions for comparison
        doc_parts = re.findall(r"\d+", doc_version)[:2]
        target_parts = re.findall(r"\d+", target_version)[:2]
        
        matches = doc_parts == target_parts
        
        return RuleResult(
            rule_id=self.rule_id,
            category=self.category,
            passed=matches,
            message=f"Version {doc_version} matches target" if matches 
                    else f"Version mismatch: {doc_version} != {target_version}"
        )

class CrossReferenceRule(ComplianceRule):
    """Check for broken cross-references"""
    
    rule_id = "cross-reference"
    category = RuleCategory.REFERENCE
    description = "All internal links must be valid"
    
    LINK_PATTERN = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    
    def check(self, content: str, file_path: Path, config: 'SDLCConfig') -> RuleResult:
        broken_links = []
        
        for match in self.LINK_PATTERN.finditer(content):
            text, link = match.groups()
            
            # Skip external links
            if link.startswith(('http://', 'https://', 'mailto:', '#')):
                continue
            
            # Check if file exists
            target = (file_path.parent / link).resolve()
            if not target.exists():
                broken_links.append(link)
        
        passed = len(broken_links) == 0
        
        return RuleResult(
            rule_id=self.rule_id,
            category=self.category,
            passed=passed,
            message="All links valid" if passed 
                    else f"Broken links: {', '.join(broken_links[:3])}"
        )

class StageSequenceRule(ComplianceRule):
    """Check stage sequence is valid"""
    
    rule_id = "stage-sequence"
    category = RuleCategory.STAGE
    description = "Stage numbers must be sequential"
    
    def check(self, content: str, file_path: Path, config: 'SDLCConfig') -> RuleResult:
        # Extract stage from path
        parts = file_path.parts
        
        for part in parts:
            match = re.match(r"^(\d{2})-", part)
            if match:
                stage_num = int(match.group(1))
                valid_stages = [int(s) for s in config.stages]
                
                is_valid = stage_num in valid_stages or stage_num >= 10  # Legacy
                
                return RuleResult(
                    rule_id=self.rule_id,
                    category=self.category,
                    passed=is_valid,
                    message=f"Stage {stage_num:02d} is valid" if is_valid 
                            else f"Stage {stage_num:02d} not in valid stages"
                )
        
        return RuleResult(
            rule_id=self.rule_id,
            category=self.category,
            passed=True,
            message="No stage folder detected"
        )

class FolderStructureRule(ComplianceRule):
    """Check folder structure compliance"""
    
    rule_id = "folder-structure"
    category = RuleCategory.NAMING
    description = "Folder structure must match SDLC standard"
    
    def check(self, content: str, file_path: Path, config: 'SDLCConfig') -> RuleResult:
        # Check depth (should not be too deep)
        relative_parts = file_path.parts
        
        # Find docs folder depth
        try:
            docs_idx = relative_parts.index("docs")
            depth = len(relative_parts) - docs_idx - 1  # -1 for file itself
        except ValueError:
            depth = len(relative_parts)
        
        # Max recommended depth is 4
        passed = depth <= 4
        
        return RuleResult(
            rule_id=self.rule_id,
            category=self.category,
            passed=passed,
            message=f"Folder depth {depth} is OK" if passed 
                    else f"Folder depth {depth} exceeds recommended max of 4"
        )
```

---

### Day 5: WebSocket Notification Service

**Task**: Real-time updates to dashboard

```python
# backend/app/services/compliance_websocket.py

import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from typing import Set, Dict, Any
from dataclasses import dataclass
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class ComplianceUpdate:
    """WebSocket message for compliance updates"""
    event_type: str  # score_update, violation, file_change
    data: Dict[str, Any]
    
    def to_json(self) -> str:
        return json.dumps({
            "event": self.event_type,
            "data": self.data
        })

class ComplianceWebSocketManager:
    """
    Manage WebSocket connections for real-time compliance updates
    
    Features:
    - Multiple client support
    - Automatic reconnection handling
    - Message broadcasting
    """
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")
    
    async def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        async with self._lock:
            self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, update: ComplianceUpdate):
        """Broadcast update to all connected clients"""
        if not self.active_connections:
            return
        
        message = update.to_json()
        
        # Send to all connections
        disconnected = set()
        for websocket in self.active_connections:
            try:
                await websocket.send_text(message)
            except Exception:
                disconnected.add(websocket)
        
        # Clean up disconnected
        async with self._lock:
            self.active_connections -= disconnected
    
    async def send_score_update(self, score: 'ComplianceScore'):
        """Send compliance score update"""
        await self.broadcast(ComplianceUpdate(
            event_type="score_update",
            data={
                "total_score": score.total_score,
                "grade": score.grade,
                "status": score.status,
                "category_scores": score.category_scores,
                "violations_count": len(score.violations),
                "timestamp": score.timestamp
            }
        ))
    
    async def send_file_change(self, file_path: str, event_type: str):
        """Send file change notification"""
        await self.broadcast(ComplianceUpdate(
            event_type="file_change",
            data={
                "file": file_path,
                "change_type": event_type
            }
        ))
    
    async def send_violation(self, violation: 'RuleResult'):
        """Send new violation notification"""
        await self.broadcast(ComplianceUpdate(
            event_type="violation",
            data={
                "rule_id": violation.rule_id,
                "category": violation.category.value,
                "message": violation.message,
                "file": str(violation.file_path) if violation.file_path else None,
                "severity": violation.severity
            }
        ))


# FastAPI routes

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..core.deps import get_compliance_manager

router = APIRouter(prefix="/api/v1/compliance", tags=["compliance"])

ws_manager = ComplianceWebSocketManager()

@router.websocket("/ws")
async def compliance_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time compliance updates"""
    await ws_manager.connect(websocket)
    
    try:
        while True:
            # Keep connection alive, receive any client messages
            data = await websocket.receive_text()
            
            # Handle ping/pong
            if data == "ping":
                await websocket.send_text("pong")
    
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)

@router.get("/score")
async def get_compliance_score():
    """Get current compliance score"""
    from ..services.compliance_service import compliance_service
    score = await compliance_service.get_current_score()
    return {
        "total_score": score.total_score,
        "grade": score.grade,
        "status": score.status,
        "category_scores": score.category_scores,
        "passed_rules": score.passed_rules,
        "total_rules": score.total_rules,
        "violations": [
            {
                "rule_id": v.rule_id,
                "category": v.category.value,
                "message": v.message,
                "file": str(v.file_path) if v.file_path else None
            }
            for v in score.violations[:20]  # First 20 violations
        ],
        "timestamp": score.timestamp
    }
```

---

## Week 2: Dashboard & Integration (May 12-16)

### Day 6-7: Dashboard Widget

**Task**: React component for compliance display

```typescript
// frontend/web/src/components/compliance/ComplianceWidget.tsx

import React, { useEffect, useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { AlertCircle, CheckCircle, XCircle, TrendingUp } from 'lucide-react';

interface ComplianceScore {
  total_score: number;
  grade: string;
  status: string;
  category_scores: Record<string, number>;
  violations_count: number;
  timestamp: string;
}

interface ComplianceWidgetProps {
  projectId?: string;
}

export const ComplianceWidget: React.FC<ComplianceWidgetProps> = ({ projectId }) => {
  const [score, setScore] = useState<ComplianceScore | null>(null);
  const [connected, setConnected] = useState(false);
  const [trend, setTrend] = useState<'up' | 'down' | 'stable'>('stable');
  const [previousScore, setPreviousScore] = useState<number | null>(null);

  // WebSocket connection
  useEffect(() => {
    const ws = new WebSocket(`${process.env.NEXT_PUBLIC_WS_URL}/api/v1/compliance/ws`);
    
    ws.onopen = () => {
      setConnected(true);
      console.log('Compliance WebSocket connected');
    };
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      
      if (message.event === 'score_update') {
        // Calculate trend
        if (score) {
          if (message.data.total_score > score.total_score) {
            setTrend('up');
          } else if (message.data.total_score < score.total_score) {
            setTrend('down');
          } else {
            setTrend('stable');
          }
          setPreviousScore(score.total_score);
        }
        
        setScore(message.data);
      }
    };
    
    ws.onclose = () => {
      setConnected(false);
      console.log('Compliance WebSocket disconnected');
    };
    
    // Ping every 30 seconds
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send('ping');
      }
    }, 30000);
    
    return () => {
      clearInterval(pingInterval);
      ws.close();
    };
  }, []);

  // Initial fetch
  useEffect(() => {
    fetch('/api/v1/compliance/score')
      .then(res => res.json())
      .then(data => setScore(data))
      .catch(console.error);
  }, [projectId]);

  if (!score) {
    return (
      <Card className="w-full">
        <CardContent className="p-6">
          <div className="animate-pulse flex space-x-4">
            <div className="flex-1 space-y-4">
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const getGradeColor = (grade: string) => {
    switch (grade) {
      case 'A': return 'bg-green-500';
      case 'B': return 'bg-blue-500';
      case 'C': return 'bg-yellow-500';
      case 'D': return 'bg-orange-500';
      default: return 'bg-red-500';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 70) return 'text-blue-600';
    if (score >= 50) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <Card className="w-full">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-lg font-medium">SDLC Compliance</CardTitle>
        <div className="flex items-center gap-2">
          {connected ? (
            <Badge variant="outline" className="text-green-600 border-green-600">
              <span className="w-2 h-2 bg-green-500 rounded-full mr-1 animate-pulse"></span>
              Live
            </Badge>
          ) : (
            <Badge variant="outline" className="text-gray-400">
              Offline
            </Badge>
          )}
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Main Score */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className={`w-16 h-16 rounded-full ${getGradeColor(score.grade)} flex items-center justify-center`}>
              <span className="text-2xl font-bold text-white">{score.grade}</span>
            </div>
            <div>
              <div className={`text-3xl font-bold ${getScoreColor(score.total_score)}`}>
                {score.total_score}%
              </div>
              <div className="text-sm text-gray-500">{score.status}</div>
            </div>
          </div>
          
          {/* Trend indicator */}
          {previousScore !== null && (
            <div className="flex items-center gap-1">
              {trend === 'up' && (
                <TrendingUp className="w-5 h-5 text-green-500" />
              )}
              {trend === 'down' && (
                <TrendingUp className="w-5 h-5 text-red-500 transform rotate-180" />
              )}
              <span className={`text-sm ${
                trend === 'up' ? 'text-green-500' : 
                trend === 'down' ? 'text-red-500' : 
                'text-gray-400'
              }`}>
                {trend === 'up' && '+'}
                {(score.total_score - previousScore).toFixed(1)}
              </span>
            </div>
          )}
        </div>
        
        {/* Category Breakdown */}
        <div className="space-y-2">
          <div className="text-sm font-medium text-gray-600">Category Scores</div>
          
          {Object.entries(score.category_scores).map(([category, categoryScore]) => (
            <div key={category} className="space-y-1">
              <div className="flex justify-between text-sm">
                <span className="capitalize">{category}</span>
                <span className={getScoreColor(categoryScore)}>{categoryScore.toFixed(0)}%</span>
              </div>
              <Progress value={categoryScore} className="h-2" />
            </div>
          ))}
        </div>
        
        {/* Violations Summary */}
        {score.violations_count > 0 && (
          <div className="flex items-center gap-2 p-2 bg-yellow-50 rounded-md">
            <AlertCircle className="w-4 h-4 text-yellow-600" />
            <span className="text-sm text-yellow-700">
              {score.violations_count} violation{score.violations_count > 1 ? 's' : ''} detected
            </span>
          </div>
        )}
        
        {/* Last Updated */}
        <div className="text-xs text-gray-400 text-right">
          Updated: {new Date(score.timestamp).toLocaleTimeString()}
        </div>
      </CardContent>
    </Card>
  );
};

export default ComplianceWidget;
```

---

### Day 8: VS Code Extension Integration

**Task**: Add compliance display to VS Code extension

```typescript
// vscode-extension/src/compliance/ComplianceProvider.ts

import * as vscode from 'vscode';

interface ComplianceScore {
  totalScore: number;
  grade: string;
  status: string;
  categoryScores: Record<string, number>;
  violationsCount: number;
}

export class ComplianceProvider implements vscode.TreeDataProvider<ComplianceItem> {
  private _onDidChangeTreeData = new vscode.EventEmitter<ComplianceItem | undefined>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;
  
  private score: ComplianceScore | null = null;
  private websocket: WebSocket | null = null;

  constructor() {
    this.connectWebSocket();
    this.fetchInitialScore();
  }

  private connectWebSocket() {
    const wsUrl = vscode.workspace.getConfiguration('sdlc').get<string>('serverUrl');
    if (!wsUrl) return;

    this.websocket = new WebSocket(`${wsUrl.replace('http', 'ws')}/api/v1/compliance/ws`);
    
    this.websocket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.event === 'score_update') {
        this.score = {
          totalScore: message.data.total_score,
          grade: message.data.grade,
          status: message.data.status,
          categoryScores: message.data.category_scores,
          violationsCount: message.data.violations_count,
        };
        this._onDidChangeTreeData.fire(undefined);
      }
    };
  }

  private async fetchInitialScore() {
    const serverUrl = vscode.workspace.getConfiguration('sdlc').get<string>('serverUrl');
    if (!serverUrl) return;

    try {
      const response = await fetch(`${serverUrl}/api/v1/compliance/score`);
      const data = await response.json();
      
      this.score = {
        totalScore: data.total_score,
        grade: data.grade,
        status: data.status,
        categoryScores: data.category_scores,
        violationsCount: data.violations_count,
      };
      
      this._onDidChangeTreeData.fire(undefined);
    } catch (error) {
      console.error('Failed to fetch compliance score:', error);
    }
  }

  getTreeItem(element: ComplianceItem): vscode.TreeItem {
    return element;
  }

  getChildren(element?: ComplianceItem): Thenable<ComplianceItem[]> {
    if (!this.score) {
      return Promise.resolve([
        new ComplianceItem('Loading...', '', vscode.TreeItemCollapsibleState.None)
      ]);
    }

    if (!element) {
      // Root items
      return Promise.resolve([
        new ComplianceItem(
          `Score: ${this.score.totalScore}% (${this.score.grade})`,
          this.score.status,
          vscode.TreeItemCollapsibleState.Collapsed,
          this.getScoreIcon(this.score.totalScore)
        ),
        new ComplianceItem(
          'Categories',
          '',
          vscode.TreeItemCollapsibleState.Collapsed,
          new vscode.ThemeIcon('list-tree')
        ),
      ]);
    }

    // Category children
    if (element.label === 'Categories') {
      return Promise.resolve(
        Object.entries(this.score.categoryScores).map(([category, score]) => 
          new ComplianceItem(
            `${this.capitalize(category)}: ${score.toFixed(0)}%`,
            '',
            vscode.TreeItemCollapsibleState.None,
            this.getScoreIcon(score)
          )
        )
      );
    }

    return Promise.resolve([]);
  }

  private getScoreIcon(score: number): vscode.ThemeIcon {
    if (score >= 90) return new vscode.ThemeIcon('check', new vscode.ThemeColor('charts.green'));
    if (score >= 70) return new vscode.ThemeIcon('check', new vscode.ThemeColor('charts.blue'));
    if (score >= 50) return new vscode.ThemeIcon('warning', new vscode.ThemeColor('charts.yellow'));
    return new vscode.ThemeIcon('error', new vscode.ThemeColor('charts.red'));
  }

  private capitalize(s: string): string {
    return s.charAt(0).toUpperCase() + s.slice(1);
  }

  refresh(): void {
    this.fetchInitialScore();
  }

  dispose(): void {
    if (this.websocket) {
      this.websocket.close();
    }
  }
}

class ComplianceItem extends vscode.TreeItem {
  constructor(
    public readonly label: string,
    public readonly description: string,
    public readonly collapsibleState: vscode.TreeItemCollapsibleState,
    public readonly iconPath?: vscode.ThemeIcon
  ) {
    super(label, collapsibleState);
    this.description = description;
  }
}

// Register in extension.ts
export function activate(context: vscode.ExtensionContext) {
  const complianceProvider = new ComplianceProvider();
  
  context.subscriptions.push(
    vscode.window.registerTreeDataProvider('sdlcCompliance', complianceProvider),
    vscode.commands.registerCommand('sdlc.refreshCompliance', () => {
      complianceProvider.refresh();
    })
  );
}
```

---

### Day 9-10: Testing & Documentation

**Task**: Integration tests and user guide

```python
# tests/integration/test_compliance_realtime.py

import pytest
import asyncio
from pathlib import Path
import tempfile

class TestRealtimeCompliance:
    """Integration tests for real-time compliance monitoring"""
    
    @pytest.fixture
    def docs_with_issues(self, tmp_path):
        """Create docs folder with compliance issues"""
        docs = tmp_path / "docs" / "00-foundation"
        docs.mkdir(parents=True)
        
        # File with missing headers
        (docs / "readme.md").write_text("# README\n\nNo headers here.")
        
        return tmp_path
    
    async def test_watcher_detects_changes(self, docs_with_issues):
        """File watcher should detect changes within 500ms"""
        from sdlcctl.compliance.watcher import ComplianceWatcher, FileChange
        
        changes = []
        
        def on_change(change: FileChange):
            changes.append(change)
        
        watcher = ComplianceWatcher(docs_with_issues / "docs", on_change)
        watcher.start()
        
        try:
            # Create a new file
            new_file = docs_with_issues / "docs" / "00-foundation" / "new.md"
            new_file.write_text("# New File\n")
            
            # Wait for debounce
            await asyncio.sleep(1.0)
            
            assert len(changes) >= 1
            assert changes[0].event_type == "created"
            
        finally:
            watcher.stop()
    
    async def test_scorer_calculates_correctly(self, docs_with_issues):
        """Scorer should calculate correct compliance score"""
        from sdlcctl.compliance.scorer import ComplianceScorer
        from sdlcctl.migration.config_generator import SDLCConfig
        
        config = SDLCConfig(sdlc_version="5.1.0")
        scorer = ComplianceScorer(config)
        
        score = scorer.score(docs_with_issues / "docs")
        
        # File without headers should have low score
        assert score.total_score < 100
        assert len(score.violations) > 0
        
        # Check category scores exist
        assert "header" in score.category_scores
        assert "naming" in score.category_scores
    
    async def test_websocket_broadcasts_updates(self):
        """WebSocket should broadcast score updates to all clients"""
        from app.services.compliance_websocket import ComplianceWebSocketManager, ComplianceUpdate
        
        manager = ComplianceWebSocketManager()
        
        # Mock WebSocket
        class MockWebSocket:
            def __init__(self):
                self.messages = []
            
            async def accept(self):
                pass
            
            async def send_text(self, message: str):
                self.messages.append(message)
        
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()
        
        await manager.connect(ws1)
        await manager.connect(ws2)
        
        # Broadcast update
        await manager.broadcast(ComplianceUpdate(
            event_type="score_update",
            data={"total_score": 85.0}
        ))
        
        # Both clients should receive
        assert len(ws1.messages) == 1
        assert len(ws2.messages) == 1
        assert "85.0" in ws1.messages[0]
```

---

## Deliverables

| # | Deliverable | Status |
|---|-------------|--------|
| 1 | `ComplianceWatcher` with debouncing | ⏳ |
| 2 | `ComplianceScorer` with 9 rules | ⏳ |
| 3 | WebSocket notification service | ⏳ |
| 4 | React `ComplianceWidget` | ⏳ |
| 5 | VS Code extension integration | ⏳ |
| 6 | Integration tests | ⏳ |
| 7 | User documentation | ⏳ |

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| High CPU on large repos | Medium | Medium | Debounce + selective scanning |
| WebSocket disconnects | Low | Low | Auto-reconnect in client |
| Score calculation slow | Low | Low | Cache + incremental updates |

---

*Sprint planned: December 21, 2025*
*CTO Approval: Pending*
