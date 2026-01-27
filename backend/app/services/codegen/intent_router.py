"""
Intent Router - Route codegen requests to appropriate provider

SDLC Framework Compliance:
- Framework: SDLC 5.2.0 (7-Pillar + AI Governance Principles)
- Pillar 3: Build Phase - Multi-Provider Orchestration
- AI Governance Principle 3: Context-Aware Decision Making
- Methodology: Risk-based routing with confidence thresholds

Purpose:
Detects user intent from spec description and routes to:
- app-builder: NEW_SCAFFOLD (confidence ≥ 0.75)
- ollama/claude: MODIFY_EXISTING, FEATURE_ADD
- ep06-sme: DOMAIN_SME (Vietnamese SME templates)

Prevents misrouting (e.g., scaffolding when user wants to modify existing code).

Sprint: 106 - App Builder Integration (MVP)
Date: January 27, 2026
Owner: Backend Team
"""

from enum import Enum
from typing import Tuple, Optional
from pydantic import BaseModel
import re

from app.schemas.codegen.template_blueprint import TemplateType


class IntentType(str, Enum):
    """Request intent types for routing"""
    NEW_SCAFFOLD = "new_scaffold"      # → app-builder provider
    MODIFY_EXISTING = "modify"         # → ollama/claude provider
    DOMAIN_SME = "domain_sme"          # → EP-06 Vietnamese templates
    FEATURE_ADD = "feature_add"        # → ollama/claude provider
    UNKNOWN = "unknown"                # → manual routing (default: ollama)


class IntentDetectionResult(BaseModel):
    """Result of intent detection with confidence score"""
    intent: IntentType
    confidence: float  # 0.0 to 1.0
    recommended_provider: str
    reasoning: str
    matched_keywords: list[str] = []


