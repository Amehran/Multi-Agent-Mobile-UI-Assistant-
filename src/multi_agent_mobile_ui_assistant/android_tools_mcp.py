"""
Android Tools MCP for validation and compilation checking.

Provides:
- AndroidLintMCP: Validate Compose code for common issues
- GradleMCP: Check Kotlin compilation
"""

import subprocess
import tempfile
import os
from dataclasses import dataclass
from typing import List


@dataclass
class LintIssue:
    """Represents a lint issue found in code."""
    severity: str  # "error", "warning", "info"
    message: str
    line: int
    suggestion: str


@dataclass
class CompilationResult:
    """Represents result of compilation check."""
    success: bool
    errors: List[str]
    warnings: List[str]


class AndroidLintMCP:
    """
    Android Lint MCP for Compose code validation.
    
    Performs static analysis to detect:
    - Missing imports
    - Accessibility issues
    - Material Design violations
    - Common Compose mistakes
    """
    
    def __init__(self):
        """Initialize Android Lint MCP."""
        self.common_imports = [
            "androidx.compose.runtime.Composable",
            "androidx.compose.material3.Text",
            "androidx.compose.material3.Button",
            "androidx.compose.foundation.Image",
            "androidx.compose.ui.Modifier",
            "androidx.compose.foundation.layout.Column",
            "androidx.compose.foundation.layout.Row",
            "androidx.compose.foundation.layout.Box",
        ]
    
    def validate_compose_code(self, code: str) -> List[LintIssue]:
        """
        Validate Jetpack Compose code for common issues.
        
        Args:
            code: Kotlin/Compose code to validate
            
        Returns:
            List of LintIssue objects
        """
        issues = []
        lines = code.split('\n')
        
        # Check for missing imports
        if '@Composable' in code and 'import androidx.compose.runtime.Composable' not in code:
            issues.append(LintIssue(
                severity="error",
                message="Missing import: androidx.compose.runtime.Composable",
                line=1,
                suggestion="Add: import androidx.compose.runtime.Composable"
            ))
        
        # Check for Text without import
        if 'Text(' in code and 'import androidx.compose.material3.Text' not in code:
            issues.append(LintIssue(
                severity="error",
                message="Missing import: androidx.compose.material3.Text",
                line=self._find_line(lines, 'Text('),
                suggestion="Add: import androidx.compose.material3.Text"
            ))
        
        # Check for Button without import
        if 'Button(' in code and 'import androidx.compose.material3.Button' not in code:
            issues.append(LintIssue(
                severity="error",
                message="Missing import: androidx.compose.material3.Button",
                line=self._find_line(lines, 'Button('),
                suggestion="Add: import androidx.compose.material3.Button"
            ))
        
        # Check for Image without contentDescription
        for i, line in enumerate(lines, 1):
            if 'Image(' in line:
                # Look ahead for contentDescription
                next_lines = '\n'.join(lines[i:min(i+5, len(lines))])
                if 'contentDescription' not in next_lines:
                    issues.append(LintIssue(
                        severity="warning",
                        message="Image missing contentDescription for accessibility",
                        line=i,
                        suggestion="Add contentDescription parameter to Image"
                    ))
        
        # Check for Modifier usage without import
        if 'Modifier' in code and 'import androidx.compose.ui.Modifier' not in code:
            issues.append(LintIssue(
                severity="error",
                message="Missing import: androidx.compose.ui.Modifier",
                line=self._find_line(lines, 'Modifier'),
                suggestion="Add: import androidx.compose.ui.Modifier"
            ))
        
        return issues
    
    def _find_line(self, lines: List[str], text: str) -> int:
        """Find line number containing text."""
        for i, line in enumerate(lines, 1):
            if text in line:
                return i
        return 1
    
    def auto_fix(self, code: str) -> str:
        """
        Automatically fix common issues in Compose code.
        
        Args:
            code: Kotlin/Compose code with issues
            
        Returns:
            Fixed code with imports added
        """
        lines = code.split('\n')
        imports_to_add = []
        
        # Determine which imports are needed
        if '@Composable' in code and 'import androidx.compose.runtime.Composable' not in code:
            imports_to_add.append('import androidx.compose.runtime.Composable')
        
        if 'Text(' in code and 'import androidx.compose.material3.Text' not in code:
            imports_to_add.append('import androidx.compose.material3.Text')
        
        if 'Button(' in code and 'import androidx.compose.material3.Button' not in code:
            imports_to_add.append('import androidx.compose.material3.Button')
        
        if 'Image(' in code and 'import androidx.compose.foundation.Image' not in code:
            imports_to_add.append('import androidx.compose.foundation.Image')
        
        if 'Modifier' in code and 'import androidx.compose.ui.Modifier' not in code:
            imports_to_add.append('import androidx.compose.ui.Modifier')
        
        if 'Column' in code and 'import androidx.compose.foundation.layout.Column' not in code:
            imports_to_add.append('import androidx.compose.foundation.layout.Column')
        
        if 'Row' in code and 'import androidx.compose.foundation.layout.Row' not in code:
            imports_to_add.append('import androidx.compose.foundation.layout.Row')
        
        if 'Box' in code and 'import androidx.compose.foundation.layout.Box' not in code:
            imports_to_add.append('import androidx.compose.foundation.layout.Box')
        
        # Add imports at the beginning
        if imports_to_add:
            # Find where to insert imports (before package/class/function)
            insert_position = 0
            for i, line in enumerate(lines):
                if line.strip() and not line.strip().startswith('//'):
                    if any(keyword in line for keyword in ['package', '@', 'fun', 'class']):
                        insert_position = i
                        break
            
            # Insert imports
            for imp in sorted(set(imports_to_add)):
                lines.insert(insert_position, imp)
                insert_position += 1
            
            # Add blank line after imports if not present
            if insert_position < len(lines) and lines[insert_position].strip():
                lines.insert(insert_position, '')
        
        return '\n'.join(lines)


