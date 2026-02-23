"""
CRM Domain Template.

Sprint 196: Vietnamese SME Pilot Prep — Track C-03
ADR-023: IR-Based Deterministic Code Generation

Domain-specific template for Vietnamese CRM:
- Lead management (Quản lý khách tiềm năng)
- Contact management (Quản lý liên hệ)
- Deal pipeline (Pipeline giao dịch)
- Activity tracking (Lịch sử hoạt động)

Key Vietnamese Context:
- Zalo integration patterns (primary messaging channel)
- Vietnamese phone format (09xx, 03xx, 07xx, 08xx, 05xx)
- Relationship-driven sales culture (mối quan hệ)
- Lunar New Year (Tết) sales cycle

CGF Process Integration:
- MP-006 Lead-to-Customer (L2C): Tiềm năng đến Khách hàng
- MDP-005 Customer Master

Author: Backend Team
Date: February 23, 2026
Version: 1.0.0
Status: ACTIVE — Sprint 196 Track C
"""

from typing import List

from .base import (
    DomainTemplate,
    DomainModule,
    DomainEntity,
    DomainField,
    DomainRelationship,
    DomainRegistry,
    FieldType,
    RelationType,
)


@DomainRegistry.register
class CrmDomainTemplate(DomainTemplate):
    """
    CRM Domain Template for Vietnamese SME businesses.

    Provides complete entity structure for:
    - Lead management (Khách tiềm năng)
    - Contact management (Liên hệ)
    - Deal pipeline (Giao dịch)
    - Activity tracking (Hoạt động)

    Vietnamese Sales Context:
    - Zalo as primary outreach channel
    - Relationship-driven culture
    - VND-denominated deals

    Target: Vietnamese SME sales teams
    Price tier: Founder Plan ($99/team/month)
    """

    @property
    def domain_name(self) -> str:
        return "crm"

    @property
    def vietnamese_name(self) -> str:
        return "Quản lý quan hệ khách hàng"

    @property
    def description(self) -> str:
        return (
            "Mẫu ứng dụng CRM cho doanh nghiệp Việt Nam. "
            "Bao gồm quản lý khách tiềm năng, liên hệ, giao dịch và hoạt động. "
            "Tích hợp Zalo, hỗ trợ SĐT Việt Nam."
        )

    def get_modules(self) -> List[DomainModule]:
        return [
            self._create_lead_module(),
            self._create_contact_module(),
            self._create_deal_module(),
            self._create_activity_module(),
        ]

    def _create_lead_module(self) -> DomainModule:
        """Lead management module (MP-006 L2C)."""
        lead = DomainEntity(
            name="Lead",
            vietnamese_name="Khách tiềm năng",
            description="Khách hàng tiềm năng — MP-006 L2C",
            fields=[
                DomainField(
                    name="full_name",
                    field_type=FieldType.STRING,
                    vietnamese_name="Họ và tên",
                    description="Tên khách tiềm năng",
                    required=True,
                    max_length=100,
                ),
                DomainField(
                    name="phone",
                    field_type=FieldType.STRING,
                    vietnamese_name="Số điện thoại",
                    description="SĐT Việt Nam",
                    required=True,
                    max_length=15,
                    indexed=True,
                ),
                DomainField(
                    name="email",
                    field_type=FieldType.STRING,
                    vietnamese_name="Email",
                    description="Địa chỉ email",
                    max_length=200,
                ),
                DomainField(
                    name="company",
                    field_type=FieldType.STRING,
                    vietnamese_name="Công ty",
                    description="Tên công ty / tổ chức",
                    max_length=200,
                ),
                DomainField(
                    name="source",
                    field_type=FieldType.STRING,
                    vietnamese_name="Nguồn",
                    description="Nguồn khách hàng",
                    max_length=50,
                    choices=["zalo", "facebook", "website", "referral", "cold_call", "event"],
                ),
                DomainField(
                    name="status",
                    field_type=FieldType.STRING,
                    vietnamese_name="Trạng thái",
                    description="Trạng thái lead",
                    required=True,
                    max_length=30,
                    choices=["new", "contacted", "qualified", "converted", "lost"],
                    default="new",
                ),
                DomainField(
                    name="zalo_id",
                    field_type=FieldType.STRING,
                    vietnamese_name="Zalo ID",
                    description="Mã Zalo (nếu có)",
                    max_length=50,
                ),
                DomainField(
                    name="notes",
                    field_type=FieldType.TEXT,
                    vietnamese_name="Ghi chú",
                    description="Ghi chú về khách hàng",
                ),
            ],
        )

        return DomainModule(
            name="leads",
            vietnamese_name="Quản lý khách tiềm năng",
            description="Thu thập, phân loại và nuôi dưỡng khách tiềm năng",
            entities=[lead],
        )

    def _create_contact_module(self) -> DomainModule:
        """Contact management module (MDP-005)."""
        contact = DomainEntity(
            name="Contact",
            vietnamese_name="Liên hệ",
            description="Liên hệ khách hàng — MDP-005",
            fields=[
                DomainField(
                    name="full_name",
                    field_type=FieldType.STRING,
                    vietnamese_name="Họ và tên",
                    description="Tên liên hệ",
                    required=True,
                    max_length=100,
                ),
                DomainField(
                    name="phone",
                    field_type=FieldType.STRING,
                    vietnamese_name="Số điện thoại",
                    description="SĐT chính",
                    required=True,
                    max_length=15,
                    indexed=True,
                ),
                DomainField(
                    name="email",
                    field_type=FieldType.STRING,
                    vietnamese_name="Email",
                    description="Email liên hệ",
                    max_length=200,
                ),
                DomainField(
                    name="company",
                    field_type=FieldType.STRING,
                    vietnamese_name="Công ty",
                    description="Công ty / tổ chức",
                    max_length=200,
                ),
                DomainField(
                    name="position",
                    field_type=FieldType.STRING,
                    vietnamese_name="Chức vụ",
                    description="Vị trí công tác",
                    max_length=100,
                ),
                DomainField(
                    name="zalo_id",
                    field_type=FieldType.STRING,
                    vietnamese_name="Zalo ID",
                    description="Mã Zalo liên hệ",
                    max_length=50,
                ),
                DomainField(
                    name="address",
                    field_type=FieldType.TEXT,
                    vietnamese_name="Địa chỉ",
                    description="Địa chỉ liên hệ",
                ),
            ],
        )

        return DomainModule(
            name="contacts",
            vietnamese_name="Quản lý liên hệ",
            description="Danh bạ khách hàng và đối tác",
            entities=[contact],
        )

    def _create_deal_module(self) -> DomainModule:
        """Deal pipeline module."""
        deal = DomainEntity(
            name="Deal",
            vietnamese_name="Giao dịch",
            description="Pipeline giao dịch kinh doanh",
            fields=[
                DomainField(
                    name="title",
                    field_type=FieldType.STRING,
                    vietnamese_name="Tên giao dịch",
                    description="Tên giao dịch / hợp đồng",
                    required=True,
                    max_length=200,
                ),
                DomainField(
                    name="value_vnd",
                    field_type=FieldType.INTEGER,
                    vietnamese_name="Giá trị (VNĐ)",
                    description="Giá trị ước tính giao dịch",
                    min_value=0,
                ),
                DomainField(
                    name="stage",
                    field_type=FieldType.STRING,
                    vietnamese_name="Giai đoạn",
                    description="Giai đoạn trong pipeline",
                    required=True,
                    max_length=30,
                    choices=["prospecting", "qualification", "proposal", "negotiation", "closed_won", "closed_lost"],
                    default="prospecting",
                ),
                DomainField(
                    name="probability",
                    field_type=FieldType.INTEGER,
                    vietnamese_name="Xác suất (%)",
                    description="Xác suất thành công",
                    min_value=0,
                    max_value=100,
                    default=0,
                ),
                DomainField(
                    name="expected_close_date",
                    field_type=FieldType.DATE,
                    vietnamese_name="Ngày dự kiến chốt",
                    description="Ngày dự kiến ký hợp đồng",
                ),
                DomainField(
                    name="notes",
                    field_type=FieldType.TEXT,
                    vietnamese_name="Ghi chú",
                    description="Ghi chú giao dịch",
                ),
            ],
            relationships=[
                DomainRelationship(
                    name="contact",
                    target="Contact",
                    relation_type=RelationType.MANY_TO_ONE,
                    vietnamese_name="Liên hệ",
                    description="Người liên hệ chính",
                ),
            ],
        )

        return DomainModule(
            name="deals",
            vietnamese_name="Pipeline giao dịch",
            description="Quản lý cơ hội kinh doanh từ tiếp cận đến chốt",
            entities=[deal],
        )

    def _create_activity_module(self) -> DomainModule:
        """Activity tracking module."""
        activity = DomainEntity(
            name="Activity",
            vietnamese_name="Hoạt động",
            description="Lịch sử tương tác với khách hàng",
            fields=[
                DomainField(
                    name="activity_type",
                    field_type=FieldType.STRING,
                    vietnamese_name="Loại hoạt động",
                    description="Loại tương tác",
                    required=True,
                    max_length=30,
                    choices=["call", "zalo_message", "email", "meeting", "note", "task"],
                ),
                DomainField(
                    name="subject",
                    field_type=FieldType.STRING,
                    vietnamese_name="Tiêu đề",
                    description="Tiêu đề hoạt động",
                    required=True,
                    max_length=200,
                ),
                DomainField(
                    name="description",
                    field_type=FieldType.TEXT,
                    vietnamese_name="Chi tiết",
                    description="Mô tả chi tiết hoạt động",
                ),
                DomainField(
                    name="activity_date",
                    field_type=FieldType.DATETIME,
                    vietnamese_name="Thời gian",
                    description="Thời gian thực hiện",
                    required=True,
                ),
                DomainField(
                    name="outcome",
                    field_type=FieldType.STRING,
                    vietnamese_name="Kết quả",
                    description="Kết quả hoạt động",
                    max_length=50,
                    choices=["positive", "neutral", "negative", "no_answer"],
                ),
            ],
            relationships=[
                DomainRelationship(
                    name="contact",
                    target="Contact",
                    relation_type=RelationType.MANY_TO_ONE,
                    vietnamese_name="Liên hệ",
                    description="Liên hệ liên quan",
                ),
                DomainRelationship(
                    name="deal",
                    target="Deal",
                    relation_type=RelationType.MANY_TO_ONE,
                    vietnamese_name="Giao dịch",
                    description="Giao dịch liên quan",
                ),
            ],
        )

        return DomainModule(
            name="activities",
            vietnamese_name="Hoạt động",
            description="Ghi nhận cuộc gọi, tin nhắn, gặp mặt, ghi chú",
            entities=[activity],
        )
