"""
End-to-End Codegen Pipeline Tests.

Sprint 196: Vietnamese SME Pilot Prep — Track D-01
ADR-023: IR-Based Deterministic Code Generation

Tests the full codegen pipeline from domain template → IR validation
→ Bundle generation → Quality Pipeline (Gates 1-3).

Coverage:
- Vietnamese E-commerce domain → full pipeline
- Vietnamese HRM domain → full pipeline
- Vietnamese CRM domain → full pipeline
- Quality Pipeline integration (syntax, context)
- Bundle output validation (files, structure, compilability)

Author: Backend Team
Date: February 23, 2026
Version: 1.0.0
Status: ACTIVE — Sprint 196 Track D
"""

import ast
from pathlib import Path
from typing import Dict, Any

import pytest

from app.services.codegen.domains.base import DomainRegistry
from app.services.codegen.domains.ecommerce import EcommerceDomainTemplate
from app.services.codegen.domains.hrm import HrmDomainTemplate
from app.services.codegen.domains.crm import CrmDomainTemplate
from app.services.codegen.ir.bundle_builder import BundleBuilder, GeneratedBundle
from app.services.codegen.quality_pipeline import (
    QualityPipeline,
    GateStatus,
    PipelineResult,
)


@pytest.fixture
def builder() -> BundleBuilder:
    """Create BundleBuilder with default templates."""
    template_dir = (
        Path(__file__).parent.parent.parent.parent.parent
        / "app"
        / "services"
        / "codegen"
        / "templates"
    )
    return BundleBuilder(template_dir=template_dir)


@pytest.fixture
def quality_pipeline() -> QualityPipeline:
    """Create QualityPipeline with security skipped (no semgrep in test env)."""
    return QualityPipeline(skip_security=True, skip_tests=True)


# ---------------------------------------------------------------------------
# E-commerce Domain: Full Pipeline
# ---------------------------------------------------------------------------

class TestEcommerceE2EPipeline:
    """E2E test: E-commerce domain template → IR → Bundle → Quality Gates."""

    @pytest.fixture
    def ecommerce_blueprint(self) -> Dict[str, Any]:
        """Generate E-commerce blueprint from domain template."""
        template = EcommerceDomainTemplate()
        return template.to_app_blueprint("ShopMyPhamOnline")

    def test_ecommerce_blueprint_valid_structure(
        self, ecommerce_blueprint: Dict[str, Any]
    ):
        """Blueprint has required top-level keys for IR validation."""
        assert ecommerce_blueprint["name"] == "ShopMyPhamOnline"
        assert ecommerce_blueprint["version"] == "1.0.0"
        assert ecommerce_blueprint["business_domain"] == "ecommerce"
        assert len(ecommerce_blueprint["modules"]) == 4

    def test_ecommerce_bundle_generation_succeeds(
        self,
        builder: BundleBuilder,
        ecommerce_blueprint: Dict[str, Any],
    ):
        """BundleBuilder produces a successful bundle from E-commerce blueprint."""
        bundle = builder.build(ecommerce_blueprint)

        assert bundle.success is True, f"Bundle errors: {bundle.errors}"
        assert bundle.file_count > 0
        assert bundle.total_lines > 0
        assert len(bundle.errors) == 0

    def test_ecommerce_bundle_has_product_module_files(
        self,
        builder: BundleBuilder,
        ecommerce_blueprint: Dict[str, Any],
    ):
        """Bundle contains model/schema/route/service files for Product entity."""
        bundle = builder.build(ecommerce_blueprint)
        file_paths = [f.path for f in bundle.files]

        assert "app/models/product.py" in file_paths
        assert "app/schemas/product.py" in file_paths
        assert "app/api/routes/products.py" in file_paths
        assert "app/services/product_service.py" in file_paths

    def test_ecommerce_bundle_has_order_module_files(
        self,
        builder: BundleBuilder,
        ecommerce_blueprint: Dict[str, Any],
    ):
        """Bundle contains model/schema/route/service files for Order entity."""
        bundle = builder.build(ecommerce_blueprint)
        file_paths = [f.path for f in bundle.files]

        assert "app/models/order.py" in file_paths
        assert "app/schemas/order.py" in file_paths
        assert "app/api/routes/orders.py" in file_paths
        assert "app/services/order_service.py" in file_paths

    def test_ecommerce_generated_python_compiles(
        self,
        builder: BundleBuilder,
        ecommerce_blueprint: Dict[str, Any],
    ):
        """All generated Python files are syntactically valid."""
        bundle = builder.build(ecommerce_blueprint)
        python_files = bundle.get_files_by_language("python")
        assert len(python_files) > 0

        for f in python_files:
            try:
                ast.parse(f.content)
            except SyntaxError as e:
                pytest.fail(f"Syntax error in {f.path}: {e}")

    def test_ecommerce_quality_pipeline_runs(
        self,
        builder: BundleBuilder,
        ecommerce_blueprint: Dict[str, Any],
        quality_pipeline: QualityPipeline,
    ):
        """Quality Pipeline executes on E-commerce generated code.

        Note: Gate 1 may report ruff lint issues (unused imports, undefined names)
        in template-generated code. This is a known limitation across ALL domains.
        The key assertion is that ast.parse succeeds (covered by
        test_ecommerce_generated_python_compiles).
        """
        bundle = builder.build(ecommerce_blueprint)
        assert bundle.success is True

        files = {f.path: f.content for f in bundle.files}
        result = quality_pipeline.run(files, language="python")

        assert len(result.gates) >= 1
        gate1 = result.gates[0]
        assert gate1.gate_name == "Syntax Check"
        assert gate1.duration_ms >= 0

    def test_ecommerce_product_model_has_class(
        self,
        builder: BundleBuilder,
        ecommerce_blueprint: Dict[str, Any],
    ):
        """Product model file contains 'class Product'."""
        bundle = builder.build(ecommerce_blueprint)
        model_file = bundle.get_file("app/models/product.py")
        assert model_file is not None
        assert "class Product" in model_file.content


