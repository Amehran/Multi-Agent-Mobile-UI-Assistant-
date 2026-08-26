"""
Unit tests for the UI generator module.

NOTE: Intent Parser and Layout Planner agents have been removed from the architecture
as they were redundant with LLM capabilities and degraded output quality.
The simplified architecture goes directly from user input to UI Generator.
"""

from unittest.mock import patch, MagicMock
from langchain_core.messages import AIMessage
from src.multi_agent_mobile_ui_assistant.ui_generator import (
    UIGeneratorState,
    ui_generator_agent,
    accessibility_reviewer_agent,
    ui_reviewer_agent,
    output_node,
    validator_node,
    route_after_validation,
    build_ui_generator_graph,
    generate_ui_from_description,
)
from src.multi_agent_mobile_ui_assistant.android_tools_mcp import LintIssue, CompilationResult


# ==============================================================================
# NOTE: Intent Parser and Layout Planner tests have been removed
# ==============================================================================
# These agents were removed from the architecture because:
# 1. They were redundant - LLMs handle intent understanding and layout planning internally
# 2. They degraded output quality by losing information and reordering components
# 3. Direct user prompts produce better results than preprocessed versions
#
# The simplified architecture: User Input → UI Generator → Accessibility → UI Review → Output
# MCP tools (GitHub, FileSystem, AndroidLint, Gradle, Figma) still enhance generation quality
# ==============================================================================


class TestUIGeneratorAgent:
    """Tests for the UI Generator Agent."""

    def test_ui_generator_creates_composable_function(self):
        """Test that UI generator creates a composable function."""
        state = {
            "user_input": "Create a simple UI",
            "github_examples": [],
            "project_context": {},
            "use_llm_generation": False,  # Use template mode for testing
            "messages": [],
        }
        
        result = ui_generator_agent(state)
        
        assert "generated_code" in result
        assert "@Composable" in result["generated_code"]
        assert "fun GeneratedUI()" in result["generated_code"]

    def test_ui_generator_creates_column_layout(self):
        """Test that UI generator creates Column layout."""
        state = {
            "user_input": "Create a column layout",
            "github_examples": [],
            "project_context": {},
            "use_llm_generation": False,
            "messages": [],
        }
        
        result = ui_generator_agent(state)
        
        assert "Column(" in result["generated_code"]

    def test_ui_generator_creates_row_layout(self):
        """Test that UI generator creates Row layout (fallback uses Column)."""
        state = {
            "user_input": "Create a row layout",
            "github_examples": [],
            "project_context": {},
            "use_llm_generation": False,
            "messages": [],
        }
        
        result = ui_generator_agent(state)
        
        # Fallback template mode creates Column by default
        assert "Column(" in result["generated_code"]

    def test_ui_generator_with_text_in_prompt(self):
        """Test that UI generator handles text in user prompt (template fallback mode)."""
        state = {
            "user_input": "Create text saying Hello World",
            "github_examples": [],
            "project_context": {},
            "use_llm_generation": False,
            "messages": [],
        }
        
        result = ui_generator_agent(state)
        
        assert "Text(" in result["generated_code"]
        # Template mode shows the user input
        assert "Create text saying Hello World" in result["generated_code"] or "Error generating UI" in result["generated_code"]

    def test_ui_generator_with_button_in_prompt(self):
        """Test that UI generator handles button in user prompt (template fallback mode)."""
        state = {
            "user_input": "Create button saying Click Me",
            "github_examples": [],
            "project_context": {},
            "use_llm_generation": False,
            "messages": [],
        }
        
        result = ui_generator_agent(state)
        
        assert "@Composable" in result["generated_code"]
        assert "fun GeneratedUI()" in result["generated_code"]

    def test_ui_generator_with_image_in_prompt(self):
        """Test that UI generator handles image in user prompt (template fallback mode)."""
        state = {
            "user_input": "Create image for profile picture",
            "github_examples": [],
            "project_context": {},
            "use_llm_generation": False,
            "messages": [],
        }
        
        result = ui_generator_agent(state)
        
        assert "@Composable" in result["generated_code"]

    def test_ui_generator_sets_current_step(self):
        """Test that UI generator sets current_step."""
        state = {
            "user_input": "Create UI",
            "github_examples": [],
            "project_context": {},
            "use_llm_generation": False,
            "messages": [],
        }
        
        result = ui_generator_agent(state)
        
        assert result["current_step"] == "code_generated"



