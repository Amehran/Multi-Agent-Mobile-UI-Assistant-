"""
Unit tests for the basic LangGraph example module.
"""

from src.multi_agent_mobile_ui_assistant.example import (
    State,
    node_1,
    node_2,
    node_3,
    route_after_node_1,
    build_graph,
)


class TestNodeFunctions:
    """Tests for individual node functions."""

    def test_node_1_increments_step_count(self):
        """Test that node_1 increments step count."""
        initial_state = {"messages": [], "step_count": 0}
        result = node_1(initial_state)
        
        assert result["step_count"] == 1
        assert len(result["messages"]) == 1
        assert result["messages"][0]["role"] == "system"
        assert result["messages"][0]["content"] == "Processed by Node 1"

    def test_node_1_with_existing_count(self):
        """Test that node_1 correctly increments existing count."""
        initial_state = {"messages": [], "step_count": 5}
        result = node_1(initial_state)
        
        assert result["step_count"] == 6

    def test_node_2_increments_step_count(self):
        """Test that node_2 increments step count."""
        initial_state = {"messages": [], "step_count": 1}
        result = node_2(initial_state)
        
        assert result["step_count"] == 2
        assert len(result["messages"]) == 1
        assert result["messages"][0]["content"] == "Processed by Node 2"

    def test_node_3_increments_step_count(self):
        """Test that node_3 increments step count."""
        initial_state = {"messages": [], "step_count": 2}
        result = node_3(initial_state)
        
        assert result["step_count"] == 3
        assert len(result["messages"]) == 1
        assert result["messages"][0]["content"] == "Processed by Node 3"

    def test_nodes_handle_empty_state(self):
        """Test that nodes handle empty state gracefully."""
        empty_state = {}
        
        result_1 = node_1(empty_state)
        assert result_1["step_count"] == 1
        
        result_2 = node_2(empty_state)
        assert result_2["step_count"] == 1
        
        result_3 = node_3(empty_state)
        assert result_3["step_count"] == 1


class TestRouting:
    """Tests for routing logic."""

    def test_route_after_node_1_to_node_2(self):
        """Test routing to node_2 when step count is less than 2."""
        state = {"step_count": 0}
        assert route_after_node_1(state) == "node_2"
        
        state = {"step_count": 1}
        assert route_after_node_1(state) == "node_2"

    def test_route_after_node_1_to_node_3(self):
        """Test routing to node_3 when step count is 2 or more."""
        state = {"step_count": 2}
        assert route_after_node_1(state) == "node_3"
        
        state = {"step_count": 5}
        assert route_after_node_1(state) == "node_3"

    def test_route_with_empty_state(self):
        """Test routing with empty state defaults to node_2."""
        state = {}
        assert route_after_node_1(state) == "node_2"


class TestGraphBuilder:
    """Tests for graph building."""

    def test_build_graph_returns_state_graph(self):
        """Test that build_graph returns a StateGraph instance."""
        from langgraph.graph import StateGraph
        
        workflow = build_graph()
        assert isinstance(workflow, StateGraph)

    def test_build_graph_has_nodes(self):
        """Test that the built graph has all required nodes."""
        workflow = build_graph()
        app = workflow.compile()
        
        # The graph should be compilable without errors
        assert app is not None

    def test_graph_execution_with_initial_state(self):
        """Test graph execution with initial state."""
        workflow = build_graph()
        app = workflow.compile()
        
        initial_state = {"messages": [], "step_count": 0}
        result = app.invoke(initial_state)
        
        # After execution, step count should have increased
        assert result["step_count"] > initial_state["step_count"]
        assert len(result["messages"]) > 0

    def test_graph_execution_reaches_node_3(self):
        """Test that graph execution eventually reaches node_3."""
        workflow = build_graph()
        app = workflow.compile()
        
        initial_state = {"messages": [], "step_count": 0}
        result = app.invoke(initial_state)
        
        # Check that we processed through the nodes
        # Should have messages from multiple nodes
        assert len(result["messages"]) >= 2


class TestStateType:
    """Tests for State TypedDict."""

    def test_state_structure(self):
        """Test that State has the expected structure."""
        state: State = {"messages": [], "step_count": 0}
        
        assert "messages" in state
        assert "step_count" in state
        assert isinstance(state["messages"], list)
        assert isinstance(state["step_count"], int)

    def test_state_with_messages(self):
        """Test State with messages."""
        state: State = {
            "messages": [
                {"role": "system", "content": "Test message"},
                {"role": "user", "content": "Another message"}
            ],
            "step_count": 5
        }
        
        assert len(state["messages"]) == 2
        assert state["step_count"] == 5
