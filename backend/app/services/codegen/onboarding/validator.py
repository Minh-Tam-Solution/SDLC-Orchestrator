"""
Vietnamese Onboarding Input Validator.

Sprint 47: Vietnamese Domain Templates + Onboarding IR (EP-06)

This module validates user input during the onboarding flow:
- App name validation (Vietnamese diacritics support)
- Domain selection validation
- Feature selection validation
- Scale validation

Author: Backend Lead
Date: December 23, 2025
Status: ACTIVE
"""

import re
import unicodedata
from dataclasses import dataclass
from typing import List, Optional, Tuple

from .prompts import VIETNAMESE_PROMPTS, FEATURE_LABELS_VI


@dataclass
class ValidationResult:
    """Result of input validation."""

    valid: bool
    message: str  # Error message if invalid, empty if valid
    normalized_value: Optional[str] = None  # Normalized/cleaned value


class OnboardingValidator:
    """
    Validates onboarding input for Vietnamese SME founders.

    Handles:
    - Vietnamese diacritics (Nguyen → Nguyen)
    - Non-ASCII characters
    - Business name variations
    - Feature validation per domain

    Example:
        >>> validator = OnboardingValidator()
        >>> result = validator.validate_app_name("Quan Com Ba Hai")
        >>> result.valid
        True
        >>> result.normalized_value
        "QuanComBaHai"
    """

    # Regex for valid app names (after normalization)
    # Allows letters, numbers, Vietnamese without diacritics
    APP_NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9]*$")

    # Max length for app name
    MAX_APP_NAME_LENGTH = 50

    # Min/max features
    MIN_FEATURES = 2
    MAX_FEATURES = 10

    # Valid domains
    VALID_DOMAINS = {"restaurant", "hotel", "retail", "ecommerce", "hrm", "crm"}

    # Valid scales
    VALID_SCALES = {"micro", "small", "medium", "large"}

    def __init__(self):
        """Initialize validator with prompts."""
        self.prompts = VIETNAMESE_PROMPTS

    def validate_app_name(self, name: str) -> ValidationResult:
        """
        Validate and normalize app name.

        Handles Vietnamese diacritics by removing them:
        - "Quan Com Ngon" → "QuanComNgon"
        - "Nha Hang 99" → "NhaHang99"
        - "Pho 24" → "Pho24"

        Args:
            name: Raw app name input (can contain Vietnamese, spaces)

        Returns:
            ValidationResult with normalized PascalCase name
        """
        if not name or not name.strip():
            return ValidationResult(
                valid=False,
                message=self.prompts.error_required_field
            )

        # Remove leading/trailing whitespace
        name = name.strip()

        # Check original length (before normalization)
        if len(name) > self.MAX_APP_NAME_LENGTH * 2:  # Allow for spaces
            return ValidationResult(
                valid=False,
                message=f"Ten qua dai (toi da {self.MAX_APP_NAME_LENGTH} ky tu)"
            )

        # Normalize: remove Vietnamese diacritics
        normalized = self._remove_diacritics(name)

        # Convert to PascalCase: "Quan Com Ngon" → "QuanComNgon"
        pascal_case = self._to_pascal_case(normalized)

        # Validate normalized name
        if not pascal_case:
            return ValidationResult(
                valid=False,
                message=self.prompts.error_invalid_name
            )

        if not self.APP_NAME_PATTERN.match(pascal_case):
            return ValidationResult(
                valid=False,
                message=self.prompts.error_invalid_name
            )

        if len(pascal_case) > self.MAX_APP_NAME_LENGTH:
            return ValidationResult(
                valid=False,
                message=f"Ten qua dai (toi da {self.MAX_APP_NAME_LENGTH} ky tu)"
            )

        return ValidationResult(
            valid=True,
            message="",
            normalized_value=pascal_case
        )

    def validate_domain(self, domain: str) -> ValidationResult:
        """
        Validate domain selection.

        Args:
            domain: Domain key (restaurant, hotel, retail)

        Returns:
            ValidationResult
        """
        if not domain:
            return ValidationResult(
                valid=False,
                message=self.prompts.error_required_field
            )

        domain = domain.lower().strip()

        if domain not in self.VALID_DOMAINS:
            valid_options = ", ".join(self.VALID_DOMAINS)
            return ValidationResult(
                valid=False,
                message=f"Loai hinh khong hop le. Chon: {valid_options}"
            )

        return ValidationResult(
            valid=True,
            message="",
            normalized_value=domain
        )

    def validate_features(
        self, domain: str, features: List[str]
    ) -> ValidationResult:
        """
        Validate feature selection for a domain.

        Args:
            domain: Domain key
            features: List of feature keys selected

        Returns:
            ValidationResult with normalized feature list
        """
        if not features:
            return ValidationResult(
                valid=False,
                message=self.prompts.error_min_features
            )

        if len(features) < self.MIN_FEATURES:
            return ValidationResult(
                valid=False,
                message=f"Vui long chon it nhat {self.MIN_FEATURES} tinh nang"
            )

        if len(features) > self.MAX_FEATURES:
            return ValidationResult(
                valid=False,
                message=f"Toi da {self.MAX_FEATURES} tinh nang"
            )

        # Get valid features for domain
        valid_features = set(FEATURE_LABELS_VI.get(domain, {}).keys())

        if not valid_features:
            return ValidationResult(
                valid=False,
                message="Loai hinh kinh doanh khong hop le"
            )

        # Check all features are valid
        invalid = set(features) - valid_features
        if invalid:
            return ValidationResult(
                valid=False,
                message=f"Tinh nang khong hop le: {', '.join(invalid)}"
            )

        # Normalize to list (remove duplicates, sort)
        normalized = sorted(set(features))

        return ValidationResult(
            valid=True,
            message="",
            normalized_value=",".join(normalized)
        )

    def validate_scale(self, scale: str) -> ValidationResult:
        """
        Validate business scale selection.

        Args:
            scale: Scale key (micro, small, medium, large)

        Returns:
            ValidationResult
        """
        if not scale:
            return ValidationResult(
                valid=False,
                message=self.prompts.error_required_field
            )

        scale = scale.lower().strip()

        if scale not in self.VALID_SCALES:
            valid_options = ", ".join(self.VALID_SCALES)
            return ValidationResult(
                valid=False,
                message=f"Quy mo khong hop le. Chon: {valid_options}"
            )

        return ValidationResult(
            valid=True,
            message="",
            normalized_value=scale
        )

    def validate_all(
        self,
        app_name: str,
        domain: str,
        features: List[str],
        scale: str
    ) -> Tuple[bool, List[str], dict]:
        """
        Validate all onboarding inputs at once.

        Args:
            app_name: App name input
            domain: Domain selection
            features: Feature selections
            scale: Scale selection

        Returns:
            Tuple of (all_valid, error_messages, normalized_values)
        """
        errors = []
        normalized = {}

        # Validate app name
        name_result = self.validate_app_name(app_name)
        if not name_result.valid:
            errors.append(f"Ten ung dung: {name_result.message}")
        else:
            normalized["app_name"] = name_result.normalized_value

        # Validate domain
        domain_result = self.validate_domain(domain)
        if not domain_result.valid:
            errors.append(f"Loai hinh: {domain_result.message}")
        else:
            normalized["domain"] = domain_result.normalized_value

        # Validate features (only if domain is valid)
        if domain_result.valid:
            features_result = self.validate_features(
                domain_result.normalized_value, features
            )
            if not features_result.valid:
                errors.append(f"Tinh nang: {features_result.message}")
            else:
                normalized["features"] = features_result.normalized_value.split(",")
        else:
            errors.append("Tinh nang: Vui long chon loai hinh truoc")

        # Validate scale
        scale_result = self.validate_scale(scale)
        if not scale_result.valid:
            errors.append(f"Quy mo: {scale_result.message}")
        else:
            normalized["scale"] = scale_result.normalized_value

        return (len(errors) == 0, errors, normalized)

    def _remove_diacritics(self, text: str) -> str:
        """
        Remove Vietnamese diacritics from text.

        Examples:
            - "Nguyen" → "Nguyen"
            - "Pho" → "Pho"
            - "Bun bo Hue" → "Bun bo Hue"
        """
        # Normalize to NFD (decomposed form)
        normalized = unicodedata.normalize("NFD", text)

        # Remove combining diacritical marks
        result = "".join(
            char for char in normalized
            if unicodedata.category(char) != "Mn"
        )

        # Handle special Vietnamese characters that aren't just diacritics
        replacements = {
            "đ": "d", "Đ": "D",
            "ư": "u", "Ư": "U",
            "ơ": "o", "Ơ": "O",
        }
        for old, new in replacements.items():
            result = result.replace(old, new)

        return result

    def _to_pascal_case(self, text: str) -> str:
        """
        Convert text to PascalCase.

        Examples:
            - "quan com ngon" → "QuanComNgon"
            - "nha hang 99" → "NhaHang99"
            - "ABC DEF" → "AbcDef"
        """
        # Split by whitespace and non-alphanumeric
        words = re.split(r"[\s\-_]+", text)

        # Capitalize each word, then join
        pascal_words = []
        for word in words:
            if word:
                # Handle all-uppercase words
                if word.isupper() and len(word) > 1:
                    word = word.capitalize()
                else:
                    word = word[0].upper() + word[1:]
                pascal_words.append(word)

        return "".join(pascal_words)
