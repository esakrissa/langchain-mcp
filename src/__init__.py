"""LangGraph MCP Integration package."""

import sys
import os
import pathlib

__version__ = "0.1.0"

# Add the src directory to Python path for any imports
SRC_DIR = str(pathlib.Path(__file__).parent.absolute())
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
