"""
Streamlit Web Interface for Multi-Agent UI Generator

This module provides an interactive web UI for generating and refining
Jetpack Compose UI code with iterative improvements using Streamlit.
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
from langchain_core.messages import SystemMessage, HumanMessage
import json

# Add src directory to path for imports
src_path = Path(__file__).parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.multi_agent_mobile_ui_assistant.ui_generator import generate_ui_from_description
from src.multi_agent_mobile_ui_assistant.llm_config import create_llm
from src.multi_agent_mobile_ui_assistant.figma_mcp import FigmaMCP

# The 3 curated demo prompts (CAP-8): each mixes a concrete UI requirement with a
# subjective style cue, to demonstrate genuine interpretation rather than
# template-filling. Keep this in sync with the copy documented in README.md.
CURATED_DEMO_PROMPTS = [
    "A login screen with an email field, a password field, and a login button — keep it minimal and calm, nothing loud.",
    "A product card with an image, a title, a price, and an add-to-cart button, but make it feel energetic and playful.",
    "A settings screen with toggle switches for notifications and dark mode, styled to feel trustworthy and professional, like a banking app.",
]


# Page configuration
st.set_page_config(
    page_title="Multi-Agent UI Generator",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .iteration-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stCodeBlock {
        background-color: #1e1e1e;
    }
    .review-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #667eea;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_code' not in st.session_state:
    st.session_state.current_code = ""
if 'current_accessibility' not in st.session_state:
    st.session_state.current_accessibility = []
if 'current_design' not in st.session_state:
    st.session_state.current_design = []
if 'current_trace' not in st.session_state:
    st.session_state.current_trace = []
if 'current_validation_checks' not in st.session_state:
    st.session_state.current_validation_checks = []
if 'iteration_count' not in st.session_state:
    st.session_state.iteration_count = 0
if 'llm_provider' not in st.session_state:
    st.session_state.llm_provider = "ollama"
if 'llm_model' not in st.session_state:
    st.session_state.llm_model = "llama3.2"


def get_llm_for_session():
    """Get LLM instance based on session state settings."""
    provider = st.session_state.llm_provider
    model = st.session_state.llm_model
    
    return create_llm(provider=provider, model=model)


def extract_code_from_output(output: str) -> str:
    """Extract the Kotlin code from the full output."""
    lines = output.split("\n")
    code_lines = []
    in_code = False
    brace_count = 0
    
    for line in lines:
        if "@Composable" in line:
            in_code = True
        if in_code:
            code_lines.append(line)
            # Count braces to find the matching closing brace
            brace_count += line.count("{") - line.count("}")
            # Stop when we've closed all braces (back to 0)
            if brace_count == 0 and len(code_lines) > 5:
                break
    
    return "\n".join(code_lines) if code_lines else output


def render_check_results(title: str, checks) -> None:
    """
    Render a list of CheckResult dicts using a generic status-driven icon
    (pass -> st.success, warn -> st.warning, fail -> st.error). No message-text
    sniffing -- rendering is keyed only on the `status` field. Uses `.get()`
    with sensible defaults throughout so a malformed/missing key degrades
    gracefully instead of crashing the tab.

    `checks=None` means the check never ran for this generation (e.g. Figma or
    multi-file mode); `checks=[]` means it ran and found nothing -- these are
    rendered with distinct messages so an empty result doesn't read as a false
    "all clear."
    """
    if title:
        st.subheader(title)
    if checks is None:
        st.info("Not run for this generation mode.")
        return
    if not checks:
        st.info("No checks recorded.")
        return
    icon_fns = {"pass": st.success, "warn": st.warning, "fail": st.error}
    for c in checks:
        icon_fn = icon_fns.get(c.get("status"), st.info)
        attempt = c.get("attempt")
        prefix = f"(attempt {attempt}) " if attempt is not None else ""
        icon_fn(f"{prefix}{c.get('message', '')}")


def render_trace_steps(title: str, steps: list) -> None:
    """
    Render a list of TraceStep dicts: one line per step (node + summary),
    with the step's detail shown in a nested expander. Uses `.get()` with
    sensible defaults throughout so a malformed/missing key degrades
    gracefully instead of crashing the tab.
    """
    if title:
        st.subheader(title)
    if not steps:
        st.info("No trace recorded.")
        return
    for step in steps:
        node = step.get("node", "")
        summary = step.get("summary", "")
        with st.expander(f"**{node}** — {summary}"):
            st.caption(step.get("detail", ""))


def render_review(title: str, review) -> None:
    """
    Render a "review" that may be either a list[CheckResult] (produced by the
    initial-generation flow, story 3) or a legacy prose string (still produced
    by `refine_ui`'s free-form LLM review, which this story does not touch).
    Dispatches on type so viewing Reviews after a Generate -> Refine sequence
    doesn't crash by iterating a string as if it were a list of dicts.
    """
    if review is None or isinstance(review, list):
        render_check_results(title, review)
    else:
        if title:
            st.subheader(title)
        st.markdown(f'<div class="review-section">{review}</div>', unsafe_allow_html=True)


def generate_initial_ui(description: str):
    """Generate initial UI from description."""
    if not description.strip():
        st.error("Please enter a UI description")
        return
    
    with st.spinner("🔮 Generating UI code..."):
        try:
            # Get options from session state
            validate = st.session_state.get('validate_code', True)
            multi_file = st.session_state.get('multi_file', False)
            use_figma = st.session_state.get('use_figma', False)
            
            # Check if using Figma
            figma_design = None
            if use_figma:
                figma_token = st.session_state.get('figma_token', '')
                figma_file_key = st.session_state.get('figma_file_key', '')
                
                if figma_token and figma_file_key:
                    try:
                        with st.spinner("🎨 Extracting Figma design..."):
                            figma = FigmaMCP(access_token=figma_token)
                            figma_design = figma.extract_design(file_key=figma_file_key)
                            
                            # Convert Figma design directly to Compose
                            code = figma.convert_to_compose(figma_design)
                            
                            st.success(f"✅ Imported design from Figma: {figma_design.name}")
                            st.info(f"📊 Found {len(figma_design.colors)} colors, {len(figma_design.typography)} text styles, {len(figma_design.components)} components")
                    except Exception as e:
                        st.error(f"Failed to import from Figma: {str(e)}")
                        st.info("Falling back to text-based generation...")
                        figma_design = None
                else:
                    st.warning("Figma credentials missing. Using text-based generation.")
            
            # If not using Figma or Figma failed, use standard generation
            if not figma_design:
                # Generate UI with options. `return_report` is requested
                # unconditionally so trace/CheckResult data is always available
                # for the Reviews/Trace tabs, regardless of validate/multi_file.
                output = generate_ui_from_description(
                    description,
                    validate=validate,
                    return_report=True,
                    multi_file=multi_file
                )

                if multi_file:
                    # Multi-file returns its own dict-of-files contract -- no
                    # trace/CheckResult data is produced for this path. `None`
                    # (not `[]`) marks "never run" distinctly from "ran clean".
                    code = output
                    validation_report = None
                    trace = []
                    accessibility_issues = None
                    design_issues = None
                    validation_checks = None
                else:
                    code = output['code']
                    validation_report = output.get('validation_report')
                    trace = output.get('trace', [])
                    accessibility_issues = output.get('accessibility_issues', [])
                    design_issues = output.get('design_issues', [])
                    validation_checks = output.get('validation_checks', [])
            else:
                # Figma design was used -- no trace/CheckResult data either.
                validation_report = None
                trace = []
                accessibility_issues = None
                design_issues = None
                validation_checks = None

            # Parse output
            if not multi_file and not figma_design:
                code_text = extract_code_from_output(code) if isinstance(code, str) else code
            else:
                code_text = code  # Multi-file or Figma returns structured data

            # Update session state
            st.session_state.current_code = code_text
            st.session_state.current_trace = trace
            st.session_state.current_accessibility = accessibility_issues
            st.session_state.current_design = design_issues
            st.session_state.current_validation_checks = validation_checks
            st.session_state.iteration_count += 1
            st.session_state.validation_report = validation_report

            # Add to history
            st.session_state.history.append({
                "iteration": st.session_state.iteration_count,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "description": description,
                "code": code_text,
                "accessibility": accessibility_issues,
                "design": design_issues,
                "feedback": "",
                "validation_report": validation_report
            })

            st.success("✅ UI generated successfully!")
            if validate and validation_report:
                st.info("🔍 Code validation completed - check the Validation Report tab")
            st.rerun()
            
        except Exception as e:
            st.error(f"Error generating UI: {str(e)}")


def refine_ui(feedback: str):
    """Refine the current UI based on user feedback."""
    if not feedback.strip():
        st.error("Please provide feedback on what to improve")
        return
    
    if not st.session_state.current_code:
        st.error("No current code to refine. Generate a UI first.")
        return
    
    with st.spinner("✨ Refining UI based on your feedback..."):
        try:
            llm = get_llm_for_session()
            
            # Create refinement prompt
            system_prompt = """You are a Jetpack Compose UI expert. You refine generated UI code based on user feedback.

Given the current code and user feedback, produce an improved version that addresses the feedback while maintaining:
- Proper Jetpack Compose syntax
- Material 3 guidelines
- Accessibility best practices
- Clean, readable code

IMPORTANT: Return ONLY a valid JSON object. The "refined_code" field must have all newlines and quotes properly escaped.
Use \\n for newlines and \\" for quotes inside the code string.

Respond with this exact JSON structure:
{
    "refined_code": "the complete improved @Composable function with \\n for newlines",
    "changes_made": ["improvement 1", "improvement 2"],
    "accessibility_notes": ["note 1", "note 2"],
    "design_notes": ["note 1", "note 2"]
}

Do not include any text before or after the JSON object."""

            user_message = f"""Current Code:
```kotlin
{st.session_state.current_code}
```

User Feedback:
{feedback}

Please refine the code based on this feedback."""

            # Call LLM
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ]
            
            response = llm.invoke(messages)
            
            # Parse response with better error handling
            response_text = response.content
            
            # Extract JSON from markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            # Try to parse JSON with strict=False to handle control characters
            try:
                result = json.loads(response_text, strict=False)
            except json.JSONDecodeError as e:
                # If JSON parsing fails, try to extract code manually
                st.warning(f"JSON parsing issue: {str(e)}. Attempting to extract code...")
                
                # Fallback: look for code between quotes or just use original
                if '"refined_code"' in response_text:
                    # Try to extract the code section manually
                    try:
                        # Find the refined_code field and extract until the next field
                        code_start = response_text.find('"refined_code"')
                        code_section = response_text[code_start:]
                        # Find the opening quote after the colon
                        first_quote = code_section.find('"', code_section.find(':'))
                        # Find the closing quote (accounting for escaped quotes)
                        code_content = ""
                        i = first_quote + 1
                        while i < len(code_section):
                            if code_section[i] == '"' and (i == 0 or code_section[i-1] != '\\'):
                                break
                            code_content += code_section[i]
                            i += 1
                        
                        refined_code = code_content.replace('\\n', '\n').replace('\\"', '"')
                        changes = ["Code refined based on your feedback"]
                        accessibility_notes = ["Please review accessibility manually"]
                        design_notes = ["Please review design manually"]
                    except Exception as extract_error:
                        st.error(f"Could not extract refined code: {str(extract_error)}")
                        return
                else:
                    st.error("Could not parse LLM response. Please try again with different feedback.")
                    return
            else:
                # Successfully parsed JSON
                refined_code = result.get("refined_code", st.session_state.current_code)
                changes = result.get("changes_made", [])
                accessibility_notes = result.get("accessibility_notes", [])
                design_notes = result.get("design_notes", [])
            
            # Format reviews
            accessibility_review = "**Improvements Made:**\n" + "\n".join([f"• {note}" for note in accessibility_notes])
            design_review = "**Improvements Made:**\n" + "\n".join([f"• {note}" for note in design_notes])
            design_review += "\n\n**Changes Applied:**\n" + "\n".join([f"• {change}" for change in changes])
            
            # Update session state. Refine doesn't invoke the graph, so the
            # prior generation's trace/validation data no longer describes the
            # current code -- clear it rather than leave it stale and misleading.
            st.session_state.current_code = refined_code
            st.session_state.current_accessibility = accessibility_review
            st.session_state.current_design = design_review
            st.session_state.current_trace = []
            st.session_state.current_validation_checks = None
            st.session_state.validation_report = None
            st.session_state.iteration_count += 1
            
            # Add to history
            last_description = st.session_state.history[-1]['description'] if st.session_state.history else "Refinement"
            st.session_state.history.append({
                "iteration": st.session_state.iteration_count,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "description": last_description,
                "code": refined_code,
                "accessibility": accessibility_review,
                "design": design_review,
                "feedback": feedback
            })
            
            st.success("✅ UI refined successfully!")
            st.rerun()
            
        except Exception as e:
            st.error(f"Error refining UI: {str(e)}")


def reset_session():
    """Reset the session and clear all history."""
    st.session_state.history = []
    st.session_state.current_code = ""
    st.session_state.current_accessibility = []
    st.session_state.current_design = []
    st.session_state.current_trace = []
    st.session_state.current_validation_checks = []
    st.session_state.iteration_count = 0
    st.success("Session reset successfully!")
    st.rerun()


def generate_preview_html(code: str) -> str:
    """
    Generate a simple HTML preview visualization of Compose UI.
    """
    if not code:
        return "<p>No code to preview</p>"
    
    colors = {
        "Icon": "#FF6B35",
        "Text": "#2196F3",
        "TextField": "#4CAF50",
        "Button": "#9C27B0"
    }
    
    lines = code.split('\n')
    html_content = []
    html_content.append('<div style="font-family: system-ui; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px;">')
    html_content.append('<div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">')
    
    import html
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Icon
        if 'Icon(' in stripped and 'IconButton' not in stripped and 'imageVector' in stripped:
            icon_name = "Icon"
            if 'Icons.Default.' in stripped:
                try:
                    icon_name = stripped.split('Icons.Default.')[1].split(',')[0].split(')')[0].strip()
                except:
                    pass
            
            icon_emoji = "👤" if 'Account' in icon_name else ("🔴" if 'Google' in icon_name else "🔵")
            size = ""
            if '.size(' in stripped:
                try:
                    size = f" ({stripped.split('.size(')[1].split(')')[0]})"
                except:
                    pass
            
            html_content.append(f'<div style="margin: 12px 0; padding: 12px; background: #fff3e0; border-left: 3px solid {colors["Icon"]}; border-radius: 4px; text-align: center;">')
            html_content.append(f'<div style="font-size: 2em;">{icon_emoji}</div>')
            html_content.append(f'<div style="font-size: 0.85em; color: #666; margin-top: 4px;">{html.escape(icon_name)}{html.escape(size)}</div>')
            html_content.append('</div>')
        
        # Spacer
        elif 'Spacer(' in stripped and 'Modifier' in stripped:
            height = "16.dp"
            if '.height(' in stripped:
                try:
                    height = stripped.split('.height(')[1].split(')')[0]
                except:
                    pass
            
            html_content.append(f'<div style="margin: 8px 0; padding: 8px; background: #f5f5f5; border-radius: 4px; text-align: center;">')
            html_content.append(f'<span style="font-size: 0.75em; color: #999;">↕️ Spacer {html.escape(height)}</span>')
            html_content.append('</div>')
        
        # Text
        elif 'Text(' in stripped and 'TextField' not in stripped and not any(x in line for x in ['Button', 'label =', 'placeholder =']):
            text_content = ""
            if 'text = "' in stripped:
                try:
                    text_content = stripped.split('text = "')[1].split('"')[0]
                except:
                    pass
            elif 'Text("' in stripped:
                try:
                    text_content = stripped.split('Text("')[1].split('"')[0]
                except:
                    pass
            
            if text_content and 'OR' not in text_content:  # Skip OR text
                style = ""
                for j in range(i, min(i+3, len(lines))):
                    if 'headlineLarge' in lines[j]:
                        style = " • Headline"
                        break
                    elif 'bodySmall' in lines[j]:
                        style = " • Small"
                        break
                
                html_content.append(f'<div style="margin: 12px 0; padding: 12px; background: #e3f2fd; border-left: 3px solid {colors["Text"]}; border-radius: 4px;">')
                html_content.append(f'<div style="font-weight: 500;">"{html.escape(text_content)}"</div>')
                if style:
                    html_content.append(f'<div style="font-size: 0.75em; color: #666; margin-top: 4px;">{style}</div>')
                html_content.append('</div>')
        
        # TextField
        elif 'OutlinedTextField(' in stripped:
            label = "Text Field"
            placeholder = ""
            for j in range(i, min(i + 10, len(lines))):
                if 'label = { Text("' in lines[j]:
                    try:
                        label = lines[j].split('label = { Text("')[1].split('"')[0]
                    except:
                        pass
                if 'placeholder = { Text("' in lines[j]:
                    try:
                        placeholder = lines[j].split('placeholder = { Text("')[1].split('"')[0]
                    except:
                        pass
            
            html_content.append(f'<div style="margin: 12px 0; padding: 14px; border: 2px solid {colors["TextField"]}; border-radius: 8px; background: white;">')
            html_content.append(f'<div style="font-size: 0.7em; color: #666; margin-bottom: 6px;">{html.escape(label)}</div>')
            html_content.append(f'<div style="color: #999;">✏️ {html.escape(placeholder) or "Enter text"}</div>')
            html_content.append('</div>')
        
        # Button
        elif ('Button(' in stripped or 'OutlinedButton(' in stripped) and 'IconButton' not in stripped:
            button_text = "Button"
            is_outlined = 'OutlinedButton(' in stripped
            for j in range(i, min(i + 10, len(lines))):
                if 'Text("' in lines[j] and 'TextField' not in lines[j]:
                    try:
                        button_text = lines[j].split('Text("')[1].split('"')[0]
                    except:
                        pass
                    break
            
            if is_outlined:
                html_content.append(f'<div style="margin: 12px 0; padding: 12px 24px; background: white; border: 2px solid {colors["Button"]}; color: {colors["Button"]}; border-radius: 8px; font-weight: 500; text-align: center;">')
            else:
                html_content.append(f'<div style="margin: 12px 0; padding: 12px 24px; background: {colors["Button"]}; color: white; border-radius: 8px; font-weight: 500; text-align: center;">')
            html_content.append(f'▶ {html.escape(button_text)}')
            html_content.append('</div>')
        
        # HorizontalDivider (OR pattern)
        elif 'HorizontalDivider(' in stripped:
            # Check for OR divider
            is_or = False
            for j in range(max(0, i-3), min(i+4, len(lines))):
                if '"OR"' in lines[j] or "'OR'" in lines[j]:
                    is_or = True
                    break
            
            if is_or and (i == 0 or 'HorizontalDivider' not in lines[i-1]):
                html_content.append('<div style="margin: 16px 0; display: flex; align-items: center; gap: 12px;">')
                html_content.append('<div style="flex: 1; height: 1px; background: #ddd;"></div>')
                html_content.append('<span style="color: #666; font-weight: 500;">OR</span>')
                html_content.append('<div style="flex: 1; height: 1px; background: #ddd;"></div>')
                html_content.append('</div>')
    
    html_content.append('</div>')
    html_content.append('</div>')
    return '\n'.join(html_content)



# Main UI Layout
def main():
    # Header
    st.markdown('<h1 class="main-header">🎨 Multi-Agent Jetpack Compose UI Generator</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    Generate beautiful Jetpack Compose UI code from natural language descriptions,
    then iteratively refine it based on your feedback!
    """)
    
    # Sidebar
    with st.sidebar:
        # LLM Provider Selection
        st.header("🤖 LLM Settings")
        
        # Predefined LLM options
        llm_options = {
            "Ollama - Llama 3.2": {"provider": "ollama", "model": "llama3.2"},
            "Ollama - CodeLlama": {"provider": "ollama", "model": "codellama"},
            "OpenAI - GPT-4o Mini": {"provider": "openai", "model": "gpt-4o-mini"},
            "OpenAI - GPT-4o": {"provider": "openai", "model": "gpt-4o"},
            "OpenAI - GPT-4o Nano": {"provider": "openai", "model": "gpt-4o-nano"},
            "Google - Gemini Pro": {"provider": "google", "model": "gemini-pro"},
            "Custom": {"provider": "custom", "model": "custom"}
        }
        
        # Find current selection
        current_selection = "Custom"
        for option_name, option_config in llm_options.items():
            if (option_config["provider"] == st.session_state.llm_provider and 
                option_config["model"] == st.session_state.llm_model):
                current_selection = option_name
                break
        
        # LLM selection dropdown
        selected_option = st.selectbox(
            "LLM Model",
            options=list(llm_options.keys()),
            index=list(llm_options.keys()).index(current_selection),
            help="Choose your preferred LLM model",
            key="llm_option_select"
        )
        
        # Update session state based on selection
        if selected_option != "Custom":
            config = llm_options[selected_option]
            st.session_state.llm_provider = config["provider"]
            st.session_state.llm_model = config["model"]
        else:
            # Show custom input fields
            st.session_state.llm_provider = st.text_input(
                "Provider",
                value=st.session_state.get('llm_provider', 'ollama'),
                help="e.g., ollama, openai, google",
                key="custom_provider_input"
            )
            st.session_state.llm_model = st.text_input(
                "Model Name",
                value=st.session_state.get('llm_model', 'llama3.2'),
                help="Enter the model name",
                key="custom_model_input"
            )
        
        # Show current configuration
        st.info(f"✓ Using **{st.session_state.llm_provider}** with model **{st.session_state.llm_model}**")
        
        st.divider()
        
        # Figma Integration
        st.header("🎨 Figma Integration")
        
        use_figma = st.checkbox(
            "Import from Figma",
            value=st.session_state.get('use_figma', False),
            help="Extract design specifications from Figma and generate accurate Compose code",
            key="use_figma_checkbox"
        )
        st.session_state.use_figma = use_figma
        
        if use_figma:
            figma_token = st.text_input(
                "Figma Access Token",
                value=st.session_state.get('figma_token', ''),
                type="password",
                help="Your Figma personal access token. Get it from Figma Settings > Account > Personal Access Tokens",
                key="figma_token_input"
            )
            st.session_state.figma_token = figma_token
            
            figma_file_key = st.text_input(
                "Figma File Key",
                value=st.session_state.get('figma_file_key', ''),
                placeholder="e.g., abc123xyz from figma.com/file/abc123xyz/...",
                help="The file key from your Figma URL",
                key="figma_file_key_input"
            )
            st.session_state.figma_file_key = figma_file_key
            
            if figma_token and figma_file_key:
                st.success("✓ Figma credentials configured")
            else:
                st.warning("⚠️ Please provide both Figma token and file key")
        
        st.divider()
        
        # Advanced Options
        st.header("⚙️ Advanced Options")
        
        # Multi-file project generation
        multi_file = st.checkbox(
            "Multi-file Project",
            value=st.session_state.get('multi_file', False),
            help="Generate a complete project structure with separate files for each component",
            key="multi_file_checkbox"
        )
        st.session_state.multi_file = multi_file
        
        # Validation and auto-fix
        validate_code = st.checkbox(
            "Code Validation & Auto-fix",
            value=st.session_state.get('validate_code', True),
            help="Automatically validate generated code and fix common issues like missing imports",
            key="validate_checkbox"
        )
        st.session_state.validate_code = validate_code

        st.divider()
        
        st.header("📋 How It Works")
        st.markdown("""
        1. **Describe** your UI in plain English
        2. Click **Generate UI** to create the code
        3. Review the generated code and feedback
        4. Provide **feedback** on what to improve
        5. Click **Refine UI** to get an improved version
        6. Repeat steps 4-5 until satisfied!
        """)
        
        st.divider()
        
        st.header("🎬 Curated Demo Prompts")
        st.caption("Each mixes a concrete requirement with a subjective style cue.")

        for i, prompt in enumerate(CURATED_DEMO_PROMPTS):
            if st.button(prompt, key=f"curated_demo_{i}", use_container_width=True):
                st.session_state.description_input = prompt
                st.rerun()

        st.divider()

        st.header("💡 Example Prompts")
        examples = [
            "Create a login screen with a logo, email field, password field, and login button",
            "Build a profile card with a circular avatar, name, bio text, and follow button",
            "Design a settings screen with toggle switches for notifications, dark mode, and auto-update",
            "Create a product card with image, title, price, rating stars, and add to cart button",
            "Make a bottom navigation bar with home, search, favorites, and profile icons"
        ]
        
        for example in examples:
            if st.button(example, key=f"example_{examples.index(example)}", use_container_width=True):
                st.session_state.description_input = example
                st.rerun()
        
        st.divider()
        
        # History
        st.header("📜 Iteration History")
        if st.session_state.history:
            for item in reversed(st.session_state.history[-5:]):  # Show last 5
                with st.expander(f"Iteration {item['iteration']} - {item['timestamp']}"):
                    st.markdown(f"**Description:** {item['description'][:100]}...")
                    if item['feedback']:
                        st.markdown(f"**Feedback:** {item['feedback'][:100]}...")
        else:
            st.info("No history yet. Generate a UI to start!")
        
        st.divider()
        
        if st.button("🔄 Reset Session", use_container_width=True, type="secondary"):
            reset_session()
    
    # Main content area with tabs
    tab1, tab2 = st.tabs(["🎨 Generate & Refine", "📚 History"])
    
    with tab1:
        # Input section
        st.header("📝 Input")
        
        # Description input
        description = st.text_area(
            "UI Description",
            value=st.session_state.get('description_input', ''),
            placeholder="Example: Create a login screen with a logo, email field, password field, and login button",
            height=100,
            help="Describe the UI you want to generate in plain English"
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🚀 Generate UI", type="primary", use_container_width=True):
                generate_initial_ui(description)
        
        st.divider()
        
        # Refinement section
        st.header("🔄 Refinement")
        
        feedback = st.text_area(
            "Feedback for Refinement",
            placeholder="Example: Make the button larger, add spacing between fields, change colors to blue theme",
            height=100,
            help="What would you like to improve in the current UI?"
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("✨ Refine UI", type="primary", use_container_width=True):
                refine_ui(feedback)
        
        st.divider()
        
        # Output section
        if st.session_state.current_code:
            st.header("💻 Generated Code")
            
            # Create tabs for Code, Preview, Trace, and Validation -- Trace and
            # Validation Report are conditional since not every path produces them.
            tabs = ["📝 Code", "👁️ Preview"]
            trace_tab_index = None
            validation_tab_index = None
            if st.session_state.get('current_trace'):
                trace_tab_index = len(tabs)
                tabs.append("🔎 Trace")
            if st.session_state.get('validation_report'):
                validation_tab_index = len(tabs)
                tabs.append("🔍 Validation Report")

            tab_objects = st.tabs(tabs)
            
            # Code tab
            with tab_objects[0]:
                # Code display
                st.code(st.session_state.current_code, language="kotlin", line_numbers=True)
                
                # Download button - only show if code exists
                if st.session_state.current_code and len(st.session_state.current_code.strip()) > 0:
                    st.download_button(
                        label="📥 Download Code",
                        data=st.session_state.current_code,
                        file_name="GeneratedUI.kt",
                        mime="text/x-kotlin",
                        key=f"download_code_{st.session_state.iteration_count}"
                    )
                else:
                    st.info("No code to download yet. Generate UI first.")
            
            # Preview tab
            with tab_objects[1]:
                st.markdown("### Visual Structure Preview")
                st.markdown("*This is a visual representation of your UI layout hierarchy*")
                
                # Generate and display preview
                preview_html = generate_preview_html(st.session_state.current_code)
                st.markdown(preview_html, unsafe_allow_html=True)
                
                st.info("💡 **Tip:** This preview shows the structure and hierarchy of your UI components. For a real preview, copy the code into Android Studio.")

            # Trace tab (if available)
            if trace_tab_index is not None:
                with tab_objects[trace_tab_index]:
                    st.markdown("### 🔎 Execution Trace")
                    st.markdown("*Structured record of each node the graph executed, in order*")
                    render_trace_steps("", st.session_state.current_trace)

            # Validation Report tab (if available)
            if validation_tab_index is not None:
                with tab_objects[validation_tab_index]:
                    st.markdown("### 🔍 Validation Report")
                    st.markdown("*Automated code quality and compilation checks*")

                    report = st.session_state.validation_report

                    render_check_results("📋 Validation Checks", st.session_state.get('current_validation_checks', []))

                    st.divider()

                    # Compilation Check
                    st.subheader("🔨 Compilation Check")
                    compilation = report.get('compilation', {})
                    if compilation.get('success'):
                        st.success("✅ Code compiles successfully!")
                    else:
                        st.error("❌ Compilation failed")
                        errors = compilation.get('errors', [])
                        for error in errors:
                            st.code(error, language="text")

            st.divider()

            # Reviews
            st.header("📋 Reviews")

            col1, col2 = st.columns(2)

            with col1:
                render_review("♿ Accessibility Review", st.session_state.current_accessibility)

            with col2:
                render_review("🎨 Design Review", st.session_state.current_design)
        else:
            st.info("👆 Enter a UI description above and click 'Generate UI' to get started!")
    
    with tab2:
        st.header("📚 Complete History")
        
        if st.session_state.history:
            for item in reversed(st.session_state.history):
                with st.expander(f"**Iteration {item['iteration']}** - {item['timestamp']}", expanded=False):
                    st.markdown(f"**Description:** {item['description']}")
                    if item['feedback']:
                        st.markdown(f"**Feedback:** {item['feedback']}")
                    
                    st.markdown("**Code:**")
                    st.code(item['code'], language="kotlin")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**Accessibility:**")
                        if isinstance(item['accessibility'], list):
                            render_check_results("", item['accessibility'])
                        else:
                            st.markdown(item['accessibility'])
                    with col2:
                        st.markdown("**Design:**")
                        if isinstance(item['design'], list):
                            render_check_results("", item['design'])
                        else:
                            st.markdown(item['design'])
        else:
            st.info("No history yet. Generate a UI to start tracking iterations!")
    
    # Footer
    st.divider()
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem 0;">
        <p><strong>Tips for Best Results:</strong></p>
        <p>✅ Be specific about UI elements | ✅ Mention layout preferences | ✅ Include styling needs</p>
        <p>✅ Focus on 1-2 improvements per refinement | ✅ Use clear, actionable feedback</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