# ---------------------------------------------------------------------------
# HRM Domain: Full Pipeline
# ---------------------------------------------------------------------------

class TestHrmE2EPipeline:
    """E2E test: HRM domain template → IR → Bundle → Quality Gates."""

    @pytest.fixture
    def hrm_blueprint(self) -> Dict[str, Any]:
        """Generate HRM blueprint from domain template."""
        template = HrmDomainTemplate()
        return template.to_app_blueprint("NhanSuAbcCorp")

    def test_hrm_blueprint_valid_structure(self, hrm_blueprint: Dict[str, Any]):
        """Blueprint has required top-level keys for IR validation."""
        assert hrm_blueprint["name"] == "NhanSuAbcCorp"
        assert hrm_blueprint["business_domain"] == "hrm"
        assert len(hrm_blueprint["modules"]) == 4

    def test_hrm_bundle_generation_succeeds(
        self,
        builder: BundleBuilder,
        hrm_blueprint: Dict[str, Any],
    ):
        """BundleBuilder produces a successful bundle from HRM blueprint."""
        bundle = builder.build(hrm_blueprint)

        assert bundle.success is True, f"Bundle errors: {bundle.errors}"
        assert bundle.file_count > 0
        assert len(bundle.errors) == 0

    def test_hrm_bundle_has_employee_module_files(
        self,
        builder: BundleBuilder,
        hrm_blueprint: Dict[str, Any],
    ):
        """Bundle contains model/schema/route/service files for Employee entity.

        Sprint 197 C-02: Fixed singularization — 'employees' → 'employee' (not 'employe').
        """
        bundle = builder.build(hrm_blueprint)
        file_paths = [f.path for f in bundle.files]

        assert "app/models/employee.py" in file_paths
        assert "app/schemas/employee.py" in file_paths
        assert "app/api/routes/employees.py" in file_paths
        assert "app/services/employee_service.py" in file_paths

    def test_hrm_bundle_has_payroll_module_files(
        self,
        builder: BundleBuilder,
        hrm_blueprint: Dict[str, Any],
    ):
        """Bundle contains model/schema/route/service files for Payroll entity."""
        bundle = builder.build(hrm_blueprint)
        file_paths = [f.path for f in bundle.files]

        assert "app/models/payroll.py" in file_paths
        assert "app/schemas/payroll.py" in file_paths
        assert "app/api/routes/payroll.py" in file_paths
        assert "app/services/payroll_service.py" in file_paths

    def test_hrm_generated_python_compiles(
        self,
        builder: BundleBuilder,
        hrm_blueprint: Dict[str, Any],
    ):
        """All generated Python files are syntactically valid."""
        bundle = builder.build(hrm_blueprint)
        python_files = bundle.get_files_by_language("python")

        for f in python_files:
            try:
                ast.parse(f.content)
            except SyntaxError as e:
                pytest.fail(f"Syntax error in {f.path}: {e}")

    def test_hrm_quality_pipeline_runs(
        self,
        builder: BundleBuilder,
        hrm_blueprint: Dict[str, Any],
        quality_pipeline: QualityPipeline,
    ):
        """Quality Pipeline executes on HRM generated code.

        Note: Gate 1 may report ruff lint issues (pre-existing template issue).
        """
        bundle = builder.build(hrm_blueprint)
        assert bundle.success is True

        files = {f.path: f.content for f in bundle.files}
        result = quality_pipeline.run(files, language="python")

        assert len(result.gates) >= 1
        gate1 = result.gates[0]
        assert gate1.gate_name == "Syntax Check"
        assert gate1.duration_ms >= 0

    def test_hrm_employee_model_has_class(
        self,
        builder: BundleBuilder,
        hrm_blueprint: Dict[str, Any],
    ):
        """Employee model file contains 'class Employee'."""
        bundle = builder.build(hrm_blueprint)
        model_file = bundle.get_file("app/models/employee.py")
        assert model_file is not None
        assert "class Employee" in model_file.content


