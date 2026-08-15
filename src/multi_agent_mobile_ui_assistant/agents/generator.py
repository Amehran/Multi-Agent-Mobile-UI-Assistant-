"""
UI Generator Agent.

Directly generates production-ready Jetpack Compose UI code from natural language
descriptions enriched with MCP tools (GitHub examples, project context, Figma tokens).
"""

from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage
from ..config.llm import get_default_llm
from ..core.state import UIGeneratorState
from ..mcp.android_tools import AndroidLintMCP


SYSTEM_PROMPT = """You are an expert Android Jetpack Compose engineer. Generate complete, production-ready Compose code.

CRITICAL RULES - FOLLOW EXACTLY:
1. Generate ONLY valid Kotlin Jetpack Compose code.
2. Use Material 3 components (androidx.compose.material3.*).
3. Include ALL necessary imports at the top.
4. Use proper modifier ordering: .fillMaxWidth() THEN .padding() THEN .height().
5. For TextFields, ALWAYS use OutlinedTextField with remember { mutableStateOf("") }.
6. For spacing, ALWAYS use: Spacer(modifier = Modifier.height(X.dp)).
7. Use proper typography: MaterialTheme.typography.headlineLarge, bodyMedium, etc.
8. For buttons: Button(onClick = {}, modifier = Modifier.fillMaxWidth().height(48.dp)).
9. Use Column with: verticalArrangement = Arrangement.Top, horizontalAlignment = Alignment.CenterHorizontally.
10. For password fields: visualTransformation = PasswordVisualTransformation().
11. For icons: Icon(imageVector = Icons.Default.IconName, contentDescription = "...").
12. For dividers with text: Use Row with HorizontalDivider and Text.
13. MATCH THE EXACT SPECIFICATIONS: If the user requests specific fields/labels, include all of them.
14. PRESERVE EXACT SPACING: Use the exact dp values specified.

OUTPUT FORMAT:
Return ONLY the complete Kotlin code. Start with imports, end with closing brace. No markdown fences, no explanatory text.
"""


def ui_generator_agent(state: UIGeneratorState) -> Dict[str, Any]:
    """
    UI Generator Agent: Synthesizes Jetpack Compose UI code from the user description.

    Args:
        state: Current workflow state

    Returns:
        Updated state dictionary with generated code
    """
    user_input = state.get("user_input", "")
    github_examples = state.get("github_examples", [])
    project_context = state.get("project_context", {})
    use_llm = state.get("use_llm_generation", True)

    print("\n[UI Generator] Generating Jetpack Compose code from user prompt...")

    if not use_llm:
        # Fallback template mode
        generated_code = _generate_template_code(user_input)
    else:
        # Build prompt context
        context_parts = []
        if github_examples:
            context_parts.append("Here are some real Jetpack Compose examples for reference:")
            for i, example in enumerate(github_examples[:3], 1):
                desc = getattr(example, "description", str(example))
                code_snippet = getattr(example, "code", "")[:400]
                context_parts.append(f"\nExample {i}: {desc}\n```kotlin\n{code_snippet}...\n```")

        if project_context.get("existing_composables"):
            comp_names = [
                c.get("name", str(c)) if isinstance(c, dict) else str(c)
                for c in project_context["existing_composables"][:5]
            ]
            context_parts.append(f"\nExisting composables in project: {', '.join(comp_names)}")

        user_prompt_lines = [
            "=== USER REQUIREMENTS ===",
            user_input,
            "\n=== MANDATORY IMPORTS ===",
            """import androidx.compose.foundation.layout.*
import androidx.compose.foundation.clickable
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp""",
        ]

        if context_parts:
            user_prompt_lines.append("\n=== REFERENCE CONTEXT ===")
            user_prompt_lines.append("\n".join(context_parts))

        user_prompt_lines.append("\nGenerate complete, standalone Jetpack Compose code now.")

        llm = get_default_llm()
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content="\n".join(user_prompt_lines)),
        ]

        try:
            response = llm.invoke(messages)
            raw_content = response.content if hasattr(response, "content") else str(response)
            generated_code = _extract_clean_code(str(raw_content).strip())
        except Exception as e:
            print(f"[UI Generator] LLM generation error: {e}, falling back to template")
            generated_code = _generate_template_code(user_input)

    # Apply auto-fix if requested
    if state.get("validate_code", False):
        lint = AndroidLintMCP()
        generated_code = lint.auto_fix(generated_code)

    return {
        "messages": [{"role": "assistant", "content": "UI code generation complete"}],
        "generated_code": generated_code,
        "current_step": "code_generated",
    }


def _extract_clean_code(raw_code: str) -> str:
    """Clean markdown code blocks and ensure proper imports header."""
    code = raw_code.strip()

    # Extract code from markdown fences if present
    if "```kotlin" in code:
        code = code.split("```kotlin")[1].split("```")[0].strip()
    elif "```java" in code:
        code = code.split("```java")[1].split("```")[0].strip()
    elif "```" in code:
        parts = code.split("```")
        if len(parts) >= 3:
            code = parts[1].strip()
            lines = code.split("\n")
            if lines and lines[0].strip() in ["kotlin", "java", "kt"]:
                code = "\n".join(lines[1:]).strip()

    # Ensure baseline imports if missing
    if not code.startswith("import") and "@Composable" in code:
        default_imports = [
            "import androidx.compose.runtime.Composable",
            "import androidx.compose.ui.Modifier",
            "import androidx.compose.material3.*",
            "import androidx.compose.foundation.layout.*",
            "import androidx.compose.foundation.clickable",
            "import androidx.compose.material.icons.Icons",
            "import androidx.compose.material.icons.filled.*",
            "import androidx.compose.ui.unit.dp",
            "import androidx.compose.runtime.remember",
            "import androidx.compose.runtime.mutableStateOf",
            "import androidx.compose.runtime.getValue",
            "import androidx.compose.runtime.setValue",
            "import androidx.compose.ui.Alignment",
            "import androidx.compose.ui.graphics.Color",
            "import androidx.compose.ui.text.font.FontWeight",
            "",
        ]
        code = "\n".join(default_imports) + "\n" + code

    return code


def _generate_template_code(user_input: str) -> str:
    """Generate deterministic template Compose code for offline/fallback mode."""
    return f"""import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.material3.*
import androidx.compose.foundation.layout.*
import androidx.compose.ui.unit.dp
import androidx.compose.ui.Alignment

@Composable
fun GeneratedUI() {{
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {{
        Text(
            text = "{user_input or 'Jetpack Compose UI'}",
            style = MaterialTheme.typography.headlineMedium
        )
        Spacer(modifier = Modifier.height(16.dp))
        Button(onClick = {{ /* Action */ }}) {{
            Text("Action Button")
        }}
    }}
}}"""
