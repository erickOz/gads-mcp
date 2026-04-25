"""A simple test tool."""

from ads_mcp.coordinator import mcp_server as mcp

@mcp.tool()
def hello(name: str = "world") -> str:
    """A simple test tool that returns a greeting."""
    return f"Hello, {name}!"
