"""
Tests for Streamlit Interface helper functions.
"""

from unittest.mock import MagicMock, patch

import pytest
from src.multi_agent_mobile_ui_assistant.streamlit_interface import (
    extract_code_from_output,
    generate_preview_html,
    render_check_results,
    render_review,
    render_trace_steps,
)

class TestStreamlitHelpers:
    """Tests for helper functions in streamlit_interface.py."""

    def test_extract_code_from_output_simple(self):
        """Test extracting code from a simple string."""
        output = """
        Here is the code:
        @Composable
        fun MyUI() {
            Text("Hello")
        }
        """
        code = extract_code_from_output(output)
        assert "@Composable" in code
        assert 'Text("Hello")' in code
        assert "Here is the code:" not in code

    def test_extract_code_from_output_with_braces(self):
        """Test extracting code with nested braces."""
        output = """
        @Composable
        fun ComplexUI() {
            Column {
                Text("Nested")
            }
        }
        Extra text
        """
        code = extract_code_from_output(output)
        assert "fun ComplexUI" in code
        assert 'Text("Nested")' in code
        assert "Extra text" not in code

    def test_extract_code_no_composable(self):
        """Test behavior when no @Composable tag is found."""
        output = "Just some text without code."
        code = extract_code_from_output(output)
        assert code == output

    def test_generate_preview_html_empty(self):
        """Test preview generation with empty code."""
        html = generate_preview_html("")
        assert "<p>No code to preview</p>" in html

    def test_generate_preview_html_basic(self):
        """Test preview generation with basic components."""
        code = """
        @Composable
        fun Preview() {
            Text("Hello World")
            Button(onClick = {}) {
                Text("Click Me")
            }
        }
        """
        html = generate_preview_html(code)
        assert "Hello World" in html
        assert "Click Me" in html
        assert "font-family: system-ui" in html

    def test_generate_preview_html_xss_prevention(self):
        """Test that HTML content is escaped to prevent XSS."""
        code = """
        @Composable
        fun Malicious() {
            Text("<script>alert('xss')</script>")
            Button(onClick = {}) {
                Text("<b>Bold</b>")
            }
        }
        """
        html = generate_preview_html(code)
        
        # Should NOT contain raw script tags
        assert "<script>" not in html
        assert "&lt;script&gt;" in html
        
        # Should NOT contain raw bold tags from user input
        assert "<b>" not in html
        assert "&lt;b&gt;" in html


class TestRenderCheckResults:
    """Tests for the generic CheckResult renderer (story 3)."""

    def test_empty_checks_shows_info_message(self):
        with patch("src.multi_agent_mobile_ui_assistant.streamlit_interface.st") as mock_st:
            render_check_results("Title", [])
            mock_st.subheader.assert_called_once_with("Title")
            mock_st.info.assert_called_once_with("No checks recorded.")

    def test_falsy_title_skips_subheader(self):
        with patch("src.multi_agent_mobile_ui_assistant.streamlit_interface.st") as mock_st:
            render_check_results("", [])
            mock_st.subheader.assert_not_called()

    def test_dispatches_to_icon_function_by_status(self):
        checks = [
            {"check": "a", "status": "pass", "message": "ok"},
            {"check": "b", "status": "warn", "message": "careful"},
            {"check": "c", "status": "fail", "message": "broken"},
        ]
        with patch("src.multi_agent_mobile_ui_assistant.streamlit_interface.st") as mock_st:
            render_check_results("Title", checks)
            mock_st.success.assert_called_once_with("ok")
            mock_st.warning.assert_called_once_with("careful")
            mock_st.error.assert_called_once_with("broken")

    def test_status_drives_rendering_not_message_text(self):
        """A pass-status message containing alarming prose must still render
        via st.success -- rendering is keyed only on `status`, never on
        sniffing the message text."""
        checks = [{"check": "a", "status": "pass", "message": "ERROR: looks scary but passed"}]
        with patch("src.multi_agent_mobile_ui_assistant.streamlit_interface.st") as mock_st:
            render_check_results("Title", checks)
            mock_st.success.assert_called_once_with("ERROR: looks scary but passed")
            mock_st.error.assert_not_called()
            mock_st.warning.assert_not_called()

    def test_missing_status_degrades_gracefully_via_info(self):
        """A CheckResult missing/with an unrecognized `status` must not raise
        KeyError -- it should fall back to st.info instead of crashing the tab."""
        checks = [{"check": "a", "message": "no status here"}]
        with patch("src.multi_agent_mobile_ui_assistant.streamlit_interface.st") as mock_st:
            render_check_results("Title", checks)  # must not raise
            mock_st.info.assert_called_with("no status here")

    def test_unrecognized_status_degrades_gracefully_via_info(self):
        checks = [{"check": "a", "status": "unknown", "message": "weird status"}]
        with patch("src.multi_agent_mobile_ui_assistant.streamlit_interface.st") as mock_st:
            render_check_results("Title", checks)  # must not raise
            mock_st.info.assert_called_with("weird status")

    def test_missing_message_defaults_to_empty_string(self):
        checks = [{"check": "a", "status": "pass"}]
        with patch("src.multi_agent_mobile_ui_assistant.streamlit_interface.st") as mock_st:
            render_check_results("Title", checks)  # must not raise
            mock_st.success.assert_called_once_with("")


