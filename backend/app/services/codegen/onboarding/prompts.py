"""
Vietnamese Onboarding Prompts.

Sprint 47: Vietnamese Domain Templates + Onboarding IR (EP-06)

This module provides Vietnamese language prompts for the onboarding
questionnaire flow. All prompts are designed for non-technical
SME founders who may not understand software terminology.

CGF V2.1 Integration:
- Master Processes (MP) selection
- Industry classification (ISIC)
- Scale indicators for context

Author: Backend Lead
Date: December 23, 2025
Status: ACTIVE
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class DomainOption:
    """Domain selection option with Vietnamese labels."""

    key: str  # Internal key (restaurant, hotel, retail)
    name_vi: str  # Vietnamese display name
    name_en: str  # English name
    description_vi: str  # Vietnamese description
    icon: str  # Emoji icon
    isic_codes: List[str]  # ISIC industry codes
    example_apps: List[str]  # Example app names (Vietnamese)


@dataclass
class OnboardingPrompts:
    """
    Vietnamese onboarding questionnaire prompts.

    Designed for non-technical founders:
    - Simple Vietnamese language
    - No technical jargon
    - Examples familiar to Vietnamese market
    - Emotional engagement (icons, encouragement)
    """

    # Welcome screen
    welcome_title: str
    welcome_subtitle: str
    welcome_description: str

    # Step 1: Business type
    step1_title: str
    step1_question: str
    step1_hint: str

    # Step 2: App name
    step2_title: str
    step2_question: str
    step2_placeholder: str
    step2_hint: str

    # Step 3: Features selection
    step3_title: str
    step3_question: str
    step3_hint: str

    # Step 4: Scale/size
    step4_title: str
    step4_question: str
    step4_options: Dict[str, str]  # key: Vietnamese label

    # Step 5: Confirmation
    step5_title: str
    step5_summary_label: str
    step5_confirm_button: str
    step5_edit_button: str

    # Success screen
    success_title: str
    success_message: str
    success_next_steps: List[str]

    # Error messages
    error_required_field: str
    error_invalid_name: str
    error_min_features: str

    # Navigation
    nav_next: str
    nav_previous: str
    nav_skip: str

    # Domain-specific options
    domains: Dict[str, DomainOption]


# Vietnamese prompts (primary)
VIETNAMESE_PROMPTS = OnboardingPrompts(
    # Welcome
    welcome_title="Xin chao! Tao ung dung cua ban",
    welcome_subtitle="Chi 5 phut de bat dau",
    welcome_description=(
        "Khong can biet lap trinh. Chung toi se giup ban tao mot ung dung "
        "quan ly cho doanh nghiep cua ban trong vai buoc don gian."
    ),

    # Step 1: Business type
    step1_title="Buoc 1: Loai hinh kinh doanh",
    step1_question="Ban dang kinh doanh gi?",
    step1_hint="Chon loai hinh gan nhat voi doanh nghiep cua ban",

    # Step 2: App name
    step2_title="Buoc 2: Dat ten ung dung",
    step2_question="Ban muon dat ten ung dung la gi?",
    step2_placeholder="Vi du: Quan Com Ngon, Khach San Viet...",
    step2_hint="Dung ten thuong hieu hoac ten de nho cua ban",

    # Step 3: Features
    step3_title="Buoc 3: Chon tinh nang",
    step3_question="Ung dung cua ban can nhung tinh nang nao?",
    step3_hint="Chon it nhat 2 tinh nang. Cac tinh nang co the them sau.",

    # Step 4: Scale
    step4_title="Buoc 4: Quy mo",
    step4_question="Quy mo doanh nghiep cua ban?",
    step4_options={
        "micro": "Ca nhan / 1-5 nhan vien",
        "small": "Nho / 6-20 nhan vien",
        "medium": "Vua / 21-100 nhan vien",
        "large": "Lon / Tren 100 nhan vien"
    },

    # Step 5: Confirmation
    step5_title="Buoc 5: Xac nhan",
    step5_summary_label="Thong tin ung dung cua ban:",
    step5_confirm_button="Tao ung dung",
    step5_edit_button="Chinh sua",

    # Success
    success_title="Thanh cong!",
    success_message="Ung dung cua ban da duoc tao. Bay gio ban co the:",
    success_next_steps=[
        "Xem code duoc tao ra",
        "Tai ve va chay thu",
        "Tuy chinh them tinh nang"
    ],

    # Errors
    error_required_field="Vui long dien thong tin nay",
    error_invalid_name="Ten chi duoc chua chu cai, so va dau gach",
    error_min_features="Vui long chon it nhat 2 tinh nang",

    # Navigation
    nav_next="Tiep theo",
    nav_previous="Quay lai",
    nav_skip="Bo qua",

    # Domains
    domains={
        "restaurant": DomainOption(
            key="restaurant",
            name_vi="Nha hang / Quan an",
            name_en="Restaurant / F&B",
            description_vi=(
                "Quan ly thuc don, don hang, ban, dat cho. "
                "Phu hop cho quan cafe, nha hang, quan an, bun pho..."
            ),
            icon="🍜",
            isic_codes=["56.10", "56.21", "56.29", "56.30"],
            example_apps=[
                "Quan Pho 24h",
                "Coffee House Manager",
                "Bun Bo Hue Cua",
                "Banh Mi Saigon"
            ]
        ),
        "hotel": DomainOption(
            key="hotel",
            name_vi="Khach san / Luu tru",
            name_en="Hotel / Hospitality",
            description_vi=(
                "Quan ly phong, dat phong, khach, thanh toan. "
                "Phu hop cho khach san, nha nghi, homestay, resort..."
            ),
            icon="🏨",
            isic_codes=["55.10", "55.20", "55.30", "55.90"],
            example_apps=[
                "Khach San Hai Au",
                "Homestay Dalat",
                "Resort Phu Quoc",
                "Nha Nghi Thanh Xuan"
            ]
        ),
        "retail": DomainOption(
            key="retail",
            name_vi="Ban le / Cua hang",
            name_en="Retail / Store",
            description_vi=(
                "Quan ly san pham, ton kho, ban hang, khach hang. "
                "Phu hop cho cua hang tap hoa, sieu thi mini, shop thoi trang..."
            ),
            icon="🏪",
            isic_codes=["47.11", "47.19", "47.21", "47.71"],
            example_apps=[
                "Tap Hoa Co Hai",
                "Shop Thoi Trang Miu",
                "Sieu Thi Mini 365",
                "Cua Hang Dien May"
            ]
        ),
        "ecommerce": DomainOption(
            key="ecommerce",
            name_vi="Thuong mai dien tu",
            name_en="E-commerce / Online Shop",
            description_vi=(
                "Quan ly san pham online, don hang, thanh toan, van chuyen. "
                "Phu hop cho ban hang Shopee, Tiki, Lazada, website rieng..."
            ),
            icon="🛒",
            isic_codes=["47.91", "47.99"],
            example_apps=[
                "Shop My Pham Online",
                "Trai Cay Sach Ha Noi",
                "Do Gia Dung 24h",
                "Thoi Trang Nu Sai Gon"
            ]
        ),
        "hrm": DomainOption(
            key="hrm",
            name_vi="Quan ly nhan su",
            name_en="HR Management",
            description_vi=(
                "Quan ly nhan vien, cham cong, tinh luong, nghi phep. "
                "Ho tro BHXH, BHYT, PIT theo luat Viet Nam..."
            ),
            icon="👥",
            isic_codes=["78.10", "78.20"],
            example_apps=[
                "Nhan Su ABC Corp",
                "Cham Cong Nha May XYZ",
                "HR Manager Viet",
                "Quan Ly Nhan Vien SME"
            ]
        ),
        "crm": DomainOption(
            key="crm",
            name_vi="Quan ly khach hang",
            name_en="CRM / Sales Management",
            description_vi=(
                "Quan ly khach tiem nang, lien he, giao dich, hoat dong. "
                "Tich hop Zalo, ho tro SDT Viet Nam, pipeline ban hang..."
            ),
            icon="🤝",
            isic_codes=["62.01", "62.09"],
            example_apps=[
                "Sales Pro Viet",
                "Zalo CRM Manager",
                "Pipeline Kinh Doanh",
                "Khach Hang Vang"
            ]
        ),
    }
)


# English prompts (for international users)
ENGLISH_PROMPTS = OnboardingPrompts(
    # Welcome
    welcome_title="Welcome! Create your app",
    welcome_subtitle="Just 5 minutes to get started",
    welcome_description=(
        "No coding required. We'll help you create a management app "
        "for your business in a few simple steps."
    ),

    # Step 1: Business type
    step1_title="Step 1: Business Type",
    step1_question="What type of business do you have?",
    step1_hint="Choose the type that best matches your business",

    # Step 2: App name
    step2_title="Step 2: Name Your App",
    step2_question="What would you like to name your app?",
    step2_placeholder="E.g., Tasty Restaurant, Sunny Hotel...",
    step2_hint="Use your brand name or a memorable name",

    # Step 3: Features
    step3_title="Step 3: Choose Features",
    step3_question="What features does your app need?",
    step3_hint="Select at least 2 features. You can add more later.",

    # Step 4: Scale
    step4_title="Step 4: Scale",
    step4_question="What's the size of your business?",
    step4_options={
        "micro": "Solo / 1-5 employees",
        "small": "Small / 6-20 employees",
        "medium": "Medium / 21-100 employees",
        "large": "Large / 100+ employees"
    },

    # Step 5: Confirmation
    step5_title="Step 5: Confirm",
    step5_summary_label="Your app information:",
    step5_confirm_button="Create App",
    step5_edit_button="Edit",

    # Success
    success_title="Success!",
    success_message="Your app has been created. Now you can:",
    success_next_steps=[
        "View generated code",
        "Download and run locally",
        "Customize features"
    ],

    # Errors
    error_required_field="Please fill in this field",
    error_invalid_name="Name can only contain letters, numbers, and underscores",
    error_min_features="Please select at least 2 features",

    # Navigation
    nav_next="Next",
    nav_previous="Back",
    nav_skip="Skip",

    # Domains
    domains={
        "restaurant": DomainOption(
            key="restaurant",
            name_vi="Restaurant / F&B",
            name_en="Restaurant / F&B",
            description_vi=(
                "Manage menus, orders, tables, reservations. "
                "Perfect for cafes, restaurants, food stalls..."
            ),
            icon="🍜",
            isic_codes=["56.10", "56.21", "56.29", "56.30"],
            example_apps=[
                "Pho 24h",
                "Coffee House Manager",
                "Bun Bo Hue Cua",
                "Banh Mi Saigon"
            ]
        ),
        "hotel": DomainOption(
            key="hotel",
            name_vi="Hotel / Hospitality",
            name_en="Hotel / Hospitality",
            description_vi=(
                "Manage rooms, bookings, guests, billing. "
                "Perfect for hotels, guesthouses, homestays, resorts..."
            ),
            icon="🏨",
            isic_codes=["55.10", "55.20", "55.30", "55.90"],
            example_apps=[
                "Seagull Hotel",
                "Dalat Homestay",
                "Phu Quoc Resort",
                "Thanh Xuan Guesthouse"
            ]
        ),
        "retail": DomainOption(
            key="retail",
            name_vi="Retail / Store",
            name_en="Retail / Store",
            description_vi=(
                "Manage products, inventory, sales, customers. "
                "Perfect for grocery stores, mini marts, fashion shops..."
            ),
            icon="🏪",
            isic_codes=["47.11", "47.19", "47.21", "47.71"],
            example_apps=[
                "Hai's Grocery",
                "Miu Fashion Shop",
                "365 Mini Mart",
                "Electronics Store"
            ]
        ),
    }
)


# Feature labels per domain (Vietnamese)
FEATURE_LABELS_VI = {
    "restaurant": {
        "menu": {"name": "Quan ly thuc don", "description": "Tao va sua thuc don, gia ca"},
        "orders": {"name": "Quan ly don hang", "description": "Nhan don, theo doi trang thai"},
        "tables": {"name": "Quan ly ban", "description": "So do ban, trang thai trong/ban"},
        "reservations": {"name": "Dat cho truoc", "description": "Khach dat cho qua dien thoai/online"},
        "kitchen_display": {"name": "Man hinh bep", "description": "Hien thi don cho bep"},
        "inventory": {"name": "Ton kho nguyen lieu", "description": "Theo doi nguyen lieu"},
        "reports": {"name": "Bao cao doanh thu", "description": "Thong ke theo ngay/thang"},
    },
    "hotel": {
        "rooms": {"name": "Quan ly phong", "description": "Loai phong, gia, tien nghi"},
        "bookings": {"name": "Dat phong", "description": "Dat phong online va truc tiep"},
        "guests": {"name": "Thong tin khach", "description": "Luu thong tin khach luu tru"},
        "billing": {"name": "Thanh toan", "description": "Hoa don, thanh toan"},
        "housekeeping": {"name": "Don phong", "description": "Lich don dep, kiem tra"},
        "services": {"name": "Dich vu bo sung", "description": "Spa, dua don, an uong"},
        "reports": {"name": "Bao cao", "description": "Cong suat, doanh thu"},
    },
    "retail": {
        "products": {"name": "Quan ly san pham", "description": "Danh muc, gia ban"},
        "inventory": {"name": "Quan ly ton kho", "description": "Nhap, xuat, kiem kho"},
        "sales": {"name": "Ban hang", "description": "Lap hoa don, tinh tien"},
        "customers": {"name": "Quan ly khach hang", "description": "Luu thong tin, lich su mua"},
        "suppliers": {"name": "Quan ly nha cung cap", "description": "Thong tin NCC, dat hang"},
        "promotions": {"name": "Khuyen mai", "description": "Giam gia, voucher"},
        "reports": {"name": "Bao cao", "description": "Doanh thu, loi nhuan"},
    },
    "ecommerce": {
        "products": {"name": "Quan ly san pham", "description": "Danh muc, gia ban, hinh anh"},
        "orders": {"name": "Quan ly don hang", "description": "Don hang online, trang thai van chuyen"},
        "customers": {"name": "Quan ly khach hang", "description": "Thong tin khach, lich su mua"},
        "payments": {"name": "Thanh toan", "description": "COD, chuyen khoan, MoMo, ZaloPay, VNPay"},
        "categories": {"name": "Danh muc", "description": "Phan loai san pham"},
        "shipping": {"name": "Van chuyen", "description": "Theo doi giao hang"},
        "reports": {"name": "Bao cao", "description": "Doanh thu, don hang, khach hang"},
    },
    "hrm": {
        "employees": {"name": "Quan ly nhan vien", "description": "Ho so, hop dong, phong ban"},
        "attendance": {"name": "Cham cong", "description": "Gio vao/ra, ngay cong"},
        "payroll": {"name": "Tinh luong", "description": "Luong co ban, phu cap, BHXH, thue TNCN"},
        "leave": {"name": "Nghi phep", "description": "Don nghi, duyet phep, so ngay con lai"},
        "contracts": {"name": "Hop dong lao dong", "description": "Thu viec, xac dinh, vo thoi han"},
        "departments": {"name": "Phong ban", "description": "Co cau to chuc"},
        "reports": {"name": "Bao cao", "description": "Nhan su, cham cong, luong"},
    },
    "crm": {
        "leads": {"name": "Khach tiem nang", "description": "Thu thap, phan loai, nuoi duong"},
        "contacts": {"name": "Danh ba lien he", "description": "Thong tin khach hang, doi tac"},
        "deals": {"name": "Giao dich", "description": "Pipeline ban hang, gia tri, giai doan"},
        "activities": {"name": "Hoat dong", "description": "Cuoc goi, tin nhan Zalo, gap mat"},
        "pipeline": {"name": "Pipeline", "description": "Theo doi co hoi kinh doanh"},
        "follow_ups": {"name": "Theo doi", "description": "Lich hen, nhac nho lien he lai"},
        "reports": {"name": "Bao cao", "description": "Doanh thu, ty le chuyen doi"},
    },
}


# Scale to CGF tier mapping
SCALE_TO_CGF_TIER = {
    "micro": "LITE",
    "small": "STANDARD",
    "medium": "PROFESSIONAL",
    "large": "ENTERPRISE"
}


# Scale to employee count range
SCALE_TO_EMPLOYEE_RANGE = {
    "micro": (1, 5),
    "small": (6, 20),
    "medium": (21, 100),
    "large": (101, 1000)
}
