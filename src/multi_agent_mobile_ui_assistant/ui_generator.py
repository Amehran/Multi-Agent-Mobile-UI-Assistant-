"""
Multi-Agent Jetpack Compose UI Generator

This module implements a LangGraph-based multi-agent system that generates
functional, high-quality Jetpack Compose UI code from natural language descriptions.

Agent Flow:
User Input → Intent Parser → Layout Planner → UI Generator → 
Accessibility Reviewer → UI Reviewer → Output
"""

from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import SystemMessage, HumanMessage
from .llm_config import get_default_llm
import json


class UIGeneratorState(TypedDict):
    """State for the UI generator workflow."""
    messages: Annotated[list, add_messages]
    user_input: str
    parsed_intent: dict
    layout_plan: dict
    generated_code: str
    accessibility_issues: list[str]
    design_issues: list[str]
    final_output: str
    current_step: str
    github_examples: list  # MCP: GitHub examples for context
    project_context: dict  # MCP: Existing project info
    multi_file: bool  # MCP: Generate multiple files
    validate_code: bool  # Android Tools MCP: Run validation


# ============================================================================
# Agent: Intent Parser
# ============================================================================

def intent_parser_agent(state: UIGeneratorState) -> UIGeneratorState:
    """
    Intent Parser Agent: Extracts UI elements, layout hierarchy, 
    styles, and actions from natural language using LLM.
    """
    user_input = state.get("user_input", "")
    print(f"\n[Intent Parser] Analyzing: '{user_input}'")
    
    # Get LLM instance
    llm = get_default_llm()
    
    # Create prompt for intent parsing
    system_prompt = """You are a UI intent parser. Extract UI components and layout information from user descriptions.

Respond with a JSON object containing:
- ui_elements: array of UI components (type, text/content, style, action)
- layout_type: main container type (Column, Row, Card, Box, etc.)
- styles: any specific styling requirements
- actions: any user interactions mentioned

Component types: Text, Button, Image, TextField, Icon, Divider, Spacer
Layout types: Column, Row, Card, Box, LazyColumn, LazyRow

Example input: "Create a login screen with a title, email field, password field, and login button"
Example output:
{
    "ui_elements": [
        {"type": "Text", "content": "Login", "style": "headlineLarge"},
        {"type": "TextField", "content": "Email", "hint": "Enter your email"},
        {"type": "TextField", "content": "Password", "hint": "Enter your password", "secure": true},
        {"type": "Button", "text": "Login", "action": "onLogin"}
    ],
    "layout_type": "Column",
    "styles": {"spacing": "medium", "alignment": "center"},
    "actions": ["onLogin"]
}

Only return valid JSON, no additional text."""

    # Call LLM
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_input)
    ]
    
    response = llm.invoke(messages)
    
    # Parse LLM response
    try:
        # Extract JSON from response
        response_text = response.content
        # Handle potential markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        parsed_intent = json.loads(response_text)
        print(f"[Intent Parser] Extracted {len(parsed_intent.get('ui_elements', []))} UI elements")
        print(f"[Intent Parser] Layout type: {parsed_intent.get('layout_type', 'Column')}")
    except (json.JSONDecodeError, IndexError, AttributeError) as e:
        print(f"[Intent Parser] Warning: Failed to parse LLM response: {e}")
        print(f"[Intent Parser] Response: {response.content}")
        # Fallback to default structure
        parsed_intent = {
            "ui_elements": [
                {"type": "Text", "content": "Error parsing intent", "style": "bodyLarge"}
            ],
            "layout_type": "Column",
            "styles": {},
            "actions": []
        }
    
    return {
        "messages": [{"role": "assistant", "content": "Intent parsing complete"}],
        "parsed_intent": parsed_intent,
        "current_step": "intent_parsed"
    }


# ============================================================================
# Agent: Layout Planner
# ============================================================================