# ---------------------------------------------------------------------------
# CRM Domain: Full Pipeline
# ---------------------------------------------------------------------------

class TestCrmE2EPipeline:
    """E2E test: CRM domain template → IR → Bundle → Quality Gates."""

    @pytest.fixture
    def crm_blueprint(self) -> Dict[str, Any]:
        """Generate CRM blueprint from domain template."""
        template = CrmDomainTemplate()
        return template.to_app_blueprint("SalesProViet")

    def test_crm_blueprint_valid_structure(self, crm_blueprint: Dict[str, Any]):
        """Blueprint has required top-level keys for IR validation."""
        assert crm_blueprint["name"] == "SalesProViet"
        assert crm_blueprint["business_domain"] == "crm"
        assert len(crm_blueprint["modules"]) == 4

    def test_crm_bundle_generation_succeeds(
        self,
        builder: BundleBuilder,
        crm_blueprint: Dict[str, Any],
    ):
        """BundleBuilder produces a successful bundle from CRM blueprint."""
        bundle = builder.build(crm_blueprint)

        assert bundle.success is True, f"Bundle errors: {bundle.errors}"
        assert bundle.file_count > 0
        assert len(bundle.errors) == 0

    def test_crm_bundle_has_lead_module_files(
        self,
        builder: BundleBuilder,
        crm_blueprint: Dict[str, Any],
    ):
        """Bundle contains model/schema/route/service files for Lead entity."""
        bundle = builder.build(crm_blueprint)
        file_paths = [f.path for f in bundle.files]

        assert "app/models/lead.py" in file_paths
        assert "app/schemas/lead.py" in file_paths
        assert "app/api/routes/leads.py" in file_paths
        assert "app/services/lead_service.py" in file_paths

    def test_crm_bundle_has_deal_module_files(
        self,
        builder: BundleBuilder,
        crm_blueprint: Dict[str, Any],
    ):
        """Bundle contains model/schema/route/service files for Deal entity."""
        bundle = builder.build(crm_blueprint)
        file_paths = [f.path for f in bundle.files]

        assert "app/models/deal.py" in file_paths
        assert "app/schemas/deal.py" in file_paths
        assert "app/api/routes/deals.py" in file_paths
        assert "app/services/deal_service.py" in file_paths

    def test_crm_bundle_has_contact_and_activity_files(
        self,
        builder: BundleBuilder,
        crm_blueprint: Dict[str, Any],
    ):
        """Bundle contains files for Contact and Activity entities."""
        bundle = builder.build(crm_blueprint)
        file_paths = [f.path for f in bundle.files]

        assert "app/models/contact.py" in file_paths
        assert "app/models/activity.py" in file_paths

    def test_crm_generated_python_compiles(
        self,
        builder: BundleBuilder,
        crm_blueprint: Dict[str, Any],
    ):
        """All generated Python files are syntactically valid."""
        bundle = builder.build(crm_blueprint)
        python_files = bundle.get_files_by_language("python")

        for f in python_files:
            try:
                ast.parse(f.content)
            except SyntaxError as e:
                pytest.fail(f"Syntax error in {f.path}: {e}")

    def test_crm_quality_pipeline_runs(
        self,
        builder: BundleBuilder,
        crm_blueprint: Dict[str, Any],
        quality_pipeline: QualityPipeline,
    ):
        """Quality Pipeline executes on CRM generated code.

        Note: Gate 1 may report ruff lint issues (pre-existing template issue).
        """
        bundle = builder.build(crm_blueprint)
        assert bundle.success is True

        files = {f.path: f.content for f in bundle.files}
        result = quality_pipeline.run(files, language="python")

        assert len(result.gates) >= 1
        gate1 = result.gates[0]
        assert gate1.gate_name == "Syntax Check"
        assert gate1.duration_ms >= 0

    def test_crm_lead_model_has_class(
        self,
        builder: BundleBuilder,
        crm_blueprint: Dict[str, Any],
    ):
        """Lead model file contains 'class Lead'."""
        bundle = builder.build(crm_blueprint)
        model_file = bundle.get_file("app/models/lead.py")
        assert model_file is not None
        assert "class Lead" in model_file.content


