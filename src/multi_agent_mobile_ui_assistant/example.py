"""
Basic LangGraph Example

This module demonstrates a simple LangGraph workflow with a state-based graph.
"""

from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages


class State(TypedDict):
    """State for the graph."""
    messages: Annotated[list, add_messages]
    step_count: int


def node_1(state: State) -> State:
    """First node in the graph."""
    print("Executing Node 1")
    return {
        "messages": [{"role": "system", "content": "Processed by Node 1"}],
        "step_count": state.get("step_count", 0) + 1
    }


def node_2(state: State) -> State:
    """Second node in the graph."""
    print("Executing Node 2")
    return {
        "messages": [{"role": "system", "content": "Processed by Node 2"}],
        "step_count": state.get("step_count", 0) + 1
    }


def node_3(state: State) -> State:
    """Third node in the graph."""
    print("Executing Node 3")
    return {
        "messages": [{"role": "system", "content": "Processed by Node 3"}],
        "step_count": state.get("step_count", 0) + 1
    }


def route_after_node_1(state: State) -> str:
    """Conditional routing after node 1."""
    # Simple routing logic
    if state.get("step_count", 0) < 2:
        return "node_2"
    return "node_3"


def build_graph() -> StateGraph:
    """Build and return the graph."""
    # Create the graph
    workflow = StateGraph(State)
    
    # Add nodes
    workflow.add_node("node_1", node_1)
    workflow.add_node("node_2", node_2)
    workflow.add_node("node_3", node_3)
    
    # Set entry point
    workflow.set_entry_point("node_1")
    
    # Add edges
    workflow.add_conditional_edges(
        "node_1",
        route_after_node_1,
        {
            "node_2": "node_2",
            "node_3": "node_3"
        }
    )
    workflow.add_edge("node_2", "node_3")
    workflow.add_edge("node_3", END)
    
    return workflow


def run_example():
    """Run the basic LangGraph example."""
    print("=" * 60)
    print("Running Basic LangGraph Example")
    print("=" * 60)
    
    # Build the graph
    workflow = build_graph()
    app = workflow.compile()
    
    # Run the graph
    initial_state = {
        "messages": [],
        "step_count": 0
    }
    
    print("\nExecuting graph with initial state:")
    print(f"Step count: {initial_state['step_count']}")
    print()
    
    result = app.invoke(initial_state)
    
    print("\n" + "=" * 60)
    print("Final Result:")
    print("=" * 60)
    print(f"Final step count: {result['step_count']}")
    print(f"Number of messages: {len(result['messages'])}")
    print("\nMessages:")
    for i, msg in enumerate(result['messages'], 1):
        print(f"  {i}. {msg}")
    print("=" * 60)


if __name__ == "__main__":
    run_example()
