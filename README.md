# Multi-Agent Mobile UI Assistant

A basic LangGraph project in Python using `uv` package manager with Python 3.13.

## Overview

This project demonstrates a simple LangGraph implementation with a state-based graph workflow. It showcases how to build multi-agent systems using LangGraph's declarative graph API.

## Features

- **Python 3.13**: Uses the latest Python version
- **uv Package Manager**: Fast, modern Python package manager
- **LangGraph**: Framework for building stateful, multi-agent applications
- **Basic Example**: Demonstrates a simple state-based graph with conditional routing

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

### Run the Example

```bash
uv run main.py
```

Or activate the virtual environment and run directly:

```bash
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python main.py
```

### Run the Example Module Directly

```bash
uv run python -m src.multi_agent_mobile_ui_assistant.example
```

## Project Structure

```
.
├── .python-version          # Python version specification
├── pyproject.toml          # Project configuration and dependencies
├── main.py                 # Main entry point
├── src/
│   └── multi_agent_mobile_ui_assistant/
│       ├── __init__.py     # Package initialization
│       └── example.py      # Basic LangGraph example
└── README.md              # This file
```

## Example Description

The included example demonstrates:

1. **State Management**: Using TypedDict to define graph state
2. **Node Creation**: Multiple processing nodes in the graph
3. **Conditional Routing**: Dynamic edge routing based on state
4. **Message Handling**: Using LangGraph's message annotation system

The graph flow:
- Starts at `node_1`
- Conditionally routes to either `node_2` or `node_3` based on step count
- Processes through the selected path
- Ends after completing all nodes

## Dependencies

- `langgraph>=1.0.3`: Core graph framework
- `langchain-core>=1.0.4`: LangChain core functionality
- `langchain-openai>=1.0.2`: OpenAI integration for LangChain

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

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
