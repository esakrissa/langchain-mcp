import asyncio
import os
import signal
import logging
import sys
from typing import Dict, Any, Union, List, Optional, AsyncIterator
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
import httpx

# Configure minimal logging first so we can log import errors
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("tavily_mcp")

# Load environment variables
load_dotenv()

# Flag to track shutdown state
shutdown_requested = False

def signal_handler(sig, frame):
    """Handle termination signals"""
    global shutdown_requested
    logger.info("Received termination signal, initiating shutdown...")
    shutdown_requested = True

# Set up signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Input/output models
class SearchWebInput(BaseModel):
    query: str
    max_results: int = Field(default=10, description="Maximum number of search results to return")

class SearchNewsInput(BaseModel):
    query: str
    max_results: int = Field(default=10, description="Maximum number of news search results to return")

class SearchResult(BaseModel):
    title: str
    url: str
    content: str

class SearchResponse(BaseModel):
    results: List[SearchResult]

def run_server():
    """Run the Tavily MCP server"""
    try:
        logger.info("Starting Tavily MCP server")
        
        # Check for API key
        api_key = os.environ.get("TAVILY_API_KEY")
        if not api_key:
            logger.error("TAVILY_API_KEY environment variable is not set")
            raise ValueError("TAVILY_API_KEY environment variable is not set")
            
        # Create FastMCP server with name
        mcp = FastMCP("Tavily Search Tools")
        
        # Define the search_web tool
        @mcp.tool()
        async def search_web(query: str, max_results: int = 10) -> SearchResponse:
            """Search the web for information using Tavily API"""
            global shutdown_requested
            
            if shutdown_requested:
                logger.info("Shutdown requested, canceling web search")
                raise ValueError("Server is shutting down")
                
            try:
                logger.info(f"Searching web for: {query}")
                
                # Use httpx directly to call Tavily API
                url = "https://api.tavily.com/search"
                headers = {
                    "content-type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                }
                
                payload = {
                    "query": query,
                    "search_depth": "advanced",
                    "include_answer": True,
                    "include_images": False,
                    "max_results": max_results
                }
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(url, json=payload, headers=headers)
                    response.raise_for_status()
                    data = response.json()
                
                results = []
                for result in data.get("results", []):
                    results.append(
                        SearchResult(
                            title=result.get("title", ""),
                            url=result.get("url", ""),
                            content=result.get("content", ""),
                        )
                    )
                
                return SearchResponse(results=results)
            except Exception as e:
                logger.error(f"Error in web search: {str(e)}")
                raise ValueError(f"Error in web search: {str(e)}")
        
        # Define the search_news tool
        @mcp.tool()
        async def search_news(query: str, max_results: int = 10) -> SearchResponse:
            """Search recent news articles for the latest information"""
            global shutdown_requested
            
            if shutdown_requested:
                logger.info("Shutdown requested, canceling news search")
                raise ValueError("Server is shutting down")
                
            try:
                logger.info(f"Searching news for: {query}")
                
                # Use httpx directly to call Tavily API
                url = "https://api.tavily.com/search"
                headers = {
                    "content-type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                }
                
                payload = {
                    "query": query,
                    "search_depth": "advanced",
                    "include_answer": True,
                    "include_images": False,
                    "max_results": max_results,
                    "search_type": "news"
                }
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(url, json=payload, headers=headers)
                    response.raise_for_status()
                    data = response.json()
                
                results = []
                for result in data.get("results", []):
                    results.append(
                        SearchResult(
                            title=result.get("title", ""),
                            url=result.get("url", ""),
                            content=result.get("content", ""),
                        )
                    )
                
                return SearchResponse(results=results)
            except Exception as e:
                logger.error(f"Error in news search: {str(e)}")
                raise ValueError(f"Error in news search: {str(e)}")
        
        # Setup shutdown check task
        async def check_shutdown():
            """Periodically check if shutdown was requested"""
            while not shutdown_requested:
                await asyncio.sleep(0.5)
            logger.info("Shutdown check detected termination request")
            
        # Start the server with a shutdown task
        if "stdio" in sys.argv:
            # For testing with stdio directly
            asyncio.run(asyncio.gather(
                mcp.run_stdio_async(),
                check_shutdown()
            ))
        else:
            # Normal operation
            mcp.run(transport="stdio")
            
    except KeyboardInterrupt:
        logger.info("Tavily MCP server stopped by keyboard interrupt")
    except Exception as e:
        logger.error(f"Error running Tavily MCP server: {str(e)}")
    finally:
        logger.info("Tavily MCP server shutdown complete")

if __name__ == "__main__":
    run_server() 