"""
High-Level UI Generation Pipeline.

Coordinates the LangGraph multi-agent execution, MCP tools,
and auto-validation logic.
"""

from typing import Optional, List, Dict, Any, Union
from .graph import build_ui_generator_graph
from ..mcp.android_tools import AndroidLintMCP, GradleMCP


def generate_ui_from_description(
    user_description: str,
    github_examples: Optional[List[Any]] = None,
    project_context: Optional[Dict[str, Any]] = None,
    multi_file: bool = False,
    validate: bool = True,
    return_report: bool = False,
) -> Union[str, Dict[str, Any]]:
    """
    Generate Jetpack Compose UI code from a natural language prompt.

    Args:
        user_description: Natural language prompt describing desired UI
        github_examples: Optional list of ComposeExample objects
        project_context: Optional dictionary with existing project metadata
        multi_file: If True, returns dictionary of generated files
        validate: If True, runs Android Lint MCP checks and auto-fixes
        return_report: If True, returns dictionary containing code and lint/compilation reports

    Returns:
        Generated Kotlin code string or structured report dictionary
    """
    print("=" * 70)
    print("JETPACK COMPOSE UI GENERATOR")
    print("Multi-Agent LangGraph System")
    print("=" * 70)
    print(f"\nUser Input: {user_description}")

    # Build and compile graph
    workflow = build_ui_generator_graph()
    app = workflow.compile()

    initial_state = {
        "messages": [],
        "user_input": user_description,
        "generated_code": "",
        "accessibility_issues": [],
        "design_issues": [],
        "final_output": "",
        "current_step": "start",
        "github_examples": github_examples or [],
        "project_context": project_context or {},
        "multi_file": multi_file,
        "validate_code": validate,
        "use_llm_generation": True,
    }

    result = app.invoke(initial_state)

    generated_code = result.get("generated_code", "")
    accessibility_issues = result.get("accessibility_issues", [])
    design_issues = result.get("design_issues", [])

    lint_issues = []
    compilation_success = True
    compilation_errors = []

    # Run validation and compilation checks if enabled
    if validate:
        print("\n[Validation] Running Android Tools MCP checks...")
        lint_mcp = AndroidLintMCP()
        gradle_mcp = GradleMCP()

        # Run lint
        lint_issues = lint_mcp.validate_compose_code(generated_code)
        print(f"[Validation] Found {len(lint_issues)} lint issues")

        # Auto-fix code
        if lint_issues:
            print("[Validation] Applying auto-fix...")
            generated_code = lint_mcp.auto_fix(generated_code)

        # Check compilation syntax
        comp_res = gradle_mcp.check_compilation(generated_code)
        compilation_success = comp_res.success
        compilation_errors = comp_res.errors
        print(f"[Validation] Compilation check: {'SUCCESS' if comp_res.success else 'FAILED'}")

    # Format the complete output with updated code and preserved reviews
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

    # Return structured report if requested
    if return_report:
        return {
            "code": generated_code,
            "final_output": final_output,
            "validation_report": {
                "lint_issues": [
                    {
                        "severity": issue.severity,
                        "message": issue.message,
                        "line": issue.line,
                        "suggestion": issue.suggestion,
                    }
                    for issue in lint_issues
                ],
                "lint_issues_count": len(lint_issues),
                "auto_fixed": len(lint_issues) > 0,
                "compilation": {
                    "success": compilation_success,
                    "errors": compilation_errors,
                },
            },
        }

    if multi_file:
        return {"Main.kt": generated_code}

    return final_output