class IntentRouter:
    """
    Detect user intent and route to appropriate provider
    
    Routing Rules (Priority Order):
    1. Existing repo context → MODIFY_EXISTING (0.95 confidence)
    2. Vietnamese SME domain → DOMAIN_SME (0.85-0.90 confidence)
    3. Scaffold keywords → NEW_SCAFFOLD (0.50-0.85 confidence)
    4. Modify keywords → FEATURE_ADD (0.40-0.80 confidence)
    5. Fallback → UNKNOWN (0.30 confidence, default to Ollama)
    
    Confidence Threshold:
    - ≥ 0.75: Use app-builder
    - < 0.75: Fallback to Ollama/Claude
    
    Example:
        router = IntentRouter()
        
        # Scaffold request
        spec = CodegenSpec(description="Create a Next.js blog with Prisma")
        result = router.detect_intent(spec)
        # → IntentType.NEW_SCAFFOLD, confidence=0.85
        
        # Modify request
        spec = CodegenSpec(description="Add comments to posts", has_repo=True)
        result = router.detect_intent(spec, has_existing_repo=True)
        # → IntentType.MODIFY_EXISTING, confidence=0.95
    """
    
    # Keywords for each intent type
    NEW_SCAFFOLD_KEYWORDS = [
        "create", "new", "scaffold", "bootstrap", "init", "initialize",
        "start", "generate project", "build app", "make app", "setup",
        "tạo mới", "khởi tạo", "tạo dự án",
    ]
    
    MODIFY_KEYWORDS = [
        "modify", "change", "update", "refactor", "fix", "improve",
        "optimize", "add feature to", "enhance", "adjust", "tweak",
        "sửa", "cải thiện", "thay đổi", "chỉnh sửa",
    ]
    
    DOMAIN_SME_KEYWORDS = {
        # F&B
        "restaurant", "cafe", "food", "fnb", "kitchen", "menu", "order",
        "nhà hàng", "quán ăn", "quán cafe", "đồ ăn", "thực đơn",
        
        # Hospitality
        "hotel", "resort", "hospitality", "booking", "reservation", "room",
        "khách sạn", "khu nghỉ dưỡng", "đặt phòng",
        
        # Retail
        "shop", "store", "retail", "ecommerce", "e-commerce", "product", "cart",
        "cửa hàng", "bán lẻ", "sản phẩm", "giỏ hàng",
    }
    
    # Template detection patterns
    TEMPLATE_PATTERNS = {
        TemplateType.NEXTJS_FULLSTACK: [
            r'\bnext\.?js\b', r'\bnextjs\b', r'\breact.*full.*stack\b',
        ],
        TemplateType.NEXTJS_SAAS: [
            r'\bnext\.?js.*saas\b', r'\bsaas.*next\.?js\b', r'\bstripe\b', r'\bpayment\b',
        ],
        TemplateType.FASTAPI: [
            r'\bfastapi\b', r'\bfast.*api\b', r'\bpython.*api\b',
        ],
        TemplateType.REACT_NATIVE: [
            r'\breact.*native\b', r'\brn\b', r'\bexpo\b', r'\bmobile.*app\b',
        ],
    }
    
    def __init__(self, confidence_threshold: float = 0.75):
        """
        Initialize Intent Router
        
        Args:
            confidence_threshold: Minimum confidence to use app-builder (default: 0.75)
        """
        self.confidence_threshold = confidence_threshold
    
    def detect_intent(
        self,
        description: str,
        domain: Optional[str] = None,
        has_existing_repo: bool = False
    ) -> IntentDetectionResult:
        """
        Detect intent from spec description and context
        
        Args:
            description: User's codegen request description
            domain: Optional domain hint (e.g., "fnb", "retail")
            has_existing_repo: True if user has uploaded repo context
        
        Returns:
            IntentDetectionResult with confidence score and routing recommendation
        """
        description_lower = description.lower()
        
        # Rule 1: Existing repo context → MODIFY_EXISTING (high confidence)
        if has_existing_repo:
            # Edge case: "new module" in existing repo
            if self._contains_new_module_keyword(description_lower):
                return IntentDetectionResult(
                    intent=IntentType.NEW_SCAFFOLD,
                    confidence=0.80,
                    recommended_provider="app-builder",
                    reasoning="New module in existing repo (scaffold new component)",
                    matched_keywords=["new module", "repo context"]
                )
            
            return IntentDetectionResult(
                intent=IntentType.MODIFY_EXISTING,
                confidence=0.95,
                recommended_provider="ollama",
                reasoning="Existing repository context detected"
            )
        
        # Rule 2: Vietnamese SME domain → DOMAIN_SME (high confidence)
        if domain and domain.lower() in ["fnb", "retail", "hospitality"]:
            return IntentDetectionResult(
                intent=IntentType.DOMAIN_SME,
                confidence=0.90,
                recommended_provider="ep06-sme",
                reasoning=f"Vietnamese SME domain: {domain}"
            )
        
        # Check for SME keywords in description
        sme_keywords = [kw for kw in self.DOMAIN_SME_KEYWORDS if kw in description_lower]
        if sme_keywords:
            return IntentDetectionResult(
                intent=IntentType.DOMAIN_SME,
                confidence=0.85,
                recommended_provider="ep06-sme",
                reasoning="Vietnamese SME keywords detected",
                matched_keywords=sme_keywords
            )
        
        # Rule 3: Scaffold keywords → NEW_SCAFFOLD (medium-high confidence)
        scaffold_matches = [kw for kw in self.NEW_SCAFFOLD_KEYWORDS if kw in description_lower]
        scaffold_score = len(scaffold_matches) / len(self.NEW_SCAFFOLD_KEYWORDS)
        
        # Boost confidence if template explicitly mentioned
        template_detected = self._detect_template(description_lower)
        if template_detected:
            scaffold_score = min(1.0, scaffold_score + 0.30)  # +30% boost
        
        if scaffold_score > 0.15:  # At least 15% keywords match
            confidence = min(0.90, 0.50 + scaffold_score)
            return IntentDetectionResult(
                intent=IntentType.NEW_SCAFFOLD,
                confidence=confidence,
                recommended_provider="app-builder",
                reasoning=f"Scaffold keywords detected (score: {scaffold_score:.2f})",
                matched_keywords=scaffold_matches[:5]  # Top 5
            )
        
        # Rule 4: Modify keywords → FEATURE_ADD (medium confidence)
        modify_matches = [kw for kw in self.MODIFY_KEYWORDS if kw in description_lower]
        modify_score = len(modify_matches) / len(self.MODIFY_KEYWORDS)
        
        if modify_score > 0.10:
            confidence = min(0.80, 0.40 + modify_score)
            return IntentDetectionResult(
                intent=IntentType.FEATURE_ADD,
                confidence=confidence,
                recommended_provider="ollama",
                reasoning=f"Modify keywords detected (score: {modify_score:.2f})",
                matched_keywords=modify_matches[:5]
            )
        
        # Rule 5: Fallback → UNKNOWN (low confidence)
        return IntentDetectionResult(
            intent=IntentType.UNKNOWN,
            confidence=0.30,
            recommended_provider="ollama",  # Safe default
            reasoning="No clear intent detected, defaulting to Ollama"
        )
    
    def should_use_app_builder(self, detection: IntentDetectionResult) -> bool:
        """
        Decide if app-builder should be used based on intent + confidence
        
        Args:
            detection: Intent detection result
        
        Returns:
            True if app-builder should be used, False otherwise
        """
        return (
            detection.intent == IntentType.NEW_SCAFFOLD and
            detection.confidence >= self.confidence_threshold
        )
    
    def _detect_template(self, description_lower: str) -> Optional[str]:
        """
        Detect if a specific template is mentioned
        
        Args:
            description_lower: Lowercase description
        
        Returns:
            Template name if detected, None otherwise
        """
        for template, patterns in self.TEMPLATE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, description_lower, re.IGNORECASE):
                    return template.value
        return None
    
    def _contains_new_module_keyword(self, description_lower: str) -> bool:
        """Check if description mentions creating a new module/component"""
        new_module_keywords = [
            "new module", "new component", "new feature", "new page",
            "add new", "create new", "module mới", "component mới"
        ]
        return any(kw in description_lower for kw in new_module_keywords)
    
    def get_routing_summary(self, detection: IntentDetectionResult) -> str:
        """
        Get human-readable routing summary for logging
        
        Args:
            detection: Intent detection result
        
        Returns:
            Formatted summary string
        """
        return (
            f"Intent: {detection.intent.value} "
            f"(confidence: {detection.confidence:.2f}) → "
            f"Provider: {detection.recommended_provider}"
        )


# Import TemplateType from template_blueprint
try:
    from backend.app.schemas.codegen.template_blueprint import TemplateType
except ImportError:
    # Fallback if import fails (for testing)
    from enum import Enum
    class TemplateType(str, Enum):
        NEXTJS_FULLSTACK = "nextjs-fullstack"
        NEXTJS_SAAS = "nextjs-saas"
        FASTAPI = "fastapi"
        REACT_NATIVE = "react-native"
