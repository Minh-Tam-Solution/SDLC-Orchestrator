"""
Vietnamese Onboarding Service.

Sprint 47: Vietnamese Domain Templates + Onboarding IR (EP-06)

This module provides the core onboarding service that converts
Vietnamese questionnaire input into valid AppBlueprint IR.

Flow:
1. User selects domain (restaurant, hotel, retail)
2. User enters app name (Vietnamese OK)
3. User selects features (modules)
4. User selects scale
5. Service generates AppBlueprint IR

Author: Backend Lead
Date: December 23, 2025
Status: ACTIVE
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from ..domains import (
    DomainRegistry,
    DomainTemplate,
    FnBDomainTemplate,
    HospitalityDomainTemplate,
    RetailDomainTemplate,
    EcommerceDomainTemplate,
    HrmDomainTemplate,
    CrmDomainTemplate,
)
from ..domains.cgf_metadata import get_domain_cgf_mapping
from .prompts import (
    FEATURE_LABELS_VI,
    SCALE_TO_CGF_TIER,
    SCALE_TO_EMPLOYEE_RANGE,
    VIETNAMESE_PROMPTS,
)
from .validator import OnboardingValidator

logger = logging.getLogger(__name__)

# Module-level session storage (singleton pattern)
# This ensures sessions persist across OnboardingService instances
_global_sessions: Dict[str, "OnboardingSession"] = {}


class OnboardingStep(str, Enum):
    """Steps in the onboarding flow."""

    WELCOME = "welcome"
    DOMAIN = "domain"
    APP_NAME = "app_name"
    FEATURES = "features"
    SCALE = "scale"
    CONFIRM = "confirm"
    COMPLETE = "complete"


@dataclass
class OnboardingSession:
    """
    Onboarding session state.

    Tracks user progress through the onboarding wizard.
    Sessions persist until completion or expiry (1 hour).
    """

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Progress
    current_step: OnboardingStep = OnboardingStep.WELCOME
    completed_steps: List[OnboardingStep] = field(default_factory=list)

    # User input
    domain: Optional[str] = None
    app_name: Optional[str] = None  # Normalized PascalCase
    app_name_display: Optional[str] = None  # Original user input
    features: List[str] = field(default_factory=list)
    scale: Optional[str] = None

    # Generated output
    app_blueprint: Optional[Dict[str, Any]] = None
    generation_errors: List[str] = field(default_factory=list)

    # Metadata
    locale: str = "vi"  # vi or en
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None

    # Sprint 49: Time To First Value (TTFV)
    first_value_at: Optional[datetime] = None
    ttfv_ms: Optional[int] = None

    def mark_first_value(self, at: Optional[datetime] = None) -> None:
        """Mark the first time the session produced user-visible value.

        Idempotent: subsequent calls are no-ops.
        """
        if self.first_value_at is not None:
            return

        now = at or datetime.now(timezone.utc)
        self.first_value_at = now
        self.ttfv_ms = max(0, int((now - self.created_at).total_seconds() * 1000))
        self.updated_at = now

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for API response."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "first_value_at": self.first_value_at.isoformat() if self.first_value_at else None,
            "ttfv_ms": self.ttfv_ms,
            "current_step": self.current_step.value,
            "completed_steps": [s.value for s in self.completed_steps],
            "domain": self.domain,
            "app_name": self.app_name,
            "app_name_display": self.app_name_display,
            "features": self.features,
            "scale": self.scale,
            "has_blueprint": self.app_blueprint is not None,
            "generation_errors": self.generation_errors,
            "locale": self.locale,
        }


class OnboardingService:
    """
    Vietnamese SME Onboarding Service.

    Converts Vietnamese questionnaire input into valid AppBlueprint IR.

    Usage:
        >>> service = OnboardingService()
        >>> session = service.create_session()
        >>> service.set_domain(session, "restaurant")
        >>> service.set_app_name(session, "Quan Com Ngon")
        >>> service.set_features(session, ["menu", "orders", "tables"])
        >>> service.set_scale(session, "small")
        >>> blueprint = service.generate_blueprint(session)
    """

    def __init__(self, locale: str = "vi"):
        """
        Initialize onboarding service.

        Args:
            locale: UI locale (vi or en)
        """
        self.locale = locale
        self.validator = OnboardingValidator()
        self.prompts = VIETNAMESE_PROMPTS

        # Use global session storage (singleton pattern)
        # Sessions persist across service instances within same process
        self._sessions = _global_sessions

        # Domain templates
        self._domain_templates: Dict[str, type] = {
            "restaurant": FnBDomainTemplate,
            "hotel": HospitalityDomainTemplate,
            "retail": RetailDomainTemplate,
            "ecommerce": EcommerceDomainTemplate,
            "hrm": HrmDomainTemplate,
            "crm": CrmDomainTemplate,
        }

        logger.info("OnboardingService initialized with locale: %s", locale)

    def create_session(
        self,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        locale: Optional[str] = None,
    ) -> OnboardingSession:
        """
        Create new onboarding session.

        Args:
            user_agent: Browser user agent
            ip_address: Client IP address

        Returns:
            New OnboardingSession
        """
        session = OnboardingSession(
            locale=locale or self.locale,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        self._sessions[session.session_id] = session

        logger.info("Created onboarding session: %s", session.session_id)
        return session

    def get_session(self, session_id: str) -> Optional[OnboardingSession]:
        """
        Get existing session by ID.

        Args:
            session_id: Session UUID

        Returns:
            OnboardingSession if found, None otherwise
        """
        return self._sessions.get(session_id)

    def set_domain(
        self, session: OnboardingSession, domain: str
    ) -> Dict[str, Any]:
        """
        Set domain selection for session.

        Args:
            session: Onboarding session
            domain: Domain key (restaurant, hotel, retail)

        Returns:
            Dict with validation result and available features
        """
        result = self.validator.validate_domain(domain)

        if not result.valid:
            return {
                "success": False,
                "error": result.message,
            }

        session.domain = result.normalized_value
        session.updated_at = datetime.now(timezone.utc)
        self._mark_step_complete(session, OnboardingStep.DOMAIN)

        # Get available features for this domain
        features = self._get_domain_features(result.normalized_value)

        logger.info(
            "Session %s: set domain to %s",
            session.session_id, result.normalized_value
        )

        return {
            "success": True,
            "domain": result.normalized_value,
            "domain_info": self.prompts.domains.get(result.normalized_value),
            "available_features": features,
            "next_step": OnboardingStep.APP_NAME.value,
        }

    def set_app_name(
        self, session: OnboardingSession, app_name: str
    ) -> Dict[str, Any]:
        """
        Set app name for session.

        Args:
            session: Onboarding session
            app_name: User input app name (Vietnamese OK)

        Returns:
            Dict with validation result
        """
        result = self.validator.validate_app_name(app_name)

        if not result.valid:
            return {
                "success": False,
                "error": result.message,
            }

        session.app_name = result.normalized_value
        session.app_name_display = app_name.strip()
        session.updated_at = datetime.now(timezone.utc)
        self._mark_step_complete(session, OnboardingStep.APP_NAME)

        logger.info(
            "Session %s: set app_name to %s (display: %s)",
            session.session_id, result.normalized_value, app_name
        )

        return {
            "success": True,
            "app_name": result.normalized_value,
            "app_name_display": session.app_name_display,
            "next_step": OnboardingStep.FEATURES.value,
        }

    def set_features(
        self, session: OnboardingSession, features: List[str]
    ) -> Dict[str, Any]:
        """
        Set feature selection for session.

        Args:
            session: Onboarding session
            features: List of feature keys

        Returns:
            Dict with validation result
        """
        if not session.domain:
            return {
                "success": False,
                "error": "Vui long chon loai hinh kinh doanh truoc",
            }

        result = self.validator.validate_features(session.domain, features)

        if not result.valid:
            return {
                "success": False,
                "error": result.message,
            }

        session.features = result.normalized_value.split(",")
        session.updated_at = datetime.now(timezone.utc)
        self._mark_step_complete(session, OnboardingStep.FEATURES)

        logger.info(
            "Session %s: set features to %s",
            session.session_id, session.features
        )

        return {
            "success": True,
            "features": session.features,
            "feature_count": len(session.features),
            "next_step": OnboardingStep.SCALE.value,
        }

    def set_scale(
        self, session: OnboardingSession, scale: str
    ) -> Dict[str, Any]:
        """
        Set business scale for session.

        Args:
            session: Onboarding session
            scale: Scale key (micro, small, medium, large)

        Returns:
            Dict with validation result and summary
        """
        result = self.validator.validate_scale(scale)

        if not result.valid:
            return {
                "success": False,
                "error": result.message,
            }

        session.scale = result.normalized_value
        session.updated_at = datetime.now(timezone.utc)
        self._mark_step_complete(session, OnboardingStep.SCALE)

        logger.info(
            "Session %s: set scale to %s",
            session.session_id, result.normalized_value
        )

        # Generate summary for confirmation
        summary = self._generate_summary(session)

        return {
            "success": True,
            "scale": result.normalized_value,
            "cgf_tier": SCALE_TO_CGF_TIER.get(result.normalized_value),
            "employee_range": SCALE_TO_EMPLOYEE_RANGE.get(result.normalized_value),
            "summary": summary,
            "next_step": OnboardingStep.CONFIRM.value,
        }

    def generate_blueprint(
        self, session: OnboardingSession
    ) -> Dict[str, Any]:
        """
        Generate AppBlueprint IR from session data.

        Args:
            session: Completed onboarding session

        Returns:
            Dict with AppBlueprint or errors
        """
        # Validate all inputs
        valid, errors, normalized = self.validator.validate_all(
            app_name=session.app_name_display or "",
            domain=session.domain or "",
            features=session.features,
            scale=session.scale or ""
        )

        if not valid:
            session.generation_errors = errors
            return {
                "success": False,
                "errors": errors,
            }

        try:
            # Get domain template
            template_class = self._domain_templates.get(normalized["domain"])
            if not template_class:
                raise ValueError(f"Unknown domain: {normalized['domain']}")

            template: DomainTemplate = template_class()

            # Map features to modules
            selected_modules = self._map_features_to_modules(
                normalized["domain"],
                normalized["features"]
            )

            # Generate blueprint
            blueprint = template.to_app_blueprint(
                app_name=normalized["app_name"],
                app_version="1.0.0",
                selected_modules=selected_modules,
            )

            # Add metadata
            blueprint["_onboarding"] = {
                "session_id": session.session_id,
                "domain": normalized["domain"],
                "scale": normalized["scale"],
                "cgf_tier": SCALE_TO_CGF_TIER.get(normalized["scale"]),
                "features_selected": normalized["features"],
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

            # Get CGF mapping
            cgf = get_domain_cgf_mapping(normalized["domain"])
            if cgf:
                blueprint["_cgf"] = {
                    "master_processes": cgf.master_processes,
                    "mdg_compliance": cgf.mdg_compliance,
                    "dag_levels": {k: v.value for k, v in cgf.dag_levels.items()},
                }

            # Store in session
            session.app_blueprint = blueprint
            session.current_step = OnboardingStep.COMPLETE
            session.updated_at = datetime.now(timezone.utc)
            self._mark_step_complete(session, OnboardingStep.CONFIRM)
            self._mark_step_complete(session, OnboardingStep.COMPLETE)

            logger.info(
                "Session %s: generated blueprint for %s",
                session.session_id, normalized["app_name"]
            )

            return {
                "success": True,
                "blueprint": blueprint,
                "stats": {
                    "modules": len(blueprint.get("modules", [])),
                    "entities": sum(
                        len(m.get("entities", []))
                        for m in blueprint.get("modules", [])
                    ),
                },
            }

        except Exception as e:
            error_msg = f"Loi tao ung dung: {str(e)}"
            session.generation_errors = [error_msg]
            logger.exception("Blueprint generation failed for session %s", session.session_id)

            return {
                "success": False,
                "errors": [error_msg],
            }

    def get_domain_options(self) -> List[Dict[str, Any]]:
        """
        Get available domain options for UI.

        Returns:
            List of domain options with Vietnamese labels
        """
        options = []
        for key, domain in self.prompts.domains.items():
            options.append({
                "key": key,
                "name": domain.name_vi,
                "name_en": domain.name_en,
                "description": domain.description_vi,
                "icon": domain.icon,
                "example_apps": domain.example_apps,
            })
        return options

    def get_feature_options(self, domain: str) -> List[Dict[str, Any]]:
        """
        Get available feature options for a domain.

        Args:
            domain: Domain key

        Returns:
            List of feature options with Vietnamese labels
        """
        return self._get_domain_features(domain)

    def get_scale_options(self) -> List[Dict[str, Any]]:
        """
        Get available scale options for UI.

        Returns:
            List of scale options with Vietnamese labels
        """
        options = []
        for key, label in self.prompts.step4_options.items():
            employee_range = SCALE_TO_EMPLOYEE_RANGE.get(key, (1, 5))
            options.append({
                "key": key,
                "label": label,
                "employee_min": employee_range[0],
                "employee_max": employee_range[1],
                "cgf_tier": SCALE_TO_CGF_TIER.get(key),
            })
        return options

    def _get_domain_features(self, domain: str) -> List[Dict[str, Any]]:
        """Get features available for a domain."""
        features = FEATURE_LABELS_VI.get(domain, {})
        result = []
        for key, info in features.items():
            result.append({
                "key": key,
                "name": info["name"],
                "description": info["description"],
            })
        return result

    def _map_features_to_modules(
        self, domain: str, features: List[str]
    ) -> List[str]:
        """
        Map user-selected features to domain module names.

        The mapping depends on domain template structure.
        """
        # Feature to module mapping per domain
        mappings = {
            "restaurant": {
                "menu": "menu",
                "orders": "orders",
                "tables": "tables",
                "reservations": "reservations",
                "kitchen_display": "orders",  # Part of orders module
                "inventory": "menu",  # Part of menu module
                "reports": "orders",  # Part of orders module
            },
            "hotel": {
                "rooms": "rooms",
                "bookings": "bookings",
                "guests": "guests",
                "billing": "billing",
                "housekeeping": "rooms",  # Part of rooms module
                "services": "billing",  # Part of billing module
                "reports": "billing",  # Part of billing module
            },
            "retail": {
                "products": "products",
                "inventory": "inventory",
                "sales": "sales",
                "customers": "customers",
                "suppliers": "inventory",  # Part of inventory module
                "promotions": "sales",  # Part of sales module
                "reports": "sales",  # Part of sales module
            },
            "ecommerce": {
                "products": "products",
                "orders": "orders",
                "customers": "customers",
                "payments": "payments",
                "categories": "products",  # Part of products module
                "shipping": "orders",  # Part of orders module
                "reports": "orders",  # Part of orders module
            },
            "hrm": {
                "employees": "employees",
                "attendance": "attendance",
                "payroll": "payroll",
                "leave": "leave",
                "contracts": "employees",  # Part of employees module
                "departments": "employees",  # Part of employees module
                "reports": "payroll",  # Part of payroll module
            },
            "crm": {
                "leads": "leads",
                "contacts": "contacts",
                "deals": "deals",
                "activities": "activities",
                "pipeline": "deals",  # Part of deals module
                "follow_ups": "activities",  # Part of activities module
                "reports": "deals",  # Part of deals module
            },
        }

        domain_mapping = mappings.get(domain, {})

        # Map features to unique modules
        modules = set()
        for feature in features:
            module = domain_mapping.get(feature, feature)
            modules.add(module)

        return sorted(modules)

    def _mark_step_complete(
        self, session: OnboardingSession, step: OnboardingStep
    ) -> None:
        """Mark a step as completed in session."""
        if step not in session.completed_steps:
            session.completed_steps.append(step)

        # Update current step to next step
        step_order = [
            OnboardingStep.WELCOME,
            OnboardingStep.DOMAIN,
            OnboardingStep.APP_NAME,
            OnboardingStep.FEATURES,
            OnboardingStep.SCALE,
            OnboardingStep.CONFIRM,
            OnboardingStep.COMPLETE,
        ]

        current_idx = step_order.index(step)
        if current_idx < len(step_order) - 1:
            session.current_step = step_order[current_idx + 1]

    def _generate_summary(self, session: OnboardingSession) -> Dict[str, Any]:
        """Generate summary for confirmation step."""
        domain_info = self.prompts.domains.get(session.domain)
        feature_labels = FEATURE_LABELS_VI.get(session.domain, {})

        # Get feature names
        feature_names = []
        for f in session.features:
            label_info = feature_labels.get(f, {})
            feature_names.append(label_info.get("name", f))

        return {
            "app_name": session.app_name_display,
            "app_name_normalized": session.app_name,
            "domain": domain_info.name_vi if domain_info else session.domain,
            "domain_icon": domain_info.icon if domain_info else "",
            "features": feature_names,
            "feature_count": len(session.features),
            "scale": self.prompts.step4_options.get(session.scale, session.scale),
            "cgf_tier": SCALE_TO_CGF_TIER.get(session.scale),
        }
