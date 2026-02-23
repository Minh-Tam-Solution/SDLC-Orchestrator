"""
Tests for Vietnamese Onboarding Service.

Sprint 47: Vietnamese Domain Templates + Onboarding IR (EP-06)

Tests:
- OnboardingValidator: Vietnamese name validation, diacritics
- OnboardingService: Session management, blueprint generation
- OnboardingPrompts: Vietnamese prompts structure

Author: Backend Lead
Date: December 23, 2025
"""

import pytest
from app.services.codegen.onboarding import (
    OnboardingService,
    OnboardingSession,
    OnboardingStep,
    OnboardingValidator,
    OnboardingPrompts,
    VIETNAMESE_PROMPTS,
)
from app.services.codegen.onboarding.prompts import (
    FEATURE_LABELS_VI,
    SCALE_TO_CGF_TIER,
)


class TestOnboardingValidator:
    """Tests for OnboardingValidator."""

    def test_validate_simple_app_name(self):
        """Test simple app name validation."""
        validator = OnboardingValidator()

        result = validator.validate_app_name("MyApp")
        assert result.valid is True
        assert result.normalized_value == "MyApp"

    def test_validate_vietnamese_app_name(self):
        """Test Vietnamese app name with spaces."""
        validator = OnboardingValidator()

        result = validator.validate_app_name("Quan Com Ngon")
        assert result.valid is True
        assert result.normalized_value == "QuanComNgon"

    def test_validate_vietnamese_with_diacritics(self):
        """Test Vietnamese name with diacritics removed."""
        validator = OnboardingValidator()

        # Vietnamese diacritics should be normalized
        result = validator.validate_app_name("Pho 24")
        assert result.valid is True
        assert result.normalized_value == "Pho24"

    def test_validate_app_name_with_numbers(self):
        """Test app name with numbers."""
        validator = OnboardingValidator()

        result = validator.validate_app_name("Shop 365")
        assert result.valid is True
        assert result.normalized_value == "Shop365"

    def test_validate_empty_app_name(self):
        """Test empty app name is invalid."""
        validator = OnboardingValidator()

        result = validator.validate_app_name("")
        assert result.valid is False
        assert result.message != ""

    def test_validate_whitespace_only_app_name(self):
        """Test whitespace-only app name is invalid."""
        validator = OnboardingValidator()

        result = validator.validate_app_name("   ")
        assert result.valid is False

    def test_validate_domain_restaurant(self):
        """Test restaurant domain validation."""
        validator = OnboardingValidator()

        result = validator.validate_domain("restaurant")
        assert result.valid is True
        assert result.normalized_value == "restaurant"

    def test_validate_domain_hotel(self):
        """Test hotel domain validation."""
        validator = OnboardingValidator()

        result = validator.validate_domain("Hotel")  # Case insensitive
        assert result.valid is True
        assert result.normalized_value == "hotel"

    def test_validate_domain_retail(self):
        """Test retail domain validation."""
        validator = OnboardingValidator()

        result = validator.validate_domain("RETAIL")
        assert result.valid is True
        assert result.normalized_value == "retail"

    def test_validate_invalid_domain(self):
        """Test invalid domain is rejected."""
        validator = OnboardingValidator()

        result = validator.validate_domain("factory")
        assert result.valid is False
        assert "Loai hinh khong hop le" in result.message

    def test_validate_features_minimum(self):
        """Test minimum feature requirement."""
        validator = OnboardingValidator()

        # Need at least 2 features
        result = validator.validate_features("restaurant", ["menu"])
        assert result.valid is False
        assert "it nhat" in result.message.lower()

    def test_validate_features_valid(self):
        """Test valid feature selection."""
        validator = OnboardingValidator()

        result = validator.validate_features(
            "restaurant", ["menu", "orders", "tables"]
        )
        assert result.valid is True
        assert "menu" in result.normalized_value
        assert "orders" in result.normalized_value

    def test_validate_features_invalid_feature(self):
        """Test invalid feature is rejected."""
        validator = OnboardingValidator()

        result = validator.validate_features(
            "restaurant", ["menu", "orders", "spa"]  # spa not in restaurant
        )
        assert result.valid is False
        assert "khong hop le" in result.message.lower()

    def test_validate_scale_valid(self):
        """Test valid scale options."""
        validator = OnboardingValidator()

        for scale in ["micro", "small", "medium", "large"]:
            result = validator.validate_scale(scale)
            assert result.valid is True
            assert result.normalized_value == scale

    def test_validate_scale_invalid(self):
        """Test invalid scale is rejected."""
        validator = OnboardingValidator()

        result = validator.validate_scale("huge")
        assert result.valid is False

    def test_validate_all_valid_input(self):
        """Test validate_all with valid input."""
        validator = OnboardingValidator()

        valid, errors, normalized = validator.validate_all(
            app_name="Quan Com Ngon",
            domain="restaurant",
            features=["menu", "orders"],
            scale="small"
        )

        assert valid is True
        assert len(errors) == 0
        assert normalized["app_name"] == "QuanComNgon"
        assert normalized["domain"] == "restaurant"
        assert "menu" in normalized["features"]
        assert normalized["scale"] == "small"

    def test_validate_all_invalid_input(self):
        """Test validate_all with invalid input."""
        validator = OnboardingValidator()

        valid, errors, normalized = validator.validate_all(
            app_name="",
            domain="factory",
            features=["menu"],
            scale="huge"
        )

        assert valid is False
        assert len(errors) > 0

    def test_remove_diacritics(self):
        """Test Vietnamese diacritics removal."""
        validator = OnboardingValidator()

        # Test various Vietnamese characters
        assert "a" in validator._remove_diacritics("a")
        assert validator._remove_diacritics("Ngon") == "Ngon"


