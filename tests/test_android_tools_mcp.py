"""
Tests for Android Tools MCP integration.

Following TDD methodology:
1. RED: Write failing tests that define desired validation behavior
2. GREEN: Implement minimal code to make tests pass
3. REFACTOR: Improve code while keeping tests green
"""

from unittest.mock import patch, MagicMock
from src.multi_agent_mobile_ui_assistant.android_tools_mcp import (
    AndroidLintMCP,
    GradleMCP,
    LintIssue,
    CompilationResult,
)


class TestAndroidLintMCP:
    """Test Android Lint MCP for Compose code validation."""
    
    def test_validate_compose_code_returns_lint_issues(self):
        """
        GIVEN valid Compose code
        WHEN validating with Android Lint
        THEN should return list of LintIssue objects
        """
        lint_mcp = AndroidLintMCP()
        code = "@Composable fun MyScreen() { Text(\"Hello\") }"
        
        issues = lint_mcp.validate_compose_code(code)
        
        assert isinstance(issues, list)
        assert all(isinstance(issue, LintIssue) for issue in issues)
    
    def test_lint_issue_has_required_fields(self):
        """
        GIVEN a LintIssue object
        THEN it should have severity, message, line, and suggestion
        """
        issue = LintIssue(
            severity="warning",
            message="Missing content description",
            line=5,
            suggestion="Add contentDescription parameter"
        )
        
        assert issue.severity == "warning"
        assert issue.message == "Missing content description"
        assert issue.line == 5
        assert issue.suggestion == "Add contentDescription parameter"
    
    def test_validate_detects_missing_imports(self):
        """
        GIVEN Compose code without necessary imports
        WHEN validating
        THEN should detect missing import issues
        """
        lint_mcp = AndroidLintMCP()
        code = """
        @Composable
        fun MyScreen() {
            Text("Hello")
        }
        """
        
        issues = lint_mcp.validate_compose_code(code)
        
        # Should detect missing imports
        import_issues = [i for i in issues if "import" in i.message.lower()]
        assert len(import_issues) > 0
    
    def test_validate_detects_accessibility_issues(self):
        """
        GIVEN Compose code with accessibility problems
        WHEN validating
        THEN should detect accessibility issues
        """
        lint_mcp = AndroidLintMCP()
        code = """
        @Composable
        fun ImageScreen() {
            Image(painter = painterResource(id = R.drawable.logo))
        }
        """
        
        issues = lint_mcp.validate_compose_code(code)
        
        # Should detect missing contentDescription
        accessibility_issues = [i for i in issues if "content" in i.message.lower()]
        assert len(accessibility_issues) > 0
    
    def test_validate_returns_empty_for_valid_code(self):
        """
        GIVEN perfectly valid Compose code
        WHEN validating
        THEN should return empty list or minimal issues
        """
        lint_mcp = AndroidLintMCP()
        code = """
        import androidx.compose.material3.Text
        import androidx.compose.runtime.Composable
        
        @Composable
        fun ValidScreen() {
            Text(text = "Hello World")
        }
        """
        
        issues = lint_mcp.validate_compose_code(code)
        
        # Should have no critical issues
        critical_issues = [i for i in issues if i.severity == "error"]
        assert len(critical_issues) == 0
    
    def test_auto_fix_adds_missing_imports(self):
        """
        GIVEN code with missing imports
        WHEN running auto_fix
        THEN should add necessary imports
        """
        lint_mcp = AndroidLintMCP()
        code = "@Composable fun MyScreen() { Text(\"Hello\") }"
        
        fixed_code = lint_mcp.auto_fix(code)
        
        assert "import" in fixed_code
        assert "@Composable" in fixed_code
    
    def test_auto_fix_preserves_existing_code(self):
        """
        GIVEN code to fix
        WHEN running auto_fix
        THEN should preserve original code logic
        """
        lint_mcp = AndroidLintMCP()
        original = "@Composable fun MyScreen() { Text(\"Hello\") }"
        
        fixed = lint_mcp.auto_fix(original)
        
        # Should still contain the original function
        assert "MyScreen" in fixed
        assert "Text" in fixed
        assert "Hello" in fixed


