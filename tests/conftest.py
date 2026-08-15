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
    with patch('src.multi_agent_mobile_ui_assistant.agents.generator.get_default_llm') as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def sample_ui_generator_state():
    """Fixture providing a sample UIGeneratorState."""
    return {
        "messages": [],
        "user_input": "Create a simple UI",
        "generated_code": "",
        "accessibility_issues": [],
        "design_issues": [],
        "final_output": "",
        "current_step": "start",
        "github_examples": [],
        "project_context": {},
        "multi_file": False,
        "validate_code": False,
        "use_llm_generation": False,
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
