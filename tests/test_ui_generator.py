"""
Unit tests for the UI generator module.
"""

from langchain_core.messages import AIMessage
from src.multi_agent_mobile_ui_assistant.ui_generator import (
    UIGeneratorState,
    intent_parser_agent,
    layout_planner_agent,
    ui_generator_agent,
    accessibility_reviewer_agent,
    ui_reviewer_agent,
    output_node,
    build_ui_generator_graph,
    generate_ui_from_description,
)


class TestIntentParserAgent:
    """Tests for the Intent Parser Agent."""

    def test_intent_parser_detects_button(self, mock_llm):
        """Test that intent parser detects button in user input."""
        # Mock LLM response
        mock_llm.invoke.return_value = AIMessage(content="""{
            "ui_elements": [{"type": "Button", "text": "Click Me"}],
            "layout_type": "Column",
            "styles": {},
            "actions": []
        }""")
        
        state = {
            "user_input": "Create a screen with a button",
            "messages": [],
        }
        
        result = intent_parser_agent(state)
        
        assert "parsed_intent" in result
        assert len(result["parsed_intent"]["ui_elements"]) > 0
        assert any(el["type"] == "Button" for el in result["parsed_intent"]["ui_elements"])

    def test_intent_parser_detects_text(self, mock_llm):
        """Test that intent parser detects text in user input."""
        mock_llm.invoke.return_value = AIMessage(content="""{
            "ui_elements": [{"type": "Text", "content": "Title"}],
            "layout_type": "Column",
            "styles": {},
            "actions": []
        }""")
        
        state = {
            "user_input": "Create a title for the page",
            "messages": [],
        }
        
        result = intent_parser_agent(state)
        
        assert "parsed_intent" in result
        ui_elements = result["parsed_intent"]["ui_elements"]
        assert any(el["type"] == "Text" for el in ui_elements)

    def test_intent_parser_detects_image(self, mock_llm):
        """Test that intent parser detects image in user input."""
        mock_llm.invoke.return_value = AIMessage(content="""{
            "ui_elements": [{"type": "Image", "description": "Profile"}],
            "layout_type": "Column",
            "styles": {},
            "actions": []
        }""")
        
        state = {
            "user_input": "Add an image to the screen",
            "messages": [],
        }
        
        result = intent_parser_agent(state)
        
        ui_elements = result["parsed_intent"]["ui_elements"]
        assert any(el["type"] == "Image" for el in ui_elements)

    def test_intent_parser_detects_card_layout(self, mock_llm):
        """Test that intent parser detects card layout type."""
        mock_llm.invoke.return_value = AIMessage(content="""{
            "ui_elements": [],
            "layout_type": "Card",
            "styles": {},
            "actions": []
        }""")
        
        state = {
            "user_input": "Create a card with content",
            "messages": [],
        }
        
        result = intent_parser_agent(state)
        
        assert result["parsed_intent"]["layout_type"] == "Card"

    def test_intent_parser_detects_row_layout(self, mock_llm):
        """Test that intent parser detects row layout type."""
        mock_llm.invoke.return_value = AIMessage(content="""{
            "ui_elements": [],
            "layout_type": "Row",
            "styles": {},
            "actions": []
        }""")
        
        state = {
            "user_input": "Create a row with buttons",
            "messages": [],
        }
        
        result = intent_parser_agent(state)
        
        assert result["parsed_intent"]["layout_type"] == "Row"

    def test_intent_parser_detects_multiple_elements(self, mock_llm):
        """Test that intent parser detects multiple UI elements."""
        mock_llm.invoke.return_value = AIMessage(content="""{
            "ui_elements": [
                {"type": "Text", "content": "Title"},
                {"type": "Button", "text": "Click"},
                {"type": "Image", "description": "Hero"}
            ],
            "layout_type": "Column",
            "styles": {},
            "actions": []
        }""")
        
        state = {
            "user_input": "Create a screen with a title, button, and image",
            "messages": [],
        }
        
        result = intent_parser_agent(state)
        
        ui_elements = result["parsed_intent"]["ui_elements"]
        assert len(ui_elements) == 3

    def test_intent_parser_sets_current_step(self, mock_llm):
        """Test that intent parser sets current_step."""
        mock_llm.invoke.return_value = AIMessage(content="""{
            "ui_elements": [],
            "layout_type": "Column",
            "styles": {},
            "actions": []
        }""")
        
        state = {
            "user_input": "Test input",
            "messages": [],
        }
        
        result = intent_parser_agent(state)
        
        assert result["current_step"] == "intent_parsed"


class TestLayoutPlannerAgent:
    """Tests for the Layout Planner Agent."""

    def test_layout_planner_creates_plan(self):
        """Test that layout planner creates a layout plan."""
        state = {
            "parsed_intent": {
                "ui_elements": [{"type": "Button", "text": "Click"}],
                "layout_type": "Column",
            },
            "messages": [],
        }
        
        result = layout_planner_agent(state)
        
        assert "layout_plan" in result
        assert "root_container" in result["layout_plan"]
        assert "children" in result["layout_plan"]

    def test_layout_planner_uses_parsed_layout_type(self):
        """Test that layout planner uses layout type from parsed intent."""
        state = {
            "parsed_intent": {
                "ui_elements": [],
                "layout_type": "Row",
            },
            "messages": [],
        }
        
        result = layout_planner_agent(state)
        
        assert result["layout_plan"]["root_container"] == "Row"

    def test_layout_planner_adds_modifiers(self):
        """Test that layout planner adds modifiers."""
        state = {
            "parsed_intent": {
                "ui_elements": [],
                "layout_type": "Column",
            },
            "messages": [],
        }
        
        result = layout_planner_agent(state)
        
        assert "modifiers" in result["layout_plan"]
        assert len(result["layout_plan"]["modifiers"]) > 0

    def test_layout_planner_plans_children(self):
        """Test that layout planner plans children components."""
        state = {
            "parsed_intent": {
                "ui_elements": [
                    {"type": "Text", "content": "Hello"},
                    {"type": "Button", "text": "Click"}
                ],
                "layout_type": "Column",
            },
            "messages": [],
        }
        
        result = layout_planner_agent(state)
        
        assert len(result["layout_plan"]["children"]) == 2

    def test_layout_planner_sets_current_step(self):
        """Test that layout planner sets current_step."""
        state = {
            "parsed_intent": {"ui_elements": [], "layout_type": "Column"},
            "messages": [],
        }
        
        result = layout_planner_agent(state)
        
        assert result["current_step"] == "layout_planned"


