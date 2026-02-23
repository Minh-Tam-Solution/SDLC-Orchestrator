"""
Endpoint Processor - Generates CRUD API endpoints and services.

Sprint 46: EP-06 IR-Based Backend Scaffold Generation
ADR-023: IR-Based Deterministic Code Generation

Generates API layer code from module specifications:
- FastAPI route handlers (CRUD endpoints)
- Service classes with business logic
- API router registration

Supported Operations:
- create: POST /{entities}
- list: GET /{entities}
- read: GET /{entities}/{id}
- update: PATCH /{entities}/{id}
- delete: DELETE /{entities}/{id}
- search: GET /{entities}/search (optional)

Design Reference:
    docs/02-design/14-Technical-Specs/IR-Processor-Specification.md

Author: Backend Lead
Date: December 23, 2025
Version: 1.0.0
Status: ACTIVE - Sprint 46 Implementation
"""

from typing import Dict, Any, List
from pathlib import Path
import logging

from .processor_base import IRProcessor, ProcessorResult, GeneratedFile

logger = logging.getLogger(__name__)


class EndpointProcessor(IRProcessor):
    """
    Generates CRUD API endpoints and services.

    This processor creates:
    - app/api/routes/{module}.py: FastAPI route handlers
    - app/services/{entity}_service.py: Service classes
    - app/api/__init__.py: API router registration
    - app/api/routes/__init__.py: Route exports

    Example:
        processor = EndpointProcessor(template_dir=Path("templates/fastapi"))
        result = processor.process(normalized_ir)
        for f in result.files:
            print(f"{f.path}: {len(f.content)} chars")
    """

    @property
    def name(self) -> str:
        return "endpoint"

    def process(self, ir: Dict[str, Any]) -> ProcessorResult:
        """
        Generate endpoint and service files.

        Args:
            ir: Normalized IR (AppBlueprint)

        Returns:
            ProcessorResult with endpoint and service files
        """
        files: List[GeneratedFile] = []
        errors: List[str] = []

        try:
            modules = self._get_all_modules(ir)

            if not modules:
                logger.warning("No modules found in IR")
                return ProcessorResult(
                    success=True,
                    files=files,
                    warnings=["No modules found in blueprint"]
                )

            # Generate for each module
            for module in modules:
                module_name = module["name"]
                operations = module.get("operations", [])
                entities = module.get("entities", [])

                # Generate route file for module
                files.append(GeneratedFile(
                    path=f"app/api/routes/{module_name}.py",
                    content=self.render_template("route.py.j2", {
                        "module_name": module_name,
                        "entities": entities,
                        "operations": operations,
                    })
                ))

                # Generate service for each entity
                for entity in entities:
                    service_name = self._get_service_filename(entity)
                    files.append(GeneratedFile(
                        path=f"app/services/{service_name}_service.py",
                        content=self.render_template("crud.py.j2", {
                            "entity": entity,
                            "operations": operations,
                        })
                    ))

            # Generate api/__init__.py with router registration
            files.append(GeneratedFile(
                path="app/api/__init__.py",
                content=self._generate_api_init(modules)
            ))

            # Generate api/routes/__init__.py
            files.append(GeneratedFile(
                path="app/api/routes/__init__.py",
                content=self._generate_routes_init(modules)
            ))

            # Generate services/__init__.py
            all_entities = self._get_all_entities(ir)
            files.append(GeneratedFile(
                path="app/services/__init__.py",
                content=self._generate_services_init(all_entities)
            ))

            logger.info(f"EndpointProcessor generated {len(files)} files for {len(modules)} modules")
            return ProcessorResult(success=True, files=files)

        except Exception as e:
            logger.exception(f"EndpointProcessor error: {e}")
            errors.append(f"EndpointProcessor failed: {str(e)}")
            return ProcessorResult(success=False, files=files, errors=errors)

    def _get_service_filename(self, entity: Dict[str, Any]) -> str:
        """Get service filename from entity.

        Examples: employees→employee, categories→category, addresses→address
        """
        table_name = entity.get("table_name", "")
        if not table_name:
            return table_name
        if table_name.endswith("ies") and len(table_name) > 3:
            return table_name[:-3] + "y"
        if table_name.endswith("es") and len(table_name) > 2:
            base = table_name[:-2]
            if base.endswith(("s", "sh", "ch", "x", "z")):
                return base
        if table_name.endswith("s") and not table_name.endswith("ss"):
            return table_name[:-1]
        return table_name

    def _generate_api_init(self, modules: List[Dict]) -> str:
        """Generate api/__init__.py with router registration."""
        lines = [
            '"""API router configuration.',
            '',
            'Generated by SDLC Orchestrator EP-06 IR Processor.',
            '"""',
            'from fastapi import APIRouter',
            '',
        ]

        # Import routers
        for module in modules:
            lines.append(
                f"from .routes.{module['name']} import router as {module['name']}_router"
            )

        lines.extend([
            '',
            'api_router = APIRouter()',
            '',
        ])

        # Include routers with prefixes and tags
        for module in modules:
            name = module["name"]
            lines.append(
                f'api_router.include_router('
                f'{name}_router, '
                f'prefix="/{name}", '
                f'tags=["{name}"]'
                f')'
            )

        lines.append('')
        return '\n'.join(lines)

    def _generate_routes_init(self, modules: List[Dict]) -> str:
        """Generate api/routes/__init__.py."""
        lines = [
            '"""API routes package.',
            '',
            'Generated by SDLC Orchestrator EP-06 IR Processor.',
            '"""',
            '',
        ]

        # Import routers
        for module in modules:
            lines.append(
                f"from .{module['name']} import router as {module['name']}_router"
            )

        lines.append('')

        # Export all
        exports = [f"{m['name']}_router" for m in modules]
        lines.append(f"__all__ = {exports}")
        lines.append('')

        return '\n'.join(lines)

    def _generate_services_init(self, entities: List[Dict]) -> str:
        """Generate services/__init__.py."""
        lines = [
            '"""Service classes package.',
            '',
            'Generated by SDLC Orchestrator EP-06 IR Processor.',
            '"""',
            '',
        ]

        # Import services
        for entity in entities:
            service_file = self._get_service_filename(entity)
            lines.append(
                f"from .{service_file}_service import {entity['name']}Service"
            )

        lines.append('')

        # Export all
        exports = [f"{e['name']}Service" for e in entities]
        lines.append(f"__all__ = {exports}")
        lines.append('')

        return '\n'.join(lines)
