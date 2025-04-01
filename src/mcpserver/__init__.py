"""MCP servers for the LangGraph MCP Integration."""

import sys
import pathlib

# Make sure src is in the path
SRC_DIR = str(pathlib.Path(__file__).parent.parent.absolute())
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
    
# Now we can import the modules
from mcpserver.tavily import run_server as run_tavily_server
from mcpserver.math_server import run_server as run_math_server
from mcpserver.weather import run_server as run_weather_server

__all__ = [
    "run_tavily_server",
    "run_math_server", 
    "run_weather_server"
]
