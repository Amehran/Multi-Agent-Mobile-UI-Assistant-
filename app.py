#!/usr/bin/env python3
"""
Streamlit Application Launcher.

Launches the interactive web UI for generating and refining Jetpack Compose UI code.

Usage:
    python app.py
    # or with uv:
    uv run python app.py
"""

import subprocess
import sys
import os

interface_path = os.path.join(
    os.path.dirname(__file__),
    "src",
    "multi_agent_mobile_ui_assistant",
    "web",
    "app.py"
)

if os.path.exists(".venv"):
    subprocess.run([sys.executable, "-m", "streamlit", "run", interface_path])
else:
    subprocess.run(["streamlit", "run", interface_path])
