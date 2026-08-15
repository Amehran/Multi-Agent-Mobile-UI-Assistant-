"""
Tests for Web Interface helper functions and visual preview generator.
"""

import pytest
from src.multi_agent_mobile_ui_assistant.web.app import (
    extract_code_from_output,
    extract_section,
)
from src.multi_agent_mobile_ui_assistant.preview.visualizer import generate_preview_html


class TestStreamlitHelpers:
    """Tests for helper functions in web/app.py and preview/visualizer.py."""

    def test_extract_code_from_output_simple(self):
        """Test extracting code from a structured report."""
        output = """======================================================================
GENERATED JETPACK COMPOSE UI CODE
======================================================================

import androidx.compose.material3.Text

@Composable
fun MyUI() {
    Text("Hello")
}

======================================================================
ACCESSIBILITY REVIEW
======================================================================
"""
        code = extract_code_from_output(output)
        assert "@Composable" in code
        assert 'Text("Hello")' in code
        assert "import androidx.compose.material3.Text" in code

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
        assert "No issues found" in section or "No specific issues" in section

    def test_generate_preview_html_empty(self):
        """Test preview generation with empty code."""
        html = generate_preview_html("")
        assert "No code to preview" in html

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
