# Vietnamese Domain Templates Specification
## EP-06: Onboarding → IR Builder | Sprint 47

**Status**: APPROVED
**Version**: 1.0.0
**Date**: December 23, 2025
**Author**: Backend Lead + Product
**Sprint**: Sprint 47 (Feb 3-14, 2026)
**Framework**: SDLC 6.1.0
**Dependency**: Sprint 46 (IR Processors)

---

## 1. Overview

### 1.1 Purpose

This specification defines the Vietnamese Domain Templates system and Onboarding → IR Builder that enables non-tech Vietnam SME founders to generate valid AppBlueprint through guided Vietnamese questionnaires.

### 1.2 Strategic Context

**Founder Plan Validation**: $99/team/month for Vietnam SME
- Target: 25 Vietnam SME teams Year 1
- TTFV (Time to First Value): <30 minutes
- Domain focus: F&B, Hospitality, Retail

```
┌─────────────────────────────────────────────────────────────────────┐
│                    VIETNAMESE FOUNDER JOURNEY                        │
│                                                                      │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐       │
│  │ Chọn     │ →  │ Trả lời  │ →  │ Xem      │ →  │ Tạo      │       │
│  │ ngành    │    │ câu hỏi  │    │ preview  │    │ ứng dụng │       │
│  │ (Domain) │    │ (Survey) │    │ (IR)     │    │ (Code)   │       │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘       │
│       ↓               ↓               ↓               ↓              │
│   3 domains      Vietnamese       AppBlueprint     Generated         │
│   templates      questions        JSON             Backend           │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.3 Scope

| In Scope | Out of Scope |
|----------|--------------|
| 3 domain templates (F&B, Hotel, Retail) | Voice input |
| Vietnamese questionnaire flow | Complex UI customization |
| IR builder (answers → AppBlueprint) | Multi-tenant packaging |
| Minimal frontend preview | Payment integration |

---

## 2. Domain Templates

### 2.1 F&B (Nhà hàng / Quán ăn)

**Target Users**: Restaurant, cafe, food stall owners

```yaml
domain: restaurant
vietnamese_name: "Nhà hàng / Quán ăn"
icon: "🍜"

modules:
  - name: menu
    vietnamese_name: "Thực đơn"
    entities:
      - name: Category
        vietnamese_name: "Danh mục"
        fields:
          - name: name
            vietnamese_label: "Tên danh mục"
            type: string
            required: true
            example: "Món chính"
          - name: description
            vietnamese_label: "Mô tả"
            type: text
          - name: display_order
            vietnamese_label: "Thứ tự hiển thị"
            type: integer
            default: 0

      - name: MenuItem
        vietnamese_name: "Món ăn"
        fields:
          - name: name
            vietnamese_label: "Tên món"
            type: string
            required: true
            example: "Phở bò"
          - name: price
            vietnamese_label: "Giá (VND)"
            type: integer
            required: true
          - name: description
            vietnamese_label: "Mô tả"
            type: text
          - name: image_url
            vietnamese_label: "Hình ảnh"
            type: string
          - name: available
            vietnamese_label: "Còn món"
            type: boolean
            default: true

  - name: orders
    vietnamese_name: "Đơn hàng"
    entities:
      - name: Order
        vietnamese_name: "Đơn hàng"
        fields:
          - name: table_number
            vietnamese_label: "Số bàn"
            type: integer
          - name: customer_name
            vietnamese_label: "Tên khách"
            type: string
          - name: status
            vietnamese_label: "Trạng thái"
            type: string
            enum: ["pending", "preparing", "ready", "delivered", "paid"]
            default: "pending"
          - name: total_amount
            vietnamese_label: "Tổng tiền"
            type: integer
          - name: notes
            vietnamese_label: "Ghi chú"
            type: text

      - name: OrderItem
        vietnamese_name: "Chi tiết đơn"
        fields:
          - name: quantity
            vietnamese_label: "Số lượng"
            type: integer
            required: true
          - name: unit_price
            vietnamese_label: "Đơn giá"
            type: integer
          - name: notes
            vietnamese_label: "Ghi chú"
            type: text

  - name: tables
    vietnamese_name: "Quản lý bàn"
    entities:
      - name: Table
        vietnamese_name: "Bàn"
        fields:
          - name: number
            vietnamese_label: "Số bàn"
            type: integer
            required: true
            unique: true
          - name: capacity
            vietnamese_label: "Số ghế"
            type: integer
            default: 4
          - name: status
            vietnamese_label: "Trạng thái"
            type: string
            enum: ["available", "occupied", "reserved"]
            default: "available"
          - name: location
            vietnamese_label: "Vị trí"
            type: string
            example: "Tầng 1"