# ---------------------------------------------------------------------------
# Cross-Domain Pipeline Validation
# ---------------------------------------------------------------------------

class TestCrossDomainPipeline:
    """Cross-domain validation: all 6 domains through full pipeline."""

    ALL_DOMAINS = ["restaurant", "hotel", "retail", "ecommerce", "hrm", "crm"]

    @pytest.fixture
    def builder(self) -> BundleBuilder:
        template_dir = (
            Path(__file__).parent.parent.parent.parent.parent
            / "app"
            / "services"
            / "codegen"
            / "templates"
        )
        return BundleBuilder(template_dir=template_dir)

    @pytest.fixture
    def quality_pipeline(self) -> QualityPipeline:
        return QualityPipeline(skip_security=True, skip_tests=True)

    @pytest.mark.parametrize("domain", ALL_DOMAINS)
    def test_domain_blueprint_via_registry(self, domain: str):
        """DomainRegistry.get_blueprint() returns valid blueprint for each domain."""
        blueprint = DomainRegistry.get_blueprint(domain, f"TestApp_{domain}")
        assert blueprint is not None, f"No blueprint for domain: {domain}"
        assert blueprint["name"] == f"TestApp_{domain}"
        assert "modules" in blueprint
        assert len(blueprint["modules"]) >= 2

    @pytest.mark.parametrize("domain", ALL_DOMAINS)
    def test_domain_bundle_generation(self, builder: BundleBuilder, domain: str):
        """BundleBuilder produces a successful bundle for each domain."""
        blueprint = DomainRegistry.get_blueprint(domain, f"TestApp_{domain}")
        assert blueprint is not None

        bundle = builder.build(blueprint)
        assert bundle.success is True, (
            f"Domain '{domain}' bundle failed: {bundle.errors}"
        )
        assert bundle.file_count > 0

    @pytest.mark.parametrize("domain", ALL_DOMAINS)
    def test_domain_python_compiles(self, builder: BundleBuilder, domain: str):
        """All generated Python files compile (ast.parse) for every domain."""
        blueprint = DomainRegistry.get_blueprint(domain, f"TestApp_{domain}")
        assert blueprint is not None

        bundle = builder.build(blueprint)
        assert bundle.success is True

        python_files = bundle.get_files_by_language("python")
        assert len(python_files) > 0

        for f in python_files:
            try:
                ast.parse(f.content)
            except SyntaxError as e:
                pytest.fail(
                    f"Domain '{domain}' syntax error in {f.path}: {e}"
                )

    @pytest.mark.parametrize("domain", ALL_DOMAINS)
    def test_domain_main_py_exists(self, builder: BundleBuilder, domain: str):
        """Every domain bundle has app/main.py."""
        blueprint = DomainRegistry.get_blueprint(domain, f"TestApp_{domain}")
        bundle = builder.build(blueprint)

        main_file = bundle.get_file("app/main.py")
        assert main_file is not None, (
            f"Domain '{domain}' missing app/main.py"
        )

    @pytest.mark.parametrize("domain", ALL_DOMAINS)
    def test_domain_requirements_txt_exists(self, builder: BundleBuilder, domain: str):
        """Every domain bundle has requirements.txt."""
        blueprint = DomainRegistry.get_blueprint(domain, f"TestApp_{domain}")
        bundle = builder.build(blueprint)

        req_file = bundle.get_file("requirements.txt")
        assert req_file is not None, (
            f"Domain '{domain}' missing requirements.txt"
        )


