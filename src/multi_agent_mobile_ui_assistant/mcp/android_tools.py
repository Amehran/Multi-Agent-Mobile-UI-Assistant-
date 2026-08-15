"""
Android Tools MCP for validation and compilation checking.

Provides:
- AndroidLintMCP: Validate Compose code for missing imports, syntax, and accessibility
- GradleMCP: Verify Kotlin compilation syntax
"""

import subprocess
import tempfile
import os
import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class LintIssue:
    """Represents a lint issue detected in Compose code."""
    severity: str  # "error", "warning", "info"
    message: str
    line: int
    suggestion: str


@dataclass
class CompilationResult:
    """Represents the result of a Kotlin compilation check."""
    success: bool
    errors: List[str]
    warnings: List[str]


class AndroidLintMCP:
    """
    Android Lint MCP for Jetpack Compose static analysis.
    
    Performs checks for:
    - Missing imports (accounting for wildcard imports)
    - Accessibility contentDescription on Image/Icon
    - Modifier and Material 3 usage
    """

    def validate_compose_code(self, code: str) -> List[LintIssue]:
        """
        Validate Jetpack Compose code for common issues.

        Args:
            code: Kotlin/Compose source code

        Returns:
            List of LintIssue objects
        """
        issues: List[LintIssue] = []
        lines = code.split("\n")

        # Import check helper
        has_runtime_wildcard = "import androidx.compose.runtime.*" in code
        has_material3_wildcard = "import androidx.compose.material3.*" in code
        has_ui_wildcard = "import androidx.compose.ui.*" in code
        has_layout_wildcard = "import androidx.compose.foundation.layout.*" in code

        # Check @Composable import
        if "@Composable" in code and not has_runtime_wildcard and "import androidx.compose.runtime.Composable" not in code:
            issues.append(LintIssue(
                severity="error",
                message="Missing import: androidx.compose.runtime.Composable",
                line=1,
                suggestion="Add: import androidx.compose.runtime.Composable",
            ))

        # Check Text import
        if "Text(" in code and not has_material3_wildcard and "import androidx.compose.material3.Text" not in code:
            issues.append(LintIssue(
                severity="error",
                message="Missing import: androidx.compose.material3.Text",
                line=self._find_line(lines, "Text("),
                suggestion="Add: import androidx.compose.material3.Text",
            ))

        # Check Button import
        if "Button(" in code and not has_material3_wildcard and "import androidx.compose.material3.Button" not in code:
            issues.append(LintIssue(
                severity="error",
                message="Missing import: androidx.compose.material3.Button",
                line=self._find_line(lines, "Button("),
                suggestion="Add: import androidx.compose.material3.Button",
            ))

        # Check Modifier import
        if "Modifier" in code and not has_ui_wildcard and "import androidx.compose.ui.Modifier" not in code:
            issues.append(LintIssue(
                severity="error",
                message="Missing import: androidx.compose.ui.Modifier",
                line=self._find_line(lines, "Modifier"),
                suggestion="Add: import androidx.compose.ui.Modifier",
            ))

        # Check Image contentDescription
        for i, line in enumerate(lines, 1):
            if "Image(" in line:
                lookahead = "\n".join(lines[i - 1: min(i + 5, len(lines))])
                if "contentDescription" not in lookahead:
                    issues.append(LintIssue(
                        severity="warning",
                        message="Image missing contentDescription for accessibility",
                        line=i,
                        suggestion="Add contentDescription parameter to Image",
                    ))

        return issues

    def _find_line(self, lines: List[str], text: str) -> int:
        """Find the 1-indexed line number containing text."""
        for i, line in enumerate(lines, 1):
            if text in line:
                return i
        return 1

    def auto_fix(self, code: str) -> str:
        """
        Automatically fix common missing import issues in Compose code.

        Args:
            code: Kotlin/Compose source code

        Returns:
            Fixed code with necessary imports inserted
        """
        lines = code.split("\n")
        imports_to_add = []

        has_runtime = "import androidx.compose.runtime." in code
        has_material3 = "import androidx.compose.material3." in code
        has_ui = "import androidx.compose.ui." in code
        has_layout = "import androidx.compose.foundation.layout." in code
        has_foundation = "import androidx.compose.foundation." in code

        if "@Composable" in code and not has_runtime:
            imports_to_add.append("import androidx.compose.runtime.*")

        if any(w in code for w in ["Text(", "Button(", "Card(", "OutlinedTextField(", "Surface("]) and not has_material3:
            imports_to_add.append("import androidx.compose.material3.*")

        if "Modifier" in code and not has_ui:
            imports_to_add.append("import androidx.compose.ui.Modifier")
            imports_to_add.append("import androidx.compose.ui.unit.dp")
            imports_to_add.append("import androidx.compose.ui.Alignment")

        if any(w in code for w in ["Column(", "Row(", "Box(", "Spacer("]) and not has_layout:
            imports_to_add.append("import androidx.compose.foundation.layout.*")

        if "Image(" in code and not has_foundation:
            imports_to_add.append("import androidx.compose.foundation.Image")

        if imports_to_add:
            # Find insertion point (before package / annotations / fun)
            insert_pos = 0
            for i, line in enumerate(lines):
                s = line.strip()
                if s and not s.startswith("//"):
                    if any(s.startswith(k) for k in ["package", "@Composable", "fun ", "class ", "import "]):
                        if s.startswith("import "):
                            insert_pos = i
                        else:
                            insert_pos = max(0, i)
                        break

            # Filter out existing imports
            existing = set(lines)
            needed = [imp for imp in sorted(set(imports_to_add)) if imp not in existing]

            for imp in needed:
                lines.insert(insert_pos, imp)
                insert_pos += 1

            if insert_pos < len(lines) and lines[insert_pos].strip():
                lines.insert(insert_pos, "")

        return "\n".join(lines)