questions:
  - id: business_name
    vietnamese: "Tên nhà hàng/quán của bạn là gì?"
    field: app_name
    required: true
    example: "Phở Hà Nội"

  - id: business_type
    vietnamese: "Loại hình kinh doanh?"
    type: select
    options:
      - value: "restaurant"
        label: "Nhà hàng"
      - value: "cafe"
        label: "Quán cà phê"
      - value: "food_stall"
        label: "Quán ăn nhỏ"

  - id: has_tables
    vietnamese: "Quán có bàn ghế cho khách ngồi không?"
    type: boolean
    affects_modules: ["tables"]

  - id: menu_categories
    vietnamese: "Bạn có những danh mục món nào? (VD: Món chính, Món phụ, Đồ uống)"
    type: text_array
    example: ["Món chính", "Món phụ", "Đồ uống", "Tráng miệng"]

  - id: needs_reservation
    vietnamese: "Khách có cần đặt bàn trước không?"
    type: boolean
    affects_modules: ["reservations"]
```

### 2.2 Hospitality (Khách sạn / Homestay)

**Target Users**: Hotel, homestay, guesthouse owners

```yaml
domain: hotel
vietnamese_name: "Khách sạn / Homestay"
icon: "🏨"

modules:
  - name: rooms
    vietnamese_name: "Quản lý phòng"
    entities:
      - name: RoomType
        vietnamese_name: "Loại phòng"
        fields:
          - name: name
            vietnamese_label: "Tên loại phòng"
            type: string
            required: true
            example: "Phòng đôi"
          - name: description
            vietnamese_label: "Mô tả"
            type: text
          - name: base_price
            vietnamese_label: "Giá cơ bản (VND/đêm)"
            type: integer
            required: true
          - name: capacity
            vietnamese_label: "Số khách tối đa"
            type: integer
            default: 2
          - name: amenities
            vietnamese_label: "Tiện nghi"
            type: json

      - name: Room
        vietnamese_name: "Phòng"
        fields:
          - name: room_number
            vietnamese_label: "Số phòng"
            type: string
            required: true
            unique: true
          - name: floor
            vietnamese_label: "Tầng"
            type: integer
          - name: status
            vietnamese_label: "Trạng thái"
            type: string
            enum: ["available", "occupied", "maintenance", "cleaning"]
            default: "available"

  - name: bookings
    vietnamese_name: "Đặt phòng"
    entities:
      - name: Booking
        vietnamese_name: "Đặt phòng"
        fields:
          - name: guest_name
            vietnamese_label: "Tên khách"
            type: string
            required: true
          - name: guest_phone
            vietnamese_label: "Số điện thoại"
            type: string
            required: true
          - name: guest_email
            vietnamese_label: "Email"
            type: string
          - name: check_in_date
            vietnamese_label: "Ngày nhận phòng"
            type: date
            required: true
          - name: check_out_date
            vietnamese_label: "Ngày trả phòng"
            type: date
            required: true
          - name: num_guests
            vietnamese_label: "Số khách"
            type: integer
            default: 1
          - name: status
            vietnamese_label: "Trạng thái"
            type: string
            enum: ["pending", "confirmed", "checked_in", "checked_out", "cancelled"]
          - name: total_amount
            vietnamese_label: "Tổng tiền"
            type: integer
          - name: notes
            vietnamese_label: "Ghi chú"
            type: text

  - name: guests
    vietnamese_name: "Khách hàng"
    entities:
      - name: Guest
        vietnamese_name: "Khách"
        fields:
          - name: name
            vietnamese_label: "Họ tên"
            type: string
            required: true
          - name: phone
            vietnamese_label: "Số điện thoại"
            type: string
          - name: email
            vietnamese_label: "Email"
            type: string
          - name: id_number
            vietnamese_label: "CCCD/CMND"
            type: string
          - name: nationality
            vietnamese_label: "Quốc tịch"
            type: string
            default: "Việt Nam"