def layout_planner_agent(state: UIGeneratorState) -> UIGeneratorState:
    """
    Layout Planner Agent: Translates parsed intent into structured layout
    (Column, Row, Box, etc.) following Compose best practices.
    """
    parsed_intent = state.get("parsed_intent", {})
    print(f"\n[Layout Planner] Creating layout plan...")
    
    layout_plan = {
        "root_container": parsed_intent.get("layout_type", "Column"),
        "children": [],
        "modifiers": ["fillMaxSize", "padding(16.dp)"],
        "arrangement": "Center" if parsed_intent.get("layout_type") == "Column" else "Start"
    }
    
    # Plan the layout structure
    for element in parsed_intent.get("ui_elements", []):
        layout_plan["children"].append({
            "component": element["type"],
            "properties": element,
            "modifiers": []
        })
    
    print(f"[Layout Planner] Planned {len(layout_plan['children'])} components")
    print(f"[Layout Planner] Root container: {layout_plan['root_container']}")
    
    return {
        "messages": [{"role": "assistant", "content": "Layout planning complete"}],
        "layout_plan": layout_plan,
        "current_step": "layout_planned"
    }


# ============================================================================
# Agent: UI Generator
# ============================================================================

def ui_generator_agent(state: UIGeneratorState) -> UIGeneratorState:
    """
    UI Generator Agent: Generates actual Jetpack Compose code
    from the layout plan using LLM, enriched with GitHub examples if available.
    """
    layout_plan = state.get("layout_plan", {})
    parsed_intent = state.get("parsed_intent", {})
    user_input = state.get("user_input", "")
    github_examples = state.get("github_examples", [])
    project_context = state.get("project_context", {})
    use_llm = state.get("use_llm_generation", True)  # Default to True for production
    
    print("\n[UI Generator] Generating Jetpack Compose code...")
    
    # If LLM is disabled (for testing), use fallback
    if not use_llm:
        print("[UI Generator] Using fallback template generation (testing mode)")
        generated_code = _generate_template_code(layout_plan)
    else:
        # Build context for LLM
        context_parts = []
        
        # Add GitHub examples if available
        if github_examples:
            print(f"[UI Generator] Using {len(github_examples)} GitHub examples as reference")
            context_parts.append("Here are some real Jetpack Compose examples for reference:")
            for i, example in enumerate(github_examples[:3], 1):
                context_parts.append(f"\nExample {i}: {example.description}")
                context_parts.append(f"```kotlin\n{example.code[:500]}...\n```")
        
        # Add project context if available
        if project_context.get("existing_composables"):
            print(f"[UI Generator] Found {len(project_context['existing_composables'])} existing composables")
            context_parts.append(f"\nExisting composables in project: {', '.join(project_context['existing_composables'][:5])}")
        
        # Create detailed prompt for LLM
        system_prompt = """You are an expert Jetpack Compose developer. Generate complete, production-ready Compose code.

CRITICAL RULES - FOLLOW EXACTLY:
1. Generate ONLY valid Kotlin Jetpack Compose code
2. Use Material3 components (androidx.compose.material3.*)
3. Include ALL necessary imports at the top
4. Use proper modifiers in THIS ORDER: .fillMaxWidth() THEN .padding() THEN .height()
5. For TextFields, ALWAYS use OutlinedTextField with:
   - var state by remember { mutableStateOf("") }
   - value = state
   - onValueChange = { state = it }
   - label = { Text("Label") }
   - placeholder = { Text("Hint text") }
6. For spacing, ALWAYS use: Spacer(modifier = Modifier.height(XYdp))
7. Use proper typography: MaterialTheme.typography.headlineLarge, bodyMedium, etc.
8. For buttons: Button(onClick = {}, modifier = Modifier.fillMaxWidth().height(48.dp))
9. Use Column with: verticalArrangement = Arrangement.Top, horizontalAlignment = Alignment.CenterHorizontally
10. For password fields: visualTransformation = PasswordVisualTransformation()
11. For icons: use Icon(imageVector = Icons.Default.IconName, contentDescription = "...")
12. For dividers with text: Use Row with HorizontalDivider and Text
13. MATCH THE EXACT COMPONENT COUNT: If user specifies 18 components, generate exactly 18 components
14. PRESERVE EXACT SPACING: Use the exact dp values specified (24dp, 32dp, 16dp, 8dp)
15. For images/logos: Use Icon() or Box() with specified size

EXAMPLE STRUCTURE FOR LOGIN SCREEN:
```kotlin
@Composable
fun LoginScreen() {
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var passwordVisible by remember { mutableStateOf(false) }
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Top
    ) {
        // Logo
        Icon(
            imageVector = Icons.Default.AccountCircle,
            contentDescription = "Logo",
            modifier = Modifier.size(80.dp)
        )
        
        Spacer(modifier = Modifier.height(24.dp))
        
        // Title
        Text(
            text = "Welcome Back",
            style = MaterialTheme.typography.headlineLarge,
            fontWeight = FontWeight.Bold
        )
        
        // Email TextField
        OutlinedTextField(
            value = email,
            onValueChange = { email = it },
            label = { Text("Email") },
            placeholder = { Text("Enter your email") },
            modifier = Modifier.fillMaxWidth()
        )
        
        // More components...
    }
}
```

Generate code that EXACTLY matches the user's specifications."""

        # Build user message with all context
        user_message_parts = [
            "=== USER'S EXACT REQUIREMENTS ===",
            f"{user_input}",
            f"\n=== YOUR TASK ===",
            f"Generate Jetpack Compose code that implements EVERY SINGLE ITEM listed above.",
            f"You MUST include ALL {len(parsed_intent.get('ui_elements', []))} components mentioned.",
            f"\n=== MANDATORY CODE STRUCTURE ===",
        ]
        
        # Add step-by-step component generation instructions
        user_message_parts.append("\n1. START WITH THESE IMPORTS (copy exactly):")
        user_message_parts.append("""
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
""")
        
        user_message_parts.append("\n2. FUNCTION SIGNATURE:")
        user_message_parts.append("@Composable\nfun LoginScreen() {")
        
        user_message_parts.append("\n3. STATE VARIABLES (declare ALL text fields):")
        user_message_parts.append("For EACH TextField in the requirements, add:")
        user_message_parts.append("    var fieldName by remember { mutableStateOf(\"\") }")
        user_message_parts.append("Example: var email by remember { mutableStateOf(\"\") }")
        user_message_parts.append("Example: var password by remember { mutableStateOf(\"\") }")
        user_message_parts.append("Example: var passwordVisible by remember { mutableStateOf(false) }")
        
        user_message_parts.append(f"\n4. MAIN CONTAINER - {layout_plan.get('root_container', 'Column')}:")
        user_message_parts.append("""    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Top
    ) {""")
        
        user_message_parts.append("\n5. IMPLEMENT EACH COMPONENT FROM USER'S LIST:")
        user_message_parts.append("Go through EACH numbered item in the user requirements above and generate code.")
        user_message_parts.append("\nCOMPONENT PATTERNS TO USE:")
        
        user_message_parts.append("""
• Logo/Icon: Icon(imageVector = Icons.Default.AccountCircle, contentDescription = "Logo", modifier = Modifier.size(80.dp))
• Spacing: Spacer(modifier = Modifier.height(24.dp))  ← Use EXACT dp value from requirements
• Title Text: Text(text = "Welcome Back", style = MaterialTheme.typography.headlineLarge, fontWeight = FontWeight.Bold)
• Subtitle: Text(text = "Sign in to continue", style = MaterialTheme.typography.bodyMedium, color = Color.Gray)
• Email Field:
    OutlinedTextField(
        value = email,
        onValueChange = { email = it },
        label = { Text("Email") },
        placeholder = { Text("Enter your email") },
        modifier = Modifier.fillMaxWidth()
    )
• Password Field:
    OutlinedTextField(
        value = password,
        onValueChange = { password = it },
        label = { Text("Password") },
        placeholder = { Text("Enter your password") },
        visualTransformation = if (passwordVisible) VisualTransformation.None else PasswordVisualTransformation(),
        trailingIcon = {
            IconButton(onClick = { passwordVisible = !passwordVisible }) {
                Icon(imageVector = if (passwordVisible) Icons.Default.Visibility else Icons.Default.VisibilityOff, contentDescription = "Toggle")
            }
        },
        modifier = Modifier.fillMaxWidth()
    )
• Clickable Text: Text(text = "Forgot Password?", modifier = Modifier.fillMaxWidth().clickable { }, textAlign = TextAlign.End, style = MaterialTheme.typography.bodySmall)
• Button:
    Button(
        onClick = { },
        modifier = Modifier.fillMaxWidth().height(48.dp),
        colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary)
    ) {
        Text("Sign In", color = Color.White)
    }
• Outlined Button:
    OutlinedButton(
        onClick = { },
        modifier = Modifier.fillMaxWidth().height(48.dp)
    ) {
        Icon(imageVector = Icons.Default.Google, contentDescription = null)
        Spacer(modifier = Modifier.width(8.dp))
        Text("Continue with Google")
    }
• Divider with Text:
    Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.fillMaxWidth()) {
        HorizontalDivider(modifier = Modifier.weight(1f))
        Text("OR", modifier = Modifier.padding(horizontal = 8.dp))
        HorizontalDivider(modifier = Modifier.weight(1f))
    }
• Sign Up Row:
    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.Center) {
        Text("Don't have an account? ")
        Text("Sign Up", color = MaterialTheme.colorScheme.primary, modifier = Modifier.clickable { })
    }
""")
        
        user_message_parts.append("\n6. CLOSE THE FUNCTION:")
        user_message_parts.append("    }\n}")
        
        user_message_parts.append(f"\n\n=== CRITICAL CHECKLIST ===")
        user_message_parts.append(f"☐ Did you include ALL {len(parsed_intent.get('ui_elements', []))} components?")
        user_message_parts.append("☐ Did you use the EXACT spacing values (24dp, 32dp, 16dp, 8dp)?")
        user_message_parts.append("☐ Did you use OutlinedTextField (not Text) for input fields?")
        user_message_parts.append("☐ Did you add password visibility toggle?")
        user_message_parts.append("☐ Did you make clickable texts clickable with .clickable { }?")
        user_message_parts.append("☐ Did you use .fillMaxWidth() for buttons and fields?")
        user_message_parts.append("☐ Did you match ALL text labels exactly?")
        
        if context_parts:
            user_message_parts.append("\n=== REFERENCE EXAMPLES ===")
            user_message_parts.append("\n".join(context_parts))
        
        user_message_parts.append("\n\n=== OUTPUT FORMAT ===")
        user_message_parts.append("Return ONLY the complete Kotlin code. Start with imports, end with closing brace. NO explanations, NO markdown fences.")
        
        user_message = "\n".join(user_message_parts)
        
        # Call LLM to generate code
        from langchain_core.messages import SystemMessage, HumanMessage
        from .llm_config import get_default_llm
        
        llm = get_default_llm()
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]
        
        try:
            response = llm.invoke(messages)
            generated_code = response.content.strip()
            
            print(f"[UI Generator] Raw LLM response length: {len(generated_code)} chars")
            
            # Clean up the response - extract code if wrapped in markdown
            if "```kotlin" in generated_code:
                print("[UI Generator] Extracting from kotlin markdown block")
                generated_code = generated_code.split("```kotlin")[1].split("```")[0].strip()
            elif "```java" in generated_code:
                print("[UI Generator] Extracting from java markdown block")
                generated_code = generated_code.split("```java")[1].split("```")[0].strip()
            elif "```" in generated_code:
                print("[UI Generator] Extracting from generic markdown block")
                # Find first code block
                parts = generated_code.split("```")
                if len(parts) >= 3:
                    # Take the content between first pair of ```
                    generated_code = parts[1].strip()
                    # Remove language identifier if present
                    if "\n" in generated_code:
                        lines = generated_code.split("\n")
                        # Check if first line is a language identifier
                        if lines[0].strip() in ["kotlin", "java", "kt"]:
                            generated_code = "\n".join(lines[1:])
            
            # Remove any leading/trailing whitespace
            generated_code = generated_code.strip()
            
            # Ensure it starts with imports or @Composable
            if not generated_code.startswith("import") and not generated_code.startswith("@Composable"):
                print("[UI Generator] Code doesn't start with imports, adding them")
                # Add necessary imports
                imports = [
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
                    "import androidx.compose.ui.text.input.PasswordVisualTransformation",
                    "import androidx.compose.ui.text.input.VisualTransformation",
                    "import androidx.compose.ui.text.style.TextAlign",
                    ""
                ]
                generated_code = "\n".join(imports) + "\n" + generated_code
            
            print(f"[UI Generator] Generated {len(generated_code.split(chr(10)))} lines of code using LLM")
            
        except Exception as e:
            print(f"[UI Generator] LLM generation failed: {e}, falling back to template")
            # Fallback to basic template if LLM fails
            generated_code = _generate_template_code(layout_plan)
    
    # Apply validation if requested
    if state.get("validate_code"):
        from .android_tools_mcp import AndroidLintMCP
        
        print("[UI Generator] Applying validation and auto-fix...")
        lint_mcp = AndroidLintMCP()
        generated_code = lint_mcp.auto_fix(generated_code)
        print("[UI Generator] Code validated and auto-fixed")
    
    return {
        "messages": [{"role": "assistant", "content": "UI code generation complete"}],
        "generated_code": generated_code,
        "current_step": "code_generated"
    }


