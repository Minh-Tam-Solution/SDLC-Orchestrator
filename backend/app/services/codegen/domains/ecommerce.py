"""
E-commerce Domain Template.

Sprint 196: Vietnamese SME Pilot Prep — Track C-01
ADR-023: IR-Based Deterministic Code Generation

Domain-specific template for Vietnamese e-commerce businesses:
- Marketplace sellers (Shopee, Tiki, Lazada)
- D2C (Direct to Consumer) shops
- Wholesale B2B platforms

CGF Process Integration:
- MP-002 Order-to-Cash (O2C): Đơn hàng đến Thu tiền
- MP-006 Lead-to-Customer (L2C): Tiềm năng đến Khách hàng
- MDG-003 Product & Pricing Governance
- MDP-005 Customer Master

Key Vietnamese Context:
- VND currency (no decimal, large amounts)
- COD (Cash on Delivery) as primary payment method
- Shopee/Tiki/Lazada marketplace integration patterns
- Vietnamese address format (Tỉnh/Thành phố → Quận/Huyện → Phường/Xã)

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
class EcommerceDomainTemplate(DomainTemplate):
    """
    E-commerce Domain Template for Vietnamese online retail.

    Provides complete entity structure for:
    - Product catalog (Danh mục sản phẩm)
    - Order management (Quản lý đơn hàng)
    - Customer management (Khách hàng)
    - Payment/COD (Thanh toán / Thu hộ)

    CGF Compliance:
    - Follows MDG-003 Product & Pricing Governance
    - Integrates with MP-002 Order-to-Cash (O2C)
    - VND-native (no decimal pricing)

    Target: Vietnamese SME e-commerce businesses
    Price tier: Founder Plan ($99/team/month)
    """

    @property
    def domain_name(self) -> str:
        return "ecommerce"

    @property
    def vietnamese_name(self) -> str:
        return "Thương mại điện tử"

    @property
    def description(self) -> str:
        return (
            "Mẫu ứng dụng thương mại điện tử cho doanh nghiệp Việt Nam. "
            "Bao gồm quản lý sản phẩm, đơn hàng, khách hàng và thanh toán COD."
        )

    def get_modules(self) -> List[DomainModule]:
        return [
            self._create_product_module(),
            self._create_order_module(),
            self._create_customer_module(),
            self._create_payment_module(),
        ]

    def _create_product_module(self) -> DomainModule:
        """Product catalog module (MDG-003 compliant)."""
        product = DomainEntity(
            name="Product",
            vietnamese_name="Sản phẩm",
            description="Sản phẩm bán online — MDG-003",
            fields=[
                DomainField(
                    name="sku",
                    field_type=FieldType.STRING,
                    vietnamese_name="Mã SKU",
                    description="Mã sản phẩm duy nhất",
                    required=True,
                    max_length=50,
                    unique=True,
                    indexed=True,
                ),
                DomainField(
                    name="name",
                    field_type=FieldType.STRING,
                    vietnamese_name="Tên sản phẩm",
                    description="Tên hiển thị sản phẩm",
                    required=True,
                    max_length=200,
                ),
                DomainField(
                    name="price_vnd",
                    field_type=FieldType.INTEGER,
                    vietnamese_name="Giá bán (VNĐ)",
                    description="Giá bán lẻ bằng VNĐ (không thập phân)",
                    required=True,
                    min_value=0,
                ),
                DomainField(
                    name="stock_quantity",
                    field_type=FieldType.INTEGER,
                    vietnamese_name="Tồn kho",
                    description="Số lượng còn trong kho",
                    required=True,
                    default=0,
                    min_value=0,
                ),
                DomainField(
                    name="category",
                    field_type=FieldType.STRING,
                    vietnamese_name="Danh mục",
                    description="Danh mục sản phẩm",
                    max_length=100,
                ),
                DomainField(
                    name="is_active",
                    field_type=FieldType.BOOLEAN,
                    vietnamese_name="Đang bán",
                    description="Sản phẩm có đang bán không",
                    default=True,
                ),
            ],
        )

        return DomainModule(
            name="products",
            vietnamese_name="Quản lý sản phẩm",
            description="Quản lý danh mục và sản phẩm bán online",
            entities=[product],
        )

    def _create_order_module(self) -> DomainModule:
        """Order management module (MP-002 O2C)."""
        order = DomainEntity(
            name="Order",
            vietnamese_name="Đơn hàng",
            description="Đơn hàng online — MP-002 O2C",
            fields=[
                DomainField(
                    name="order_code",
                    field_type=FieldType.STRING,
                    vietnamese_name="Mã đơn hàng",
                    description="Mã đơn hàng tự sinh (ORD-XXXXXX)",
                    required=True,
                    max_length=20,
                    unique=True,
                    indexed=True,
                ),
                DomainField(
                    name="total_vnd",
                    field_type=FieldType.INTEGER,
                    vietnamese_name="Tổng tiền (VNĐ)",
                    description="Tổng giá trị đơn hàng",
                    required=True,
                    min_value=0,
                ),
                DomainField(
                    name="status",
                    field_type=FieldType.STRING,
                    vietnamese_name="Trạng thái",
                    description="Trạng thái đơn hàng",
                    required=True,
                    max_length=30,
                    choices=["pending", "confirmed", "shipping", "delivered", "cancelled"],
                    default="pending",
                ),
                DomainField(
                    name="payment_method",
                    field_type=FieldType.STRING,
                    vietnamese_name="Phương thức thanh toán",
                    description="COD / Bank Transfer / E-wallet",
                    required=True,
                    max_length=30,
                    choices=["cod", "bank_transfer", "momo", "zalopay", "vnpay"],
                ),
                DomainField(
                    name="shipping_address",
                    field_type=FieldType.TEXT,
                    vietnamese_name="Địa chỉ giao hàng",
                    description="Địa chỉ giao hàng đầy đủ",
                    required=True,
                ),
                DomainField(
                    name="notes",
                    field_type=FieldType.TEXT,
                    vietnamese_name="Ghi chú",
                    description="Ghi chú từ khách hàng",
                ),
            ],
            relationships=[
                DomainRelationship(
                    name="customer",
                    target="Customer",
                    relation_type=RelationType.MANY_TO_ONE,
                    vietnamese_name="Khách hàng",
                    description="Khách hàng đặt đơn",
                ),
            ],
        )

        order_item = DomainEntity(
            name="OrderItem",
            vietnamese_name="Chi tiết đơn hàng",
            description="Sản phẩm trong đơn hàng",
            fields=[
                DomainField(
                    name="quantity",
                    field_type=FieldType.INTEGER,
                    vietnamese_name="Số lượng",
                    description="Số lượng mua",
                    required=True,
                    min_value=1,
                ),
                DomainField(
                    name="unit_price_vnd",
                    field_type=FieldType.INTEGER,
                    vietnamese_name="Đơn giá (VNĐ)",
                    description="Giá tại thời điểm mua",
                    required=True,
                    min_value=0,
                ),
            ],
            relationships=[
                DomainRelationship(
                    name="order",
                    target="Order",
                    relation_type=RelationType.MANY_TO_ONE,
                    vietnamese_name="Đơn hàng",
                    description="Thuộc đơn hàng nào",
                ),
                DomainRelationship(
                    name="product",
                    target="Product",
                    relation_type=RelationType.MANY_TO_ONE,
                    vietnamese_name="Sản phẩm",
                    description="Sản phẩm được mua",
                ),
            ],
        )

        return DomainModule(
            name="orders",
            vietnamese_name="Quản lý đơn hàng",
            description="Đặt hàng, xử lý và theo dõi đơn hàng",
            entities=[order, order_item],
        )

    def _create_customer_module(self) -> DomainModule:
        """Customer management module (MDP-005)."""
        customer = DomainEntity(
            name="Customer",
            vietnamese_name="Khách hàng",
            description="Khách hàng mua hàng online — MDP-005",
            fields=[
                DomainField(
                    name="phone",
                    field_type=FieldType.STRING,
                    vietnamese_name="Số điện thoại",
                    description="SĐT Việt Nam (09xx, 03xx, ...)",
                    required=True,
                    max_length=15,
                    unique=True,
                    indexed=True,
                ),
                DomainField(
                    name="full_name",
                    field_type=FieldType.STRING,
                    vietnamese_name="Họ và tên",
                    description="Tên đầy đủ khách hàng",
                    required=True,
                    max_length=100,
                ),
                DomainField(
                    name="email",
                    field_type=FieldType.STRING,
                    vietnamese_name="Email",
                    description="Địa chỉ email",
                    max_length=200,
                ),
                DomainField(
                    name="default_address",
                    field_type=FieldType.TEXT,
                    vietnamese_name="Địa chỉ mặc định",
                    description="Địa chỉ giao hàng mặc định",
                ),
            ],
        )

        return DomainModule(
            name="customers",
            vietnamese_name="Quản lý khách hàng",
            description="Hồ sơ và lịch sử mua hàng khách hàng",
            entities=[customer],
        )

    def _create_payment_module(self) -> DomainModule:
        """Payment tracking module — COD-centric."""
        payment = DomainEntity(
            name="Payment",
            vietnamese_name="Thanh toán",
            description="Theo dõi thanh toán — hỗ trợ COD",
            fields=[
                DomainField(
                    name="amount_vnd",
                    field_type=FieldType.INTEGER,
                    vietnamese_name="Số tiền (VNĐ)",
                    description="Số tiền thanh toán",
                    required=True,
                    min_value=0,
                ),
                DomainField(
                    name="method",
                    field_type=FieldType.STRING,
                    vietnamese_name="Phương thức",
                    description="Hình thức thanh toán",
                    required=True,
                    max_length=30,
                    choices=["cod", "bank_transfer", "momo", "zalopay", "vnpay"],
                ),
                DomainField(
                    name="status",
                    field_type=FieldType.STRING,
                    vietnamese_name="Trạng thái",
                    description="Trạng thái thanh toán",
                    required=True,
                    max_length=20,
                    choices=["pending", "completed", "failed", "refunded"],
                    default="pending",
                ),
                DomainField(
                    name="paid_at",
                    field_type=FieldType.DATETIME,
                    vietnamese_name="Thời gian thanh toán",
                    description="Thời điểm hoàn tất thanh toán",
                ),
            ],
            relationships=[
                DomainRelationship(
                    name="order",
                    target="Order",
                    relation_type=RelationType.ONE_TO_ONE,
                    vietnamese_name="Đơn hàng",
                    description="Thanh toán cho đơn hàng",
                ),
            ],
        )

        return DomainModule(
            name="payments",
            vietnamese_name="Quản lý thanh toán",
            description="Theo dõi thanh toán, COD, chuyển khoản",
            entities=[payment],
        )