questions:
  - id: business_name
    vietnamese: "Tên khách sạn/homestay của bạn?"
    field: app_name
    required: true

  - id: business_type
    vietnamese: "Loại hình lưu trú?"
    type: select
    options:
      - value: "hotel"
        label: "Khách sạn"
      - value: "homestay"
        label: "Homestay"
      - value: "guesthouse"
        label: "Nhà nghỉ"

  - id: room_types
    vietnamese: "Bạn có những loại phòng nào?"
    type: text_array
    example: ["Phòng đơn", "Phòng đôi", "Phòng gia đình"]

  - id: total_rooms
    vietnamese: "Tổng số phòng?"
    type: integer
```

### 2.3 Retail (Cửa hàng bán lẻ)

**Target Users**: Shop, store, small retail business owners

```yaml
domain: retail
vietnamese_name: "Cửa hàng bán lẻ"
icon: "🏪"

modules:
  - name: products
    vietnamese_name: "Sản phẩm"
    entities:
      - name: Category
        vietnamese_name: "Danh mục"
        fields:
          - name: name
            vietnamese_label: "Tên danh mục"
            type: string
            required: true
          - name: description
            vietnamese_label: "Mô tả"
            type: text

      - name: Product
        vietnamese_name: "Sản phẩm"
        fields:
          - name: name
            vietnamese_label: "Tên sản phẩm"
            type: string
            required: true
          - name: sku
            vietnamese_label: "Mã sản phẩm"
            type: string
            unique: true
          - name: price
            vietnamese_label: "Giá bán (VND)"
            type: integer
            required: true
          - name: cost_price
            vietnamese_label: "Giá vốn"
            type: integer
          - name: description
            vietnamese_label: "Mô tả"
            type: text
          - name: image_url
            vietnamese_label: "Hình ảnh"
            type: string

  - name: inventory
    vietnamese_name: "Kho hàng"
    entities:
      - name: Stock
        vietnamese_name: "Tồn kho"
        fields:
          - name: quantity
            vietnamese_label: "Số lượng"
            type: integer
            default: 0
          - name: min_quantity
            vietnamese_label: "Số lượng tối thiểu"
            type: integer
            default: 5
          - name: location
            vietnamese_label: "Vị trí kho"
            type: string

  - name: sales
    vietnamese_name: "Bán hàng"
    entities:
      - name: Sale
        vietnamese_name: "Hóa đơn"
        fields:
          - name: customer_name
            vietnamese_label: "Tên khách"
            type: string
          - name: customer_phone
            vietnamese_label: "SĐT khách"
            type: string
          - name: total_amount
            vietnamese_label: "Tổng tiền"
            type: integer
          - name: discount
            vietnamese_label: "Giảm giá"
            type: integer
            default: 0
          - name: payment_method
            vietnamese_label: "Phương thức thanh toán"
            type: string
            enum: ["cash", "transfer", "card"]
          - name: status
            vietnamese_label: "Trạng thái"
            type: string
            enum: ["pending", "completed", "refunded"]

      - name: SaleItem
        vietnamese_name: "Chi tiết hóa đơn"
        fields:
          - name: quantity
            vietnamese_label: "Số lượng"
            type: integer
            required: true
          - name: unit_price
            vietnamese_label: "Đơn giá"
            type: integer

  - name: customers
    vietnamese_name: "Khách hàng"
    entities:
      - name: Customer
        vietnamese_name: "Khách hàng"
        fields:
          - name: name
            vietnamese_label: "Họ tên"
            type: string
            required: true
          - name: phone
            vietnamese_label: "Số điện thoại"
            type: string
          - name: email
            vietnamese_label: "Email"
            type: string
          - name: address
            vietnamese_label: "Địa chỉ"
            type: text
          - name: points
            vietnamese_label: "Điểm tích lũy"
            type: integer
            default: 0

