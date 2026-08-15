"""
Core State Definitions for LangGraph Orchestration.
"""

from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph.message import add_messages


class UIGeneratorState(TypedDict):
    """Workflow state passed through the LangGraph agent pipeline."""
    messages: Annotated[list, add_messages]
    user_input: str
    generated_code: str
    accessibility_issues: List[str]
    design_issues: List[str]
    final_output: str
    current_step: str
    github_examples: List[Any]      # ComposeExample items for few-shot context
    project_context: Dict[str, Any] # Existing project composables / manifest
    multi_file: bool                # Multi-file generation flag
    validate_code: bool             # Android lint & compilation validation flag
    use_llm_generation: bool        # Testing / fallback flag