class TestOnboardingService:
    """Tests for OnboardingService."""

    def test_create_session(self):
        """Test session creation."""
        service = OnboardingService()
        session = service.create_session()

        assert session.session_id is not None
        assert session.current_step == OnboardingStep.WELCOME
        assert len(session.completed_steps) == 0

    def test_set_domain(self):
        """Test setting domain."""
        service = OnboardingService()
        session = service.create_session()

        result = service.set_domain(session, "restaurant")

        assert result["success"] is True
        assert session.domain == "restaurant"
        assert OnboardingStep.DOMAIN in session.completed_steps
        assert len(result["available_features"]) > 0

    def test_set_app_name(self):
        """Test setting app name."""
        service = OnboardingService()
        session = service.create_session()

        result = service.set_app_name(session, "Quan Com Ba Hai")

        assert result["success"] is True
        assert session.app_name == "QuanComBaHai"
        assert session.app_name_display == "Quan Com Ba Hai"
        assert OnboardingStep.APP_NAME in session.completed_steps

    def test_set_features(self):
        """Test setting features."""
        service = OnboardingService()
        session = service.create_session()
        service.set_domain(session, "restaurant")

        result = service.set_features(session, ["menu", "orders", "tables"])

        assert result["success"] is True
        assert "menu" in session.features
        assert result["feature_count"] == 3

    def test_set_features_requires_domain(self):
        """Test features require domain to be set first."""
        service = OnboardingService()
        session = service.create_session()

        result = service.set_features(session, ["menu", "orders"])

        assert result["success"] is False
        assert "loai hinh" in result["error"].lower()

    def test_set_scale(self):
        """Test setting scale."""
        service = OnboardingService()
        session = service.create_session()

        result = service.set_scale(session, "small")

        assert result["success"] is True
        assert session.scale == "small"
        assert result["cgf_tier"] == "STANDARD"

    def test_generate_blueprint_restaurant(self):
        """Test blueprint generation for restaurant."""
        service = OnboardingService()
        session = service.create_session()

        # Complete all steps
        service.set_domain(session, "restaurant")
        service.set_app_name(session, "Quan Pho Ngon")
        service.set_features(session, ["menu", "orders", "tables"])
        service.set_scale(session, "small")

        result = service.generate_blueprint(session)

        assert result["success"] is True
        assert "blueprint" in result

        blueprint = result["blueprint"]
        assert blueprint["name"] == "QuanPhoNgon"
        assert len(blueprint.get("modules", [])) > 0
        assert "_onboarding" in blueprint
        assert blueprint["_onboarding"]["domain"] == "restaurant"

    def test_generate_blueprint_hotel(self):
        """Test blueprint generation for hotel."""
        service = OnboardingService()
        session = service.create_session()

        service.set_domain(session, "hotel")
        service.set_app_name(session, "Khach San Hai Au")
        service.set_features(session, ["rooms", "bookings", "guests"])
        service.set_scale(session, "medium")

        result = service.generate_blueprint(session)

        assert result["success"] is True
        blueprint = result["blueprint"]
        assert blueprint["name"] == "KhachSanHaiAu"
        assert blueprint["_onboarding"]["cgf_tier"] == "PROFESSIONAL"

    def test_generate_blueprint_retail(self):
        """Test blueprint generation for retail."""
        service = OnboardingService()
        session = service.create_session()

        service.set_domain(session, "retail")
        service.set_app_name(session, "Cua Hang 365")
        service.set_features(session, ["products", "inventory", "sales"])
        service.set_scale(session, "micro")

        result = service.generate_blueprint(session)

        assert result["success"] is True
        blueprint = result["blueprint"]
        assert blueprint["name"] == "CuaHang365"
        assert blueprint["_onboarding"]["cgf_tier"] == "LITE"

    def test_generate_blueprint_incomplete_session(self):
        """Test blueprint generation fails with incomplete data."""
        service = OnboardingService()
        session = service.create_session()

        # Only set domain, missing other fields
        service.set_domain(session, "restaurant")

        result = service.generate_blueprint(session)

        assert result["success"] is False
        assert len(result["errors"]) > 0

    def test_get_domain_options(self):
        """Test getting domain options."""
        service = OnboardingService()
        options = service.get_domain_options()

        assert len(options) == 6

        keys = [o["key"] for o in options]
        assert "restaurant" in keys
        assert "hotel" in keys
        assert "retail" in keys
        assert "ecommerce" in keys
        assert "hrm" in keys
        assert "crm" in keys

        # Check Vietnamese names
        for opt in options:
            assert opt["name"] != ""
            assert opt["icon"] != ""

    def test_get_feature_options(self):
        """Test getting feature options per domain."""
        service = OnboardingService()

        restaurant_features = service.get_feature_options("restaurant")
        assert len(restaurant_features) > 0
        assert any(f["key"] == "menu" for f in restaurant_features)

        hotel_features = service.get_feature_options("hotel")
        assert any(f["key"] == "rooms" for f in hotel_features)

        retail_features = service.get_feature_options("retail")
        assert any(f["key"] == "products" for f in retail_features)

    def test_get_scale_options(self):
        """Test getting scale options."""
        service = OnboardingService()
        options = service.get_scale_options()

        assert len(options) == 4

        keys = [o["key"] for o in options]
        assert "micro" in keys
        assert "small" in keys
        assert "medium" in keys
        assert "large" in keys

        # Check CGF tier mapping
        for opt in options:
            assert "cgf_tier" in opt

    def test_session_persistence(self):
        """Test session can be retrieved."""
        service = OnboardingService()
        session = service.create_session()
        session_id = session.session_id

        # Modify session
        service.set_domain(session, "retail")

        # Retrieve session
        retrieved = service.get_session(session_id)

        assert retrieved is not None
        assert retrieved.domain == "retail"

    def test_session_to_dict(self):
        """Test session serialization."""
        service = OnboardingService()
        session = service.create_session()
        service.set_domain(session, "restaurant")
        service.set_app_name(session, "Test App")

        data = session.to_dict()

        assert "session_id" in data
        assert "current_step" in data
        assert "domain" in data
        assert data["domain"] == "restaurant"
        assert data["app_name"] == "TestApp"


