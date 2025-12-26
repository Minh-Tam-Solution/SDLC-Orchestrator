"""
File Boundary Parser for Streaming Code Generation.

Sprint 51B: File Parsing POC (90%+ accuracy target)
Date: December 25, 2025
Status: POC - Proof of Concept

Purpose:
- Parse AI-generated code output into individual files
- Support multiple file marker patterns from different LLMs
- Achieve 90%+ accuracy on file boundary detection
- Stream-compatible: can parse incrementally as tokens arrive

Supported Patterns:
1. ### FILE: path/to/file.py (Ollama default, current standard)
2. ```python\n# filename: path/to/file.py (Common in Claude/GPT)
3. // FILE: path/to/file.ts (TypeScript convention)
4. <!-- FILE: path/to/file.html --> (HTML convention)
5. # --- file: path/to/file.py --- (Alternative marker)

Author: Backend Lead
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Generator
from enum import Enum

logger = logging.getLogger(__name__)


class FileMarkerPattern(Enum):
    """Supported file marker patterns."""
    HASH_FILE = "### FILE:"  # Primary: ### FILE: path/to/file.py
    CODE_BLOCK_FILENAME = "# filename:"  # ```python\n# filename: ...
    DOUBLE_SLASH_FILE = "// FILE:"  # // FILE: path/to/file.ts
    HTML_COMMENT_FILE = "<!-- FILE:"  # <!-- FILE: path/to/file.html -->
    DASH_FILE = "# --- file:"  # # --- file: path/to/file.py ---
    TRIPLE_HASH_PATH = "### "  # ### path/to/file.py (no FILE: prefix)


@dataclass
class ParsedFile:
    """Result of parsing a single file from output."""
    path: str
    content: str
    start_line: int
    end_line: int
    pattern_used: FileMarkerPattern
    language: str = "unknown"
    syntax_valid: Optional[bool] = None

    @property
    def lines(self) -> int:
        """Number of lines in the file content."""
        return len(self.content.split("\n")) if self.content else 0


@dataclass
class ParserState:
    """Streaming parser state for incremental parsing."""
    buffer: str = ""
    current_file: Optional[str] = None
    current_content: List[str] = field(default_factory=list)
    current_start_line: int = 0
    current_pattern: Optional[FileMarkerPattern] = None
    in_code_block: bool = False
    code_block_lang: str = ""
    line_number: int = 0
    parsed_files: List[ParsedFile] = field(default_factory=list)


class FileBoundaryParser:
    """
    Multi-pattern file boundary parser for LLM code output.

    Supports both batch and streaming parsing modes:
    - Batch: parse_output() for complete output
    - Streaming: parse_chunk() for incremental token streams

    Example (Batch):
        parser = FileBoundaryParser()
        files = parser.parse_output(llm_output)
        for file in files:
            print(f"{file.path}: {len(file.content)} chars")

    Example (Streaming):
        parser = FileBoundaryParser()
        state = ParserState()
        for chunk in llm_stream:
            new_files = parser.parse_chunk(chunk, state)
            for file in new_files:
                yield file  # Emit as soon as complete
    """

    # Regex patterns for file detection
    PATTERNS = {
        FileMarkerPattern.HASH_FILE: re.compile(
            r'^#{2,3}\s*FILE:\s*(.+?)(?:\s*###)?$',
            re.MULTILINE
        ),
        FileMarkerPattern.CODE_BLOCK_FILENAME: re.compile(
            r'^```(\w+)?\s*\n#\s*filename:\s*(.+?)$',
            re.MULTILINE
        ),
        FileMarkerPattern.DOUBLE_SLASH_FILE: re.compile(
            r'^// FILE:\s*(.+?)$',
            re.MULTILINE
        ),
        FileMarkerPattern.HTML_COMMENT_FILE: re.compile(
            r'^<!-- FILE:\s*(.+?)\s*-->',
            re.MULTILINE
        ),
        FileMarkerPattern.DASH_FILE: re.compile(
            r'^#\s*---\s*file:\s*(.+?)\s*---\s*$',
            re.MULTILINE | re.IGNORECASE
        ),
        FileMarkerPattern.TRIPLE_HASH_PATH: re.compile(
            r'^###\s+([\w./\-]+\.\w+)\s*$',
            re.MULTILINE
        ),
    }

    # Language detection from file extension
    EXTENSION_TO_LANG = {
        "py": "python",
        "ts": "typescript",
        "tsx": "typescript",
        "js": "javascript",
        "jsx": "javascript",
        "json": "json",
        "yaml": "yaml",
        "yml": "yaml",
        "md": "markdown",
        "sql": "sql",
        "html": "html",
        "css": "css",
        "sh": "bash",
        "bash": "bash",
        "txt": "text",
        "toml": "toml",
        "ini": "ini",
        "cfg": "ini",
        "go": "go",
        "rs": "rust",
        "java": "java",
        "kt": "kotlin",
        "swift": "swift",
        "rb": "ruby",
        "php": "php",
        "c": "c",
        "cpp": "cpp",
        "h": "c",
        "hpp": "cpp",
    }

    def __init__(self, strict_mode: bool = False):
        """
        Initialize parser.

        Args:
            strict_mode: If True, raise on parse errors instead of logging
        """
        self.strict_mode = strict_mode

    def parse_output(self, output: str) -> List[ParsedFile]:
        """
        Parse complete LLM output into files.

        Args:
            output: Complete LLM output string

        Returns:
            List of ParsedFile objects
        """
        if not output or not output.strip():
            logger.warning("Empty output provided to parser")
            return []

        # Try each pattern in priority order
        files = self._parse_with_primary_pattern(output)

        if not files:
            # Fallback: try alternative patterns
            files = self._parse_with_fallback_patterns(output)

        if not files:
            logger.warning(
                f"No files parsed from output ({len(output)} chars). "
                "Output may not contain file markers."
            )

        # Detect language for each file
        for file in files:
            file.language = self._detect_language(file.path)

        return files

    def _parse_with_primary_pattern(self, output: str) -> List[ParsedFile]:
        """
        Parse using primary ### FILE: pattern (most common).

        This is the format we instruct LLMs to use.
        """
        files: List[ParsedFile] = []
        current_file: Optional[str] = None
        current_content: List[str] = []
        current_start_line: int = 0
        in_code_block = False

        lines = output.split('\n')

        for i, line in enumerate(lines):
            # Check for file marker
            file_match = self.PATTERNS[FileMarkerPattern.HASH_FILE].match(line)

            if file_match:
                # Save previous file if exists
                if current_file and current_content:
                    content = '\n'.join(current_content)
                    content = self._clean_code_content(content)
                    files.append(ParsedFile(
                        path=current_file,
                        content=content,
                        start_line=current_start_line,
                        end_line=i - 1,
                        pattern_used=FileMarkerPattern.HASH_FILE,
                    ))

                # Start new file
                current_file = file_match.group(1).strip()
                current_content = []
                current_start_line = i
                in_code_block = False
                continue

            if current_file:
                # Track code block state
                if line.startswith('```'):
                    if in_code_block:
                        in_code_block = False
                        continue  # Skip closing ```
                    else:
                        in_code_block = True
                        continue  # Skip opening ``` with language

                current_content.append(line)

        # Save last file
        if current_file and current_content:
            content = '\n'.join(current_content)
            content = self._clean_code_content(content)
            files.append(ParsedFile(
                path=current_file,
                content=content,
                start_line=current_start_line,
                end_line=len(lines) - 1,
                pattern_used=FileMarkerPattern.HASH_FILE,
            ))

        return files

    def _parse_with_fallback_patterns(self, output: str) -> List[ParsedFile]:
        """
        Try alternative patterns if primary fails.

        Tests each pattern and returns first successful parse.
        """
        for pattern_type, pattern in self.PATTERNS.items():
            if pattern_type == FileMarkerPattern.HASH_FILE:
                continue  # Already tried

            files = self._parse_with_pattern(output, pattern_type, pattern)
            if files:
                logger.info(
                    f"Parsed {len(files)} files using fallback pattern: {pattern_type.name}"
                )
                return files

        # Last resort: try to extract from code blocks
        return self._parse_from_code_blocks(output)

    def _parse_with_pattern(
        self,
        output: str,
        pattern_type: FileMarkerPattern,
        pattern: re.Pattern
    ) -> List[ParsedFile]:
        """Parse output using a specific pattern."""
        files: List[ParsedFile] = []

        matches = list(pattern.finditer(output))

        if not matches:
            return []

        for i, match in enumerate(matches):
            # Get file path from appropriate group
            if pattern_type == FileMarkerPattern.CODE_BLOCK_FILENAME:
                file_path = match.group(2).strip()
            else:
                file_path = match.group(1).strip()

            # Determine content boundaries
            start = match.end()

            if i + 1 < len(matches):
                end = matches[i + 1].start()
            else:
                end = len(output)

            content = output[start:end].strip()
            content = self._clean_code_content(content)

            if content:  # Only add if has content
                files.append(ParsedFile(
                    path=file_path,
                    content=content,
                    start_line=output[:start].count('\n'),
                    end_line=output[:end].count('\n'),
                    pattern_used=pattern_type,
                ))

        return files

    def _parse_from_code_blocks(self, output: str) -> List[ParsedFile]:
        """
        Last resort: extract files from code blocks with filename comments.

        Looks for patterns like:
        ```python
        # app/main.py
        from fastapi import FastAPI
        ...
        ```
        """
        files: List[ParsedFile] = []

        # Match code blocks with first-line filename comment
        code_block_pattern = re.compile(
            r'```(\w+)?\s*\n(?:#|//|<!--)\s*([^\n]+\.\w+)\s*(?:-->)?\n(.*?)```',
            re.DOTALL
        )

        for match in code_block_pattern.finditer(output):
            lang = match.group(1) or "unknown"
            file_path = match.group(2).strip()
            content = match.group(3).strip()

            # Validate file path looks reasonable
            if '/' in file_path or file_path.count('.') == 1:
                files.append(ParsedFile(
                    path=file_path,
                    content=content,
                    start_line=output[:match.start()].count('\n'),
                    end_line=output[:match.end()].count('\n'),
                    pattern_used=FileMarkerPattern.CODE_BLOCK_FILENAME,
                    language=lang,
                ))

        return files

    def _clean_code_content(self, content: str) -> str:
        """
        Clean up code content.

        Removes:
        - Stray code block markers
        - Leading/trailing whitespace
        - Empty first/last lines
        """
        # Remove any remaining code block markers
        content = re.sub(r'^```\w*\n?', '', content)
        content = re.sub(r'\n?```$', '', content)

        # Trim whitespace
        content = content.strip()

        return content

    def _detect_language(self, file_path: str) -> str:
        """Detect language from file extension."""
        if '.' not in file_path:
            return "unknown"

        ext = file_path.rsplit('.', 1)[-1].lower()
        return self.EXTENSION_TO_LANG.get(ext, ext)

    # =========================================================================
    # Streaming Support (for Sprint 51B real-time parsing)
    # =========================================================================

    def parse_chunk(
        self,
        chunk: str,
        state: ParserState
    ) -> List[ParsedFile]:
        """
        Parse a chunk of streaming output.

        Accumulates text until a complete file is detected,
        then emits ParsedFile objects.

        Args:
            chunk: New text chunk from LLM stream
            state: Current parser state (mutated in place)

        Returns:
            List of newly completed files (may be empty)
        """
        state.buffer += chunk
        completed_files: List[ParsedFile] = []

        # Process complete lines
        while '\n' in state.buffer:
            line, state.buffer = state.buffer.split('\n', 1)
            state.line_number += 1

            # Check for file marker
            file_match = self.PATTERNS[FileMarkerPattern.HASH_FILE].match(line)

            if file_match:
                # Complete previous file if exists
                if state.current_file and state.current_content:
                    content = '\n'.join(state.current_content)
                    content = self._clean_code_content(content)
                    parsed = ParsedFile(
                        path=state.current_file,
                        content=content,
                        start_line=state.current_start_line,
                        end_line=state.line_number - 1,
                        pattern_used=state.current_pattern or FileMarkerPattern.HASH_FILE,
                    )
                    parsed.language = self._detect_language(parsed.path)
                    completed_files.append(parsed)
                    state.parsed_files.append(parsed)

                # Start new file
                state.current_file = file_match.group(1).strip()
                state.current_content = []
                state.current_start_line = state.line_number
                state.current_pattern = FileMarkerPattern.HASH_FILE
                state.in_code_block = False
                continue

            if state.current_file:
                # Track code block state
                if line.startswith('```'):
                    if state.in_code_block:
                        state.in_code_block = False
                        continue
                    else:
                        state.in_code_block = True
                        state.code_block_lang = line[3:].strip()
                        continue

                state.current_content.append(line)

        return completed_files

    def finalize_stream(self, state: ParserState) -> Optional[ParsedFile]:
        """
        Finalize streaming parse, returning any remaining file.

        Call this when the stream ends to get the last file.

        Args:
            state: Current parser state

        Returns:
            Last file if any content remains, None otherwise
        """
        # Process any remaining buffer
        if state.buffer:
            state.current_content.append(state.buffer)
            state.buffer = ""

        # Complete last file
        if state.current_file and state.current_content:
            content = '\n'.join(state.current_content)
            content = self._clean_code_content(content)
            parsed = ParsedFile(
                path=state.current_file,
                content=content,
                start_line=state.current_start_line,
                end_line=state.line_number,
                pattern_used=state.current_pattern or FileMarkerPattern.HASH_FILE,
            )
            parsed.language = self._detect_language(parsed.path)
            state.parsed_files.append(parsed)
            state.current_file = None
            state.current_content = []
            return parsed

        return None


# ============================================================================
# POC Test Cases for 90%+ Accuracy Validation
# ============================================================================

def run_poc_tests() -> Dict[str, bool]:
    """
    Run POC tests to validate 90%+ accuracy.

    Returns:
        Dict of test_name -> passed
    """
    parser = FileBoundaryParser()
    results: Dict[str, bool] = {}

    # Test 1: Primary pattern (### FILE:)
    test1_input = """### FILE: app/main.py
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
```

### FILE: app/models.py
```python
from sqlalchemy import Column, Integer, String
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
```
"""
    files = parser.parse_output(test1_input)
    results["test1_primary_pattern"] = (
        len(files) == 2 and
        files[0].path == "app/main.py" and
        files[1].path == "app/models.py" and
        "FastAPI" in files[0].content and
        "User" in files[1].content
    )

    # Test 2: Fallback pattern (# filename:)
    test2_input = """```python