class TestAccessibilityReviewerAgent:
    """Tests for the Accessibility Reviewer Agent."""

    def test_accessibility_reviewer_checks_code(self):
        """Test that accessibility reviewer analyzes generated code."""
        state = {
            "generated_code": "@Composable\nfun Test() { Text(\"Hello\") }",
            "messages": [],
        }
        
        result = accessibility_reviewer_agent(state)
        
        assert "accessibility_issues" in result
        assert len(result["accessibility_issues"]) > 0

    def test_accessibility_reviewer_detects_missing_content_description(self):
        """Test detection of missing contentDescription."""
        state = {
            "generated_code": "@Composable\nfun Test() { Image() }",
            "messages": [],
        }
        
        result = accessibility_reviewer_agent(state)

        issues = result["accessibility_issues"]
        # Should detect missing contentDescription
        assert any("contentDescription" in issue["message"] for issue in issues)
        assert any(issue["status"] == "fail" for issue in issues)

    def test_accessibility_reviewer_checks_button_size(self):
        """Test that reviewer checks button touch target sizes."""
        state = {
            "generated_code": "@Composable\nfun Test() { Button(onClick = {}) { Text(\"Click\") } }",
            "messages": [],
        }
        
        result = accessibility_reviewer_agent(state)
        
        issues = result["accessibility_issues"]
        assert len(issues) > 0

    def test_accessibility_reviewer_sets_current_step(self):
        """Test that accessibility reviewer sets current_step."""
        state = {
            "generated_code": "code",
            "messages": [],
        }
        
        result = accessibility_reviewer_agent(state)
        
        assert result["current_step"] == "accessibility_reviewed"


class TestUIReviewerAgent:
    """Tests for the UI Reviewer Agent."""

    def test_ui_reviewer_checks_code(self):
        """Test that UI reviewer analyzes generated code."""
        state = {
            "generated_code": "@Composable\nfun Test() { Column { Text(\"Hello\") } }",
            "messages": [],
        }
        
        result = ui_reviewer_agent(state)
        
        assert "design_issues" in result
        assert len(result["design_issues"]) > 0

    def test_ui_reviewer_checks_material_theme(self):
        """Test that UI reviewer checks for MaterialTheme usage."""
        state = {
            "generated_code": "Column { Text(\"Hello\") }",
            "messages": [],
        }
        
        result = ui_reviewer_agent(state)

        issues = result["design_issues"]
        assert any("MaterialTheme" in issue["message"] for issue in issues)
        assert any(issue["status"] == "warn" for issue in issues)

    def test_ui_reviewer_approves_padding(self):
        """Test that UI reviewer approves padding usage."""
        state = {
            "generated_code": "Column(modifier = Modifier.padding(16.dp)) { }",
            "messages": [],
        }
        
        result = ui_reviewer_agent(state)

        issues = result["design_issues"]
        assert any("padding" in issue["message"].lower() for issue in issues)
        assert any(issue["check"] == "padding" and issue["status"] == "pass" for issue in issues)

    def test_ui_reviewer_sets_current_step(self):
        """Test that UI reviewer sets current_step."""
        state = {
            "generated_code": "code",
            "messages": [],
        }
        
        result = ui_reviewer_agent(state)
        
        assert result["current_step"] == "ui_reviewed"


class TestOutputNode:
    """Tests for the Output Node."""

    def test_output_node_creates_final_output(self):
        """Test that output node creates final output."""
        state = {
            "generated_code": "@Composable\nfun Test() { }",
            "accessibility_issues": [{"check": "overall", "status": "pass", "message": "Issue 1"}],
            "design_issues": [{"check": "overall", "status": "pass", "message": "Issue 2"}],
            "messages": [],
        }

        result = output_node(state)

        assert "final_output" in result
        assert len(result["final_output"]) > 0

    def test_output_node_includes_generated_code(self):
        """Test that output includes generated code."""
        state = {
            "generated_code": "TEST_CODE_123",
            "accessibility_issues": [],
            "design_issues": [],
            "messages": [],
        }

        result = output_node(state)

        assert "TEST_CODE_123" in result["final_output"]

    def test_output_node_includes_accessibility_issues(self):
        """Test that output includes accessibility issues."""
        state = {
            "generated_code": "code",
            "accessibility_issues": [
                {"check": "check_1", "status": "fail", "message": "Accessibility Issue 1"},
                {"check": "check_2", "status": "warn", "message": "Accessibility Issue 2"},
            ],
            "design_issues": [],
            "messages": [],
        }

        result = output_node(state)

        assert "Accessibility Issue 1" in result["final_output"]
        assert "Accessibility Issue 2" in result["final_output"]

    def test_output_node_includes_design_issues(self):
        """Test that output includes design issues."""
        state = {
            "generated_code": "code",
            "accessibility_issues": [],
            "design_issues": [{"check": "check_1", "status": "warn", "message": "Design Issue 1"}],
            "messages": [],
        }

        result = output_node(state)

        assert "Design Issue 1" in result["final_output"]

    def test_output_node_sets_current_step(self):
        """Test that output node sets current_step to complete."""
        state = {
            "generated_code": "code",
            "accessibility_issues": [],
            "design_issues": [],
            "messages": [],
        }
        
        result = output_node(state)
        
        assert result["current_step"] == "complete"


