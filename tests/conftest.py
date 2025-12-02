"""
Pytest configuration and shared fixtures for tests.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture
def mock_llm():
    """Fixture providing a mocked LLM for testing without API calls."""
    with patch('src.multi_agent_mobile_ui_assistant.ui_generator.get_default_llm') as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def sample_ui_generator_state():
    """Fixture providing a sample UIGeneratorState."""
    return {
        "messages": [],
        "user_input": "Create a simple UI",
        "parsed_intent": {},
        "layout_plan": {},
        "generated_code": "",
        "accessibility_issues": [],
        "design_issues": [],
        "final_output": "",
        "current_step": "start"
    }


@pytest.fixture
def sample_agent_state():
    """Fixture providing a sample AgentState."""
    return {
        "messages": [],
        "current_task": "Test task",
        "tools_used": [],
        "is_complete": False
    }


@pytest.fixture
def sample_basic_state():
    """Fixture providing a sample basic State."""
    return {
        "messages": [],
        "step_count": 0
    }


@pytest.fixture
def sample_parsed_intent():
    """Fixture providing a sample parsed intent."""
    return {
        "ui_elements": [
            {"type": "Text", "content": "Hello", "style": "headlineMedium"},
            {"type": "Button", "text": "Click Me", "action": "onClick"}
        ],
        "layout_type": "Column",
        "styles": {},
        "actions": []
    }


@pytest.fixture
def sample_layout_plan():
    """Fixture providing a sample layout plan."""
    return {
        "root_container": "Column",
        "children": [
            {
                "component": "Text",
                "properties": {"content": "Title", "style": "headlineMedium"},
                "modifiers": []
            },
            {
                "component": "Button",
                "properties": {"text": "Submit"},
                "modifiers": []
            }
        ],
        "modifiers": ["fillMaxSize", "padding(16.dp)"],
        "arrangement": "Center"
    }


@pytest.fixture
def sample_generated_code():
    """Fixture providing sample generated Compose code."""
    return """@Composable
fun GeneratedUI() {
    Column(
        modifier = Modifier.fillMaxSize().padding(16.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = "Hello World",
            style = MaterialTheme.typography.headlineMedium
        )
        Button(onClick = { /* TODO: Add action */ }) {
            Text("Click Me")
        }
    }
}"""
