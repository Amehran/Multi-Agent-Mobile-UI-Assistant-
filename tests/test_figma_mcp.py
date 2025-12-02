"""
Unit tests for Figma MCP integration.

Tests the FigmaMCP class for extracting design specifications
from Figma and converting them to Jetpack Compose code.
"""

import pytest
from src.multi_agent_mobile_ui_assistant.figma_mcp import (
    FigmaMCP,
    FigmaDesign,
    DesignToken,
    FigmaComponent,
)


class TestFigmaMCP:
    """Tests for Figma MCP integration."""
    
    def test_extract_design_returns_figma_design(self):
        """
        GIVEN a Figma file URL or ID
        WHEN extract_design is called
        THEN should return a FigmaDesign object
        """
        figma = FigmaMCP(access_token="test_token")
        design = figma.extract_design(file_key="test_file_key")
        
        assert isinstance(design, FigmaDesign)
        assert design.file_key == "test_file_key"
    
    def test_figma_design_has_required_fields(self):
        """
        GIVEN a FigmaDesign object
        WHEN accessing its fields
        THEN should have name, colors, typography, spacing, and components
        """
        design = FigmaDesign(
            file_key="test_key",
            name="Test Design",
            colors={},
            typography={},
            spacing={},
            components=[]
        )
        
        assert design.name == "Test Design"
        assert isinstance(design.colors, dict)
        assert isinstance(design.typography, dict)
        assert isinstance(design.spacing, dict)
        assert isinstance(design.components, list)
    
    def test_get_colors_extracts_color_tokens(self):
        """
        GIVEN a Figma design with color styles
        WHEN get_colors is called
        THEN should extract color tokens as hex values
        """
        figma = FigmaMCP(access_token="test_token")
        design = figma.extract_design(file_key="test_file_key")
        colors = figma.get_colors(design)
        
        assert isinstance(colors, dict)
        assert len(colors) > 0
        # Colors should be in hex format
        for color_name, color_value in colors.items():
            assert isinstance(color_name, str)
            assert isinstance(color_value, str)
            assert color_value.startswith("#") or color_value.startswith("0xFF")
    
    def test_get_typography_extracts_text_styles(self):
        """
        GIVEN a Figma design with text styles
        WHEN get_typography is called
        THEN should extract typography tokens (font, size, weight, line height)
        """
        figma = FigmaMCP(access_token="test_token")
        design = figma.extract_design(file_key="test_file_key")
        typography = figma.get_typography(design)
        
        assert isinstance(typography, dict)
        # Each typography token should have font properties
        for style_name, style_props in typography.items():
            assert "fontSize" in style_props
            assert "fontWeight" in style_props
            assert isinstance(style_props["fontSize"], (int, float))
    
    def test_get_spacing_extracts_spacing_tokens(self):
        """
        GIVEN a Figma design with spacing/layout grid
        WHEN get_spacing is called
        THEN should extract spacing tokens (padding, margin, gap)
        """
        figma = FigmaMCP(access_token="test_token")
        design = figma.extract_design(file_key="test_file_key")
        spacing = figma.get_spacing(design)
        
        assert isinstance(spacing, dict)
        assert len(spacing) >= 0
        # Spacing values should be numeric
        for spacing_name, spacing_value in spacing.items():
            assert isinstance(spacing_value, (int, float))
    
    def test_extract_components_finds_ui_components(self):
        """
        GIVEN a Figma design with components/frames
        WHEN extract_components is called
        THEN should return list of FigmaComponent objects
        """
        figma = FigmaMCP(access_token="test_token")
        design = figma.extract_design(file_key="test_file_key")
        components = figma.extract_components(design)
        
        assert isinstance(components, list)
        if len(components) > 0:
            component = components[0]
            assert isinstance(component, FigmaComponent)
            assert hasattr(component, "name")
            assert hasattr(component, "type")
            assert hasattr(component, "properties")
    
    def test_figma_component_has_required_fields(self):
        """
        GIVEN a FigmaComponent
        WHEN accessing its fields
        THEN should have name, type, properties, and children
        """
        component = FigmaComponent(
            name="Button",
            type="COMPONENT",
            properties={"width": 100, "height": 48},
            children=[]
        )
        
        assert component.name == "Button"
        assert component.type == "COMPONENT"
        assert component.properties["width"] == 100
        assert component.children == []