class TestRenderTraceSteps:
    """Tests for the generic TraceStep renderer (story 3)."""

    def test_empty_steps_shows_info_message(self):
        with patch("src.multi_agent_mobile_ui_assistant.streamlit_interface.st") as mock_st:
            render_trace_steps("Trace", [])
            mock_st.subheader.assert_called_once_with("Trace")
            mock_st.info.assert_called_once_with("No trace recorded.")

    def test_falsy_title_skips_subheader(self):
        with patch("src.multi_agent_mobile_ui_assistant.streamlit_interface.st") as mock_st:
            render_trace_steps("", [])
            mock_st.subheader.assert_not_called()

    def test_renders_node_and_summary_with_detail_in_expander(self):
        steps = [
            {"node": "ui_generator", "summary": "generated code", "detail": "long detail text"},
        ]
        with patch("src.multi_agent_mobile_ui_assistant.streamlit_interface.st") as mock_st:
            render_trace_steps("Trace", steps)
            mock_st.expander.assert_called_once_with("**ui_generator** — generated code")
            mock_st.caption.assert_called_once_with("long detail text")

    def test_missing_detail_defaults_to_empty_caption(self):
        steps = [{"node": "validator", "summary": "validated code"}]
        with patch("src.multi_agent_mobile_ui_assistant.streamlit_interface.st") as mock_st:
            render_trace_steps("Trace", steps)
            mock_st.caption.assert_called_once_with("")

    def test_missing_node_and_summary_default_to_empty_strings(self):
        """A TraceStep missing `node`/`summary` must not raise KeyError --
        it should degrade to an empty-labelled expander instead of crashing."""
        steps = [{"detail": "some detail"}]
        with patch("src.multi_agent_mobile_ui_assistant.streamlit_interface.st") as mock_st:
            render_trace_steps("Trace", steps)  # must not raise
            mock_st.expander.assert_called_once_with("**** — ")
            mock_st.caption.assert_called_once_with("some detail")


class TestRenderReview:
    """
    Tests for `render_review`, which dispatches between the new list[CheckResult]
    shape (generate_initial_ui) and the legacy prose-string shape still produced
    by refine_ui's own review generation (untouched by this story).
    """

    def test_list_review_dispatches_to_render_check_results(self):
        checks = [{"check": "a", "status": "pass", "message": "looks good"}]
        with patch("src.multi_agent_mobile_ui_assistant.streamlit_interface.st") as mock_st:
            render_review("♿ Accessibility Review", checks)
            mock_st.subheader.assert_called_once_with("♿ Accessibility Review")
            mock_st.success.assert_called_once_with("looks good")

    def test_string_review_renders_via_markdown_fallback_without_crashing(self):
        """
        Regression test: after a Generate -> Refine sequence, `current_accessibility`
        /`current_design` hold refine_ui's plain prose strings. Rendering that
        through the Reviews columns must not raise (previously crashed with
        "string indices must be integers" from iterating the string as if it
        were a list of CheckResult dicts).
        """
        prose = "**Improvements Made:**\n• Added contentDescription"
        with patch("src.multi_agent_mobile_ui_assistant.streamlit_interface.st") as mock_st:
            render_review("♿ Accessibility Review", prose)  # must not raise
            mock_st.subheader.assert_called_once_with("♿ Accessibility Review")
            mock_st.markdown.assert_called_once_with(
                f'<div class="review-section">{prose}</div>', unsafe_allow_html=True
            )
            mock_st.success.assert_not_called()
            mock_st.error.assert_not_called()
            mock_st.warning.assert_not_called()

    def test_empty_title_skips_subheader_for_string_review(self):
        with patch("src.multi_agent_mobile_ui_assistant.streamlit_interface.st") as mock_st:
            render_review("", "some prose")
            mock_st.subheader.assert_not_called()
