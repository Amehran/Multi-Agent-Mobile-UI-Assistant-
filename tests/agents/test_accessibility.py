"""
Tests for Accessibility Reviewer Agent (agents/accessibility.py).
"""

from src.multi_agent_mobile_ui_assistant.agents.accessibility import accessibility_reviewer_agent


class TestAccessibilityReviewerAgent:
    """Tests for the Accessibility Reviewer Agent."""

    def test_accessibility_reviewer_checks_code(self):
        """Test that accessibility reviewer analyzes generated code."""
        state = {
            "generated_code": "@Composable\nfun Test() { Text(\"Hello\") }",
            "messages": [],
        }

        result = accessibility_reviewer_agent(state)

        assert "accessibility_issues" in result
        assert len(result["accessibility_issues"]) > 0

    def test_accessibility_reviewer_detects_missing_content_description(self):
        """Test detection of missing contentDescription."""
        state = {
            "generated_code": "@Composable\nfun Test() { Image() }",
            "messages": [],
        }

        result = accessibility_reviewer_agent(state)

        issues = result["accessibility_issues"]
        assert any("contentDescription" in issue for issue in issues)

    def test_accessibility_reviewer_checks_button_size(self):
        """Test that reviewer checks button touch target sizes."""
        state = {
            "generated_code": "@Composable\nfun Test() { Button(onClick = {}) { Text(\"Click\") } }",
            "messages": [],
        }

        result = accessibility_reviewer_agent(state)

        issues = result["accessibility_issues"]
        assert len(issues) > 0

    def test_accessibility_reviewer_sets_current_step(self):
        """Test that accessibility reviewer sets current_step."""
        state = {
            "generated_code": "code",
            "messages": [],
        }

        result = accessibility_reviewer_agent(state)

        assert result["current_step"] == "accessibility_reviewed"
