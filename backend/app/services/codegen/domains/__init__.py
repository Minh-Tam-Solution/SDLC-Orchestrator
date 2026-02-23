"""
Vietnamese Domain Templates Package.

Sprint 47: Vietnamese SME Domain Templates
ADR-023: IR-Based Deterministic Code Generation

This package provides domain-specific template blueprints for Vietnamese SME market:
- F&B (Food & Beverage): Restaurant, Café, Bar management
- Hospitality: Hotel, Homestay, Resort management
- Retail: Shop, Store, E-commerce management

Each domain provides:
- Pre-defined entities with Vietnamese field descriptions
- Common business logic patterns
- Industry-specific validations
- Localized field names and comments

Target Market: Founder Plan ($99/team/month) - Vietnam SME
Goal: <10 minutes from onboarding to valid AppBlueprint

Author: Backend Lead
Date: December 23, 2025
Version: 1.0.0
Status: ACTIVE - Sprint 47 Implementation
"""

from .base import (
    DomainTemplate,
    DomainEntity,
    DomainField,
    DomainRelationship,
    DomainRegistry,
)
from .fnb import FnBDomainTemplate
from .hospitality import HospitalityDomainTemplate
from .retail import RetailDomainTemplate
from .ecommerce import EcommerceDomainTemplate
from .hrm import HrmDomainTemplate
from .crm import CrmDomainTemplate

__all__ = [
    # Base classes
    "DomainTemplate",
    "DomainEntity",
    "DomainField",
    "DomainRelationship",
    "DomainRegistry",
    # Domain templates
    "FnBDomainTemplate",
    "HospitalityDomainTemplate",
    "RetailDomainTemplate",
    "EcommerceDomainTemplate",
    "HrmDomainTemplate",
    "CrmDomainTemplate",
]
