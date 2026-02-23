"""
Unit tests for Vietnamese Domain Templates.

Sprint 47: Vietnamese SME Domain Templates
ADR-023: IR-Based Deterministic Code Generation

Tests domain template functionality:
- Template registration and discovery
- Entity/field structure validation
- AppBlueprint generation
- CGF metadata integration

Author: Backend Lead
Date: December 23, 2025
Version: 1.0.0
Status: ACTIVE - Sprint 47 Implementation
"""

import pytest
from typing import Dict, Any


class TestDomainRegistry:
    """Test domain template registry."""

    def test_registry_has_all_domains(self):
        """Test all expected domains are registered."""
        from app.services.codegen.domains import DomainRegistry

        domains = DomainRegistry.list_domains()
        domain_names = [d["domain"] for d in domains]

        assert "restaurant" in domain_names
        assert "hotel" in domain_names
        assert "retail" in domain_names

    def test_get_domain_by_name(self):
        """Test getting domain by name."""
        from app.services.codegen.domains import DomainRegistry

        restaurant = DomainRegistry.get("restaurant")
        assert restaurant is not None
        assert restaurant.domain_name == "restaurant"
        assert "Nhà hàng" in restaurant.vietnamese_name

    def test_list_domains_has_vietnamese_names(self):
        """Test domains have Vietnamese names."""
        from app.services.codegen.domains import DomainRegistry

        domains = DomainRegistry.list_domains()

        for domain in domains:
            assert "vietnamese_name" in domain
            assert domain["vietnamese_name"]  # Not empty
            assert "description" in domain
            assert domain["description"]  # Not empty


class TestFnBDomainTemplate:
    """Test F&B (Restaurant) domain template."""

    def test_fnb_has_correct_modules(self):
        """Test F&B domain has required modules."""
        from app.services.codegen.domains import FnBDomainTemplate

        template = FnBDomainTemplate()
        modules = template.get_modules()
        module_names = [m.name for m in modules]

        assert "menu" in module_names
        assert "orders" in module_names
        assert "tables" in module_names
        assert "reservations" in module_names

    def test_fnb_menu_module_entities(self):
        """Test menu module has correct entities."""
        from app.services.codegen.domains import FnBDomainTemplate

        template = FnBDomainTemplate()
        modules = template.get_modules()
        menu_module = next(m for m in modules if m.name == "menu")

        entity_names = [e.name for e in menu_module.entities]
        assert "Category" in entity_names
        assert "MenuItem" in entity_names

    def test_fnb_order_entity_fields(self):
        """Test Order entity has required fields."""
        from app.services.codegen.domains import FnBDomainTemplate

        template = FnBDomainTemplate()
        order = template.get_entity_by_name("Order")

        assert order is not None
        field_names = [f.name for f in order.fields]

        # Required fields for O2C process
        assert "order_number" in field_names
        assert "status" in field_names
        assert "total" in field_names
        assert "payment_status" in field_names
        assert "payment_method" in field_names

    def test_fnb_menuitem_has_vietnamese_fields(self):
        """Test MenuItem has Vietnamese field descriptions."""
        from app.services.codegen.domains import FnBDomainTemplate

        template = FnBDomainTemplate()
        menu_item = template.get_entity_by_name("MenuItem")

        assert menu_item is not None
        assert "Món ăn" in menu_item.vietnamese_name

        # Check price field has Vietnamese name
        price_field = next(f for f in menu_item.fields if f.name == "price")
        assert "Giá bán" in price_field.vietnamese_name

    def test_fnb_to_app_blueprint(self):
        """Test F&B can generate AppBlueprint."""
        from app.services.codegen.domains import FnBDomainTemplate

        template = FnBDomainTemplate()
        blueprint = template.to_app_blueprint("Quán Cà Phê ABC")

        assert blueprint["name"] == "Quán Cà Phê ABC"
        assert blueprint["business_domain"] == "restaurant"
        assert len(blueprint["modules"]) == 4

    def test_fnb_blueprint_module_has_entities(self):
        """Test generated blueprint modules have entities."""
        from app.services.codegen.domains import FnBDomainTemplate

        template = FnBDomainTemplate()
        blueprint = template.to_app_blueprint("Test Restaurant")

        for module in blueprint["modules"]:
            assert "entities" in module
            assert len(module["entities"]) > 0

            for entity in module["entities"]:
                assert "name" in entity
                assert "fields" in entity
                assert len(entity["fields"]) > 0