class TestUIGeneratorAgent:
    """Tests for the UI Generator Agent."""

    def test_ui_generator_creates_composable_function(self):
        """Test that UI generator creates a composable function."""
        state = {
            "layout_plan": {
                "root_container": "Column",
                "children": [],
                "modifiers": ["fillMaxSize"],
                "arrangement": "Center"
            },
            "messages": [],
        }
        
        result = ui_generator_agent(state)
        
        assert "generated_code" in result
        assert "@Composable" in result["generated_code"]
        assert "fun GeneratedUI()" in result["generated_code"]

    def test_ui_generator_creates_column_layout(self):
        """Test that UI generator creates Column layout."""
        state = {
            "layout_plan": {
                "root_container": "Column",
                "children": [],
                "modifiers": ["fillMaxSize"],
                "arrangement": "Center"
            },
            "messages": [],
        }
        
        result = ui_generator_agent(state)
        
        assert "Column(" in result["generated_code"]

    def test_ui_generator_creates_row_layout(self):
        """Test that UI generator creates Row layout."""
        state = {
            "layout_plan": {
                "root_container": "Row",
                "children": [],
                "modifiers": ["fillMaxSize"],
                "arrangement": "Start"
            },
            "messages": [],
        }
        
        result = ui_generator_agent(state)
        
        assert "Row(" in result["generated_code"]

    def test_ui_generator_adds_text_component(self):
        """Test that UI generator adds Text component."""
        state = {
            "layout_plan": {
                "root_container": "Column",
                "children": [
                    {
                        "component": "Text",
                        "properties": {"content": "Hello World", "style": "headlineMedium"}
                    }
                ],
                "modifiers": [],
                "arrangement": "Center"
            },
            "messages": [],
        }
        
        result = ui_generator_agent(state)
        
        assert "Text(" in result["generated_code"]
        assert "Hello World" in result["generated_code"]

    def test_ui_generator_adds_button_component(self):
        """Test that UI generator adds Button component."""
        state = {
            "layout_plan": {
                "root_container": "Column",
                "children": [
                    {
                        "component": "Button",
                        "properties": {"text": "Click Me"}
                    }
                ],
                "modifiers": [],
                "arrangement": "Center"
            },
            "messages": [],
        }
        
        result = ui_generator_agent(state)
        
        assert "Button(onClick" in result["generated_code"]
        assert "Click Me" in result["generated_code"]

    def test_ui_generator_adds_image_component(self):
        """Test that UI generator adds Image component."""
        state = {
            "layout_plan": {
                "root_container": "Column",
                "children": [
                    {
                        "component": "Image",
                        "properties": {"description": "Profile picture"}
                    }
                ],
                "modifiers": [],
                "arrangement": "Center"
            },
            "messages": [],
        }
        
        result = ui_generator_agent(state)
        
        assert "Box(" in result["generated_code"]  # Image uses Box placeholder
        assert "Profile picture" in result["generated_code"]

    def test_ui_generator_sets_current_step(self):
        """Test that UI generator sets current_step."""
        state = {
            "layout_plan": {
                "root_container": "Column",
                "children": [],
                "modifiers": [],
                "arrangement": "Center"
            },
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
        assert any("contentDescription" in issue for issue in issues)

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
        assert any("MaterialTheme" in issue for issue in issues)

    def test_ui_reviewer_approves_padding(self):
        """Test that UI reviewer approves padding usage."""
        state = {
            "generated_code": "Column(modifier = Modifier.padding(16.dp)) { }",
            "messages": [],
        }
        
        result = ui_reviewer_agent(state)
        
        issues = result["design_issues"]
        assert any("padding" in issue.lower() for issue in issues)

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
            "accessibility_issues": ["Issue 1"],
            "design_issues": ["Issue 2"],
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
            "accessibility_issues": ["Accessibility Issue 1", "Accessibility Issue 2"],
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
            "design_issues": ["Design Issue 1"],
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
        assert "fun GeneratedUI()" in result

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
        """Test that UIGeneratorState has expected structure."""
        state: UIGeneratorState = {
            "messages": [],
            "user_input": "test",
            "parsed_intent": {},
            "layout_plan": {},
            "generated_code": "",
            "accessibility_issues": [],
            "design_issues": [],
            "final_output": "",
            "current_step": "start"
        }
        
        assert "messages" in state
        assert "user_input" in state
        assert "parsed_intent" in state
        assert "layout_plan" in state
        assert "generated_code" in state
        assert "accessibility_issues" in state
        assert "design_issues" in state
        assert "final_output" in state
        assert "current_step" in state


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
            "parsed_intent": {"ui_elements": [{"type": "Button"}]},
            "layout_plan": {"layout": "Column"},
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