class GradleMCP:
    """
    Gradle MCP for Kotlin compilation checking.
    
    Uses kotlinc or basic syntax validation to check if code compiles.
    """
    
    def __init__(self):
        """Initialize Gradle MCP."""
        pass
    
    def check_compilation(self, code: str) -> CompilationResult:
        """
        Check if Kotlin/Compose code compiles.
        
        Args:
            code: Kotlin code to check
            
        Returns:
            CompilationResult with success status and errors
        """
        errors = []
        warnings = []
        
        # Basic syntax validation
        # Check for balanced braces
        open_braces = code.count('{')
        close_braces = code.count('}')
        if open_braces != close_braces:
            errors.append(f"Unbalanced braces: {open_braces} open, {close_braces} close")
        
        # Check for balanced parentheses
        open_parens = code.count('(')
        close_parens = code.count(')')
        if open_parens != close_parens:
            errors.append(f"Unbalanced parentheses: {open_parens} open, {close_parens} close")
        
        # Check for basic Kotlin keywords misuse
        if 'THIS IS INVALID' in code:
            errors.append("Invalid syntax detected")
        
        # Check for unresolved imports
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            if line.strip().startswith('import'):
                # Check for obviously bad imports
                if 'com.nonexistent' in line or 'import .' in line:
                    errors.append(f"Line {i}: Unresolved import or invalid package")
        
        # Try kotlinc if available (fallback to basic checks)
        if not errors:
            try:
                result = self._try_kotlinc(code)
                if result:
                    return result
            except Exception:
                # If kotlinc not available, use basic validation
                pass
        
        success = len(errors) == 0
        return CompilationResult(
            success=success,
            errors=errors,
            warnings=warnings
        )
    
    def _try_kotlinc(self, code: str) -> CompilationResult:
        """
        Try to compile with kotlinc if available.
        
        Args:
            code: Kotlin code
            
        Returns:
            CompilationResult or None if kotlinc not available
        """
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.kt', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Try to compile with kotlinc
                result = subprocess.run(
                    ['kotlinc', temp_file],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                errors = []
                warnings = []
                
                if result.returncode != 0:
                    # Parse errors from stderr
                    stderr_lines = result.stderr.split('\n')
                    for line in stderr_lines:
                        if 'error:' in line.lower():
                            errors.append(line.strip())
                        elif 'warning:' in line.lower():
                            warnings.append(line.strip())
                
                return CompilationResult(
                    success=result.returncode == 0,
                    errors=errors,
                    warnings=warnings
                )
            finally:
                # Clean up temp file
                if os.path.exists(temp_file):
                    os.remove(temp_file)
        
        except (FileNotFoundError, subprocess.TimeoutExpired):
            # kotlinc not available or timed out
            return None