class TestHospitalityDomainTemplate:
    """Test Hospitality (Hotel) domain template."""

    def test_hotel_has_correct_modules(self):
        """Test hotel domain has required modules."""
        from app.services.codegen.domains import HospitalityDomainTemplate

        template = HospitalityDomainTemplate()
        modules = template.get_modules()
        module_names = [m.name for m in modules]

        assert "rooms" in module_names
        assert "bookings" in module_names
        assert "guests" in module_names
        assert "billing" in module_names

    def test_hotel_room_module_entities(self):
        """Test room module has correct entities."""
        from app.services.codegen.domains import HospitalityDomainTemplate

        template = HospitalityDomainTemplate()
        modules = template.get_modules()
        room_module = next(m for m in modules if m.name == "rooms")

        entity_names = [e.name for e in room_module.entities]
        assert "Room" in entity_names
        assert "RoomType" in entity_names

    def test_hotel_booking_entity_fields(self):
        """Test Booking entity has required fields."""
        from app.services.codegen.domains import HospitalityDomainTemplate

        template = HospitalityDomainTemplate()
        booking = template.get_entity_by_name("Booking")

        assert booking is not None
        field_names = [f.name for f in booking.fields]

        # Required fields for G2D process
        assert "booking_code" in field_names
        assert "guest_id" in field_names
        assert "room_id" in field_names
        assert "check_in_date" in field_names
        assert "check_out_date" in field_names
        assert "status" in field_names

    def test_hotel_guest_entity_fields(self):
        """Test Guest entity has ID verification fields."""
        from app.services.codegen.domains import HospitalityDomainTemplate

        template = HospitalityDomainTemplate()
        guest = template.get_entity_by_name("Guest")

        assert guest is not None
        field_names = [f.name for f in guest.fields]

        # Vietnamese ID verification
        assert "id_type" in field_names
        assert "id_number" in field_names
        assert "nationality" in field_names


class TestRetailDomainTemplate:
    """Test Retail domain template."""

    def test_retail_has_correct_modules(self):
        """Test retail domain has required modules."""
        from app.services.codegen.domains import RetailDomainTemplate

        template = RetailDomainTemplate()
        modules = template.get_modules()
        module_names = [m.name for m in modules]

        assert "products" in module_names
        assert "inventory" in module_names
        assert "sales" in module_names
        assert "customers" in module_names

    def test_retail_product_entity_fields(self):
        """Test Product entity has required fields (MDG-003 compliant)."""
        from app.services.codegen.domains import RetailDomainTemplate

        template = RetailDomainTemplate()
        product = template.get_entity_by_name("Product")

        assert product is not None
        field_names = [f.name for f in product.fields]

        # MDG-003 Product & Pricing Governance
        assert "sku" in field_names
        assert "barcode" in field_names
        assert "name" in field_names
        assert "cost_price" in field_names
        assert "selling_price" in field_names
        assert "vat_rate" in field_names

    def test_retail_inventory_entity_fields(self):
        """Test Inventory entity has required fields."""
        from app.services.codegen.domains import RetailDomainTemplate

        template = RetailDomainTemplate()
        inventory = template.get_entity_by_name("Inventory")

        assert inventory is not None
        field_names = [f.name for f in inventory.fields]

        # Inventory management
        assert "product_id" in field_names
        assert "warehouse_id" in field_names
        assert "quantity" in field_names
        assert "reserved_quantity" in field_names
        assert "min_stock" in field_names

    def test_retail_sale_entity_fields(self):
        """Test Sale entity has required fields (MP-002 O2C compliant)."""
        from app.services.codegen.domains import RetailDomainTemplate

        template = RetailDomainTemplate()
        sale = template.get_entity_by_name("Sale")

        assert sale is not None
        field_names = [f.name for f in sale.fields]

        # MP-002 Order-to-Cash
        assert "order_number" in field_names
        assert "customer_id" in field_names
        assert "status" in field_names
        assert "payment_status" in field_names
        assert "invoice_number" in field_names  # VAT invoice

    def test_retail_customer_entity_fields(self):
        """Test Customer entity has required fields (MDP-005 compliant)."""
        from app.services.codegen.domains import RetailDomainTemplate

        template = RetailDomainTemplate()
        customer = template.get_entity_by_name("Customer")

        assert customer is not None
        field_names = [f.name for f in customer.fields]

        # MDP-005 Customer Master
        assert "customer_code" in field_names
        assert "customer_type" in field_names
        assert "full_name" in field_names
        assert "phone" in field_names
        assert "tax_code" in field_names  # For VAT invoice