# filename: src/utils.py
def helper():
    return True
```

```python
# filename: src/config.py
DEBUG = True
```
"""
    files = parser.parse_output(test2_input)
    results["test2_fallback_pattern"] = (
        len(files) == 2 and
        files[0].path == "src/utils.py" and
        files[1].path == "src/config.py"
    )

    # Test 3: Mixed content with noise
    test3_input = """Here's the generated code:

### FILE: api/routes.py
```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/users")
def list_users():
    return []
```

Some explanation about the code above...

### FILE: api/__init__.py
```python
from .routes import router
```

Done!
"""
    files = parser.parse_output(test3_input)
    results["test3_noise_handling"] = (
        len(files) == 2 and
        files[0].path == "api/routes.py" and
        files[1].path == "api/__init__.py" and
        "router = APIRouter()" in files[0].content
    )

    # Test 4: TypeScript files
    test4_input = """### FILE: src/index.ts
```typescript
export function hello(): string {
    return "Hello, World!";
}
```

### FILE: src/types.ts
```typescript
export interface User {
    id: number;
    name: string;
}
```
"""
    files = parser.parse_output(test4_input)
    results["test4_typescript"] = (
        len(files) == 2 and
        files[0].language == "typescript" and
        files[1].language == "typescript"
    )

    # Test 5: Streaming mode
    test5_chunks = [
        "### FILE: app/",
        "service.py\n```python\n",
        "class Service:\n    pass\n",
        "```\n### FILE: app/",
        "model.py\n```python\n",
        "class Model:\n    pass\n```",
    ]
    state = ParserState()
    all_files = []
    for chunk in test5_chunks:
        completed = parser.parse_chunk(chunk, state)
        all_files.extend(completed)
    final = parser.finalize_stream(state)
    if final:
        all_files.append(final)

    results["test5_streaming"] = (
        len(all_files) == 2 and
        all_files[0].path == "app/service.py" and
        all_files[1].path == "app/model.py"
    )

    # Test 6: Empty/invalid input
    files = parser.parse_output("")
    results["test6_empty_input"] = len(files) == 0

    files = parser.parse_output("Just some text without files")
    results["test7_no_markers"] = len(files) == 0

    # Test 8: Language detection
    test8_input = """### FILE: test.py
```python
pass
```
### FILE: test.tsx
```tsx
export default () => null
```
### FILE: test.sql
```sql
SELECT 1
```
"""
    files = parser.parse_output(test8_input)
    results["test8_language_detection"] = (
        len(files) == 3 and
        files[0].language == "python" and
        files[1].language == "typescript" and
        files[2].language == "sql"
    )

    return results