def _generate_template_code(layout_plan: dict) -> str:
    """Generate code using template-based approach (for testing or fallback)."""
    code_lines = [
        "import androidx.compose.runtime.Composable",
        "import androidx.compose.ui.Modifier",
        "import androidx.compose.material3.*",
        "import androidx.compose.foundation.layout.*",
        "import androidx.compose.foundation.background",
        "import androidx.compose.ui.graphics.Color",
        "import androidx.compose.ui.unit.dp",
        "import androidx.compose.ui.Alignment",
        "",
        "@Composable",
        "fun GeneratedUI() {",
    ]
    
    # Add root container
    root = layout_plan.get("root_container", "Column")
    modifiers = layout_plan.get("modifiers", [])
    
    if root == "Column":
        arrangement = layout_plan.get("arrangement", "Center")
        code_lines.append(f"    {root}(")
        if modifiers:
            code_lines.append(f"        modifier = Modifier.{'.'.join(modifiers)},")
        code_lines.append(f"        verticalArrangement = Arrangement.{arrangement},")
        code_lines.append(f"        horizontalAlignment = Alignment.CenterHorizontally")
        code_lines.append(f"    ) {{")
    elif root == "Row":
        code_lines.append(f"    {root}(")
        if modifiers:
            code_lines.append(f"        modifier = Modifier.{'.'.join(modifiers)},")
        code_lines.append(f"        horizontalArrangement = Arrangement.SpaceBetween")
        code_lines.append(f"    ) {{")
    else:
        if modifiers:
            code_lines.append(f"    {root}(modifier = Modifier.{'.'.join(modifiers)}) {{")
        else:
            code_lines.append(f"    {root}() {{")
    
    # Add children components
    for child in layout_plan.get("children", []):
        component_type = child.get("component", "Text")
        props = child.get("properties", {})
        
        if component_type == "Text":
            text_content = props.get("content", "Sample Text")
            style = props.get("style", "bodyLarge")
            code_lines.append(f"        Text(")
            code_lines.append(f'            text = "{text_content}",')
            code_lines.append(f"            style = MaterialTheme.typography.{style}")
            code_lines.append(f"        )")
        
        elif component_type == "Button":
            button_text = props.get("text", "Button")
            code_lines.append(f"        Button(onClick = {{ /* TODO: Add action */ }}) {{")
            code_lines.append(f'            Text("{button_text}")')
            code_lines.append(f"        }}")
        
        elif component_type == "Image":
            description = props.get("description", "Image")
            code_lines.append(f"        // Image placeholder")
            code_lines.append(f"        Box(")
            code_lines.append(f"            modifier = Modifier")
            code_lines.append(f"                .size(200.dp)")
            code_lines.append(f"                .background(Color.LightGray)")
            code_lines.append(f"        )")
    
    code_lines.append(f"    }}")
    code_lines.append(f"}}")
    
    return "\n".join(code_lines)