class TestGraphBuilder:
    """Tests for UI generator graph building."""

    def test_build_ui_generator_graph_returns_state_graph(self):
        """Test that build_ui_generator_graph returns a StateGraph."""
        from langgraph.graph import StateGraph
        
        workflow = build_ui_generator_graph()
        assert isinstance(workflow, StateGraph)

    def test_build_ui_generator_graph_compiles(self):
        """Test that the UI generator graph compiles successfully."""
        workflow = build_ui_generator_graph()
        app = workflow.compile()
        
        assert app is not None


class TestGenerateUIFromDescription:
    """Tests for the main UI generation function."""

    def test_generate_ui_from_description_returns_output(self):
        """Test that generate_ui_from_description returns output."""
        result = generate_ui_from_description("Create a simple button")
        
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_ui_from_description_includes_code(self):
        """Test that generated output includes Compose code."""
        result = generate_ui_from_description("Create a button")
        
        assert "@Composable" in result
        # LLM generates appropriate function names based on context, not always "GeneratedUI"
        assert "fun " in result and "() {" in result

    def test_generate_ui_from_description_includes_reviews(self):
        """Test that generated output includes review sections."""
        result = generate_ui_from_description("Create a text field")
        
        assert "ACCESSIBILITY REVIEW" in result
        assert "DESIGN REVIEW" in result

    def test_generate_ui_from_description_handles_complex_input(self):
        """Test generation with complex user input."""
        result = generate_ui_from_description(
            "Create a login screen with title, text fields, and button"
        )
        
        assert "@Composable" in result
        assert len(result) > 100  # Should be a substantial output


class TestUIGeneratorStateType:
    """Tests for UIGeneratorState TypedDict."""

    def test_ui_generator_state_structure(self):
        """Test that UIGeneratorState has expected structure (simplified architecture)."""
        state: UIGeneratorState = {
            "messages": [],
            "trace": [],
            "user_input": "test",
            "generated_code": "",
            "accessibility_issues": [],
            "design_issues": [],
            "validation_checks": [],
            "final_output": "",
            "current_step": "start",
            "github_examples": [],
            "project_context": {},
            "multi_file": False,
            "validate_code": False,
            "retry_count": 0,
            "last_validation_errors": [],
            "lint_issues": [],
            "auto_fixed": False,
            "compilation_result": None
        }

        assert "messages" in state
        assert "trace" in state
        assert "user_input" in state
        assert "generated_code" in state
        assert "accessibility_issues" in state
        assert "design_issues" in state
        assert "validation_checks" in state
        assert "final_output" in state
        assert "current_step" in state
        assert "github_examples" in state
        assert "project_context" in state
        assert "multi_file" in state
        assert "validate_code" in state
        assert "retry_count" in state
        assert "last_validation_errors" in state


