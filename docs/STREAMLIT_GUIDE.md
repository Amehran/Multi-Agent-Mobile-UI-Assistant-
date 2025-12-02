# Streamlit Web Interface Guide

## Overview

The Streamlit web interface provides a modern, intuitive way to generate and iteratively refine Jetpack Compose UI code through a beautiful web application.

## Features

### 🎨 Generate UI from Natural Language
- Describe your desired UI in plain English
- Get complete Jetpack Compose code instantly
- See accessibility and design reviews automatically

### ✨ Iterative Refinement
- Provide feedback on generated code
- Refine and improve the UI through multiple iterations
- Each refinement builds on the previous version

### 📜 Complete History Tracking
- View all iterations and refinements in dedicated tab
- See what feedback was provided
- Track improvements over time
- Never lose your work during the session

### 👀 Beautiful Interface
- Modern, responsive design
- Syntax-highlighted Kotlin code
- Separate accessibility and design review panels
- Download generated code with one click
- Example prompts in sidebar

## Quick Start

### 1. Launch the Interface

```bash
# Option 1: Using the launcher script
python app.py

# Option 2: Direct Streamlit command
streamlit run src/multi_agent_mobile_ui_assistant/streamlit_interface.py

# Option 3: With uv
uv run python app.py
```

The interface will open automatically in your browser at: `http://localhost:8501`

### 2. Generate Initial UI

1. Enter your UI description in the **UI Description** field
   - Example: "Create a login screen with email, password, and login button"

2. Click **🚀 Generate UI**

3. Review the generated code and feedback

### 3. Refine the UI

1. Enter feedback in the **Feedback for Refinement** field
   - Example: "Make the button larger and add spacing between fields"

2. Click **✨ Refine UI**

3. See the improved code with highlighted changes

4. Repeat steps 1-3 until satisfied

### 4. Download or Reset

- Click **📥 Download Code** to save your Kotlin file
- Click **🔄 Reset Session** in sidebar to start fresh

## Interface Layout

```
┌─────────────────────────────────────────────────────────────┐
│              Multi-Agent UI Generator                        │
│                    (with tabs)                               │
├──────────────────┬──────────────────────────────────────────┤
│  Sidebar         │  Main Content                            │
│                  │                                           │
│ How It Works     │ Tab 1: Generate & Refine                 │
│ Example Prompts  │ ┌──────────────────────────────────────┐│
│ Iteration History│ │  UI Description                       ││
│ Reset Button     │ │  [Generate UI Button]                 ││
│                  │ └──────────────────────────────────────┘│
│                  │ ┌──────────────────────────────────────┐│
│                  │ │  Feedback for Refinement              ││
│                  │ │  [Refine UI Button]                   ││
│                  │ └──────────────────────────────────────┘│
│                  │ ┌──────────────────────────────────────┐│
│                  │ │  Generated Code (Kotlin)              ││
│                  │ │  [Download Button]                    ││
│                  │ └──────────────────────────────────────┘│
│                  │ ┌──────────┬──────────┐                 │
│                  │ │Accessibility│Design  │                 │
│                  │ │Review      │Review  │                 │
│                  │ └──────────┴──────────┘                 │
│                  │                                          │
│                  │ Tab 2: History                           │
│                  │ - All iterations with expandable details │
└──────────────────┴──────────────────────────────────────────┘
```

## Usage Examples

### Example 1: Login Screen

**Initial Description:**
```
Create a login screen with a title, email field, password field, and login button
```

**Generated Result:**
- Complete Compose code with all elements
- Accessibility review (content descriptions, touch targets)
- Design review (Material 3 compliance)

**Refinement Feedback:**
```
Make the login button larger, add spacing between fields, and change to a blue color theme
```

**Refined Result:**
- Updated code with requested changes
- List of improvements made
- Additional accessibility/design notes

### Example 2: Using Example Prompts

1. Click any example in the sidebar
2. Description auto-fills
3. Click Generate UI
4. Code appears instantly!

## Tips for Best Results

### Writing Good Descriptions

✅ **Good:**
- "Create a login screen with email field, password field, and login button"
- "Build a product card with image, title, price, and add to cart button"
- "Design a bottom navigation with 4 tabs: home, search, favorites, profile"

❌ **Avoid:**
- "Make a screen" (too vague)
- "Something for login" (unclear requirements)
- Just listing components without context

### Writing Effective Feedback

✅ **Good:**
- "Make the button larger and change color to blue"
- "Add 16dp spacing between the text fields"
- "Include icons in the navigation items"
- "Change the title to bold and increase font size"