def _generate_fallback_code(layout_plan: dict) -> str:
    """Generate basic fallback code if LLM fails (deprecated - use _generate_template_code)."""
    return _generate_template_code(layout_plan)


# ============================================================================
# Agent: Accessibility Reviewer
# ============================================================================

def accessibility_reviewer_agent(state: UIGeneratorState) -> UIGeneratorState:
    """
    Accessibility Reviewer Agent: Validates color contrast, 
    content descriptions, and touch targets.
    """
    generated_code = state.get("generated_code", "")
    print(f"\n[Accessibility Reviewer] Checking accessibility...")
    
    issues = []
    
    # Check for content descriptions on images
    if "Image" in generated_code and "contentDescription" not in generated_code:
        issues.append("Missing contentDescription for Image components")
    
    # Check for touch target sizes
    if "Button" in generated_code:
        if ".size(" not in generated_code or "48.dp" not in generated_code:
            issues.append("Ensure buttons meet minimum touch target size (48dp)")
    
    # Check for semantic content
    if "Text" in generated_code:
        issues.append("Consider adding semantics for screen readers")
    
    if not issues:
        issues.append("No major accessibility issues found")
    
    print(f"[Accessibility Reviewer] Found {len(issues)} items to review")
    for issue in issues:
        print(f"  - {issue}")
    
    return {
        "messages": [{"role": "assistant", "content": "Accessibility review complete"}],
        "accessibility_issues": issues,
        "current_step": "accessibility_reviewed"
    }


