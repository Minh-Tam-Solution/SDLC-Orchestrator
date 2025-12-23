"""
Vietnamese SME Demo App Blueprint.

Sprint 45: Multi-Provider Codegen Architecture (EP-06)
Demo for Vietnam SME market wedge (40% strategy).

This module provides a complete demo AppBlueprint for generating
a typical Vietnamese SME business application.

Use Case: Quản lý cửa hàng bán lẻ (Retail Store Management)
- Quản lý sản phẩm (Products)
- Quản lý khách hàng (Customers)
- Quản lý đơn hàng (Orders)
- Quản lý nhân viên (Employees)

Author: Backend Lead
Date: December 23, 2025
Target: Non-tech founders generating MVPs without coding
"""

from app.services.codegen.schemas import (
    AppBlueprint,
    ModuleSpec,
    EntitySpec,
    FieldSpec,
    RelationSpec,
    FieldType,
    RelationType
)


def get_retail_store_blueprint() -> AppBlueprint:
    """
    Generate a complete retail store management app blueprint.

    This demo showcases:
    - Vietnamese field names and descriptions
    - Common SME business entities
    - Relationships between entities
    - Validation rules

    Returns:
        AppBlueprint for a retail store management system
    """
    return AppBlueprint(
        name="QuanLyCuaHang",
        description="Hệ thống quản lý cửa hàng bán lẻ cho doanh nghiệp SME Việt Nam",
        version="1.0.0",
        author="SDLC Orchestrator",
        organization="Vietnamese SME",
        language="python",
        framework="fastapi",
        database="postgresql",
        features={
            "authentication": True,
            "authorization": True,
            "pagination": True,
            "filtering": True,
            "sorting": True,
            "soft_delete": True,
            "audit_log": True,
            "rate_limiting": False,
            "caching": True
        },
        modules=[
            # Module 1: Quản lý sản phẩm
            ModuleSpec(
                name="san_pham",
                description="Quản lý danh mục và sản phẩm",
                generate_crud=True,
                auth_required=True,
                entities=[
                    EntitySpec(
                        name="DanhMuc",
                        description="Danh mục sản phẩm",
                        soft_delete=True,
                        timestamps=True,
                        fields=[
                            FieldSpec(
                                name="id",
                                type=FieldType.UUID,
                                primary=True,
                                description="Mã danh mục"
                            ),
                            FieldSpec(
                                name="ten",
                                type=FieldType.STRING,
                                max_length=100,
                                nullable=False,
                                description="Tên danh mục"
                            ),
                            FieldSpec(
                                name="mo_ta",
                                type=FieldType.TEXT,
                                nullable=True,
                                description="Mô tả danh mục"
                            ),
                            FieldSpec(
                                name="hinh_anh",
                                type=FieldType.IMAGE,
                                nullable=True,
                                description="Hình đại diện"
                            ),
                            FieldSpec(
                                name="thu_tu",
                                type=FieldType.INTEGER,
                                default=0,
                                description="Thứ tự hiển thị"
                            ),
                            FieldSpec(
                                name="hoat_dong",
                                type=FieldType.BOOLEAN,
                                default=True,
                                description="Trạng thái hoạt động"
                            )
                        ],
                        relations=[
                            RelationSpec(
                                name="san_phams",
                                target_entity="SanPham",
                                type=RelationType.ONE_TO_MANY,
                                back_populates="danh_muc"
                            )
                        ]
                    ),
                    EntitySpec(
                        name="SanPham",
                        description="Sản phẩm",
                        soft_delete=True,
                        timestamps=True,
                        auditable=True,
                        fields=[
                            FieldSpec(
                                name="id",
                                type=FieldType.UUID,
                                primary=True,
                                description="Mã sản phẩm"
                            ),
                            FieldSpec(
                                name="ma_sp",
                                type=FieldType.STRING,
                                max_length=50,
                                unique=True,
                                nullable=False,
                                description="Mã SKU sản phẩm"
                            ),
                            FieldSpec(
                                name="ten",
                                type=FieldType.STRING,
                                max_length=200,
                                nullable=False,
                                indexed=True,
                                description="Tên sản phẩm"
                            ),
                            FieldSpec(
                                name="mo_ta",
                                type=FieldType.TEXT,
                                nullable=True,
                                description="Mô tả chi tiết"
                            ),
                            FieldSpec(
                                name="gia_nhap",
                                type=FieldType.DECIMAL,
                                min_value=0,
                                nullable=False,
                                description="Giá nhập (VNĐ)"
                            ),
                            FieldSpec(
                                name="gia_ban",
                                type=FieldType.DECIMAL,
                                min_value=0,
                                nullable=False,
                                description="Giá bán (VNĐ)"
                            ),
                            FieldSpec(
                                name="so_luong_ton",
                                type=FieldType.INTEGER,
                                min_value=0,
                                default=0,
                                description="Số lượng tồn kho"
                            ),
                            FieldSpec(
                                name="don_vi",
                                type=FieldType.STRING,
                                max_length=20,
                                default="cái",
                                description="Đơn vị tính"
                            ),
                            FieldSpec(
                                name="hinh_anh",
                                type=FieldType.JSON,
                                nullable=True,
                                description="Danh sách hình ảnh (URLs)"
                            ),
                            FieldSpec(
                                name="trang_thai",
                                type=FieldType.ENUM,
                                enum_values=["con_hang", "het_hang", "ngung_kinh_doanh"],
                                default="con_hang",
                                description="Trạng thái sản phẩm"
                            ),
                            FieldSpec(
                                name="danh_muc_id",
                                type=FieldType.UUID,
                                nullable=True,
                                indexed=True,
                                description="Mã danh mục"
                            )
                        ],
                        relations=[
                            RelationSpec(
                                name="danh_muc",
                                target_entity="DanhMuc",
                                type=RelationType.MANY_TO_ONE,
                                back_populates="san_phams"
                            )
                        ]
                    )
                ]
            ),

            # Module 2: Quản lý khách hàng
            ModuleSpec(
                name="khach_hang",
                description="Quản lý thông tin khách hàng",
                generate_crud=True,
                auth_required=True,
                entities=[
                    EntitySpec(
                        name="KhachHang",
                        description="Khách hàng",
                        soft_delete=True,
                        timestamps=True,
                        fields=[
                            FieldSpec(
                                name="id",
                                type=FieldType.UUID,
                                primary=True,
                                description="Mã khách hàng"
                            ),
                            FieldSpec(
                                name="ho_ten",
                                type=FieldType.STRING,
                                max_length=100,
                                nullable=False,
                                indexed=True,
                                description="Họ và tên"
                            ),
                            FieldSpec(
                                name="so_dien_thoai",
                                type=FieldType.STRING,
                                max_length=15,
                                unique=True,
                                nullable=False,
                                regex=r"^(0|\+84)[0-9]{9,10}$",
                                description="Số điện thoại"
                            ),
                            FieldSpec(
                                name="email",
                                type=FieldType.STRING,
                                max_length=100,
                                nullable=True,
                                description="Địa chỉ email"
                            ),
                            FieldSpec(
                                name="dia_chi",
                                type=FieldType.TEXT,
                                nullable=True,
                                description="Địa chỉ giao hàng"
                            ),
                            FieldSpec(
                                name="ngay_sinh",
                                type=FieldType.DATE,
                                nullable=True,
                                description="Ngày sinh"
                            ),
                            FieldSpec(
                                name="gioi_tinh",
                                type=FieldType.ENUM,
                                enum_values=["nam", "nu", "khac"],
                                nullable=True,
                                description="Giới tính"
                            ),
                            FieldSpec(
                                name="diem_tich_luy",
                                type=FieldType.INTEGER,
                                min_value=0,
                                default=0,
                                description="Điểm tích lũy"
                            ),
                            FieldSpec(
                                name="hang_thanh_vien",
                                type=FieldType.ENUM,
                                enum_values=["thuong", "bac", "vang", "kim_cuong"],
                                default="thuong",
                                description="Hạng thành viên"
                            ),
                            FieldSpec(
                                name="ghi_chu",
                                type=FieldType.TEXT,
                                nullable=True,
                                description="Ghi chú về khách hàng"
                            )
                        ],
                        relations=[
                            RelationSpec(
                                name="don_hangs",
                                target_entity="DonHang",
                                type=RelationType.ONE_TO_MANY,
                                back_populates="khach_hang"
                            )
                        ]
                    )
                ]
            ),

            # Module 3: Quản lý đơn hàng
            ModuleSpec(
                name="don_hang",
                description="Quản lý đơn hàng và thanh toán",
                generate_crud=True,
                auth_required=True,
                entities=[
                    EntitySpec(
                        name="DonHang",
                        description="Đơn hàng",
                        soft_delete=True,
                        timestamps=True,
                        auditable=True,
                        fields=[
                            FieldSpec(
                                name="id",
                                type=FieldType.UUID,
                                primary=True,
                                description="Mã đơn hàng"
                            ),
                            FieldSpec(
                                name="ma_don",
                                type=FieldType.STRING,
                                max_length=20,
                                unique=True,
                                nullable=False,
                                description="Mã đơn hàng hiển thị"
                            ),
                            FieldSpec(
                                name="khach_hang_id",
                                type=FieldType.UUID,
                                nullable=True,
                                indexed=True,
                                description="Mã khách hàng"
                            ),
                            FieldSpec(
                                name="nhan_vien_id",
                                type=FieldType.UUID,
                                nullable=False,
                                indexed=True,
                                description="Mã nhân viên bán hàng"
                            ),
                            FieldSpec(
                                name="tong_tien",
                                type=FieldType.DECIMAL,
                                min_value=0,
                                nullable=False,
                                description="Tổng tiền (VNĐ)"
                            ),
                            FieldSpec(
                                name="giam_gia",
                                type=FieldType.DECIMAL,
                                min_value=0,
                                default=0,
                                description="Giảm giá (VNĐ)"
                            ),
                            FieldSpec(
                                name="thanh_toan",
                                type=FieldType.DECIMAL,
                                min_value=0,
                                nullable=False,
                                description="Số tiền thanh toán (VNĐ)"
                            ),
                            FieldSpec(
                                name="phuong_thuc_tt",
                                type=FieldType.ENUM,
                                enum_values=["tien_mat", "chuyen_khoan", "the", "vi_dien_tu"],
                                default="tien_mat",
                                description="Phương thức thanh toán"
                            ),
                            FieldSpec(
                                name="trang_thai",
                                type=FieldType.ENUM,
                                enum_values=["cho_xu_ly", "dang_giao", "hoan_thanh", "da_huy"],
                                default="cho_xu_ly",
                                description="Trạng thái đơn hàng"
                            ),
                            FieldSpec(
                                name="dia_chi_giao",
                                type=FieldType.TEXT,
                                nullable=True,
                                description="Địa chỉ giao hàng"
                            ),
                            FieldSpec(
                                name="ghi_chu",
                                type=FieldType.TEXT,
                                nullable=True,
                                description="Ghi chú đơn hàng"
                            )
                        ],
                        relations=[
                            RelationSpec(
                                name="khach_hang",
                                target_entity="KhachHang",
                                type=RelationType.MANY_TO_ONE,
                                back_populates="don_hangs"
                            ),
                            RelationSpec(
                                name="chi_tiets",
                                target_entity="ChiTietDonHang",
                                type=RelationType.ONE_TO_MANY,
                                back_populates="don_hang"
                            )
                        ]
                    ),
                    EntitySpec(
                        name="ChiTietDonHang",
                        description="Chi tiết đơn hàng",
                        soft_delete=False,
                        timestamps=True,
                        fields=[
                            FieldSpec(
                                name="id",
                                type=FieldType.UUID,
                                primary=True,
                                description="Mã chi tiết"
                            ),
                            FieldSpec(
                                name="don_hang_id",
                                type=FieldType.UUID,
                                nullable=False,
                                indexed=True,
                                description="Mã đơn hàng"
                            ),
                            FieldSpec(
                                name="san_pham_id",
                                type=FieldType.UUID,
                                nullable=False,
                                indexed=True,
                                description="Mã sản phẩm"
                            ),
                            FieldSpec(
                                name="ten_san_pham",
                                type=FieldType.STRING,
                                max_length=200,
                                nullable=False,
                                description="Tên sản phẩm (snapshot)"
                            ),
                            FieldSpec(
                                name="so_luong",
                                type=FieldType.INTEGER,
                                min_value=1,
                                nullable=False,
                                description="Số lượng"
                            ),
                            FieldSpec(
                                name="don_gia",
                                type=FieldType.DECIMAL,
                                min_value=0,
                                nullable=False,
                                description="Đơn giá (VNĐ)"
                            ),
                            FieldSpec(
                                name="thanh_tien",
                                type=FieldType.DECIMAL,
                                min_value=0,
                                nullable=False,
                                description="Thành tiền (VNĐ)"
                            )
                        ],
                        relations=[
                            RelationSpec(
                                name="don_hang",
                                target_entity="DonHang",
                                type=RelationType.MANY_TO_ONE,
                                back_populates="chi_tiets"
                            )
                        ]
                    )
                ]
            ),

            # Module 4: Quản lý nhân viên
            ModuleSpec(
                name="nhan_vien",
                description="Quản lý nhân viên cửa hàng",
                generate_crud=True,
                auth_required=True,
                roles_required=["admin", "manager"],
                entities=[
                    EntitySpec(
                        name="NhanVien",
                        description="Nhân viên",
                        soft_delete=True,
                        timestamps=True,
                        auditable=True,
                        fields=[
                            FieldSpec(
                                name="id",
                                type=FieldType.UUID,
                                primary=True,
                                description="Mã nhân viên"
                            ),
                            FieldSpec(
                                name="ma_nv",
                                type=FieldType.STRING,
                                max_length=20,
                                unique=True,
                                nullable=False,
                                description="Mã nhân viên hiển thị"
                            ),
                            FieldSpec(
                                name="ho_ten",
                                type=FieldType.STRING,
                                max_length=100,
                                nullable=False,
                                description="Họ và tên"
                            ),
                            FieldSpec(
                                name="so_dien_thoai",
                                type=FieldType.STRING,
                                max_length=15,
                                nullable=False,
                                description="Số điện thoại"
                            ),
                            FieldSpec(
                                name="email",
                                type=FieldType.STRING,
                                max_length=100,
                                nullable=True,
                                description="Email"
                            ),
                            FieldSpec(
                                name="dia_chi",
                                type=FieldType.TEXT,
                                nullable=True,
                                description="Địa chỉ"
                            ),
                            FieldSpec(
                                name="chuc_vu",
                                type=FieldType.ENUM,
                                enum_values=["nhan_vien", "truong_ca", "quan_ly", "admin"],
                                default="nhan_vien",
                                description="Chức vụ"
                            ),
                            FieldSpec(
                                name="luong_co_ban",
                                type=FieldType.DECIMAL,
                                min_value=0,
                                nullable=True,
                                description="Lương cơ bản (VNĐ)"
                            ),
                            FieldSpec(
                                name="ngay_vao_lam",
                                type=FieldType.DATE,
                                nullable=False,
                                description="Ngày vào làm"
                            ),
                            FieldSpec(
                                name="trang_thai",
                                type=FieldType.ENUM,
                                enum_values=["dang_lam", "nghi_phep", "da_nghi"],
                                default="dang_lam",
                                description="Trạng thái"
                            )
                        ]
                    )
                ]
            )
        ]
    )