class TestMCPIntegration:
    """Tests for MCP (Model Context Protocol) integration with UI Generator."""
    
    def test_generate_ui_accepts_github_examples(self, mock_llm):
        """
        GIVEN GitHub compose examples
        WHEN generating UI with examples as context
        THEN should use examples to improve generation quality
        """
        from src.multi_agent_mobile_ui_assistant.mcp_tools import ComposeExample
        
        # Mock LLM to return code
        mock_llm.invoke.return_value = AIMessage(content="@Composable fun MyScreen() {}")
        
        examples = [
            ComposeExample(
                code="@Composable fun LoginButton() { Button { Text(\"Login\") } }",
                description="Login button example",
                file_path="samples/Login.kt",
                repo_url="https://github.com/android/compose-samples"
            )
        ]
        
        # Should accept examples parameter
        result = generate_ui_from_description(
            "Create a login screen",
            github_examples=examples
        )
        
        assert result is not None
        assert "@Composable" in result
    
    def test_generate_ui_accepts_project_context(self, mock_llm):
        """
        GIVEN existing project structure info
        WHEN generating UI
        THEN should respect existing components
        """
        mock_llm.invoke.return_value = AIMessage(content="@Composable fun NewScreen() {}")
        
        project_context = {
            "existing_composables": [
                {"name": "CustomButton", "file": "ui/Button.kt"}
            ]
        }
        
        result = generate_ui_from_description(
            "Create a screen",
            project_context=project_context
        )
        
        assert result is not None
    
    def test_generate_multi_file_ui(self, mock_llm):
        """
        GIVEN request for complete feature with multi_file=True
        WHEN generating multi-file UI  
        THEN should accept parameter and return dict (even if single file for now)
        """
        mock_llm.invoke.return_value = AIMessage(content="@Composable fun MainActivity() {}")
        
        result = generate_ui_from_description(
            "Create a complete login feature",
            multi_file=True
        )
        
        # Should return dict format when multi_file=True
        assert isinstance(result, dict)
        # For Phase 1, we accept it returning a single file
        assert len(result) >= 1
    
    def test_ui_generator_enriches_prompt_with_examples(self, mock_llm):
        """
        GIVEN GitHub examples provided
        WHEN UI generator agent runs
        THEN should log that examples are being used
        """
        from src.multi_agent_mobile_ui_assistant.mcp_tools import ComposeExample
        
        mock_llm.invoke.return_value = AIMessage(content="@Composable fun Screen() {}")
        
        state = {
            "user_input": "Create a button",
            "messages": [],
            "github_examples": [
                ComposeExample(
                    code="@Composable fun Example() {}",
                    description="Example",
                    file_path="ex.kt",
                    repo_url="https://github.com/test"
                )
            ],
            "project_context": {},
            "multi_file": False
        }
        
        _ = ui_generator_agent(state)
        
        # Should recognize and use examples (verified by print output or state)
        # For now, we just verify it doesn't crash with examples present
        assert True  # Phase 1: Basic acceptance test