class TestCGFMetadata:
    """Test CGF metadata integration."""

    def test_domain_has_master_processes(self):
        """Test domain mappings have master processes."""
        from app.services.codegen.domains.cgf_metadata import (
            get_domain_cgf_mapping,
            get_domain_master_processes,
        )

        mapping = get_domain_cgf_mapping("retail")
        assert mapping is not None
        assert "MP-002" in mapping.master_processes  # O2C

        processes = get_domain_master_processes("retail")
        assert len(processes) > 0
        process_ids = [p.id for p in processes]
        assert "MP-002" in process_ids

    def test_entity_dag_levels(self):
        """Test entity DAG approval levels."""
        from app.services.codegen.domains.cgf_metadata import (
            get_entity_dag_level,
            DAGLevel,
        )

        # Staff can create sales
        sale_level = get_entity_dag_level("retail", "Sale")
        assert sale_level == DAGLevel.LEVEL_1

        # Director approves warehouses
        warehouse_level = get_entity_dag_level("retail", "Warehouse")
        assert warehouse_level == DAGLevel.LEVEL_4

    def test_entity_code_structure(self):
        """Test entity code structures (Simplified Code V2.0)."""
        from app.services.codegen.domains.cgf_metadata import (
            get_entity_code_structure,
        )

        # Product: PRD-XXXX
        product_code = get_entity_code_structure("retail", "Product")
        assert product_code == "PRD-XXXX"

        # Customer: CUS-XXXX
        customer_code = get_entity_code_structure("retail", "Customer")
        assert customer_code == "CUS-XXXX"

    def test_vietnamese_ci_constants(self):
        """Test Vietnamese Cultural Intelligence constants."""
        from app.services.codegen.domains.cgf_metadata import VIETNAMESE_CI

        # BHXH rates
        assert VIETNAMESE_CI["bhxh"]["employer_rate"] == "17.5%"
        assert VIETNAMESE_CI["bhxh"]["employee_rate"] == "8%"

        # VAT rates
        assert VIETNAMESE_CI["vat"]["standard_rate"] == "10%"

        # Currency
        assert VIETNAMESE_CI["currency"]["code"] == "VND"
        assert VIETNAMESE_CI["currency"]["decimals"] == 0

    def test_master_process_registry(self):
        """Test Master Process registry."""
        from app.services.codegen.domains.cgf_metadata import (
            MASTER_PROCESSES,
            ProcessTier,
        )

        # MP-002 Order-to-Cash
        o2c = MASTER_PROCESSES.get("MP-002")
        assert o2c is not None
        assert o2c.name == "Order-to-Cash (O2C)"
        assert o2c.tier == ProcessTier.TIER_1_CORE
        assert o2c.kernel == "O2C"

        # MP-011 Guest-to-Departure (Industry-specific)
        g2d = MASTER_PROCESSES.get("MP-011")
        assert g2d is not None
        assert g2d.tier == ProcessTier.TIER_3_INDUSTRY
        assert "hotel" in g2d.industries