def get_minimal_demo_blueprint() -> AppBlueprint:
    """
    Generate a minimal demo blueprint for testing.

    Useful for quick tests and integration verification.

    Returns:
        Minimal AppBlueprint with single entity
    """
    return AppBlueprint(
        name="MinimalDemo",
        description="Demo tối giản",
        version="1.0.0",
        modules=[
            ModuleSpec(
                name="items",
                description="Quản lý items",
                entities=[
                    EntitySpec(
                        name="Item",
                        description="Item đơn giản",
                        fields=[
                            FieldSpec(
                                name="id",
                                type=FieldType.UUID,
                                primary=True
                            ),
                            FieldSpec(
                                name="name",
                                type=FieldType.STRING,
                                max_length=100,
                                nullable=False
                            ),
                            FieldSpec(
                                name="description",
                                type=FieldType.TEXT,
                                nullable=True
                            )
                        ]
                    )
                ]
            )
        ]
    )


# Export blueprints for CLI/API use
DEMO_BLUEPRINTS = {
    "retail_store": get_retail_store_blueprint,
    "minimal": get_minimal_demo_blueprint
}


if __name__ == "__main__":
    # Print demo blueprint as JSON for testing
    import json

    blueprint = get_retail_store_blueprint()
    print(json.dumps(blueprint.model_dump(), indent=2, ensure_ascii=False))