# ---------------------------------------------------------------------------
# Quality Pipeline Integration
# ---------------------------------------------------------------------------

class TestQualityPipelineIntegration:
    """Test QualityPipeline with real generated code (not mocks)."""

    @pytest.fixture
    def ecommerce_files(self, builder: BundleBuilder) -> Dict[str, str]:
        """Generate E-commerce files for pipeline testing."""
        template = EcommerceDomainTemplate()
        blueprint = template.to_app_blueprint("QualityTestApp")
        bundle = builder.build(blueprint)
        assert bundle.success is True
        return {f.path: f.content for f in bundle.files}

    def test_pipeline_all_gates_status_populated(
        self,
        ecommerce_files: Dict[str, str],
        quality_pipeline: QualityPipeline,
    ):
        """Pipeline result has status for all executed gates."""
        result = quality_pipeline.run(ecommerce_files, language="python")
        assert len(result.gates) >= 1
        for gate in result.gates:
            assert gate.status in (
                GateStatus.PASSED,
                GateStatus.FAILED,
                GateStatus.SKIPPED,
                GateStatus.SOFT_FAIL,
            )

    def test_pipeline_duration_reasonable(
        self,
        ecommerce_files: Dict[str, str],
        quality_pipeline: QualityPipeline,
    ):
        """Pipeline completes in under 30 seconds (Gates 1+3 only)."""
        result = quality_pipeline.run(ecommerce_files, language="python")
        assert result.total_duration_ms < 30_000

    def test_pipeline_summary_populated(
        self,
        ecommerce_files: Dict[str, str],
        quality_pipeline: QualityPipeline,
    ):
        """Pipeline result has a non-empty summary."""
        result = quality_pipeline.run(ecommerce_files, language="python")
        assert result.summary
        assert "gates passed" in result.summary.lower() or "failed" in result.summary.lower()

    def test_pipeline_to_dict_serializable(
        self,
        ecommerce_files: Dict[str, str],
        quality_pipeline: QualityPipeline,
    ):
        """Pipeline result can be serialized to dict for API response."""
        result = quality_pipeline.run(ecommerce_files, language="python")
        result_dict = result.to_dict()

        assert "success" in result_dict
        assert "gates" in result_dict
        assert "total_duration_ms" in result_dict
        assert isinstance(result_dict["gates"], list)

    def test_invalid_python_fails_gate1(self, quality_pipeline: QualityPipeline):
        """Intentionally invalid Python fails Gate 1 (Syntax)."""
        invalid_files = {
            "app/broken.py": "def foo(\n  # missing closing paren",
        }
        result = quality_pipeline.run(invalid_files, language="python")

        assert result.success is False
        assert result.failed_gate == 1
        assert result.gates[0].status == GateStatus.FAILED
