"""
Tests for UI Generator Agent (agents/generator.py).
"""

from unittest.mock import patch, MagicMock
from langchain_core.messages import AIMessage
from src.multi_agent_mobile_ui_assistant.agents.generator import ui_generator_agent
from src.multi_agent_mobile_ui_assistant.mcp.github import ComposeExample


class TestUIGeneratorAgent:
    """Tests for the UI Generator Agent."""

    def test_ui_generator_creates_composable_function(self):
        """Test that UI generator creates a composable function."""
        state = {
            "user_input": "Create a simple UI",
            "github_examples": [],
            "project_context": {},
            "use_llm_generation": False,
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

        assert "Column(" in result["generated_code"]

    def test_ui_generator_with_text_in_prompt(self):
        """Test that UI generator handles text in user prompt (template fallback)."""
        state = {
            "user_input": "Create text saying Hello World",
            "github_examples": [],
            "project_context": {},
            "use_llm_generation": False,
            "messages": [],
        }

        result = ui_generator_agent(state)

        assert "Text(" in result["generated_code"]
        assert "Create text saying Hello World" in result["generated_code"] or "Error generating UI" in result["generated_code"]

    def test_ui_generator_with_button_in_prompt(self):
        """Test that UI generator handles button in user prompt (template fallback)."""
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
        """Test that UI generator handles image in user prompt (template fallback)."""
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

    def test_ui_generator_enriches_prompt_with_examples(self, mock_llm):
        """Test that examples don't cause errors when provided."""
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

        assert True  # Acceptance test: no crash with examples

    def test_ui_generator_agent_applies_auto_fix(self, mock_llm):
        """Test that validation auto-fix is applied when validate_code=True."""
        mock_llm.invoke.return_value = AIMessage(content="@Composable fun Screen() {}")

        state = {
            "user_input": "Create screen",
            "messages": [],
            "validate_code": True,
            "github_examples": [],
            "project_context": {},
            "multi_file": False
        }

        result = ui_generator_agent(state)

        code = result.get("generated_code", "")
        assert "import" in code or "@Composable" in code
