import asyncio
from fastmcp import Client

async def test_orchestration_agent():
    """
    Test the orchestration agent by calling its tools and accessing its resources.
    """
    print("=" * 70)
    print("Testing Orchestration Agent MCP Server")
    print("=" * 70)
    
    # Connect to the orchestration agent (in-memory server for testing)
    # For production, you would connect to a running server
    from orchestration_agent import mcp as server
    
    client = Client(server)
    
    async with client:
        print("\n1. Testing server connectivity...")
        await client.ping()
        print("✓ Server is responsive")
        
        # List available operations
        print("\n2. Listing available tools...")
        tools = await client.list_tools()
        print(f"✓ Found {len(tools)} tools:")
        for tool in tools:
            print(f"   - {tool.name}: {tool.description}")
        
        print("\n3. Listing available resources...")
        resources = await client.list_resources()
        print(f"✓ Found {len(resources)} resources:")
        for resource in resources:
            print(f"   - {resource.uri}: {resource.name}")
        
        print("\n4. Listing available prompts...")
        prompts = await client.list_prompts()
        print(f"✓ Found {len(prompts)} prompts:")
        for prompt in prompts:
            print(f"   - {prompt.name}: {prompt.description}")
        
        # Test FunctionA
        print("\n5. Testing FunctionA...")
        result = await client.call_tool("function_a", {"input_data": "test data"})
        print(f"✓ FunctionA result: {result.content[0].text}")
        
        # Test FunctionB
        print("\n6. Testing FunctionB...")
        result = await client.call_tool("function_b", {
            "parameters": {"key1": "value1", "key2": "value2"}
        })
        print(f"✓ FunctionB result: {result.content[0].text}")
        
        # Test FunctionC
        print("\n7. Testing FunctionC...")
        result = await client.call_tool("function_c", {
            "task_id": "TASK-001",
            "action": "analyze"
        })
        print(f"✓ FunctionC result: {result.content[0].text}")
        
        # Access knowledge base resource
        print("\n8. Accessing knowledge base...")
        kb_result = await client.read_resource("knowledge-base://pdfs")
        print(f"✓ Knowledge base info:")
        print(f"   {kb_result[0].text}")
        
        # Test prompts
        print("\n9. Testing incident analysis prompt...")
        prompt_result = await client.get_prompt("incident_analysis_prompt", {
            "incident_description": "Server down in production environment"
        })
        print(f"✓ Generated prompt (first 200 chars):")
        prompt_text = str(prompt_result.messages[0].content)
        print(prompt_text[:200] + "..." if len(prompt_text) > 200 else prompt_text)
        
    print("\n" + "=" * 70)
    print("All tests completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_orchestration_agent())