class TestOnboardingPrompts:
    """Tests for Vietnamese prompts."""

    def test_vietnamese_prompts_exist(self):
        """Test Vietnamese prompts are defined."""
        assert VIETNAMESE_PROMPTS is not None
        assert VIETNAMESE_PROMPTS.welcome_title != ""
        assert VIETNAMESE_PROMPTS.step1_title != ""

    def test_all_domains_have_prompts(self):
        """Test all domains have Vietnamese prompts."""
        for domain in ["restaurant", "hotel", "retail"]:
            assert domain in VIETNAMESE_PROMPTS.domains
            domain_info = VIETNAMESE_PROMPTS.domains[domain]
            assert domain_info.name_vi != ""
            assert domain_info.description_vi != ""
            assert domain_info.icon != ""

    def test_all_domains_have_features(self):
        """Test all domains have feature labels."""
        for domain in ["restaurant", "hotel", "retail"]:
            assert domain in FEATURE_LABELS_VI
            features = FEATURE_LABELS_VI[domain]
            assert len(features) > 0

            for key, info in features.items():
                assert "name" in info
                assert "description" in info

    def test_scale_options_complete(self):
        """Test all scale options have labels."""
        for scale in ["micro", "small", "medium", "large"]:
            assert scale in VIETNAMESE_PROMPTS.step4_options
            assert VIETNAMESE_PROMPTS.step4_options[scale] != ""
            assert scale in SCALE_TO_CGF_TIER


