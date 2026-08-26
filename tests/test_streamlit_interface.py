"""
Tests for Streamlit Interface helper functions.
"""

from unittest.mock import MagicMock, patch

import pytest
from src.multi_agent_mobile_ui_assistant.streamlit_interface import (
    extract_code_from_output,
    generate_initial_ui,
    generate_preview_html,
    refine_ui,
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


class TestGenerateInitialUiWiring:
    """
    Tests for generate_initial_ui's unpacking of generate_ui_from_description's
    dict shape into session state -- the actual glue between story 2's producer
    shapes and story 3's renderers, which no other test exercised together.
    """

    def test_unpacks_trace_and_check_results_into_session_state(self):
        fixture = {
            "code": "@Composable\nfun Screen() {}",
            "validation_report": None,
            "trace": [{"node": "ui_generator", "summary": "generated code", "detail": ""}],
            "accessibility_issues": [{"check": "a11y", "status": "pass", "message": "ok"}],
            "design_issues": [{"check": "design", "status": "warn", "message": "careful"}],
            "validation_checks": [{"check": "compilation", "status": "pass", "message": "ok", "attempt": 0}],
        }
        with patch("src.multi_agent_mobile_ui_assistant.streamlit_interface.st") as mock_st, \
             patch("src.multi_agent_mobile_ui_assistant.streamlit_interface.generate_ui_from_description",
                   return_value=fixture) as mock_generate:
            mock_st.session_state.get = lambda key, default=None: default
            mock_st.session_state.history = []
            mock_st.spinner.return_value.__enter__ = MagicMock(return_value=None)
            mock_st.spinner.return_value.__exit__ = MagicMock(return_value=False)

            generate_initial_ui("Create a screen")

            mock_generate.assert_called_once()
            assert mock_st.session_state.current_trace == fixture["trace"]
            assert mock_st.session_state.current_accessibility == fixture["accessibility_issues"]
            assert mock_st.session_state.current_design == fixture["design_issues"]
            assert mock_st.session_state.current_validation_checks == fixture["validation_checks"]
            assert mock_st.session_state.current_code == fixture["code"]

    def test_multi_file_path_sets_check_fields_to_none_not_empty_list(self):
        """
        GIVEN multi_file=True, so generate_ui_from_description returns its own
        dict-of-files contract (no trace/CheckResult keys)
        WHEN generate_initial_ui unpacks it
        THEN accessibility/design/validation_checks are set to None (never ran)
        rather than [] (ran, found nothing) -- these render differently.
        """
        multi_file_output = {"Screen.kt": "@Composable\nfun Screen() {}"}
        with patch("src.multi_agent_mobile_ui_assistant.streamlit_interface.st") as mock_st, \
             patch("src.multi_agent_mobile_ui_assistant.streamlit_interface.generate_ui_from_description",
                   return_value=multi_file_output):
            mock_st.session_state.get = lambda key, default=None: (
                True if key == "multi_file" else default
            )
            mock_st.session_state.history = []
            mock_st.spinner.return_value.__enter__ = MagicMock(return_value=None)
            mock_st.spinner.return_value.__exit__ = MagicMock(return_value=False)

            generate_initial_ui("Create a multi-file project")

            assert mock_st.session_state.current_accessibility is None
            assert mock_st.session_state.current_design is None
            assert mock_st.session_state.current_validation_checks is None


class TestRefineUiClearsStaleTraceAndValidation:
    """
    refine_ui doesn't invoke the graph, so a prior generation's trace/
    validation data no longer describes the refined code -- it must be
    cleared, not left stale (previously it was left untouched, so the Trace
    and Validation Report tabs kept showing pre-refine data as current).
    """

    def test_refine_resets_trace_and_validation_fields(self):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content=(
            '{"refined_code": "@Composable\\nfun Screen() {}", '
            '"changes_made": ["tweak"], "accessibility_notes": [], "design_notes": []}'
        ))
        with patch("src.multi_agent_mobile_ui_assistant.streamlit_interface.st") as mock_st, \
             patch("src.multi_agent_mobile_ui_assistant.streamlit_interface.get_llm_for_session",
                   return_value=mock_llm):
            mock_st.session_state.get = lambda key, default=None: default
            mock_st.session_state.current_code = "@Composable\nfun Old() {}"
            mock_st.session_state.current_trace = [{"node": "ui_generator", "summary": "x", "detail": ""}]
            mock_st.session_state.current_validation_checks = [{"check": "compilation", "status": "pass", "message": "ok"}]
            mock_st.session_state.validation_report = {"compilation": {"success": True}}
            mock_st.session_state.history = [{"description": "prior", "iteration": 1}]
            mock_st.spinner.return_value.__enter__ = MagicMock(return_value=None)
            mock_st.spinner.return_value.__exit__ = MagicMock(return_value=False)

            refine_ui("make it better")

            assert mock_st.session_state.current_trace == []
            assert mock_st.session_state.current_validation_checks is None
            assert mock_st.session_state.validation_report is None