class TestDomainFieldConversion:
    """Test domain field to IR conversion."""

    def test_field_to_ir_dict(self):
        """Test field conversion to IR dictionary."""
        from app.services.codegen.domains.base import DomainField, FieldType

        field = DomainField(
            name="price",
            field_type=FieldType.FLOAT,
            vietnamese_name="Giá bán",
            description="Giá bán sản phẩm (VND)",
            required=True,
            min_value=0,
        )

        ir_dict = field.to_ir_dict()

        assert ir_dict["name"] == "price"
        assert ir_dict["type"] == "float"
        assert ir_dict["required"] is True
        assert ir_dict["min_value"] == 0
        assert ir_dict["_meta"]["vietnamese_name"] == "Giá bán"

    def test_entity_to_ir_dict(self):
        """Test entity conversion to IR dictionary."""
        from app.services.codegen.domains.base import (
            DomainEntity,
            DomainField,
            FieldType,
        )

        entity = DomainEntity(
            name="Product",
            vietnamese_name="Sản phẩm",
            description="Chi tiết sản phẩm",
            fields=[
                DomainField(
                    name="name",
                    field_type=FieldType.STRING,
                    vietnamese_name="Tên sản phẩm",
                    required=True,
                    max_length=200,
                ),
            ],
        )

        ir_dict = entity.to_ir_dict()

        assert ir_dict["name"] == "Product"
        assert len(ir_dict["fields"]) == 1
        assert ir_dict["fields"][0]["name"] == "name"
        assert ir_dict["_meta"]["vietnamese_name"] == "Sản phẩm"


class TestBlueprintValidation:
    """Test generated blueprints can be validated."""

    def test_fnb_blueprint_validates(self):
        """Test F&B blueprint passes IR validation."""
        from app.services.codegen.domains import FnBDomainTemplate
        from app.services.codegen.ir import IRValidator

        template = FnBDomainTemplate()
        blueprint = template.to_app_blueprint("Test Restaurant", "1.0.0")

        # Remove _meta fields for validation
        clean_blueprint = _clean_meta_fields(blueprint)

        validator = IRValidator()
        result = validator.validate_app_blueprint(clean_blueprint)

        assert result.valid is True, f"Validation failed: {result.issues}"

    def test_hotel_blueprint_validates(self):
        """Test Hotel blueprint passes IR validation."""
        from app.services.codegen.domains import HospitalityDomainTemplate
        from app.services.codegen.ir import IRValidator

        template = HospitalityDomainTemplate()
        blueprint = template.to_app_blueprint("Test Hotel", "1.0.0")

        clean_blueprint = _clean_meta_fields(blueprint)

        validator = IRValidator()
        result = validator.validate_app_blueprint(clean_blueprint)

        assert result.valid is True, f"Validation failed: {result.issues}"

    def test_retail_blueprint_validates(self):
        """Test Retail blueprint passes IR validation."""
        from app.services.codegen.domains import RetailDomainTemplate
        from app.services.codegen.ir import IRValidator

        template = RetailDomainTemplate()
        blueprint = template.to_app_blueprint("Test Store", "1.0.0")

        clean_blueprint = _clean_meta_fields(blueprint)

        validator = IRValidator()
        result = validator.validate_app_blueprint(clean_blueprint)

        assert result.valid is True, f"Validation failed: {result.issues}"


def _clean_meta_fields(obj: Dict[str, Any]) -> Dict[str, Any]:
    """Remove _meta fields recursively for IR validation."""
    if isinstance(obj, dict):
        return {
            k: _clean_meta_fields(v)
            for k, v in obj.items()
            if k != "_meta"
        }
    elif isinstance(obj, list):
        return [_clean_meta_fields(item) for item in obj]
    return obj