# ============================================================================
# Agent: UI Reviewer
# ============================================================================

def ui_reviewer_agent(state: UIGeneratorState) -> UIGeneratorState:
    """
    UI Reviewer Agent: Evaluates design against Material 3 guidelines
    and best practices.
    """
    generated_code = state.get("generated_code", "")
    print(f"\n[UI Reviewer] Evaluating against Material 3 guidelines...")
    
    issues = []
    
    # Check for Material 3 compliance
    if "MaterialTheme" not in generated_code:
        issues.append("Consider using MaterialTheme for consistent theming")
    
    # Check for proper spacing
    if "padding" in generated_code:
        issues.append("Good: Using padding for spacing")
    else:
        issues.append("Consider adding padding for better visual hierarchy")
    
    # Check for proper arrangement
    if "Arrangement" in generated_code:
        issues.append("Good: Using Arrangement for proper spacing")
    
    # Check for alignment
    if "Alignment" in generated_code:
        issues.append("Good: Using Alignment for proper positioning")
    
    if not issues:
        issues.append("Code follows Material 3 guidelines")
    
    print(f"[UI Reviewer] Found {len(issues)} design considerations")
    for issue in issues:
        print(f"  - {issue}")
    
    return {
        "messages": [{"role": "assistant", "content": "UI review complete"}],
        "design_issues": issues,
        "current_step": "ui_reviewed"
    }


