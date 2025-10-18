# UI Integration Guide

This guide explains how to connect the web UI (`incident-analyzer-hackathon`) to the orchestration agent.

## Overview

The orchestration agent is an MCP server that can be accessed by the Flask web application to:

- Analyze incidents using AI-powered tools
- Access knowledge base documents
- Execute orchestration functions
- Generate structured prompts for incident analysis

## Integration Approaches

### Option 1: Direct In-Memory Integration

For development and testing, you can import and use the orchestration agent directly in your Flask app.

```python
# In your Flask app (app.py)
from fastmcp import Client
import sys
sys.path.append('../agents')
from orchestration_agent import mcp as orchestration_server

# Create a global client
orchestration_client = None

@app.before_first_request
async def setup_orchestration_client():
    global orchestration_client
    orchestration_client = Client(orchestration_server)

@app.route('/api/analyze-incident', methods=['POST'])
async def analyze_incident():
    data = request.json
    incident_description = data.get('description', '')

    async with orchestration_client:
        # Get analysis prompt
        prompt = await orchestration_client.get_prompt(
            "incident_analysis_prompt",
            {"incident_description": incident_description}
        )

        # Call analysis function
        result = await orchestration_client.call_tool(
            "function_a",
            {"input_data": incident_description}
        )

        return jsonify({
            "status": "success",
            "analysis": result.content[0].text
        })
```

### Option 2: HTTP Server Integration

For production, run the orchestration agent as a separate HTTP server.

#### Step 1: Modify orchestration_agent.py to run as HTTP server

```python
# Add at the end of orchestration_agent.py
if __name__ == "__main__":
    # For HTTP server mode
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--http":
        from mcp.server.fastmcp import FastMCPServer
        server = FastMCPServer(mcp)
        server.run(host="localhost", port=8080)
    else:
        # Normal mode
        asyncio.run(main())
```

#### Step 2: Start the HTTP server

```bash
cd agents
python3.10 orchestration_agent.py --http
```

#### Step 3: Connect from Flask

```python
from fastmcp import Client

# Connect to HTTP server
client = Client("http://localhost:8080/mcp")

@app.route('/api/analyze-incident', methods=['POST'])
async def analyze_incident():
    data = request.json

    async with client:
        result = await client.call_tool(
            "function_a",
            {"input_data": data['description']}
        )

        return jsonify({"analysis": result.content[0].text})
```

## Example: Full Flask Integration

Here's a complete example showing how to integrate the orchestration agent with your Flask app:

```python
# incident-analyzer-hackathon/incident-analyzer/app.py (additions)

from fastmcp import Client
import asyncio
import sys
sys.path.append('../../agents')

# Initialize orchestration client
def get_orchestration_client():
    from orchestration_agent import mcp as server
    return Client(server)

# New route for orchestrated analysis
@app.route('/api/orchestrate-analysis', methods=['POST'])
def orchestrate_analysis():
    """
    Uses the orchestration agent to analyze an incident.
    """
    data = request.json
    incident_data = data.get('incident', {})

    async def run_analysis():
        client = get_orchestration_client()
        async with client:
            # Get available knowledge base
            kb = await client.read_resource("knowledge-base://documents")

            # Generate analysis prompt
            prompt = await client.get_prompt(
                "incident_analysis_prompt",
                {"incident_description": incident_data.get('description', '')}
            )

            # Execute analysis
            result = await client.call_tool(
                "function_a",
                {"input_data": str(incident_data)}
            )

            return {
                "knowledge_base": kb[0].text,
                "prompt_used": str(prompt.messages[0].content),
                "analysis_result": result.content[0].text
            }

    # Run async code
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(run_analysis())
    loop.close()

    return jsonify(result)

# Route to get available orchestration tools
@app.route('/api/orchestration-capabilities', methods=['GET'])
def get_orchestration_capabilities():
    """
    Returns information about available orchestration tools and resources.
    """
    async def get_capabilities():
        client = get_orchestration_client()
        async with client:
            tools = await client.list_tools()
            resources = await client.list_resources()
            prompts = await client.list_prompts()

            return {
                "tools": [{"name": t.name, "description": t.description} for t in tools],
                "resources": [{"uri": r.uri, "name": r.name} for r in resources],
                "prompts": [{"name": p.name, "description": p.description} for p in prompts]
            }

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(get_capabilities())
    loop.close()

    return jsonify(result)
```

