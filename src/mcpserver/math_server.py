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
logger = logging.getLogger("math_mcp")

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
class CalculateResponse(BaseModel):
    result: float
    expression: str

def run_server():
    """Run the Math MCP server"""
    try:
        logger.info("Starting Math MCP server")
        
        # Create FastMCP server with name
        mcp = FastMCP("Math Operations")
        
        # Define the calculate tool
        @mcp.tool()
        async def calculate(expression: str) -> CalculateResponse:
            """Calculate the result of a mathematical expression"""
            global shutdown_requested
            
            if shutdown_requested:
                logger.info("Shutdown requested, canceling calculation")
                raise ValueError("Server is shutting down")
                
            try:
                logger.info(f"Calculating expression: {expression}")
                
                # Security check to prevent code execution
                allowed_chars = set("0123456789+-*/().^ ")
                if not all(c in allowed_chars for c in expression):
                    raise ValueError("Expression contains invalid characters")
                
                # Replace ^ with ** for exponentiation
                expression = expression.replace("^", "**")
                
                # Safety evaluation using Python's eval
                # Note: This is generally not recommended in production without more safeguards
                result = eval(expression, {"__builtins__": {}}, {})
                
                logger.info(f"Calculation result: {result}")
                return CalculateResponse(result=float(result), expression=expression)
            except Exception as e:
                logger.error(f"Error calculating expression: {str(e)}")
                raise ValueError(f"Error calculating expression: {str(e)}")
        
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
        logger.info("Math MCP server stopped by keyboard interrupt")
    except Exception as e:
        logger.error(f"Error running Math MCP server: {str(e)}")
    finally:
        logger.info("Math MCP server shutdown complete")

if __name__ == "__main__":
    run_server() 