class TestFigmaToCompose:
    """Tests for converting Figma designs to Compose code."""
    
    def test_convert_to_compose_returns_kotlin_code(self):
        """
        GIVEN a FigmaDesign
        WHEN convert_to_compose is called
        THEN should return valid Kotlin Compose code
        """
        figma = FigmaMCP(access_token="test_token")
        design = figma.extract_design(file_key="test_file_key")
        code = figma.convert_to_compose(design)
        
        assert isinstance(code, str)
        assert "@Composable" in code
        assert "fun" in code
    
    def test_convert_colors_to_compose_theme(self):
        """
        GIVEN Figma color tokens
        WHEN convert_to_compose is called
        THEN should generate Compose Color definitions
        """
        figma = FigmaMCP(access_token="test_token")
        colors = {
            "primary": "#6200EE",
            "secondary": "#03DAC6",
            "background": "#FFFFFF"
        }
        
        theme_code = figma.convert_colors_to_compose(colors)
        
        assert "Color" in theme_code
        assert "primary" in theme_code
        assert "0xFF6200EE" in theme_code or "#6200EE" in theme_code
    
    def test_convert_typography_to_compose_theme(self):
        """
        GIVEN Figma typography tokens
        WHEN convert_to_compose is called
        THEN should generate Compose TextStyle definitions
        """
        figma = FigmaMCP(access_token="test_token")
        typography = {
            "heading1": {
                "fontSize": 32,
                "fontWeight": 700,
                "lineHeight": 40
            }
        }
        
        typography_code = figma.convert_typography_to_compose(typography)
        
        assert "TextStyle" in typography_code
        assert "fontSize" in typography_code
        assert "32.sp" in typography_code or "32" in typography_code
    
    def test_convert_component_to_composable(self):
        """
        GIVEN a FigmaComponent (e.g., Button)
        WHEN convert_component_to_composable is called
        THEN should generate a Composable function
        """
        figma = FigmaMCP(access_token="test_token")
        component = FigmaComponent(
            name="LoginButton",
            type="COMPONENT",
            properties={"width": 200, "height": 48, "text": "Login"},
            children=[]
        )
        
        code = figma.convert_component_to_composable(component)
        
        assert "@Composable" in code
        assert "fun LoginButton" in code
        assert "Button" in code or "Text" in code
    
    def test_detect_layout_type_from_figma(self):
        """
        GIVEN a Figma frame with auto-layout
        WHEN detect_layout_type is called
        THEN should return appropriate Compose layout (Column, Row, Box)
        """
        figma = FigmaMCP(access_token="test_token")
        
        # Vertical auto-layout
        vertical_component = FigmaComponent(
            name="VerticalList",
            type="FRAME",
            properties={"layoutMode": "VERTICAL"},
            children=[]
        )
        layout = figma.detect_layout_type(vertical_component)
        assert layout == "Column"
        
        # Horizontal auto-layout
        horizontal_component = FigmaComponent(
            name="HorizontalRow",
            type="FRAME",
            properties={"layoutMode": "HORIZONTAL"},
            children=[]
        )
        layout = figma.detect_layout_type(horizontal_component)
        assert layout == "Row"


class TestFigmaIntegration:
    """Integration tests for Figma MCP."""
    
    def test_full_figma_to_compose_pipeline(self):
        """
        GIVEN a Figma file key
        WHEN running the full pipeline
        THEN should extract design and generate complete Compose code
        """
        figma = FigmaMCP(access_token="test_token")
        
        # Extract design
        design = figma.extract_design(file_key="test_file_key")
        
        # Get design tokens
        colors = figma.get_colors(design)
        typography = figma.get_typography(design)
        spacing = figma.get_spacing(design)
        
        # Convert to Compose
        code = figma.convert_to_compose(design)
        
        assert isinstance(code, str)
        assert len(code) > 0
        assert "@Composable" in code
    
    def test_figma_mcp_handles_api_errors_gracefully(self):
        """
        GIVEN invalid Figma credentials or file key
        WHEN extract_design is called
        THEN should handle errors gracefully without crashing
        """
        figma = FigmaMCP(access_token="invalid_token")
        
        # Should not crash, but return empty or error state
        try:
            design = figma.extract_design(file_key="invalid_key")
            # If no exception, should return a valid (possibly empty) design
            assert isinstance(design, FigmaDesign)
        except Exception as e:
            # Should raise informative error
            assert "Figma" in str(e) or "API" in str(e) or "authentication" in str(e).lower()
    
    def test_figma_design_token_class(self):
        """
        GIVEN design tokens from Figma
        WHEN creating DesignToken objects
        THEN should store token information properly
        """
        token = DesignToken(
            name="primary-color",
            value="#6200EE",
            type="COLOR"
        )
        
        assert token.name == "primary-color"
        assert token.value == "#6200EE"
        assert token.type == "COLOR"