## Frontend Integration

Update your JavaScript to call the new endpoints:

```javascript
// In main.js

async function analyzeWithOrchestration(incidentData) {
  try {
    const response = await fetch("/api/orchestrate-analysis", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        incident: incidentData,
      }),
    });

    const result = await response.json();

    // Display results
    displayOrchestrationResults(result);
  } catch (error) {
    console.error("Orchestration analysis failed:", error);
  }
}

function displayOrchestrationResults(result) {
  // Update UI with analysis results
  document.getElementById("knowledge-base-info").textContent =
    result.knowledge_base;
  document.getElementById("analysis-result").textContent =
    result.analysis_result;
}

// Get orchestration capabilities on page load
async function loadOrchestrationCapabilities() {
  const response = await fetch("/api/orchestration-capabilities");
  const capabilities = await response.json();

  console.log("Orchestration Tools:", capabilities.tools);
  console.log("Available Resources:", capabilities.resources);
  console.log("Available Prompts:", capabilities.prompts);
}

// Call on page load
document.addEventListener("DOMContentLoaded", loadOrchestrationCapabilities);
```

## Resource Management

### Updating UI Connection Status

Create a handler to update the UI connection status resource:

```python
# Add to orchestration_agent.py

# Store UI connection state
ui_connection_state = {
    "connected": False,
    "last_ping": None,
    "session_id": None
}

@mcp.resource("ui://connection-status")
async def get_ui_connection_status() -> str:
    """
    Provides information about the UI connection status.
    """
    if ui_connection_state["connected"]:
        return f"""UI Connection Status: CONNECTED
Session ID: {ui_connection_state['session_id']}
Last Ping: {ui_connection_state['last_ping']}
"""
    else:
        return "UI Connection Status: DISCONNECTED"

@mcp.tool()
async def register_ui_connection(session_id: str) -> Dict[str, Any]:
    """
    Register a UI connection.
    """
    from datetime import datetime
    ui_connection_state["connected"] = True
    ui_connection_state["session_id"] = session_id
    ui_connection_state["last_ping"] = datetime.now().isoformat()

    return {
        "status": "success",
        "message": "UI connection registered",
        "session_id": session_id
    }
```

## Testing the Integration

1. Start the orchestration agent:

```bash
cd agents
python3.10 orchestration_agent.py
```

2. In another terminal, start the Flask app:

```bash
cd incident-analyzer-hackathon/incident-analyzer
python app.py
```

3. Access the web UI and use the new orchestration features

## Best Practices

1. **Error Handling**: Wrap MCP calls in try-except blocks
2. **Async Management**: Properly manage async event loops in Flask
3. **Connection Pooling**: Consider connection pooling for production
4. **Timeouts**: Set appropriate timeouts for MCP calls
5. **Logging**: Log all orchestration interactions for debugging

## Troubleshooting

### Issue: "Event loop is already running"

**Solution**: Use `asyncio.new_event_loop()` as shown in examples

### Issue: Import errors for fastmcp

**Solution**: Ensure Flask app also uses Python 3.10+

### Issue: Connection refused

**Solution**: Verify orchestration agent is running before starting Flask app

## Next Steps

1. Implement actual orchestration logic in FunctionA, B, C
2. Add PDF parsing to extract content from knowledge base
3. Create more sophisticated prompts for different incident types
4. Add caching layer for frequently accessed resources
5. Implement authentication/authorization for production use
