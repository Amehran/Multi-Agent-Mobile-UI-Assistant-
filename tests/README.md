# Unit Tests for Multi-Agent Mobile UI Assistant

This directory contains comprehensive unit tests for the Multi-Agent Mobile UI Assistant project.

## Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Pytest configuration and shared fixtures
├── test_example.py            # Tests for basic LangGraph example
├── test_agent_example.py      # Tests for advanced agent example
└── test_ui_generator.py       # Tests for UI generator module
```

## Test Coverage

### test_example.py
Tests for the basic LangGraph workflow (`src/multi_agent_mobile_ui_assistant/example.py`):
- **TestNodeFunctions**: Tests for individual node functions (node_1, node_2, node_3)
- **TestRouting**: Tests for conditional routing logic
- **TestGraphBuilder**: Tests for graph building and execution
- **TestStateType**: Tests for State TypedDict structure

### test_agent_example.py
Tests for the advanced agent workflow (`src/multi_agent_mobile_ui_assistant/agent_example.py`):
- **TestAgentNodes**: Tests for agent node functions (analyze_task, execute_tool_1, execute_tool_2, synthesize_results)
- **TestConditionalRouting**: Tests for agent conditional routing
- **TestGraphBuilder**: Tests for agent graph building and execution
- **TestAgentStateType**: Tests for AgentState TypedDict structure

### test_ui_generator.py
Tests for the UI generator system (`src/multi_agent_mobile_ui_assistant/ui_generator.py`):
- **TestIntentParserAgent**: Tests for natural language parsing
- **TestLayoutPlannerAgent**: Tests for layout planning
- **TestUIGeneratorAgent**: Tests for Compose code generation
- **TestAccessibilityReviewerAgent**: Tests for accessibility validation
- **TestUIReviewerAgent**: Tests for Material 3 design review
- **TestOutputNode**: Tests for final output generation
- **TestGraphBuilder**: Tests for UI generator graph
- **TestGenerateUIFromDescription**: Integration tests for full workflow
- **TestUIGeneratorStateType**: Tests for UIGeneratorState structure

## Running Tests

### Install Test Dependencies

```bash
# Install the package with dev dependencies
pip install -e ".[dev]"
```

### Run All Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=src/multi_agent_mobile_ui_assistant --cov-report=term-missing

# Run with HTML coverage report
pytest --cov=src/multi_agent_mobile_ui_assistant --cov-report=html
```

### Run Specific Test Files

```bash
# Run basic example tests
pytest tests/test_example.py

# Run agent example tests
pytest tests/test_agent_example.py

# Run UI generator tests
pytest tests/test_ui_generator.py
```

### Run Specific Test Classes

```bash
# Run specific test class
pytest tests/test_ui_generator.py::TestIntentParserAgent

# Run specific test method
pytest tests/test_ui_generator.py::TestIntentParserAgent::test_intent_parser_detects_button
```

### Additional Options

```bash
# Run tests and stop on first failure
pytest -x

# Run tests with detailed output
pytest -vv

# Run tests in parallel (requires pytest-xdist)
pytest -n auto

# Show local variables in tracebacks
pytest -l
```

## Test Fixtures

The `conftest.py` file provides shared fixtures:

- `sample_ui_generator_state`: Sample UIGeneratorState
- `sample_agent_state`: Sample AgentState
- `sample_basic_state`: Sample basic State
- `sample_parsed_intent`: Sample parsed intent data
- `sample_layout_plan`: Sample layout plan
- `sample_generated_code`: Sample Compose code

## Coverage Goals

- Target: 80%+ code coverage
- All public functions should have tests
- Edge cases and error conditions should be tested
- Integration tests for complete workflows

## Writing New Tests

When adding new tests:

1. Follow the existing test structure
2. Use descriptive test names (test_what_when_expected)
3. Use AAA pattern: Arrange, Act, Assert
4. Keep tests isolated and independent
5. Use fixtures for common setup
6. Add docstrings to explain what's being tested

Example:
```python
def test_function_name_when_condition_then_expected_result(self):
    """Test that function_name does X when Y condition is met."""
    # Arrange
    state = {"input": "test"}
    
    # Act
    result = function_name(state)
    
    # Assert
    assert result["output"] == "expected"
```

## Continuous Integration

These tests are designed to run in CI/CD pipelines. Ensure all tests pass before merging code.

## Coverage Reports

After running tests with coverage, view the HTML report:

```bash
# Generate coverage report
pytest --cov=src/multi_agent_mobile_ui_assistant --cov-report=html

# Open the report in browser
open htmlcov/index.html
```
