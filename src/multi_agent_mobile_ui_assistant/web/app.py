"""
Streamlit Web Interface for Multi-Agent UI Generator.

Provides an interactive web UI for generating and refining
Jetpack Compose UI code with iterative improvements.
"""

import streamlit as st
import json
from datetime import datetime
from langchain_core.messages import SystemMessage, HumanMessage

from ..core.pipeline import generate_ui_from_description
from ..config.llm import create_llm
from ..mcp.figma import FigmaMCP
from ..preview.visualizer import generate_preview_html

# Page configuration
st.set_page_config(
    page_title="Multi-Agent UI Generator",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 0.5rem 0 1.5rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 800;
    }
    .review-box {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []
if "current_code" not in st.session_state:
    st.session_state.current_code = ""
if "current_accessibility" not in st.session_state:
    st.session_state.current_accessibility = ""
if "current_design" not in st.session_state:
    st.session_state.current_design = ""
if "iteration_count" not in st.session_state:
    st.session_state.iteration_count = 0
if "llm_provider" not in st.session_state:
    st.session_state.llm_provider = "ollama"
if "llm_model" not in st.session_state:
    st.session_state.llm_model = "llama3.2"


def get_llm_for_session():
    """Create an LLM instance based on current session preferences."""
    return create_llm(
        provider=st.session_state.llm_provider,
        model=st.session_state.llm_model,
    )


def extract_code_from_output(output: str) -> str:
    """
    Extract the full Kotlin code (including imports) from output report.
    """
    if "GENERATED JETPACK COMPOSE UI CODE" in output:
        parts = output.split("GENERATED JETPACK COMPOSE UI CODE")
        if len(parts) > 1:
            code_section = parts[1]
            if "ACCESSIBILITY REVIEW" in code_section:
                code_section = code_section.split("ACCESSIBILITY REVIEW")[0]
            # Strip separator lines
            lines = [l for l in code_section.split("\n") if not l.startswith("=" * 10)]
            return "\n".join(lines).strip()
    return output.strip()


def extract_section(output: str, section_name: str) -> str:
    """Extract review bullet points from the output report."""
    if section_name not in output:
        return "No issues found"

    lines = output.split("\n")
    section_lines = []
    in_section = False
    header_separator_skipped = False

    for line in lines:
        stripped = line.strip()
        if section_name in line:
            in_section = True
            continue
        if in_section:
            if stripped.startswith("=" * 10):
                if not header_separator_skipped:
                    header_separator_skipped = True
                    continue
                else:
                    break
            # Break if next section header starts
            if any(h in stripped for h in ["DESIGN REVIEW", "ACCESSIBILITY REVIEW", "GENERATED JETPACK COMPOSE"]) and not stripped.startswith("•"):
                break
            if stripped.startswith("•"):
                section_lines.append(stripped)

    return "\n".join(section_lines) if section_lines else "No specific issues identified."


def generate_initial_ui(description: str):
    """Trigger initial UI generation from user prompt or Figma."""
    if not description.strip():
        st.error("Please enter a UI description.")
        return

    with st.spinner("⚡ Generating Jetpack Compose UI with AI agents..."):
        try:
            validate = st.session_state.get("validate_code", True)
            use_figma = st.session_state.get("use_figma", False)

            code_text = ""
            accessibility = ""
            design = ""
            validation_report = None

            if use_figma:
                token = st.session_state.get("figma_token", "")
                key = st.session_state.get("figma_file_key", "")
                if token and key:
                    with st.spinner("🎨 Fetching Figma design tokens..."):
                        figma = FigmaMCP(access_token=token)
                        design_data = figma.extract_design(file_key=key)
                        code_text = figma.convert_to_compose(design_data)
                        accessibility = "• Generated directly from Figma layout tokens"
                        design = f"• Imported {len(design_data.colors)} colors, {len(design_data.typography)} styles"
                        st.success(f"✅ Imported Figma design: {design_data.name}")
                else:
                    st.warning("Figma credentials missing. Falling back to prompt generation.")

            if not code_text:
                result = generate_ui_from_description(
                    user_description=description,
                    validate=validate,
                    return_report=True,
                )
                if isinstance(result, dict):
                    code_text = result.get("code", "")
                    raw_output = result.get("final_output", "")
                    validation_report = result.get("validation_report")
                else:
                    code_text = extract_code_from_output(result)
                    raw_output = result

                accessibility = extract_section(raw_output, "ACCESSIBILITY REVIEW")
                design = extract_section(raw_output, "DESIGN REVIEW")

            st.session_state.current_code = code_text
            st.session_state.current_accessibility = accessibility
            st.session_state.current_design = design
            st.session_state.iteration_count += 1
            st.session_state.validation_report = validation_report

            st.session_state.history.append({
                "iteration": st.session_state.iteration_count,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "description": description,
                "code": code_text,
                "accessibility": accessibility,
                "design": design,
                "feedback": "",
                "validation_report": validation_report,
            })

            st.success("✅ UI generation complete!")
            st.rerun()
        except Exception as e:
            st.error(f"Error during UI generation: {str(e)}")


def refine_ui(feedback: str):
    """Iteratively refine the current Compose code based on feedback."""
    if not feedback.strip():
        st.error("Please provide feedback for refinement.")
        return
    if not st.session_state.current_code:
        st.error("No active code to refine. Generate a UI first.")
        return

    with st.spinner("✨ Refining Compose code with agent..."):
        try:
            llm = get_llm_for_session()

            prompt = f"""You are a senior Android Jetpack Compose engineer. Refine the existing Compose code based on user feedback.

Current Code:
```kotlin
{st.session_state.current_code}
```

User Feedback:
{feedback}

Return a valid JSON object with this exact structure:
{{
    "refined_code": "the complete updated Kotlin code with imports",
    "changes_made": ["change 1", "change 2"],
    "accessibility_notes": ["note 1"],
    "design_notes": ["note 1"]
}}
Return ONLY the JSON object.
"""
            response = llm.invoke([
                SystemMessage(content="You are an expert Compose developer."),
                HumanMessage(content=prompt),
            ])

            res_text = response.content.strip()
            if "```json" in res_text:
                res_text = res_text.split("```json")[1].split("```")[0].strip()
            elif "```" in res_text:
                res_text = res_text.split("```")[1].split("```")[0].strip()

            try:
                data = json.loads(res_text, strict=False)
                refined_code = data.get("refined_code", st.session_state.current_code)
                changes = data.get("changes_made", [])
                acc_notes = data.get("accessibility_notes", [])
                des_notes = data.get("design_notes", [])
            except Exception:
                refined_code = res_text
                changes = ["Applied user feedback"]
                acc_notes = ["Review accessibility for new elements"]
                des_notes = ["Applied design updates"]

            accessibility_review = "\n".join([f"• {n}" for n in acc_notes])
            design_review = "\n".join([f"• {n}" for n in des_notes] + [f"• Change: {c}" for c in changes])

            st.session_state.current_code = refined_code
            st.session_state.current_accessibility = accessibility_review
            st.session_state.current_design = design_review
            st.session_state.iteration_count += 1

            last_desc = st.session_state.history[-1]["description"] if st.session_state.history else "Refinement"
            st.session_state.history.append({
                "iteration": st.session_state.iteration_count,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "description": last_desc,
                "code": refined_code,
                "accessibility": accessibility_review,
                "design": design_review,
                "feedback": feedback,
            })

            st.success("✅ UI refined successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Error refining UI: {str(e)}")


def main():
    st.markdown('<h1 class="main-header">📱 Multi-Agent Jetpack Compose Assistant</h1>', unsafe_allow_html=True)
    st.caption("Generate production-ready Jetpack Compose UI code from natural language or Figma designs.")

    # Sidebar settings
    with st.sidebar:
        st.header("⚙️ Model Settings")

        llm_options = {
            "Ollama - Llama 3.2": {"provider": "ollama", "model": "llama3.2"},
            "Ollama - CodeLlama": {"provider": "ollama", "model": "codellama"},
            "OpenAI - GPT-4o Mini": {"provider": "openai", "model": "gpt-4o-mini"},
            "OpenAI - GPT-4o": {"provider": "openai", "model": "gpt-4o"},
            "Custom": {"provider": "custom", "model": "custom"},
        }

        current_sel = "Ollama - Llama 3.2"
        for name, cfg in llm_options.items():
            if cfg["provider"] == st.session_state.llm_provider and cfg["model"] == st.session_state.llm_model:
                current_sel = name
                break

        selected_option = st.selectbox("Select Model", options=list(llm_options.keys()), index=list(llm_options.keys()).index(current_sel))

        if selected_option != "Custom":
            st.session_state.llm_provider = llm_options[selected_option]["provider"]
            st.session_state.llm_model = llm_options[selected_option]["model"]
        else:
            st.session_state.llm_provider = st.text_input("Provider (ollama/openai)", value=st.session_state.llm_provider)
            st.session_state.llm_model = st.text_input("Model Name", value=st.session_state.llm_model)

        st.info(f"Using **{st.session_state.llm_provider}** / `{st.session_state.llm_model}`")
        st.divider()

        st.header("🎨 Figma Integration")
        use_figma = st.checkbox("Import from Figma", value=st.session_state.get("use_figma", False))
        st.session_state.use_figma = use_figma
        if use_figma:
            st.session_state.figma_token = st.text_input("Figma Personal Access Token", type="password")
            st.session_state.figma_file_key = st.text_input("Figma File Key")

        st.divider()
        st.session_state.validate_code = st.checkbox("Run Android Lint & Auto-Fix", value=True)

        if st.button("🔄 Reset Session", use_container_width=True):
            st.session_state.history = []
            st.session_state.current_code = ""
            st.session_state.current_accessibility = ""
            st.session_state.current_design = ""
            st.session_state.iteration_count = 0
            st.rerun()

    # Main Tabs
    tab_gen, tab_preview, tab_reviews, tab_history = st.tabs(["🚀 Generator", "👁️ Preview", "📋 Agent Reviews", "📜 History"])

    with tab_gen:
        col_input, col_out = st.columns([1, 1])

        with col_input:
            st.subheader("1. Describe UI")
            desc_input = st.text_area(
                "UI Prompt",
                height=160,
                placeholder="e.g., Login screen with app logo, email field, password field with visibility toggle, forgot password button, login button, and social sign-in row.",
                key="desc_input_area",
            )

            if st.button("✨ Generate Jetpack Compose UI", type="primary", use_container_width=True):
                generate_initial_ui(desc_input)

            if st.session_state.current_code:
                st.divider()
                st.subheader("2. Refine & Iterate")
                feedback_input = st.text_input("Feedback for Agent", placeholder="e.g., Make the login button full width and add 24dp vertical spacing")
                if st.button("🔁 Apply Refinements", use_container_width=True):
                    refine_ui(feedback_input)

        with col_out:
            st.subheader("Generated Kotlin / Compose Code")
            if st.session_state.current_code:
                st.code(st.session_state.current_code, language="kotlin")
                st.download_button(
                    label="💾 Download .kt File",
                    data=st.session_state.current_code,
                    file_name="GeneratedScreen.kt",
                    mime="text/plain",
                    use_container_width=True,
                )
            else:
                st.info("Your generated Jetpack Compose code will appear here.")

    with tab_preview:
        st.subheader("Visual Layout Mock")
        if st.session_state.current_code:
            html_preview = generate_preview_html(st.session_state.current_code)
            st.components.v1.html(html_preview, height=520, scrolling=True)
        else:
            st.info("Generate a UI to see its visual layout mockup.")

    with tab_reviews:
        st.subheader("Agent Audit Reports")
        if st.session_state.current_code:
            st.markdown("### ♿ Accessibility Reviewer")
            st.markdown(f'<div class="review-box">{st.session_state.current_accessibility}</div>', unsafe_allow_html=True)

            st.markdown("### 📐 Material 3 Design Reviewer")
            st.markdown(f'<div class="review-box">{st.session_state.current_design}</div>', unsafe_allow_html=True)
        else:
            st.info("Reviews will be generated alongside the UI code.")

    with tab_history:
        st.subheader("Iteration History")
        if st.session_state.history:
            for item in reversed(st.session_state.history):
                with st.expander(f"Iteration #{item['iteration']} - {item['timestamp']}"):
                    st.write(f"**Prompt:** {item['description']}")
                    if item.get("feedback"):
                        st.write(f"**Feedback:** {item['feedback']}")
                    st.code(item["code"], language="kotlin")
        else:
            st.info("No iterations recorded yet.")


if __name__ == "__main__":
    main()
