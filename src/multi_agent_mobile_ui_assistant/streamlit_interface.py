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
    st.session_state.current_accessibility = ""
if 'current_design' not in st.session_state:
    st.session_state.current_design = ""
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
    
    for line in lines:
        if "@Composable" in line:
            in_code = True
        if in_code:
            code_lines.append(line)
        if in_code and line.strip() == "}" and len(code_lines) > 5:
            break
    
    return "\n".join(code_lines) if code_lines else output


def extract_section(output: str, section_name: str) -> str:
    """Extract a specific section from the output."""
    lines = output.split("\n")
    section_lines = []
    in_section = False
    
    for line in lines:
        if section_name in line:
            in_section = True
            continue
        if in_section:
            if "=" * 10 in line:
                break
            if line.strip().startswith("•"):
                section_lines.append(line)
    
    return "\n".join(section_lines) if section_lines else "No issues found"


def generate_initial_ui(description: str):
    """Generate initial UI from description."""
    if not description.strip():
        st.error("Please enter a UI description")
        return
    
    with st.spinner("🔮 Generating UI code..."):
        try:
            # Get options from session state
            validate = st.session_state.get('validate_code', True)
            return_report = st.session_state.get('show_validation_report', False)
            multi_file = st.session_state.get('multi_file', False)
            
            # Generate UI with options
            output = generate_ui_from_description(
                description,
                validate=validate,
                return_report=return_report and validate,
                multi_file=multi_file
            )
            
            # Handle validation report if returned
            validation_report = None
            if isinstance(output, dict) and 'code' in output:
                code = output['code']
                validation_report = output.get('validation_report')
            else:
                code = output
            
            # Parse output
            if not multi_file:
                code_text = extract_code_from_output(code) if isinstance(code, str) else code
            else:
                code_text = code  # Multi-file returns structured data
                
            accessibility = extract_section(code if isinstance(code, str) else str(code), "ACCESSIBILITY REVIEW")
            design = extract_section(code if isinstance(code, str) else str(code), "DESIGN REVIEW")
            
            # Update session state
            st.session_state.current_code = code_text
            st.session_state.current_accessibility = accessibility
            st.session_state.current_design = design
            st.session_state.iteration_count += 1
            st.session_state.validation_report = validation_report
            
            # Add to history
            st.session_state.history.append({
                "iteration": st.session_state.iteration_count,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "description": description,
                "code": code_text,
                "accessibility": accessibility,
                "design": design,
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
            
            # Update session state
            st.session_state.current_code = refined_code
            st.session_state.current_accessibility = accessibility_review
            st.session_state.current_design = design_review
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
    st.session_state.current_accessibility = ""
    st.session_state.current_design = ""
    st.session_state.iteration_count = 0
    st.success("Session reset successfully!")
    st.rerun()


def generate_preview_html(code: str) -> str:
    """
    Generate an HTML preview visualization of the Compose UI structure.
    This creates a visual representation of the layout hierarchy.
    """
    if not code:
        return "<p>No code to preview</p>"
    
    # Parse the code to extract UI structure
    lines = code.split('\n')
    preview_html = ['<div style="font-family: system-ui; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px;">']
    preview_html.append('<div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">')
    
    indent_level = 0
    component_colors = {
        'Column': '#4CAF50',
        'Row': '#2196F3',
        'Card': '#FF9800',
        'Box': '#9C27B0',
        'Text': '#607D8B',
        'Button': '#F44336',
        'Image': '#00BCD4',
        'TextField': '#FFC107',
        'LazyColumn': '#8BC34A',
        'LazyRow': '#3F51B5'
    }
    
    for line in lines:
        stripped = line.strip()
        
        # Detect containers
        for component in ['Column', 'Row', 'Card', 'Box', 'LazyColumn', 'LazyRow']:
            if f'{component}(' in stripped:
                color = component_colors.get(component, '#666')
                preview_html.append(f'<div style="margin: 8px 0; padding: 12px; border-left: 4px solid {color}; background: #f5f5f5; border-radius: 4px;">')
                preview_html.append(f'<strong style="color: {color};">📦 {component}</strong>')
                
                # Extract modifiers
                if 'padding' in stripped:
                    preview_html.append(' <span style="color: #666; font-size: 0.85em;">• padding</span>')
                if 'fillMaxSize' in stripped or 'fillMaxWidth' in stripped:
                    preview_html.append(' <span style="color: #666; font-size: 0.85em;">• fill</span>')
                
                indent_level += 1
        
        # Detect UI components
        if 'Text(' in stripped:
            # Extract text content
            if 'text = "' in stripped:
                text_content = stripped.split('text = "')[1].split('"')[0]
                preview_html.append(f'<div style="margin: 8px 0 8px {indent_level * 20}px; padding: 8px; background: #e3f2fd; border-left: 3px solid {component_colors["Text"]}; border-radius: 3px;">')
                preview_html.append(f'📝 <strong>Text:</strong> "{text_content}"')
                preview_html.append('</div>')
        
        elif 'Button(' in stripped and 'Text(' in code[code.index(stripped):code.index(stripped)+200]:
            # Try to find button text
            button_text = "Button"
            next_lines = '\n'.join(lines[lines.index(line):min(lines.index(line)+5, len(lines))])
            if 'Text("' in next_lines:
                try:
                    button_text = next_lines.split('Text("')[1].split('"')[0]
                except (IndexError, ValueError):
                    pass
            
            preview_html.append(f'<div style="margin: 8px 0 8px {indent_level * 20}px; padding: 10px 16px; background: {component_colors["Button"]}; color: white; border-radius: 4px; display: inline-block; font-weight: 500;">')
            preview_html.append(f'🔘 {button_text}')
            preview_html.append('</div>')
        
        elif 'Image(' in stripped or 'Box(' in stripped and 'Image' in code:
            preview_html.append(f'<div style="margin: 8px 0 8px {indent_level * 20}px; padding: 20px; background: linear-gradient(135deg, #e0e0e0 0%, #bdbdbd 100%); border-radius: 4px; text-align: center; color: #666;">')
            preview_html.append('🖼️ <strong>Image Placeholder</strong>')
            preview_html.append('</div>')
        
        elif 'TextField(' in stripped:
            hint = "Enter text"
            if 'hint = "' in stripped:
                try:
                    hint = stripped.split('hint = "')[1].split('"')[0]
                except (IndexError, ValueError):
                    pass
            preview_html.append(f'<div style="margin: 8px 0 8px {indent_level * 20}px; padding: 10px; border: 2px solid {component_colors["TextField"]}; border-radius: 4px; background: white;">')
            preview_html.append(f'✏️ <span style="color: #999;">{hint}</span>')
            preview_html.append('</div>')
        
        # Close containers
        if stripped == '}' or stripped == '})':
            if indent_level > 0:
                indent_level -= 1
                preview_html.append('</div>')
    
    preview_html.append('</div>')
    preview_html.append('</div>')
    
    return '\n'.join(preview_html)


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
        
        provider_option = st.selectbox(
            "LLM Provider",
            options=["ollama", "openai"],
            index=0 if st.session_state.llm_provider == "ollama" else 1,
            help="Choose between local Ollama or OpenAI API",
            key="llm_provider_select"
        )
        
        # Update session state if changed
        if provider_option != st.session_state.llm_provider:
            st.session_state.llm_provider = provider_option
            # Update default model based on provider
            if provider_option == "ollama":
                st.session_state.llm_model = "llama3.2"
            else:
                st.session_state.llm_model = "gpt-4o-mini"
        
        # Model selection
        model_name = st.text_input(
            "Model Name",
            value=st.session_state.llm_model,
            help="For Ollama: llama3.2, codellama, etc.\nFor OpenAI: gpt-4o-mini, gpt-4, gpt-3.5-turbo, etc.",
            key="llm_model_input"
        )
        
        # Update session state if changed
        if model_name != st.session_state.llm_model:
            st.session_state.llm_model = model_name
        
        # Show current configuration
        st.info(f"✓ Using **{st.session_state.llm_provider}** with model **{st.session_state.llm_model}**")
        
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
        
        # Show validation report
        show_validation_report = st.checkbox(
            "Show Validation Report",
            value=st.session_state.get('show_validation_report', False),
            help="Display detailed validation report including lint issues and compilation checks",
            key="validation_report_checkbox",
            disabled=not validate_code
        )
        st.session_state.show_validation_report = show_validation_report
        
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
            
            # Create tabs for Code, Preview, and Validation
            tabs = ["📝 Code", "👁️ Preview"]
            if st.session_state.get('validation_report'):
                tabs.append("🔍 Validation Report")
            
            tab_objects = st.tabs(tabs)
            
            # Code tab
            with tab_objects[0]:
                # Code display
                st.code(st.session_state.current_code, language="kotlin", line_numbers=True)
                
                # Download button
                st.download_button(
                    label="📥 Download Code",
                    data=st.session_state.current_code,
                    file_name="GeneratedUI.kt",
                    mime="text/plain"
                )
            
            # Preview tab
            with tab_objects[1]:
                st.markdown("### Visual Structure Preview")
                st.markdown("*This is a visual representation of your UI layout hierarchy*")
                
                # Generate and display preview
                preview_html = generate_preview_html(st.session_state.current_code)
                st.markdown(preview_html, unsafe_allow_html=True)
                
                st.info("💡 **Tip:** This preview shows the structure and hierarchy of your UI components. For a real preview, copy the code into Android Studio.")
            
            # Validation Report tab (if available)
            if st.session_state.get('validation_report'):
                with tab_objects[2]:
                    st.markdown("### 🔍 Validation Report")
                    st.markdown("*Automated code quality and compilation checks*")
                    
                    report = st.session_state.validation_report
                    
                    # Lint Issues
                    st.subheader("📋 Lint Issues")
                    lint_issues = report.get('lint_issues', [])
                    if lint_issues:
                        for issue in lint_issues:
                            severity = issue.get('severity', 'info')
                            icon = "🔴" if severity == "error" else "🟡" if severity == "warning" else "🔵"
                            st.markdown(f"{icon} **{issue.get('message', 'Unknown issue')}**")
                            if issue.get('line'):
                                st.caption(f"Line {issue['line']}")
                    else:
                        st.success("✅ No lint issues found!")
                    
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
                    
                    # Auto-fixes Applied
                    if report.get('auto_fixes'):
                        st.subheader("🔧 Auto-fixes Applied")
                        st.info(f"Applied {len(report['auto_fixes'])} automatic fixes to the code")
                        for fix in report['auto_fixes']:
                            st.markdown(f"• {fix}")
            
            st.divider()
            
            # Reviews
            st.header("📋 Reviews")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("♿ Accessibility Review")
                st.markdown(f'<div class="review-section">{st.session_state.current_accessibility}</div>', unsafe_allow_html=True)
            
            with col2:
                st.subheader("🎨 Design Review")
                st.markdown(f'<div class="review-section">{st.session_state.current_design}</div>', unsafe_allow_html=True)
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
                        st.markdown(item['accessibility'])
                    with col2:
                        st.markdown("**Design:**")
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
