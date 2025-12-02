"""
Tests for Streamlit Interface helper functions.
"""

import pytest
from src.multi_agent_mobile_ui_assistant.streamlit_interface import (
    extract_code_from_output,
    extract_section,
    generate_preview_html
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

    def test_extract_section_found(self):
        """Test extracting a specific section."""
        output = """
        Some code...
        
        ACCESSIBILITY REVIEW
        ======================================================================
        • Issue 1
        • Issue 2
        
        DESIGN REVIEW
        ======================================================================
        • Design issue
        """
        section = extract_section(output, "ACCESSIBILITY REVIEW")
        assert "• Issue 1" in section
        assert "• Issue 2" in section
        assert "• Design issue" not in section

    def test_extract_section_not_found(self):
        """Test behavior when section is missing."""
        output = "No reviews here."
        section = extract_section(output, "MISSING SECTION")
        assert section == "No issues found"

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