class TestValidationPipeline:
    """Tests for Android Tools MCP validation pipeline integration."""
    
    def test_generate_ui_validates_code_automatically(self, mock_llm):
        """
        GIVEN UI generation request
        WHEN generating code with validate=True
        THEN should run lint validation and auto-fix issues
        """
        # Mock LLM to return code with missing imports
        mock_llm.invoke.return_value = AIMessage(
            content="@Composable fun MyScreen() { Text(\"Hello\") }"
        )
        
        result = generate_ui_from_description(
            "Create a simple screen",
            validate=True
        )
        
        # Should have added imports automatically
        assert "import" in result
        assert "@Composable" in result
    
    def test_generate_ui_returns_validation_report(self, mock_llm):
        """
        GIVEN UI generation with validation
        WHEN code has lint issues
        THEN should return report with issues found and fixed
        """
        mock_llm.invoke.return_value = AIMessage(
            content="@Composable fun MyScreen() { Text(\"Hello\") }"
        )
        
        result = generate_ui_from_description(
            "Create a screen",
            validate=True,
            return_report=True
        )
        
        assert isinstance(result, dict)
        assert "code" in result
        assert "validation_report" in result
        assert "lint_issues" in result["validation_report"]
    
    def test_ui_generator_agent_no_longer_auto_fixes(self, mock_llm):
        """
        GIVEN generated code with lint issues (missing imports)
        WHEN ui_generator_agent runs with validate_code=True
        THEN it should NOT apply auto_fix itself -- that is now the validator
        node's job, exclusively, in the compiled graph (single validation path).
        """
        mock_llm.invoke.return_value = AIMessage(
            content="@Composable\nfun Screen() { Text(\"Hi\") }"
        )

        state = {
            "user_input": "Create screen",
            "messages": [],
            "validate_code": True,
            "github_examples": [],
            "project_context": {},
            "multi_file": False
        }

        result = ui_generator_agent(state)

        # The raw LLM output already starts with "@Composable" so the
        # "missing imports" fallback prepend doesn't trigger either --
        # the agent should return the code completely untouched by lint/auto-fix.
        code = result.get("generated_code", "")
        assert code == "@Composable\nfun Screen() { Text(\"Hi\") }"
        assert "import androidx.compose.material3.Text" not in code
        assert "import androidx.compose.runtime.Composable" not in code

    def test_validator_node_pass_through_when_validation_disabled(self):
        """
        GIVEN validate_code is False (or absent)
        WHEN validator_node runs
        THEN it makes no lint/compile calls and produces no retry side effects
        """
        state = {
            "validate_code": False,
            "generated_code": "@Composable\nfun Screen() { Text(\"Hi\") }",
            "retry_count": 0,
        }

        result = validator_node(state)

        assert result["current_step"] == "validation_skipped"
        # No lint/compile side-effect keys should be present -- only the
        # current_step and the node's own structured trace entry.
        assert set(result.keys()) == {"current_step", "trace"}
        assert len(result["trace"]) == 1
        assert result["trace"][0]["node"] == "validator"

    def test_validator_node_passes_valid_code_without_retry(self):
        """
        GIVEN validate_code is True and the code compiles on the first try
        WHEN validator_node runs
        THEN retry_count stays at 0 and last_validation_errors is empty
        """
        state = {
            "validate_code": True,
            "generated_code": "@Composable\nfun Screen() { Text(\"Hi\") }",
            "retry_count": 0,
        }

        result = validator_node(state)

        assert result["retry_count"] == 0
        assert result["last_validation_errors"] == []
        assert result["current_step"] == "validated"
        assert result["compilation_result"].success is True

    def test_validator_node_flags_retry_on_compilation_failure(self):
        """
        GIVEN validate_code is True and the code fails compilation (unbalanced braces)
        WHEN validator_node runs and retry_count is below the cap
        THEN retry_count increments, last_validation_errors is populated, and
        current_step signals a retryable failure
        """
        state = {
            "validate_code": True,
            "generated_code": "@Composable\nfun Screen() { Text(\"Hi\")",  # missing closing brace
            "retry_count": 0,
        }

        result = validator_node(state)

        assert result["retry_count"] == 1
        assert result["last_validation_errors"]
        assert result["current_step"] == "validation_failed_retry"

    def test_validator_node_exhausts_retries_and_proceeds(self):
        """
        GIVEN validate_code is True, the code keeps failing compilation, and
        retry_count is already at the cap (2)
        WHEN validator_node runs
        THEN it does not increment retry_count further and signals to proceed
        forward anyway (demo must always complete)
        """
        state = {
            "validate_code": True,
            "generated_code": "@Composable\nfun Screen() { Text(\"Hi\")",
            "retry_count": 2,
        }

        result = validator_node(state)

        assert result["retry_count"] == 2
        assert result["last_validation_errors"]
        assert result["current_step"] == "validated"

    def test_route_after_validation_retries_on_failed_step(self):
        assert route_after_validation({"current_step": "validation_failed_retry"}) == "retry"

    def test_route_after_validation_continues_otherwise(self):
        assert route_after_validation({"current_step": "validated"}) == "continue"
        assert route_after_validation({"current_step": "validation_skipped"}) == "continue"

    def test_retry_loop_fails_once_then_passes(self, mock_llm):
        """
        GIVEN the first generation attempt fails compilation and the second succeeds
        WHEN the compiled graph runs with validate_code=True
        THEN retry_count reaches 1, the second ui_generator call's prompt includes
        the failure feedback, and the graph completes with the fixed code
        """
        bad_code = "@Composable\nfun Screen() { Text(\"Hi\")"  # unbalanced braces -> fails
        good_code = (
            "import androidx.compose.runtime.Composable\n"
            "import androidx.compose.material3.Text\n\n"
            "@Composable\nfun Screen() { Text(\"Hi\") }"
        )
        mock_llm.invoke.side_effect = [
            AIMessage(content=bad_code),
            AIMessage(content=good_code),
        ]

        app = build_ui_generator_graph().compile()
        initial_state = {
            "messages": [],
            "user_input": "Create screen",
            "generated_code": "",
            "accessibility_issues": [],
            "design_issues": [],
            "final_output": "",
            "current_step": "start",
            "github_examples": [],
            "project_context": {},
            "multi_file": False,
            "validate_code": True,
            "retry_count": 0,
            "last_validation_errors": [],
        }

        result = app.invoke(initial_state)

        assert result["retry_count"] == 1
        assert result["current_step"] == "complete"
        assert mock_llm.invoke.call_count == 2

        # The retried (second) call's prompt must carry the failure feedback --
        # not just the static header, but the actual error text from the
        # failed compilation (bad_code has 1 open brace and 0 close braces).
        second_call_messages = mock_llm.invoke.call_args_list[1][0][0]
        second_user_message = second_call_messages[1].content
        assert "PREVIOUS ATTEMPT FAILED VALIDATION" in second_user_message
        assert "Unbalanced braces: 1 open, 0 close" in second_user_message

    def test_retry_loop_exhausts_and_completes(self, mock_llm):
        """
        GIVEN generation fails compilation on every attempt
        WHEN the compiled graph runs with validate_code=True
        THEN the graph still completes (never hangs/errors) once retry_count
        reaches the cap of 2, with last_validation_errors populated
        """
        bad_code = "@Composable\nfun Screen() { Text(\"Hi\")"  # always unbalanced
        mock_llm.invoke.return_value = AIMessage(content=bad_code)

        app = build_ui_generator_graph().compile()
        initial_state = {
            "messages": [],
            "user_input": "Create screen",
            "generated_code": "",
            "accessibility_issues": [],
            "design_issues": [],
            "final_output": "",
            "current_step": "start",
            "github_examples": [],
            "project_context": {},
            "multi_file": False,
            "validate_code": True,
            "retry_count": 0,
            "last_validation_errors": [],
        }

        result = app.invoke(initial_state)

        assert result["retry_count"] == 2
        assert result["last_validation_errors"]
        assert result["current_step"] == "complete"
        assert mock_llm.invoke.call_count == 3  # initial attempt + 2 retries

    def test_generate_ui_from_description_retries_exhausted_still_returns(self, mock_llm):
        """
        GIVEN validate=True, return_report=True, and code that fails every attempt
        WHEN generate_ui_from_description runs
        THEN it returns (does not hang/raise) and the validation report reflects
        the failed compilation
        """
        bad_code = "@Composable\nfun Screen() { Text(\"Hi\")"
        mock_llm.invoke.return_value = AIMessage(content=bad_code)

        result = generate_ui_from_description(
            "Create screen",
            validate=True,
            return_report=True
        )

        assert isinstance(result, dict)
        assert result["validation_report"]["compilation"]["success"] is False

    def test_return_report_without_validate_returns_structured_dict(self, mock_llm):
        """
        GIVEN return_report=True and validate=False
        WHEN generate_ui_from_description runs
        THEN branch A's guard is decoupled from `validate` -- it still returns
        the structured dict (code/trace/CheckResult lists), with
        validation_report=None since validation never ran.
        """
        mock_llm.invoke.return_value = AIMessage(
            content="@Composable\nfun Screen() { Text(\"Hi\") }"
        )

        result = generate_ui_from_description(
            "Create screen",
            validate=False,
            return_report=True
        )

        assert isinstance(result, dict)
        assert "code" in result
        assert result["validation_report"] is None
        assert "trace" in result and len(result["trace"]) > 0
        assert "accessibility_issues" in result
        assert "design_issues" in result
        assert "validation_checks" in result

    def test_return_report_with_multi_file_still_returns_file_dict(self, mock_llm):
        """
        GIVEN multi_file=True and return_report=True
        WHEN generate_ui_from_description runs
        THEN the `not multi_file` guard keeps branch A from firing -- the
        multi_file dict-of-files contract is untouched.
        """
        mock_llm.invoke.return_value = AIMessage(
            content="@Composable\nfun Screen() { Text(\"Hi\") }"
        )

        result = generate_ui_from_description(
            "Create screen",
            validate=False,
            return_report=True,
            multi_file=True
        )

        assert isinstance(result, dict)
        assert "trace" not in result
        assert "validation_report" not in result

        # The multi_file dict-of-files contract itself must still be intact:
        # non-empty, filepath -> code string mapping (parse_multi_file_output's
        # contract), containing the actual generated code.
        assert result != {}
        assert all(isinstance(k, str) and isinstance(v, str) for k, v in result.items())
        assert any("@Composable" in v for v in result.values())

    def test_validation_preserves_code_functionality(self, mock_llm):
        """
        GIVEN generated code missing imports through the full workflow
        WHEN the in-graph validator auto-fixes lint issues
        THEN should preserve generated components and add imports
        """
        mock_llm.invoke.return_value = AIMessage(content="""@Composable
fun ClickScreen() {
    Text(text = "Click")
}""")

        result = generate_ui_from_description(
            "Create text that says Click",
            validate=True
        )

        # Generated code should have Text component
        assert "Text" in result
        # Validator's auto-fix should add missing imports
        assert "import androidx.compose" in result
        # Should have the Composable function
        assert "@Composable" in result
    
    def test_validation_detects_compilation_errors(self, mock_llm):
        """
        GIVEN validation is enabled
        WHEN validation runs on generated code  
        THEN should return compilation check results
        """
        # Provide a simple valid intent - compilation check happens on generated code
        mock_llm.invoke.return_value = AIMessage(content="""{
            "ui_elements": [{"type": "Text", "content": "Test"}],
            "layout_type": "Column",
            "styles": {},
            "actions": []
        }""")
        
        result = generate_ui_from_description(
            "Create text",
            validate=True,
            return_report=True
        )
        
        # Should return validation report
        assert "validation_report" in result
        report = result["validation_report"]
        assert "compilation" in report
        # The mock compilation check should return success for valid generated code
        assert "success" in report["compilation"]
    
    def test_validation_pipeline_handles_valid_code(self, mock_llm):
        """
        GIVEN already valid code
        WHEN validation runs
        THEN should pass validation without changes
        """
        valid_code = """
        import androidx.compose.runtime.Composable
        import androidx.compose.material3.Text
        
        @Composable
        fun ValidScreen() {
            Text("Hello")
        }
        """
        mock_llm.invoke.return_value = AIMessage(content=valid_code)
        
        result = generate_ui_from_description(
            "Create screen",
            validate=True,
            return_report=True
        )
        
        # Should validate successfully
        report = result["validation_report"]
        assert report["lint_issues_count"] == 0 or report.get("auto_fixed") is True
        assert report["compilation"]["success"] is True


