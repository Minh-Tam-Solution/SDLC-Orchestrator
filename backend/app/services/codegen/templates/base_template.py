"""
Base Template - Abstract base class for deterministic app scaffolding

SDLC Framework Compliance:
- Framework: SDLC 5.2.0 (7-Pillar + AI Governance Principles)
- Pillar 3: Build Phase - Template-Based Code Generation
- AI Governance Principle 4: Deterministic Intermediate Representations
- Methodology: Template Method pattern for consistent scaffolding

Purpose:
Abstract base class for all app builder templates (Next.js, FastAPI, React Native, etc.)
Provides common scaffolding workflow:
1. Validate blueprint → 2. Generate file structure → 3. Populate files → 4. Return artifacts

Ensures consistency across templates while allowing framework-specific customization.

Related ADRs:
- ADR-022: IR-Based Codegen with 4-Gate Quality Pipeline
- ADR-040: App Builder Integration - Competitive Necessity

Sprint: 106 - App Builder Integration (MVP)
Date: January 28, 2026
Owner: Backend Team
Status: ACTIVE
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import logging

from backend.app.schemas.codegen.template_blueprint import (
    TemplateBlueprint,
    TemplateType,
    Entity,
    APIRoute,
    Page
)

logger = logging.getLogger(__name__)


@dataclass
class GeneratedFile:
    """
    Represents a single generated file from template scaffolding.

    Attributes:
        path: Relative file path (e.g., "src/pages/index.tsx")
        content: File content as string
        language: Programming language for syntax highlighting
        is_binary: True if file is binary (images, fonts, etc.)
    """
    path: str
    content: str
    language: str = "text"
    is_binary: bool = False

    def __post_init__(self):
        """Auto-detect language from file extension if not provided"""
        if self.language == "text" and not self.is_binary:
            ext_map = {
                '.py': 'python',
                '.ts': 'typescript',
                '.tsx': 'typescriptreact',
                '.js': 'javascript',
                '.jsx': 'javascriptreact',
                '.json': 'json',
                '.md': 'markdown',
                '.yml': 'yaml',
                '.yaml': 'yaml',
                '.toml': 'toml',
                '.env': 'dotenv',
                '.sql': 'sql',
                '.sh': 'bash',
            }
            ext = Path(self.path).suffix
            self.language = ext_map.get(ext, 'text')


class BaseTemplate(ABC):
    """
    Abstract base class for app scaffolding templates.

    Template Method Pattern:
    1. validate_blueprint() → Check blueprint completeness
    2. get_file_structure() → Define directory structure
    3. generate_base_files() → Create common files (README, .gitignore, etc.)
    4. generate_framework_files() → Create framework-specific files
    5. generate_entity_files() → Create entity/model files
    6. generate_route_files() → Create API route files
    7. generate_page_files() → Create frontend page files

    Subclasses implement framework-specific logic while base class orchestrates.
    """

    # Template metadata
    template_type: TemplateType
    template_name: str
    template_version: str = "1.0.0"

    # Tech stack defaults
    default_tech_stack: List[str] = []
    required_env_vars: List[str] = []

    def __init__(self):
        """Initialize template with default configuration"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def get_file_structure(self, blueprint: TemplateBlueprint) -> Dict[str, str]:
        """
        Define directory structure for this template.

        Args:
            blueprint: Template blueprint with project specification

        Returns:
            Dict mapping directory paths to descriptions
            Example: {"src/": "Source code", "src/components/": "React components"}
        """
        pass

    @abstractmethod
    def generate_config_files(self, blueprint: TemplateBlueprint) -> List[GeneratedFile]:
        """
        Generate framework configuration files.

        Examples:
        - Next.js: package.json, next.config.js, tsconfig.json
        - FastAPI: pyproject.toml, setup.py, requirements.txt
        - React Native: package.json, app.json, metro.config.js

        Args:
            blueprint: Template blueprint

        Returns:
            List of configuration files
        """
        pass

    @abstractmethod
    def generate_entry_point(self, blueprint: TemplateBlueprint) -> List[GeneratedFile]:
        """
        Generate application entry point files.

        Examples:
        - Next.js: pages/_app.tsx, pages/index.tsx
        - FastAPI: main.py
        - React Native: App.tsx

        Args:
            blueprint: Template blueprint

        Returns:
            List of entry point files
        """
        pass

    def scaffold(self, blueprint: TemplateBlueprint) -> List[GeneratedFile]:
        """
        Main scaffolding workflow (Template Method).

        Orchestrates the complete scaffolding process:
        1. Validate blueprint
        2. Generate base files (README, .gitignore, LICENSE)
        3. Generate framework config files
        4. Generate entry point
        5. Generate entities/models (if applicable)
        6. Generate API routes (if applicable)
        7. Generate pages (if applicable)

        Args:
            blueprint: Validated and finalized template blueprint

        Returns:
            List of all generated files

        Raises:
            ValueError: If blueprint validation fails
        """
        self.logger.info(f"Starting scaffold for {blueprint.project_name} with {self.template_name}")

        # Step 1: Validate blueprint
        self.validate_blueprint(blueprint)

        # Step 2: Collect all files
        files: List[GeneratedFile] = []

        # Base files (common to all templates)
        files.extend(self.generate_base_files(blueprint))

        # Framework-specific files
        files.extend(self.generate_config_files(blueprint))
        files.extend(self.generate_entry_point(blueprint))

        # Entity/Model files (if entities defined)
        if blueprint.entities:
            files.extend(self.generate_entity_files(blueprint))

        # API route files (if routes defined)
        if blueprint.api_routes:
            files.extend(self.generate_route_files(blueprint))

        # Frontend page files (if pages defined)
        if blueprint.pages:
            files.extend(self.generate_page_files(blueprint))

        self.logger.info(f"Scaffold complete: {len(files)} files generated")

        return files

    def validate_blueprint(self, blueprint: TemplateBlueprint) -> None:
        """
        Validate blueprint completeness for this template.

        Args:
            blueprint: Template blueprint to validate

        Raises:
            ValueError: If blueprint is invalid for this template
        """
        # Check template type matches
        if blueprint.template_type != self.template_type:
            raise ValueError(
                f"Blueprint template type {blueprint.template_type} "
                f"does not match {self.template_type}"
            )

        # Check required tech stack
        if self.default_tech_stack:
            missing = [
                tech for tech in self.default_tech_stack
                if tech not in blueprint.tech_stack
            ]
            if missing:
                self.logger.warning(
                    f"Missing recommended tech stack: {', '.join(missing)}"
                )

        # Verify integrity hash
        if not blueprint.verify_integrity():
            raise ValueError(
                f"Blueprint integrity check failed for {blueprint.blueprint_id}"
            )

        self.logger.debug(f"Blueprint validation passed for {blueprint.project_name}")

    def generate_base_files(self, blueprint: TemplateBlueprint) -> List[GeneratedFile]:
        """
        Generate base files common to all templates.

        Files:
        - README.md: Project documentation
        - .gitignore: Git ignore patterns
        - .env.example: Environment variable template
        - LICENSE: MIT License (default)

        Args:
            blueprint: Template blueprint

        Returns:
            List of base files
        """
        files = []

        # README.md
        files.append(GeneratedFile(
            path="README.md",
            content=self._generate_readme(blueprint),
            language="markdown"
        ))

        # .gitignore
        files.append(GeneratedFile(
            path=".gitignore",
            content=self._generate_gitignore(blueprint),
            language="text"
        ))

        # .env.example
        if blueprint.env_vars:
            files.append(GeneratedFile(
                path=".env.example",
                content=self._generate_env_example(blueprint),
                language="dotenv"
            ))

        return files

    def generate_entity_files(self, blueprint: TemplateBlueprint) -> List[GeneratedFile]:
        """
        Generate entity/model files.

        Default implementation returns empty list.
        Override in subclass for backend frameworks (FastAPI, Express).

        Args:
            blueprint: Template blueprint

        Returns:
            List of entity files
        """
        return []

    def generate_route_files(self, blueprint: TemplateBlueprint) -> List[GeneratedFile]:
        """
        Generate API route files.

        Default implementation returns empty list.
        Override in subclass for API frameworks (Next.js, FastAPI, Express).

        Args:
            blueprint: Template blueprint

        Returns:
            List of route files
        """
        return []

    def generate_page_files(self, blueprint: TemplateBlueprint) -> List[GeneratedFile]:
        """
        Generate frontend page files.

        Default implementation returns empty list.
        Override in subclass for frontend frameworks (Next.js, React Native, Nuxt).

        Args:
            blueprint: Template blueprint

        Returns:
            List of page files
        """
        return []

    # Helper methods for base file generation

    def _generate_readme(self, blueprint: TemplateBlueprint) -> str:
        """Generate README.md content"""
        tech_stack_list = "\n".join([f"- {tech}" for tech in blueprint.tech_stack])
        features_list = "\n".join([f"- {feat}" for feat in blueprint.features]) if blueprint.features else "- Basic scaffolding"

        return f"""# {blueprint.project_name}

Generated with SDLC Orchestrator App Builder

## Tech Stack

{tech_stack_list}

## Features

{features_list}

## Getting Started

1. Install dependencies:
```bash
# See package.json or requirements.txt for dependency installation
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run development server:
```bash
# See package.json scripts for available commands
```

## Project Structure

Generated using template: **{self.template_name}** (v{self.template_version})

## License

MIT License - See LICENSE file for details

---

Built with ❤️ using SDLC Orchestrator
"""

    def _generate_gitignore(self, blueprint: TemplateBlueprint) -> str:
        """Generate .gitignore content"""
        # Common patterns for all templates
        base_patterns = [
            "# Dependencies",
            "node_modules/",
            "__pycache__/",
            "*.pyc",
            ".pytest_cache/",
            "",
            "# Environment variables",
            ".env",
            ".env.local",
            ".env.*.local",
            "",
            "# IDE",
            ".vscode/",
            ".idea/",
            "*.swp",
            "*.swo",
            ".DS_Store",
            "",
            "# Build outputs",
            "dist/",
            "build/",
            ".next/",
            "out/",
            "*.egg-info/",
            "",
            "# Logs",
            "*.log",
            "logs/",
            "",
            "# Testing",
            "coverage/",
            ".coverage",
            "*.cover",
        ]

        return "\n".join(base_patterns)

    def _generate_env_example(self, blueprint: TemplateBlueprint) -> str:
        """Generate .env.example content"""
        lines = ["# Environment Variables\n"]

        for var in blueprint.env_vars:
            lines.append(f"{var}=")

        return "\n".join(lines)

    def get_smoke_test_command(self) -> str:
        """
        Get smoke test command for this template.

        Used by Quality Gate 4 (Smoke Test) to verify scaffolded project.

        Returns:
            Shell command to run smoke test
        """
        return "echo 'No smoke test defined'"