class TestOnboardingIntegration:
    """Integration tests for onboarding flow."""

    def test_full_onboarding_flow_restaurant(self):
        """Test complete onboarding flow for restaurant."""
        service = OnboardingService()

        # Step 1: Create session
        session = service.create_session()
        assert session.current_step == OnboardingStep.WELCOME

        # Step 2: Select domain
        result = service.set_domain(session, "restaurant")
        assert result["success"] is True
        assert session.current_step == OnboardingStep.APP_NAME

        # Step 3: Set app name
        result = service.set_app_name(session, "Pho 24 Quan")
        assert result["success"] is True
        assert session.current_step == OnboardingStep.FEATURES

        # Step 4: Select features
        result = service.set_features(
            session, ["menu", "orders", "tables", "reservations"]
        )
        assert result["success"] is True
        assert session.current_step == OnboardingStep.SCALE

        # Step 5: Set scale
        result = service.set_scale(session, "small")
        assert result["success"] is True
        assert session.current_step == OnboardingStep.CONFIRM

        # Step 6: Generate blueprint
        result = service.generate_blueprint(session)
        assert result["success"] is True
        assert session.current_step == OnboardingStep.COMPLETE

        # Verify blueprint
        blueprint = result["blueprint"]
        assert blueprint["name"] == "Pho24Quan"
        # Language/framework may not be present in domain blueprint
        # (set by IRValidator normalization)

        # Verify modules
        module_names = [m["name"] for m in blueprint["modules"]]
        assert "menu" in module_names
        assert "orders" in module_names

        # Verify metadata
        assert blueprint["_onboarding"]["domain"] == "restaurant"
        assert blueprint["_onboarding"]["scale"] == "small"
        assert blueprint["_onboarding"]["cgf_tier"] == "STANDARD"

    def test_full_onboarding_flow_hotel(self):
        """Test complete onboarding flow for hotel."""
        service = OnboardingService()
        session = service.create_session()

        service.set_domain(session, "hotel")
        service.set_app_name(session, "Dalat Homestay")
        service.set_features(session, ["rooms", "bookings", "billing"])
        service.set_scale(session, "medium")

        result = service.generate_blueprint(session)

        assert result["success"] is True
        blueprint = result["blueprint"]

        # Verify hotel-specific modules
        module_names = [m["name"] for m in blueprint["modules"]]
        assert "rooms" in module_names
        assert "bookings" in module_names

        # Verify CGF metadata
        assert "_cgf" in blueprint
        # Hotel uses MP-002 (O2C), MP-011 (S2S), MP-015 (R2F)
        assert "MP-002" in blueprint["_cgf"]["master_processes"]

    def test_blueprint_validates_with_ir_validator(self):
        """Test generated blueprint passes IR validation."""
        from app.services.codegen.ir import IRValidator

        service = OnboardingService()
        session = service.create_session()

        service.set_domain(session, "retail")
        service.set_app_name(session, "Mini Mart 365")
        service.set_features(session, ["products", "inventory", "sales", "customers"])
        service.set_scale(session, "small")

        result = service.generate_blueprint(session)
        assert result["success"] is True

        # Clean metadata fields for validation
        blueprint = result["blueprint"]
        clean_blueprint = _clean_meta_fields(blueprint)

        # Validate with IR validator
        validator = IRValidator()
        validation_result = validator.validate_app_blueprint(clean_blueprint)

        assert validation_result.valid is True, \
            f"Validation errors: {validation_result.errors}"


