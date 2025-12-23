"""
Base Template Classes for Codegen.

Sprint 45: Multi-Provider Codegen Architecture (EP-06)

This module provides base classes for prompt templates,
including context management and template rendering.

Author: Backend Lead
Date: December 23, 2025
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from enum import Enum
import json


class GenerationType(str, Enum):
    """Types of code generation."""
    FULL_APP = "full_app"
    MODULE = "module"
    ENTITY = "entity"
    CRUD_API = "crud_api"
    SCHEMA = "schema"
    MIGRATION = "migration"


class TemplateContext(BaseModel):
    """
    Context for template rendering.

    Contains all information needed to render a prompt template,
    including the blueprint, target, and options.
    """
    # Blueprint data
    app_name: str = Field(..., description="Application name")
    app_description: Optional[str] = Field(None, description="App description")
    blueprint_json: str = Field(..., description="Full blueprint as JSON")

    # Target specification
    generation_type: GenerationType = Field(
        GenerationType.FULL_APP,
        description="Type of generation"
    )
    target_module: Optional[str] = Field(None, description="Target module name")
    target_entity: Optional[str] = Field(None, description="Target entity name")

    # Technology stack
    language: str = Field("python", description="Target language")
    framework: str = Field("fastapi", description="Target framework")
    database: str = Field("postgresql", description="Target database")

    # Options
    include_tests: bool = Field(True, description="Generate tests")
    include_docs: bool = Field(True, description="Generate docstrings")
    vietnamese_comments: bool = Field(True, description="Use Vietnamese comments")

    # Additional context
    extra: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context data"
    )


class BaseTemplates(ABC):
    """
    Base class for framework-specific templates.

    Provides common functionality for template rendering
    and prompt generation.
    """

    # Vietnamese coding standards
    VIETNAMESE_CODING_RULES = """
## Quy tắc coding tiếng Việt
1. Comments giải thích business logic bằng tiếng Việt
2. Tên biến/hàm dùng tiếng Anh (snake_case cho Python)
3. Docstrings có thể dùng tiếng Việt cho mô tả
4. Error messages song ngữ (Việt/Anh)
5. Validation messages bằng tiếng Việt
"""

    # Output format instructions
    OUTPUT_FORMAT = """
## Output Format
Mỗi file bắt đầu bằng marker `### FILE: path/to/file.ext`
Sau đó là code trong block ``` với ngôn ngữ tương ứng.

Ví dụ:
### FILE: app/models/user.py
```python
# code here
```

### FILE: app/schemas/user.py
```python
# code here
```
"""

    @property
    @abstractmethod
    def framework_name(self) -> str:
        """Framework name (e.g., 'fastapi', 'nextjs')."""
        pass

    @property
    @abstractmethod
    def language(self) -> str:
        """Primary programming language."""
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this framework."""
        pass

    @abstractmethod
    def get_generation_prompt(self, context: TemplateContext) -> str:
        """
        Get the generation prompt for given context.

        Args:
            context: TemplateContext with blueprint and options

        Returns:
            Formatted prompt string
        """
        pass

    def get_validation_prompt(self, code: str, context: Dict[str, Any]) -> str:
        """
        Get validation prompt for code review.

        Args:
            code: Code to validate
            context: Additional context

        Returns:
            Formatted validation prompt
        """
        context_str = json.dumps(context, ensure_ascii=False, indent=2)

        return f"""Bạn là senior code reviewer với kinh nghiệm về {self.framework_name}.

## Code cần review
```{self.language}
{code[:6000]}
```

## Context
{context_str}

## Yêu cầu đánh giá
1. **Errors** (Lỗi nghiêm trọng): Bugs, security issues, logic errors
2. **Warnings** (Cảnh báo): Code smell, performance issues, best practice violations
3. **Suggestions** (Gợi ý): Improvements, refactoring opportunities

## Output Format (JSON only)
```json
{{
  "valid": true/false,
  "errors": ["Mô tả lỗi 1", "Mô tả lỗi 2"],
  "warnings": ["Cảnh báo 1"],
  "suggestions": ["Gợi ý cải thiện 1"]
}}
```

Chỉ trả về JSON, không có text khác.
"""

    def format_blueprint(self, blueprint: Dict[str, Any]) -> str:
        """
        Format blueprint for prompt inclusion.

        Args:
            blueprint: App blueprint dict

        Returns:
            Formatted JSON string
        """
        return json.dumps(blueprint, indent=2, ensure_ascii=False)

    def get_file_structure_hint(self) -> str:
        """
        Get framework-specific file structure hint.

        Returns:
            File structure description
        """
        return ""

    def get_common_patterns(self) -> str:
        """
        Get common coding patterns for this framework.

        Returns:
            Pattern descriptions
        """
        return ""