# ============================================================================
# Output Node
# ============================================================================

def output_node(state: UIGeneratorState) -> UIGeneratorState:
    """
    Output Node: Prepares the final output with generated code 
    and review feedback.
    """
    print(f"\n[Output] Preparing final output...")
    
    generated_code = state.get("generated_code", "")
    accessibility_issues = state.get("accessibility_issues", [])
    design_issues = state.get("design_issues", [])
    
    # Create final output
    output_lines = [
        "=" * 70,
        "GENERATED JETPACK COMPOSE UI CODE",
        "=" * 70,
        "",
        generated_code,
        "",
        "=" * 70,
        "ACCESSIBILITY REVIEW",
        "=" * 70,
    ]
    
    for issue in accessibility_issues:
        output_lines.append(f"  • {issue}")
    
    output_lines.extend([
        "",
        "=" * 70,
        "DESIGN REVIEW (Material 3 Guidelines)",
        "=" * 70,
    ])
    
    for issue in design_issues:
        output_lines.append(f"  • {issue}")
    
    output_lines.append("=" * 70)
    
    final_output = "\n".join(output_lines)
    
    print(f"[Output] Final output prepared")
    
    return {
        "messages": [{"role": "assistant", "content": "Output generation complete"}],
        "final_output": final_output,
        "current_step": "complete"
    }


# ============================================================================
# Graph Builder
# ============================================================================

def build_ui_generator_graph() -> StateGraph:
    """Build and return the UI generator graph."""
    workflow = StateGraph(UIGeneratorState)
    
    # Add all agent nodes
    workflow.add_node("intent_parser", intent_parser_agent)
    workflow.add_node("layout_planner", layout_planner_agent)
    workflow.add_node("ui_generator", ui_generator_agent)
    workflow.add_node("accessibility_reviewer", accessibility_reviewer_agent)
    workflow.add_node("ui_reviewer", ui_reviewer_agent)
    workflow.add_node("output", output_node)
    
    # Set entry point
    workflow.set_entry_point("intent_parser")
    
    # Define the linear flow
    workflow.add_edge("intent_parser", "layout_planner")
    workflow.add_edge("layout_planner", "ui_generator")
    workflow.add_edge("ui_generator", "accessibility_reviewer")
    workflow.add_edge("accessibility_reviewer", "ui_reviewer")
    workflow.add_edge("ui_reviewer", "output")
    workflow.add_edge("output", END)
    
    return workflow


# ============================================================================
# Main Function
# ============================================================================