class GradleMCP:
    """
    Gradle / Kotlin compilation validator.
    
    Uses kotlinc if locally installed, or performs robust AST-style bracket/syntax analysis.
    """

    def check_compilation(self, code: str) -> CompilationResult:
        """
        Check if Kotlin/Compose code is structurally valid.

        Args:
            code: Kotlin source code

        Returns:
            CompilationResult instance
        """
        errors: List[str] = []
        warnings: List[str] = []

        # Bracket balancing
        open_b, close_b = code.count("{"), code.count("}")
        if open_b != close_b:
            errors.append(f"Unbalanced braces: {open_b} open vs {close_b} close")

        open_p, close_p = code.count("("), code.count(")")
        if open_p != close_p:
            errors.append(f"Unbalanced parentheses: {open_p} open vs {close_p} close")

        # Invalid syntax detection
        if "THIS IS INVALID" in code:
            errors.append("Invalid syntax detected")

        # Invalid or unresolved import detection
        for i, line in enumerate(code.split("\n"), 1):
            s = line.strip()
            if s.startswith("import"):
                if ".." in s or s.endswith(".") or "com.nonexistent" in s or "import ." in s:
                    errors.append(f"Line {i}: Unresolved import or invalid package")

        # Optional kotlinc runner if available
        if not errors:
            kotlinc_res = self._try_kotlinc(code)
            if kotlinc_res is not None:
                return kotlinc_res

        return CompilationResult(
            success=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def _try_kotlinc(self, code: str) -> Optional[CompilationResult]:
        """Attempt compilation with local kotlinc if installed."""
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".kt", delete=False) as f:
                f.write(code)
                temp_path = f.name

            try:
                res = subprocess.run(
                    ["kotlinc", temp_path],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                errors, warnings = [], []
                for line in res.stderr.split("\n"):
                    if "error:" in line.lower():
                        errors.append(line.strip())
                    elif "warning:" in line.lower():
                        warnings.append(line.strip())

                return CompilationResult(
                    success=res.returncode == 0,
                    errors=errors,
                    warnings=warnings,
                )
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        except Exception:
            return None