class TestBundleBuilderIntegration:
    """Test domain templates with BundleBuilder scaffold generation."""

    def test_fnb_scaffold_generation(self):
        """Test F&B domain generates compilable Python scaffold."""
        from pathlib import Path
        from app.services.codegen.domains import FnBDomainTemplate
        from app.services.codegen.ir import BundleBuilder, IRValidator

        template = FnBDomainTemplate()
        blueprint = template.to_app_blueprint("Test Restaurant", "1.0.0")
        clean_blueprint = _clean_meta_fields(blueprint)

        # Validate and normalize
        validator = IRValidator()
        result = validator.validate_app_blueprint(clean_blueprint)
        assert result.valid is True

        # Build scaffold
        template_dir = Path(__file__).parent.parent.parent.parent.parent / \
            "app" / "services" / "codegen" / "templates"
        builder = BundleBuilder(template_dir=template_dir)
        bundle = builder.build(result.normalized_ir)

        assert bundle.success is True
        assert bundle.file_count > 0

        # Verify Python files compile
        python_files = bundle.get_files_by_language("python")
        assert len(python_files) > 0

        for file in python_files:
            try:
                compile(file.content, file.path, "exec")
            except SyntaxError as e:
                raise AssertionError(f"Syntax error in {file.path}: {e}")

    def test_hotel_scaffold_generation(self):
        """Test Hotel domain generates compilable Python scaffold."""
        from pathlib import Path
        from app.services.codegen.domains import HospitalityDomainTemplate
        from app.services.codegen.ir import BundleBuilder, IRValidator

        template = HospitalityDomainTemplate()
        blueprint = template.to_app_blueprint("Test Hotel", "1.0.0")
        clean_blueprint = _clean_meta_fields(blueprint)

        validator = IRValidator()
        result = validator.validate_app_blueprint(clean_blueprint)
        assert result.valid is True

        template_dir = Path(__file__).parent.parent.parent.parent.parent / \
            "app" / "services" / "codegen" / "templates"
        builder = BundleBuilder(template_dir=template_dir)
        bundle = builder.build(result.normalized_ir)

        assert bundle.success is True
        assert bundle.file_count > 0

        # Verify model files exist for key entities
        file_paths = [f.path for f in bundle.files]
        assert "app/models/room.py" in file_paths
        assert "app/models/booking.py" in file_paths
        assert "app/models/guest.py" in file_paths

    def test_retail_scaffold_generation(self):
        """Test Retail domain generates compilable Python scaffold."""
        from pathlib import Path
        from app.services.codegen.domains import RetailDomainTemplate
        from app.services.codegen.ir import BundleBuilder, IRValidator

        template = RetailDomainTemplate()
        blueprint = template.to_app_blueprint("Test Store", "1.0.0")
        clean_blueprint = _clean_meta_fields(blueprint)

        validator = IRValidator()
        result = validator.validate_app_blueprint(clean_blueprint)
        assert result.valid is True

        template_dir = Path(__file__).parent.parent.parent.parent.parent / \
            "app" / "services" / "codegen" / "templates"
        builder = BundleBuilder(template_dir=template_dir)
        bundle = builder.build(result.normalized_ir)

        assert bundle.success is True
        assert bundle.file_count > 0

        # Verify retail-specific files
        file_paths = [f.path for f in bundle.files]
        assert "app/models/product.py" in file_paths
        assert "app/models/inventory.py" in file_paths
        # Entity names Sale → sal (snake_case processing)
        assert "app/models/sal.py" in file_paths or "app/models/sale.py" in file_paths
        assert "app/models/customer.py" in file_paths

    def test_all_domains_generate_sufficient_files(self):
        """Test all domains generate >20 files each."""
        from pathlib import Path
        from app.services.codegen.domains import (
            DomainRegistry,
            FnBDomainTemplate,
            HospitalityDomainTemplate,
            RetailDomainTemplate,
        )
        from app.services.codegen.ir import BundleBuilder, IRValidator

        template_dir = Path(__file__).parent.parent.parent.parent.parent / \
            "app" / "services" / "codegen" / "templates"

        domains = [
            ("restaurant", FnBDomainTemplate()),
            ("hotel", HospitalityDomainTemplate()),
            ("retail", RetailDomainTemplate()),
        ]

        for domain_name, template in domains:
            blueprint = template.to_app_blueprint(f"Test {domain_name}", "1.0.0")
            clean_blueprint = _clean_meta_fields(blueprint)

            validator = IRValidator()
            result = validator.validate_app_blueprint(clean_blueprint)
            assert result.valid is True, f"{domain_name} validation failed"

            builder = BundleBuilder(template_dir=template_dir)
            bundle = builder.build(result.normalized_ir)

            assert bundle.success is True, f"{domain_name} build failed"
            assert bundle.file_count >= 20, \
                f"{domain_name} only generated {bundle.file_count} files"