questions:
  - id: business_name
    vietnamese: "Tên cửa hàng của bạn?"
    field: app_name
    required: true

  - id: business_type
    vietnamese: "Bạn bán loại hàng gì?"
    type: select
    options:
      - value: "fashion"
        label: "Thời trang"
      - value: "electronics"
        label: "Điện tử"
      - value: "grocery"
        label: "Tạp hóa"
      - value: "cosmetics"
        label: "Mỹ phẩm"
      - value: "other"
        label: "Khác"

  - id: has_inventory
    vietnamese: "Bạn có cần quản lý tồn kho không?"
    type: boolean
    affects_modules: ["inventory"]

  - id: has_customer_loyalty
    vietnamese: "Bạn có chương trình tích điểm khách hàng không?"
    type: boolean
    affects_modules: ["customers"]
```

---

## 3. Onboarding Flow Architecture

### 3.1 Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ONBOARDING FLOW                                   │
│                                                                      │
│  Step 1: Domain Selection                                            │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  🍜 Nhà hàng    🏨 Khách sạn    🏪 Cửa hàng                  │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              ↓                                       │
│  Step 2: Vietnamese Questionnaire (5-10 questions)                  │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Q1: Tên nhà hàng của bạn là gì? [_____________]            │    │
│  │  Q2: Quán có bàn ghế cho khách ngồi không? [Có] [Không]     │    │
│  │  Q3: Danh mục món ăn? [Thêm danh mục...]                    │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              ↓                                       │
│  Step 3: IR Preview                                                  │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  AppBlueprint Preview:                                       │    │
│  │  - Tên: Phở Hà Nội                                           │    │
│  │  - Modules: Thực đơn, Đơn hàng, Quản lý bàn                  │    │
│  │  - Entities: Category, MenuItem, Order, Table...             │    │
│  │  [Chỉnh sửa] [Tiếp tục]                                      │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              ↓                                       │
│  Step 4: Generate                                                    │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Đang tạo ứng dụng... ████████░░ 80%                        │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/onboarding/domains` | List available domains |
| `GET` | `/api/v1/onboarding/domains/{domain}/questions` | Get questions for domain |
| `POST` | `/api/v1/onboarding/generate-ir` | Generate IR from answers |
| `POST` | `/api/v1/onboarding/preview` | Preview generated IR |

### 3.3 Data Models

```python
# backend/app/schemas/onboarding.py

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from enum import Enum

class DomainType(str, Enum):
    RESTAURANT = "restaurant"
    HOTEL = "hotel"
    RETAIL = "retail"

class QuestionType(str, Enum):
    TEXT = "text"
    TEXT_ARRAY = "text_array"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    BOOLEAN = "boolean"
    INTEGER = "integer"

class QuestionOption(BaseModel):
    value: str
    label: str

class OnboardingQuestion(BaseModel):
    id: str
    vietnamese: str
    english: Optional[str] = None
    type: QuestionType = QuestionType.TEXT
    required: bool = False
    options: Optional[List[QuestionOption]] = None
    example: Optional[str] = None
    affects_modules: Optional[List[str]] = None

class DomainTemplate(BaseModel):
    domain: DomainType
    vietnamese_name: str
    icon: str
    description: str
    questions: List[OnboardingQuestion]
    default_modules: List[str]

class OnboardingAnswer(BaseModel):
    question_id: str
    value: Any

class OnboardingSubmission(BaseModel):
    domain: DomainType
    answers: List[OnboardingAnswer]

class IRPreview(BaseModel):
    app_name: str
    domain: str
    modules: List[Dict[str, Any]]
    entity_count: int
    field_count: int
    estimated_endpoints: int
```