def generate_ui_from_description(
    user_description: str,
    github_examples: list = None,
    project_context: dict = None,
    multi_file: bool = False,
    validate: bool = False,
    return_report: bool = False
) -> str | dict:
    """
    Generate Jetpack Compose UI code from a natural language description.
    
    Args:
        user_description: Natural language description of the desired UI
        github_examples: Optional list of ComposeExample from GitHub for context
        project_context: Optional dict with existing project structure info
        multi_file: If True, return dict with multiple files; if False, return single file string
        validate: If True, run Android Tools MCP validation and auto-fix
        return_report: If True, return dict with code and validation report
        
    Returns:
        Final output with generated code and reviews (str or dict based on multi_file/return_report)
    """
    print("=" * 70)
    print("JETPACK COMPOSE UI GENERATOR")
    print("Multi-Agent LangGraph System")
    print("=" * 70)
    print(f"\nUser Input: {user_description}")
    
    if github_examples:
        print(f"Using {len(github_examples)} GitHub examples for context")
    if project_context:
        print(f"Using project context with {len(project_context.get('existing_composables', []))} existing composables")
    if validate:
        print("Validation enabled: Will run Android Tools MCP checks")
    
    # Build the graph
    workflow = build_ui_generator_graph()
    app = workflow.compile()
    
    # Initial state
    initial_state = {
        "messages": [],
        "user_input": user_description,
        "parsed_intent": {},
        "layout_plan": {},
        "generated_code": "",
        "accessibility_issues": [],
        "design_issues": [],
        "final_output": "",
        "current_step": "start",
        "github_examples": github_examples or [],
        "project_context": project_context or {},
        "multi_file": multi_file,
        "validate_code": validate
    }
    
    # Execute the workflow
    result = app.invoke(initial_state)
    
    # Get the output
    final_output = result.get("final_output", "")
    generated_code = result.get("generated_code", "")
    
    # Apply validation if requested
    if validate:
        from .android_tools_mcp import AndroidLintMCP, GradleMCP
        
        print("\n[Validation] Running Android Tools MCP checks...")
        lint_mcp = AndroidLintMCP()
        gradle_mcp = GradleMCP()
        
        # Extract code from final output
        code_to_validate = generated_code if generated_code else final_output
        
        # Run lint validation
        lint_issues = lint_mcp.validate_compose_code(code_to_validate)
        print(f"[Validation] Found {len(lint_issues)} lint issues")
        
        # Auto-fix if issues found
        if lint_issues:
            print("[Validation] Applying auto-fix...")
            fixed_code = lint_mcp.auto_fix(code_to_validate)
        else:
            fixed_code = code_to_validate
        
        # Check compilation
        compilation_result = gradle_mcp.check_compilation(fixed_code)
        print(f"[Validation] Compilation: {'SUCCESS' if compilation_result.success else 'FAILED'}")
        
        # Update output with fixed code
        final_output = fixed_code
        
        # Return with report if requested
        if return_report:
            return {
                "code": fixed_code,
                "validation_report": {
                    "lint_issues": [
                        {
                            "severity": issue.severity,
                            "message": issue.message,
                            "line": issue.line,
                            "suggestion": issue.suggestion
                        }
                        for issue in lint_issues
                    ],
                    "lint_issues_count": len(lint_issues),
                    "auto_fixed": len(lint_issues) > 0,
                    "compilation": {
                        "success": compilation_result.success,
                        "errors": compilation_result.errors,
                        "warnings": compilation_result.warnings
                    }
                }
            }
    
    # Return based on multi_file flag
    if multi_file:
        # Parse and return multiple files
        final_output = result.get("final_output", "")
        return parse_multi_file_output(final_output)
    else:
        # Return single file output
        final_output = result.get("final_output", "")
        print("\n" + final_output)
        return final_output


def parse_multi_file_output(output: str) -> dict:
    """
    Parse multi-file output from LLM response.
    
    Args:
        output: LLM output potentially containing multiple files
        
    Returns:
        Dict mapping file paths to code content
    """
    try:
        # Try to parse as JSON first
        return json.loads(output)
    except json.JSONDecodeError:
        # If not JSON, return as single file
        return {"Main.kt": output}


def run_demo():
    """Run demonstration examples."""
    examples = [
        "Create a simple login screen with a title, username field, password field, and a login button",
        "Build a card with an image, title text, and a button",
        "Design a settings screen with text and buttons in a column",
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n\n{'#' * 70}")
        print(f"EXAMPLE {i}")
        print(f"{'#' * 70}")
        generate_ui_from_description(example)
        
        if i < len(examples):
            print("\n" + "." * 70 + "\n")


if __name__ == "__main__":
    run_demo()
