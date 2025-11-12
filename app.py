#!/usr/bin/env python3
"""
Launch script for the Streamlit Web Interface

This script launches the interactive web UI for generating and refining
Jetpack Compose UI code.

Usage:
    python app.py
    # or with uv:
    uv run python app.py
"""

import subprocess
import sys
import os

# Get the path to the streamlit interface
interface_path = os.path.join(
    os.path.dirname(__file__),
    "src",
    "multi_agent_mobile_ui_assistant",
    "streamlit_interface.py"
)

# Check if we're in a uv environment
if os.path.exists(".venv"):
    # Use uv run to ensure we're in the virtual environment
    subprocess.run([sys.executable, "-m", "streamlit", "run", interface_path])
else:
    # Fall back to direct streamlit command
    subprocess.run(["streamlit", "run", interface_path])
