# LangChain MCP Agent

A LangChain agent that uses MCP (Model Context Protocol) servers for various capabilities.

## Overview

This project demonstrates how to build a LangChain agent that uses the Model Context Protocol (MCP) to interact with various services:

- **Tavily Search**: Web search and news search capabilities
- **Weather**: Mock weather information retrieval
- **Math**: Mathematical expression evaluation

The agent uses LangGraph's ReAct agent pattern to dynamically select and use these tools based on user queries.

## Features

- **Graceful Shutdown**: All MCP servers implement proper signal handling for clean termination
- **Subprocess Management**: The main agent tracks and manages all MCP server subprocesses
- **Error Handling**: Robust error handling throughout the application
- **Modular Design**: Easy to extend with additional MCP servers

## Graceful Shutdown Mechanism

This project implements a comprehensive graceful shutdown system:

1. **Signal Handling**: Captures SIGINT and SIGTERM signals to initiate graceful shutdown
2. **Process Tracking**: The main agent maintains a registry of all child processes
3. **Cleanup Process**: Ensures all subprocesses are properly terminated on exit
4. **Shutdown Flags**: Each MCP server has a shutdown flag to prevent new operations when shutdown is initiated
5. **Async Cooperation**: Uses asyncio to allow operations in progress to complete when possible

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/langchain-mcp.git
cd langchain-mcp

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

## Configuration

Create a `.env` file in the project root with the following variables:

```
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key
```

## Usage

Run the agent from the command line:

```bash
python src/agent.py
```

The agent will prompt for your query and then process it using the appropriate tools.

## Development

To add a new MCP server:

1. Create a new file in `src/mcpserver/`
2. Implement the server with proper signal handling
3. Update `src/mcpserver/__init__.py` to expose the new server
4. Add the server configuration to `src/agent.py`

## License

MIT 