❌ **Avoid:**
- "Make it better" (not specific)
- "Fix it" (what needs fixing?)
- "I don't like it" (what don't you like?)

### Iterative Refinement Strategy

1. **Start Broad** - Get the basic structure first
2. **Refine Details** - Improve spacing, sizing, colors
3. **Polish** - Add final touches, icons, animations
4. **Focus** - One or two changes per iteration work best

## Streamlit-Specific Features

### Session State

- Your work persists during your browser session
- Refresh the page to reset everything
- History is stored in memory (not saved to disk)

### Sidebar Navigation

- Quick access to example prompts
- Recent history (last 5 iterations)
- Reset button for fresh start

### Tabs

- **Generate & Refine**: Main workspace
- **History**: Complete iteration history with expandable details

### Download

- One-click download of generated code
- File saved as `GeneratedUI.kt`
- Ready to copy into your Android project

## Advanced Features

### Custom Streamlit Options

You can customize Streamlit behavior by creating `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#667eea"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[server]
port = 8501
headless = false
enableCORS = false
```

### Running on Different Port

```bash
streamlit run src/multi_agent_mobile_ui_assistant/streamlit_interface.py --server.port 8080
```

### Running Headless (Server Mode)

```bash
streamlit run src/multi_agent_mobile_ui_assistant/streamlit_interface.py --server.headless true
```

## Troubleshooting

### Interface Won't Load

**Problem**: Browser shows connection error

**Solution**:
1. Check if Streamlit is running (look for URL in terminal)
2. Verify port is not in use: `lsof -i :8501`
3. Try a different port: `--server.port 8080`
4. Check firewall settings

### Generation Fails

**Problem**: Error during UI generation

**Solution**:
1. Check LLM configuration in `.env`
2. For Ollama: Ensure server is running (`ollama serve`)
3. For OpenAI: Verify API key is valid
4. Check terminal for error details

### Refinement Not Working

**Problem**: Refinement returns same code

**Solution**:
1. Make feedback more specific
2. Ensure current code is not empty
3. Try generating fresh UI first
4. Check LLM is responding (see terminal logs)

### Streamlit Keeps Rerunning

**Problem**: Interface keeps refreshing

**Solution**:
1. Don't modify widget values in callbacks
2. Use `st.session_state` properly
3. This is normal Streamlit behavior on interaction

### History Not Showing

**Problem**: History panel is empty

**Solution**:
1. Generate a UI first (history starts after first generation)
2. Check the History tab (separate from main view)
3. History resets on browser refresh

## Performance

### Response Times

- **Initial Generation**: 2-10 seconds (depends on LLM)
- **Refinement**: 3-12 seconds (more complex)
- **Ollama**: Faster with GPU, slower on CPU
- **OpenAI**: Generally faster, consistent

### Resource Usage

- **Memory**: ~100-300MB for Streamlit app
- **Ollama**: Additional 2-8GB for models
- **OpenAI**: Minimal local resources

## Advantages Over Gradio

✅ **Better Performance**: Faster, more responsive
✅ **Native Python**: No JavaScript compilation issues
✅ **Better State Management**: Built-in session state
✅ **Superior UI**: Modern, clean design
✅ **Better Documentation**: Extensive Streamlit docs
✅ **Easier Customization**: Simple theming system
✅ **Production Ready**: Used by many companies
✅ **Active Community**: Large user base
✅ **No Language Limitations**: Works with any code language

## Deployment

### Deploy to Streamlit Cloud (Free)

1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect repository
4. Deploy with one click
5. Get a public URL

### Deploy to Other Platforms

- **Heroku**: `Procfile` with `web: streamlit run ...`
- **AWS/GCP/Azure**: Run as Docker container
- **Docker**: Create Dockerfile with Streamlit

## Keyboard Shortcuts

- `Ctrl/Cmd + Enter` in text area → Auto-trigger (optional)
- `Tab` → Navigate between fields
- `Esc` → Close dialogs/modals
- `Ctrl/Cmd + R` → Refresh page

## Integration

### Embedding in Larger Apps

```python
# Import the main function
from src.multi_agent_mobile_ui_assistant.streamlit_interface import main

# Run as part of multipage app
if __name__ == "__main__":
    main()
```

### Custom Components

Streamlit supports custom components:
- Add your own visualizations
- Integrate with other tools
- Create custom widgets

## Next Steps

1. Launch the app: `python app.py`
2. Try the example prompts
3. Experiment with different UI types
4. Practice giving specific feedback
5. Build a complete app screen by screen
6. Export and integrate code into your project

## Support

- Streamlit docs: [docs.streamlit.io](https://docs.streamlit.io)
- Check terminal output for detailed logs
- Review error messages in the interface
- Consult LLM_SETUP.md for LLM issues
- See README.md for general setup

---

**Ready to create amazing UIs?** Launch the app and start generating! 🚀
