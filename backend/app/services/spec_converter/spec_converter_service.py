"""
Spec Converter Service
Sprint 154 - Spec Standard Completion

Main service for converting between specification formats.

Supports:
- BDD (Gherkin) ↔ OpenSpec YAML
- User Story → BDD conversion
- Natural Language → BDD (AI-assisted)

Architecture: ADR-050 Spec Converter Editor Architecture
"""

from typing import Optional

from .models import SpecFormat, SpecIR
from .parsers.gherkin_parser import GherkinParser
from .parsers.openspec_parser import OpenSpecParser
from .parsers.user_story_parser import UserStoryParser


class SpecConverterService:
    """
    Main service for specification format conversion.

    Provides bidirectional conversion between:
    - BDD (Gherkin feature files)
    - OpenSpec (YAML frontmatter + markdown)
    - User Stories
    - Natural Language (AI-assisted)

    Example:
        service = SpecConverterService()
        ir = await service.parse(content, SpecFormat.BDD)
        openspec = await service.render(ir, SpecFormat.OPENSPEC)

    Architecture: ADR-050 Spec Converter Editor Architecture
    """

    def __init__(self):
        """Initialize parsers."""
        self._parsers = {
            SpecFormat.BDD: GherkinParser(),
            SpecFormat.OPENSPEC: OpenSpecParser(),
            SpecFormat.USER_STORY: UserStoryParser(),
        }

    async def parse(
        self,
        content: str,
        source_format: SpecFormat,
    ) -> SpecIR:
        """
        Parse specification content to intermediate representation.

        Args:
            content: Raw specification content
            source_format: Format of the input content

        Returns:
            SpecIR intermediate representation

        Raises:
            ValueError: If format is not supported or content is invalid
        """
        if source_format not in self._parsers:
            raise ValueError(f"Unsupported source format: {source_format}")

        parser = self._parsers[source_format]
        return await parser.parse(content)

    async def render(
        self,
        ir: SpecIR,
        target_format: SpecFormat,
    ) -> str:
        """
        Render intermediate representation to target format.

        Args:
            ir: SpecIR intermediate representation
            target_format: Desired output format

        Returns:
            Rendered specification content

        Raises:
            ValueError: If format is not supported
        """
        # Renderers will be implemented in Day 2
        raise NotImplementedError(
            f"Renderer for {target_format} not yet implemented (Day 2 task)"
        )

    async def convert(
        self,
        content: str,
        source_format: SpecFormat,
        target_format: SpecFormat,
    ) -> str:
        """
        Convert specification from one format to another.

        Args:
            content: Raw specification content
            source_format: Format of the input content
            target_format: Desired output format

        Returns:
            Converted specification content

        Raises:
            ValueError: If conversion is not supported
        """
        ir = await self.parse(content, source_format)
        return await self.render(ir, target_format)

    async def detect_format(self, content: str) -> Optional[SpecFormat]:
        """
        Auto-detect specification format from content.

        Args:
            content: Raw specification content

        Returns:
            Detected SpecFormat or None if unknown
        """
        content = content.strip()

        # Check for YAML frontmatter (OpenSpec)
        if content.startswith("---"):
            return SpecFormat.OPENSPEC

        # Check for Gherkin keywords
        gherkin_keywords = ["Feature:", "Scenario:", "Given ", "When ", "Then "]
        if any(kw in content for kw in gherkin_keywords):
            return SpecFormat.BDD

        # Check for user story format
        if "As a " in content or "As an " in content:
            if "I want" in content:
                return SpecFormat.USER_STORY

        # Unable to detect
        return None
