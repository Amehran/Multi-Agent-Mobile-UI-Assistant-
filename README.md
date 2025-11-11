# Multi-Agent Mobile UI Assistant

A LangGraph-based multi-agent system that generates functional, high-quality Jetpack Compose UI code from natural language descriptions using Python 3.13 and `uv` package manager.

## Overview

This project implements a sophisticated multi-agent workflow that takes natural language descriptions of mobile UI and generates production-ready Jetpack Compose code with accessibility and design review feedback.

## Architecture

The system uses a **LangGraph-based multi-agent architecture** with the following flow:

```
User Input → Intent Parser Agent → Layout Planner Agent → UI Generator Agent 
→ Accessibility Reviewer Agent → UI Reviewer Agent → Output Node
```

### Agent Roles

1. **Intent Parser Agent**: Extracts UI elements, layout hierarchy, styles, and actions from natural language
2. **Layout Planner Agent**: Translates parsed intent into structured layout (Column, Row, Box, etc.)
3. **UI Generator Agent**: Generates actual Jetpack Compose code
4. **Accessibility Reviewer Agent**: Validates color contrast, content descriptions, and touch targets
5. **UI Reviewer Agent**: Evaluates design against Material 3 guidelines

## Features

- **Natural Language Input**: Describe UIs in plain English
- **Jetpack Compose Code Generation**: Produces functional Kotlin Compose code
- **Multi-Agent Review System**: Automated accessibility and design review
- **Material 3 Compliance**: Follows Material Design 3 guidelines
- **Python 3.13**: Uses the latest Python version
- **uv Package Manager**: Fast, modern Python package manager

## Prerequisites

- Python 3.13+
- `uv` package manager

## Installation

### Install uv (if not already installed)

```bash
pip install uv
```

### Clone and Setup

```bash
git clone <repository-url>
cd Multi-Agent-Mobile-UI-Assistant-
```

### Install Dependencies

```bash
uv sync
```

This will create a virtual environment and install all dependencies.

## Usage

### Interactive Mode

```bash
uv run main.py
```

You'll be prompted to describe the UI you want to create. Examples:
- "Create a login screen with username, password, and login button"
- "Build a card with an image, title, and action button"
- "Design a settings page with multiple options"

Press Enter without input to run the demo examples.

### Run UI Generator Directly

```bash
uv run python -m src.multi_agent_mobile_ui_assistant.ui_generator
```

### Run Basic Examples (Learning)

The project includes basic LangGraph examples for learning:

**Basic Example:**
```bash
uv run python -m src.multi_agent_mobile_ui_assistant.example
```

**Advanced Agent Example:**
```bash
uv run python -m src.multi_agent_mobile_ui_assistant.agent_example
```

## Project Structure

```
.
├── .python-version                         # Python version specification
├── pyproject.toml                         # Project configuration and dependencies
├── uv.lock                                # Locked dependency versions
├── main.py                                # Main entry point (interactive UI generator)
├── src/
│   └── multi_agent_mobile_ui_assistant/
│       ├── __init__.py                    # Package initialization
│       ├── ui_generator.py                # Main UI generator (multi-agent system)
│       ├── example.py                     # Basic LangGraph example (learning)
│       └── agent_example.py               # Advanced agent example (learning)
└── README.md                              # This file
```

## How It Works

### 1. Intent Parser Agent
Analyzes the natural language input and extracts:
- UI elements (buttons, text, images, etc.)
- Layout type (Column, Row, Card, etc.)
- Styling requirements
- User actions

### 2. Layout Planner Agent
Creates a structured layout plan:
- Determines root container type
- Plans component hierarchy
- Defines modifiers and arrangements
- Sets alignment and spacing

### 3. UI Generator Agent
Generates Jetpack Compose code:
- Creates @Composable function
- Implements layout containers
- Adds UI components with properties
- Applies Material 3 theming

### 4. Accessibility Reviewer Agent
Validates accessibility:
- Content descriptions for images
- Touch target sizes (minimum 48dp)
- Semantic properties for screen readers
- Color contrast ratios

### 5. UI Reviewer Agent
Evaluates design quality:
- Material 3 guideline compliance
- Proper spacing and padding
- Correct use of Arrangement and Alignment
- Theme consistency

### 6. Output Node
Produces final deliverable:
- Generated Jetpack Compose code
- Accessibility review feedback
- Design review recommendations

## Example Output

**Input:** "Create a card with an image, title text, and a button"

**Output:**
```kotlin
@Composable
fun GeneratedUI() {
    Card(modifier = Modifier.fillMaxSize.padding(16.dp)) {
        Image(
            // Image implementation
            contentDescription = "Sample image"
        )
        Text(
            text = "Sample Text",
            style = MaterialTheme.typography.headlineMedium
        )
        Button(onClick = { /* TODO: Add action */ }) {
            Text("Click Me")
        }
    }
}
```

Plus accessibility and design review feedback.

## Dependencies

- `langgraph>=1.0.3`: Core graph framework
- `langchain-core>=1.0.4`: LangChain core functionality
- `langchain-openai>=1.0.2`: OpenAI integration for LangChain

## Testing

The project includes comprehensive unit tests for all modules.

### Install Test Dependencies

```bash
uv sync --extra dev
```

### Run Tests

```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=src/multi_agent_mobile_ui_assistant --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_ui_generator.py

# Run with verbose output
uv run pytest -v
```

### Test Coverage

The test suite includes:
- **test_example.py**: Tests for basic LangGraph workflow (13 tests)
- **test_agent_example.py**: Tests for advanced agent workflow (17 tests)
- **test_ui_generator.py**: Tests for UI generator system (50+ tests)

See [tests/README.md](tests/README.md) for detailed testing documentation.

## Development

### Adding Dependencies

```bash
uv add <package-name>
```

### Removing Dependencies

```bash
uv remove <package-name>
```

### Updating Dependencies

```bash
uv sync --upgrade
```

## Future Enhancements

This is a basic starter implementation. Future enhancements could include:

- **LLM Integration**: Connect to OpenAI, Anthropic, or other LLMs for better intent parsing
- **Advanced UI Components**: Support for more Compose components (LazyColumn, Scaffold, etc.)
- **State Management**: Generate ViewModels and state handling code
- **Navigation**: Multi-screen app generation with navigation
- **Custom Themes**: User-defined color schemes and typography
- **Preview Generation**: Generate preview functions and screenshots
- **File Export**: Write generated code to actual .kt files
- **Interactive Refinement**: Allow users to refine generated code iteratively

## Learning Resources

The project includes example files demonstrating LangGraph concepts:
- `example.py`: Basic state-based graph workflow
- `agent_example.py`: Multi-tool agent orchestration

These are useful for understanding LangGraph fundamentals before diving into the UI generator.

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