---

## 4. IR Builder Logic

### 4.1 Answer → IR Transformer

```python
# backend/app/services/codegen/ir/ir_builder.py

from typing import Dict, Any, List
from app.schemas.onboarding import (
    DomainType, OnboardingSubmission, OnboardingAnswer
)
import yaml
from pathlib import Path

class IRBuilder:
    """Builds AppBlueprint from onboarding answers."""

    def __init__(self, template_dir: Path):
        self.template_dir = template_dir
        self._templates: Dict[DomainType, Dict] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """Load domain templates from YAML files."""
        for domain in DomainType:
            path = self.template_dir / f"{domain.value}.yaml"
            if path.exists():
                with open(path) as f:
                    self._templates[domain] = yaml.safe_load(f)

    def build(self, submission: OnboardingSubmission) -> Dict[str, Any]:
        """
        Build AppBlueprint from submission.

        Args:
            submission: OnboardingSubmission with domain and answers

        Returns:
            Valid AppBlueprint JSON
        """
        template = self._templates.get(submission.domain)
        if not template:
            raise ValueError(f"Unknown domain: {submission.domain}")

        # Extract answers by ID
        answers = {a.question_id: a.value for a in submission.answers}

        # Build base blueprint
        blueprint = {
            "name": answers.get("business_name", "My App"),
            "version": "1.0.0",
            "business_domain": submission.domain.value,
            "modules": []
        }

        # Filter modules based on boolean answers
        active_modules = self._filter_modules(template, answers)

        # Build modules with entities
        for module_def in template.get("modules", []):
            if module_def["name"] in active_modules:
                module = self._build_module(module_def, answers)
                blueprint["modules"].append(module)

        # Add custom data from answers
        blueprint = self._apply_custom_answers(blueprint, answers, template)

        return blueprint

    def _filter_modules(
        self,
        template: Dict,
        answers: Dict[str, Any]
    ) -> List[str]:
        """Filter modules based on boolean question answers."""
        active = []

        # Start with default modules
        for module in template.get("modules", []):
            active.append(module["name"])

        # Check questions that affect modules
        for question in template.get("questions", []):
            if "affects_modules" in question:
                answer = answers.get(question["id"])
                if answer is False:
                    # Remove affected modules
                    for mod in question["affects_modules"]:
                        if mod in active:
                            active.remove(mod)

        return active

    def _build_module(
        self,
        module_def: Dict,
        answers: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build a module from template definition."""
        module = {
            "name": module_def["name"],
            "entities": [],
            "operations": module_def.get("operations", [
                "create", "read", "update", "delete", "list"
            ])
        }

        for entity_def in module_def.get("entities", []):
            entity = self._build_entity(entity_def)
            module["entities"].append(entity)

        return module

    def _build_entity(self, entity_def: Dict) -> Dict[str, Any]:
        """Build an entity from template definition."""
        entity = {
            "name": entity_def["name"],
            "fields": []
        }

        for field_def in entity_def.get("fields", []):
            field = {
                "name": field_def["name"],
                "type": field_def["type"],
                "required": field_def.get("required", False)
            }

            if "default" in field_def:
                field["default"] = field_def["default"]
            if "max_length" in field_def:
                field["max_length"] = field_def["max_length"]
            if "unique" in field_def:
                field["unique"] = field_def["unique"]

            entity["fields"].append(field)

        return entity

    def _apply_custom_answers(
        self,
        blueprint: Dict,
        answers: Dict[str, Any],
        template: Dict
    ) -> Dict[str, Any]:
        """Apply custom answers to blueprint."""

        # Handle menu_categories for restaurant
        if "menu_categories" in answers:
            categories = answers["menu_categories"]
            if isinstance(categories, list) and categories:
                # Add predefined categories to the blueprint
                blueprint["_custom"] = {
                    "seed_data": {
                        "categories": categories
                    }
                }

        # Handle room_types for hotel
        if "room_types" in answers:
            room_types = answers["room_types"]
            if isinstance(room_types, list) and room_types:
                blueprint["_custom"] = blueprint.get("_custom", {})
                blueprint["_custom"]["seed_data"] = blueprint["_custom"].get("seed_data", {})
                blueprint["_custom"]["seed_data"]["room_types"] = room_types

        return blueprint
```