# ---------------------------------------------------------------------------
# Sprint 196 Track C-05: Vietnamese Domain Template Validation
# ---------------------------------------------------------------------------
class TestEcommerceDomainTemplate:
    """Test E-commerce domain template (Sprint 196 Track C-01)."""

    def test_ecommerce_has_correct_modules(self):
        """Test e-commerce domain has required modules."""
        from app.services.codegen.domains import EcommerceDomainTemplate

        template = EcommerceDomainTemplate()
        modules = template.get_modules()
        module_names = [m.name for m in modules]

        assert "products" in module_names
        assert "orders" in module_names
        assert "customers" in module_names
        assert "payments" in module_names

    def test_ecommerce_domain_name(self):
        """Test e-commerce domain properties."""
        from app.services.codegen.domains import EcommerceDomainTemplate

        template = EcommerceDomainTemplate()
        assert template.domain_name == "ecommerce"
        assert "điện tử" in template.vietnamese_name

    def test_ecommerce_product_entity_fields(self):
        """Test Product entity has required fields (MDG-003 compliant)."""
        from app.services.codegen.domains import EcommerceDomainTemplate

        template = EcommerceDomainTemplate()
        product = template.get_entity_by_name("Product")

        assert product is not None
        field_names = [f.name for f in product.fields]

        assert "name" in field_names
        assert "sku" in field_names
        assert "price_vnd" in field_names
        assert "stock_quantity" in field_names

    def test_ecommerce_order_entity_fields(self):
        """Test Order entity has required fields (MP-002 O2C)."""
        from app.services.codegen.domains import EcommerceDomainTemplate

        template = EcommerceDomainTemplate()
        order = template.get_entity_by_name("Order")

        assert order is not None
        field_names = [f.name for f in order.fields]

        assert "order_code" in field_names
        assert "status" in field_names
        assert "total_vnd" in field_names
        assert "payment_method" in field_names

    def test_ecommerce_payment_methods_include_cod(self):
        """Test Payment entity supports COD (Vietnamese primary method)."""
        from app.services.codegen.domains import EcommerceDomainTemplate

        template = EcommerceDomainTemplate()
        payment = template.get_entity_by_name("Payment")

        assert payment is not None
        method_field = next(f for f in payment.fields if f.name == "method")
        assert "cod" in method_field.choices

    def test_ecommerce_to_app_blueprint(self):
        """Test e-commerce generates valid AppBlueprint."""
        from app.services.codegen.domains import EcommerceDomainTemplate

        template = EcommerceDomainTemplate()
        blueprint = template.to_app_blueprint("Shop Thoi Trang Online")

        assert blueprint["name"] == "Shop Thoi Trang Online"
        assert blueprint["business_domain"] == "ecommerce"
        assert len(blueprint["modules"]) == 4

    def test_ecommerce_blueprint_validates(self):
        """Test e-commerce blueprint passes IR validation."""
        from app.services.codegen.domains import EcommerceDomainTemplate
        from app.services.codegen.ir import IRValidator

        template = EcommerceDomainTemplate()
        blueprint = template.to_app_blueprint("TestEcommerceShop", "1.0.0")
        clean_blueprint = _clean_meta_fields(blueprint)

        validator = IRValidator()
        result = validator.validate_app_blueprint(clean_blueprint)

        assert result.valid is True, f"Validation failed: {result.issues}"