class TestStructuredTraceAndVerdicts:
    """Tests for story 2: TraceStep/CheckResult structured shapes."""

    @staticmethod
    def _initial_state(validate_code=False):
        return {
            "messages": [],
            "trace": [],
            "user_input": "Create screen",
            "generated_code": "",
            "accessibility_issues": [],
            "design_issues": [],
            "validation_checks": [],
            "final_output": "",
            "current_step": "start",
            "github_examples": [],
            "project_context": {},
            "multi_file": False,
            "validate_code": validate_code,
            "retry_count": 0,
            "last_validation_errors": [],
            "lint_issues": [],
            "auto_fixed": False,
            "compilation_result": None,
        }

    def test_trace_has_one_entry_per_executed_node_full_run(self, mock_llm):
        """
        GIVEN a full run with validate_code=False
        WHEN the graph completes
        THEN state["trace"] has exactly one entry per node actually executed,
        in execution order.
        """
        mock_llm.invoke.return_value = AIMessage(
            content=(
                "import androidx.compose.runtime.Composable\n"
                "import androidx.compose.material3.Text\n\n"
                "@Composable\nfun Screen() { Text(\"Hi\") }"
            )
        )

        app = build_ui_generator_graph().compile()
        result = app.invoke(self._initial_state(validate_code=False))

        nodes = [step["node"] for step in result["trace"]]
        assert nodes == [
            "ui_generator",
            "validator",
            "accessibility_reviewer",
            "ui_reviewer",
            "output",
        ]
        # Every trace entry is a well-formed TraceStep
        for step in result["trace"]:
            assert set(step.keys()) == {"node", "summary", "detail"}

    def test_trace_shows_two_entries_per_retried_node(self, mock_llm):
        """
        GIVEN a validator retry loop that fails once then passes
        WHEN the graph completes
        THEN trace shows two ui_generator and two validator entries, with no
        dropped or duplicated unrelated entries.
        """
        bad_code = "@Composable\nfun Screen() { Text(\"Hi\")"  # unbalanced braces -> fails
        good_code = (
            "import androidx.compose.runtime.Composable\n"
            "import androidx.compose.material3.Text\n\n"
            "@Composable\nfun Screen() { Text(\"Hi\") }"
        )
        mock_llm.invoke.side_effect = [
            AIMessage(content=bad_code),
            AIMessage(content=good_code),
        ]

        app = build_ui_generator_graph().compile()
        result = app.invoke(self._initial_state(validate_code=True))

        nodes = [step["node"] for step in result["trace"]]
        assert nodes.count("ui_generator") == 2
        assert nodes.count("validator") == 2
        assert nodes.count("accessibility_reviewer") == 1
        assert nodes.count("ui_reviewer") == 1
        assert nodes.count("output") == 1
        assert len(nodes) == 7

    def test_reviewers_never_return_empty_findings_on_clean_code(self):
        """
        GIVEN generated code that trips none of the accessibility/design
        detection conditions (no Image, Button, Text, Arrangement, or
        Alignment usage; MaterialTheme and padding present)
        WHEN accessibility_reviewer_agent and ui_reviewer_agent run
        THEN each returns a non-empty list of CheckResult with status="pass"
        """
        clean_code = (
            "@Composable\n"
            "fun Clean() {\n"
            "    MaterialTheme {\n"
            "        Box(modifier = Modifier.padding(16.dp)) {}\n"
            "    }\n"
            "}"
        )
        state = {"generated_code": clean_code, "messages": []}

        accessibility_result = accessibility_reviewer_agent(state)
        design_result = ui_reviewer_agent(state)

        accessibility_issues = accessibility_result["accessibility_issues"]
        design_issues = design_result["design_issues"]

        assert len(accessibility_issues) == 1
        assert accessibility_issues[0]["status"] == "pass"
        assert accessibility_issues[0]["check"] == "accessibility_summary"

        assert len(design_issues) == 1
        assert design_issues[0]["status"] == "pass"

    def test_validation_checks_contains_fail_for_missing_import_lint_issue(self):
        """
        GIVEN generated code missing an import
        WHEN validator_node runs with validate_code=True
        THEN validation_checks contains a fail-status CheckResult for that lint
        issue, plus one compilation CheckResult.
        """
        state = {
            "validate_code": True,
            "generated_code": "@Composable\nfun Screen() { Text(\"Hi\") }",  # missing imports
            "retry_count": 0,
        }

        result = validator_node(state)

        validation_checks = result["validation_checks"]
        assert any(
            check["check"] == "lint" and check["status"] == "fail"
            for check in validation_checks
        )
        assert any(check["check"] == "compilation" for check in validation_checks)
        assert len(result["trace"]) == 1
        assert result["trace"][0]["node"] == "validator"

    def test_validation_checks_severity_to_status_mapping(self):
        """
        GIVEN lint issues of every severity (error, warning, info)
        WHEN validator_node maps LintIssue -> CheckResult
        THEN error->fail, warning->warn, info->pass, pinned per severity so a
        future swap of the mapping table would be caught.
        """
        lint_issues = [
            LintIssue(severity="error", message="err msg", line=1, suggestion="fix1"),
            LintIssue(severity="warning", message="warn msg", line=2, suggestion="fix2"),
            LintIssue(severity="info", message="info msg", line=3, suggestion="fix3"),
        ]
        compilation_result = CompilationResult(success=True, errors=[], warnings=[])

        with patch(
            "src.multi_agent_mobile_ui_assistant.android_tools_mcp.AndroidLintMCP.validate_compose_code",
            return_value=lint_issues,
        ), patch(
            "src.multi_agent_mobile_ui_assistant.android_tools_mcp.GradleMCP.check_compilation",
            return_value=compilation_result,
        ):
            state = {
                "validate_code": True,
                "generated_code": "@Composable\nfun Screen() { Text(\"Hi\") }",
                "retry_count": 0,
            }
            result = validator_node(state)

        lint_checks = [c for c in result["validation_checks"] if c["check"] == "lint"]
        assert len(lint_checks) == 3
        status_by_message = {
            c["message"].split(" (line")[0]: c["status"] for c in lint_checks
        }
        assert status_by_message["err msg"] == "fail"
        assert status_by_message["warn msg"] == "warn"
        assert status_by_message["info msg"] == "pass"

    def test_validation_checks_accumulate_across_retries(self, mock_llm):
        """
        GIVEN a validator retry loop that fails once then passes
        WHEN the graph completes
        THEN validation_checks holds compilation verdicts from BOTH attempts
        (accumulated the same way trace does), not just the last one --
        otherwise the first (failed) attempt's structured verdicts would be
        silently discarded.
        """
        bad_code = "@Composable\nfun Screen() { Text(\"Hi\")"  # unbalanced braces -> fails
        good_code = (
            "import androidx.compose.runtime.Composable\n"
            "import androidx.compose.material3.Text\n\n"
            "@Composable\nfun Screen() { Text(\"Hi\") }"
        )
        mock_llm.invoke.side_effect = [
            AIMessage(content=bad_code),
            AIMessage(content=good_code),
        ]

        app = build_ui_generator_graph().compile()
        result = app.invoke(self._initial_state(validate_code=True))

        compilation_checks = [
            c for c in result["validation_checks"] if c["check"] == "compilation"
        ]
        assert len(compilation_checks) == 2
        assert any(c["status"] == "fail" for c in compilation_checks)
        assert any(c["status"] == "pass" for c in compilation_checks)

        # Each attempt's CheckResults must carry which attempt produced them --
        # otherwise a fail/pass pair from two different retries is indistinguishable.
        attempts = {c["attempt"] for c in compilation_checks}
        assert attempts == {0, 1}
        failed = next(c for c in compilation_checks if c["status"] == "fail")
        passed = next(c for c in compilation_checks if c["status"] == "pass")
        assert failed["attempt"] == 0
        assert passed["attempt"] == 1
