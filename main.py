"""MCP Client"""

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command="uv",  # Executable
    args=["run", "server.py"],  # Optional command line arguments
)


async def run():
    """
    Run the client
    """
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()

            # Call a tool
            result = await session.call_tool(
                "get_todays_weather", arguments={"city_name": "london"}
            )

            print(result)


if __name__ == "__main__":
    asyncio.run(run())
