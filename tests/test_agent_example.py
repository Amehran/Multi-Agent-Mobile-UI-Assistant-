"""
Unit tests for the advanced LangGraph agent example module.
"""

from src.multi_agent_mobile_ui_assistant.agent_example import (
    AgentState,
    analyze_task,
    execute_tool_1,
    execute_tool_2,
    synthesize_results,
    should_continue,
    build_agent_graph,
)


class TestAgentNodes:
    """Tests for agent node functions."""

    def test_analyze_task_adds_analyzer_tool(self):
        """Test that analyze_task adds 'analyzer' to tools_used."""
        initial_state = {
            "messages": [],
            "current_task": "Test task",
            "tools_used": [],
            "is_complete": False
        }
        
        result = analyze_task(initial_state)
        
        assert "analyzer" in result["tools_used"]
        assert len(result["messages"]) == 1
        assert result["messages"][0]["role"] == "assistant"
        assert "Task analysis complete" in result["messages"][0]["content"]

    def test_analyze_task_preserves_existing_tools(self):
        """Test that analyze_task preserves existing tools."""
        initial_state = {
            "messages": [],
            "current_task": "Test task",
            "tools_used": ["existing_tool"],
            "is_complete": False
        }
        
        result = analyze_task(initial_state)
        
        assert "existing_tool" in result["tools_used"]
        assert "analyzer" in result["tools_used"]
        assert len(result["tools_used"]) == 2

    def test_analyze_task_handles_no_task(self):
        """Test analyze_task handles missing current_task gracefully."""
        initial_state = {
            "messages": [],
            "tools_used": [],
            "is_complete": False
        }
        
        result = analyze_task(initial_state)
        
        assert "analyzer" in result["tools_used"]

    def test_execute_tool_1_adds_data_collector(self):
        """Test that execute_tool_1 adds 'data_collector' to tools_used."""
        initial_state = {
            "messages": [],
            "current_task": "Collect data",
            "tools_used": ["analyzer"],
            "is_complete": False
        }
        
        result = execute_tool_1(initial_state)
        
        assert "data_collector" in result["tools_used"]
        assert len(result["messages"]) == 1
        assert "Collected data from source" in result["messages"][0]["content"]

    def test_execute_tool_2_adds_data_processor(self):
        """Test that execute_tool_2 adds 'data_processor' to tools_used."""
        initial_state = {
            "messages": [],
            "current_task": "Process data",
            "tools_used": ["analyzer", "data_collector"],
            "is_complete": False
        }
        
        result = execute_tool_2(initial_state)
        
        assert "data_processor" in result["tools_used"]
        assert len(result["messages"]) == 1
        assert "Processed collected data" in result["messages"][0]["content"]

    def test_synthesize_results_sets_is_complete(self):
        """Test that synthesize_results sets is_complete to True."""
        initial_state = {
            "messages": [],
            "current_task": "Synthesize",
            "tools_used": ["analyzer", "data_collector", "data_processor"],
            "is_complete": False
        }
        
        result = synthesize_results(initial_state)
        
        assert result["is_complete"] is True
        assert len(result["messages"]) == 1
        assert "Synthesis complete" in result["messages"][0]["content"]

    def test_synthesize_results_includes_tool_count(self):
        """Test that synthesize_results includes tool count in message."""
        initial_state = {
            "messages": [],
            "current_task": "Synthesize",
            "tools_used": ["tool1", "tool2", "tool3"],
            "is_complete": False
        }
        
        result = synthesize_results(initial_state)
        
        assert "3 tools" in result["messages"][0]["content"]


class TestConditionalRouting:
    """Tests for conditional routing logic."""

    def test_should_continue_routes_to_tool_1(self):
        """Test routing to tool_1 when analyzer is used but not data_collector."""
        state = {
            "tools_used": ["analyzer"],
            "is_complete": False
        }
        
        assert should_continue(state) == "tool_1"

    def test_should_continue_routes_to_tool_2(self):
        """Test routing to tool_2 when data_collector is used but not data_processor."""
        state = {
            "tools_used": ["analyzer", "data_collector"],
            "is_complete": False
        }
        
        assert should_continue(state) == "tool_2"

    def test_should_continue_routes_to_synthesize(self):
        """Test routing to synthesize when both tools are used."""
        state = {
            "tools_used": ["analyzer", "data_collector", "data_processor"],
            "is_complete": False
        }
        
        assert should_continue(state) == "synthesize"

    def test_should_continue_with_empty_tools(self):
        """Test routing with empty tools_used."""
        state = {
            "tools_used": [],
            "is_complete": False
        }
        
        # Should route to synthesize when conditions aren't met
        assert should_continue(state) == "synthesize"

    def test_should_continue_with_missing_tools_used(self):
        """Test routing when tools_used is missing from state."""
        state = {
            "is_complete": False
        }
        
        # Should handle gracefully
        result = should_continue(state)
        assert result in ["tool_1", "tool_2", "synthesize"]


class TestGraphBuilder:
    """Tests for agent graph building."""

    def test_build_agent_graph_returns_state_graph(self):
        """Test that build_agent_graph returns a StateGraph instance."""
        from langgraph.graph import StateGraph
        
        workflow = build_agent_graph()
        assert isinstance(workflow, StateGraph)

    def test_build_agent_graph_compiles(self):
        """Test that the agent graph compiles successfully."""
        workflow = build_agent_graph()
        app = workflow.compile()
        
        assert app is not None

    def test_agent_graph_execution(self):
        """Test agent graph execution with initial state."""
        workflow = build_agent_graph()
        app = workflow.compile()
        
        initial_state = {
            "messages": [],
            "current_task": "Test task execution",
            "tools_used": [],
            "is_complete": False
        }
        
        result = app.invoke(initial_state)
        
        # Should have executed and marked as complete
        assert result["is_complete"] is True
        assert len(result["tools_used"]) > 0
        assert len(result["messages"]) > 0

    def test_agent_graph_uses_all_tools(self):
        """Test that agent graph uses all expected tools."""
        workflow = build_agent_graph()
        app = workflow.compile()
        
        initial_state = {
            "messages": [],
            "current_task": "Complete workflow test",
            "tools_used": [],
            "is_complete": False
        }
        
        result = app.invoke(initial_state)
        
        # Should have used analyzer, data_collector, and data_processor
        assert "analyzer" in result["tools_used"]
        assert "data_collector" in result["tools_used"]
        assert "data_processor" in result["tools_used"]


class TestAgentStateType:
    """Tests for AgentState TypedDict."""

    def test_agent_state_structure(self):
        """Test that AgentState has the expected structure."""
        state: AgentState = {
            "messages": [],
            "current_task": "test",
            "tools_used": [],
            "is_complete": False
        }
        
        assert "messages" in state
        assert "current_task" in state
        assert "tools_used" in state
        assert "is_complete" in state

    def test_agent_state_with_data(self):
        """Test AgentState with populated data."""
        state: AgentState = {
            "messages": [{"role": "assistant", "content": "Test"}],
            "current_task": "Process data",
            "tools_used": ["tool1", "tool2"],
            "is_complete": True
        }
        
        assert len(state["messages"]) == 1
        assert state["current_task"] == "Process data"
        assert len(state["tools_used"]) == 2
        assert state["is_complete"] is True