def _clean_meta_fields(obj):
    """Remove _meta and onboarding fields for IR validation."""
    if isinstance(obj, dict):
        return {
            k: _clean_meta_fields(v)
            for k, v in obj.items()
            if not k.startswith("_")
        }
    elif isinstance(obj, list):
        return [_clean_meta_fields(item) for item in obj]
    return obj


# ---------------------------------------------------------------------------
# Sprint 196 Track D-02: Onboarding Test Expansion — New Domains
# ---------------------------------------------------------------------------

class TestOnboardingValidatorNewDomains:
    """Validator tests for ecommerce, hrm, crm domains."""

    def test_validate_domain_ecommerce(self):
        """Test ecommerce domain validation."""
        validator = OnboardingValidator()

        result = validator.validate_domain("ecommerce")
        assert result.valid is True
        assert result.normalized_value == "ecommerce"

    def test_validate_domain_hrm(self):
        """Test hrm domain validation."""
        validator = OnboardingValidator()

        result = validator.validate_domain("HRM")  # case insensitive
        assert result.valid is True
        assert result.normalized_value == "hrm"

    def test_validate_domain_crm(self):
        """Test crm domain validation."""
        validator = OnboardingValidator()

        result = validator.validate_domain("Crm")
        assert result.valid is True
        assert result.normalized_value == "crm"

    def test_validate_ecommerce_features(self):
        """Test ecommerce features validation."""
        validator = OnboardingValidator()

        result = validator.validate_features(
            "ecommerce", ["products", "orders"]
        )
        assert result.valid is True

    def test_validate_hrm_features(self):
        """Test hrm features validation."""
        validator = OnboardingValidator()

        result = validator.validate_features(
            "hrm", ["employees", "payroll"]
        )
        assert result.valid is True

    def test_validate_crm_features(self):
        """Test crm features validation."""
        validator = OnboardingValidator()

        result = validator.validate_features(
            "crm", ["leads", "contacts"]
        )
        assert result.valid is True

    def test_validate_ecommerce_invalid_feature(self):
        """Test invalid feature for ecommerce is rejected."""
        validator = OnboardingValidator()

        result = validator.validate_features(
            "ecommerce", ["products", "rooms"]  # 'rooms' is hotel feature
        )
        assert result.valid is False

    def test_validate_all_ecommerce(self):
        """Test validate_all for ecommerce domain."""
        validator = OnboardingValidator()

        valid, errors, normalized = validator.validate_all(
            app_name="Shop My Pham Online",
            domain="ecommerce",
            features=["products", "orders"],
            scale="small",
        )
        assert valid is True
        assert len(errors) == 0
        assert normalized["app_name"] == "ShopMyPhamOnline"
        assert normalized["domain"] == "ecommerce"


