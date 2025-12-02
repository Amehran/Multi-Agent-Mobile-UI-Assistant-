# Testing Quick Reference

## Quick Start

```bash
# Install test dependencies
uv sync --extra dev

# Run all tests
uv run pytest

# Run with coverage
./run_tests.sh -c
```

## Common Commands

| Command | Description |
|---------|-------------|
| `uv run pytest` | Run all tests |
| `uv run pytest -v` | Verbose output |
| `uv run pytest -x` | Stop on first failure |
| `uv run pytest tests/test_example.py` | Run specific file |
| `uv run pytest tests/test_ui_generator.py::TestIntentParserAgent` | Run specific class |
| `uv run pytest --cov` | Run with coverage |
| `./run_tests.sh -c -v` | Coverage + verbose (using script) |

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── test_example.py          # Basic workflow tests (13 tests)
├── test_agent_example.py    # Agent workflow tests (17 tests)
└── test_ui_generator.py     # UI generator tests (50+ tests)
```

## Coverage Commands

```bash
# Terminal report
uv run pytest --cov=src/multi_agent_mobile_ui_assistant --cov-report=term-missing

# HTML report
uv run pytest --cov=src/multi_agent_mobile_ui_assistant --cov-report=html

# View HTML report
open htmlcov/index.html
```

## Using Test Runner Script

```bash
./run_tests.sh              # Run all tests
./run_tests.sh -c           # With coverage
./run_tests.sh -v           # Verbose
./run_tests.sh -t test_ui_generator.py  # Specific file
./run_tests.sh -h           # Help
```

## Writing Tests

### Template
```python
def test_function_does_something_when_condition(self):
    """Test that function does X when Y."""
    # Arrange
    state = {"input": "test"}
    
    # Act
    result = function(state)
    
    # Assert
    assert result["output"] == "expected"
```

### Using Fixtures
```python
def test_with_fixture(sample_ui_generator_state):
    """Test using a fixture."""
    result = agent(sample_ui_generator_state)
    assert "parsed_intent" in result
```

## Test Statistics

- **Total Tests**: 80+
- **Test Files**: 3
- **Test Classes**: 15
- **Coverage Target**: 80%+

## Key Fixtures (conftest.py)

- `sample_ui_generator_state`
- `sample_agent_state`
- `sample_basic_state`
- `sample_parsed_intent`
- `sample_layout_plan`
- `sample_generated_code`

## Documentation

- **Detailed Guide**: [tests/README.md](tests/README.md)
- **Summary**: [TEST_SUITE_SUMMARY.md](TEST_SUITE_SUMMARY.md)
- **Main README**: [README.md](README.md)
