import asyncio
import logging
import sys
import signal
from typing import Dict, Any, Optional, List

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("weather_mcp")

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
class WeatherData(BaseModel):
    temperature: float
    description: str
    humidity: float
    wind_speed: float
    location: str

def run_server():
    """Run the Weather MCP server"""
    try:
        logger.info("Starting Weather MCP server")
        
        # Create FastMCP server with name
        mcp = FastMCP("Weather Information")
        
        # Define the get_weather tool
        @mcp.tool()
        async def get_weather(location: str, units: str = "metric") -> WeatherData:
            """Get current weather for a location"""
            global shutdown_requested
            
            if shutdown_requested:
                logger.info("Shutdown requested, canceling weather request")
                raise ValueError("Server is shutting down")
                
            try:
                logger.info(f"Getting weather for: {location} in {units}")
                
                # This is a mock implementation - would connect to a real weather API in production
                await asyncio.sleep(1)  # Simulate API call
                
                # Mock data
                temperature = 22.5 if units == "metric" else 72.5
                weather_data = WeatherData(
                    temperature=temperature,
                    description="Partly cloudy with a chance of rain",
                    humidity=65.0,
                    wind_speed=10.0,
                    location=location
                )
                
                logger.info(f"Weather data retrieved for {location}")
                return weather_data
            except Exception as e:
                logger.error(f"Error getting weather: {str(e)}")
                raise ValueError(f"Error getting weather: {str(e)}")
        
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
        logger.info("Weather MCP server stopped by keyboard interrupt")
    except Exception as e:
        logger.error(f"Error running Weather MCP server: {str(e)}")
    finally:
        logger.info("Weather MCP server shutdown complete")

if __name__ == "__main__":
    run_server() 