class TestOnboardingServiceNewDomains:
    """Service tests for ecommerce, hrm, crm domains."""

    def test_set_domain_ecommerce(self):
        """Test setting ecommerce domain."""
        service = OnboardingService()
        session = service.create_session()

        result = service.set_domain(session, "ecommerce")
        assert result["success"] is True
        assert session.domain == "ecommerce"
        assert len(result["available_features"]) > 0

    def test_set_domain_hrm(self):
        """Test setting hrm domain."""
        service = OnboardingService()
        session = service.create_session()

        result = service.set_domain(session, "hrm")
        assert result["success"] is True
        assert session.domain == "hrm"

    def test_set_domain_crm(self):
        """Test setting crm domain."""
        service = OnboardingService()
        session = service.create_session()

        result = service.set_domain(session, "crm")
        assert result["success"] is True
        assert session.domain == "crm"

    def test_get_feature_options_ecommerce(self):
        """Test feature options for ecommerce."""
        service = OnboardingService()
        features = service.get_feature_options("ecommerce")

        assert len(features) > 0
        keys = [f["key"] for f in features]
        assert "products" in keys
        assert "orders" in keys

    def test_get_feature_options_hrm(self):
        """Test feature options for hrm."""
        service = OnboardingService()
        features = service.get_feature_options("hrm")

        assert len(features) > 0
        keys = [f["key"] for f in features]
        assert "employees" in keys
        assert "payroll" in keys

    def test_get_feature_options_crm(self):
        """Test feature options for crm."""
        service = OnboardingService()
        features = service.get_feature_options("crm")

        assert len(features) > 0
        keys = [f["key"] for f in features]
        assert "leads" in keys
        assert "contacts" in keys

    def test_generate_blueprint_ecommerce(self):
        """Test blueprint generation for ecommerce."""
        service = OnboardingService()
        session = service.create_session()

        service.set_domain(session, "ecommerce")
        service.set_app_name(session, "Shop My Pham")
        service.set_features(session, ["products", "orders"])
        service.set_scale(session, "small")

        result = service.generate_blueprint(session)

        assert result["success"] is True
        blueprint = result["blueprint"]
        assert blueprint["name"] == "ShopMyPham"
        assert blueprint["_onboarding"]["domain"] == "ecommerce"

    def test_generate_blueprint_hrm(self):
        """Test blueprint generation for hrm."""
        service = OnboardingService()
        session = service.create_session()

        service.set_domain(session, "hrm")
        service.set_app_name(session, "Nhan Su ABC")
        service.set_features(session, ["employees", "payroll"])
        service.set_scale(session, "medium")

        result = service.generate_blueprint(session)

        assert result["success"] is True
        blueprint = result["blueprint"]
        assert blueprint["name"] == "NhanSuAbc"
        assert blueprint["_onboarding"]["domain"] == "hrm"

    def test_generate_blueprint_crm(self):
        """Test blueprint generation for crm."""
        service = OnboardingService()
        session = service.create_session()

        service.set_domain(session, "crm")
        service.set_app_name(session, "Sales Pro Viet")
        service.set_features(session, ["leads", "contacts"])
        service.set_scale(session, "small")

        result = service.generate_blueprint(session)

        assert result["success"] is True
        blueprint = result["blueprint"]
        assert blueprint["name"] == "SalesProViet"
        assert blueprint["_onboarding"]["domain"] == "crm"


class TestOnboardingPromptsNewDomains:
    """Prompt tests for ecommerce, hrm, crm domains."""

    def test_new_domains_have_prompts(self):
        """Test new domains have Vietnamese prompts."""
        for domain in ["ecommerce", "hrm", "crm"]:
            assert domain in VIETNAMESE_PROMPTS.domains, (
                f"Domain '{domain}' missing from VIETNAMESE_PROMPTS"
            )
            domain_info = VIETNAMESE_PROMPTS.domains[domain]
            assert domain_info.name_vi != ""
            assert domain_info.description_vi != ""
            assert domain_info.icon != ""

    def test_new_domains_have_features(self):
        """Test new domains have feature labels in Vietnamese."""
        for domain in ["ecommerce", "hrm", "crm"]:
            assert domain in FEATURE_LABELS_VI, (
                f"Domain '{domain}' missing from FEATURE_LABELS_VI"
            )
            features = FEATURE_LABELS_VI[domain]
            assert len(features) >= 2, (
                f"Domain '{domain}' needs at least 2 features"
            )
            for key, info in features.items():
                assert "name" in info, f"Feature '{key}' in '{domain}' missing 'name'"
                assert "description" in info, f"Feature '{key}' in '{domain}' missing 'description'"