class TestHrmDomainTemplate:
    """Test HRM domain template (Sprint 196 Track C-02)."""

    def test_hrm_has_correct_modules(self):
        """Test HRM domain has required modules."""
        from app.services.codegen.domains import HrmDomainTemplate

        template = HrmDomainTemplate()
        modules = template.get_modules()
        module_names = [m.name for m in modules]

        assert "employees" in module_names
        assert "attendance" in module_names
        assert "payroll" in module_names
        assert "leave" in module_names

    def test_hrm_domain_name(self):
        """Test HRM domain properties."""
        from app.services.codegen.domains import HrmDomainTemplate

        template = HrmDomainTemplate()
        assert template.domain_name == "hrm"
        assert "nhân sự" in template.vietnamese_name

    def test_hrm_employee_entity_fields(self):
        """Test Employee entity has Vietnamese labor law fields."""
        from app.services.codegen.domains import HrmDomainTemplate

        template = HrmDomainTemplate()
        employee = template.get_entity_by_name("Employee")

        assert employee is not None
        field_names = [f.name for f in employee.fields]

        assert "full_name" in field_names
        assert "employee_code" in field_names
        assert "phone" in field_names
        assert "contract_type" in field_names

    def test_hrm_payroll_entity_has_bhxh_fields(self):
        """Test Payroll entity has BHXH/BHYT/BHTN deduction fields."""
        from app.services.codegen.domains import HrmDomainTemplate

        template = HrmDomainTemplate()
        payroll = template.get_entity_by_name("Payroll")

        assert payroll is not None
        field_names = [f.name for f in payroll.fields]

        assert "base_salary_vnd" in field_names
        assert "bhxh_employee_vnd" in field_names
        assert "bhyt_employee_vnd" in field_names
        assert "bhtn_employee_vnd" in field_names
        assert "net_salary_vnd" in field_names

    def test_hrm_leave_entity_fields(self):
        """Test LeaveRequest entity has leave management fields."""
        from app.services.codegen.domains import HrmDomainTemplate

        template = HrmDomainTemplate()
        leave = template.get_entity_by_name("LeaveRequest")

        assert leave is not None
        field_names = [f.name for f in leave.fields]

        assert "leave_type" in field_names
        assert "start_date" in field_names
        assert "end_date" in field_names
        assert "status" in field_names

    def test_hrm_to_app_blueprint(self):
        """Test HRM generates valid AppBlueprint."""
        from app.services.codegen.domains import HrmDomainTemplate

        template = HrmDomainTemplate()
        blueprint = template.to_app_blueprint("Nhan Su ABC Corp")

        assert blueprint["name"] == "Nhan Su ABC Corp"
        assert blueprint["business_domain"] == "hrm"
        assert len(blueprint["modules"]) == 4

    def test_hrm_blueprint_validates(self):
        """Test HRM blueprint passes IR validation."""
        from app.services.codegen.domains import HrmDomainTemplate
        from app.services.codegen.ir import IRValidator

        template = HrmDomainTemplate()
        blueprint = template.to_app_blueprint("TestHrmApp", "1.0.0")
        clean_blueprint = _clean_meta_fields(blueprint)

        validator = IRValidator()
        result = validator.validate_app_blueprint(clean_blueprint)

        assert result.valid is True, f"Validation failed: {result.issues}"


