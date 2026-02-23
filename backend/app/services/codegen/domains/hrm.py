"""
HRM Domain Template.

Sprint 196: Vietnamese SME Pilot Prep — Track C-02
ADR-023: IR-Based Deterministic Code Generation

Domain-specific template for Vietnamese HR Management:
- Employee management (Quản lý nhân viên)
- Attendance tracking (Chấm công)
- Payroll (Bảng lương)
- Leave management (Nghỉ phép)

Key Vietnamese Context:
- Vietnamese labor law (Bộ luật Lao động 2019)
- Social insurance (BHXH: 8% employee, 17.5% employer)
- Health insurance (BHYT: 1.5% employee, 3% employer)
- Unemployment insurance (BHTN: 1% employee, 1% employer)
- 13th-month salary (Lương tháng 13)
- Public holidays (11 days/year + regional holidays)

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
class HrmDomainTemplate(DomainTemplate):
    """
    HRM Domain Template for Vietnamese SME businesses.

    Provides complete entity structure for:
    - Employee management (Nhân viên)
    - Attendance tracking (Chấm công)
    - Payroll processing (Bảng lương)
    - Leave management (Nghỉ phép)

    Vietnamese Labor Law Compliance:
    - BHXH/BHYT/BHTN contribution rates
    - Mandatory 13th-month salary
    - 12 annual leave days minimum
    - 11 public holidays per year

    Target: Vietnamese SME (50-200 employees)
    Price tier: Founder Plan ($99/team/month)
    """

    @property
    def domain_name(self) -> str:
        return "hrm"

    @property
    def vietnamese_name(self) -> str:
        return "Quản lý nhân sự"

    @property
    def description(self) -> str:
        return (
            "Mẫu ứng dụng quản lý nhân sự cho doanh nghiệp Việt Nam. "
            "Bao gồm quản lý nhân viên, chấm công, bảng lương và nghỉ phép. "
            "Tuân thủ Bộ luật Lao động 2019."
        )

    def get_modules(self) -> List[DomainModule]:
        return [
            self._create_employee_module(),
            self._create_attendance_module(),
            self._create_payroll_module(),
            self._create_leave_module(),
        ]

    def _create_employee_module(self) -> DomainModule:
        """Employee management module."""
        employee = DomainEntity(
            name="Employee",
            vietnamese_name="Nhân viên",
            description="Hồ sơ nhân viên — tuân thủ luật lao động VN",
            fields=[
                DomainField(
                    name="employee_code",
                    field_type=FieldType.STRING,
                    vietnamese_name="Mã nhân viên",
                    description="Mã nhân viên (NV-XXXX)",
                    required=True,
                    max_length=20,
                    unique=True,
                    indexed=True,
                ),
                DomainField(
                    name="full_name",
                    field_type=FieldType.STRING,
                    vietnamese_name="Họ và tên",
                    description="Họ tên đầy đủ",
                    required=True,
                    max_length=100,
                ),
                DomainField(
                    name="phone",
                    field_type=FieldType.STRING,
                    vietnamese_name="Số điện thoại",
                    description="SĐT liên hệ",
                    required=True,
                    max_length=15,
                ),
                DomainField(
                    name="email",
                    field_type=FieldType.STRING,
                    vietnamese_name="Email",
                    description="Email công ty",
                    max_length=200,
                ),
                DomainField(
                    name="id_number",
                    field_type=FieldType.STRING,
                    vietnamese_name="CCCD/CMND",
                    description="Số căn cước công dân",
                    required=True,
                    max_length=20,
                    unique=True,
                ),
                DomainField(
                    name="department",
                    field_type=FieldType.STRING,
                    vietnamese_name="Phòng ban",
                    description="Phòng ban công tác",
                    required=True,
                    max_length=100,
                ),
                DomainField(
                    name="position",
                    field_type=FieldType.STRING,
                    vietnamese_name="Chức vụ",
                    description="Vị trí công việc",
                    required=True,
                    max_length=100,
                ),
                DomainField(
                    name="base_salary_vnd",
                    field_type=FieldType.INTEGER,
                    vietnamese_name="Lương cơ bản (VNĐ)",
                    description="Lương cơ bản tháng",
                    required=True,
                    min_value=0,
                ),
                DomainField(
                    name="start_date",
                    field_type=FieldType.DATE,
                    vietnamese_name="Ngày vào làm",
                    description="Ngày bắt đầu hợp đồng",
                    required=True,
                ),
                DomainField(
                    name="contract_type",
                    field_type=FieldType.STRING,
                    vietnamese_name="Loại hợp đồng",
                    description="Loại HĐLĐ",
                    max_length=30,
                    choices=["probation", "definite_1y", "definite_3y", "indefinite"],
                ),
                DomainField(
                    name="is_active",
                    field_type=FieldType.BOOLEAN,
                    vietnamese_name="Đang làm việc",
                    description="Nhân viên đang hoạt động",
                    default=True,
                ),
            ],
        )

        return DomainModule(
            name="employees",
            vietnamese_name="Quản lý nhân viên",
            description="Hồ sơ, hợp đồng và thông tin nhân viên",
            entities=[employee],
        )

    def _create_attendance_module(self) -> DomainModule:
        """Attendance tracking module."""
        attendance = DomainEntity(
            name="Attendance",
            vietnamese_name="Chấm công",
            description="Bảng chấm công nhân viên",
            fields=[
                DomainField(
                    name="date",
                    field_type=FieldType.DATE,
                    vietnamese_name="Ngày",
                    description="Ngày chấm công",
                    required=True,
                    indexed=True,
                ),
                DomainField(
                    name="check_in",
                    field_type=FieldType.DATETIME,
                    vietnamese_name="Giờ vào",
                    description="Thời gian check-in",
                ),
                DomainField(
                    name="check_out",
                    field_type=FieldType.DATETIME,
                    vietnamese_name="Giờ ra",
                    description="Thời gian check-out",
                ),
                DomainField(
                    name="status",
                    field_type=FieldType.STRING,
                    vietnamese_name="Trạng thái",
                    description="Trạng thái chấm công",
                    required=True,
                    max_length=20,
                    choices=["present", "absent", "late", "half_day", "holiday", "leave"],
                ),
                DomainField(
                    name="overtime_hours",
                    field_type=FieldType.FLOAT,
                    vietnamese_name="Giờ tăng ca",
                    description="Số giờ làm thêm",
                    default=0,
                    min_value=0,
                ),
            ],
            relationships=[
                DomainRelationship(
                    name="employee",
                    target="Employee",
                    relation_type=RelationType.MANY_TO_ONE,
                    vietnamese_name="Nhân viên",
                    description="Nhân viên chấm công",
                ),
            ],
        )

        return DomainModule(
            name="attendance",
            vietnamese_name="Chấm công",
            description="Quản lý giờ làm việc và tăng ca",
            entities=[attendance],
        )

    def _create_payroll_module(self) -> DomainModule:
        """Payroll module (BHXH/BHYT/BHTN compliant)."""
        payroll = DomainEntity(
            name="Payroll",
            vietnamese_name="Bảng lương",
            description="Bảng lương tháng — tính BHXH/BHYT/BHTN",
            fields=[
                DomainField(
                    name="month",
                    field_type=FieldType.INTEGER,
                    vietnamese_name="Tháng",
                    description="Tháng lương (1-12)",
                    required=True,
                    min_value=1,
                    max_value=12,
                ),
                DomainField(
                    name="year",
                    field_type=FieldType.INTEGER,
                    vietnamese_name="Năm",
                    description="Năm lương",
                    required=True,
                ),
                DomainField(
                    name="base_salary_vnd",
                    field_type=FieldType.INTEGER,
                    vietnamese_name="Lương cơ bản",
                    description="Lương cơ bản tháng",
                    required=True,
                    min_value=0,
                ),
                DomainField(
                    name="allowances_vnd",
                    field_type=FieldType.INTEGER,
                    vietnamese_name="Phụ cấp",
                    description="Tổng phụ cấp (ăn trưa, xăng xe, ...)",
                    default=0,
                    min_value=0,
                ),
                DomainField(
                    name="bhxh_employee_vnd",
                    field_type=FieldType.INTEGER,
                    vietnamese_name="BHXH (NV đóng)",
                    description="Bảo hiểm xã hội — 8% lương",
                    default=0,
                ),
                DomainField(
                    name="bhyt_employee_vnd",
                    field_type=FieldType.INTEGER,
                    vietnamese_name="BHYT (NV đóng)",
                    description="Bảo hiểm y tế — 1.5% lương",
                    default=0,
                ),
                DomainField(
                    name="bhtn_employee_vnd",
                    field_type=FieldType.INTEGER,
                    vietnamese_name="BHTN (NV đóng)",
                    description="Bảo hiểm thất nghiệp — 1% lương",
                    default=0,
                ),
                DomainField(
                    name="pit_vnd",
                    field_type=FieldType.INTEGER,
                    vietnamese_name="Thuế TNCN",
                    description="Thuế thu nhập cá nhân",
                    default=0,
                ),
                DomainField(
                    name="net_salary_vnd",
                    field_type=FieldType.INTEGER,
                    vietnamese_name="Lương thực nhận",
                    description="Lương thực nhận sau khấu trừ",
                    required=True,
                ),
                DomainField(
                    name="status",
                    field_type=FieldType.STRING,
                    vietnamese_name="Trạng thái",
                    description="Trạng thái bảng lương",
                    max_length=20,
                    choices=["draft", "approved", "paid"],
                    default="draft",
                ),
            ],
            relationships=[
                DomainRelationship(
                    name="employee",
                    target="Employee",
                    relation_type=RelationType.MANY_TO_ONE,
                    vietnamese_name="Nhân viên",
                    description="Nhân viên nhận lương",
                ),
            ],
        )

        return DomainModule(
            name="payroll",
            vietnamese_name="Bảng lương",
            description="Tính lương, BHXH, thuế TNCN",
            entities=[payroll],
        )

    def _create_leave_module(self) -> DomainModule:
        """Leave management module (Vietnamese labor law)."""
        leave = DomainEntity(
            name="LeaveRequest",
            vietnamese_name="Đơn nghỉ phép",
            description="Đơn xin nghỉ phép — tối thiểu 12 ngày/năm",
            fields=[
                DomainField(
                    name="leave_type",
                    field_type=FieldType.STRING,
                    vietnamese_name="Loại nghỉ",
                    description="Loại nghỉ phép",
                    required=True,
                    max_length=30,
                    choices=["annual", "sick", "maternity", "paternity", "unpaid", "wedding", "funeral"],
                ),
                DomainField(
                    name="start_date",
                    field_type=FieldType.DATE,
                    vietnamese_name="Từ ngày",
                    description="Ngày bắt đầu nghỉ",
                    required=True,
                ),
                DomainField(
                    name="end_date",
                    field_type=FieldType.DATE,
                    vietnamese_name="Đến ngày",
                    description="Ngày kết thúc nghỉ",
                    required=True,
                ),
                DomainField(
                    name="days",
                    field_type=FieldType.FLOAT,
                    vietnamese_name="Số ngày nghỉ",
                    description="Tổng số ngày nghỉ",
                    required=True,
                    min_value=0.5,
                ),
                DomainField(
                    name="reason",
                    field_type=FieldType.TEXT,
                    vietnamese_name="Lý do",
                    description="Lý do xin nghỉ",
                ),
                DomainField(
                    name="status",
                    field_type=FieldType.STRING,
                    vietnamese_name="Trạng thái",
                    description="Trạng thái duyệt",
                    required=True,
                    max_length=20,
                    choices=["pending", "approved", "rejected"],
                    default="pending",
                ),
            ],
            relationships=[
                DomainRelationship(
                    name="employee",
                    target="Employee",
                    relation_type=RelationType.MANY_TO_ONE,
                    vietnamese_name="Nhân viên",
                    description="Nhân viên xin nghỉ",
                ),
            ],
        )

        return DomainModule(
            name="leave",
            vietnamese_name="Nghỉ phép",
            description="Quản lý nghỉ phép, xin phép, duyệt phép",
            entities=[leave],
        )
