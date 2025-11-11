"""
Advanced LangGraph Example - Agent with Tools

This module demonstrates a more advanced LangGraph workflow with tool usage.
"""

from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """State for the agent graph."""
    messages: Annotated[list, add_messages]
    current_task: str
    tools_used: list[str]
    is_complete: bool


def analyze_task(state: AgentState) -> AgentState:
    """Analyze the incoming task."""
    print(f"Analyzing task: {state.get('current_task', 'No task provided')}")
    
    return {
        "messages": [{"role": "assistant", "content": "Task analysis complete"}],
        "tools_used": state.get("tools_used", []) + ["analyzer"]
    }


def execute_tool_1(state: AgentState) -> AgentState:
    """Execute first tool."""
    print("Executing Tool 1: Data Collection")
    
    return {
        "messages": [{"role": "assistant", "content": "Collected data from source"}],
        "tools_used": state.get("tools_used", []) + ["data_collector"]
    }


def execute_tool_2(state: AgentState) -> AgentState:
    """Execute second tool."""
    print("Executing Tool 2: Data Processing")
    
    return {
        "messages": [{"role": "assistant", "content": "Processed collected data"}],
        "tools_used": state.get("tools_used", []) + ["data_processor"]
    }


def synthesize_results(state: AgentState) -> AgentState:
    """Synthesize results from all tools."""
    print("Synthesizing results from all tools")
    
    tools_count = len(state.get("tools_used", []))
    
    return {
        "messages": [{"role": "assistant", "content": f"Synthesis complete using {tools_count} tools"}],
        "is_complete": True
    }


def should_continue(state: AgentState) -> Literal["tool_1", "tool_2", "synthesize"]:
    """Determine the next step based on state."""
    tools_used = state.get("tools_used", [])
    
    if "analyzer" in tools_used and "data_collector" not in tools_used:
        return "tool_1"
    elif "data_collector" in tools_used and "data_processor" not in tools_used:
        return "tool_2"
    else:
        return "synthesize"


def build_agent_graph() -> StateGraph:
    """Build and return the agent graph."""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("analyze", analyze_task)
    workflow.add_node("tool_1", execute_tool_1)
    workflow.add_node("tool_2", execute_tool_2)
    workflow.add_node("synthesize", synthesize_results)
    
    # Set entry point
    workflow.set_entry_point("analyze")
    
    # Add conditional routing
    workflow.add_conditional_edges(
        "analyze",
        should_continue,
        {
            "tool_1": "tool_1",
            "tool_2": "tool_2",
            "synthesize": "synthesize"
        }
    )
    
    workflow.add_conditional_edges(
        "tool_1",
        should_continue,
        {
            "tool_1": "tool_1",
            "tool_2": "tool_2",
            "synthesize": "synthesize"
        }
    )
    
    workflow.add_conditional_edges(
        "tool_2",
        should_continue,
        {
            "tool_1": "tool_1",
            "tool_2": "tool_2",
            "synthesize": "synthesize"
        }
    )
    
    workflow.add_edge("synthesize", END)
    
    return workflow


def run_agent_example():
    """Run the advanced agent example."""
    print("=" * 70)
    print("Running Advanced LangGraph Agent Example")
    print("=" * 70)
    
    # Build the graph
    workflow = build_agent_graph()
    app = workflow.compile()
    
    # Run the graph with a task
    initial_state = {
        "messages": [],
        "current_task": "Process user interface data and generate insights",
        "tools_used": [],
        "is_complete": False
    }
    
    print(f"\nInitial Task: {initial_state['current_task']}")
    print("\nExecuting agent workflow...\n")
    
    result = app.invoke(initial_state)
    
    print("\n" + "=" * 70)
    print("Agent Execution Complete")
    print("=" * 70)
    print(f"Task Complete: {result.get('is_complete', False)}")
    print(f"Tools Used: {', '.join(result.get('tools_used', []))}")
    print(f"Total Messages: {len(result.get('messages', []))}")
    
    print("\nWorkflow Messages:")
    for i, msg in enumerate(result.get('messages', []), 1):
        role = msg.__class__.__name__.replace('Message', '').upper()
        content = msg.content if hasattr(msg, 'content') else str(msg)
        print(f"  {i}. [{role}] {content}")
    
    print("=" * 70)


if __name__ == "__main__":
    run_agent_example()