def run_edge_case_tests() -> Dict[str, bool]:
    """
    Run additional edge case tests.

    Returns:
        Dict of test_name -> passed
    """
    parser = FileBoundaryParser()
    results: Dict[str, bool] = {}

    # Edge 1: Unicode in file content (Vietnamese)
    edge1_input = """### FILE: app/messages.py
```python
# Tin nhắn tiếng Việt
WELCOME_MESSAGE = "Xin chào! Chào mừng bạn đến với hệ thống."
ERROR_MESSAGE = "Đã xảy ra lỗi. Vui lòng thử lại."
```
"""
    files = parser.parse_output(edge1_input)
    results["edge1_vietnamese_content"] = (
        len(files) == 1 and
        "Xin chào" in files[0].content and
        "tiếng Việt" in files[0].content
    )

    # Edge 2: Multiple nested code blocks
    edge2_input = """### FILE: docs/readme.md
```markdown
# API Documentation

Example usage:
```python
client.get("/users")
```

Another example:
```bash
curl http://localhost:8000
```
```
"""
    files = parser.parse_output(edge2_input)
    results["edge2_nested_blocks"] = (
        len(files) == 1 and
        files[0].path == "docs/readme.md" and
        "API Documentation" in files[0].content
    )

    # Edge 3: Very long file path
    edge3_input = """### FILE: backend/app/services/codegen/templates/domains/vietnamese/retail/models.py
```python
class Product:
    pass
```
"""
    files = parser.parse_output(edge3_input)
    results["edge3_long_path"] = (
        len(files) == 1 and
        "vietnamese/retail" in files[0].path
    )

    # Edge 4: Files without code blocks (raw content)
    edge4_input = """### FILE: config.yaml
database:
  host: localhost
  port: 5432

### FILE: .env.example
DEBUG=true
DATABASE_URL=postgresql://localhost/db
"""
    files = parser.parse_output(edge4_input)
    results["edge4_no_code_blocks"] = (
        len(files) == 2 and
        "host: localhost" in files[0].content and
        "DATABASE_URL" in files[1].content
    )

    # Edge 5: Whitespace variations in marker
    edge5_input = """###FILE:app/main.py
```python
main_content = True
```

### FILE:  app/utils.py
```python
utils_content = True
```

###  FILE: app/config.py
```python
config_content = True
```
"""
    files = parser.parse_output(edge5_input)
    # Should handle various spacing
    results["edge5_whitespace_variations"] = len(files) >= 2

    # Edge 6: Empty file content
    edge6_input = """### FILE: app/__init__.py
```python
```

### FILE: app/real.py
```python
real_content = True
```
"""
    files = parser.parse_output(edge6_input)
    results["edge6_empty_file"] = (
        len(files) >= 1 and
        any("real_content" in f.content for f in files)
    )

    # Edge 7: Special characters in path
    edge7_input = """### FILE: app/models-v2.py
```python
v2_model = True
```

### FILE: app/test_config.py
```python
test_config = True
```
"""
    files = parser.parse_output(edge7_input)
    results["edge7_special_chars_path"] = (
        len(files) == 2 and
        files[0].path == "app/models-v2.py"
    )

    # Edge 8: JSON file parsing
    edge8_input = """### FILE: package.json
```json
{
  "name": "my-app",
  "version": "1.0.0"
}
```
"""
    files = parser.parse_output(edge8_input)
    results["edge8_json_file"] = (
        len(files) == 1 and
        files[0].language == "json" and
        '"name"' in files[0].content
    )

    # Edge 9: Streaming with incomplete chunks
    edge9_chunks = [
        "### FI",
        "LE: app/",
        "stream_",
        "test.py\n",
        "```python\n",
        "def test():\n",
        "    pass",
        "\n```",
    ]
    state = ParserState()
    all_files = []
    for chunk in edge9_chunks:
        completed = parser.parse_chunk(chunk, state)
        all_files.extend(completed)
    final = parser.finalize_stream(state)
    if final:
        all_files.append(final)

    results["edge9_incomplete_chunks"] = (
        len(all_files) == 1 and
        all_files[0].path == "app/stream_test.py" and
        "def test()" in all_files[0].content
    )

    # Edge 10: Real-world output sample (simulated Ollama)
    edge10_input = """Tôi sẽ tạo code cho ứng dụng quản lý nhà hàng.

### FILE: app/main.py
```python
from fastapi import FastAPI
from app.routes import menu, orders

app = FastAPI(title="Restaurant Management API")

app.include_router(menu.router, prefix="/api/v1/menu")
app.include_router(orders.router, prefix="/api/v1/orders")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

Tiếp theo là file routes cho menu:

### FILE: app/routes/menu.py
```python
from fastapi import APIRouter, Depends
from typing import List
from app.schemas.menu import MenuItem, MenuItemCreate
from app.services.menu_service import MenuService

router = APIRouter(tags=["Menu"])

@router.get("/items", response_model=List[MenuItem])
async def get_menu_items(service: MenuService = Depends()):
    return await service.get_all_items()
```

Xong rồi! Đây là code cơ bản cho hệ thống.
"""
    files = parser.parse_output(edge10_input)
    results["edge10_real_world"] = (
        len(files) == 2 and
        files[0].path == "app/main.py" and
        files[1].path == "app/routes/menu.py" and
        "FastAPI" in files[0].content and
        "MenuService" in files[1].content
    )

    return results


if __name__ == "__main__":
    # Run POC tests
    print("=" * 60)
    print("File Boundary Parser - POC Tests")
    print("=" * 60)

    results = run_poc_tests()
    edge_results = run_edge_case_tests()

    all_results = {**results, **edge_results}

    passed = sum(1 for v in all_results.values() if v)
    total = len(all_results)
    accuracy = (passed / total) * 100

    print(f"\nCore Tests:")
    for test_name, passed_flag in results.items():
        status = "✅ PASS" if passed_flag else "❌ FAIL"
        print(f"  {test_name}: {status}")

    print(f"\nEdge Case Tests:")
    for test_name, passed_flag in edge_results.items():
        status = "✅ PASS" if passed_flag else "❌ FAIL"
        print(f"  {test_name}: {status}")

    print(f"\n{'=' * 60}")
    print(f"Total Accuracy: {accuracy:.1f}% ({passed}/{total})")
    print(f"Target: 90%")
    print(f"Status: {'✅ POC PASSED' if accuracy >= 90 else '❌ POC FAILED'}")
    print(f"{'=' * 60}")
