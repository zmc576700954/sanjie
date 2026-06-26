"""Unified component exporter.

Orchestrates format generation, file writing, and validation for exporting
core components to one or more target tool formats. Handles errors gracefully
-- if one tool fails, the others continue.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List

from core.shared.base import CoreComponent
from core.shared.errors import FormatGenerationError, UnsupportedToolError
from migration.generators.base import FormatGenerator
from migration.validators.base import FormatValidator, ValidationResult

logger = logging.getLogger(__name__)


class ComponentExporter:
    """Export core components to one or more target tool formats.

    The exporter orchestrates the full export pipeline:
        1. Check if a generator exists for each target tool.
        2. Generate format files using the generator.
        3. Write generated files to disk under ``output_dir/formats/{tool}/``.
        4. Validate generated files using the validator (if available).
        5. Return validation results per tool.

    Errors are handled gracefully: if one tool fails during generation,
    the error is recorded and the exporter continues with the remaining tools.

    Attributes:
        generators: Mapping of tool name to FormatGenerator instance.
        validators: Mapping of tool name to FormatValidator instance.
    """

    def __init__(
        self,
        generators: Dict[str, FormatGenerator],
        validators: Dict[str, FormatValidator],
    ) -> None:
        """Initialize the exporter with generators and validators.

        Args:
            generators: A dictionary mapping tool names (e.g. "claude") to
                        FormatGenerator instances.
            validators: A dictionary mapping tool names to FormatValidator
                        instances.
        """
        self.generators = generators
        self.validators = validators

    def export(
        self,
        component: CoreComponent,
        manifest: Dict[str, Any],
        target_tools: List[str],
        output_dir: Path,
    ) -> Dict[str, ValidationResult]:
        """Export a component to the specified tool formats.

        For each target tool, the exporter:
            1. Checks if a generator exists (records UnsupportedToolError if not).
            2. Generates format files.
            3. Writes files to ``output_dir/formats/{tool}/``.
            4. Validates generated files.
            5. Records the ValidationResult.

        If a tool fails during generation, it is skipped and the error is
        recorded in the result. Other tools continue processing.

        Args:
            component: The core component to export.
            manifest: The manifest.json content.
            target_tools: A list of tool names to export to (e.g. ["claude", "mcp"]).
            output_dir: The root output directory.

        Returns:
            A dictionary mapping tool names to their ValidationResult.
        """
        results: Dict[str, ValidationResult] = {}

        for tool in target_tools:
            # Step 1: Check if generator exists
            if tool not in self.generators:
                results[tool] = ValidationResult(
                    valid=False,
                    errors=[f"Unsupported tool: {tool}"],
                )
                continue

            # Step 2: Generate format files
            generator = self.generators[tool]
            try:
                generated = generator.generate(component, manifest)
            except (FormatGenerationError, Exception) as exc:
                error_msg = f"Generation failed for tool '{tool}': {exc}"
                logger.error(error_msg)
                results[tool] = ValidationResult(
                    valid=False,
                    errors=[error_msg],
                )
                continue

            # Step 3: Write files to disk
            tool_dir = output_dir / "formats" / tool
            try:
                self._write_files(generated, tool_dir)
            except OSError as exc:
                error_msg = f"Failed to write files for tool '{tool}': {exc}"
                logger.error(error_msg)
                results[tool] = ValidationResult(
                    valid=False,
                    errors=[error_msg],
                )
                continue

            # Step 4: Validate generated files
            if tool in self.validators:
                results[tool] = self.validators[tool].validate(generated, manifest)
            else:
                # No validator available -- assume valid
                results[tool] = ValidationResult(valid=True)

        return results

    def _write_files(self, generated: Dict[str, str], output_dir: Path) -> None:
        """Write generated files to disk.

        Creates any necessary parent directories and writes each file with
        UTF-8 encoding.

        Args:
            generated: A dictionary mapping relative file paths to content.
            output_dir: The directory to write files into.
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        for rel_path, content in generated.items():
            file_path = output_dir / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")

    @classmethod
    def create_default(cls) -> "ComponentExporter":
        """Create an exporter with all default generators and validators.

        Instantiates all five generators (claude, zcode, cursor, reasionix,
        mcp) and four validators (claude, zcode, cursor, mcp). Each generator
        loads templates from the ``formats/`` directory relative to the project
        root.

        Returns:
            A fully configured ComponentExporter instance.
        """
        from migration.generators.claude_generator import ClaudeFormatGenerator
        from migration.generators.zcode_generator import ZCodeFormatGenerator
        from migration.generators.cursor_generator import CursorFormatGenerator
        from migration.generators.reasionix_generator import ReasionixFormatGenerator
        from migration.generators.mcp_generator import MCPFormatGenerator
        from migration.validators.claude_validator import ClaudeFormatValidator
        from migration.validators.zcode_validator import ZCodeFormatValidator
        from migration.validators.cursor_validator import CursorFormatValidator
        from migration.validators.mcp_validator import MCPFormatValidator

        # Determine the project root (where formats/ directory lives)
        project_root = Path(__file__).parent.parent
        formats_dir = project_root / "formats"

        generators: Dict[str, FormatGenerator] = {
            "claude": ClaudeFormatGenerator(formats_dir / "claude"),
            "zcode": ZCodeFormatGenerator(formats_dir / "zcode"),
            "cursor": CursorFormatGenerator(formats_dir / "cursor"),
            "reasionix": ReasionixFormatGenerator(formats_dir / "reasionix"),
            "mcp": MCPFormatGenerator(formats_dir / "mcp"),
        }

        validators: Dict[str, FormatValidator] = {
            "claude": ClaudeFormatValidator(),
            "zcode": ZCodeFormatValidator(),
            "cursor": CursorFormatValidator(),
            "mcp": MCPFormatValidator(),
        }

        return cls(generators=generators, validators=validators)
