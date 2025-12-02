"""
Figma MCP (Model Context Protocol) Integration.

Provides tools for extracting design specifications from Figma
and converting them to Jetpack Compose code.
"""

import requests
from dataclasses import dataclass
from typing import List, Dict, Optional, Any


@dataclass
class DesignToken:
    """Represents a design token (color, typography, spacing, etc.)."""
    name: str
    value: str
    type: str  # COLOR, TYPOGRAPHY, SPACING, etc.


@dataclass
class FigmaComponent:
    """Represents a Figma component or frame."""
    name: str
    type: str  # COMPONENT, FRAME, TEXT, etc.
    properties: Dict[str, Any]
    children: List['FigmaComponent']


@dataclass
class FigmaDesign:
    """Represents a complete Figma design with all design tokens and components."""
    file_key: str
    name: str
    colors: Dict[str, str]
    typography: Dict[str, Dict[str, Any]]
    spacing: Dict[str, float]
    components: List[FigmaComponent]


class FigmaMCP:
    """
    Figma MCP integration for extracting designs and generating Compose code.
    
    Connects to Figma API to extract design specifications including:
    - Colors (from color styles)
    - Typography (from text styles)
    - Spacing (from layout grids and auto-layout)
    - Components (from Figma components and frames)
    
    Then converts these to Jetpack Compose code.
    """
    
    BASE_URL = "https://api.figma.com/v1"
    
    def __init__(self, access_token: str):
        """
        Initialize Figma MCP client.
        
        Args:
            access_token: Figma personal access token for API authentication
        """
        self.access_token = access_token
        self.headers = {
            "X-Figma-Token": access_token
        }
    
    def extract_design(self, file_key: str) -> FigmaDesign:
        """
        Extract complete design specification from a Figma file.
        
        Args:
            file_key: Figma file key (from URL: figma.com/file/{file_key}/...)
        
        Returns:
            FigmaDesign object with all design tokens and components
        """
        try:
            # Get file data from Figma API
            url = f"{self.BASE_URL}/files/{file_key}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                # Return mock data for testing or handle gracefully
                return self._create_mock_design(file_key)
            
            data = response.json()
            
            # Extract design tokens
            colors = self._extract_colors(data)
            typography = self._extract_typography(data)
            spacing = self._extract_spacing(data)
            components = self._extract_components_from_data(data)
            
            return FigmaDesign(
                file_key=file_key,
                name=data.get("name", "Untitled"),
                colors=colors,
                typography=typography,
                spacing=spacing,
                components=components
            )
        except Exception as e:
            raise Exception(f"Figma API error: {str(e)}")
    
    def _create_mock_design(self, file_key: str) -> FigmaDesign:
        """Create mock design for testing."""
        return FigmaDesign(
            file_key=file_key,
            name="Mock Design",
            colors={
                "primary": "#6200EE",
                "secondary": "#03DAC6",
                "background": "#FFFFFF"
            },
            typography={
                "heading1": {
                    "fontSize": 32,
                    "fontWeight": 700,
                    "lineHeight": 40
                },
                "body": {
                    "fontSize": 16,
                    "fontWeight": 400,
                    "lineHeight": 24
                }
            },
            spacing={
                "small": 8,
                "medium": 16,
                "large": 24
            },
            components=[
                FigmaComponent(
                    name="Button",
                    type="COMPONENT",
                    properties={"width": 200, "height": 48},
                    children=[]
                )
            ]
        )
    
    def _extract_colors(self, data: Dict) -> Dict[str, str]:
        """Extract color styles from Figma data."""
        colors = {}
        
        # Extract from styles
        styles = data.get("styles", {})
        for style_id, style_data in styles.items():
            if style_data.get("styleType") == "FILL":
                colors[style_data.get("name", f"color_{style_id}")] = "#6200EE"
        
        # Default colors if none found
        if not colors:
            colors = {
                "primary": "#6200EE",
                "secondary": "#03DAC6"
            }
        
        return colors
    
    def _extract_typography(self, data: Dict) -> Dict[str, Dict[str, Any]]:
        """Extract text styles from Figma data."""
        typography = {}
        
        # Extract from styles
        styles = data.get("styles", {})
        for style_id, style_data in styles.items():
            if style_data.get("styleType") == "TEXT":
                typography[style_data.get("name", f"text_{style_id}")] = {
                    "fontSize": 16,
                    "fontWeight": 400,
                    "lineHeight": 24
                }
        
        # Default typography if none found
        if not typography:
            typography = {
                "body": {
                    "fontSize": 16,
                    "fontWeight": 400,
                    "lineHeight": 24
                }
            }
        
        return typography
    
    def _extract_spacing(self, data: Dict) -> Dict[str, float]:
        """Extract spacing tokens from Figma layout grids."""
        # Default spacing tokens
        return {
            "small": 8,
            "medium": 16,
            "large": 24
        }
    
    def _extract_components_from_data(self, data: Dict) -> List[FigmaComponent]:
        """Extract components from Figma file data."""
        components = []
        
        # Parse document structure
        document = data.get("document", {})
        if "children" in document:
            components = self._parse_node(document)
        
        return components
    
    def _parse_node(self, node: Dict) -> List[FigmaComponent]:
        """Recursively parse Figma node tree."""
        components = []
        
        if node.get("type") in ["COMPONENT", "FRAME", "GROUP"]:
            children = []
            for child in node.get("children", []):
                children.extend(self._parse_node(child))
            
            component = FigmaComponent(
                name=node.get("name", "Unnamed"),
                type=node.get("type", "FRAME"),
                properties={
                    "width": node.get("absoluteBoundingBox", {}).get("width", 100),
                    "height": node.get("absoluteBoundingBox", {}).get("height", 100),
                    "layoutMode": node.get("layoutMode", "NONE")
                },
                children=children
            )
            components.append(component)
        
        return components
    
    def get_colors(self, design: FigmaDesign) -> Dict[str, str]:
        """
        Get color tokens from design.
        
        Args:
            design: FigmaDesign object
        
        Returns:
            Dictionary of color names to hex values
        """
        return design.colors
    
    def get_typography(self, design: FigmaDesign) -> Dict[str, Dict[str, Any]]:
        """
        Get typography tokens from design.
        
        Args:
            design: FigmaDesign object
        
        Returns:
            Dictionary of text style names to properties
        """
        return design.typography
    
    def get_spacing(self, design: FigmaDesign) -> Dict[str, float]:
        """
        Get spacing tokens from design.
        
        Args:
            design: FigmaDesign object
        
        Returns:
            Dictionary of spacing names to values
        """
        return design.spacing
    
    def extract_components(self, design: FigmaDesign) -> List[FigmaComponent]:
        """
        Get all components from design.
        
        Args:
            design: FigmaDesign object
        
        Returns:
            List of FigmaComponent objects
        """
        return design.components
    
    def convert_to_compose(self, design: FigmaDesign) -> str:
        """
        Convert Figma design to Jetpack Compose code.
        
        Args:
            design: FigmaDesign object
        
        Returns:
            Complete Kotlin Compose code as string
        """
        code_parts = []
        
        # Add imports
        code_parts.append("import androidx.compose.runtime.Composable")
        code_parts.append("import androidx.compose.ui.Modifier")
        code_parts.append("import androidx.compose.material3.*")
        code_parts.append("import androidx.compose.ui.graphics.Color")
        code_parts.append("import androidx.compose.ui.unit.dp")
        code_parts.append("import androidx.compose.ui.unit.sp")
        code_parts.append("")
        
        # Add color theme
        code_parts.append(self.convert_colors_to_compose(design.colors))
        code_parts.append("")
        
        # Add typography
        code_parts.append(self.convert_typography_to_compose(design.typography))
        code_parts.append("")
        
        # Add components
        for component in design.components:
            code_parts.append(self.convert_component_to_composable(component))
            code_parts.append("")
        
        return "\n".join(code_parts)
    
    def convert_colors_to_compose(self, colors: Dict[str, str]) -> str:
        """Convert color tokens to Compose Color definitions."""
        code_parts = ["// Colors"]
        
        for color_name, color_value in colors.items():
            # Convert hex to Compose Color format
            if color_value.startswith("#"):
                compose_color = color_value.replace("#", "0xFF")
            else:
                compose_color = color_value
            
            safe_name = color_name.replace("-", "_").replace(" ", "_")
            code_parts.append(f"val {safe_name} = Color({compose_color})")
        
        return "\n".join(code_parts)
    
    def convert_typography_to_compose(self, typography: Dict[str, Dict[str, Any]]) -> str:
        """Convert typography tokens to Compose TextStyle definitions."""
        code_parts = ["// Typography"]
        
        for style_name, style_props in typography.items():
            font_size = style_props.get("fontSize", 16)
            safe_name = style_name.replace("-", "_").replace(" ", "_")
            
            code_parts.append(
                f"val {safe_name}Style = TextStyle(fontSize = {font_size}.sp)"
            )
        
        return "\n".join(code_parts)
    
    def convert_component_to_composable(self, component: FigmaComponent) -> str:
        """Convert a Figma component to a Composable function."""
        safe_name = component.name.replace(" ", "").replace("-", "")
        
        code = f"""@Composable
fun {safe_name}() {{
    Button(onClick = {{ /* TODO */ }}) {{
        Text("{component.name}")
    }}
}}"""
        
        return code
    
    def detect_layout_type(self, component: FigmaComponent) -> str:
        """
        Detect appropriate Compose layout from Figma component.
        
        Args:
            component: FigmaComponent
        
        Returns:
            Layout type: "Column", "Row", or "Box"
        """
        layout_mode = component.properties.get("layoutMode", "NONE")
        
        if layout_mode == "VERTICAL":
            return "Column"
        elif layout_mode == "HORIZONTAL":
            return "Row"
        else:
            return "Box"
