import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run_mcp_test():
    print("🚀 Starting MCP Client Integration Test...")
    
    # Define the parameters to connect to our local Yindan MCP Server
    server_params = StdioServerParameters(
        command="python",
        args=["skills/mcp_servers/yindan_server.py"],
    )

    print("🔌 Connecting to Yindan Server via stdio...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection (Standard MCP Handshake)
            await session.initialize()
            print("✅ Session Initialized.")
            
            # 1. Discover Tools
            print("\n🔍 Requesting Available Tools...")
            tools_response = await session.list_tools()
            for tool in tools_response.tools:
                print(f"   - Discovered Tool: {tool.name}")
                print(f"     Description: {tool.description[:50]}...")
            
            # 2. Execute Tool (Simulating Nezha fixing the bug)
            print("\n⚡ Executing Tool: yindan_precise_replace...")
            try:
                result = await session.call_tool(
                    "yindan_precise_replace",
                    arguments={
                        "filepath": "UserService.py",
                        "old_str": "token == None",
                        "new_str": "token is None"
                    }
                )
                print(f"🎯 Tool Execution Result:\n{result.content[0].text}")
            except Exception as e:
                print(f"❌ Tool Execution Failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_mcp_test())
