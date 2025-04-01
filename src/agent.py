import asyncio
import os
import sys
import pathlib
import signal
import atexit
from typing import Dict, Any, List, Optional
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

# Get the absolute path to the src directory
SRC_DIR = str(pathlib.Path(__file__).parent.absolute())

# Store active processes for cleanup
active_processes: List[asyncio.subprocess.Process] = []
# Track if cleanup has already been called
_cleanup_called = False

# Graceful shutdown function
def cleanup_processes():
    """Terminate all active subprocesses gracefully."""
    global _cleanup_called
    
    # Only run cleanup once
    if _cleanup_called:
        return
        
    _cleanup_called = True
    print("\nShutting down MCP servers...")
    for process in active_processes:
        if process and process.returncode is None:
            try:
                # Try to terminate gracefully
                process.terminate()
            except Exception as e:
                print(f"Error terminating process: {e}")
    print("Shutdown complete.")

# Register cleanup function at exit
atexit.register(cleanup_processes)

# Handle keyboard interrupts
def signal_handler(sig, frame):
    """Handle SIGINT and SIGTERM signals."""
    print("\nReceived termination signal. Cleaning up...")
    cleanup_processes()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

class ProcessTrackingClient(MultiServerMCPClient):
    """Subclass to track subprocess handles."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.server_processes = []
    
    async def _start_server(self, name, server_config):
        proc = await super()._start_server(name, server_config)
        active_processes.append(proc)
        return proc
    
    async def close(self):
        await super().close()
        # Don't clear process list here, let the cleanup function handle it

async def run_agent():
    # Get essential environment variables
    tavily_api_key = os.environ.get("TAVILY_API_KEY", "")
    
    if not tavily_api_key:
        print("Error: TAVILY_API_KEY environment variable is not set.")
        return "Tavily API key is not configured. Please set TAVILY_API_KEY in your .env file."
    
    # Define MCP servers configuration with absolute Python path
    async with ProcessTrackingClient(
        {
            "weather": {
                "command": sys.executable,
                "args": ["-c", f"import sys; sys.path.insert(0, '{SRC_DIR}'); from mcpserver.weather import run_server; run_server()"],
                "transport": "stdio",
                "env": {
                    "PYTHONPATH": SRC_DIR,
                }
            },
            "tavily": {
                "command": sys.executable,
                "args": ["-c", f"import sys; sys.path.insert(0, '{SRC_DIR}'); from mcpserver.tavily import run_server; run_server()"],
                "transport": "stdio",
                "env": {
                    "TAVILY_API_KEY": tavily_api_key,
                    "PATH": os.environ.get("PATH", ""),
                    "HOME": os.environ.get("HOME", ""),
                    "PYTHONPATH": SRC_DIR,
                }
            }, 
            "math": {
                "command": sys.executable,
                "args": ["-c", f"import sys; sys.path.insert(0, '{SRC_DIR}'); from mcpserver.math_server import run_server; run_server()"],
                "transport": "stdio",
                "env": {
                    "PYTHONPATH": SRC_DIR,
                }
            },       
        }
    ) as client:
        # Initialize LLM
        model = ChatOpenAI(model="gpt-4o-mini")
        
        # Load available tools
        tools = client.get_tools()
        agent = create_react_agent(model, tools)

        # Define system message
        system_message = SystemMessage(content=(
            "You have access to multiple tools that can help answer queries. "
            "Use them dynamically and efficiently based on the user's request. "
            "The Tavily tools can search the web or recent news, giving you access to up-to-date information. "
            "For questions about current information like weather, news, or currency exchange rates, "
            "always use the Tavily search_web tool to get the most recent data."
        ))

        # Get user query
        try:
            query = input("Query: ")
            
            print("Processing your query. This may take a moment...")
            
            # Process the query
            agent_response = await agent.ainvoke({
                "messages": [system_message, HumanMessage(content=query)]
            })

            return agent_response["messages"][-1].content
        except (KeyboardInterrupt, EOFError):
            print("\nQuery input interrupted. Shutting down...")
            return "Operation cancelled by user."

def main():
    """Run the LangGraph MCP agent as a CLI application."""
    try:
        # Make sure the src directory is in the Python path
        if SRC_DIR not in sys.path:
            sys.path.insert(0, SRC_DIR)
            
        print("Starting agent. Press Ctrl+C to exit.")
        response = asyncio.run(run_agent())
        print("\nFinal Response:", response)
        return 0
    except KeyboardInterrupt:
        print("\nAgent stopped by user.")
        return 130
    except Exception as e:
        print(f"\nError: {e}")
        return 1
    finally:
        # Ensure cleanup is called
        cleanup_processes()

if __name__ == "__main__":
    exit(main()) 