### 4.2 API Routes

```python
# backend/app/api/routes/onboarding.py

from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas.onboarding import (
    DomainType, DomainTemplate, OnboardingQuestion,
    OnboardingSubmission, IRPreview
)
from app.services.codegen.ir.ir_builder import IRBuilder
from app.core.config import settings

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

ir_builder = IRBuilder(settings.DOMAIN_TEMPLATE_DIR)


@router.get("/domains", response_model=List[dict])
async def list_domains():
    """List available domain templates."""
    return [
        {
            "domain": "restaurant",
            "vietnamese_name": "Nhà hàng / Quán ăn",
            "icon": "🍜",
            "description": "Quản lý thực đơn, đơn hàng, bàn"
        },
        {
            "domain": "hotel",
            "vietnamese_name": "Khách sạn / Homestay",
            "icon": "🏨",
            "description": "Quản lý phòng, đặt phòng, khách"
        },
        {
            "domain": "retail",
            "vietnamese_name": "Cửa hàng bán lẻ",
            "icon": "🏪",
            "description": "Quản lý sản phẩm, kho, bán hàng"
        }
    ]


@router.get("/domains/{domain}/questions", response_model=List[OnboardingQuestion])
async def get_domain_questions(domain: DomainType):
    """Get onboarding questions for a domain."""
    questions = ir_builder.get_questions(domain)
    if not questions:
        raise HTTPException(status_code=404, detail="Domain not found")
    return questions


@router.post("/generate-ir")
async def generate_ir(submission: OnboardingSubmission):
    """Generate AppBlueprint from onboarding answers."""
    try:
        blueprint = ir_builder.build(submission)
        return {
            "success": True,
            "app_blueprint": blueprint
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/preview", response_model=IRPreview)
async def preview_ir(submission: OnboardingSubmission):
    """Preview generated IR without full generation."""
    try:
        blueprint = ir_builder.build(submission)

        # Calculate stats
        entity_count = sum(
            len(m.get("entities", []))
            for m in blueprint.get("modules", [])
        )
        field_count = sum(
            len(e.get("fields", []))
            for m in blueprint.get("modules", [])
            for e in m.get("entities", [])
        )

        return IRPreview(
            app_name=blueprint["name"],
            domain=blueprint["business_domain"],
            modules=blueprint["modules"],
            entity_count=entity_count,
            field_count=field_count,
            estimated_endpoints=entity_count * 5  # CRUD + list
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

## 5. Frontend Components

### 5.1 Onboarding Wizard

```typescript
// frontend/web/src/components/onboarding/OnboardingWizard.tsx

import React, { useState } from 'react';
import { DomainSelector } from './DomainSelector';
import { QuestionForm } from './QuestionForm';
import { IRPreview } from './IRPreview';
import { GenerationProgress } from './GenerationProgress';

type Step = 'domain' | 'questions' | 'preview' | 'generate';

interface OnboardingWizardProps {
  onComplete: (blueprint: any) => void;
}

