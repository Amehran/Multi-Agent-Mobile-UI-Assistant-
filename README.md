# 📱 Multi-Agent Mobile UI Assistant

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.39-FF4B4B.svg)](https://streamlit.io)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.0-green.svg)](https://langchain-ai.github.io/langgraph/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A powerful **LangGraph-based multi-agent system** that generates production-ready **Jetpack Compose UI code** from natural language descriptions or Figma designs. It features a modern Streamlit web interface for iterative refinement, real-time preview, and automated code validation.

---

## 🚀 Key Features

*   **🗣️ Natural Language to UI**: Describe your interface in plain English (e.g., "Login screen with email, password, and social login buttons") and get functional Compose code instantly.
*   **🎨 Figma to Code**: Import designs directly from Figma using the **Figma MCP** integration. Extracts layout, colors, and typography automatically.
*   **🤖 Multi-Agent Architecture**:
    *   **UI Generator**: A single LLM call that interprets the full request — concrete requirements and subjective style cues alike — and writes the Kotlin/Compose code directly.
    *   **Validator**: Lints and compiles the generated code in-graph; on failure it loops back to the UI Generator with the specific error, up to 2 retries, before proceeding regardless of outcome.
    *   **Accessibility Reviewer**: Checks for content descriptions, touch targets, and contrast.
    *   **UI Reviewer**: Validates against Material 3 design guidelines.
*   **🛠️ MCP Tools Integration**:
    *   **Android Lint MCP**: Static analysis for common Compose errors (missing imports, modifier misuse).
    *   **Gradle MCP**: Validates Kotlin compilation (real `kotlinc` when available, heuristic fallback otherwise — see known limitation below).
    *   **Figma MCP**: Connects to Figma API for design extraction.
*   **✨ Interactive Refinement**: Use the Streamlit UI to chat with the agent and refine the code (e.g., "Make the button bigger", "Change the color scheme").
*   **🛡️ Auto-Validation & Fix**: Automatically detects and fixes missing imports and syntax errors before showing you the code.
*   **👁️ Visual Preview**: Generates a structural HTML preview of the Compose layout.

---

## 🏗️ Architecture

The system uses a directed cyclic graph (LangGraph) to orchestrate specialized agents:

```mermaid
graph LR
    User[User Input] --> Generator[UI Generator]
    Figma[Figma Design] --> Generator
    Generator --> Validator[Validator]
    Validator -->|fail, retries remaining| Generator
    Validator -->|pass or retries exhausted| Reviewer1[Accessibility Reviewer]
    Reviewer1 --> Reviewer2[UI Reviewer]
    Reviewer2 --> Output[Final Code + Trace + Verdicts]
```

There is no separate Intent Parser or Layout Planner stage — a single LLM call in the UI Generator handles interpretation and layout together, which produced better results than splitting them.

---

## 🛠️ Installation

### Prerequisites
*   **Python 3.13+**
*   **uv** package manager (Recommended) or `pip`
*   **Git**

### 1. Clone the Repository
```bash
git clone <repository-url>
cd Multi-Agent-Mobile-UI-Assistant-
```

### 2. Install Dependencies
Using `uv` (fastest):
```bash
uv sync
```
Or using `pip`:
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
Create a `.env` file from the example:
```bash
cp .env.example .env
```

Edit `.env` to configure your LLM provider and optional Figma credentials:

**For Ollama (Local, Free):**
```env
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434
```

**For OpenAI (Cloud, Best Quality):**
```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
OPENAI_API_KEY=sk-...
```

**For Figma Integration (Optional):**
```env
FIGMA_ACCESS_TOKEN=your_figma_token
```

---

## 💻 Usage

### 🌐 Web Interface (Recommended)
Launch the interactive Streamlit app:
```bash
uv run python app.py
```
Or directly:
```bash
streamlit run src/multi_agent_mobile_ui_assistant/streamlit_interface.py
```
Open **http://localhost:8501** in your browser.

**Web UI Features:**
1.  **Generate**: Type a description or paste a Figma file key.
2.  **Preview**: See a visual representation of the layout.
3.  **Refine**: Chat with the agent to tweak the design.
4.  **Validate**: View linting reports and auto-fix logs.
5.  **Download**: Get the `.kt` file ready for Android Studio.

> ⚠️ **Known limitation:** The "Compilation Check" in the Validation Report tries real `kotlinc` compilation when that binary is available on your `PATH`; if it isn't (the common case for this demo, since it doesn't require an Android/Kotlin toolchain to run), it falls back to a heuristic — brace/paren balance and basic import checks via Gradle MCP — which catches structural errors but cannot guarantee the code truly compiles. If validation still fails after the retry loop's 2 attempts, the code is shown anyway with the failing checks visible here.

### 🎬 Curated Demo Prompts

These 3 prompts each mix a concrete UI requirement with a subjective style cue, to show the agent genuinely interpreting intent rather than filling a template. They're available as one-click buttons in the sidebar and are the canonical prompts used throughout this project's demos:

1. *"A login screen with an email field, a password field, and a login button — keep it minimal and calm, nothing loud."*
2. *"A product card with an image, a title, a price, and an add-to-cart button, but make it feel energetic and playful."*
3. *"A settings screen with toggle switches for notifications and dark mode, styled to feel trustworthy and professional, like a banking app."*

### ⌨️ CLI Mode
Run the generator from the terminal:
```bash
uv run main.py
```

---

## 🎨 Figma Integration

To use the Figma-to-Code feature:

1.  Get a **Personal Access Token** from Figma (Settings > Account > Personal Access Tokens).
2.  Add it to your `.env` file or enter it in the Streamlit sidebar.
3.  Get the **File Key** from your Figma design URL:
    `https://www.figma.com/file/abc123xyz/My-Design` -> Key is `abc123xyz`.
4.  In the Streamlit app, check "Import from Figma" and enter the key.

---

## 📂 Project Structure

```
.
├── src/multi_agent_mobile_ui_assistant/
│   ├── android_tools_mcp.py    # Linting & Compilation tools
│   ├── figma_mcp.py            # Figma API integration
│   ├── ui_generator.py         # LangGraph pipeline: generator, validator retry loop, reviewers
│   ├── streamlit_interface.py  # Web UI
│   └── llm_config.py           # LLM provider setup
├── tests/                      # Unit and integration tests
├── app.py                      # Launcher script
├── pyproject.toml              # Dependencies
└── README.md                   # Documentation
```

---

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/multi_agent_mobile_ui_assistant
```

---

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) (coming soon).

1.  Fork the repo
2.  Create a feature branch (`git checkout -b feature/amazing-feature`)
3.  Commit your changes (`git commit -m 'Add amazing feature'`)
4.  Push to the branch (`git push origin feature/amazing-feature`)
5.  Open a Pull Request

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