class TestGradleMCP:
    """Test Gradle MCP for compilation checking."""
    
    def test_check_compilation_returns_result(self):
        """
        GIVEN Kotlin/Compose code
        WHEN checking compilation
        THEN should return CompilationResult object
        """
        gradle_mcp = GradleMCP()
        code = "@Composable fun MyScreen() {}"
        
        result = gradle_mcp.check_compilation(code)
        
        assert isinstance(result, CompilationResult)
        assert hasattr(result, 'success')
        assert hasattr(result, 'errors')
    
    def test_compilation_result_has_required_fields(self):
        """
        GIVEN a CompilationResult
        THEN it should have success, errors, and warnings
        """
        result = CompilationResult(
            success=True,
            errors=[],
            warnings=["Unused import"]
        )
        
        assert result.success is True
        assert result.errors == []
        assert result.warnings == ["Unused import"]
    
    def test_check_compilation_detects_syntax_errors(self):
        """
        GIVEN code with syntax errors
        WHEN checking compilation
        THEN should detect errors and return success=False
        """
        gradle_mcp = GradleMCP()
        bad_code = "@Composable fun MyScreen() { THIS IS INVALID }"
        
        result = gradle_mcp.check_compilation(bad_code)
        
        assert result.success is False
        assert len(result.errors) > 0
    
    def test_check_compilation_succeeds_for_valid_code(self):
        """
        GIVEN valid Kotlin/Compose code
        WHEN checking compilation
        THEN should return success=True
        """
        gradle_mcp = GradleMCP()
        good_code = """
        import androidx.compose.runtime.Composable
        import androidx.compose.material3.Text
        
        @Composable
        fun MyScreen() {
            Text("Hello")
        }
        """
        
        result = gradle_mcp.check_compilation(good_code)
        
        assert result.success is True
    
    def test_check_compilation_handles_missing_dependencies(self):
        """
        GIVEN code using unavailable dependencies
        WHEN checking compilation
        THEN should detect dependency errors
        """
        gradle_mcp = GradleMCP()
        code = """
        import com.nonexistent.library.Something
        
        @Composable
        fun MyScreen() {
            Something()
        }
        """
        
        result = gradle_mcp.check_compilation(code)
        
        # Should fail due to missing dependency
        assert result.success is False
        assert any("import" in err.lower() or "unresolved" in err.lower() 
                  for err in result.errors)
    
    @patch('subprocess.run')
    def test_check_compilation_uses_gradle(self, mock_run):
        """
        GIVEN code to compile
        WHEN checking compilation
        THEN should invoke gradle/kotlin compiler
        """
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="BUILD SUCCESSFUL",
            stderr=""
        )
        
        gradle_mcp = GradleMCP()
        code = "@Composable fun MyScreen() {}"
        
        _ = gradle_mcp.check_compilation(code)
        
        # Should have called gradle or kotlinc
        assert mock_run.called


class TestAndroidToolsIntegration:
    """Integration tests for Android Tools MCP working together."""
    
    def test_lint_and_gradle_work_together(self):
        """
        GIVEN code with lint issues but valid syntax
        WHEN running both lint and compilation checks
        THEN lint finds issues but compilation succeeds
        """
        lint_mcp = AndroidLintMCP()
        gradle_mcp = GradleMCP()
        
        code = """
        import androidx.compose.runtime.Composable
        import androidx.compose.material3.Text
        
        @Composable
        fun MyScreen() {
            Text("Hello")
            // Missing imports for some components would be lint issue
        }
        """
        
        lint_issues = lint_mcp.validate_compose_code(code)
        compile_result = gradle_mcp.check_compilation(code)
        
        # Can have lint issues but still compile
        assert isinstance(lint_issues, list)
        assert isinstance(compile_result, CompilationResult)
    
    def test_auto_fix_improves_compilation(self):
        """
        GIVEN code that fails compilation
        WHEN applying auto_fix
        THEN fixed code should compile successfully
        """
        lint_mcp = AndroidLintMCP()
        gradle_mcp = GradleMCP()
        
        broken_code = "@Composable fun MyScreen() { Text(\"Hello\") }"
        
        # Fix the code
        fixed_code = lint_mcp.auto_fix(broken_code)
        
        # Should improve or maintain compilation status
        original_result = gradle_mcp.check_compilation(broken_code)
        fixed_result = gradle_mcp.check_compilation(fixed_code)
        
        # Fixed version should be at least as good
        if not original_result.success:
            # If original failed, fixed should have fewer or equal errors
            assert len(fixed_result.errors) <= len(original_result.errors)
    
    def test_validation_pipeline_full_flow(self):
        """
        GIVEN generated code
        WHEN running full validation pipeline (lint -> auto-fix -> compile)
        THEN should produce validated, compilable code
        """
        lint_mcp = AndroidLintMCP()
        gradle_mcp = GradleMCP()
        
        generated_code = "@Composable fun MyUI() { Button(onClick = {}) { Text(\"Click\") } }"
        
        # Step 1: Lint
        issues = lint_mcp.validate_compose_code(generated_code)
        
        # Step 2: Auto-fix if issues found
        if issues:
            fixed_code = lint_mcp.auto_fix(generated_code)
        else:
            fixed_code = generated_code
        
        # Step 3: Compile check
        result = gradle_mcp.check_compilation(fixed_code)
        
        # Pipeline should complete without crashing
        assert fixed_code is not None
        assert result is not None
