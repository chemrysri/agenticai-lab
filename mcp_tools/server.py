from mcp.server.fastmcp import FastMCP

from tools.searxng_tool import register_searxng_tools
from tools.filesystem_tool import register_filesystem_tools
from tools.sqlite_tool import register_sqlite_tools
# from tools.calendar_tool import register_calendar_tools


mcp = FastMCP(
    name="Private AI Local Tools",
    json_response=True,
)


register_searxng_tools(mcp)
register_filesystem_tools(mcp)
register_sqlite_tools(mcp)
# register_calendar_tools(mcp)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")