class TestOnboardingIntegrationNewDomains:
    """Full flow integration tests for new domains."""

    def test_full_onboarding_flow_ecommerce(self):
        """Test complete onboarding flow for ecommerce."""
        service = OnboardingService()
        session = service.create_session()

        service.set_domain(session, "ecommerce")
        assert session.current_step == OnboardingStep.APP_NAME

        service.set_app_name(session, "Trai Cay Sach Ha Noi")
        assert session.current_step == OnboardingStep.FEATURES

        service.set_features(session, ["products", "orders", "customers"])
        assert session.current_step == OnboardingStep.SCALE

        service.set_scale(session, "small")
        assert session.current_step == OnboardingStep.CONFIRM

        result = service.generate_blueprint(session)
        assert result["success"] is True
        assert session.current_step == OnboardingStep.COMPLETE

        blueprint = result["blueprint"]
        assert blueprint["name"] == "TraiCaySachHaNoi"
        module_names = [m["name"] for m in blueprint["modules"]]
        assert "products" in module_names
        assert "orders" in module_names

    def test_full_onboarding_flow_hrm(self):
        """Test complete onboarding flow for hrm."""
        service = OnboardingService()
        session = service.create_session()

        service.set_domain(session, "hrm")
        service.set_app_name(session, "Nhan Su Nha May XYZ")
        service.set_features(session, ["employees", "attendance", "payroll", "leave"])
        service.set_scale(session, "medium")

        result = service.generate_blueprint(session)
        assert result["success"] is True

        blueprint = result["blueprint"]
        assert blueprint["name"] == "NhanSuNhaMayXyz"
        module_names = [m["name"] for m in blueprint["modules"]]
        assert "employees" in module_names
        assert "payroll" in module_names

    def test_full_onboarding_flow_crm(self):
        """Test complete onboarding flow for crm."""
        service = OnboardingService()
        session = service.create_session()

        service.set_domain(session, "crm")
        service.set_app_name(session, "Zalo CRM Manager")
        service.set_features(session, ["leads", "contacts", "deals", "activities"])
        service.set_scale(session, "small")

        result = service.generate_blueprint(session)
        assert result["success"] is True

        blueprint = result["blueprint"]
        assert blueprint["name"] == "ZaloCrmManager"
        module_names = [m["name"] for m in blueprint["modules"]]
        assert "leads" in module_names
        assert "deals" in module_names

    def test_ecommerce_blueprint_validates_with_ir(self):
        """Test ecommerce blueprint passes IR validation."""
        from app.services.codegen.ir import IRValidator

        service = OnboardingService()
        session = service.create_session()

        service.set_domain(session, "ecommerce")
        service.set_app_name(session, "Test Shop")
        service.set_features(session, ["products", "orders"])
        service.set_scale(session, "small")

        result = service.generate_blueprint(session)
        assert result["success"] is True

        clean_blueprint = _clean_meta_fields(result["blueprint"])
        validator = IRValidator()
        validation = validator.validate_app_blueprint(clean_blueprint)
        assert validation.valid is True, f"IR errors: {validation.errors}"

    def test_hrm_blueprint_validates_with_ir(self):
        """Test HRM blueprint passes IR validation."""
        from app.services.codegen.ir import IRValidator

        service = OnboardingService()
        session = service.create_session()

        service.set_domain(session, "hrm")
        service.set_app_name(session, "Test HR")
        service.set_features(session, ["employees", "payroll"])
        service.set_scale(session, "medium")

        result = service.generate_blueprint(session)
        assert result["success"] is True

        clean_blueprint = _clean_meta_fields(result["blueprint"])
        validator = IRValidator()
        validation = validator.validate_app_blueprint(clean_blueprint)
        assert validation.valid is True, f"IR errors: {validation.errors}"

    def test_crm_blueprint_validates_with_ir(self):
        """Test CRM blueprint passes IR validation."""
        from app.services.codegen.ir import IRValidator

        service = OnboardingService()
        session = service.create_session()

        service.set_domain(session, "crm")
        service.set_app_name(session, "Test CRM")
        service.set_features(session, ["leads", "contacts"])
        service.set_scale(session, "small")

        result = service.generate_blueprint(session)
        assert result["success"] is True

        clean_blueprint = _clean_meta_fields(result["blueprint"])
        validator = IRValidator()
        validation = validator.validate_app_blueprint(clean_blueprint)
        assert validation.valid is True, f"IR errors: {validation.errors}"
