"""
Multi-Agent Mobile UI Assistant.

A production-ready LangGraph-based multi-agent system for generating and refining
Jetpack Compose UI code from natural language descriptions and Figma designs.
"""

from .core.pipeline import generate_ui_from_description
from .core.graph import build_ui_generator_graph
from .core.state import UIGeneratorState
from .config.llm import create_llm, get_default_llm, LLMConfig
from .mcp.android_tools import AndroidLintMCP, GradleMCP
from .mcp.figma import FigmaMCP
from .mcp.github import GitHubMCP, FileSystemMCP

__version__ = "0.2.0"

__all__ = [
    "generate_ui_from_description",
    "build_ui_generator_graph",
    "UIGeneratorState",
    "create_llm",
    "get_default_llm",
    "LLMConfig",
    "AndroidLintMCP",
    "GradleMCP",
    "FigmaMCP",
    "GitHubMCP",
    "FileSystemMCP",
]
