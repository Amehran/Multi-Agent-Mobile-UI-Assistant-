#!/usr/bin/env python3
"""
Launch script for the Streamlit Web Interface

This script launches the interactive web UI for generating and refining
Jetpack Compose UI code.

Usage:
    python app.py
    # or
    streamlit run src/multi_agent_mobile_ui_assistant/streamlit_interface.py
"""

import os

# Get the path to the streamlit interface
interface_path = os.path.join(
    os.path.dirname(__file__),
    "src",
    "multi_agent_mobile_ui_assistant",
    "streamlit_interface.py"
)

# Run streamlit
os.system(f"streamlit run {interface_path}")
