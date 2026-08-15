"""
LangGraph Workflow Definition for Multi-Agent UI Generation.

Orchestrates:
UI Generator -> Accessibility Reviewer -> UI Reviewer -> Output Formatter
"""

from typing import Dict, Any
from langgraph.graph import StateGraph, END
from .state import UIGeneratorState
from ..agents.generator import ui_generator_agent
from ..agents.accessibility import accessibility_reviewer_agent
from ..agents.design_reviewer import ui_reviewer_agent


def output_node(state: UIGeneratorState) -> Dict[str, Any]:
    """
    Format the final combined output with generated code and review sections.

    Args:
        state: Workflow state

    Returns:
        Updated state with formatted final_output
    """
    print("\n[Output] Preparing final output report...")
    generated_code = state.get("generated_code", "")
    accessibility_issues = state.get("accessibility_issues", [])
    design_issues = state.get("design_issues", [])

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
    return {
        "messages": [{"role": "assistant", "content": "Output generation complete"}],
        "final_output": final_output,
        "current_step": "complete",
    }


def build_ui_generator_graph() -> StateGraph:
    """
    Build and compile the multi-agent UI generation workflow graph.

    Returns:
        Compiled StateGraph
    """
    workflow = StateGraph(UIGeneratorState)

    workflow.add_node("ui_generator", ui_generator_agent)
    workflow.add_node("accessibility_reviewer", accessibility_reviewer_agent)
    workflow.add_node("ui_reviewer", ui_reviewer_agent)
    workflow.add_node("output", output_node)

    workflow.set_entry_point("ui_generator")

    workflow.add_edge("ui_generator", "accessibility_reviewer")
    workflow.add_edge("accessibility_reviewer", "ui_reviewer")
    workflow.add_edge("ui_reviewer", "output")
    workflow.add_edge("output", END)

    return workflow
