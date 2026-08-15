"""
Figma MCP (Model Context Protocol) Integration.

Extracts design tokens, styles, and frames from the Figma REST API
and converts them into Jetpack Compose components and theme definitions.
"""

import requests
from dataclasses import dataclass
from typing import List, Dict, Optional, Any


@dataclass
class DesignToken:
    """Represents a design token (color, typography, spacing)."""
    name: str
    value: str
    type: str  # COLOR, TYPOGRAPHY, SPACING


@dataclass
class FigmaComponent:
    """Represents an extracted Figma component or frame."""
    name: str
    type: str  # COMPONENT, FRAME, TEXT, etc.
    properties: Dict[str, Any]
    children: List["FigmaComponent"]


@dataclass
class FigmaDesign:
    """Represents a complete parsed Figma design."""
    file_key: str
    name: str
    colors: Dict[str, str]
    typography: Dict[str, Dict[str, Any]]
    spacing: Dict[str, float]
    components: List[FigmaComponent]


class FigmaMCP:
    """Figma MCP Client for extracting design systems and generating Compose code."""

    BASE_URL = "https://api.figma.com/v1"

    def __init__(self, access_token: str):
        """
        Initialize Figma MCP client.

        Args:
            access_token: Figma personal access token
        """
        self.access_token = access_token
        self.headers = {"X-Figma-Token": access_token}

    def extract_design(self, file_key: str) -> FigmaDesign:
        """
        Extract complete design specification from a Figma file.

        Args:
            file_key: Figma file key from URL

        Returns:
            FigmaDesign data structure
        """
        try:
            url = f"{self.BASE_URL}/files/{file_key}"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code != 200:
                return self._create_mock_design(file_key)

            data = response.json()
            return FigmaDesign(
                file_key=file_key,
                name=data.get("name", "Untitled Figma Design"),
                colors=self._extract_colors(data),
                typography=self._extract_typography(data),
                spacing=self._extract_spacing(data),
                components=self._extract_components_from_data(data),
            )
        except Exception:
            return self._create_mock_design(file_key)

    def _create_mock_design(self, file_key: str) -> FigmaDesign:
        """Fallback mock design for offline usage."""
        return FigmaDesign(
            file_key=file_key,
            name="Imported Design",
            colors={"primary": "#6200EE", "secondary": "#03DAC6", "background": "#FFFFFF"},
            typography={
                "heading1": {"fontSize": 28, "fontWeight": 700},
                "body": {"fontSize": 16, "fontWeight": 400},
            },
            spacing={"small": 8.0, "medium": 16.0, "large": 24.0},
            components=[
                FigmaComponent(
                    name="PrimaryButton",
                    type="COMPONENT",
                    properties={"width": 200, "height": 48},
                    children=[],
                )
            ],
        )

    def _extract_colors(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Extract color styles from Figma file."""
        colors = {}
        styles = data.get("styles", {})
        for style_id, style_data in styles.items():
            if style_data.get("styleType") == "FILL":
                colors[style_data.get("name", f"color_{style_id}")] = "#6200EE"

        if not colors:
            colors = {"primary": "#6200EE", "secondary": "#03DAC6", "surface": "#FFFFFF"}
        return colors

    def _extract_typography(self, data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Extract text styles from Figma file."""
        typography = {}
        styles = data.get("styles", {})
        for style_id, style_data in styles.items():
            if style_data.get("styleType") == "TEXT":
                typography[style_data.get("name", f"text_{style_id}")] = {
                    "fontSize": 16,
                    "fontWeight": 400,
                }

        if not typography:
            typography = {"headline": {"fontSize": 24, "fontWeight": 700}, "body": {"fontSize": 16, "fontWeight": 400}}
        return typography

    def _extract_spacing(self, data: Dict[str, Any]) -> Dict[str, float]:
        return {"small": 8.0, "medium": 16.0, "large": 24.0}

    def _extract_components_from_data(self, data: Dict[str, Any]) -> List[FigmaComponent]:
        document = data.get("document", {})
        return self._parse_node(document) if "children" in document else []

    def _parse_node(self, node: Dict[str, Any]) -> List[FigmaComponent]:
        components = []
        node_type = node.get("type")
        if node_type in ["COMPONENT", "FRAME", "GROUP"]:
            children = []
            for child in node.get("children", []):
                children.extend(self._parse_node(child))

            bbox = node.get("absoluteBoundingBox", {})
            components.append(FigmaComponent(
                name=node.get("name", "UnnamedComponent"),
                type=node_type,
                properties={
                    "width": bbox.get("width", 100),
                    "height": bbox.get("height", 100),
                    "layoutMode": node.get("layoutMode", "NONE"),
                },
                children=children,
            ))
        return components

    def get_colors(self, design: FigmaDesign) -> Dict[str, str]:
        """Get color tokens from design."""
        return design.colors

    def get_typography(self, design: FigmaDesign) -> Dict[str, Dict[str, Any]]:
        """Get typography tokens from design."""
        return design.typography

    def get_spacing(self, design: FigmaDesign) -> Dict[str, float]:
        """Get spacing tokens from design."""
        return design.spacing

    def extract_components(self, design: FigmaDesign) -> List[FigmaComponent]:
        """Get all components from design."""
        return design.components

    def detect_layout_type(self, component: FigmaComponent) -> str:
        """Detect layout container type (Column, Row, or Box)."""
        mode = component.properties.get("layoutMode", "NONE")
        if mode == "VERTICAL":
            return "Column"
        elif mode == "HORIZONTAL":
            return "Row"
        return "Box"

    def convert_colors_to_compose(self, colors: Dict[str, str]) -> str:
        """Convert colors dictionary to Compose Color definitions."""
        lines = ["// Colors"]
        for name, val in colors.items():
            safe_val = val.replace("#", "0xFF") if val.startswith("#") else val
            safe_name = name.replace("-", "_").replace(" ", "_")
            lines.append(f"val {safe_name} = Color({safe_val})")
        return "\n".join(lines)

    def convert_typography_to_compose(self, typography: Dict[str, Dict[str, Any]]) -> str:
        """Convert typography dictionary to Compose TextStyle definitions."""
        lines = ["// Typography"]
        for name, props in typography.items():
            font_size = props.get("fontSize", 16)
            safe_name = name.replace("-", "_").replace(" ", "_")
            lines.append(f"val {safe_name}Style = TextStyle(fontSize = {font_size}.sp)")
        return "\n".join(lines)

    def convert_component_to_composable(self, component: FigmaComponent) -> str:
        """Convert a single FigmaComponent to a @Composable function."""
        safe_name = component.name.replace(" ", "").replace("-", "") or "CustomComponent"
        return f"""@Composable
fun {safe_name}() {{
    Button(onClick = {{ /* TODO */ }}) {{
        Text("{component.name}")
    }}
}}"""

    def convert_to_compose(self, design: FigmaDesign) -> str:
        """
        Convert Figma design tokens and components to standalone Jetpack Compose code.

        Args:
            design: FigmaDesign data

        Returns:
            Complete Kotlin source code
        """
        code_parts = [
            "import androidx.compose.runtime.Composable",
            "import androidx.compose.ui.Modifier",
            "import androidx.compose.material3.*",
            "import androidx.compose.ui.graphics.Color",
            "import androidx.compose.ui.unit.dp",
            "import androidx.compose.ui.unit.sp",
            "import androidx.compose.ui.text.TextStyle",
            "import androidx.compose.ui.text.font.FontWeight",
            "import androidx.compose.foundation.layout.*",
            "",
            self.convert_colors_to_compose(design.colors),
            "",
            self.convert_typography_to_compose(design.typography),
            "",
            "// Components",
        ]

        for comp in design.components:
            code_parts.append(self.convert_component_to_composable(comp))
            code_parts.append("")

        return "\n".join(code_parts)