class TestCrmDomainTemplate:
    """Test CRM domain template (Sprint 196 Track C-03)."""

    def test_crm_has_correct_modules(self):
        """Test CRM domain has required modules."""
        from app.services.codegen.domains import CrmDomainTemplate

        template = CrmDomainTemplate()
        modules = template.get_modules()
        module_names = [m.name for m in modules]

        assert "leads" in module_names
        assert "contacts" in module_names
        assert "deals" in module_names
        assert "activities" in module_names

    def test_crm_domain_name(self):
        """Test CRM domain properties."""
        from app.services.codegen.domains import CrmDomainTemplate

        template = CrmDomainTemplate()
        assert template.domain_name == "crm"
        assert "khách hàng" in template.vietnamese_name

    def test_crm_lead_entity_fields(self):
        """Test Lead entity has required fields (MP-006 L2C)."""
        from app.services.codegen.domains import CrmDomainTemplate

        template = CrmDomainTemplate()
        lead = template.get_entity_by_name("Lead")

        assert lead is not None
        field_names = [f.name for f in lead.fields]

        assert "full_name" in field_names
        assert "phone" in field_names
        assert "source" in field_names
        assert "status" in field_names
        assert "zalo_id" in field_names

    def test_crm_lead_sources_include_zalo(self):
        """Test Lead source choices include Zalo (Vietnamese primary channel)."""
        from app.services.codegen.domains import CrmDomainTemplate

        template = CrmDomainTemplate()
        lead = template.get_entity_by_name("Lead")

        source_field = next(f for f in lead.fields if f.name == "source")
        assert "zalo" in source_field.choices
        assert "facebook" in source_field.choices

    def test_crm_deal_entity_fields(self):
        """Test Deal entity has pipeline fields."""
        from app.services.codegen.domains import CrmDomainTemplate

        template = CrmDomainTemplate()
        deal = template.get_entity_by_name("Deal")

        assert deal is not None
        field_names = [f.name for f in deal.fields]

        assert "title" in field_names
        assert "value_vnd" in field_names
        assert "stage" in field_names
        assert "probability" in field_names

    def test_crm_deal_has_contact_relationship(self):
        """Test Deal has many-to-one relationship to Contact."""
        from app.services.codegen.domains import CrmDomainTemplate

        template = CrmDomainTemplate()
        deal = template.get_entity_by_name("Deal")

        assert deal is not None
        assert len(deal.relationships) >= 1
        contact_rel = next(r for r in deal.relationships if r.name == "contact")
        assert contact_rel.target == "Contact"

    def test_crm_activity_types_include_zalo_message(self):
        """Test Activity types include zalo_message."""
        from app.services.codegen.domains import CrmDomainTemplate

        template = CrmDomainTemplate()
        activity = template.get_entity_by_name("Activity")

        type_field = next(f for f in activity.fields if f.name == "activity_type")
        assert "zalo_message" in type_field.choices

    def test_crm_to_app_blueprint(self):
        """Test CRM generates valid AppBlueprint."""
        from app.services.codegen.domains import CrmDomainTemplate

        template = CrmDomainTemplate()
        blueprint = template.to_app_blueprint("Sales Pro Viet")

        assert blueprint["name"] == "Sales Pro Viet"
        assert blueprint["business_domain"] == "crm"
        assert len(blueprint["modules"]) == 4

    def test_crm_blueprint_validates(self):
        """Test CRM blueprint passes IR validation."""
        from app.services.codegen.domains import CrmDomainTemplate
        from app.services.codegen.ir import IRValidator

        template = CrmDomainTemplate()
        blueprint = template.to_app_blueprint("TestCrmApp", "1.0.0")
        clean_blueprint = _clean_meta_fields(blueprint)

        validator = IRValidator()
        result = validator.validate_app_blueprint(clean_blueprint)

        assert result.valid is True, f"Validation failed: {result.issues}"


class TestNewDomainsRegistration:
    """Test Sprint 196 domain templates are properly registered."""

    def test_registry_has_all_six_domains(self):
        """Test all 6 domains (original 3 + new 3) are registered."""
        from app.services.codegen.domains import DomainRegistry

        domains = DomainRegistry.list_domains()
        domain_names = [d["domain"] for d in domains]

        assert len(domain_names) >= 6
        assert "restaurant" in domain_names
        assert "hotel" in domain_names
        assert "retail" in domain_names
        assert "ecommerce" in domain_names
        assert "hrm" in domain_names
        assert "crm" in domain_names

    def test_new_domains_accessible_via_get(self):
        """Test new domains can be retrieved by name."""
        from app.services.codegen.domains import DomainRegistry

        for domain_name in ["ecommerce", "hrm", "crm"]:
            template = DomainRegistry.get(domain_name)
            assert template is not None, f"Domain '{domain_name}' not found in registry"
            assert template.domain_name == domain_name

    def test_all_domains_have_four_modules(self):
        """Test all 6 domains have exactly 4 modules."""
        from app.services.codegen.domains import DomainRegistry

        for domain_info in DomainRegistry.list_domains():
            template = DomainRegistry.get(domain_info["domain"])
            modules = template.get_modules()
            assert len(modules) == 4, (
                f"Domain '{domain_info['domain']}' has {len(modules)} modules, expected 4"
            )

    def test_all_new_domains_generate_blueprints(self):
        """Test all 3 new domains generate valid blueprints."""
        from app.services.codegen.domains import DomainRegistry
        from app.services.codegen.ir import IRValidator

        validator = IRValidator()

        for domain_name in ["ecommerce", "hrm", "crm"]:
            template = DomainRegistry.get(domain_name)
            blueprint = template.to_app_blueprint(f"Test {domain_name}", "1.0.0")
            clean_blueprint = _clean_meta_fields(blueprint)

            result = validator.validate_app_blueprint(clean_blueprint)
            assert result.valid is True, (
                f"Domain '{domain_name}' blueprint validation failed: {result.issues}"
            )
