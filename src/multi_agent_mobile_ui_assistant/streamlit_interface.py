"""
Streamlit Web Interface for Multi-Agent UI Generator

This module provides an interactive web UI for generating and refining
Jetpack Compose UI code with iterative improvements using Streamlit.
"""

import streamlit as st
from datetime import datetime
from .ui_generator import generate_ui_from_description
from .llm_config import get_default_llm
from langchain_core.messages import SystemMessage, HumanMessage
import json


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
            # Generate UI
            output = generate_ui_from_description(description)
            
            # Parse output
            code = extract_code_from_output(output)
            accessibility = extract_section(output, "ACCESSIBILITY REVIEW")
            design = extract_section(output, "DESIGN REVIEW")
            
            # Update session state
            st.session_state.current_code = code
            st.session_state.current_accessibility = accessibility
            st.session_state.current_design = design
            st.session_state.iteration_count += 1
            
            # Add to history
            st.session_state.history.append({
                "iteration": st.session_state.iteration_count,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "description": description,
                "code": code,
                "accessibility": accessibility,
                "design": design,
                "feedback": ""
            })
            
            st.success("✅ UI generated successfully!")
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
            llm = get_default_llm()
            
            # Create refinement prompt
            system_prompt = """You are a Jetpack Compose UI expert. You refine generated UI code based on user feedback.

Given the current code and user feedback, produce an improved version that addresses the feedback while maintaining:
- Proper Jetpack Compose syntax
- Material 3 guidelines
- Accessibility best practices
- Clean, readable code

Respond with a JSON object containing:
{
    "refined_code": "the complete improved @Composable function",
    "changes_made": ["list of improvements made"],
    "accessibility_notes": ["accessibility improvements"],
    "design_notes": ["design improvements"]
}

Only return valid JSON, no additional text."""

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
            
            # Parse response
            response_text = response.content
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(response_text)
            
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
            
            # Code display
            st.code(st.session_state.current_code, language="kotlin", line_numbers=True)
            
            # Download button
            st.download_button(
                label="📥 Download Code",
                data=st.session_state.current_code,
                file_name="GeneratedUI.kt",
                mime="text/plain"
            )
            
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