export function OnboardingWizard({ onComplete }: OnboardingWizardProps) {
  const [step, setStep] = useState<Step>('domain');
  const [domain, setDomain] = useState<string | null>(null);
  const [answers, setAnswers] = useState<Record<string, any>>({});
  const [blueprint, setBlueprint] = useState<any>(null);

  const handleDomainSelect = (selectedDomain: string) => {
    setDomain(selectedDomain);
    setStep('questions');
  };

  const handleAnswersSubmit = async (submittedAnswers: Record<string, any>) => {
    setAnswers(submittedAnswers);

    // Generate preview
    const response = await fetch('/api/v1/onboarding/preview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        domain,
        answers: Object.entries(submittedAnswers).map(([id, value]) => ({
          question_id: id,
          value
        }))
      })
    });

    const preview = await response.json();
    setBlueprint(preview);
    setStep('preview');
  };

  const handleConfirm = async () => {
    setStep('generate');
    // Trigger full generation
    const response = await fetch('/api/v1/onboarding/generate-ir', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        domain,
        answers: Object.entries(answers).map(([id, value]) => ({
          question_id: id,
          value
        }))
      })
    });

    const result = await response.json();
    onComplete(result.app_blueprint);
  };

  return (
    <div className="onboarding-wizard">
      {step === 'domain' && (
        <DomainSelector onSelect={handleDomainSelect} />
      )}
      {step === 'questions' && domain && (
        <QuestionForm
          domain={domain}
          onSubmit={handleAnswersSubmit}
          onBack={() => setStep('domain')}
        />
      )}
      {step === 'preview' && blueprint && (
        <IRPreview
          preview={blueprint}
          onConfirm={handleConfirm}
          onEdit={() => setStep('questions')}
        />
      )}
      {step === 'generate' && (
        <GenerationProgress />
      )}
    </div>
  );
}
```

### 5.2 Domain Selector

```typescript
// frontend/web/src/components/onboarding/DomainSelector.tsx

import React from 'react';

interface Domain {
  domain: string;
  vietnamese_name: string;
  icon: string;
  description: string;
}

const DOMAINS: Domain[] = [
  {
    domain: 'restaurant',
    vietnamese_name: 'Nhà hàng / Quán ăn',
    icon: '🍜',
    description: 'Quản lý thực đơn, đơn hàng, bàn'
  },
  {
    domain: 'hotel',
    vietnamese_name: 'Khách sạn / Homestay',
    icon: '🏨',
    description: 'Quản lý phòng, đặt phòng, khách'
  },
  {
    domain: 'retail',
    vietnamese_name: 'Cửa hàng bán lẻ',
    icon: '🏪',
    description: 'Quản lý sản phẩm, kho, bán hàng'
  }
];

interface DomainSelectorProps {
  onSelect: (domain: string) => void;
}

export function DomainSelector({ onSelect }: DomainSelectorProps) {
  return (
    <div className="domain-selector">
      <h2 className="text-2xl font-bold mb-6">
        Bạn muốn tạo ứng dụng cho ngành nào?
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {DOMAINS.map((domain) => (
          <button
            key={domain.domain}
            onClick={() => onSelect(domain.domain)}
            className="domain-card p-6 border rounded-lg hover:border-primary hover:shadow-lg transition-all"
          >
            <div className="text-4xl mb-4">{domain.icon}</div>
            <h3 className="text-lg font-semibold">{domain.vietnamese_name}</h3>
            <p className="text-sm text-gray-600 mt-2">{domain.description}</p>
          </button>
        ))}
      </div>
    </div>
  );
}
```

---

## 6. Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| IR validity | 95%+ sessions produce valid AppBlueprint | Automated test |
| Founder usability | Vietnamese flow understandable without help | Pilot feedback |
| Time to IR | <10 minutes from start to valid IR | User timing |
| Template coverage | 3 domains with 3+ modules each | Feature count |

---

## 7. Sprint 47 Implementation Checklist

### Week 1 (Feb 3-7)

- [ ] Create domain template YAML files (F&B, Hotel, Retail)
- [ ] Implement IRBuilder class
- [ ] Create onboarding API endpoints
- [ ] Write unit tests for IR generation
- [ ] Validate generated IR against schemas

### Week 2 (Feb 10-14)

- [ ] Create frontend OnboardingWizard component
- [ ] Implement DomainSelector, QuestionForm, IRPreview
- [ ] Connect frontend to onboarding API
- [ ] User testing with 3-5 Vietnamese founders
- [ ] Iterate based on feedback

---

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Date** | December 23, 2025 |
| **Author** | Backend Lead + Product |
| **Status** | APPROVED |
| **Sprint** | Sprint 47 (Feb 3-14, 2026) |
| **Dependency** | Sprint 46 |
